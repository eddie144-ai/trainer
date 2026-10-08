# ContractRadar — MVP (free build, nothing deployed)

Matches **live UK public-sector contract opportunities** to a specific SME
profile and ranks them by fit, so a small business sees the handful worth
bidding on instead of scrolling hundreds. Built as the no-spend MVP to prove
the product works before committing money or putting anything public.

## Why this product (recap)

Chosen over charity grant-matching because the buyer (an SME chasing public
contracts) **has a budget and an obvious ROI** — one won contract is worth
thousands to millions — whereas grant-seeking charities are cash-poor, and the
grant space has a free incumbent (Funding Scotland). The data is also the
cleanest available: Contracts Finder publishes an open OCDS API.

## What runs today (on real data)

```bash
PYTHONPATH=. python3 run.py --profile aberdeen_it --source pcs --html site/index.html
PYTHONPATH=. python3 run.py --profile aberdeen_facilities --source pcs
PYTHONPATH=. python3 run.py --profile aberdeen_it --source contracts_finder
PYTHONPATH=. python3 tests/test_match.py      # 6 tests, all pass
```

- **Data:** `data/contracts_snapshot.json` — 100 real tenders pulled live from
  Contracts Finder (OCDS, Open Government Licence v3.0).
- **Pipeline:** OCDS parse → relevance score vs a business profile → ranked
  digest (text email body + a static HTML page).
- **Matcher** combines CPV sector, keywords, region, contract value, SME
  suitability, and deadline lead-time into a 0–100 fit score with reasons.
  Hard filters (exclusions, imminent deadline, SME-suitability) zero a tender out.
- **Two sample profiles** (Aberdeen IT SME, Scottish facilities SME) produce
  correctly differentiated, sensibly ranked results.

## Sources (both live, both OCDS / Open Government Licence v3.0)

- **Public Contracts Scotland (PRIMARY for Scotland)** — `api.publiccontractsscotland.gov.uk/v1/Notices`.
  Mandated by Scottish law for all regulated procurement + Quick Quotes. Carries
  NUTS region codes (UKM = Scotland, UKM50 = Aberdeen City) so results can be
  filtered to the North-East. This is the right source for an Aberdeen business.
- **Contracts Finder (supplementary)** — UK-wide central feed, England-skewed.

`radar/sources.py` normalises both feeds to one schema and de-dupes by
(title, buyer, deadline). Live snapshots are bundled in `data/`.

**Coverage:** the PCS snapshot is built from a rolling window — opportunity
notice types (contract + website + social/concession) across the current and
previous month — then filtered to still-open deadlines (`pcs_fetch_plan()`).
That took the live working set from ~22 (one type, one month) to **194 open
Scottish contracts**, ~8 of them in the Aberdeen area (NUTS UKM5x). Production
runs this plan on a schedule and widens the month window as needed.

## Honest findings from real runs

1. **Scotland barely appears on Contracts Finder** — the 100 most-recent
   national tenders were all English. Confirmed: Scottish contracts live on PCS.
   → PCS is now the primary integrated source (`--source pcs`, the default).
2. **PCS omits CPV text labels** (code only) — we supply our own division labels.
3. **Short-keyword false positives** (e.g. "IT" inside "recruitment") — fixed
   with whole-word matching (`tests/test_match.py` guards it).
4. **Duplicates** exist in feeds — deduped on normalise.
5. **Value/region often unstated** on smaller notices — scoring treats unknowns
   as neutral rather than wrongly excluding.

## Architecture (production shape)

- `radar/ocds.py` — OCDS fetch (documented) + normalise to `Tender`.
- `radar/match.py` — `Profile` + transparent scorer (an LLM semantic pass can
  layer on top for description-level fit).
- `radar/digest.py` — email body + HTML page.
- Production: scheduled multi-source fetch (PCS + Contracts Finder + Find a
  Tender) → dedup → store → nightly per-subscriber match → email.

## Deliberately NOT built yet (needs your go + spend)

Auth, Stripe, a hosted site, scheduled email sending, programmatic SEO pages,
and PCS integration. None of that exists because nothing is deployed and no
money has been spent — per the plan, you see it work first.

## Competitive wedge (and the honest risk)

Incumbents (Stotles, Tracker, BiP) target enterprise procurement teams at
enterprise prices; Contracts Finder/PCS native search is free but has no
per-business relevance ranking or tailored alerts. The wedge is an affordable,
well-matched alert service for *small* Scottish/UK businesses. Risk: free
native search is "good enough" for some, so the matching + proactive alerts
must be clearly better. The SEO funnel ("public sector contracts for [sector]
in Scotland") is the acquisition path.

*Not affiliated with GOV.UK or Public Contracts Scotland. Data under OGL v3.0.*
