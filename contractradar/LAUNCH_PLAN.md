# ContractRadar — Costed Launch Plan

*The plan you say yes/no to before any money is spent. Prices are current
(checked Oct 2026); where a provider bills in USD it's marked, ~£1 ≈ $1.27.*

---

## 1. TL;DR — the decision

Take the working MVP (matches live Scottish public contracts to an SME profile)
and turn it into a running, paid product: a hosted site, scheduled data pulls,
email digests, Stripe billing, and an SEO content engine.

- **One-off to launch:** ~**£10** (a domain). That's it.
- **Running cost, pre-revenue:** **£0/mo** — everything starts on free tiers.
- **Running cost, once you have paying users:** **~£40–55/mo** (≈ breaks even
  at ~2 paying customers).
- **My build time:** ~**3–4 focused phases** (detailed below). I write the code.
- **Realistic path to first £:** month ~2–3 (community/outreach), with SEO
  compounding over months 3–9 toward the **£1–5k MRR** first milestone.

The honest part: **money is not the blocker — distribution is.** The stack is
cheap and I can build it. Whether it earns depends on the SEO/content grind and
whether SMEs pay for better matching over free native search. Kill-criteria in §9.

## 2. Recommended stack (and why)

| Layer | Choice | Why | Cost |
|---|---|---|---|
| Web app + hosting | **Next.js on Vercel** | Free Hobby tier covers launch; I write it, full control, lowest recurring cost | £0 → $20/mo (USD) only if you outgrow Hobby |
| Database + Auth | **Supabase** | Postgres + built-in auth + cron; free tier real (500MB, 50k users) | £0 → $25/mo (USD) when off free tier |
| Scheduled fetch | **Supabase cron / GitHub Actions** | Runs the PCS + Contracts Finder pulls nightly | £0 |
| Email digests | **Resend** | 3,000 emails/mo free (100/day), then $20/mo for 50k | £0 → $20/mo (USD) |
| Payments | **Stripe** | No monthly fee; UK cards **1.5% + 20p**, international 2.5% + 20p | per-transaction only |
| AI scoring | **Claude Haiku** | Semantic fit on a heuristic-prefiltered shortlist (see §5) | ~£0.20–0.50 / user / mo |
| Domain | `.co.uk` or `.com` | — | ~£8–12 one-off/yr |

**Data costs £0** — PCS and Contracts Finder are open OCDS APIs under OGL v3.0.
No Firecrawl needed in production (that was just my fetch tool here); the app
calls the APIs directly server-side.

*Alternative (faster scaffold, higher recurring):* I also have **Lovable** and
**Base44** available — they'd stand up the UI/auth/Stripe faster but add a
~£20–50/mo subscription and less control. I recommend the code-it-myself stack
for a bootstrapped solo founder; I can switch if you'd prefer speed over cost.

## 3. Costed breakdown by stage

| | Pre-launch (building) | Early (~10–30 paying) | Growth (~100 paying) |
|---|---|---|---|
| Vercel | £0 (Hobby) | £0–£16 ($20) | ~£16 ($20) |
| Supabase | £0 (Free) | ~£20 ($25) | ~£20 ($25) |
| Resend | £0 (Free 3k) | £0–£16 ($20) | ~£16 ($20) |
| Claude (AI scoring) | ~£0 | ~£5–15 | ~£25–50 |
| Domain (amortised) | ~£1 | ~£1 | ~£1 |
| Stripe fees | £0 | ~1.5%+20p/txn | ~1.5%+20p/txn |
| **Total /mo** | **~£0–1** | **~£40–55** | **~£80–110** |

The £50–150/mo I quoted earlier was the honest ceiling; reality starts near £0
and only rises **after** revenue does.

## 4. Pricing & unit economics

- **Launch price: £29/mo** (or £19/mo founding-member rate for the first ~20 to
  build reviews). Annual option £290/yr (2 months free) to cut churn.
- **Per-subscriber economics at £29/mo:** Stripe takes ~£0.64 → **~£28.36 net**;
  infra+AI cost per user is well under £2/mo at any realistic scale →
  **~95% gross margin.**
- **Covers all infra at ~2 paying users.** Every user after that is ~£28 margin.
- **£1k MRR ≈ 35 users @ £29; £5k MRR ≈ 170 users.** With a useful free tool
  converting ~1–3%, that needs ~1,200–6,000 free users/month — the SEO job.
