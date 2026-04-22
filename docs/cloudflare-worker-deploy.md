# LocalLens Cloudflare Worker Deploy

## Publish the Public Site

```bash
npm install
npm run deploy:public-site
```

The Worker serves:

- `/`
- `/privacy/`
- `/support/`
- `/robots.txt`
- `/sitemap.xml`

## Regenerate Store Metadata

The production Worker is currently live at `https://locallens-public-site.rapidapis.workers.dev/`.

If that hostname changes after a redeploy, export the new base and regenerate the store payloads:

```bash
export LOCALLENS_PUBLIC_SITE_BASE="https://locallens-public-site.rapidapis.workers.dev"
python3 scripts/generate_launch_manifest.py --repo-root . --out dist/launch-manifest.json
python3 scripts/generate_listing_copy.py --repo-root . --manifest dist/launch-manifest.json --out dist/store-listing.json
```

The Chrome Web Store privacy-policy link and reviewer-support link come from `dist/launch-manifest.json` and `dist/store-listing.json`, so both files must be regenerated after the Worker URL is known.
