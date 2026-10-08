"""Data sources and a shared OCDS normaliser.

Two live UK sources, both OCDS 1.1 under the Open Government Licence v3.0:

  CONTRACTS_FINDER — England-skewed, UK-wide central feed.
    GET https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?stages=tender&limit=100

  PUBLIC_CONTRACTS_SCOTLAND (PRIMARY for a Scottish business) — mandated by
    Scottish law for all regulated procurement, plus lower-value Quick Quotes.
    GET https://api.publiccontractsscotland.gov.uk/v1/Notices?dateFrom=MM-YYYY&noticeType=2&outputType=0
      noticeType 2 = contract notice, 102 = website contract notice (pull both);
      outputType 0 = OCDS. Paged by month via dateFrom.

Both return {"releases": [...]}. normalize_release() flattens one release to the
dict schema that ocds.Tender consumes, coping with the small differences between
the two feeds (PCS omits CPV text and carries a NUTS region code; Contracts
Finder carries a country code). In production the fetch is a scheduled
server-side GET per source; here we normalise a saved raw response.
"""
from __future__ import annotations
import json as _json

CONTRACTS_FINDER ="https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?stages=tender&limit=100"
PCS_NOTICES = "https://api.publiccontractsscotland.gov.uk/v1/Notices?dateFrom={month}&noticeType={ntype}&outputType=0"

# Which PCS notice types carry live open opportunities (vs awards/corrigenda).
# 2 = OJEU contract notice, 102 = website contract notice, 21/24 = social &
# concession notices. Awards (3/103/104) are excluded from the opportunity feed.
PCS_OPPORTUNITY_NOTICE_TYPES = [2, 102, 21, 24]


def pcs_fetch_plan(months: list[str], ntypes: list[int] | None = None) -> list[str]:
    """Build the set of PCS URLs to pull for good live coverage: every
    opportunity notice type across a rolling window of months (format 'MM-YYYY').
    A notice posted last month can still be open, so pull >=2 months and filter
    to open deadlines on normalise."""
    ntypes = ntypes or PCS_OPPORTUNITY_NOTICE_TYPES
    return [PCS_NOTICES.format(month=m, ntype=n) for m in months for n in ntypes]


def _first_address(release: dict) -> dict:
    for p in (release.get("parties") or []):
        a = p.get("address") or {}
        if a.get("locality") or a.get("region") or a.get("countryName"):
            return a
    return {}


def normalize_release(release: dict, source: str) -> dict:
    t = release.get("tender", {}) or {}
    cls = t.get("classification") or {}
    addl = [c.get("id") for c in (t.get("additionalClassifications") or []) if c.get("id")]
    a = _first_address(release)
    val = t.get("value") or {}
    # Region: PCS uses NUTS (address.region, e.g. UKM50=Aberdeen City);
    # Contracts Finder uses address.countryName (ENG/SCO/...). Keep whatever's there.
    region = {
        "locality": a.get("locality"),
        "nuts": a.get("region"),
        "country": a.get("countryName"),
        "postcode": a.get("postalCode"),
    }
    # suitability may be a string, or a structured object/list across feeds —
    # normalise to short text so it stores cleanly and stays truthy for matching.
    suitability = t.get("suitability")
    if suitability is not None and not isinstance(suitability, str):
        suitability = _json.dumps(suitability, separators=(",", ":"))[:120]
    val_amt = val.get("amount")
    if not isinstance(val_amt, (int, float)):
        val_amt = None
    ocid = release.get("ocid", "")
    if source == "pcs":
        url = f"https://www.publiccontractsscotland.gov.uk/search/show/search_view.aspx?ID={ocid}"
    else:
        url = f"https://www.contractsfinder.service.gov.uk/Notice/{release.get('id','')}"
    return {
        "ocid": ocid,
        "title": t.get("title"),
        "description": (t.get("description") or "")[:600],
        "status": t.get("status"),
        "buyer": (release.get("buyer") or {}).get("name"),
        "cpv": cls.get("id"),
        "cpv_desc": cls.get("description"),
        "cpv_additional": addl,
        "category": t.get("mainProcurementCategory"),
        "suitability": suitability,
        "value_amount": val_amt,
        "value_currency": val.get("currency"),
        "deadline": (t.get("tenderPeriod") or {}).get("endDate"),
        "published": t.get("datePublished") or release.get("date"),
        "region": region,
        "source": source,
        "url": url,
    }


def normalize_response(payload: dict, source: str) -> list[dict]:
    """Take a parsed OCDS response ({'releases': [...]}) → list of normalized dicts,
    de-duplicated by (title, buyer, deadline)."""
    seen, out = set(), []
    for r in payload.get("releases", []):
        rec = normalize_release(r, source)
        key = (rec["title"], rec["buyer"], rec["deadline"])
        if key in seen:
            continue
        seen.add(key)
        out.append(rec)
    return out
