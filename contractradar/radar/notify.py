"""Digest sender — the one new piece Phase 3 needs.

For each subscriber: rank the live tenders against their profile (reusing the
tested matcher), render a digest, and email it via Resend. Rendering and
matching run and are tested offline; only the final HTTPS POST to Resend needs
a real API key, so send() is isolated and dry_run exercises everything else.

Launch architecture (see RUNBOOK.md): a GitHub Actions cron runs ingest then
this sender nightly. Subscribers come from radar.subscribers; tenders from the
store the ingest fills.
"""
from __future__ import annotations
import json
import os
import urllib.request

from .match import Profile, rank
from . import digest as digest_render
from .ocds import Tender

RESEND_ENDPOINT = "https://api.resend.com/emails"


def build_digest(sub: dict, tenders: list[Tender], bar: int = 40) -> dict | None:
    """Return {to, subject, html, text, n} for a subscriber, or None if nothing
    clears the bar (we don't send empty emails — that's how you train unsubscribes)."""
    profile = Profile(**sub["profile"])
    matches = rank(profile, tenders)
    hits = [m for m in matches if m.score >= bar]
    if not hits:
        return None
    subject = (f"{len(hits)} public contract{'s' if len(hits) != 1 else ''} "
               f"match {profile.name.split('(')[0].strip()}")
    return {
        "to": sub["email"],
        "subject": subject,
        "html": digest_render.html_page(profile.name, matches, bar=bar),
        "text": digest_render.text_digest(profile.name, matches, bar=bar),
        "n": len(hits),
    }


def send(api_key: str, sender: str, to: str, subject: str, html: str) -> dict:
    """POST one email to Resend. Raises on HTTP error."""
    body = json.dumps({"from": sender, "to": [to], "subject": subject,
                       "html": html}).encode()
    req = urllib.request.Request(RESEND_ENDPOINT, data=body, method="POST",
                                 headers={"Authorization": f"Bearer {api_key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def run(subscribers: list[dict], tenders: list[Tender], *, dry_run: bool = True,
        bar: int = 40) -> dict:
    api_key = os.environ.get("RESEND_API_KEY", "")
    sender = os.environ.get("BIDBEACON_FROM", "BidBeacon <alerts@bidbeacon.co.uk>")
    sent = skipped = failed = 0
    log = []
    for sub in subscribers:
        d = build_digest(sub, tenders, bar)
        if d is None:
            skipped += 1
            log.append(f"skip  {sub['email']}: no matches today")
            continue
        if dry_run or not api_key:
            log.append(f"DRY   {sub['email']}: would send '{d['subject']}' ({d['n']} matches)")
            sent += 1
            continue
        try:
            send(api_key, sender, d["to"], d["subject"], d["html"])
            sent += 1
            log.append(f"sent  {sub['email']}: {d['n']} matches")
        except Exception as e:
            failed += 1
            log.append(f"FAIL  {sub['email']}: {e}")
    return {"sent": sent, "skipped": skipped, "failed": failed, "log": log}


if __name__ == "__main__":
    from .store import Store
    from .subscribers import load_subscribers
    live = not os.environ.get("DRY_RUN")  # default to real send in CI; DRY_RUN=1 to preview
    tenders = Store(os.environ.get("BIDBEACON_DB", "data/contracts.db")).open_tenders()
    result = run(load_subscribers(), tenders, dry_run=not live)
    print(json.dumps({k: v for k, v in result.items() if k != "log"}))
    print("\n".join(result["log"]))
