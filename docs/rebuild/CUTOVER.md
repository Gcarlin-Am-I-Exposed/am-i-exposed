# Cutover runbook — Astro rebuild → production

Live site: www.am-i-exposed.com (Vercel project `am-i-exposed`, team `am-i-exposed`), production branch **main**. Rebuild lives on branch **redesign/astro-rebuild** (Astro app in `web/`). Cutover = production starts serving the Astro build.

## How it works
`vercel.json` on the rebuild branch sets `buildCommand: cd web && npm run build` + `outputDirectory: web/dist`, while `api/` still deploys as functions from the repo root. Merging the branch to `main` makes the next production deploy build Astro. Nothing about the serverless functions, env vars, crons, Supabase, Stripe or Brevo changes.

## Ready (done + verified on the preview)
- All live routes ported EN+ES: home, 1,099 settlement pages + hub, pricing, 4 legals, 2 SEO articles, daily-hack, manage, monitoring, internal dashboard. SEO parity checked (titles/descriptions/JSON-LD identical on sampled pages).
- Real scan verified end-to-end on the preview (same-origin `/api/check-email`, HIBP test account → inline result). Monitoring checkout wired to `/api/checkout?plan=monitoring_*`; Full Report to `?plan=report`.
- `api/` functions unchanged — 10/12 Hobby functions; crons (`/api/keepalive`, `/api/healthcheck`) unchanged.
- Dynamic `/sitemap.xml` (1,118 URLs, hreflang) + `robots.txt`.
- **Data pipeline fixed:** `refresh-open-settlements.yml` now also runs `build-settlement-pages.py --export-json`, so `data/settlements-content.json` is regenerated and committed on each weekly refresh → production rebuilds Astro with fresh settlement data. daily-hack reads `daily-hack.json`/`data/radar.json` (committed by `radar-daily.yml`), so it stays fresh too.
- **Letter pages:** `/settlements/letter-*` 301 → `/settlements/` (hub has letter-anchor nav), so old URLs don't 404.
- Branded 404 page.

## Blockers to decide BEFORE cutover
1. **Password check not ported.** The live home has two checks: email (ported) AND password (browser-side k-anonymity to api.pwnedpasswords.com). The Astro home only has the email scan. Decide: port it before cutover, or launch without it (feature regression). Recommended: port it first — it's a core feature of the current home.
2. **Privacy policy.** Still says "operated from Peru / data controller based in Lima" (preserved verbatim). Reconcile with the US sole-prop setup before cutover (legal text, owner's call).

## Cutover steps (only after the blockers are resolved/accepted)
1. Final preview smoke test (logged into Vercel or via a `get_access_to_vercel_url` share link): home EN/ES, one settlement, pricing EN/ES, one legal, daily-hack, the real scan, monitoring checkout reaches Stripe, manage opens the Stripe portal, dashboard login with `DASHBOARD_PASSWORD`.
2. Merge `redesign/astro-rebuild` → `main` (squash-merge, per project convention). This carries the Astro app + the `vercel.json` build config.
3. Vercel auto-builds a **production** deploy from `main`. Wait for READY.
4. Verify production on www.am-i-exposed.com: home, a settlement, the real scan (POST `/api/check-email` → 200), `/sitemap.xml`, `/robots.txt`, a redirect (`/en/faq` → `/faq/`), a letter redirect (`/settlements/letter-a/` → `/settlements/`).

## Rollback (fast)
- **Instant:** in Vercel → the project's Deployments, promote the previous (old static) production deployment back to production. No rebuild needed.
- **Or:** revert the merge commit on `main` and push; Vercel rebuilds the old static site. The old root files (`index.html`, `app.js`, `content.css`, `settlements/*`, etc.) are still in the repo, so the old site is fully recoverable.

## Post-cutover cleanup (later, not blocking)
- Stop the Python pipeline from regenerating the now-unused root HTML (`settlements/*/index.html`, root `sitemap.xml`) — harmless noise otherwise.
- Remove old root static files once confident.
- Add Stripe **test** keys scoped to the Preview environment so preview checkouts don't use live keys.
- Minor polish: daily-hack sector labels render in Spanish on the EN page.

## What does NOT change at cutover
Serverless functions, env vars/secrets, Supabase (`morosdhhoznicppmrqyr`), Stripe products/prices, Brevo, Zoho, the alert crons, and the GitHub Actions data jobs (aside from the one added `--export-json` line).
