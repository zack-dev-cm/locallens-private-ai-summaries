from __future__ import annotations

import argparse

from common import dump_text, load_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a portfolio markdown entry from the launch manifest.")
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON.")
    parser.add_argument("--out", required=True, help="Markdown output path.")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    extension = manifest["extension"]
    repo_url = manifest["repo_url"]

    markdown = f"""# {manifest['portfolio']['title']}

> Privacy-first Chrome extension for local AI summaries.

## Summary
`LocalLens` summarizes, simplifies, translates, and safe-shares page text locally with Chrome built-in AI. The product is focused on active-tab reading assistance with minimal permissions and no external inference service.

## Project Link
{manifest['portfolio']['project_link']}

## Key Features
- Local-first page and selection summaries with Chrome built-in AI
- Safe-share mode that redacts obvious sensitive strings before local AI processing
- Minimal extension permissions and no account requirement
- Chrome Web Store-ready privacy policy and reviewer instructions

## Tech Stack
- Chrome Extension (Manifest V3)
- JavaScript
- Python
- GitHub CLI

## Benchmarks & Analytics
- Extension version: {extension['version']}
- Chrome minimum version: {extension['chrome_min_version']}
- Privacy posture: local-only text processing

## Links
- [View on GitHub]({repo_url})
"""
    dump_text(args.out, markdown)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
