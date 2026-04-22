import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

import {
  extractSelectionContextFromCurrentPage,
  extractSelectionContextFromPage,
  redactSensitive,
} from "./popup-helpers.js";

function withPageGlobals({ selectionText = "", activeElement = null }, callback) {
  const previousDocument = globalThis.document;
  const previousLocation = globalThis.location;
  const previousWindow = globalThis.window;

  globalThis.document = {
    title: "Example",
    activeElement,
  };
  globalThis.location = {
    href: "https://example.com/page",
  };
  globalThis.window = {
    getSelection() {
      return {
        toString() {
          return selectionText;
        },
      };
    },
  };

  try {
    return callback();
  } finally {
    if (previousDocument === undefined) {
      delete globalThis.document;
    } else {
      globalThis.document = previousDocument;
    }
    if (previousLocation === undefined) {
      delete globalThis.location;
    } else {
      globalThis.location = previousLocation;
    }
    if (previousWindow === undefined) {
      delete globalThis.window;
    } else {
      globalThis.window = previousWindow;
    }
  }
}

test("extractSelectionContextFromPage keeps text-input selections", () => {
  const context = extractSelectionContextFromPage({
    title: "Example",
    url: "https://example.com",
    selectionText: "",
    activeElement: {
      tagName: "INPUT",
      type: "email",
      value: "hello@example.com",
      selectionStart: 0,
      selectionEnd: 5,
    },
  });

  assert.equal(context.text, "hello");
  assert.equal(context.blockedReason, "");
});

test("extractSelectionContextFromPage blocks password-field selections", () => {
  const context = extractSelectionContextFromPage({
    title: "Example",
    url: "https://example.com",
    selectionText: "",
    activeElement: {
      tagName: "INPUT",
      type: "password",
      value: "super-secret",
      selectionStart: 0,
      selectionEnd: 12,
    },
  });

  assert.equal(context.text, "");
  assert.equal(context.blockedReason, "LocalLens does not process selections from password fields.");
});

test("extractSelectionContextFromCurrentPage reads page selections in the injected context", () => {
  const context = withPageGlobals({ selectionText: "Translate this paragraph." }, () =>
    extractSelectionContextFromCurrentPage(),
  );

  assert.deepEqual(context, {
    title: "Example",
    url: "https://example.com/page",
    text: "Translate this paragraph.",
    blockedReason: "",
  });
});

test("extractSelectionContextFromCurrentPage handles focused text inputs without module closures", () => {
  const source = extractSelectionContextFromCurrentPage.toString();
  assert.doesNotMatch(source, /extractSelectionContextFromPage/);

  const context = withPageGlobals(
    {
      activeElement: {
        tagName: "TEXTAREA",
        value: "Translate the selected words.",
        selectionStart: 0,
        selectionEnd: 9,
      },
    },
    () => extractSelectionContextFromCurrentPage(),
  );

  assert.equal(context.text, "Translate");
  assert.equal(context.blockedReason, "");
});

test("popup injects the self-contained selection extractor", async () => {
  const popupSource = await readFile(new URL("./popup.js", import.meta.url), "utf-8");

  assert.match(popupSource, /runInActiveTab\(extractSelectionContextFromCurrentPage\)/);
  assert.doesNotMatch(popupSource, /function\s+extractSelectionContext\s*\(/);
});

test("translate selection uses Chrome Translator API instead of a generic prompt", async () => {
  const popupSource = await readFile(new URL("./popup.js", import.meta.url), "utf-8");

  assert.match(popupSource, /mode:\s*"translator"/);
  assert.match(popupSource, /Translator\.create/);
  assert.match(popupSource, /LanguageDetector\.create/);
  assert.doesNotMatch(popupSource, /Translate the following text into/);
});

test("summarizer status checks specify output language", async () => {
  const popupSource = await readFile(new URL("./popup.js", import.meta.url), "utf-8");

  assert.match(popupSource, /outputLanguage:\s*"en"/);
  assert.match(popupSource, /Summarizer\.availability\(SUMMARY_OPTIONS\)/);
});

test("local AI sessions are destroyed even when streaming fails", async () => {
  const popupSource = await readFile(new URL("./popup.js", import.meta.url), "utf-8");

  assert.match(
    popupSource,
    /try\s*{[\s\S]+summarizer\.summarizeStreaming[\s\S]+}\s*finally\s*{[\s\S]+summarizer\.destroy\(\)/,
  );
  assert.match(
    popupSource,
    /try\s*{[\s\S]+session\.promptStreaming[\s\S]+}\s*finally\s*{[\s\S]+session\.destroy\(\)/,
  );
  assert.match(
    popupSource,
    /try\s*{[\s\S]+translator\.translate\(text\)[\s\S]+}\s*finally\s*{[\s\S]+translator\.destroy\(\)/,
  );
});

test("popup keeps translate selection visible in the default Chrome popup viewport", async () => {
  const popupStyles = await readFile(new URL("./popup.css", import.meta.url), "utf-8");
  const compactMedia = popupStyles.match(/@media\s*\(max-width:\s*460px\)\s*{[\s\S]+$/)?.[0] || "";
  const compactButtonGrid = compactMedia.match(/\.button-grid\s*{[^}]+}/)?.[0] || "";

  assert.match(compactButtonGrid, /grid-template-columns:\s*1fr 1fr/);
  assert.doesNotMatch(compactButtonGrid, /grid-template-columns:\s*1fr\s*;/);
});

test("redactSensitive replaces common sensitive patterns", () => {
  const result = redactSensitive(
    "Reach me at jane@example.com or https://example.com with token ghp_abcdefghijklmnop",
  );

  assert.match(result.text, /\[REDACTED_EMAIL\]/);
  assert.match(result.text, /\[REDACTED_URL\]/);
  assert.match(result.text, /\[REDACTED_TOKEN\]/);
  assert.equal(result.count, 3);
});
