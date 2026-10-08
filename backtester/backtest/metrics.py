"""Performance metrics computed from a daily equity curve.

Everything here is deliberately plain arithmetic so the numbers can be checked
by hand. No metric flatters a strategy: drawdown is worst peak-to-trough,
Sharpe uses daily excess returns annualised, and we always report the number
of trades so a 'great' result built on 3 trades is obvious.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass
class Metrics:
    start_equity: float
    end_equity: float
    total_return: float      # fraction, e.g. 0.42 = +42%
    cagr: float
    ann_vol: float
    sharpe: float
    sortino: float
    max_drawdown: float      # negative fraction, e.g. -0.35
    calmar: float
    exposure: float          # fraction of days holding a position
    n_trades: int
    win_rate: float          # fraction of closed trades that were profitable
    avg_win: float
    avg_loss: float

    def as_rows(self) -> list[tuple[str, str]]:
        def pct(x): return f"{x * 100:,.2f}%"
        return [
            ("Start equity", f"${self.start_equity:,.2f}"),
            ("End equity", f"${self.end_equity:,.2f}"),
            ("Total return", pct(self.total_return)),
            ("CAGR", pct(self.cagr)),
            ("Annualised vol", pct(self.ann_vol)),
            ("Sharpe (rf=0)", f"{self.sharpe:.2f}"),
            ("Sortino", f"{self.sortino:.2f}"),
            ("Max drawdown", pct(self.max_drawdown)),
            ("Calmar", f"{self.calmar:.2f}"),
            ("Time in market", pct(self.exposure)),
            ("Trades", str(self.n_trades)),
            ("Win rate", pct(self.win_rate)),
            ("Avg win / loss", f"{pct(self.avg_win)} / {pct(self.avg_loss)}"),
        ]


_TRADING_DAYS = 252


def compute(equity: list[float], in_market: list[bool], trade_returns: list[float],
            periods_per_year: int = _TRADING_DAYS) -> Metrics:
    assert len(equity) >= 2, "need at least two equity points"
    rets = [equity[i] / equity[i - 1] - 1.0 for i in range(1, len(equity))]
    n = len(rets)

    start, end = equity[0], equity[-1]
    total_return = end / start - 1.0
    years = n / periods_per_year
    cagr = (end / start) ** (1 / years) - 1.0 if years > 0 and end > 0 else float("nan")

    mean = sum(rets) / n
    var = sum((r - mean) ** 2 for r in rets) / (n - 1) if n > 1 else 0.0
    sd = math.sqrt(var)
    ann_vol = sd * math.sqrt(periods_per_year)
    sharpe = (mean / sd) * math.sqrt(periods_per_year) if sd > 0 else 0.0

    downside = [min(r, 0.0) for r in rets]
    dvar = sum(d * d for d in downside) / n
    dsd = math.sqrt(dvar)
    sortino = (mean / dsd) * math.sqrt(periods_per_year) if dsd > 0 else 0.0

    peak = equity[0]
    max_dd = 0.0
    for v in equity:
        peak = max(peak, v)
        dd = v / peak - 1.0
        max_dd = min(max_dd, dd)
    calmar = (cagr / abs(max_dd)) if max_dd < 0 else float("inf")

    exposure = sum(1 for x in in_market if x) / len(in_market) if in_market else 0.0

    wins = [t for t in trade_returns if t > 0]
    losses = [t for t in trade_returns if t <= 0]
    win_rate = len(wins) / len(trade_returns) if trade_returns else 0.0
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0

    return Metrics(start, end, total_return, cagr, ann_vol, sharpe, sortino,
                   max_dd, calmar, exposure, len(trade_returns), win_rate,
                   avg_win, avg_loss)
