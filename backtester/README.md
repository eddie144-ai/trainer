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

## Strategies tested

`buy_and_hold` (benchmark), `sma_crossover`, `rsi_mean_reversion`,
`ts_momentum` (6-month absolute momentum), `momentum_12_1` (classic 12-1),
`vol_target` (volatility targeting), `trend_vol_target` (trend filter + vol
targeting). Parameters are literature defaults, not fitted to this data.

## What the included data showed (SPY & BTC, 2016–2026)

Real results, not cherry-picked. Full-period, risk-adjusted:

| Market | Strategy | Total return | Sharpe | Max drawdown |
|---|---|---|---|---|
| SPY | buy & hold | +259% | 0.80 | -34% |
| SPY | **vol_target** | +193% | **0.90** | **-20%** |
| BTC | buy & hold | +13,096% | 0.89 | -83% |
| BTC | **ts_momentum** | +12,188% | **0.98** | -68% |
| BTC | **trend_vol_target** | +360% | 0.87 | **-23%** |

On the full period several strategies *look* like they beat buy & hold on
Sharpe. That is exactly where backtests lie. The only test that counts:

## The generalisation test (the one that matters)

Every strategy, fixed parameters, scored on a train half and an **unseen test
half** — repeated at three different split dates (2021, 2023, 2024) on both
assets. The rule for a real edge: higher Sharpe than buy & hold in *both*
halves.

**Result: across all three splits and both assets, NO strategy beat buy & hold
on Sharpe in both periods.** The ones that looked best in-sample (BTC
`ts_momentum`: +3,253% on training data) fell apart out-of-sample every time.
There is no reliable *return* edge here.

## The honest takeaway — the edge is risk, not return

Two things held up consistently, across every split and both assets:

1. **You cannot beat buy & hold on return.** Not on total return, not on
   Sharpe, not once hindsight is removed. Holding won every out-of-sample test.
2. **But volatility targeting and trend filtering reliably and dramatically
   cut drawdowns.** `trend_vol_target` turned Bitcoin's −53% to −77%
   out-of-sample crashes into −13% to −15% ones, at *every* split. `vol_target`
   roughly halved drawdowns too. The price is lower total return (you sit out
   part of the big rallies).

So the real, defensible edge is **not "make as much as possible" — it's "lose
far less in the crashes."** For a real human, cutting an 83% drawdown to ~15%
is often the difference between holding the plan and panic-selling at the
bottom (which is how most people actually lose money). That is a risk-management
result, not an alpha result — and it is the opposite of what an "autonomous bot
that makes thousands" promises.

If you have a genuine return edge, it must survive the generalisation test
above before a cent is risked. None of these did.

## Extending it

Add a strategy in `backtest/strategies.py` (return a 0/1 target per bar, using
only past/current closes) and register it. The engine, metrics, costs, stops,
and out-of-sample check all apply automatically. Shorting and leverage are
deliberately omitted — add them only once a long/flat edge is proven.

*Not financial advice. A backtest is a hypothesis about the past, not a promise
about the future.*
