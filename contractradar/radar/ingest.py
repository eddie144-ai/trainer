"""Phase 1 — the self-updating data service.

Fetch live OCDS from Public Contracts Scotland (primary) and Contracts Finder,
normalise, upsert into the store, prune closed. Designed to run nightly on a
schedule (Supabase cron or GitHub Actions — see cron snippet in the repo).

Two input modes:
  - LIVE (production): fetch_live() does plain HTTPS GETs against the open APIs.
  - LOCAL (testing/offline): load_payloads() reads already-saved OCDS responses,
    so the full ingest → store → prune path can be exercised without network.

In this sandbox outbound HTTP is proxied/blocked, so we validate with LOCAL mode
against real saved responses; the LIVE path is what runs in deployment.
"""
from __future__ import annotations
import json
import sys
from datetime import date

from . import sources
from .store import Store


def fetch_live(months: list[str] | None = None) -> list[tuple[dict, str]]:
    """Production fetch: returns [(ocds_payload, source), ...]. Plain stdlib,
    no third-party deps, no scraper — the APIs are open OCDS endpoints."""
    import urllib.request
    if months is None:
        today = date.today()
        prev = (today.replace(day=1))  # first of this month
        pm = (prev.month - 1) or 12
        py = prev.year - (1 if prev.month == 1 else 0)
        months = [f"{today.month:02d}-{today.year}", f"{pm:02d}-{py}"]

    out = []
    for url in sources.pcs_fetch_plan(months):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                out.append((json.loads(r.read().decode()), "pcs"))
        except Exception as e:  # keep going; one bad source isn't fatal
            print(f"  WARN pcs fetch failed: {e}", file=sys.stderr)
    try:
        with urllib.request.urlopen(sources.CONTRACTS_FINDER, timeout=60) as r:
            out.append((json.loads(r.read().decode()), "contracts_finder"))
    except Exception as e:
        print(f"  WARN contracts_finder fetch failed: {e}", file=sys.stderr)
    return out


def load_payloads(specs: list[tuple[str, str]]) -> list[tuple[dict, str]]:
    """LOCAL mode: specs = [(path_to_saved_ocds_json, source), ...]."""
    out = []
    for path, source in specs:
        raw = open(path).read()
        # saved firecrawl results wrap the body in {"rawHtml": "..."}; unwrap if so
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict) and "rawHtml" in obj:
                obj = json.loads(obj["rawHtml"])
        except json.JSONDecodeError:
            obj = json.loads(raw)
        out.append((obj, source))
    return out


def ingest(store: Store, payloads: list[tuple[dict, str]]) -> dict:
    total_new = total_upd = 0
    for payload, source in payloads:
        recs = sources.normalize_response(payload, source)
        n, u = store.upsert_many(recs)
        total_new += n
        total_upd += u
    pruned = store.prune_closed()
    return {"new": total_new, "updated": total_upd, "pruned": pruned, **store.stats()}


if __name__ == "__main__":
    # LIVE run (deployment). In the sandbox this will warn + collect nothing.
    store = Store("data/contracts.db")
    result = ingest(store, fetch_live())
    print(json.dumps(result, indent=2))
