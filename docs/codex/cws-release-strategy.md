# Chrome Web Store Release Strategy

## Current Submitted Version

Chrome Web Store draft `0.1.5` is the active Red Potassium remediation package for item `bgmdmikdapojncddhpabnofcioffnhbg`.

Leave `0.1.5` pending review as long as the dashboard still shows it as submitted or pending and no new rejection or acceptance-blocking defect is observed. Do not reset the review queue for unrelated hardening, docs cleanup, lifecycle cleanup, or future-version polish.

The submitted ZIP is the release artifact for Chrome Web Store review. Post-submit worktree changes are not part of submitted `0.1.5` unless the store draft is intentionally replaced. If current source differs from the submitted ZIP, record that difference and queue the source state for the next version.

This branch now represents queued `0.1.6` work. Do not upload or submit it until `0.1.5` reaches production or a new rejection makes replacement necessary.

## When To Resubmit

Cancel and replace a pending Chrome Web Store draft only when at least one of these is true:

- the dashboard shows a new rejection or a blocking submit error
- the submitted ZIP is not the intended version or item
- a verified acceptance blocker exists in the submitted package
- required public URLs for support, privacy, or reviewer instructions are broken
- the reviewer instructions make a false claim about the submitted package

If the issue is a nonblocking improvement, keep it local and queue it for the next package after production acceptance.

## Next Version Handling

After `0.1.5` is accepted or published, start the next package at `0.1.6`.

Use this order:

1. Confirm production state in the Chrome Web Store dashboard with the item ID and version visible.
2. Move queued hardening changes into the next release branch.
3. Run local verification, the reviewer gate, and real Chrome E2E against the packaged ZIP.
4. Regenerate launch metadata and listing copy from tracked source.
5. Update the public support site before upload when reviewer-facing copy changed.
6. Upload and submit only after the package, public URLs, and reviewer instructions match.

## Reviewer Gate

Before push or resubmission, the reviewer gate must cover:

- local Python and Node tests
- launch manifest and listing generation
- extension ZIP contents
- exact-artifact inspection for the ZIP intended for upload
- MV3 injected-function isolation
- Chrome Web Store feature claims versus shipped popup actions
- public support, privacy, and reviewer-instruction links

Install the hook with:

```bash
git config core.hooksPath .githooks
```

The pre-push hook runs deterministic local verification through `scripts/reviewer_gate.py --skip-codex` so normal contributors are not required to have Codex installed.

Release operators should run the full reviewer gate without `--skip-codex` before upload or resubmission. The full gate requires Codex authentication and may use Codex subagents through the configured runtime; missing Codex review is a release blocker.
