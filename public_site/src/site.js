import { siteContent } from './site-content.generated.js';

const navigation = [
  ['/', 'Home'],
  ['/privacy/', 'Privacy'],
  ['/support/', 'Support']
];

const sharedHeaders = {
  'content-type': 'text/html; charset=utf-8',
  'cache-control': 'no-cache',
  'content-security-policy':
    "default-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; img-src 'self' data:; style-src 'unsafe-inline'; connect-src 'self'",
  'referrer-policy': 'strict-origin-when-cross-origin',
  'x-content-type-options': 'nosniff',
  'x-frame-options': 'DENY'
};

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function renderNav(currentPath) {
  return navigation
    .map(([href, label]) => {
      const isActive = href === currentPath;
      return `<a class="nav-link${isActive ? ' active' : ''}" href="${href}"${
        isActive ? ' aria-current="page"' : ''
      }>${label}</a>`;
    })
    .join('');
}

function renderCardList(items) {
  return items
    .map(
      (item) =>
        `<li class="card-list-item"><span class="card-list-marker"></span><span>${escapeHtml(item)}</span></li>`
    )
    .join('');
}

function renderLinkList(items) {
  return items
    .map(
      (item) =>
        `<li class="link-list-item"><a href="${escapeHtml(item.href)}" rel="noreferrer">${escapeHtml(
          item.label
        )}</a><span>${escapeHtml(item.description)}</span></li>`
    )
    .join('');
}

function renderHomeContent() {
  const { metadata, home } = siteContent;
  return `
    <section class="hero">
      <div class="eyebrow">Chrome built-in AI • local-only processing</div>
      <h1>${escapeHtml(home.heroTitle)}</h1>
      <p class="hero-copy">${escapeHtml(home.heroBody)}</p>
      <div class="hero-actions">
        <a class="button primary" href="/privacy/">Read privacy policy</a>
        <a class="button secondary" href="/support/">Get support</a>
      </div>
    </section>
    <section class="grid two-up">
      <article class="panel">
        <h2>What LocalLens does</h2>
        <ul class="card-list">${renderCardList(home.features)}</ul>
      </article>
      <article class="panel accent-panel">
        <h2>Official LocalLens pages</h2>
        <p>Use these public URLs for product details, privacy review, and reviewer support.</p>
        <ul class="link-list">${renderLinkList(home.officialLinks)}</ul>
      </article>
    </section>
    <section class="grid three-up facts">
      <article class="panel">
        <div class="fact-label">Minimum Chrome</div>
        <div class="fact-value">${escapeHtml(metadata.chromeVersion)}+</div>
      </article>
      <article class="panel">
        <div class="fact-label">Permissions</div>
        <div class="fact-value">activeTab + scripting</div>
      </article>
      <article class="panel">
        <div class="fact-label">Account required</div>
        <div class="fact-value">No</div>
      </article>
    </section>
    <section class="panel">
      <h2>Reviewer-ready notes</h2>
      <ul class="card-list">${renderCardList(home.featureNotes)}</ul>
    </section>
  `;
}

function renderDocumentPage(title, html, extraKicker) {
  return `
    <section class="hero compact">
      <div class="eyebrow">${escapeHtml(extraKicker)}</div>
      <h1>${escapeHtml(title)}</h1>
    </section>
    <section class="panel prose">
      ${html}
    </section>
  `;
}

const pageRenderers = {
  '/': {
    title: siteContent.metadata.title,
    description: siteContent.metadata.description,
    render: renderHomeContent
  },
  '/privacy/': {
    title: `${siteContent.metadata.title} Privacy Policy`,
    description: 'Public privacy policy for the LocalLens Chrome extension.',
    render: () =>
      renderDocumentPage(
        siteContent.privacy.title,
        siteContent.privacy.bodyHtml,
        `Last updated ${siteContent.privacy.lastUpdated}`
      )
  },
  '/support/': {
    title: `${siteContent.metadata.title} Support`,
    description: 'Public support and reviewer help page for LocalLens.',
    render: () => renderDocumentPage(siteContent.support.title, siteContent.support.bodyHtml, 'Public support surface')
  }
};

