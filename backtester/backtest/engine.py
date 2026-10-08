"""Event-driven, long/flat backtest engine.

Realism rules (these are what separate a believable backtest from a fantasy):
  1. No lookahead. A signal computed at bar t's close is acted on at bar t+1's
     OPEN. You cannot trade on a price you couldn't have known yet.
  2. Costs are real. Commission + slippage (in basis points) hit every entry
     and every exit, on notional.
  3. Risk controls are enforced intrabar. Stop-loss / take-profit are checked
     against each bar's high/low and OVERRIDE the strategy signal. If a bar
     could have hit both the stop and the target, we assume the stop hit first
     (pessimistic on purpose).
  4. Position sizing is fractional-of-equity (default all-in long / flat).
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .data import Series
from . import metrics as M


@dataclass
class Config:
    initial_capital: float = 10_000.0
    cost_bps: float = 5.0          # commission per side, basis points of notional
    slippage_bps: float = 5.0      # slippage per side, basis points
    risk_fraction: float = 1.0     # fraction of equity deployed when long
    stop_loss_pct: float | None = None   # e.g. 0.08 = exit if -8% from entry
    take_profit_pct: float | None = None # e.g. 0.20 = exit if +20% from entry


@dataclass
class Result:
    symbol: str
    strategy: str
    dates: list = field(default_factory=list)
    equity: list[float] = field(default_factory=list)
    in_market: list[bool] = field(default_factory=list)
    trade_returns: list[float] = field(default_factory=list)
    metrics: M.Metrics | None = None


def _fee(notional: float, cfg: Config) -> float:
    return abs(notional) * (cfg.cost_bps + cfg.slippage_bps) / 10_000.0


def run(series: Series, signal: list[float], strategy_name: str,
        cfg: Config | None = None) -> Result:
    cfg = cfg or Config()
    bars = series.bars
    assert len(signal) == len(bars), "signal length must match bars"

    cash = cfg.initial_capital
    shares = 0.0
    entry_price = 0.0
    entry_equity = 0.0

    res = Result(series.symbol, strategy_name)

    for i, bar in enumerate(bars):
        # --- act at this bar's OPEN on info known at the PREVIOUS close ---
        target = signal[i - 1] if i > 0 else 0.0
        holding = shares > 0

        if holding:
            # 1) risk controls first, checked intrabar against high/low
            exit_price = None
            if cfg.stop_loss_pct is not None:
                stop = entry_price * (1 - cfg.stop_loss_pct)
                if bar.low <= stop:
                    exit_price = min(stop, bar.open)  # gap-through fills at open
            if exit_price is None and cfg.take_profit_pct is not None:
                tp = entry_price * (1 + cfg.take_profit_pct)
                if bar.high >= tp:
                    exit_price = max(tp, bar.open)
            # 2) otherwise honour a flat signal, executed at the open
            if exit_price is None and target <= 0.0:
                exit_price = bar.open

            if exit_price is not None:
                proceeds = shares * exit_price
                cash += proceeds - _fee(proceeds, cfg)
                equity_now = cash
                res.trade_returns.append(equity_now / entry_equity - 1.0)
                shares = 0.0
                holding = False

        if not holding and target > 0.0:
            # enter long at the open
            equity_now = cash
            deploy = equity_now * cfg.risk_fraction
            px = bar.open
            qty = deploy / px
            cost = qty * px
            cash -= cost + _fee(cost, cfg)
            shares = qty
            entry_price = px
            entry_equity = equity_now  # equity at moment of entry (for trade P&L)

        # --- mark to market at the close ---
        equity = cash + shares * bar.close
        res.dates.append(bar.d)
        res.equity.append(equity)
        res.in_market.append(shares > 0)

    res.metrics = M.compute(res.equity, res.in_market, res.trade_returns)
    return res
