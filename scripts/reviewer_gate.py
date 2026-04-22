#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from common import abs_path, run


ZERO_SHA = "0" * 40
EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_REASONING_EFFORT = "xhigh"
MAX_LOG_CHARS = 4_000
REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "summary", "findings"],
    "properties": {
        "status": {"type": "string", "enum": ["approved", "changes_requested"]},
        "summary": {"type": "string", "minLength": 1},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["severity", "title", "details", "file"],
                "properties": {
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "title": {"type": "string", "minLength": 1},
                    "details": {"type": "string", "minLength": 1},
                    "file": {"type": "string", "minLength": 1},
                    "line": {"type": "integer", "minimum": 1},
                },
            },
        },
    },
}
REVIEW_PROMPT = textwrap.dedent(
    """\
    You are the push-time reviewer gate for the LocalLens repository.

    Review only the outgoing git changes and verification results supplied on stdin.
    Use subagents consistently when the runtime supports them.
    Inspect the diff and any relevant repository files, but do not modify anything.

    This is a blocking gate. Approve only when the outgoing changes are safe to push as-is.
    Treat missing confidence as a blocker.
    Use these custom review roles when available:
    - extension-runtime-reviewer: verify Chrome MV3 runtime behavior, especially popup actions,
      activeTab capture, and chrome.scripting.executeScript isolation.
    - cws-policy-reviewer: compare manifest, listing copy, reviewer docs, screenshots, and support
      links against shipped behavior.
    - reviewer: final correctness, regression, security, and public-surface review.

    Block any injected chrome.scripting.executeScript function that depends on popup-module imports
    or closure state unavailable in the page context. Block any Chrome Web Store feature claim that
    lacks a reproducible reviewer path or deterministic test coverage.

    Return JSON matching the provided schema:
    - status: "approved" only when there are zero blocking findings.
    - status: "changes_requested" if any blocking finding exists or if confidence is too low.
    - summary: one short sentence.
    - findings: blocking issues only, each with severity, title, details, file, and optional line.

    Focus on correctness, regressions, Chrome Web Store privacy/support link risk, release metadata,
    deploy/test gaps, CI/hook behavior, and broken public page routing.
    """
)
ZIP_SANITY_SCRIPT = textwrap.dedent(
    """\
    import json
    import sys
    import zipfile

    zip_path = sys.argv[1]
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

    required = {"manifest.json", "popup.html", "popup.js", "popup-helpers.js"}
    missing = sorted(required - set(names))
    assert not missing, f"missing packaged files: {missing}"
    assert not any(name.endswith(".test.js") for name in names), names
    assert manifest.get("version"), "manifest version missing"
    print(f"ZIP sanity passed for version {manifest['version']} with {len(names)} files")
    """
)


@dataclass(frozen=True)
class PushTarget:
    local_ref: str
    local_sha: str
    remote_ref: str
    remote_sha: str

    @property
    def is_delete(self) -> bool:
        return self.local_sha == ZERO_SHA


@dataclass(frozen=True)
class ReviewRange:
    local_ref: str
    remote_ref: str
    base_sha: str
    head_sha: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class CodexReviewResult:
    status: str
    summary: str
    findings: tuple[dict[str, object], ...]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LocalLens push-time verification and Codex review.")
    parser.add_argument("--repo-root", default=".", help="Project root.")
    parser.add_argument("--remote-name", help="Git remote name override.")
    parser.add_argument("--remote-url", help="Git remote URL override.")
    parser.add_argument("--skip-verification", action="store_true", help="Skip local verification commands.")
    parser.add_argument("--skip-codex", action="store_true", help="Skip the Codex review step.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Codex model for review.")
    parser.add_argument(
        "--reasoning-effort",
        default=DEFAULT_REASONING_EFFORT,
        help="Codex model_reasoning_effort override.",
    )
    parser.add_argument("hook_args", nargs="*", help="Arguments forwarded from git pre-push.")
    return parser.parse_args(argv)


