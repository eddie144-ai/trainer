"""Tests for the matcher. Run: PYTHONPATH=. python3 tests/test_match.py"""
from datetime import datetime, timezone, timedelta
from radar import Tender, Profile, score

NOW = datetime(2026, 10, 8, tzinfo=timezone.utc)


def _t(**kw):
    base = dict(ocid="x", title="", description="", status="active", buyer="B",
                cpv=None, cpv_desc=None, cpv_additional=[], suitability="smeSuitable",
                value_amount=None, deadline=(NOW + timedelta(days=30)).isoformat(),
                region={"country": "SCO"})
    base.update(kw)
    return Tender(**base)


IT = Profile(name="IT", cpv_sectors=["72"], keywords=["software"],
             exclude_keywords=["taxi"], regions=["SCO"], min_value=5000,
             max_value=500000, min_lead_days=5)


def test_sector_and_keyword_match_scores_high():
    t = _t(title="Bespoke software development", cpv="72212000",
           cpv_desc="software", value_amount=50000)
    m = score(IT, t, NOW)
    assert m.score >= 70, (m.score, m.reasons)
    print("ok: strong match scores high", m.score)


def test_exclude_keyword_zeroes():
    t = _t(title="Taxi service for school run", cpv="60000000")
    m = score(IT, t, NOW)
    assert m.score == 0 and "Excluded" in m.reasons[0]
    print("ok: exclusion filter zeroes it")


def test_deadline_too_soon_zeroes():
    t = _t(title="software", cpv="72000000",
           deadline=(NOW + timedelta(days=2)).isoformat())
    m = score(IT, t, NOW)
    assert m.score == 0 and "too soon" in m.reasons[0].lower()
    print("ok: imminent deadline filtered")


def test_wrong_region_penalised_not_zeroed():
    t = _t(title="software development", cpv="72000000",
           region={"country": "ENG"}, value_amount=40000)
    m = score(IT, t, NOW)
    eng = m.score
    t2 = _t(title="software development", cpv="72000000",
            region={"country": "SCO"}, value_amount=40000)
    sco = score(IT, t2, NOW).score
    assert sco > eng, (sco, eng)
    print("ok: in-region outranks out-of-region", sco, ">", eng)


def test_wrong_sector_low():
    t = _t(title="Grounds maintenance and grass cutting", cpv="77314000",
           cpv_desc="grounds maintenance", value_amount=40000)
    m = score(IT, t, NOW)
    assert m.score < 40, (m.score, m.reasons)
    print("ok: off-sector scores low", m.score)


def test_store_dedup_and_prune():
    from radar.store import Store
    from radar import sources
    rel = {"ocid": "o1", "buyer": {"name": "B"}, "tender": {
        "title": "Open thing", "tenderPeriod": {"endDate": (NOW + timedelta(days=20)).isoformat()},
        "classification": {"id": "72000000"}}}
    closed = {"ocid": "o2", "buyer": {"name": "B"}, "tender": {
        "title": "Closed thing", "tenderPeriod": {"endDate": (NOW - timedelta(days=5)).isoformat()},
        "classification": {"id": "45000000"}}}
    recs = sources.normalize_response({"releases": [rel, closed]}, "pcs")
    s = Store(":memory:")
    new, upd = s.upsert_many(recs)
    assert (new, upd) == (2, 0)
    new2, upd2 = s.upsert_many(recs)          # idempotent
    assert new2 == 0 and upd2 == 2
    assert s.prune_closed(NOW) == 1           # the past-deadline one goes
    titles = [t.title for t in s.open_tenders()]
    assert titles == ["Open thing"], titles
    print("ok: store upserts, dedupes, and prunes closed")


def test_keyword_whole_word_only():
    # 'IT' must NOT match inside 'recruitment'. Off-sector + no real keyword -> low.
    t = _t(title="Recruitment services for the council", cpv="79600000",
           region={"country": "SCO"}, value_amount=40000)
    m = score(IT, t, NOW)
    assert "Matches:" not in " ".join(m.reasons), m.reasons
    print("ok: 'IT' does not match inside 'recruitment'")


def test_notify_dry_run_builds_digest():
    from radar import notify
    tenders = [
        _t(title="Bespoke software development platform", cpv="72212000",
           cpv_desc="software", value_amount=60000, region={"nuts": "UKM50"}),
        _t(title="Grounds maintenance", cpv="77314000", value_amount=20000,
           region={"nuts": "UKM50"}),
    ]
    sub = {"email": "x@y.co.uk", "profile": {
        "name": "Test IT Ltd", "cpv_sectors": ["72"], "keywords": ["software"],
        "exclude_keywords": [], "regions": ["UKM"], "min_lead_days": 5}}
    # matcher ranks; at least the software one should clear the bar
    d = notify.build_digest(sub, tenders, bar=40)
    assert d and d["n"] >= 1 and "software" in d["html"].lower()
    res = notify.run([sub], tenders, dry_run=True)
    assert res["sent"] == 1 and res["failed"] == 0
    print("ok: notify builds & dry-run 'sends' a matched digest")


if __name__ == "__main__":
    test_sector_and_keyword_match_scores_high()
    test_exclude_keyword_zeroes()
    test_deadline_too_soon_zeroes()
    test_wrong_region_penalised_not_zeroed()
    test_wrong_sector_low()
    test_keyword_whole_word_only()
    test_store_dedup_and_prune()
    test_notify_dry_run_builds_digest()
    print("\nall tests passed")
