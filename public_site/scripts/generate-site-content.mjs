import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const publicSiteRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(publicSiteRoot, '..');

const defaultPublicSiteBase = 'https://locallens-public-site.rapidapis.workers.dev/';
const publicSiteBase = (process.env.LOCALLENS_PUBLIC_SITE_BASE || defaultPublicSiteBase).replace(/\/?$/, '/');

const [privacyMarkdown, reviewerMarkdown, manifestRaw] = await Promise.all([
  readFile(path.join(repoRoot, 'docs', 'privacy-policy.md'), 'utf8'),
  readFile(path.join(repoRoot, 'docs', 'test-instructions.md'), 'utf8'),
  readFile(path.join(repoRoot, 'extension', 'manifest.json'), 'utf8')
]);

const manifest = JSON.parse(manifestRaw);

function extractSection(markdown, heading) {
  const escapedHeading = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = markdown.match(new RegExp(`^## ${escapedHeading}\\n([\\s\\S]*?)(?=^## |\\Z)`, 'm'));
  return match ? match[1].trim() : '';
}

function extractBulletList(markdownSection) {
  return markdownSection
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('- '))
    .map((line) => line.slice(2).trim());
}

function extractFirstParagraph(markdownSection) {
  return markdownSection
    .split('\n\n')
    .map((block) => block.trim())
    .find((block) => block.length > 0) ?? '';
}

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80) || 'section';
}

function restoreTokens(text, tokens) {
  return tokens.reduce((current, token, index) => current.replaceAll(`__TOKEN_${index}__`, token), text);
}

function renderInline(text) {
  const tokens = [];
  const pushToken = (html) => {
    const marker = `__TOKEN_${tokens.length}__`;
    tokens.push(html);
    return marker;
  };

  let working = text;

  working = working.replace(/`([^`]+)`/g, (_, code) =>
    pushToken(`<code>${escapeHtml(code)}</code>`)
  );
  working = working.replace(/\*\*([^*]+)\*\*/g, (_, strong) =>
    pushToken(`<strong>${escapeHtml(strong)}</strong>`)
  );
  working = working.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) =>
    pushToken(
      `<a href="${escapeHtml(href)}" rel="noreferrer">${escapeHtml(label)}</a>`
    )
  );
  working = working.replace(/<((?:https?:\/\/|mailto:)[^>\s]+)>/g, (_, href) =>
    pushToken(
      `<a href="${escapeHtml(href)}" rel="noreferrer">${escapeHtml(href)}</a>`
    )
  );

  return restoreTokens(escapeHtml(working), tokens);
}

function markdownToHtml(markdown) {
  const lines = markdown.replaceAll('\r\n', '\n').split('\n');
  const html = [];
  let paragraph = [];
  let listType = null;
  let listItems = [];
  let inCodeBlock = false;
  let codeLanguage = '';
  let codeLines = [];

  const flushParagraph = () => {
    if (paragraph.length === 0) return;
    html.push(`<p>${renderInline(paragraph.join(' '))}</p>`);
    paragraph = [];
  };

  const flushList = () => {
    if (!listType || listItems.length === 0) return;
    const rendered = listItems.map((item) => `<li>${renderInline(item)}</li>`).join('');
    html.push(`<${listType}>${rendered}</${listType}>`);
    listType = null;
    listItems = [];
  };

  const flushCode = () => {
    if (!inCodeBlock) return;
    const languageAttr = codeLanguage ? ` class="language-${escapeHtml(codeLanguage)}"` : '';
    html.push(
      `<pre><code${languageAttr}>${escapeHtml(codeLines.join('\n'))}</code></pre>`
    );
    inCodeBlock = false;
    codeLanguage = '';
    codeLines = [];
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();
    const trimmed = line.trim();

    if (inCodeBlock) {
      if (trimmed.startsWith('```')) {
        flushCode();
      } else {
        codeLines.push(line);
      }
      continue;
    }

    if (trimmed === '') {
      flushParagraph();
      flushList();
      continue;
    }

    if (trimmed.startsWith('```')) {
      flushParagraph();
      flushList();
      inCodeBlock = true;
      codeLanguage = trimmed.slice(3).trim();
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      flushParagraph();
      flushList();
      const level = headingMatch[1].length;
      const text = headingMatch[2].trim();
      html.push(`<h${level} id="${slugify(text)}">${renderInline(text)}</h${level}>`);
      continue;
    }

    const unorderedMatch = trimmed.match(/^-\s+(.+)$/);
    if (unorderedMatch) {
      flushParagraph();
      if (listType && listType !== 'ul') flushList();
      listType = 'ul';
      listItems.push(unorderedMatch[1].trim());
      continue;
    }

    const orderedMatch = trimmed.match(/^\d+\.\s+(.+)$/);
    if (orderedMatch) {
      flushParagraph();
      if (listType && listType !== 'ol') flushList();
      listType = 'ol';
      listItems.push(orderedMatch[1].trim());
      continue;
    }

    paragraph.push(trimmed);
  }

  flushParagraph();
  flushList();
  flushCode();

  return html.join('\n');
}