def parse_push_targets(stdin_text: str) -> list[PushTarget]:
    targets: list[PushTarget] = []
    for raw_line in stdin_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"Unexpected pre-push input: {raw_line!r}")
        targets.append(PushTarget(*parts))
    return targets


def shell_join(command: Sequence[str]) -> str:
    return shlex.join([str(part) for part in command])


def to_command_result(command: Sequence[str], completed: subprocess.CompletedProcess[str]) -> CommandResult:
    return CommandResult(
        command=tuple(str(part) for part in command),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    input_text: str | None = None,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    if input_text is None:
        completed = run(list(command), cwd=cwd, timeout=timeout, env=env)
        return to_command_result(command, completed)
    completed = subprocess.run(
        list(command),
        cwd=str(cwd),
        env={**os.environ, **(env or {})},
        text=True,
        input=input_text,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    return to_command_result(command, completed)


def clip_text(text: str, limit: int = MAX_LOG_CHARS) -> str:
    if len(text) <= limit:
        return text
    kept = text[: limit - 48].rstrip()
    return f"{kept}\n... [truncated {len(text) - len(kept)} chars]"


def print_status(message: str) -> None:
    print(f"[reviewer-gate] {message}", file=sys.stderr)


def require_success(result: CommandResult, context: str) -> str:
    if result.returncode != 0:
        raise RuntimeError(
            f"{context} failed with exit code {result.returncode}: {shell_join(result.command)}\n"
            f"{clip_text((result.stderr or result.stdout).strip())}"
        )
    return result.stdout


def git_output(repo_root: Path, *args: str) -> str:
    result = run_process(("git", *args), cwd=repo_root)
    return require_success(result, "git command")


def git_ok(repo_root: Path, *args: str) -> bool:
    return run_process(("git", *args), cwd=repo_root).ok


def rev_exists(repo_root: Path, rev: str) -> bool:
    return git_ok(repo_root, "rev-parse", "--verify", "--quiet", rev)


def tracked(repo_root: Path, relative_path: str) -> bool:
    return git_ok(repo_root, "ls-files", "--error-unmatch", relative_path)


def python_module_available(repo_root: Path, module_name: str) -> bool:
    result = run_process((sys.executable, "-c", f"import {module_name}"), cwd=repo_root)
    return result.ok


def default_base_ref(repo_root: Path, remote_name: str) -> str | None:
    symbolic = run_process(("git", "symbolic-ref", "--quiet", f"refs/remotes/{remote_name}/HEAD"), cwd=repo_root)
    candidates: list[str] = []
    if symbolic.ok and symbolic.stdout.strip():
        candidates.append(symbolic.stdout.strip())
    candidates.extend(
        [
            f"refs/remotes/{remote_name}/main",
            f"refs/remotes/{remote_name}/master",
        ]
    )
    for candidate in candidates:
        if candidate and rev_exists(repo_root, candidate):
            return candidate
    return None


def resolve_base_sha(repo_root: Path, remote_name: str, target: PushTarget) -> str:
    if target.remote_sha != ZERO_SHA and rev_exists(repo_root, target.remote_sha):
        return target.remote_sha
    base_ref = default_base_ref(repo_root, remote_name)
    if base_ref:
        merge_base = run_process(("git", "merge-base", target.local_sha, base_ref), cwd=repo_root)
        if merge_base.ok and merge_base.stdout.strip():
            return merge_base.stdout.strip()
    return EMPTY_TREE_SHA


def diff_files(repo_root: Path, base_sha: str, head_sha: str) -> tuple[str, ...]:
    output = git_output(repo_root, "diff", "--name-only", "--find-renames", base_sha, head_sha)
    return tuple(line.strip() for line in output.splitlines() if line.strip())


def build_review_ranges(repo_root: Path, remote_name: str, targets: Sequence[PushTarget]) -> list[ReviewRange]:
    review_ranges: list[ReviewRange] = []
    seen: set[tuple[str, str, str, str]] = set()
    for target in targets:
        if target.is_delete:
            continue
        base_sha = resolve_base_sha(repo_root, remote_name, target)
        files = diff_files(repo_root, base_sha, target.local_sha)
        if not files:
            continue
        key = (target.local_ref, target.remote_ref, base_sha, target.local_sha)
        if key in seen:
            continue
        seen.add(key)
        review_ranges.append(
            ReviewRange(
                local_ref=target.local_ref,
                remote_ref=target.remote_ref,
                base_sha=base_sha,
                head_sha=target.local_sha,
                files=files,
            )
        )
    return review_ranges


def tracked_python_targets(repo_root: Path) -> list[str]:
    candidates = sorted(repo_root.glob("scripts/*.py"))
    candidates.extend(sorted(repo_root.glob("tests/*.py")))
    targets: list[str] = []
    for candidate in candidates:
        relative = str(candidate.relative_to(repo_root))
        if tracked(repo_root, relative):
            targets.append(relative)
    return targets


def run_local_verification(repo_root: Path) -> list[CommandResult]:
    results: list[CommandResult] = []
    pytest_env = {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    compile_targets = tracked_python_targets(repo_root)
    if compile_targets:
        results.append(run_process((sys.executable, "-m", "py_compile", *compile_targets), cwd=repo_root))

    if tracked(repo_root, "package.json"):
        results.append(run_process(("npm", "test"), cwd=repo_root))

    results.append(run_process((sys.executable, "-m", "pytest", "-q"), cwd=repo_root, env=pytest_env))

    with tempfile.TemporaryDirectory(prefix="locallens-reviewer-gate-") as temp_dir:
        temp_path = Path(temp_dir)
        launch_manifest = temp_path / "launch-manifest.json"
        listing_payload = temp_path / "store-listing.json"
        extension_zip = temp_path / "locallens-extension.zip"
        results.append(
            run_process(
                (
                    sys.executable,
                    "scripts/generate_launch_manifest.py",
                    "--repo-root",
                    str(repo_root),
                    "--out",
                    str(launch_manifest),
                ),
                cwd=repo_root,
            )
        )
        results.append(
            run_process(
                (
                    sys.executable,
                    "scripts/generate_listing_copy.py",
                    "--repo-root",
                    str(repo_root),
                    "--manifest",
                    str(launch_manifest),
                    "--out",
                    str(listing_payload),
                ),
                cwd=repo_root,
            )
        )
        results.append(
            run_process(
                (
                    sys.executable,
                    "scripts/build_extension_zip.py",
                    "--extension-dir",
                    "extension",
                    "--out",
                    str(extension_zip),
                ),
                cwd=repo_root,
            )
        )
        if results[-1].ok:
            results.append(
                run_process((sys.executable, "-c", ZIP_SANITY_SCRIPT, str(extension_zip)), cwd=repo_root)
            )

    if python_module_available(repo_root, "codex_harness"):
        results.append(
            run_process(
                (
                    sys.executable,
                    "-m",
                    "codex_harness",
                    "audit",
                    ".",
                    "--strict",
                    "--min-score",
                    "90",
                ),
                cwd=repo_root,
            )
        )
    return results


def verification_failed(results: Sequence[CommandResult]) -> bool:
    return any(not result.ok for result in results)


def indent_block(text: str, prefix: str = "    ") -> str:
    return "\n".join(f"{prefix}{line}" for line in text.splitlines())


def render_verification_section(results: Sequence[CommandResult]) -> str:
    lines = ["## Local Verification"]
    for result in results:
        lines.append(f"- {'PASS' if result.ok else 'FAIL'}: {shell_join(result.command)}")
        if result.stdout.strip():
            lines.append("  stdout:")
            lines.append(indent_block(clip_text(result.stdout.rstrip())))
        if result.stderr.strip():
            lines.append("  stderr:")
            lines.append(indent_block(clip_text(result.stderr.rstrip())))
    return "\n".join(lines)


def render_diff_context(repo_root: Path, remote_name: str, remote_url: str, review_ranges: Sequence[ReviewRange]) -> str:
    lines = [
        "## Push Context",
        f"- repository: {repo_root}",
        f"- remote: {remote_name}",
        f"- remote_url: {remote_url}",
        "",
        "## Review Ranges",
    ]
    for review_range in review_ranges:
        lines.append(
            f"- {review_range.local_ref} -> {review_range.remote_ref}: "
            f"{review_range.base_sha}..{review_range.head_sha}"
        )
        for file_path in review_range.files:
            lines.append(f"  - {file_path}")
    lines.append("")
    lines.append("## Unified Diff")
    for review_range in review_ranges:
        lines.append(
            f"### {review_range.local_ref} -> {review_range.remote_ref} "
            f"({review_range.base_sha}..{review_range.head_sha})"
        )
        patch = git_output(
            repo_root,
            "diff",
            "--binary",
            "--find-renames",
            "--unified=3",
            review_range.base_sha,
            review_range.head_sha,
        ).rstrip()
        lines.append(patch or "(no diff)")
        lines.append("")
    return "\n".join(lines).rstrip()


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()


def prepare_isolated_codex_home(parent_dir: Path, repo_root: Path) -> dict[str, str]:
    codex_home = parent_dir / "codex-home"
    codex_home.mkdir(parents=True, exist_ok=True)

    source_auth = default_codex_home() / "auth.json"
    if source_auth.exists():
        shutil.copy2(source_auth, codex_home / "auth.json")

    config_text = textwrap.dedent(
        f"""\
        model = "{DEFAULT_MODEL}"
        model_reasoning_effort = "high"
        personality = "pragmatic"
        approval_policy = "never"

        [features]
        multi_agent = true

        [projects."{repo_root}"]
        trust_level = "trusted"
        """
    )
    (codex_home / "config.toml").write_text(config_text, encoding="utf-8")
    return {"CODEX_HOME": str(codex_home)}


def ensure_codex_available(env: dict[str, str]) -> None:
    if not shutil.which("codex"):
        raise RuntimeError("codex is not installed or not on PATH.")
    if os.environ.get("CODEX_API_KEY"):
        return
    codex_home = Path(env["CODEX_HOME"])
    if not (codex_home / "auth.json").exists():
        raise RuntimeError("Codex is not authenticated. Run `codex login` or export `CODEX_API_KEY` before pushing.")


def parse_codex_review(payload: str) -> CodexReviewResult:
    data = json.loads(payload)
    findings = tuple(data.get("findings", ()))
    if data.get("status") == "approved" and findings:
        raise ValueError("Codex review returned status=approved with blocking findings.")
    return CodexReviewResult(
        status=str(data["status"]),
        summary=str(data["summary"]),
        findings=findings,
    )


def build_codex_review_command(
    repo_root: Path,
    *,
    model: str,
    reasoning_effort: str,
    output_path: Path,
    prompt: str,
) -> tuple[str, ...]:
    return (
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--cd",
        str(repo_root),
        "--sandbox",
        "read-only",
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--config",
        "features.multi_agent=true",
        "--output-last-message",
        str(output_path),
        prompt,
    )


def run_codex_review(
    repo_root: Path,
    *,
    context: str,
    model: str,
    reasoning_effort: str,
) -> CodexReviewResult:
    with tempfile.TemporaryDirectory(prefix="locallens-codex-review-") as temp_dir:
        temp_path = Path(temp_dir)
        codex_env = prepare_isolated_codex_home(temp_path, repo_root)
        ensure_codex_available(codex_env)
        output_path = temp_path / "review-output.json"
        prompt = f"{REVIEW_PROMPT}\n\n{context}"
        command = build_codex_review_command(
            repo_root,
            model=model,
            reasoning_effort=reasoning_effort,
            output_path=output_path,
            prompt=prompt,
        )
        result = run_process(
            command,
            cwd=repo_root,
            timeout=900,
            env=codex_env,
        )
        if (
            not result.ok
            and reasoning_effort == "xhigh"
            and "unknown variant `xhigh`" in (result.stderr or result.stdout)
        ):
            print_status(
                "Installed Codex CLI does not support model_reasoning_effort=xhigh; retrying reviewer gate with high."
            )
            result = run_process(
                build_codex_review_command(
                    repo_root,
                    model=model,
                    reasoning_effort="high",
                    output_path=output_path,
                    prompt=prompt,
                ),
                cwd=repo_root,
                timeout=900,
                env=codex_env,
            )
        if not result.ok:
            raise RuntimeError(
                f"Codex review failed with exit code {result.returncode}: {shell_join(result.command)}\n"
                f"{clip_text((result.stderr or result.stdout).strip())}"
            )
        if not output_path.exists():
            raise RuntimeError("Codex review did not write the structured output file.")
        return parse_codex_review(output_path.read_text(encoding="utf-8"))


def print_codex_findings(review_result: CodexReviewResult) -> None:
    print_status(review_result.summary)
    for finding in review_result.findings:
        location = str(finding.get("file", "unknown"))
        line = finding.get("line")
        if line is not None:
            location = f"{location}:{line}"
        print_status(
            f"{str(finding.get('severity', 'unknown')).upper()} {location} - "
            f"{finding.get('title', 'Untitled finding')}"
        )
        details = str(finding.get("details", "")).strip()
        if details:
            print(indent_block(details), file=sys.stderr)


def gate(
    repo_root: Path,
    *,
    remote_name: str,
    remote_url: str,
    stdin_text: str,
    skip_verification: bool,
    skip_codex: bool,
    model: str,
    reasoning_effort: str,
) -> int:
    targets = parse_push_targets(stdin_text)
    review_ranges = build_review_ranges(repo_root, remote_name, targets)
    if not review_ranges:
        print_status("No outgoing file changes detected; skipping reviewer gate.")
        return 0

    verification_results: list[CommandResult] = []
    if skip_verification:
        print_status("Skipping local verification by request.")
    else:
        print_status("Running local verification.")
        verification_results = run_local_verification(repo_root)
        for result in verification_results:
            print_status(f"{shell_join(result.command)} {'passed' if result.ok else 'failed'}.")
        if verification_failed(verification_results):
            print_status("Skipping Codex review because local verification failed.")
            print_status("Push blocked.")
            return 1

    review_context = "\n\n".join(
        section
        for section in (
            render_verification_section(verification_results) if verification_results else "",
            render_diff_context(repo_root, remote_name, remote_url, review_ranges),
        )
        if section
    )

    review_result: CodexReviewResult | None = None
    if skip_codex:
        print_status("Skipping Codex review by request.")
    else:
        print_status(f"Running Codex review with {model} / {reasoning_effort}.")
        review_result = run_codex_review(
            repo_root,
            context=review_context,
            model=model,
            reasoning_effort=reasoning_effort,
        )
        if review_result is not None:
            if review_result.status == "approved":
                print_status(review_result.summary)
            else:
                print_codex_findings(review_result)

    blocked = verification_failed(verification_results)
    if review_result is not None and review_result.status != "approved":
        blocked = True
    if blocked:
        print_status("Push blocked.")
        return 1
    print_status("Push approved.")
    return 0


def main(argv: Sequence[str] | None = None, stdin_text: str | None = None) -> int:
    args = parse_args(argv)
    repo_root = abs_path(args.repo_root)
    remote_name = args.remote_name or (args.hook_args[0] if args.hook_args else "origin")
    if args.remote_url:
        remote_url = args.remote_url
    elif len(args.hook_args) >= 2:
        remote_url = args.hook_args[1]
    else:
        remote_url = git_output(repo_root, "remote", "get-url", remote_name).strip()
    input_text = stdin_text if stdin_text is not None else sys.stdin.read()

    try:
        return gate(
            repo_root,
            remote_name=remote_name,
            remote_url=remote_url,
            stdin_text=input_text,
            skip_verification=args.skip_verification,
            skip_codex=args.skip_codex,
            model=args.model,
            reasoning_effort=args.reasoning_effort,
        )
    except Exception as exc:
        print_status(str(exc))
        print_status("Push blocked.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
