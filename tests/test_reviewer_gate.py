from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import reviewer_gate  # noqa: E402


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "commit.gpgsign", "false")
    return repo


def commit_file(repo: Path, name: str, content: str, message: str) -> str:
    path = repo / name
    path.write_text(content, encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def test_parse_push_targets_reads_git_hook_lines() -> None:
    payload = reviewer_gate.parse_push_targets(
        "refs/heads/main abcdef refs/heads/main 123456\n"
        "refs/heads/topic fedcba refs/heads/topic 654321\n"
    )

    assert payload == [
        reviewer_gate.PushTarget("refs/heads/main", "abcdef", "refs/heads/main", "123456"),
        reviewer_gate.PushTarget("refs/heads/topic", "fedcba", "refs/heads/topic", "654321"),
    ]


def test_build_review_ranges_uses_remote_sha_for_existing_remote_update(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base_sha = commit_file(repo, "tracked.txt", "one\n", "base")
    head_sha = commit_file(repo, "tracked.txt", "one\ntwo\n", "head")
    target = reviewer_gate.PushTarget(
        local_ref="refs/heads/main",
        local_sha=head_sha,
        remote_ref="refs/heads/main",
        remote_sha=base_sha,
    )

    review_ranges = reviewer_gate.build_review_ranges(repo, "origin", [target])

    assert len(review_ranges) == 1
    review_range = review_ranges[0]
    assert review_range.base_sha == base_sha
    assert review_range.head_sha == head_sha
    assert review_range.files == ("tracked.txt",)


def test_build_review_ranges_uses_default_branch_merge_base_for_new_remote_branch(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    base_sha = commit_file(repo, "tracked.txt", "one\n", "base")
    git(repo, "update-ref", "refs/remotes/origin/main", base_sha)
    git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    git(repo, "checkout", "-b", "feature")
    head_sha = commit_file(repo, "feature.txt", "branch\n", "feature")
    target = reviewer_gate.PushTarget(
        local_ref="refs/heads/feature",
        local_sha=head_sha,
        remote_ref="refs/heads/feature",
        remote_sha=reviewer_gate.ZERO_SHA,
    )

    review_ranges = reviewer_gate.build_review_ranges(repo, "origin", [target])

    assert len(review_ranges) == 1
    review_range = review_ranges[0]
    assert review_range.base_sha == base_sha
    assert review_range.head_sha == head_sha
    assert review_range.files == ("feature.txt",)


def test_run_codex_review_uses_required_codex_flags(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    captured_output_path: Path | None = None

    monkeypatch.setattr(
        reviewer_gate,
        "prepare_isolated_codex_home",
        lambda _tmp, _repo: {"CODEX_HOME": str(tmp_path / "codex-home")},
    )
    monkeypatch.setattr(reviewer_gate, "ensure_codex_available", lambda _env: None)

    def fake_run_process(command, *, cwd, input_text=None, timeout=None, env=None):
        nonlocal captured_output_path
        assert cwd == repo
        assert command[0:4] == ("codex", "--ask-for-approval", "never", "exec")
        assert command[command.index("--model") + 1] == "gpt-5.4"
        assert command[command.index("--sandbox") + 1] == "read-only"
        assert 'model_reasoning_effort="xhigh"' in command
        assert "features.multi_agent=true" in command
        assert input_text is None
        assert "review-context" in command[-1]
        assert timeout == 900
        assert env == {"CODEX_HOME": str(tmp_path / "codex-home")}
        captured_output_path = Path(command[command.index("--output-last-message") + 1])
        captured_output_path.write_text(
            json.dumps({"status": "approved", "summary": "clean", "findings": []}),
            encoding="utf-8",
        )
        return reviewer_gate.CommandResult(tuple(command), 0, "", "")

    monkeypatch.setattr(reviewer_gate, "run_process", fake_run_process)

    result = reviewer_gate.run_codex_review(
        repo,
        context="review-context",
        model="gpt-5.4",
        reasoning_effort="xhigh",
    )

    assert captured_output_path is not None
    assert result.status == "approved"
    assert result.summary == "clean"
    assert result.findings == ()


def test_review_prompt_requires_extension_and_cws_review_agents() -> None:
    assert "extension-runtime-reviewer" in reviewer_gate.REVIEW_PROMPT
    assert "cws-policy-reviewer" in reviewer_gate.REVIEW_PROMPT
    assert "chrome.scripting.executeScript" in reviewer_gate.REVIEW_PROMPT
    assert "feature claim" in reviewer_gate.REVIEW_PROMPT


def test_parse_codex_review_rejects_approved_result_with_findings() -> None:
    payload = json.dumps(
        {
            "status": "approved",
            "summary": "looks clean",
            "findings": [
                {
                    "severity": "high",
                    "title": "Still broken",
                    "details": "The response is internally inconsistent.",
                    "file": "extension/popup.js",
                }
            ],
        }
    )

    try:
        reviewer_gate.parse_codex_review(payload)
    except ValueError as exc:
        assert "status=approved with blocking findings" in str(exc)
    else:
        raise AssertionError("expected inconsistent approved review to be rejected")


def test_run_local_verification_builds_and_inspects_extension_zip(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    calls: list[tuple[str, ...]] = []

    monkeypatch.setattr(reviewer_gate, "tracked_python_targets", lambda _repo: [])
    monkeypatch.setattr(reviewer_gate, "tracked", lambda _repo, _path: False)
    monkeypatch.setattr(reviewer_gate, "python_module_available", lambda _repo, _module: False)

    def fake_run_process(command, *, cwd, input_text=None, timeout=None, env=None):
        calls.append(tuple(str(part) for part in command))
        return reviewer_gate.CommandResult(tuple(str(part) for part in command), 0, "", "")

    monkeypatch.setattr(reviewer_gate, "run_process", fake_run_process)

    reviewer_gate.run_local_verification(repo)

    assert any("scripts/build_extension_zip.py" in command for call in calls for command in call)
    assert any("-c" in call and reviewer_gate.ZIP_SANITY_SCRIPT in call for call in calls)


def test_run_codex_review_falls_back_when_xhigh_is_unsupported(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    calls: list[tuple[str, ...]] = []
    output_path: Path | None = None

    monkeypatch.setattr(
        reviewer_gate,
        "prepare_isolated_codex_home",
        lambda _tmp, _repo: {"CODEX_HOME": str(tmp_path / "codex-home")},
    )
    monkeypatch.setattr(reviewer_gate, "ensure_codex_available", lambda _env: None)

    def fake_run_process(command, *, cwd, input_text=None, timeout=None, env=None):
        nonlocal output_path
        calls.append(tuple(command))
        output_path = Path(command[command.index("--output-last-message") + 1])
        if len(calls) == 1:
            return reviewer_gate.CommandResult(
                tuple(command),
                1,
                "",
                "unknown variant `xhigh`, expected one of `minimal`, `low`, `medium`, `high`",
            )
        output_path.write_text(
            json.dumps({"status": "approved", "summary": "clean", "findings": []}),
            encoding="utf-8",
        )
        return reviewer_gate.CommandResult(tuple(command), 0, "", "")

    monkeypatch.setattr(reviewer_gate, "run_process", fake_run_process)

    result = reviewer_gate.run_codex_review(
        repo,
        context="review-context",
        model="gpt-5.4",
        reasoning_effort="xhigh",
    )

    assert len(calls) == 2
    assert 'model_reasoning_effort="xhigh"' in calls[0]
    assert 'model_reasoning_effort="high"' in calls[1]
    assert output_path is not None
    assert result.status == "approved"


def test_run_process_uses_single_subprocess_when_input_text_is_supplied(
    tmp_path: Path, monkeypatch
) -> None:
    repo = init_repo(tmp_path)
    calls: list[tuple[str, ...]] = []

    def fake_common_run(*args, **kwargs):
        raise AssertionError("common.run should not be used when input_text is provided")

    def fake_subprocess_run(command, **kwargs):
        calls.append(tuple(command))
        assert kwargs["cwd"] == str(repo)
        assert kwargs["input"] == "review-context"
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(reviewer_gate, "run", fake_common_run)
    monkeypatch.setattr(reviewer_gate.subprocess, "run", fake_subprocess_run)

    result = reviewer_gate.run_process(
        ("codex", "exec", "review"),
        cwd=repo,
        input_text="review-context",
        timeout=30,
        env={"CODEX_HOME": str(tmp_path / "codex-home")},
    )

    assert calls == [("codex", "exec", "review")]
    assert result.ok
    assert result.stdout == "ok\n"


def test_main_blocks_when_verification_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setattr(reviewer_gate, "build_review_ranges", lambda *_args, **_kwargs: [
        reviewer_gate.ReviewRange("refs/heads/main", "refs/heads/main", "base", "head", ("tracked.txt",))
    ])
    monkeypatch.setattr(
        reviewer_gate,
        "run_local_verification",
        lambda _repo: [reviewer_gate.CommandResult((sys.executable, "-m", "pytest", "-q"), 1, "", "boom\n")],
    )
    monkeypatch.setattr(
        reviewer_gate,
        "run_codex_review",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("Codex review should be skipped")),
    )
    monkeypatch.setattr(
        reviewer_gate,
        "render_diff_context",
        lambda *_args, **_kwargs: "## Unified Diff\n+ change",
    )

    exit_code = reviewer_gate.main(
        ["--repo-root", str(repo), "--remote-name", "origin", "--remote-url", "https://example.com/repo.git"],
        "refs/heads/main head refs/heads/main base\n",
    )

    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "pytest -q failed." in stderr
    assert "Skipping Codex review because local verification failed." in stderr
    assert "Push blocked." in stderr


def test_main_blocks_when_codex_requests_changes(tmp_path: Path, monkeypatch, capsys) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setattr(reviewer_gate, "build_review_ranges", lambda *_args, **_kwargs: [
        reviewer_gate.ReviewRange("refs/heads/main", "refs/heads/main", "base", "head", ("tracked.txt",))
    ])
    monkeypatch.setattr(
        reviewer_gate,
        "run_local_verification",
        lambda _repo: [reviewer_gate.CommandResult((sys.executable, "-m", "pytest", "-q"), 0, "", "")],
    )
    monkeypatch.setattr(
        reviewer_gate,
        "run_codex_review",
        lambda *args, **kwargs: reviewer_gate.CodexReviewResult(
            "changes_requested",
            "found issues",
            (
                {
                    "severity": "high",
                    "title": "Broken flow",
                    "details": "The change would fail in production.",
                    "file": "extension/popup.js",
                    "line": 17,
                },
            ),
        ),
    )
    monkeypatch.setattr(
        reviewer_gate,
        "render_diff_context",
        lambda *_args, **_kwargs: "## Unified Diff\n+ change",
    )

    exit_code = reviewer_gate.main(
        ["--repo-root", str(repo), "--remote-name", "origin", "--remote-url", "https://example.com/repo.git"],
        "refs/heads/main head refs/heads/main base\n",
    )

    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "HIGH extension/popup.js:17 - Broken flow" in stderr
    assert "Push blocked." in stderr


def test_main_passes_when_verification_and_codex_pass(tmp_path: Path, monkeypatch, capsys) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setattr(reviewer_gate, "build_review_ranges", lambda *_args, **_kwargs: [
        reviewer_gate.ReviewRange("refs/heads/main", "refs/heads/main", "base", "head", ("tracked.txt",))
    ])
    monkeypatch.setattr(
        reviewer_gate,
        "run_local_verification",
        lambda _repo: [reviewer_gate.CommandResult((sys.executable, "-m", "pytest", "-q"), 0, "", "")],
    )
    monkeypatch.setattr(
        reviewer_gate,
        "run_codex_review",
        lambda *args, **kwargs: reviewer_gate.CodexReviewResult("approved", "clean", ()),
    )
    monkeypatch.setattr(
        reviewer_gate,
        "render_diff_context",
        lambda *_args, **_kwargs: "## Unified Diff\n+ change",
    )

    exit_code = reviewer_gate.main(
        ["--repo-root", str(repo), "--remote-name", "origin", "--remote-url", "https://example.com/repo.git"],
        "refs/heads/main head refs/heads/main base\n",
    )

    assert exit_code == 0
    stderr = capsys.readouterr().err
    assert "Push approved." in stderr
