"""Data model + loader for UK public contract notices (OCDS).

Source: Contracts Finder OCDS Search API
  https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search?stages=tender
  Open Government Licence v3.0. Returns OCDS 1.1 releases as JSON.

In production the fetch is a plain server-side HTTPS GET against that endpoint
(paginated via the OCDS pagination extension), normalised with the same code
below. The bundled data/contracts_snapshot.json is a REAL pull (100 live
tenders) so the pipeline runs offline here.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


# Human labels for the top-level CPV divisions (first 2 digits). PCS publishes
# only the code, so we fill the text ourselves for a readable digest.
CPV_DIVISIONS = {
    "03": "Agriculture & food", "09": "Energy & fuels", "14": "Mining & minerals",
    "15": "Food & beverages", "18": "Clothing & textiles", "22": "Printed matter",
    "24": "Chemicals", "30": "Office & IT equipment", "31": "Electrical equipment",
    "32": "Comms & broadcast equipment", "33": "Medical equipment", "34": "Transport equipment",
    "35": "Security & defence", "37": "Musical/sports goods", "38": "Lab & precision equipment",
    "39": "Furniture & furnishings", "41": "Water", "42": "Industrial machinery",
    "43": "Mining/construction machinery", "44": "Construction materials", "45": "Construction work",
    "48": "Software packages & IT systems", "50": "Repair & maintenance services",
    "51": "Installation services", "55": "Hospitality & catering", "60": "Transport services",
    "63": "Logistics & travel", "64": "Postal & telecoms", "65": "Utilities",
    "66": "Finance & insurance", "70": "Real estate", "71": "Architecture & engineering",
    "72": "IT services & software development", "73": "R&D", "75": "Public administration",
    "76": "Oil & gas services", "77": "Agricultural & forestry services", "79": "Business services",
    "80": "Education & training", "85": "Health & social work", "90": "Environmental & cleaning",
    "92": "Recreation & culture", "98": "Other community/personal services",
}


def cpv_label(cpv: str | None, fallback: str | None = None) -> str:
    if fallback:
        return fallback
    if cpv and cpv[:2] in CPV_DIVISIONS:
        return CPV_DIVISIONS[cpv[:2]]
    return "unclassified"


@dataclass
class Tender:
    ocid: str
    title: str
    description: str
    status: str | None
    buyer: str | None
    cpv: str | None
    cpv_desc: str | None
    cpv_additional: list[str] = field(default_factory=list)
    category: str | None = None
    suitability: str | None = None
    value_amount: float | None = None
    value_currency: str | None = None
    deadline: str | None = None
    published: str | None = None
    region: dict | None = None
    source: str | None = None
    url: str | None = None

    @property
    def deadline_dt(self) -> datetime | None:
        if not self.deadline:
            return None
        try:
            return datetime.fromisoformat(self.deadline.replace("Z", "+00:00"))
        except ValueError:
            return None

    def days_to_deadline(self, now: datetime | None = None) -> int | None:
        d = self.deadline_dt
        if not d:
            return None
        now = now or datetime.now(timezone.utc)
        return (d - now).days

    @property
    def cpv_sector(self) -> str | None:
        """First two CPV digits = the broad sector (45=construction, 72=IT …)."""
        return self.cpv[:2] if self.cpv else None

    @property
    def all_cpv_sectors(self) -> set[str]:
        out = {self.cpv_sector} if self.cpv_sector else set()
        out |= {c[:2] for c in self.cpv_additional if c}
        return out

    @property
    def region_country(self) -> str | None:
        return (self.region or {}).get("country")

    @property
    def region_tokens(self) -> set[str]:
        """Uppercased location tokens for matching: country (ENG/SCO/…), NUTS
        code (UKM50 = Aberdeen City, UKM = Scotland), and locality name."""
        r = self.region or {}
        return {str(v).upper() for v in (r.get("country"), r.get("nuts"),
                                         r.get("locality")) if v}

    @property
    def has_region(self) -> bool:
        return bool(self.region_tokens)


def load_snapshot(path: str | Path) -> list[Tender]:
    rows = json.load(open(path))
    return [Tender(**r) for r in rows]
