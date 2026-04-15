# LocalLens Privacy Policy

Last updated: April 15, 2026

`LocalLens: Private AI Summaries` is designed to keep reading assistance local to the user's browser session.

## What LocalLens Handles

When the user clicks an action in the popup, LocalLens may access:

- the active tab URL and page title
- readable text from the current page
- text the user has selected on the current page

LocalLens uses this information only to provide the user-facing feature the user requested, such as summarizing the page, simplifying selected text, translating selected text, or creating a safe-share brief.

## How Data Is Processed

- LocalLens processes page text and selected text locally in Chrome using Chrome built-in AI.
- LocalLens does not send page text, selections, generated output, or browsing activity to the developer.
- LocalLens does not use analytics, advertising trackers, remote model APIs, or background scraping.
- LocalLens does not sell or transfer user data to third parties.

## Permissions

- `activeTab`: used only after the user clicks an action, so LocalLens can access the current tab long enough to read the page title, URL, and relevant text.
- `scripting`: used to run a short extraction function inside the current tab so LocalLens can read page text or the current selection without persistent host permissions.

## Storage

The current version of LocalLens does not request the `storage` permission and does not persist captured page text or generated results.

## Contact

For support or privacy questions, use the public issue tracker:

- <https://github.com/zack-dev-cm/locallens-private-ai-summaries/issues>
