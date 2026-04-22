export const MAX_TEXT_LENGTH = 12000;

const TEXT_INPUT_TYPES = /^(?:text|search|url|tel|email)$/i;

export function clampText(text) {
  const normalized = (text || "").replace(/\s+/g, " ").trim();
  return normalized.length > MAX_TEXT_LENGTH
    ? `${normalized.slice(0, MAX_TEXT_LENGTH)}…`
    : normalized;
}

export function countWords(text) {
  return (text || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;
}

export function shortUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/^www\./, "");
  } catch {
    return "active tab";
  }
}

export function redactSensitive(text) {
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

function sliceActiveElementSelection(element) {
  const start = element.selectionStart ?? 0;
  const end = element.selectionEnd ?? 0;
  return element.value?.slice(start, end).trim() || "";
}

function extractActiveElementSelection(activeElement) {
  if (!activeElement) {
    return { text: "", blockedReason: "" };
  }

  const tagName = String(activeElement.tagName || "").toUpperCase();
  if (tagName === "TEXTAREA") {
    return { text: sliceActiveElementSelection(activeElement), blockedReason: "" };
  }

  if (tagName !== "INPUT") {
    return { text: "", blockedReason: "" };
  }

  const inputType = String(activeElement.type || "text");
  if (/^password$/i.test(inputType)) {
    return {
      text: "",
      blockedReason: "LocalLens does not process selections from password fields.",
    };
  }

  if (!TEXT_INPUT_TYPES.test(inputType)) {
    return { text: "", blockedReason: "" };
  }

  return { text: sliceActiveElementSelection(activeElement), blockedReason: "" };
}

export function extractSelectionContextFromPage({ title, url, selectionText, activeElement }) {
  const explicitSelection = (selectionText || "").trim();
  if (explicitSelection) {
    return {
      title,
      url,
      text: explicitSelection,
      blockedReason: "",
    };
  }

  const activeSelection = extractActiveElementSelection(activeElement);
  return {
    title,
    url,
    text: activeSelection.text,
    blockedReason: activeSelection.blockedReason,
  };
}

export function extractSelectionContextFromCurrentPage() {
  const textInputTypes = /^(?:text|search|url|tel|email)$/i;

  function sliceSelection(element) {
    const start = element.selectionStart ?? 0;
    const end = element.selectionEnd ?? 0;
    return element.value?.slice(start, end).trim() || "";
  }

  function readActiveElementSelection(activeElement) {
    if (!activeElement) {
      return { text: "", blockedReason: "" };
    }

    const tagName = String(activeElement.tagName || "").toUpperCase();
    if (tagName === "TEXTAREA") {
      return { text: sliceSelection(activeElement), blockedReason: "" };
    }

    if (tagName !== "INPUT") {
      return { text: "", blockedReason: "" };
    }

    const inputType = String(activeElement.type || "text");
    if (/^password$/i.test(inputType)) {
      return {
        text: "",
        blockedReason: "LocalLens does not process selections from password fields.",
      };
    }

    if (!textInputTypes.test(inputType)) {
      return { text: "", blockedReason: "" };
    }

    return { text: sliceSelection(activeElement), blockedReason: "" };
  }

  const explicitSelection = window.getSelection()?.toString().trim() || "";
  if (explicitSelection) {
    return {
      title: document.title,
      url: location.href,
      text: explicitSelection,
      blockedReason: "",
    };
  }

  const activeSelection = readActiveElementSelection(document.activeElement);
  return {
    title: document.title,
    url: location.href,
    text: activeSelection.text,
    blockedReason: activeSelection.blockedReason,
  };
}
