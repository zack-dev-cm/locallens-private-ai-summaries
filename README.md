# LocalLens: Private AI Summaries

Chrome extension for local summaries, simplification, translation, and safe-share cleanup with Chrome built-in AI.

This repo is the product home for LocalLens. It contains the extension source, Chrome Web Store assets, privacy and reviewer docs, and release helpers for packaging the extension.

## What It Does

- summarize the active page locally
- summarize selected text locally
- simplify dense text into plainer language
- translate selected text inside the popup
- create a safe-share brief by masking obvious sensitive strings before local AI processing

## Product Boundary

LocalLens keeps the extension source, public support site, privacy policy, reviewer instructions, screenshots, and release helpers in one product repository. That keeps Chrome Web Store claims, packaged behavior, and public reviewer links easy to audit together.

## Quick Start

```bash
cd locallens-private-ai-summaries
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -e '.[dev]'

python3 scripts/generate_marketing_assets.py --repo-root .
python3 scripts/build_extension_zip.py --extension-dir extension --out dist/locallens-extension.zip
python3 scripts/generate_launch_manifest.py --repo-root . --out dist/launch-manifest.json
python3 scripts/generate_listing_copy.py --repo-root . --manifest dist/launch-manifest.json --out dist/store-listing.json
python3 scripts/render_release_notes.py --manifest dist/launch-manifest.json --out dist/github-release-notes.md
```

`scripts/generate_marketing_assets.py` currently expects macOS with Google Chrome installed in `/Applications/Google Chrome.app`.

## Release Surface

- extension source: `extension/`
- privacy policy: `docs/privacy-policy.md`
- reviewer instructions: `docs/test-instructions.md`
- marketing assets: `marketing/`
- release helpers: `scripts/`

## Public Pages

- homepage: https://locallens-public-site.rapidapis.workers.dev/
- support: https://locallens-public-site.rapidapis.workers.dev/support/
- privacy policy: https://locallens-public-site.rapidapis.workers.dev/privacy/

These are the current default URLs baked into the release helpers. Override them with `LOCALLENS_PUBLIC_SITE_BASE` only if you redeploy the Worker to a different public hostname.

## Cloudflare Worker Publish

The public support and privacy surface is now implemented as a Cloudflare Worker in `public_site/`.

```bash
npm install
npm run deploy:public-site
export LOCALLENS_PUBLIC_SITE_BASE="https://locallens-public-site.rapidapis.workers.dev"
python3 scripts/generate_launch_manifest.py --repo-root . --out dist/launch-manifest.json
python3 scripts/generate_listing_copy.py --repo-root . --manifest dist/launch-manifest.json --out dist/store-listing.json
```

Set `LOCALLENS_PUBLIC_SITE_BASE` before regenerating store metadata only when you are moving to a different Worker hostname than the current production default.

## Security

Report suspected privacy, packaging, or release-surface issues privately through [SECURITY.md](SECURITY.md) instead of opening a public issue first.

## License

MIT
