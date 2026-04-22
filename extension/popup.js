import {
  clampText,
  countWords,
  extractSelectionContextFromCurrentPage,
  redactSensitive,
  shortUrl,
} from "./popup-helpers.js";

const outputEl = document.getElementById("output");
const capabilityStatusEl = document.getElementById("capability-status");
const downloadStatusEl = document.getElementById("download-status");
const sourceBadgeEl = document.getElementById("source-badge");
const sourceTitleEl = document.getElementById("source-title");
const sourceMetaEl = document.getElementById("source-meta");
const copyButton = document.getElementById("copy-output");
const translateSelect = document.getElementById("target-language");
const actionButtons = [...document.querySelectorAll("[data-action]")];

const LANGUAGE_NAMES = {
  de: "German",
  en: "English",
  es: "Spanish",
  fr: "French",
  hy: "Armenian",
  ru: "Russian",
};

const SUMMARY_OPTIONS = {
  type: "key-points",
  format: "plain-text",
  length: "medium",
  outputLanguage: "en",
};

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
    mode: "translator",
    prepareInput: (context) => context.text,
    run: (context) => translateText(context.text, getSelectedTargetLanguage()),
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
      const availability = await Summarizer.availability(SUMMARY_OPTIONS);
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

  if (typeof globalThis.Translator !== "undefined") {
    try {
      const availability = await Translator.availability({
        sourceLanguage: "en",
        targetLanguage: "es",
      });
      checks.push(`Translator: ${availability}`);
    } catch (error) {
      checks.push(`Translator: ${error.name}`);
    }
  } else {
    checks.push("Translator: unavailable");
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

function getSelectedTargetLanguage() {
  const code = translateSelect.value || "es";
  return {
    code,
    name: LANGUAGE_NAMES[code] || code,
  };
}

async function summarizeText(text, { context }) {
  if (typeof globalThis.Summarizer === "undefined") {
    throw new Error("Chrome built-in summarization is unavailable in this popup.");
  }

  const availability = await Summarizer.availability(SUMMARY_OPTIONS);
  if (availability === "unavailable") {
    throw new Error("Summarizer API is unavailable. Use Chrome 138+ with built-in AI enabled.");
  }

  if (!navigator.userActivation.isActive) {
    throw new Error("Chrome requires a direct click before starting a local summarizer session.");
  }

  const summarizer = await Summarizer.create({
    ...SUMMARY_OPTIONS,
    preference: "capability",
    monitor(monitor) {
      monitor.addEventListener("downloadprogress", (event) => {
        const percent = Math.round(event.loaded * 100);
        setDownloadStatus(`Downloading local summary model… ${percent}%`);
      });
    },
  });

  try {
    const stream = summarizer.summarizeStreaming(text, { context });
    let result = "";
    for await (const chunk of stream) {
      result = chunk;
      outputEl.textContent = chunk;
    }
    return result;
  } finally {
    if (typeof summarizer.destroy === "function") {
      summarizer.destroy();
    }
  }
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

  try {
    let result = "";
    const stream = session.promptStreaming(userPrompt);
    for await (const chunk of stream) {
      result = chunk;
      outputEl.textContent = chunk;
    }
    return result;
  } finally {
    if (typeof session.destroy === "function") {
      session.destroy();
    }
  }
}

async function translateText(text, targetLanguage) {
  if (typeof globalThis.Translator === "undefined") {
    throw new Error("Chrome Translator API is unavailable in this popup.");
  }

  const sourceLanguage = await detectSourceLanguage(text);
  if (sourceLanguage === targetLanguage.code) {
    return text;
  }

  const availability = await Translator.availability({
    sourceLanguage,
    targetLanguage: targetLanguage.code,
  });
  if (availability === "unavailable") {
    throw new Error(
      `Translator API is unavailable for ${sourceLanguage} to ${targetLanguage.name}. Use Chrome 138+ with built-in AI enabled.`,
    );
  }

  if (!navigator.userActivation.isActive) {
    throw new Error("Chrome requires a direct click before starting a local translation session.");
  }

  const translator = await Translator.create({
    sourceLanguage,
    targetLanguage: targetLanguage.code,
    monitor(monitor) {
      monitor.addEventListener("downloadprogress", (event) => {
        const percent = Math.round(event.loaded * 100);
        setDownloadStatus(`Downloading local translation model… ${percent}%`);
      });
    },
  });

  try {
    return await translator.translate(text);
  } finally {
    if (typeof translator.destroy === "function") {
      translator.destroy();
    }
  }
}

async function detectSourceLanguage(text) {
  if (typeof globalThis.LanguageDetector === "undefined") {
    return "en";
  }

  try {
    const availability = await LanguageDetector.availability();
    if (availability === "unavailable") {
      return "en";
    }

    const detector = await LanguageDetector.create({
      monitor(monitor) {
        monitor.addEventListener("downloadprogress", (event) => {
          const percent = Math.round(event.loaded * 100);
          setDownloadStatus(`Downloading local language detector… ${percent}%`);
        });
      },
    });

    try {
      const results = await detector.detect(text);
      return results.find((result) => result.confidence >= 0.5)?.detectedLanguage || "en";
    } finally {
      if (typeof detector.destroy === "function") {
        detector.destroy();
      }
    }
  } catch {
    return "en";
  }
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
  const [result] = await runInActiveTab(extractSelectionContextFromCurrentPage);
  const context = result?.result;
  if (context?.blockedReason) {
    throw new Error(context.blockedReason);
  }
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

function extractPageContext() {
  const primary = document.querySelector("article, main, [role='main']");
  const bodyText = primary?.innerText || document.body?.innerText || "";
  return {
    title: document.title,
    url: location.href,
    text: bodyText,
  };
}
