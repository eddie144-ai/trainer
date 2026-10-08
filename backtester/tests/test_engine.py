"""Sanity tests. Run: PYTHONPATH=. python3 tests/test_engine.py

These guard the two things most backtests get silently wrong:
  - lookahead (acting on a price you couldn't have known), and
  - costs actually being charged.
"""
from backtest.data import Series, Bar
from backtest import run, Config, strategies
from datetime import date


def _mk(prices):
    bars = []
    for i, p in enumerate(prices):
        bars.append(Bar(date(2020, 1, 1 + i), open=p, high=p, low=p, close=p,
                        adjclose=p, volume=1.0))
    return Series("TEST", bars)


def test_buy_and_hold_matches_price_move():
    s = _mk([100, 110, 121])  # +10% then +10%
    r = run(s, strategies.buy_and_hold(s), "bh",
            Config(initial_capital=1000, cost_bps=0, slippage_bps=0))
    # Execution is next-open: the "buy" decided at bar0's close fills at bar1's
    # open (110), NOT bar0 (100). So we capture only 110 -> 121 = +10%. Missing
    # the first bar is the honest price of never trading on unknown data.
    assert abs(r.equity[-1] - 1100) < 1e-6, r.equity[-1]
    print("ok: buy_and_hold tracks price (with 1-bar execution delay)")


def test_costs_reduce_return():
    s = _mk([100, 110])
    free = run(s, strategies.buy_and_hold(s), "bh",
               Config(initial_capital=1000, cost_bps=0, slippage_bps=0))
    costed = run(s, strategies.buy_and_hold(s), "bh",
                 Config(initial_capital=1000, cost_bps=50, slippage_bps=50))
    assert costed.equity[-1] < free.equity[-1], "costs must reduce equity"
    print("ok: costs are charged")


def test_no_lookahead_on_flat_signal():
    # Signal flips to long only at the LAST bar's close; engine must not have
    # captured earlier gains it couldn't have traded on.
    s = _mk([100, 200, 100, 100])
    sig = [0, 0, 0, 1]  # only long after the spike is over
    r = run(s, sig, "late", Config(initial_capital=1000, cost_bps=0, slippage_bps=0))
    # Entry happens at bar after signal=1, which doesn't exist -> never actually
    # deployed; equity must remain flat at 1000 the whole way.
    assert all(abs(e - 1000) < 1e-6 for e in r.equity), r.equity
    print("ok: no lookahead — missed the spike it couldn't trade")


def test_stop_loss_triggers():
    s = _mk([100, 100, 80])  # -20% drop
    sig = [1, 1, 1]
    r = run(s, sig, "stop", Config(initial_capital=1000, cost_bps=0, slippage_bps=0,
                                   stop_loss_pct=0.1))
    assert r.metrics.n_trades == 1, r.metrics.n_trades
    assert r.trade_returns[0] < 0, r.trade_returns
    print("ok: stop-loss exits the position")


if __name__ == "__main__":
    test_buy_and_hold_matches_price_move()
    test_costs_reduce_return()
    test_no_lookahead_on_flat_signal()
    test_stop_loss_triggers()
    print("\nall tests passed")
