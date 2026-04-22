from __future__ import annotations

import json
import subprocess
import sys
import time
import zipfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_extension_zip import should_package  # noqa: E402
from generate_launch_manifest import build_launch_manifest  # noqa: E402
from generate_listing_copy import build_listing_payload  # noqa: E402
from generate_marketing_assets import asset_is_fresh  # noqa: E402


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def test_asset_is_fresh_tracks_source_updates(tmp_path: Path) -> None:
    source = tmp_path / "marketing.html"
    css = tmp_path / "marketing.css"
    output = tmp_path / "out.png"
    source.write_text("<html></html>", encoding="utf-8")
    css.write_text("body{}", encoding="utf-8")
    output.write_text("png", encoding="utf-8")
    assert asset_is_fresh(output, [source, css]) is True

    time.sleep(0.01)
    css.write_text("body{color:red;}", encoding="utf-8")
    assert asset_is_fresh(output, [source, css]) is False


def test_build_launch_manifest_points_to_locallens_repo(tmp_path: Path) -> None:
    repo_root = tmp_path / "locallens-private-ai-summaries"
    extension_dir = repo_root / "extension"
    extension_dir.mkdir(parents=True)
    (extension_dir / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "LocalLens: Private AI Summaries",
                "version": "0.1.3",
                "description": "Sample description",
            }
        ),
        encoding="utf-8",
    )

    payload = build_launch_manifest(repo_root)
    assert payload["repo_url"] == "https://github.com/zack-dev-cm/locallens-private-ai-summaries"
    assert payload["homepage_url"] == "https://locallens-public-site.rapidapis.workers.dev/"
    assert payload["support_url"] == "https://locallens-public-site.rapidapis.workers.dev/support/"
    assert payload["privacy_policy_url"] == "https://locallens-public-site.rapidapis.workers.dev/privacy/"
    assert (
        payload["test_instructions_url"]
        == "https://locallens-public-site.rapidapis.workers.dev/support/#reviewer-checklist"
    )
    assert payload["portfolio"]["project_link"] == "https://locallens-public-site.rapidapis.workers.dev/"


def test_build_listing_payload_uses_repo_links(tmp_path: Path) -> None:
    repo_root = tmp_path / "locallens-private-ai-summaries"
    extension_dir = repo_root / "extension"
    extension_dir.mkdir(parents=True)
    (extension_dir / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "LocalLens: Private AI Summaries",
                "version": "0.1.3",
                "description": "Sample description",
                "permissions": ["activeTab", "scripting"],
            }
        ),
        encoding="utf-8",
    )

    launch_manifest = build_launch_manifest(repo_root)
    payload = build_listing_payload(repo_root, launch_manifest)

    assert payload["privacy"]["privacy_policy_url"] == launch_manifest["privacy_policy_url"]
    assert payload["support_url"] == launch_manifest["support_url"]
    assert set(payload["privacy"]["permission_justifications"]) == {"activeTab", "scripting"}
    assert payload["store_assets"]["icon"] == "extension/icons/icon128.png"
    assert payload["store_assets"]["screenshots"] == [
        "dist/store-assets/locallens-store-screenshot-1.png",
        "dist/store-assets/locallens-store-screenshot-2.jpg",
    ]
    reviewer_instructions = "\n".join(payload["reviewer_instructions"])
    assert "Translator: unavailable" in reviewer_instructions
    assert "leave Translate to Spanish" in reviewer_instructions
    assert "Translate selection" in reviewer_instructions
    assert Path(payload["store_assets"]["icon"]).is_absolute() is False


def test_extension_zip_excludes_test_only_files(tmp_path: Path) -> None:
    extension_dir = tmp_path / "extension"
    extension_dir.mkdir()
    (extension_dir / "manifest.json").write_text('{"name":"LocalLens"}\n', encoding="utf-8")
    (extension_dir / "popup.js").write_text("console.log('ok');\n", encoding="utf-8")
    (extension_dir / "popup-helpers.js").write_text("export const helper = true;\n", encoding="utf-8")
    (extension_dir / "popup-helpers.test.js").write_text("test('x', () => {});\n", encoding="utf-8")
    out_path = tmp_path / "locallens-extension.zip"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "build_extension_zip.py"),
            "--extension-dir",
            str(extension_dir),
            "--out",
            str(out_path),
        ],
        check=True,
    )

    with zipfile.ZipFile(out_path) as archive:
        names = sorted(archive.namelist())

    assert names == ["manifest.json", "popup-helpers.js", "popup.js"]
    assert should_package(extension_dir / "popup.js", extension_dir) is True
    assert should_package(extension_dir / "popup-helpers.js", extension_dir) is True
    assert should_package(extension_dir / "popup-helpers.test.js", extension_dir) is False


def test_build_launch_manifest_uses_public_site_override(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "locallens-private-ai-summaries"
    extension_dir = repo_root / "extension"
    extension_dir.mkdir(parents=True)
    (extension_dir / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "LocalLens: Private AI Summaries",
                "version": "0.1.3",
                "description": "Sample description",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LOCALLENS_PUBLIC_SITE_BASE", "https://locallens-public-site.example.workers.dev")

    payload = build_launch_manifest(repo_root)

    assert payload["homepage_url"] == "https://locallens-public-site.example.workers.dev/"
    assert payload["support_url"] == "https://locallens-public-site.example.workers.dev/support/"
    assert payload["privacy_policy_url"] == "https://locallens-public-site.example.workers.dev/privacy/"
    assert (
        payload["test_instructions_url"]
        == "https://locallens-public-site.example.workers.dev/support/#reviewer-checklist"
    )


def test_build_launch_manifest_prefers_origin_remote_over_folder_name(tmp_path: Path) -> None:
    repo_root = tmp_path / "renamed-worktree"
    extension_dir = repo_root / "extension"
    extension_dir.mkdir(parents=True)
    (extension_dir / "manifest.json").write_text(
        json.dumps(
            {
                "manifest_version": 3,
                "name": "LocalLens: Private AI Summaries",
                "version": "0.1.3",
                "description": "Sample description",
            }
        ),
        encoding="utf-8",
    )
    git(repo_root, "init", "-b", "main")
    git(repo_root, "remote", "add", "origin", "https://github.com/zack-dev-cm/locallens-private-ai-summaries.git")

    payload = build_launch_manifest(repo_root)

    assert payload["repo_url"] == "https://github.com/zack-dev-cm/locallens-private-ai-summaries"


def test_dev_dependencies_include_playwright_for_marketing_assets() -> None:
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert 'playwright>=' in pyproject


def test_readme_uses_public_product_boundary_language() -> None:
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "Product Boundary" in readme
    assert "operator-facing" not in readme
    assert "publisher " + "skill" not in readme


def test_cws_release_strategy_preserves_pending_review_boundary() -> None:
    root = Path(__file__).resolve().parents[1]
    strategy = (root / "docs" / "codex" / "cws-release-strategy.md").read_text(encoding="utf-8")
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    pre_push = (root / ".githooks" / "pre-push").read_text(encoding="utf-8")

    assert "0.1.5" in strategy
    assert "0.1.6" in strategy
    assert "Do not reset the review queue" in strategy
    assert "scripts/reviewer_gate.py" in strategy
    assert "Post-submit worktree changes are not part of submitted `0.1.5`" in strategy
    assert "queued `0.1.6` work" in strategy
    assert "Do not cancel or replace a Chrome Web Store draft" in agents
    assert "--skip-codex" in pre_push
    assert "full reviewer gate without `--skip-codex`" in strategy