function renderShell({ title, description, path, body, origin }) {
  const canonical = new URL(path, origin).toString();
  const supportUrl = new URL('/support/', origin).toString();
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${escapeHtml(title)}</title>
    <meta name="description" content="${escapeHtml(description)}">
    <link rel="canonical" href="${escapeHtml(canonical)}">
    <style>
      :root {
        color-scheme: light;
        --bg: #f7f1e6;
        --bg-accent: #fff9f1;
        --surface: rgba(255, 252, 247, 0.88);
        --surface-strong: #fffdf9;
        --line: rgba(40, 48, 43, 0.12);
        --text: #1f2a24;
        --muted: #5f6d65;
        --teal: #0f766e;
        --rust: #b45309;
        --shadow: 0 22px 50px rgba(82, 60, 21, 0.12);
        font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(15, 118, 110, 0.14), transparent 30%),
          radial-gradient(circle at top right, rgba(180, 83, 9, 0.18), transparent 28%),
          linear-gradient(180deg, var(--bg-accent), var(--bg));
      }

      a {
        color: var(--teal);
      }

      .page {
        width: min(1100px, calc(100% - 2rem));
        margin: 0 auto;
        padding: 2rem 0 3rem;
      }

      .site-header {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1.5rem;
      }

      .brand-block {
        display: grid;
        gap: 0.35rem;
      }

      .brand-mark {
        font-size: 0.78rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--rust);
        font-weight: 700;
      }

      .brand-title {
        margin: 0;
        font-size: clamp(1.4rem, 3vw, 2rem);
        line-height: 1;
      }

      .brand-subtitle {
        margin: 0;
        color: var(--muted);
        max-width: 38rem;
      }

      .nav {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
      }

      .nav-link {
        text-decoration: none;
        padding: 0.72rem 1rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.64);
        color: var(--text);
        border: 1px solid var(--line);
        box-shadow: 0 10px 25px rgba(82, 60, 21, 0.08);
      }

      .nav-link.active {
        background: var(--text);
        color: white;
        border-color: transparent;
      }

      .hero,
      .panel {
        background: var(--surface);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.7);
        box-shadow: var(--shadow);
        border-radius: 28px;
      }

      .hero {
        padding: clamp(1.8rem, 5vw, 3.4rem);
        margin-bottom: 1.35rem;
      }

      .hero.compact {
        padding-bottom: 1.4rem;
      }

      .hero h1 {
        margin: 0.15rem 0 0.75rem;
        font-size: clamp(2.2rem, 7vw, 4.4rem);
        line-height: 0.95;
        letter-spacing: -0.04em;
      }

      .hero-copy {
        max-width: 46rem;
        font-size: 1.1rem;
        color: var(--muted);
      }

      .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.4rem 0.75rem;
        border-radius: 999px;
        background: rgba(15, 118, 110, 0.1);
        color: var(--teal);
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      .hero-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-top: 1.35rem;
      }

      .button {
        text-decoration: none;
        border-radius: 999px;
        padding: 0.85rem 1.15rem;
        font-weight: 700;
      }

      .button.primary {
        background: var(--text);
        color: white;
      }

      .button.secondary {
        background: rgba(15, 118, 110, 0.12);
        color: var(--teal);
      }

      .button.tertiary {
        background: rgba(180, 83, 9, 0.12);
        color: var(--rust);
      }

      .grid {
        display: grid;
        gap: 1rem;
        margin-bottom: 1rem;
      }

      .two-up {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .three-up {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .panel {
        padding: 1.35rem;
      }

      .accent-panel {
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(253, 244, 231, 0.96)),
          var(--surface);
      }

      .panel h2 {
        margin-top: 0;
        margin-bottom: 0.9rem;
      }

      .card-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: 0.85rem;
      }

      .card-list-item {
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
        color: var(--text);
      }

      .card-list-marker {
        width: 0.75rem;
        height: 0.75rem;
        margin-top: 0.35rem;
        flex: none;
        border-radius: 999px;
        background: linear-gradient(135deg, var(--teal), var(--rust));
      }

      .link-list {
        list-style: none;
        margin: 1rem 0 0;
        padding: 0;
        display: grid;
        gap: 0.9rem;
      }

      .link-list-item {
        display: grid;
        gap: 0.2rem;
      }

      .link-list-item a {
        font-weight: 700;
        text-decoration: none;
      }

      .link-list-item span {
        color: var(--muted);
      }

      .facts .panel {
        text-align: center;
        background: var(--surface-strong);
      }

      .fact-label {
        color: var(--muted);
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.55rem;
      }

      .fact-value {
        font-size: 1.8rem;
        font-weight: 800;
      }

      .prose :first-child {
        margin-top: 0;
      }

      .prose p,
      .prose li {
        color: var(--text);
        line-height: 1.7;
      }

      .prose ul,
      .prose ol {
        padding-left: 1.3rem;
      }

      .prose pre {
        overflow-x: auto;
        padding: 1rem;
        border-radius: 18px;
        background: #1f2a24;
        color: #f9f8f4;
      }

      .prose code {
        font-family: "SFMono-Regular", "SF Mono", Monaco, Consolas, "Liberation Mono", monospace;
        font-size: 0.95em;
      }

      .site-footer {
        margin-top: 1.25rem;
        color: var(--muted);
        font-size: 0.95rem;
      }

      @media (max-width: 820px) {
        .two-up,
        .three-up {
          grid-template-columns: 1fr;
        }

        .page {
          width: min(100% - 1.2rem, 1100px);
          padding-top: 1rem;
        }

        .hero h1 {
          font-size: clamp(2rem, 12vw, 3.4rem);
        }
      }
    </style>
  </head>
  <body>
    <main class="page">
      <header class="site-header">
        <div class="brand-block">
          <div class="brand-mark">LocalLens Public Surface</div>
          <h1 class="brand-title">${escapeHtml(siteContent.metadata.title)}</h1>
          <p class="brand-subtitle">${escapeHtml(siteContent.metadata.description)}</p>
        </div>
        <nav class="nav" aria-label="Primary">${renderNav(path)}</nav>
      </header>
      ${body}
      <footer class="site-footer">
        Official support:
        <a href="${escapeHtml(supportUrl)}" rel="noreferrer">${escapeHtml(supportUrl)}</a>
      </footer>
    </main>
  </body>
</html>`;
}

export function redirectResponse(location, status = 301) {
  return new Response(null, {
    status,
    headers: {
      location,
      'cache-control': 'public, max-age=300'
    }
  });
}

export function renderRoute(path, origin) {
  const page = pageRenderers[path];
  if (!page) return null;
  return renderShell({
    title: page.title,
    description: page.description,
    path,
    body: page.render(),
    origin
  });
}

export function htmlResponse(html, { method = 'GET', status = 200 } = {}) {
  return new Response(method === 'HEAD' ? null : html, {
    status,
    headers: sharedHeaders
  });
}

export function notFoundResponse({ method = 'GET', origin }) {
  const html = renderShell({
    title: 'Page Not Found',
    description: 'The requested LocalLens public page was not found.',
    path: '/404/',
    body: `
      <section class="hero compact">
        <div class="eyebrow">404</div>
        <h1>Page not found</h1>
        <p class="hero-copy">Use the links above to jump to the LocalLens homepage, privacy policy, or support page.</p>
      </section>
    `,
    origin
  });

  return htmlResponse(html, { method, status: 404 });
}
