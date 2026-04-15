const outputEl = document.getElementById("output");
const capabilityStatusEl = document.getElementById("capability-status");
const downloadStatusEl = document.getElementById("download-status");
const sourceBadgeEl = document.getElementById("source-badge");
const sourceTitleEl = document.getElementById("source-title");
const sourceMetaEl = document.getElementById("source-meta");
const copyButton = document.getElementById("copy-output");
const translateSelect = document.getElementById("target-language");
const actionButtons = [...document.querySelectorAll("[data-action]")];

const MAX_TEXT_LENGTH = 12000;

const ACTIONS = {
  summarizePage: {
    label: "Page summary",
    source: "page",
    mode: "summarizer",
    prepareInput: (context) => context.text,
    run: (context) =>
      summarizeText(context.text, {
        context: `Summarize the active web page titled "${context.title}" into useful key points.`,
      }),
  },
  summarizeSelection: {
    label: "Selection summary",
    source: "selection",
    mode: "summarizer",
    prepareInput: (context) => context.text,
    run: (context) =>
      summarizeText(context.text, {
        context: "Summarize the selected text into concise practical key points.",
      }),
  },
  simplifySelection: {
    label: "Simplified selection",
    source: "selection",
    mode: "languageModel",
    prepareInput: (context) => context.text,
    run: (context) =>
      promptText({
        systemPrompt:
          "You simplify dense text without removing meaning. Keep technical terms when necessary, and use short sentences.",
        userPrompt: `Simplify this selected text for fast reading. Use bullets if helpful.\n\n${context.text}`,
      }),
  },
  translateSelection: {
    label: "Translated selection",
    source: "selection",
    mode: "languageModel",
    prepareInput: (context) => context.text,
    run: (context) =>
      promptText({
        systemPrompt:
          "You are a precise translator. Preserve meaning and tone. Do not add commentary.",
        userPrompt: `Translate the following text into ${translateSelect.value}. Preserve names, links, and formatting when possible.\n\n${context.text}`,
      }),
  },
  safeShareSelection: {
    label: "Safe-share brief",
    source: "selection",
    mode: "languageModel",
    prepareInput: (context) => context.redactedText,
    run: (context) =>
      promptText({
        systemPrompt:
          "You rewrite text for safe external sharing. Keep meaning, preserve placeholders like [REDACTED_EMAIL], and avoid re-introducing hidden details.",
        userPrompt:
          "Create a concise safe-share brief from this redacted selection. Keep the output useful for collaboration, but do not guess the hidden values.\n\n" +
          context.redactedText,
      }),
  },
};

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(outputEl.textContent ?? "");
    setDownloadStatus("Copied result to clipboard.");
  } catch (error) {
    setDownloadStatus(`Copy failed: ${error.message}`);
  }
});

actionButtons.forEach((button) => {
  button.addEventListener("click", () => runAction(button.dataset.action));
});

void refreshCapabilityStatus();

async function runAction(actionKey) {
  const action = ACTIONS[actionKey];
  if (!action) {
    return;
  }

  setBusy(true);
  setDownloadStatus("Collecting text from the active tab…");
  renderSource({
    badge: action.label,
    title: "Preparing active-tab content…",
    meta: "LocalLens only reads the active tab after your click.",
  });
  outputEl.textContent = "Working…";

  try {
    const context =
      action.source === "page"
        ? await getPageContext()
        : await getSelectionContext(actionKey === "safeShareSelection");

    const prepared = action.prepareInput(context).trim();
    if (!prepared) {
      throw new Error(
        action.source === "page"
          ? "No readable page text found."
          : "No selected text found. Highlight text on the page first.",
      );
    }

    renderSource({
      badge: action.label,
      title: context.title,
      meta: context.meta,
    });
    outputEl.textContent = "Running locally in Chrome…";

    const result = await action.run(context);
    outputEl.textContent = result.trim() || "No result returned.";
    setDownloadStatus(
      actionKey === "safeShareSelection" && context.redactionCount > 0
        ? `Redacted ${context.redactionCount} sensitive pattern${context.redactionCount === 1 ? "" : "s"} before generating the safe-share brief.`
        : "Finished locally. Nothing was sent to an external server.",
    );
  } catch (error) {
    outputEl.textContent = error.message;
    setDownloadStatus("Action failed.");
  } finally {
    setBusy(false);
    void refreshCapabilityStatus();
  }
}

async function refreshCapabilityStatus() {
  const checks = [];

  if (typeof globalThis.Summarizer !== "undefined") {
    try {
      const availability = await Summarizer.availability();
      checks.push(`Summarizer: ${availability}`);
    } catch (error) {
      checks.push(`Summarizer: ${error.name}`);
    }
  } else {
    checks.push("Summarizer: unavailable");
  }

  if (typeof globalThis.LanguageModel !== "undefined") {
    try {
      const availability = await LanguageModel.availability({
        expectedInputs: [{ type: "text", languages: ["en"] }],
        expectedOutputs: [{ type: "text", languages: ["en"] }],
      });
      checks.push(`Prompt API: ${availability}`);
    } catch (error) {
      checks.push(`Prompt API: ${error.name}`);
    }
  } else {
    checks.push("Prompt API: unavailable");
  }

  capabilityStatusEl.textContent = checks.join(" • ");
}

function setBusy(isBusy) {
  actionButtons.forEach((button) => {
    button.disabled = isBusy;
  });
  copyButton.disabled = isBusy;
}

function setDownloadStatus(message) {
  downloadStatusEl.textContent = message ?? "";
}

function renderSource({ badge, title, meta }) {
  sourceBadgeEl.textContent = badge;
  sourceTitleEl.textContent = title;
  sourceMetaEl.textContent = meta;
}