- **Free tier (the funnel):** public search of current Scottish contracts, no
  login. Paid unlocks: saved profile, matched email digests, deadline reminders,
  North-East filter, multi-source (adds Contracts Finder/Find a Tender).

## 5. Keeping the AI-scoring cost honest

Don't LLM-score all 194 tenders per user per day. Instead:
1. **Heuristic pre-filter** (the matcher already built) cuts ~194 → a ~20–30
   shortlist per profile — free.
2. **LLM scores only the shortlist**, and each tender's semantic summary is
   computed **once and cached**, not per user.
→ ~£0.20–0.50 per user per month even running daily. Scales linearly, stays <2%
of revenue.

## 6. Build timeline (what I do)

- **Phase 1 — Data service (≈ runs itself):** productionise the fetch (PCS all
  opportunity types + rolling window + Contracts Finder), nightly cron into
  Supabase, dedup, open-only. *Output: a self-updating contract database.*
- **Phase 2 — App + free tool:** Next.js site, public contract search (the SEO
  funnel), the matcher behind it. *Output: a public site worth indexing.*
- **Phase 3 — Accounts + digests + billing:** Supabase auth, profile builder,
  nightly matched email via Resend, Stripe subscription + paywall.
  *Output: it can take money and run unattended.*
- **Phase 4 — SEO engine:** programmatic pages (see §7) + first articles.
  *Output: the acquisition machine.*

I'd build and show each phase; you authorise spend only when a phase needs a
paid tier (none do at launch).

## 7. SEO / content launch (your only channel — so it's the real work)

- **Programmatic pages** generated from the live DB, each genuinely useful:
  - `/scotland/[sector]` — "IT & software public contracts in Scotland"
  - `/[council]` — "Aberdeen City Council contract opportunities"
  - `/cpv/[code]` — per-sector live listings
  Hundreds of long-tail pages, auto-refreshed, each funnelling to the free tool.
- **Cornerstone articles:** "How to win your first public-sector contract in
  Scotland," "PCS vs Contracts Finder vs Find a Tender," "What a good tender
  response looks like." These rank for intent and build trust.
- **Community seeding (non-spam):** answer real questions in Scottish
  small-business / Federation of Small Businesses / r/scotland-business type
  venues, linking the free tool only where it genuinely helps.
- Timeline: SEO is slow — **3–6 months to meaningful organic traffic.** First
  users likely come from direct outreach/community before SEO lands.

## 8. Legal & compliance (UK specifics — not optional)

- **Data licence:** PCS/Contracts Finder are OGL v3.0 → free commercial use
  **with attribution**. We display "Contains public sector information licensed
  under the Open Government Licence v3.0" and never imply GOV.UK affiliation.
- **GDPR / email:** subscriber emails need clear consent + one-click unsubscribe
  (Resend handles headers). A privacy policy + terms (simple, standard).
- **ICO registration:** as a UK data controller you'll likely need to register
  with the ICO (~£40–60/yr) — small, but real. Flagging it honestly.
- **Company:** can start as sole trader; Stripe works either way. No need to
  incorporate to launch.

## 9. Risks & kill-criteria (unchanged, still honest)

1. **Free native search is "good enough" for some** → matching + proactive
   alerts must be clearly better. *Test: do free users convert at ≥1%?*
2. **SEO never ranks** → *kill/pivot channel if <~500 organic visits/mo by month 4.*
3. **No willingness to pay** → *kill-criterion: <10 paying users after ~1,000
   engaged free users means the value prop is wrong.*
4. **Data reliability** → PCS/CF APIs are stable & official; low risk now proven.

Because burn is ~£0 pre-revenue, failing is cheap — we'd know within a quarter.

## 10. What I need from you to start

1. **A go on the spend** — realistically £0 until you have users, then the free
   tiers above. One-off: a domain (~£10). You approve each paid tier when hit.
2. **Two small decisions:** a **brand name** (I'll shortlist + check domains with
   the tools I have) and the **launch price** (I recommend £19 founding / £29
   standard).
3. Nothing else. I build Phase 1–2 (all free), you see the public site working,
   *then* decide on billing + domain.

*This is the honest best-odds shot: ~£0 to find out, real open data, a defensible
matching wedge, and a channel that fits how you can reach people. Most micro-SaaS
still fail — the kill-criteria make sure we fail cheap if it's going to.*
