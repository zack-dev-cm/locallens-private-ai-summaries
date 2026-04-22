import { htmlResponse, notFoundResponse, redirectResponse, renderRoute } from './site.js';

const slashRedirects = new Map([
  ['/privacy', '/privacy/'],
  ['/support', '/support/']
]);

const TEXT_HEADERS = {
  'cache-control': 'public, max-age=300',
  'x-content-type-options': 'nosniff'
};

function textResponse(body, contentType, { method = 'GET', status = 200 } = {}) {
  return new Response(method === 'HEAD' ? null : body, {
    status,
    headers: {
      ...TEXT_HEADERS,
      'content-type': contentType
    }
  });
}

function buildSitemap(origin) {
  const pages = ['/', '/privacy/', '/support/'];
  const urls = pages
    .map((path) => `<url><loc>${new URL(path, origin).toString()}</loc></url>`)
    .join('');
  return (
    '<?xml version="1.0" encoding="UTF-8"?>' +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls}</urlset>`
  );
}

export async function handleRequest(request) {
  if (!['GET', 'HEAD'].includes(request.method)) {
    return new Response('Method Not Allowed', {
      status: 405,
      headers: {
        allow: 'GET, HEAD',
        'content-type': 'text/plain; charset=utf-8'
      }
    });
  }

  const url = new URL(request.url);
  const redirectTarget = slashRedirects.get(url.pathname);
  if (redirectTarget) {
    return redirectResponse(new URL(redirectTarget, url.origin).toString());
  }

  if (url.pathname === '/robots.txt') {
    return textResponse(
      `User-agent: *\nAllow: /\nSitemap: ${new URL('/sitemap.xml', url.origin).toString()}\n`,
      'text/plain; charset=utf-8',
      { method: request.method }
    );
  }

  if (url.pathname === '/sitemap.xml') {
    return textResponse(buildSitemap(url.origin), 'application/xml; charset=utf-8', {
      method: request.method
    });
  }

  const html = renderRoute(url.pathname, url.origin);
  if (!html) {
    return notFoundResponse({ method: request.method, origin: url.origin });
  }

  return htmlResponse(html, { method: request.method });
}

export default {
  fetch: handleRequest
};
