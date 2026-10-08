"""Event-driven backtest engine supporting long/flat AND fractional exposure.

Realism rules (these are what separate a believable backtest from a fantasy):
  1. No lookahead. A signal computed at bar t's close is acted on at bar t+1's
     OPEN. You cannot trade on a price you couldn't have known yet.
  2. Costs are real. Commission + slippage (in basis points) hit every trade,
     on the notional actually traded (turnover), both entries and exits.
  3. Risk controls. Two mutually-exclusive modes:
       - Intrabar stops: when stop_loss_pct/take_profit_pct is set AND the
         signal is binary (0/1), stops are checked against each bar's high/low
         and OVERRIDE the signal (pessimistic: stop assumed to hit before
         target). This is the long/flat path.
       - Continuous rebalance: otherwise, the signal is a desired exposure in
         [0, 1] and the book is rebalanced toward it each bar. Volatility
         targeting lives here (the scaling IS the risk control).
  4. No leverage, no shorting: exposure is clamped to [0, 1].
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
    risk_fraction: float = 1.0     # global cap/multiplier on exposure
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


def _is_binary(signal: list[float]) -> bool:
    return all(s == 0.0 or s == 1.0 for s in signal)


def run(series: Series, signal: list[float], strategy_name: str,
        cfg: Config | None = None) -> Result:
    cfg = cfg or Config()
    assert len(signal) == len(series.bars), "signal length must match bars"
    use_stops = cfg.stop_loss_pct is not None or cfg.take_profit_pct is not None
    if use_stops and _is_binary(signal):
        return _run_intrabar(series, signal, strategy_name, cfg)
    return _run_rebalance(series, signal, strategy_name, cfg)


def _run_intrabar(series: Series, signal: list[float], strategy_name: str,
                  cfg: Config) -> Result:
    """Long/flat path with intrabar stop-loss / take-profit."""
    bars = series.bars
    cash = cfg.initial_capital
    shares = 0.0
    entry_price = 0.0
    entry_equity = 0.0
    res = Result(series.symbol, strategy_name)

    for i, bar in enumerate(bars):
        target = signal[i - 1] if i > 0 else 0.0
        holding = shares > 0

        if holding:
            exit_price = None
            if cfg.stop_loss_pct is not None:
                stop = entry_price * (1 - cfg.stop_loss_pct)
                if bar.low <= stop:
                    exit_price = min(stop, bar.open)  # gap-through fills at open
            if exit_price is None and cfg.take_profit_pct is not None:
                tp = entry_price * (1 + cfg.take_profit_pct)
                if bar.high >= tp:
                    exit_price = max(tp, bar.open)
            if exit_price is None and target <= 0.0:
                exit_price = bar.open

            if exit_price is not None:
                proceeds = shares * exit_price
                cash += proceeds - _fee(proceeds, cfg)
                res.trade_returns.append(cash / entry_equity - 1.0)
                shares = 0.0
                holding = False

        if not holding and target > 0.0:
            equity_now = cash
            deploy = equity_now * cfg.risk_fraction
            px = bar.open
            qty = deploy / px
            cost = qty * px
            cash -= cost + _fee(cost, cfg)
            shares = qty
            entry_price = px
            entry_equity = equity_now

        equity = cash + shares * bar.close
        res.dates.append(bar.d)
        res.equity.append(equity)
        res.in_market.append(shares > 0)

    res.metrics = M.compute(res.equity, res.in_market, res.trade_returns)
    return res


def _run_rebalance(series: Series, signal: list[float], strategy_name: str,
                   cfg: Config) -> Result:
    """Continuous path: rebalance toward a desired exposure in [0, 1] each bar.

    A 'trade' for win-rate purposes is one completed round trip: exposure going
    from flat (0) to invested and back to flat. Always-invested strategies
    therefore report 0 trades, which is correct.
    """
    bars = series.bars
    cash = cfg.initial_capital
    shares = 0.0
    entry_equity = 0.0
    position_open = False
    res = Result(series.symbol, strategy_name)

    for i, bar in enumerate(bars):
        raw = signal[i - 1] if i > 0 else 0.0
        target_frac = max(0.0, min(1.0, raw)) * cfg.risk_fraction

        equity_at_open = cash + shares * bar.open
        if equity_at_open <= 0:
            res.dates.append(bar.d); res.equity.append(equity_at_open)
            res.in_market.append(shares > 0); continue

        desired_value = target_frac * equity_at_open
        current_value = shares * bar.open
        delta_value = desired_value - current_value

        if abs(delta_value) > 1e-9:
            dshares = delta_value / bar.open
            cash -= dshares * bar.open + _fee(delta_value, cfg)
            shares += dshares

        # round-trip accounting
        if not position_open and shares > 1e-12:
            position_open = True
            entry_equity = equity_at_open
        elif position_open and shares <= 1e-12:
            position_open = False
            res.trade_returns.append((cash + shares * bar.open) / entry_equity - 1.0)

        equity = cash + shares * bar.close
        res.dates.append(bar.d)
        res.equity.append(equity)
        res.in_market.append(shares > 1e-12)

    res.metrics = M.compute(res.equity, res.in_market, res.trade_returns)
    return res
