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

CONTRACTS_FINDER = "https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?stages=tender&limit=100"
PCS_NOTICES = "https://api.publiccontractsscotland.gov.uk/v1/Notices?dateFrom={month}&noticeType={ntype}&outputType=0"


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
        "suitability": t.get("suitability"),
        "value_amount": val.get("amount"),
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
