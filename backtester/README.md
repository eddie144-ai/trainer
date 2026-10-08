# Honest Backtester

A small, readable backtesting engine for long/flat strategies on daily data.
Its purpose is not to make a strategy *look* good — it's to tell you, honestly,
whether a strategy would have beaten simply buying and holding, **after costs**
and **on data it was never tuned on**.

This exists because of a specific claim ("give an AI bot $50 / $10k and let it
trade autonomously to make thousands"). The backtester is the grown-up answer to
that claim: measure the edge before risking a cent.

## Why you can trust the numbers

The engine enforces the things most hyped backtests quietly skip:

1. **No lookahead.** A signal computed at a bar's *close* is executed at the
   *next* bar's *open*. You can never trade on a price you couldn't have known.
   (This even costs buy-and-hold its first bar — on purpose. See the tests.)
2. **Real costs.** Commission + slippage (basis points) are charged on every
   entry and every exit.
3. **Risk controls enforced intrabar.** Stop-loss / take-profit are checked
   against each bar's high/low and override the signal. If a bar could have hit
   both, the stop is assumed first (pessimistic).
4. **A clean benchmark.** Buy-and-hold is always run with no stops, so it's a
   true reference. Every strategy is judged against it.
5. **Out-of-sample reality check.** `--split` tunes SMA parameters on the first
   (train) half, then reports how those exact settings do on the unseen (test)
   half. Overfitting shows up here or nowhere.

## Usage

```bash
# layout: data/*.csv with columns date,open,high,low,close,adjclose,volume
PYTHONPATH=. python3 run.py --data data/SPY.csv --split 2023-01-01
PYTHONPATH=. python3 run.py --data data/BTC-USD.csv --capital 10000 \
    --stop 0.15 --tp 0.40 --split 2023-01-01

PYTHONPATH=. python3 tests/test_engine.py   # sanity tests
```

Flags: `--capital --cost-bps --slippage-bps --risk-fraction --stop --tp --split`.

## What the included data showed (SPY & BTC, 2016–2026)

These are real results from the two datasets, not cherry-picked:

| Market | Strategy | Total return | Sharpe | Max drawdown |
|---|---|---|---|---|
| SPY | **buy & hold** | **+259%** | **0.80** | -34% |
| SPY | SMA 50/200 | +111% | 0.57 | -34% |
| SPY | RSI mean-reversion | +23% | 0.23 | -29% |
| BTC | **buy & hold** | **+13,109%** | **0.89** | -83% |
| BTC | SMA 50/200 | +1,184% | 0.60 | -85% |
| BTC | RSI mean-reversion | +101% | 0.31 | -77% |

And the part that matters most — the **out-of-sample** test, where SMA
parameters were optimised on 2016–2022 and then run untouched on 2023–2026:

- **SPY:** optimised SMA returned +50% on the test years; buy & hold returned
  **+102%**. The strategy *lost to doing nothing.*
- **BTC:** optimised SMA returned +29% on the test years; buy & hold returned
  **+329%**. Again, *lost to doing nothing* — despite looking spectacular
  (+3,931%) on the training data.

## The honest takeaway

On this data, over this decade, **none of these simple strategies beat buying
and holding** once you account for costs and refuse to cheat with hindsight.
The strategy that looked best in-sample (+3,931% on BTC training data) was the
one that fell apart hardest out-of-sample. That gap — gorgeous backtest,
mediocre future — is exactly the trap the "autonomous trading bot" videos sell
you, and exactly what this tool is built to expose.

A real edge, if you have one, must survive this test first. Most don't.

## Extending it

Add a strategy in `backtest/strategies.py` (return a 0/1 target per bar, using
only past/current closes) and register it. The engine, metrics, costs, stops,
and out-of-sample check all apply automatically. Shorting and leverage are
deliberately omitted — add them only once a long/flat edge is proven.

*Not financial advice. A backtest is a hypothesis about the past, not a promise
about the future.*
