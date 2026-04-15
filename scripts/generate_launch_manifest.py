from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import abs_path, dump_json, slugify


PUBLIC_SITE_SLUG = "locallens"
PUBLIC_SITE_BASE = f"https://zack-dev-cm.github.io/{PUBLIC_SITE_SLUG}/"


def build_launch_manifest(repo_root: Path) -> dict:
    manifest = json.loads((repo_root / "extension" / "manifest.json").read_text(encoding="utf-8"))
    repo_name = repo_root.name
    extension_name = manifest["name"]
    repo_url = f"https://github.com/zack-dev-cm/{repo_name}"
    project_slug = slugify(extension_name)
    homepage_url = PUBLIC_SITE_BASE
    support_url = f"{PUBLIC_SITE_BASE}support/"
    privacy_policy_url = f"{PUBLIC_SITE_BASE}privacy/"
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
