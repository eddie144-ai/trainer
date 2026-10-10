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

1. **Domain** (~£10/yr). Register **`bidbeacon.co.uk`** — checked against Nominet's
   registry on 2026-10-10 and it's **available**. (`bidbeacon.com` is taken, held
   since 2017 — don't wait on it; `.co.uk` is right for a Scottish business.)
   *Why you: it's your money and your asset.*
2. **Stripe** account (stripe.com). Create a **Product** "BidBeacon Founding" →
   recurring **£19/month** → create a **Payment Link**. Paste that link into
   `STRIPE_LINK` in **`site/join.html`**. Then add a **webhook** pointing at
   `https://bidbeacon.co.uk/api/stripe-webhook` for events
   `checkout.session.completed`, `invoice.paid`, `customer.subscription.deleted`;
   copy its signing secret. *Why you: Stripe is in your legal name and tied to
   your bank.*
3. **Supabase** project (free). Run `deploy/schema.sql` in its SQL editor. Copy
   the project URL, the **anon** key (goes in `site/join.html`, safe in the
   browser) and the **service** key (a Vercel secret, never in the browser).
4. **Resend** account (free 3k emails/mo). Verify your domain for sending, get
   an API key. Set the "from" to `alerts@bidbeacon.co.uk`.
5. **Host on Vercel** (free) — import this repo, project root `contractradar/`.
   `vercel.json` serves `site/` as the static site and runs `api/stripe-webhook.js`
   as a function. Add Vercel env vars: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
   `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`. Point `bidbeacon.co.uk` at it.
6. **GitHub Actions** — copy `deploy/ingest-cron.yml` and `deploy/digest-cron.yml`
   into `.github/workflows/`, and add repo secrets: `DATABASE_URL`,
   `SUPABASE_URL`, `SUPABASE_KEY`, `RESEND_API_KEY`.
7. **First run, watched** — trigger the ingest workflow manually
   (`workflow_dispatch`), confirm the store fills, then trigger digests with one
   test subscriber (yourself) to confirm an email arrives. Only then let the
   schedule run.

## Signup + billing: now built (just add your keys)

- **Signup form** — `site/join.html`: members pick sectors/region/keywords; it
  saves a `pending` subscriber to Supabase and sends them to Stripe. Fill its
  three config constants (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `STRIPE_LINK`).
- **Stripe webhook** — `api/stripe-webhook.js`: flips the subscriber to `active`
  on payment and `canceled` when the subscription ends. Verifies the Stripe
  signature. Needs the env vars in step 5.
- So the loop is automatic: join → pay → active → nightly matched digests →
  cancel → stop. No manual subscriber editing required.

> Not deploy-validated here (this sandbox can't run Vercel/Stripe). Do one real
> test checkout with Stripe in **test mode** first, confirm the webhook flips the
> row to `active`, then switch to live keys.

## Compliance (do before taking real payments)

- **ICO registration** (~£40–60/yr) — you're a UK data controller.
- Fill the placeholders in `content/legal/privacy.md` and `terms.md` (your name,
  address, dates), regenerate, and keep the one-click unsubscribe + OGL
  attribution.

## Costs recap

- Now: **~£10** (domain). Everything else free-tier.
- With paying members (~10–30): **~£40–55/mo** (Supabase Pro + Resend when you
  pass free limits). Breaks even at ~2 members at £19.
