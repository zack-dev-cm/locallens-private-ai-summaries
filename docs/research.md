# Research Decision Memo

## Current Signals

### Browser AI adoption is no longer speculative

- Chrome for Developers said at Google I/O 2025 that the number of AI-powered Chrome extensions had doubled over the prior year, and that roughly 10% of all installed extensions now use AI in some form.
- Chrome for Developers also highlighted broader rollout of built-in AI support across desktop and Chromebook Plus devices, reducing the need for remote inference for lightweight text tasks.

### Stable built-in AI APIs create a practical privacy wedge

- Chrome documents the `Summarizer` API for stable local summaries.
- Chrome documents the `LanguageModel` Prompt API for Chrome extensions, including `LanguageModel.availability()` and `LanguageModel.create()`.
- These APIs make a no-server workflow realistic for a text-first extension.

### Review and listing constraints reward narrow, clean products

- Chrome Web Store policies emphasize a single purpose and minimal permissions.
- Store-listing docs require a real listing surface, screenshots, promo assets, privacy disclosures, and a clean metadata story.
- Image docs require a 128x128 icon, at least one screenshot, and a 440x280 promo tile.

## Local Machine Overlap

The local scan found multiple adjacent repos already covering:

- AI chat overlays
- repo summarization
- ChatGPT navigation/scrolling
- developer-console tooling
- general AI side-panel work

That makes another broad "AI everything" assistant a weak launch candidate.

## Decision

Build `LocalLens: Private AI Summaries`.

Why:

- broad enough for non-developers
- easy to explain in one sentence
- clear privacy story: local only, no account, no server
- minimal permission surface: `activeTab`, `scripting`, `storage`
- easy to show in screenshots and store copy
- strong fit for Chrome's built-in AI trend without fighting crowded all-in-one copilot positioning

## Extension Surface

- summarize the active page into key points
- summarize selected text
- simplify dense selected text
- translate selected text
- safe-share selected text by locally redacting obvious sensitive strings before AI processing

## Agent Surface

The companion OpenClaw skill automates:

- local extension inventory
- packaging and marketing asset generation
- leak scanning
- store-copy generation
- browser-driven Chrome Web Store submission
- GitHub + ClawHub release artifact generation

## Sources

- [Google I/O 2025 recap for AI on Chrome](https://developer.chrome.com/blog/io24-prompt-api-extensions)
- [AI challenge winners and built-in AI rollout context](https://developer.chrome.com/blog/ai-challenge-winners)
- [The Prompt API](https://developer.chrome.com/docs/ai/prompt-api)
- [Prompt API for Chrome extensions](https://developer.chrome.com/docs/extensions/ai/prompt-api)
- [Summarizer API](https://developer.chrome.com/docs/ai/summarizer-api)
- [Program Policies](https://developer.chrome.com/docs/webstore/program-policies)
- [Complete your listing information](https://developer.chrome.com/docs/webstore/cws-dashboard-listing)
- [Supplying images](https://developer.chrome.com/docs/webstore/images)
