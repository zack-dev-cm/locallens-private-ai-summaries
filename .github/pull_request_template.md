## Summary

- What changed?
- Which product surface does it affect: extension, public site, release helper, docs, or collateral?

## Verification

- [ ] `python3 -m pytest -q`
- [ ] `npm test`
- [ ] `python3 -m codex_harness audit . --strict --min-score 90` run locally when available, or the skip reason is explained
- [ ] Relevant release-helper smoke run
- [ ] Not run, with reason explained below

## Public Surface Review

- [ ] Security, privacy, and reviewer docs still match shipped behavior
- [ ] Support, homepage, and privacy links are still correct
- [ ] No local paths, secrets, leak-prone collateral, or internal-only URLs were added
- [ ] Generated artifacts are either excluded or intentionally included

## Notes

- Reviewer guidance, screenshots, or release-collateral follow-up
