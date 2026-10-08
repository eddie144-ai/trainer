"""Strategies produce a desired target position for each bar: 1.0 = fully long,
0.0 = flat. (Long/flat only — no shorting, no leverage. That's a deliberate
choice: it keeps the honest baseline honest.)

CRITICAL ANTI-LOOKAHEAD RULE: the signal for bar t may use data only up to and
including bar t's CLOSE. The engine then acts on it at bar t+1's OPEN. Every
indicator below is causal (uses past/current closes only).
"""
from __future__ import annotations
from .data import Series


def _closes(s: Series) -> list[float]:
    return [b.close for b in s.bars]


def buy_and_hold(s: Series) -> list[float]:
    """The benchmark every strategy must beat to justify its existence."""
    return [1.0] * len(s)


def sma_crossover(s: Series, fast: int = 50, slow: int = 200) -> list[float]:
    """Long when fast SMA >= slow SMA, else flat. Classic trend following."""
    c = _closes(s)
    n = len(c)
    sig = [0.0] * n
    for t in range(n):
        if t + 1 < slow:
            continue  # not enough history yet -> stay flat
        fast_ma = sum(c[t + 1 - fast:t + 1]) / fast
        slow_ma = sum(c[t + 1 - slow:t + 1]) / slow
        sig[t] = 1.0 if fast_ma >= slow_ma else 0.0
    return sig


def _rsi(c: list[float], period: int) -> list[float]:
    rsi = [float("nan")] * len(c)
    if len(c) <= period:
        return rsi
    gains = losses = 0.0
    for i in range(1, period + 1):
        ch = c[i] - c[i - 1]
        gains += max(ch, 0.0)
        losses += max(-ch, 0.0)
    avg_gain, avg_loss = gains / period, losses / period
    rs = avg_gain / avg_loss if avg_loss else float("inf")
    rsi[period] = 100 - 100 / (1 + rs)
    for i in range(period + 1, len(c)):
        ch = c[i] - c[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(ch, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-ch, 0.0)) / period
        rs = avg_gain / avg_loss if avg_loss else float("inf")
        rsi[i] = 100 - 100 / (1 + rs)
    return rsi


def rsi_mean_reversion(s: Series, period: int = 14, buy: float = 30.0,
                       exit: float = 55.0) -> list[float]:
    """Buy oversold (RSI < buy), hold until RSI recovers past `exit`."""
    c = _closes(s)
    rsi = _rsi(c, period)
    sig = [0.0] * len(c)
    holding = False
    for t in range(len(c)):
        r = rsi[t]
        if r != r:  # NaN
            continue
        if not holding and r < buy:
            holding = True
        elif holding and r > exit:
            holding = False
        sig[t] = 1.0 if holding else 0.0
    return sig


def ts_momentum(s: Series, lookback: int = 126) -> list[float]:
    """Time-series (absolute) momentum: long if price is above its level
    `lookback` bars ago, else flat. ~126 bars = 6 months. Binary."""
    c = _closes(s)
    sig = [0.0] * len(c)
    for t in range(len(c)):
        if t < lookback:
            continue
        sig[t] = 1.0 if c[t] > c[t - lookback] else 0.0
    return sig


def momentum_12_1(s: Series) -> list[float]:
    """Classic 12-1 momentum: long if the return from ~12 months ago to ~1
    month ago is positive (skipping the most recent month). Binary."""
    c = _closes(s)
    long_lb, skip = 252, 21
    sig = [0.0] * len(c)
    for t in range(len(c)):
        if t < long_lb:
            continue
        past = c[t - long_lb]
        recent = c[t - skip]
        sig[t] = 1.0 if recent > past else 0.0
    return sig


def _daily_vol(c: list[float], t: int, lookback: int) -> float | None:
    if t < lookback:
        return None
    rets = [c[i] / c[i - 1] - 1.0 for i in range(t - lookback + 1, t + 1)]
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return var ** 0.5


def vol_target(s: Series, target_vol: float = 0.15, lookback: int = 20,
               cap: float = 1.0) -> list[float]:
    """Volatility targeting: hold an exposure that scales inversely with recent
    realised volatility, aiming for a constant annualised vol. Continuous in
    [0, cap]. No leverage (cap=1.0), so calm markets are fully invested and
    turbulent ones are scaled down. Its whole pitch is better Sharpe / smaller
    drawdown, not bigger raw return."""
    c = _closes(s)
    daily_target = target_vol / (252 ** 0.5)
    sig = [0.0] * len(c)
    for t in range(len(c)):
        dv = _daily_vol(c, t, lookback)
        if dv is None or dv == 0:
            continue
        sig[t] = max(0.0, min(cap, daily_target / dv))
    return sig


def trend_vol_target(s: Series, target_vol: float = 0.15, lookback: int = 20,
                     trend_lb: int = 200, cap: float = 1.0) -> list[float]:
    """Vol targeting, but only while price is above its long SMA (trend up).
    Combines a trend filter with vol scaling. Continuous."""
    c = _closes(s)
    vt = vol_target(s, target_vol, lookback, cap)
    sig = [0.0] * len(c)
    for t in range(len(c)):
        if t + 1 < trend_lb:
            continue
        sma = sum(c[t + 1 - trend_lb:t + 1]) / trend_lb
        sig[t] = vt[t] if c[t] >= sma else 0.0
    return sig


REGISTRY = {
    "buy_and_hold": buy_and_hold,
    "sma_crossover": sma_crossover,
    "rsi_mean_reversion": rsi_mean_reversion,
    "ts_momentum": ts_momentum,
    "momentum_12_1": momentum_12_1,
    "vol_target": vol_target,
    "trend_vol_target": trend_vol_target,
}
