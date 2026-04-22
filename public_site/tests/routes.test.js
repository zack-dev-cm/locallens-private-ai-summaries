import test from 'node:test';
import assert from 'node:assert/strict';

import worker from '../src/worker.js';

function dispatch(path, options = {}) {
  return worker.fetch(new Request(`https://locallens.example${path}`, options));
}

test('homepage renders LocalLens product summary and public links', async () => {
  const response = await dispatch('/');
  assert.equal(response.status, 200);
  assert.match(response.headers.get('content-type') ?? '', /text\/html/);

  const html = await response.text();
  assert.match(html, /LocalLens: Private AI Summaries/);
  assert.match(html, /Private AI summaries that stay in Chrome/);
  assert.match(html, /\/privacy\//);
  assert.match(html, /\/support\//);
  assert.match(html, /summarize the active page locally/i);
  assert.match(html, /Official LocalLens pages/i);
  assert.doesNotMatch(html, /Why this repo stands alone/i);
  assert.doesNotMatch(html, new RegExp(['operator-facing', 'publisher', 'skill repo'].join(' '), 'i'));
  assert.doesNotMatch(html, /View source/i);
});

test('privacy route returns reviewer-ready policy content', async () => {
  const response = await dispatch('/privacy/');
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('cache-control'), 'no-cache');

  const html = await response.text();
  assert.match(html, /Privacy Policy/);
  assert.match(html, /Last updated April 15, 2026/);
  assert.match(html, /does not send page text, selections, generated output, or browsing activity to the developer/i);
  assert.match(html, /does not process selections from password fields/i);
  assert.match(html, /official support page/i);
  assert.match(html, /\/support\//);
  assert.doesNotMatch(html, /github\.com\/zack-dev-cm\/locallens-private-ai-summaries\/issues\/new/i);
});

test('support route includes official support links and reviewer checks', async () => {
  const response = await dispatch('/support/');
  assert.equal(response.status, 200);
  assert.equal(response.headers.get('cache-control'), 'no-cache');

  const html = await response.text();
  assert.match(html, /LocalLens Support/);
  assert.match(html, /Official homepage/i);
  assert.match(html, /Official privacy policy/i);
  assert.match(html, /Sensitive privacy or security reports/i);
  assert.match(html, /do not post them in a public issue/i);
  assert.match(html, /Chrome 138 or newer/i);
  assert.match(html, /No sign-in, account, or API key/i);
  assert.match(html, /Summarizer: unavailable/i);
  assert.match(html, /Prompt API: unavailable/i);
  assert.match(html, /Translator: unavailable/i);
  assert.match(html, /id="reviewer-checklist"/i);
  assert.match(html, /github\.com\/zack-dev-cm\/locallens-private-ai-summaries\/issues\/new/i);
});

test('robots and sitemap endpoints are published for crawlers and store reviewers', async () => {
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
});

test('non-canonical support and privacy paths redirect to trailing slash routes', async () => {
  const privacyResponse = await dispatch('/privacy');
  assert.equal(privacyResponse.status, 301);
  assert.equal(privacyResponse.headers.get('location'), 'https://locallens.example/privacy/');

  const supportResponse = await dispatch('/support');
  assert.equal(supportResponse.status, 301);
  assert.equal(supportResponse.headers.get('location'), 'https://locallens.example/support/');
});

test('head requests reuse the same route handling without emitting a body', async () => {
  const response = await dispatch('/support/', { method: 'HEAD' });
  assert.equal(response.status, 200);
  assert.equal(await response.text(), '');
});

test('unknown routes return a 404 page', async () => {
  const response = await dispatch('/missing/');
  assert.equal(response.status, 404);

  const html = await response.text();
  assert.match(html, /Page not found/);
});
