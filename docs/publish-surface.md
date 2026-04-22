# Publish Surface Checklist

Use this checklist before treating `dist/` as a release-ready bundle.

## Canonical outputs

- `dist/locallens-extension.zip`
- `dist/launch-manifest.json`
- `dist/store-listing.json`
- `dist/github-release-notes.md`
- `dist/cws-resubmission.md`
- `dist/store-assets/`

## Required checks

- The packaged extension ZIP excludes test-only files such as `*.test.js`.
- Generated listing metadata uses repo-relative asset paths, not workstation-local absolute paths.
- Support, privacy, and reviewer URLs all point at the current public site base.
- `dist/` does not contain duplicate or legacy release aliases that disagree about the canonical bundle.
- Generated reviewer notes and release commands reference files that actually exist in `dist/`.

## If a check fails

- Regenerate the affected artifact from the repo scripts before release.
- Remove stale duplicate files from `dist/` instead of keeping multiple conflicting variants.
- Do not present the bundle as reviewer-ready until the canonical outputs agree with each other.
