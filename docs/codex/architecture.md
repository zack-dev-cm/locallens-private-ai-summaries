# Architecture

## Boundaries

- `extension/`: user-facing Chrome extension code and packaging inputs
- `public_site/`: public support and privacy surface, deployed separately from the extension bundle
- `scripts/`: deterministic release helpers that turn repo content into manifests, store copy, and ZIP outputs
- `docs/`: public-facing policy, reviewer, and release documentation
- `marketing/`: screenshots and promotional collateral for launch and store review

## Shared design rules

- Keep extension behavior, public-site publishing, and release-helper logic explicit instead of hidden behind one broad pipeline.
- Treat privacy policy, reviewer instructions, support URLs, and homepage URLs as release metadata, not optional docs.
- Use `LOCALLENS_PUBLIC_SITE_BASE` only when the deployed public hostname changes.
- Keep generated `dist/` artifacts reproducible from tracked source rather than hand-edited.

## Do-not-break list

- The repo remains a user-facing Chrome extension product first.
- Public links point to the LocalLens support and privacy surface, not private docs.
- `docs/privacy-policy.md` and `docs/test-instructions.md` stay aligned with the shipped extension behavior.
- Release helpers continue to work from repo-native inputs without hidden workstation-specific dependencies beyond what the docs already call out.
