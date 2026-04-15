from __future__ import annotations

import argparse

from common import dump_text, load_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Render concise GitHub release notes from the launch manifest.")
    parser.add_argument("--manifest", required=True, help="Launch manifest JSON.")
    parser.add_argument("--out", required=True, help="Markdown output path.")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    extension = manifest["extension"]

    text = f"""# {manifest['release']['title']}

## What shipped

- `LocalLens` Chrome extension v{extension['version']}
- Chrome Web Store package and reviewer-ready support documents
- Store assets, privacy copy, and GitHub release collateral

## Product position

LocalLens is a privacy-first Chrome extension that summarizes, simplifies, translates, and safe-shares active-tab text with Chrome built-in AI.

## Notes

- No external inference server required
- Minimal extension permissions
- Release includes packaging and listing helpers for repeatable future updates
"""
    dump_text(args.out, text)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
