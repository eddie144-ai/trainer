"""Export the live store to site/tenders.json — the file the public tool and
the SEO generator read. Runs in the nightly cron between ingest and seo.

    PYTHONPATH=. python3 -m radar.export
"""
from __future__ import annotations
import json
import os
from pathlib import Path

from .store import Store
from .ocds import cpv_label

OUT = Path(__file__).parent.parent / "site" / "tenders.json"


def export(db: str | None = None) -> int:
    db = db or os.environ.get("BIDBEACON_DB", "data/contracts.db")
    rows = []
    for t in Store(db).open_tenders():
        if not t.title:
            continue
        rows.append({
            "title": t.title, "buyer": t.buyer,
            "cpv2": (t.cpv or "")[:2], "sector": cpv_label(t.cpv, t.cpv_desc),
            "value": t.value_amount, "deadline": (t.deadline or "")[:10],
            "days": t.days_to_deadline(), "category": t.category,
            "locality": (t.region or {}).get("locality"),
            "nuts": (t.region or {}).get("nuts"), "country": (t.region or {}).get("country"),
            "source": t.source, "url": t.url,
        })
    OUT.write_text(json.dumps(rows, separators=(",", ":")))
    return len(rows)


if __name__ == "__main__":
    print(f"exported {export()} tenders to {OUT}")
