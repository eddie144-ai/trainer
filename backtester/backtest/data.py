"""Data loading. Reads clean daily OHLCV CSVs (date,open,high,low,close,adjclose,volume)."""
from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass
class Bar:
    d: date
    open: float
    high: float
    low: float
    close: float
    adjclose: float
    volume: float


@dataclass
class Series:
    symbol: str
    bars: list[Bar]

    def __len__(self) -> int:
        return len(self.bars)

    def slice(self, start: str | None = None, end: str | None = None) -> "Series":
        s = datetime.strptime(start, "%Y-%m-%d").date() if start else None
        e = datetime.strptime(end, "%Y-%m-%d").date() if end else None
        out = [b for b in self.bars if (s is None or b.d >= s) and (e is None or b.d <= e)]
        return Series(self.symbol, out)


def load_csv(path: str | Path) -> Series:
    path = Path(path)
    symbol = path.stem
    bars: list[Bar] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            bars.append(
                Bar(
                    d=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    adjclose=float(row.get("adjclose") or row["close"]),
                    volume=float(row.get("volume") or 0.0),
                )
            )
    bars.sort(key=lambda b: b.d)
    return Series(symbol, bars)
