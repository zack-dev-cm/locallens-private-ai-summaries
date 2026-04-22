from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from common import abs_path, dump_json, slugify


PUBLIC_SITE_SLUG = "locallens"
DEFAULT_PUBLIC_SITE_BASE = "https://locallens-public-site.rapidapis.workers.dev/"
GITHUB_REMOTE_RE = re.compile(
    r"^(?:git@github\.com:|https://github\.com/)(?P<slug>[^/\s]+/[^/\s]+?)(?:\.git)?$"
)


def public_site_base() -> str:
    override = os.environ.get("LOCALLENS_PUBLIC_SITE_BASE", "").strip()
    if override:
        return override.rstrip("/") + "/"
    return DEFAULT_PUBLIC_SITE_BASE


def canonical_repo_url(repo_root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except Exception:
        completed = None

    if completed and completed.returncode == 0:
        remote = completed.stdout.strip()
        match = GITHUB_REMOTE_RE.match(remote)
        if match:
            return f"https://github.com/{match.group('slug')}"

    return f"https://github.com/zack-dev-cm/{repo_root.name}"


def build_launch_manifest(repo_root: Path) -> dict:
    manifest = json.loads((repo_root / "extension" / "manifest.json").read_text(encoding="utf-8"))
    repo_name = repo_root.name
    extension_name = manifest["name"]
    repo_url = canonical_repo_url(repo_root)
    project_slug = slugify(extension_name)
    public_base = public_site_base()
    homepage_url = public_base
    support_url = f"{public_base}support/"
    privacy_policy_url = f"{public_base}privacy/"
    test_instructions_url = f"{support_url}#reviewer-checklist"
    return {
        "repo_name": repo_name,
        "repo_url": repo_url,
        "homepage_url": homepage_url,
        "github_description": "Chrome extension for local summaries, simplification, translation, and safe-share cleanup with Chrome built-in AI.",
        "github_homepage": homepage_url,
        "support_url": support_url,
        "privacy_policy_url": privacy_policy_url,
        "test_instructions_url": test_instructions_url,
        "github_topics": [
            "chrome-extension",
            "chrome-web-store",
            "built-in-ai",
            "privacy",
            "summarization",
        ],
        "extension": {
            "name": extension_name,
            "version": manifest["version"],
            "summary": manifest["description"],
            "category": "Tools",
            "chrome_min_version": manifest.get("minimum_chrome_version", ""),
        },
        "portfolio": {
            "title": extension_name,
            "slug": project_slug,
            "project_link": homepage_url,
        },
        "release": {
            "tag": f"v{manifest['version']}",
            "title": f"Release {extension_name} v{manifest['version']}",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LocalLens release metadata for GitHub, store docs, and portfolio sync.")
    parser.add_argument("--repo-root", default=".", help="Project root.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    args = parser.parse_args()

    repo_root = abs_path(args.repo_root)
    payload = build_launch_manifest(repo_root)
    dump_json(args.out, payload)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
