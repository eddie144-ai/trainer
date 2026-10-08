"""Subscribers — who gets a digest, and the business profile to match them on.

Launch: a JSON file (profiles/subscribers.json), one entry per paying member.
Production: the same shape read from a Supabase table via its REST endpoint
(set SUPABASE_URL + SUPABASE_KEY); the Stripe Payment Link webhook adds a row on
payment, and a short profile form fills in sectors/keywords. Until that's wired,
you can add members to the JSON by hand — fine for the first handful.

Each entry:
  {"email": "...", "profile": { ... match.Profile fields ... }}
"""
from __future__ import annotations
import json
import os
import urllib.request
from pathlib import Path

LOCAL = Path(__file__).parent.parent / "profiles" / "subscribers.json"


def load_subscribers() -> list[dict]:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key:
        return _load_supabase(url, key)
    if LOCAL.exists():
        return json.load(open(LOCAL))
    return []


def _load_supabase(base: str, key: str) -> list[dict]:
    req = urllib.request.Request(
        f"{base}/rest/v1/subscribers?select=email,profile&status=eq.active",
        headers={"apikey": key, "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())
