# LocalLens: Private AI Summaries

Chrome extension for local summaries, simplification, translation, and safe-share cleanup with Chrome built-in AI.

This repo is the product home for LocalLens. It contains the extension source, Chrome Web Store assets, privacy and reviewer docs, and release helpers for packaging the extension.

## What It Does

- summarize the active page locally
- summarize selected text locally
- simplify dense text into plainer language
- translate selected text inside the popup
- create a safe-share brief by masking obvious sensitive strings before local AI processing

## Why This Repo Exists Separately

LocalLens is a user-facing extension product. Its source, policy docs, screenshots, and release notes should not be bundled into an operator-facing publisher skill repo.

## Quick Start

```bash
cd locallens-private-ai-summaries
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

python3 scripts/generate_marketing_assets.py --repo-root .
python3 scripts/build_extension_zip.py --extension-dir extension --out dist/locallens-extension.zip
python3 scripts/generate_launch_manifest.py --repo-root . --out dist/launch-manifest.json
python3 scripts/generate_listing_copy.py --repo-root . --manifest dist/launch-manifest.json --out dist/store-listing.json
python3 scripts/render_release_notes.py --manifest dist/launch-manifest.json --out dist/github-release-notes.md
```

## Release Surface

- extension source: `extension/`
- privacy policy: `docs/privacy-policy.md`
- reviewer instructions: `docs/test-instructions.md`
- marketing assets: `marketing/`
- release helpers: `scripts/`

## License

MIT
