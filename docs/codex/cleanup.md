# Cleanup

LocalLens has multiple public surfaces, so small drift accumulates quickly. This file defines the cleanup bar.

## Regular sweep

- Run a weekly cleanup cadence before release work or after repeated review drift.
- Remove stale generated artifacts and temporary review outputs.
- Prune outdated screenshots, copied release notes, and superseded launch metadata.
- Tighten repeated OSS-review comments into short docs, templates, or deterministic checks.
- Re-check support, privacy, and reviewer-document links after cleanup.

## Promote a rule when

- The same reviewer question appears more than once.
- Release helpers repeatedly depend on one undocumented assumption.
- A stale public doc or screenshot creates a false first-run or review path.

## Do not do

- Broad redesigns under the label of cleanup.
- Hand-edit generated collateral when the source helper should be fixed instead.
- Mix unrelated extension, public-site, and marketing churn into one cleanup patch.
