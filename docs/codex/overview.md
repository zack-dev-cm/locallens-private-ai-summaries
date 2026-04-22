# Overview

LocalLens is a user-facing Chrome extension product repo. It includes the extension source, the public support and privacy site, reviewer-facing collateral, and release helpers used to package and publish the extension.

## Product surfaces

- `extension/`: popup UI, built-in AI integrations, and extension manifest assets
- `public_site/`: public support and privacy pages served separately from the extension
- `scripts/`: release helpers for launch manifests, listing copy, screenshots, and ZIP packaging
- `docs/`: public documentation, privacy policy, reviewer instructions, and release notes
- `marketing/`: Chrome Web Store and launch collateral

## Repo landmarks

- Product metadata: `README.md`, `SECURITY.md`, `CONTRIBUTING.md`
- Release collateral: `marketing/`, `dist/`, `docs/`
- Review surfaces: `docs/privacy-policy.md`, `docs/test-instructions.md`
- GitHub automation: `.github/workflows/`, `.github/pull_request_template.md`

## Standard checks

- Python tests: `python3 -m pytest -q`
- Node and route checks: `npm test`
- Launch manifest smoke: `python3 scripts/generate_launch_manifest.py --repo-root . --out /tmp/locallens-launch-manifest.json`
- Listing smoke: `python3 scripts/generate_listing_copy.py --repo-root . --manifest /tmp/locallens-launch-manifest.json --out /tmp/locallens-store-listing.json`

## Non-goals

- This repo is not an internal operator skill or browser-automation bundle.
- It should not hide reviewer-critical product metadata in private notes or unpublished docs.
- Generated release artifacts in `dist/` are not source of truth.
