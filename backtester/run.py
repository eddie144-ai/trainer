#!/usr/bin/env python3
"""Run and compare strategies on a dataset, with an out-of-sample reality check.

Usage:
    python run.py --data data/SPY.csv
    python run.py --data data/BTC-USD.csv --capital 10000 --stop 0.1 --tp 0.3
    python run.py --data data/SPY.csv --split 2023-01-01   # train/test boundary

The point of this tool is NOT to find a strategy that looks good. It is to show,
honestly, whether a strategy beats simply buying and holding once real-world
costs and a HELD-OUT test period are taken into account.
"""
from __future__ import annotations
import argparse
import dataclasses
import itertools

from backtest import load_csv, run, Config, strategies


def _pure(cfg: Config) -> Config:
    """Benchmark config: a true buy & hold is never stopped out."""
    return dataclasses.replace(cfg, stop_loss_pct=None, take_profit_pct=None)


def _table(rows: list[list[str]], headers: list[str]) -> str:
    cols = list(zip(*([headers] + rows))) if rows else [[h] for h in headers]
    widths = [max(len(str(c)) for c in col) for col in cols]
    def fmt(r): return "  ".join(str(c).ljust(w) for c, w in zip(r, widths))
    line = "-" * (sum(widths) + 2 * (len(widths) - 1))
    return "\n".join([fmt(headers), line] + [fmt(r) for r in rows])


def compare(series, cfg: Config, label: str) -> None:
    print(f"\n=== {label}: {series.symbol}  ({series.bars[0].d} -> {series.bars[-1].d}, "
          f"{len(series)} bars) ===")
    print(f"    capital=${cfg.initial_capital:,.0f}  cost={cfg.cost_bps}bps  "
          f"slippage={cfg.slippage_bps}bps  stop={cfg.stop_loss_pct}  tp={cfg.take_profit_pct}")
    results = []
    for name, fn in strategies.REGISTRY.items():
        sig = fn(series)
        use_cfg = _pure(cfg) if name == "buy_and_hold" else cfg
        r = run(series, sig, name, use_cfg)
        results.append(r)
    m0 = {r.strategy: r.metrics for r in results}
    headers = ["strategy", "tot.ret", "CAGR", "vol", "Sharpe", "maxDD", "trades", "win%", "in-mkt"]
    rows = []
    for r in results:
        m = r.metrics
        rows.append([
            r.strategy,
            f"{m.total_return*100:,.1f}%",
            f"{m.cagr*100:,.1f}%",
            f"{m.ann_vol*100:,.1f}%",
            f"{m.sharpe:.2f}",
            f"{m.max_drawdown*100:,.1f}%",
            str(m.n_trades),
            f"{m.win_rate*100:.0f}%",
            f"{m.exposure*100:.0f}%",
        ])
    print(_table(rows, headers))
    bh = m0["buy_and_hold"]
    print(f"    benchmark (buy & hold): {bh.total_return*100:,.1f}% total, "
          f"Sharpe {bh.sharpe:.2f}, maxDD {bh.max_drawdown*100:,.1f}%")


def overfitting_demo(series, cfg: Config, split: str) -> None:
    """Grid-search SMA params on the TRAIN half, then show how the 'best'
    settings actually perform on the UNSEEN test half. This is the single most
    important number in the whole exercise."""
    train = series.slice(end=split)
    test = series.slice(start=split)
    if len(train) < 250 or len(test) < 100:
        print("\n(skipping out-of-sample demo: not enough data on one side of split)")
        return

    print(f"\n=== OUT-OF-SAMPLE REALITY CHECK (split at {split}) ===")
    print(f"    train: {train.bars[0].d}->{train.bars[-1].d} ({len(train)} bars)  "
          f"test: {test.bars[0].d}->{test.bars[-1].d} ({len(test)} bars)")

    best = None
    for fast, slow in itertools.product([10, 20, 50], [100, 150, 200]):
        if fast >= slow:
            continue
        sig = strategies.sma_crossover(train, fast, slow)
        r = run(train, sig, f"sma_{fast}_{slow}", cfg)
        if best is None or r.metrics.sharpe > best[0]:
            best = (r.metrics.sharpe, fast, slow, r.metrics.total_return)

    _, fast, slow, train_ret = best
    sig_test = strategies.sma_crossover(test, fast, slow)
    r_test = run(test, sig_test, f"sma_{fast}_{slow}", cfg)
    bh_test = run(test, strategies.buy_and_hold(test), "buy_and_hold", _pure(cfg))

    print(f"    best SMA on train:  fast={fast} slow={slow}  "
          f"(train total return {train_ret*100:,.1f}%, Sharpe {best[0]:.2f})")
    print(f"    SAME params on test:   total return {r_test.metrics.total_return*100:,.1f}%, "
          f"Sharpe {r_test.metrics.sharpe:.2f}, maxDD {r_test.metrics.max_drawdown*100:,.1f}%")
    print(f"    buy & hold on test:    total return {bh_test.metrics.total_return*100:,.1f}%, "
          f"Sharpe {bh_test.metrics.sharpe:.2f}, maxDD {bh_test.metrics.max_drawdown*100:,.1f}%")
    verdict = ("BEAT" if r_test.metrics.total_return > bh_test.metrics.total_return
               else "LOST TO")
    print(f"    --> out of sample, the optimised strategy {verdict} buy & hold.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", required=True)
    p.add_argument("--capital", type=float, default=10_000.0)
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--slippage-bps", type=float, default=5.0)
    p.add_argument("--risk-fraction", type=float, default=1.0)
    p.add_argument("--stop", type=float, default=None, help="stop loss fraction, e.g. 0.1")
    p.add_argument("--tp", type=float, default=None, help="take profit fraction, e.g. 0.3")
    p.add_argument("--split", type=str, default=None, help="train/test boundary YYYY-MM-DD")
    args = p.parse_args()

    series = load_csv(args.data)
    cfg = Config(
        initial_capital=args.capital,
        cost_bps=args.cost_bps,
        slippage_bps=args.slippage_bps,
        risk_fraction=args.risk_fraction,
        stop_loss_pct=args.stop,
        take_profit_pct=args.tp,
    )
    compare(series, cfg, "FULL PERIOD")
    if args.split:
        overfitting_demo(series, cfg, args.split)


if __name__ == "__main__":
    main()
