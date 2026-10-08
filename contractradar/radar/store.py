"""Tender store — SQLite here, a stand-in for Supabase Postgres in production.

The schema maps 1:1 to a Postgres table, so moving to Supabase is a connection-
string change plus the equivalent DDL. The store is what the nightly ingest
writes to and what the app/digests read from — the "self-updating contract
database" that is Phase 1's deliverable.
"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .ocds import Tender

SCHEMA = """
CREATE TABLE IF NOT EXISTS tenders (
    ocid         TEXT,
    title        TEXT,
    description  TEXT,
    status       TEXT,
    buyer        TEXT,
    cpv          TEXT,
    cpv_desc     TEXT,
    cpv_additional TEXT,   -- JSON array
    category     TEXT,
    suitability  TEXT,
    value_amount REAL,
    value_currency TEXT,
    deadline     TEXT,
    published    TEXT,
    region       TEXT,      -- JSON object
    source       TEXT,
    url          TEXT,
    dedupe_key   TEXT PRIMARY KEY,
    first_seen   TEXT,
    last_seen    TEXT
);
CREATE INDEX IF NOT EXISTS idx_tenders_deadline ON tenders(deadline);
CREATE INDEX IF NOT EXISTS idx_tenders_cpv ON tenders(cpv);
"""


def _dedupe_key(rec: dict) -> str:
    return "|".join(str(rec.get(k) or "") for k in ("title", "buyer", "deadline"))


class Store:
    def __init__(self, path: str | Path = ":memory:"):
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def upsert_many(self, records: list[dict]) -> tuple[int, int]:
        """Insert new tenders, refresh last_seen on ones we've seen before.
        Returns (new, updated)."""
        now = datetime.now(timezone.utc).isoformat()
        new = updated = 0
        for r in records:
            key = _dedupe_key(r)
            exists = self.db.execute(
                "SELECT 1 FROM tenders WHERE dedupe_key=?", (key,)).fetchone()
            if exists:
                self.db.execute("UPDATE tenders SET last_seen=? WHERE dedupe_key=?",
                                (now, key))
                updated += 1
            else:
                self.db.execute(
                    """INSERT INTO tenders (ocid,title,description,status,buyer,cpv,
                       cpv_desc,cpv_additional,category,suitability,value_amount,
                       value_currency,deadline,published,region,source,url,
                       dedupe_key,first_seen,last_seen)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (r.get("ocid"), r.get("title"), r.get("description"), r.get("status"),
                     r.get("buyer"), r.get("cpv"), r.get("cpv_desc"),
                     json.dumps(r.get("cpv_additional") or []), r.get("category"),
                     r.get("suitability"), r.get("value_amount"), r.get("value_currency"),
                     r.get("deadline"), r.get("published"), json.dumps(r.get("region") or {}),
                     r.get("source"), r.get("url"), key, now, now))
                new += 1
        self.db.commit()
        return new, updated

    def prune_closed(self, now: datetime | None = None) -> int:
        """Delete tenders whose deadline has passed. Returns rows removed."""
        now = (now or datetime.now(timezone.utc)).isoformat()
        cur = self.db.execute(
            "DELETE FROM tenders WHERE deadline IS NOT NULL AND deadline < ?", (now,))
        self.db.commit()
        return cur.rowcount

    def open_tenders(self) -> list[Tender]:
        rows = self.db.execute("SELECT * FROM tenders ORDER BY deadline").fetchall()
        out = []
        for row in rows:
            d = dict(row)
            d["cpv_additional"] = json.loads(d.get("cpv_additional") or "[]")
            d["region"] = json.loads(d.get("region") or "{}")
            for extra in ("dedupe_key", "first_seen", "last_seen"):
                d.pop(extra, None)
            out.append(Tender(**d))
        return out

    def stats(self) -> dict:
        n = self.db.execute("SELECT COUNT(*) FROM tenders").fetchone()[0]
        by_src = dict(self.db.execute(
            "SELECT source, COUNT(*) FROM tenders GROUP BY source").fetchall())
        return {"total": n, "by_source": by_src}
