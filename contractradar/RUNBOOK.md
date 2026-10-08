# BidBeacon — Go-Live Runbook

The lean launch reuses the tested Python (ingest + matcher + digest sender) and
avoids custom billing code. What Claude built is listed first; then the steps
only **you** can do (accounts, money, your name on a public site).

## Architecture at launch

```
GitHub Actions (free cron)                 Supabase (free tier)
  • nightly: python -m radar.ingest  ─────▶ Postgres: tenders + subscribers
  • nightly: python -m radar.notify  ──┐
                                        └──▶ Resend (email the matched digests)
Static site (free host: Vercel/Netlify/Pages)
  • site/bidbeacon.html  ── "Join" ──▶ Stripe Payment Link (£19/mo)  ──▶ webhook adds subscriber
```

No server to run, no billing code to maintain. Everything starts on free tiers;
the only certain cost is the domain (~£10/yr).

## Built and tested (in this repo)

- `radar/ingest.py` — nightly fetch PCS + Contracts Finder → store (tested).
- `radar/store.py` — Postgres-shaped store, dedupe + prune (tested).
- `radar/match.py` — relevance scorer (tested).
- `radar/notify.py` + `radar/subscribers.py` — per-member matched digests via
  Resend (matching/rendering tested; the Resend POST needs your key).
- `site/bidbeacon.html` — the public free tool (live preview already shown).
- `deploy/schema.sql`, `deploy/ingest-cron.yml`, `deploy/digest-cron.yml`.

> Not yet validated live: the deploy itself (this sandbox can't reach the APIs
> or run a deploy). First real ingest run should be watched — see step 7.

## Your steps (accounts, money, your name — Claude can't do these)

1. **Domain** (~£10/yr). Register `bidbeacon.co.uk` (and `.com` if free) at any
   registrar. *Why you: it's your money and your asset.*
2. **Stripe** account (stripe.com). Create a **Product** "BidBeacon Founding" →
   recurring **£19/month** → create a **Payment Link**. Paste that link into
   `STRIPE_LINK` in `site/bidbeacon.html`. *Why you: Stripe is in your legal
   name and tied to your bank.*
3. **Supabase** project (free). Run `deploy/schema.sql` in its SQL editor. Copy
   the project URL + service key.
4. **Resend** account (free 3k emails/mo). Verify your domain for sending, get
   an API key. Set the "from" to `alerts@bidbeacon.co.uk`.
5. **Host the site** — import this repo to Vercel/Netlify (free), serve
   `site/`. Point the domain at it.
6. **GitHub Actions** — copy `deploy/ingest-cron.yml` and `deploy/digest-cron.yml`
   into `.github/workflows/`, and add repo secrets: `DATABASE_URL`,
   `SUPABASE_URL`, `SUPABASE_KEY`, `RESEND_API_KEY`.
7. **First run, watched** — trigger the ingest workflow manually
   (`workflow_dispatch`), confirm the store fills, then trigger digests with one
   test subscriber (yourself) to confirm an email arrives. Only then let the
   schedule run.

## Still to wire after first customers (not needed to launch)

- **Stripe webhook → subscriber row.** At launch you can add the first few
  members to `profiles/subscribers.json` (or the Supabase table) by hand after
  they pay — fine for the first handful. Automate the webhook once volume
  justifies it.
- **Profile form** so members pick their own sectors/keywords (a small Supabase
  insert). Until then, set their profile when you add them.
- **Compliance** (from the launch plan): ICO registration (~£40–60/yr),
  privacy policy + one-click unsubscribe, keep the OGL attribution in the footer.

## Costs recap

- Now: **~£10** (domain). Everything else free-tier.
- With paying members (~10–30): **~£40–55/mo** (Supabase Pro + Resend when you
  pass free limits). Breaks even at ~2 members at £19.
