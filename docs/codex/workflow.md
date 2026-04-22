# Workflow

## Default loop

1. Clarify which product surface is changing: extension, public site, release helper, or review collateral.
2. Read the smallest relevant code and docs before editing.
3. Implement the smallest durable change.
4. Review for correctness, regressions, secrets, stale URLs, and OSS bleed.
5. Run the highest-signal local checks for the surfaces touched.
6. Update public docs when the shipped behavior, release metadata, or reviewer guidance changes.

## Open-source prep loop

1. Keep repo metadata current: `README.md`, `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, and the PR template.
2. Keep reviewer-critical docs current: privacy policy, reviewer instructions, and public-site URLs.
3. Remove local paths, copied internal links, stale screenshots, and outdated release artifacts.
4. Rebuild launch metadata from tracked source before claiming a release surface is ready.
5. Treat public-site pages and extension docs as part of one public product story even though they deploy separately.
6. If a Chrome Web Store draft is already pending review, use [Chrome Web Store Release Strategy](cws-release-strategy.md) before deciding whether to cancel or resubmit.

## Chrome Web Store Pending Review

For the active Red Potassium remediation, `0.1.5` is the submitted package. Leave it in review unless the dashboard shows a rejection, broken public reviewer URL, wrong package, or another verified acceptance blocker.

Queue nonblocking hardening for `0.1.6` after `0.1.5` reaches production. Do not reset the Chrome Web Store review queue just to include local cleanup that is not required for acceptance.

## When to use which agent

- `architect`: ambiguous scope, metadata boundaries, or review-surface decisions
- `implementer`: focused code or docs patches with minimal churn
- `reviewer`: bug, security, leak, and public-surface review
- `extension-runtime-reviewer`: Chrome extension runtime, MV3 injection, popup action, and built-in AI behavior review
- `cws-policy-reviewer`: Chrome Web Store listing, reviewer-instruction, support-link, privacy, and resubmission review
- `evolver`: measured tuning of launch copy, release heuristics, or collateral wording
- `cleanup`: stale artifact cleanup and repeated reviewer feedback reduction
