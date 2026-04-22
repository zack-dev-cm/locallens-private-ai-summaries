# LocalLens Reviewer Test Instructions

Last updated: April 22, 2026

## Environment

- Desktop Chrome 138 or newer
- Chrome built-in AI enabled and available on the machine

## Capability Preflight

1. Open the LocalLens popup on any page before running a review action.
2. Check the status line at the bottom of the popup.
3. Confirm it does **not** say `Summarizer: unavailable`, `Prompt API: unavailable`, or `Translator: unavailable`.
4. If any required API is unavailable, switch to a Chrome 138+ build and profile where Chrome built-in AI and translation are enabled, then reopen the popup and recheck the status line.

## Core Checks

1. Open any text-heavy page in Chrome.
2. Click the LocalLens toolbar action.
3. Run `Summarize page`.
4. Confirm the popup shows a locally generated summary.

## Selection Checks

1. Highlight a paragraph on any page, for example `LocalLens translates selected text inside the popup.`
2. Open LocalLens.
3. Run `Summarize selection`, `Simplify selection`, and `Safe-share selection`.
4. Leave `Translate to` set to `Spanish`, or set it back to `Spanish`, then run `Translate selection`.
5. Confirm the translate result is in Spanish and uses the current selection only.

## First-Run Note

If Chrome needs to download a local built-in AI model on first use, LocalLens shows download progress in the popup. After the download completes, rerun the action.

## Recovery Path

- If `Summarize page` fails immediately, check whether the popup status line reports `Summarizer: unavailable`.
- If `Simplify selection` or `Safe-share selection` fails immediately, check whether the popup status line reports `Prompt API: unavailable`.
- If `Translate selection` fails immediately, check whether the popup status line reports `Translator: unavailable`.
- When the status line reports the APIs as available, rerun the action from the popup after any one-time model download finishes.

## No Account Requirement

LocalLens does not require the reviewer to sign in, create an account, or provide an API key.
