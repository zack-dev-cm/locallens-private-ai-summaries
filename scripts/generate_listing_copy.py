from __future__ import annotations

import argparse
from pathlib import Path

from common import abs_path, dump_json, load_json


CERTIFICATIONS = [
    "I do not sell or transfer user data to third parties, outside of the approved use cases",
    "I do not use or transfer user data for purposes that are unrelated to my item's single purpose",
    "I do not use or transfer user data to determine creditworthiness or for lending purposes",
]


def build_permission_justifications(permissions: list[str]) -> dict[str, str]:
    templates = {
        "activeTab": (
            "LocalLens requests temporary access to the current tab only after the user clicks an action, "
            "so it can read the page title, page URL, and visible text that the user wants summarized, "
            "translated, simplified, or rewritten."
        ),
        "scripting": (
            "LocalLens injects a short on-page function into the active tab at request time so it can extract "
            "either the readable page text or the user's current selection without persistent host access."
        ),
        "storage": (
            "LocalLens stores only user-facing preferences that are needed to keep the popup consistent across uses."
        ),
    }
    return {permission: templates[permission] for permission in permissions if permission in templates}


def build_listing_payload(repo_root: Path, launch_manifest: dict) -> dict:
    permissions = load_json(repo_root / "extension" / "manifest.json").get("permissions", [])
    permission_justifications = build_permission_justifications(permissions)
    return {
        "name": launch_manifest["extension"]["name"],
        "short_description": "Local summaries, simplification, translation, and safe-share cleanup for the active tab using Chrome built-in AI.",
        "detailed_description": (
            "LocalLens helps you move through dense pages faster without routing tab text to an external server.\n\n"
            "What it does:\n"
            "- Summarizes the current page into useful key points\n"
            "- Summarizes selected text for fast scanning\n"
            "- Simplifies dense writing into plainer language\n"
            "- Translates selected text inside the popup\n"
            "- Creates safe-share briefs by masking obvious sensitive strings before local AI processing\n\n"
            "Why people use it:\n"
            "- No account or API key\n"
            "- Active-tab only workflow\n"
            "- Minimal permissions\n"
            "- No background scraping or host permissions\n"
            "- Built for privacy-sensitive reading and collaboration workflows\n\n"
            "Technical note:\n"
            "LocalLens targets Chrome 138+ with built-in AI support. If your browser has not downloaded the local model yet, Chrome may need a short warm-up download on first use."
        ),
        "category": "Tools",
        "language": "English",
        "single_purpose": (
            "Turn page or selected text from the active tab into local summaries, simplified rewrites, translations, or safe-share briefs with Chrome built-in AI."
        ),
        "privacy": {
            "stores_data": "No",
            "sells_data": "No",
            "shares_data": "No",
            "uses_external_servers": "No",
            "justification": (
                "LocalLens reads website content from the active tab only after an explicit click. The extension "
                "processes that content locally with Chrome built-in AI and does not transmit page text, selections, "
                "or generated output to the developer."
            ),
            "permission_justifications": permission_justifications,
            "remote_code": False,
            "data_categories": ["Website content"],
            "privacy_policy_url": launch_manifest["privacy_policy_url"],
            "certifications": CERTIFICATIONS,
        },
        "support_url": launch_manifest["support_url"],
        "reviewer_instructions": [
            "Use Chrome 138+ on desktop with built-in AI enabled.",
            "Open a text-heavy page, click the LocalLens action, and run Summarize page.",
            "Highlight text on a page, then run Summarize selection, Simplify selection, Translate selection, and Safe-share selection.",
            "If Chrome downloads a local model on first use, wait for the progress indicator in the popup to finish and rerun the action.",
        ],
        "store_assets": {
            "icon": str(repo_root / "extension" / "icons" / "icon128.png"),
            "screenshots": [
                str(repo_root / "dist" / "store-assets" / "locallens-store-screenshot-1.png"),
                str(repo_root / "dist" / "store-assets" / "locallens-store-screenshot-2.jpg"),
            ],
            "promo_small": str(repo_root / "dist" / "store-assets" / "locallens-promo-small.png"),
            "promo_marquee": str(repo_root / "dist" / "store-assets" / "locallens-promo-marquee.jpg"),
        },
        "keywords": [
            "ai summary",
            "private summary",
            "local ai",
            "page summary",
            "translate text",
            "safe share",
            "chrome built-in ai",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Chrome Web Store listing copy and metadata.")
    parser.add_argument("--repo-root", default=".", help="Project root.")
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    args = parser.parse_args()

    repo_root = abs_path(args.repo_root)
    launch_manifest = load_json(args.manifest)

    payload = build_listing_payload(repo_root, launch_manifest)
    dump_json(args.out, payload)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
