import assert from 'node:assert/strict';

import worker from '../src/worker.js';

function dispatch(path, options = {}) {
  return worker.fetch(new Request(`https://locallens.example${path}`, options));
}

async function main() {
  const home = await dispatch('/');
  assert.equal(home.status, 200);
  assert.match(home.headers.get('content-type') ?? '', /text\/html/);
  const homeHtml = await home.text();
  assert.match(homeHtml, /LocalLens: Private AI Summaries/);
  assert.match(homeHtml, /Private AI summaries that stay in Chrome/);
  assert.match(homeHtml, /\/privacy\//);
  assert.match(homeHtml, /\/support\//);
  assert.match(homeHtml, /summarize the active page locally/i);
  assert.match(homeHtml, /Official LocalLens pages/i);
  assert.doesNotMatch(homeHtml, /Why this repo stands alone/i);
  assert.doesNotMatch(homeHtml, new RegExp(['operator-facing', 'publisher', 'skill repo'].join(' '), 'i'));
  assert.doesNotMatch(homeHtml, /View source/i);

  const privacy = await dispatch('/privacy/');
  assert.equal(privacy.status, 200);
  assert.equal(privacy.headers.get('cache-control'), 'no-cache');
  const privacyHtml = await privacy.text();
  assert.match(privacyHtml, /Privacy Policy/);
  assert.match(privacyHtml, /Last updated April 15, 2026/);
  assert.match(
    privacyHtml,
    /does not send page text, selections, generated output, or browsing activity to the developer/i
  );
  assert.match(privacyHtml, /does not process selections from password fields/i);
  assert.match(privacyHtml, /official support page/i);
  assert.match(privacyHtml, /\/support\//);
  assert.doesNotMatch(privacyHtml, /github\.com\/zack-dev-cm\/locallens-private-ai-summaries\/issues/i);

  const support = await dispatch('/support/');
  assert.equal(support.status, 200);
  assert.equal(support.headers.get('cache-control'), 'no-cache');
  const supportHtml = await support.text();
  assert.match(supportHtml, /LocalLens Support/);
  assert.match(supportHtml, /Official homepage/i);
  assert.match(supportHtml, /Official privacy policy/i);
  assert.match(supportHtml, /Sensitive privacy or security reports/i);
  assert.match(supportHtml, /do not post them in a public issue/i);
  assert.match(supportHtml, /Chrome 138 or newer/i);
  assert.match(supportHtml, /No sign-in, account, or API key/i);
  assert.match(supportHtml, /Summarizer: unavailable/i);
  assert.match(supportHtml, /Prompt API: unavailable/i);
  assert.match(supportHtml, /Translator: unavailable/i);
  assert.match(supportHtml, /id="reviewer-checklist"/i);
  assert.match(supportHtml, /github\.com\/zack-dev-cm\/locallens-private-ai-summaries\/issues\/new/i);

  const robots = await dispatch('/robots.txt');
  assert.equal(robots.status, 200);
  assert.match(robots.headers.get('content-type') ?? '', /text\/plain/);
  assert.match(await robots.text(), /Sitemap: https:\/\/locallens\.example\/sitemap\.xml/);

  const sitemap = await dispatch('/sitemap.xml');
  assert.equal(sitemap.status, 200);
  assert.match(sitemap.headers.get('content-type') ?? '', /application\/xml/);
  const sitemapXml = await sitemap.text();
  assert.match(sitemapXml, /https:\/\/locallens\.example\/privacy\//);
  assert.match(sitemapXml, /https:\/\/locallens\.example\/support\//);

  const privacyRedirect = await dispatch('/privacy');
  assert.equal(privacyRedirect.status, 301);
  assert.equal(privacyRedirect.headers.get('location'), 'https://locallens.example/privacy/');

  const supportRedirect = await dispatch('/support');
  assert.equal(supportRedirect.status, 301);
  assert.equal(supportRedirect.headers.get('location'), 'https://locallens.example/support/');

  const head = await dispatch('/support/', { method: 'HEAD' });
  assert.equal(head.status, 200);
  assert.equal(await head.text(), '');

  const missing = await dispatch('/missing/');
  assert.equal(missing.status, 404);
  assert.match(await missing.text(), /Page not found/);

  console.log('LocalLens public site route checks passed.');
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack : String(error));
  process.exitCode = 1;
});
