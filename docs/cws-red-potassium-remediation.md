# Chrome Web Store Remediation: Red Potassium

Date: April 22, 2026

## Rejection

- Item: `LocalLens: Private AI Summaries`
- Item ID: `bgmdmikdapojncddhpabnofcioffnhbg`
- Violation reference: `Red Potassium`
- Policy area: inaccurate description / non-functional claim
- Reviewer note: `Translate Selection` was listed but was not working or reproducible in review.

## Root Cause

`Translate selection` used the same selection capture path as the other selection actions. The popup injected `extractSelectionContext()` with `chrome.scripting.executeScript`, but that injected function called `extractSelectionContextFromPage`, an imported popup-module helper that is not available inside the page execution context.

That made the selection action path depend on popup-module closure state instead of a self-contained MV3 injected function.

## Fixes

- Added `extractSelectionContextFromCurrentPage()` as a self-contained function safe to inject with `chrome.scripting.executeScript`.
- Switched popup selection actions, including `Translate selection`, to inject the self-contained selector.
- Moved `Translate selection` from a generic Prompt API instruction to Chrome's dedicated `Translator` API, with language detection fallback and Spanish as the default target for reviewer reproducibility.
- Added regression coverage for page selections and focused text-area selections in the injected context.
- Added Chrome runtime and Chrome Web Store policy reviewer agents for future submission review.
- Tightened reviewer instructions to include a concrete `Translate selection` check.
- Bumped the extension package version to `0.1.4` for the first resubmission.
- After real Chrome E2E, tightened the popup compact layout so `Translate selection` is visible without scrolling in the default Chrome extension popup viewport, then bumped the submitted package to `0.1.5`.

## Verification

- `npm test`
- `python3 -m pytest -q`
- `python3 -m py_compile scripts/*.py tests/*.py`
- `python3 scripts/build_extension_zip.py --extension-dir extension --out /tmp/locallens-extension-red-potassium-0.1.5.zip`
- `python3 scripts/generate_launch_manifest.py --repo-root . --out /tmp/locallens-launch-manifest-0.1.5.json`
- `python3 scripts/generate_listing_copy.py --repo-root . --manifest /tmp/locallens-launch-manifest-0.1.5.json --out /tmp/locallens-store-listing-0.1.5.json`
- `python3 -m codex_harness audit . --strict --min-score 90`
- Real Chrome 147 E2E: installed the unpacked `0.1.5` extension, selected page text, opened the action popup, confirmed `Translate selection` was visible without scrolling, and translated the selection to Spanish.

## Dashboard Follow-up

The `0.1.4` pending review was canceled in the Chrome Web Store Developer Dashboard, `/tmp/locallens-extension-red-potassium-0.1.5.zip` was uploaded, and draft `0.1.5` was submitted for review. The dashboard confirmed `Status: Pending review`, item ID `bgmdmikdapojncddhpabnofcioffnhbg`, and draft version `0.1.5`.

Dashboard recheck on April 22, 2026 showed `Status: Pending review`, draft version `0.1.5`, permissions `activeTab, scripting`, and no published version yet.

## Release Decision

Keep submitted draft `0.1.5` in review unless a new rejection, wrong-package upload, broken public reviewer URL, or other acceptance blocker is observed. Nonblocking hardening after submission belongs in the next package, starting with `0.1.6` after `0.1.5` is accepted or published.

The submitted ZIP remains `/tmp/locallens-extension-red-potassium-0.1.5.zip`. Later local source cleanup is not part of the submitted store artifact unless a future dashboard action replaces the draft.

Current source is queued as `0.1.6` and must not be submitted while `0.1.5` is still pending review unless a new acceptance blocker is found.