function stripDocumentTitle(markdown) {
  return markdown.replace(/^# .+\n+/, '').trim();
}

const homeFeatures = [
  'Summarize the active page locally with Chrome built-in AI.',
  'Summarize selected text for fast scanning inside the popup.',
  'Simplify dense writing into plainer language without a remote backend.',
  'Translate selected text locally in Chrome.',
  'Create safe-share text by masking obvious sensitive strings before rewriting.'
];
const officialLinks = [
  {
    label: 'Official homepage',
    href: publicSiteBase,
    description: 'Product overview and public landing page.'
  },
  {
    label: 'Privacy policy',
    href: `${publicSiteBase}privacy/`,
    description: 'Public privacy terms for users and Chrome Web Store review.'
  },
  {
    label: 'Support and reviewer help',
    href: `${publicSiteBase}support/`,
    description: 'Public support page and reviewer checklist.'
  }
];
const supportIssueUrl = 'https://github.com/zack-dev-cm/locallens-private-ai-summaries/issues/new';

const privacyLastUpdated = privacyMarkdown.match(/Last updated:\s*(.+)/)?.[1]?.trim() ?? '';
const privacyBody = stripDocumentTitle(privacyMarkdown);
const privacyBodyHtml = markdownToHtml(privacyBody);

const reviewerBody = stripDocumentTitle(reviewerMarkdown);
const supportMarkdown = `# LocalLens Support

Need help with LocalLens, want to report a bug, or need a public reviewer path? Use the official links below and include the page URL plus the action you ran.

- Official homepage: <${publicSiteBase}>
- Official privacy policy: <${publicSiteBase}privacy/>
- Reviewer support: <${publicSiteBase}support/#reviewer-checklist>
- Non-sensitive bug reports and support requests: <${supportIssueUrl}>
- Sensitive privacy or security reports: do not post them in a public issue. Follow the repository security path instead.

## Before You Report a Problem

- Confirm you are using Chrome ${manifest.minimum_chrome_version} or newer.
- Make sure Chrome built-in AI is enabled and available on the current device.
- Open the LocalLens popup and confirm the status line does not show \`Summarizer: unavailable\`, \`Prompt API: unavailable\`, or \`Translator: unavailable\`.
- No sign-in, account, or API key is required.
- If LocalLens starts a one-time model download, let it finish and rerun the action.

## Reviewer Checklist

${reviewerBody}
`;

const supportBodyHtml = markdownToHtml(stripDocumentTitle(supportMarkdown));

const generatedContent = {
  metadata: {
    title: manifest.name,
    description: manifest.description,
    chromeVersion: manifest.minimum_chrome_version,
    publicSiteBase
  },
  home: {
    heroTitle: 'Private AI summaries that stay in Chrome',
    heroBody:
      'LocalLens helps readers summarize, simplify, translate, and clean up page text without routing that content through a developer-run backend.',
    features: homeFeatures,
    officialLinks,
    featureNotes: [
      'Runs only after a user clicks an action in the popup.',
      'Uses Chrome built-in AI instead of a remote model API.',
      'Requires no sign-in, account, or API key.'
    ]
  },
  privacy: {
    title: 'Privacy Policy',
    lastUpdated: privacyLastUpdated,
    bodyHtml: privacyBodyHtml
  },
  support: {
    title: 'LocalLens Support',
    bodyHtml: supportBodyHtml,
    issueUrl: supportIssueUrl
  }
};

const outputPath = path.join(publicSiteRoot, 'src', 'site-content.generated.js');
await mkdir(path.dirname(outputPath), { recursive: true });
await writeFile(
  outputPath,
  `export const siteContent = ${JSON.stringify(generatedContent, null, 2)};\n`,
  'utf8'
);

console.log(`Generated ${path.relative(repoRoot, outputPath)}.`);
