"""The matcher — the actual product value.

Contracts Finder's own search is keyword + filters. The value we add is a
RELEVANCE SCORE against a specific business profile, combining sector (CPV),
keywords, region, contract value and SME-suitability into one ranked list, so
an SME sees the handful of tenders worth their time instead of scrolling 100s.

Scoring is transparent and tunable. An optional LLM pass (semantic fit on the
description) can layer on top in production; the heuristic here runs anywhere.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from .ocds import Tender, cpv_label


def _word_hit(word: str, text: str) -> bool:
    """Whole-word, case-insensitive match. Stops short keywords like 'IT'
    matching inside 'recruitment'."""
    return re.search(rf"(?<![a-z0-9]){re.escape(word.lower())}(?![a-z0-9])", text) is not None


@dataclass
class Profile:
    name: str
    cpv_sectors: list[str]          # 2-digit CPV prefixes, e.g. ["72","48"] for IT
    keywords: list[str]             # positive signal in title/description
    exclude_keywords: list[str]     # hard disqualifiers
    regions: list[str]              # OCDS country codes, e.g. ["SCO"]; empty = anywhere
    min_value: float | None = None  # skip contracts below this (too small to bother)
    max_value: float | None = None  # skip contracts above this (can't deliver)
    require_sme_suitable: bool = False
    min_lead_days: int = 3          # need at least this many days to bid


@dataclass
class Match:
    tender: Tender
    score: int
    reasons: list[str]


def score(profile: Profile, t: Tender, now: datetime | None = None) -> Match:
    now = now or datetime.now(timezone.utc)
    reasons: list[str] = []

    # --- hard filters first: if any fail, it's a 0 (won't be shown) ---
    dloss = t.days_to_deadline(now)
    if dloss is not None and dloss < profile.min_lead_days:
        return Match(t, 0, [f"Deadline too soon ({dloss}d) to prepare a bid"])
    text = f"{t.title or ''} {t.description or ''}".lower()
    hit_excl = [w for w in profile.exclude_keywords if _word_hit(w, text)]
    if hit_excl:
        return Match(t, 0, [f"Excluded by your filter: {', '.join(hit_excl)}"])
    if profile.require_sme_suitable and not t.suitability:
        return Match(t, 0, ["Not flagged SME/VCSE-suitable"])

    s = 0
    # --- sector (CPV) is the strongest signal ---
    if profile.cpv_sectors:
        overlap = t.all_cpv_sectors & set(profile.cpv_sectors)
        if overlap:
            s += 40
            reasons.append(f"Your sector (CPV {', '.join(sorted(overlap))}: {cpv_label(t.cpv, t.cpv_desc)})")
        else:
            reasons.append(f"Different sector (CPV {t.cpv_sector}: {cpv_label(t.cpv, t.cpv_desc)})")

    # --- keywords (whole-word) ---
    hits = [w for w in profile.keywords if _word_hit(w, text)]
    if hits:
        s += min(30, 12 * len(hits))
        reasons.append(f"Matches: {', '.join(hits[:4])}")

    # --- region. NUTS is hierarchical: UK > UKM (Scotland) > UKM5 (NE Scotland)
    #     > UKM50 (Aberdeen City). A profile region like "UKM" prefix-matches all
    #     of Scotland; a bare "UK"/"GB" token means UK-wide (an SME can still bid). ---
    NATIONAL = {"UK", "GB", "UNITED KINGDOM"}
    if profile.regions:
        wanted = [w.upper() for w in profile.regions]
        tokens = t.region_tokens
        if not tokens:
            s += 8
            reasons.append("No fixed region (likely deliverable from anywhere)")
        elif tokens & NATIONAL:
            s += 12
            reasons.append("UK-wide opportunity (you can bid)")
        elif any(tok.startswith(w) for tok in tokens for w in wanted):
            hit = next(tok for tok in tokens if any(tok.startswith(w) for w in wanted))
            s += 15
            reasons.append(f"In your region ({hit})")
        else:
            s -= 10
            reasons.append(f"Outside your region ({', '.join(sorted(tokens))})")

    # --- value fit ---
    v = t.value_amount
    if v is not None:
        if (profile.min_value is None or v >= profile.min_value) and \
           (profile.max_value is None or v <= profile.max_value):
            s += 10
            reasons.append(f"Value in range (£{v:,.0f})")
        else:
            s -= 5
            reasons.append(f"Value out of range (£{v:,.0f})")

    # --- SME suitability bonus ---
    if t.suitability:
        s += 5
        reasons.append("Flagged SME/VCSE-suitable")

    if dloss is not None:
        reasons.append(f"{dloss} days to deadline")

    return Match(t, max(0, min(100, s)), reasons)


def rank(profile: Profile, tenders: list[Tender], now: datetime | None = None) -> list[Match]:
    matches = [score(profile, t, now) for t in tenders]
    matches.sort(key=lambda m: m.score, reverse=True)
    return matches