async function summarizeText(text, { context }) {
  if (typeof globalThis.Summarizer === "undefined") {
    throw new Error("Chrome built-in summarization is unavailable in this popup.");
  }

  const availability = await Summarizer.availability();
  if (availability === "unavailable") {
    throw new Error("Summarizer API is unavailable. Use Chrome 138+ with built-in AI enabled.");
  }

  if (!navigator.userActivation.isActive) {
    throw new Error("Chrome requires a direct click before starting a local summarizer session.");
  }

  const summarizer = await Summarizer.create({
    type: "key-points",
    format: "plain-text",
    length: "medium",
    preference: "capability",
    monitor(monitor) {
      monitor.addEventListener("downloadprogress", (event) => {
        const percent = Math.round(event.loaded * 100);
        setDownloadStatus(`Downloading local summary model… ${percent}%`);
      });
    },
  });

  const stream = summarizer.summarizeStreaming(text, { context });
  let result = "";
  for await (const chunk of stream) {
    result = chunk;
    outputEl.textContent = chunk;
  }

  if (typeof summarizer.destroy === "function") {
    summarizer.destroy();
  }

  return result;
}

async function promptText({ systemPrompt, userPrompt }) {
  if (typeof globalThis.LanguageModel === "undefined") {
    throw new Error("Chrome Prompt API is unavailable in this popup.");
  }

  const availability = await LanguageModel.availability({
    expectedInputs: [{ type: "text", languages: ["en"] }],
    expectedOutputs: [{ type: "text", languages: ["en"] }],
  });
  if (availability === "unavailable") {
    throw new Error("Prompt API is unavailable. Use Chrome 138+ with built-in AI enabled.");
  }

  const session = await LanguageModel.create({
    initialPrompts: [{ role: "system", content: systemPrompt }],
    monitor(monitor) {
      monitor.addEventListener("downloadprogress", (event) => {
        const percent = Math.round(event.loaded * 100);
        setDownloadStatus(`Downloading local language model… ${percent}%`);
      });
    },
  });

  let result = "";
  const stream = session.promptStreaming(userPrompt);
  for await (const chunk of stream) {
    result = chunk;
    outputEl.textContent = chunk;
  }

  if (typeof session.destroy === "function") {
    session.destroy();
  }

  return result;
}

async function getPageContext() {
  const [result] = await runInActiveTab(extractPageContext);
  if (!result?.result?.text) {
    throw new Error("Unable to read text from the current page.");
  }

  const context = result.result;
  return {
    title: context.title || "Current page",
    text: clampText(context.text),
    meta: `${shortUrl(context.url)} • ${countWords(context.text)} words captured from the active tab`,
  };
}

async function getSelectionContext(includeRedaction) {
  const [result] = await runInActiveTab(extractSelectionContext);
  const context = result?.result;
  if (!context?.text?.trim()) {
    throw new Error("No selected text found. Highlight text on the page first.");
  }

  const text = clampText(context.text);
  const redaction = includeRedaction ? redactSensitive(text) : null;

  return {
    title: context.title || "Selected text",
    text,
    redactedText: redaction?.text ?? text,
    redactionCount: redaction?.count ?? 0,
    meta:
      `${shortUrl(context.url)} • ${countWords(text)} selected words` +
      (redaction?.count ? ` • ${redaction.count} redactions applied` : ""),
  };
}

async function runInActiveTab(func) {
  const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  if (!tab?.id) {
    throw new Error("No active tab found.");
  }

  return chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func,
  });
}

function clampText(text) {
  const normalized = (text || "").replace(/\s+/g, " ").trim();
  return normalized.length > MAX_TEXT_LENGTH
    ? `${normalized.slice(0, MAX_TEXT_LENGTH)}…`
    : normalized;
}

function countWords(text) {
  return (text || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;
}

function shortUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/^www\./, "");
  } catch {
    return "active tab";
  }
}

function redactSensitive(text) {
  const patterns = [
    /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi,
    /\b(?:\+?\d[\d\s().-]{7,}\d)\b/g,
    /\bhttps?:\/\/\S+\b/gi,
    /\b(?:sk|ghp|gho|ghu|pat)_[A-Za-z0-9_\-]{12,}\b/g,
    /\b[A-F0-9]{32,}\b/gi,
    /\b(?:\d[ -]*?){13,19}\b/g,
  ];

  const labels = [
    "[REDACTED_EMAIL]",
    "[REDACTED_PHONE]",
    "[REDACTED_URL]",
    "[REDACTED_TOKEN]",
    "[REDACTED_SECRET]",
    "[REDACTED_NUMBER]",
  ];

  let count = 0;
  let redacted = text;
  patterns.forEach((pattern, index) => {
    redacted = redacted.replace(pattern, () => {
      count += 1;
      return labels[index];
    });
  });

  return { text: redacted, count };
}

function extractPageContext() {
  const primary = document.querySelector("article, main, [role='main']");
  const bodyText = primary?.innerText || document.body?.innerText || "";
  return {
    title: document.title,
    url: location.href,
    text: bodyText,
  };
}

function extractSelectionContext() {
  const selection = window.getSelection()?.toString().trim() || "";
  let activeSelection = "";
  const element = document.activeElement;
  if (
    element &&
    (element.tagName === "TEXTAREA" ||
      (element.tagName === "INPUT" &&
        /^(?:text|search|url|tel|email|password)$/i.test(element.type)))
  ) {
    const start = element.selectionStart ?? 0;
    const end = element.selectionEnd ?? 0;
    activeSelection = element.value?.slice(start, end).trim() || "";
  }

  return {
    title: document.title,
    url: location.href,
    text: selection || activeSelection,
  };
}
