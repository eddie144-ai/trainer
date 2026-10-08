#!/usr/bin/env python3
"""ContractRadar MVP — match live UK public contracts to a business profile.

    PYTHONPATH=. python3 run.py --profile aberdeen_it
    PYTHONPATH=. python3 run.py --profile scotland_facilities --html site/index.html

Uses the bundled real Contracts Finder snapshot (data/contracts_snapshot.json).
In production, swap load_snapshot() for a live OCDS fetch on a schedule.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from radar import load_snapshot, Profile, rank, digest

ROOT = Path(__file__).parent


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--profile", default="aberdeen_it")
    p.add_argument("--source", default="pcs", choices=["pcs", "contracts_finder"],
                   help="pcs = Public Contracts Scotland (primary for Scotland)")
    p.add_argument("--data", default=None, help="override snapshot JSON path")
    p.add_argument("--db", default=None, help="read tenders from a SQLite store instead")
    p.add_argument("--bar", type=int, default=40)
    p.add_argument("--html", default=None, help="also write an HTML page here")
    args = p.parse_args()

    profiles = json.load(open(ROOT / "profiles/sample_profiles.json"))
    if args.profile not in profiles:
        raise SystemExit(f"unknown profile. choose from: {', '.join(profiles)}")
    profile = Profile(**profiles[args.profile])

    if args.db:
        from radar.store import Store
        tenders = Store(args.db).open_tenders()
    else:
        snap = args.data or str(ROOT / ("data/pcs_snapshot.json" if args.source == "pcs"
                                        else "data/contracts_snapshot.json"))
        tenders = load_snapshot(snap)
    matches = rank(profile, tenders)

    print(digest.text_digest(profile.name, matches, bar=args.bar))

    cleared = sum(1 for m in matches if m.score >= args.bar)
    print(f"\n(scanned {len(tenders)} live tenders · {cleared} cleared the fit bar "
          f">= {args.bar} · showing top matches)")

    if args.html:
        out = Path(args.html)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(digest.html_page(profile.name, matches, bar=args.bar))
        print(f"wrote demo page: {out}")


if __name__ == "__main__":
    main()
