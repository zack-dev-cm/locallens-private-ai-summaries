# Evals

## Rules

- Name the primary verification step before editing.
- Public-surface changes need link, leak, and reviewer-doc checks, not just passing tests.
- Prefer deterministic local checks before any live publish or store submission step.
- If release metadata changes, regenerate the affected manifest or listing output locally.
- If a Chrome Web Store draft is pending review, verify dashboard state before any cancel/resubmit action and record the exact version.

## Required checks

- Python tests: `python3 -m pytest -q`
- Node and route checks: `npm test`
- Launch manifest smoke: `python3 scripts/generate_launch_manifest.py --repo-root . --out /tmp/locallens-launch-manifest.json`
- Listing smoke: `python3 scripts/generate_listing_copy.py --repo-root . --manifest /tmp/locallens-launch-manifest.json --out /tmp/locallens-store-listing.json`
- Extension package smoke when packaging inputs change: `python3 scripts/build_extension_zip.py --extension-dir extension --out /tmp/locallens-extension.zip`
- Reviewer gate before push or resubmission: `python3 scripts/reviewer_gate.py --repo-root . --skip-codex` for local-only smoke, or the full `.githooks/pre-push` path when pushing.

## Quality bar

- Privacy and reviewer docs that lag behind shipped behavior are release blockers.
- Local filesystem paths, unpublished internal URLs, and secret-like strings are OSS blockers.
- Broken support, privacy, or homepage links are product-surface regressions, not doc polish issues.
- Generated outputs in `/tmp` or `dist/` should be disposable verification artifacts unless a release task explicitly needs committed collateral.
- Pending Chrome Web Store reviews are product state. Do not reset them for nonblocking improvements that can ship in the next patch version.
