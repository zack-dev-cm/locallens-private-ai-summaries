# Chrome Web Store Remediation: Purple Nickel

Date: April 17, 2026

## Rejection

- Item: `LocalLens: Private AI Summaries`
- Item ID: `bgmdmikdapojncddhpabnofcioffnhbg`
- Violation reference: `Purple Nickel`
- Policy area: `User Data Privacy`
- Reviewer note: the privacy-policy link was broken or unavailable

## Root Cause

Two separate problems existed at the same time:

1. The Chrome Web Store listing still had stale public URLs in the dashboard fields instead of the current public Worker URLs.
2. The deployed homepage was generated from repo-facing README sections and leaked internal maintainer copy such as repo separation / publisher rationale.

The second issue made the public surface look unfinished even after the Worker routes were live.

## Fixes

- Redeployed the public site so the official public routes respond:
  - Homepage: `https://locallens-public-site.rapidapis.workers.dev/`
  - Privacy: `https://locallens-public-site.rapidapis.workers.dev/privacy/`
  - Support: `https://locallens-public-site.rapidapis.workers.dev/support/`
- Updated the public-site generator so homepage copy is product-facing only.
- Removed repo-maintainer rationale from the public homepage.
- Removed source-repo promotion from the homepage.
- Switched privacy/support copy toward official public URLs and reviewer-safe wording.
- Added regression checks so the homepage no longer ships instruction bleed.
- Added `homepage_url` to generated listing payloads for dashboard/manual fill workflows.

## Verification

- `GET /` returns `200`
- `GET /privacy/` returns `200`
- `GET /support/` returns `200`
- Public homepage no longer contains:
  - `Why this repo stands alone`
  - internal publisher-tool rationale
  - `View source`

## Dashboard Follow-up

Before resubmission, ensure the Chrome Web Store dashboard fields point to the official public URLs above and save the draft before submitting for review.
