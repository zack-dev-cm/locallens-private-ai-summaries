# Contributing

## What belongs here

This repository is the product home for LocalLens. Contributions should keep the repo positioned as a user-facing Chrome extension product with:

- extension source in `extension/`
- public support and privacy pages in `public_site/`
- release helpers in `scripts/`
- reviewer and policy docs in `docs/`

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -e '.[dev]'
npm install
```

## Default verification

Run the smallest set that covers your change:

- `python3 -m pytest -q`
- `npm test`
- `python3 scripts/generate_launch_manifest.py --repo-root . --out /tmp/locallens-launch-manifest.json`
- `python3 scripts/generate_listing_copy.py --repo-root . --manifest /tmp/locallens-launch-manifest.json --out /tmp/locallens-store-listing.json`
- `python3 scripts/build_extension_zip.py --extension-dir extension --out /tmp/locallens-extension.zip` when packaging inputs change
- `python3 scripts/reviewer_gate.py --repo-root . --skip-codex` for a local reviewer-gate smoke before release-collateral pushes

Enable the push-time reviewer gate once per clone:

```bash
git config core.hooksPath .githooks
```

The full hook runs local verification and a read-only Codex reviewer pass. Treat a hook failure as a release blocker until it is understood.

## Contribution rules

- Keep diffs surgical and avoid mixing extension, public-site, and release-collateral rewrites without a clear reason.
- Keep privacy policy and reviewer instructions aligned with the shipped extension experience.
- Do not commit generated `dist/` outputs unless the task explicitly asks for release artifacts.
- Do not add private URLs, local filesystem paths, or secret-like values to tracked files.
- Do not cancel a Chrome Web Store draft that is already pending review unless the change fixes a verified acceptance blocker in that submitted package.

## Pull requests

- Explain which product surface changed.
- List the verification you ran.
- Call out any reviewer-doc, privacy-doc, or public-link changes explicitly.
