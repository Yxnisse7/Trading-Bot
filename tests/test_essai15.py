from trading_bot import essai14 as e14
from trading_bot import essai15 as e15

from conftest import make_candles
from test_essai14 import _bot_row


def test_filters_and_management_run():
    c = make_candles(n=4000, drift=0.0002, noise=0.001, seed=3)
    ctx = e15.Ctx(c)
    rows = [_bot_row(c, i, "long" if i % 2 else "short", c[i].close * 0.002) for i in range(600, 3800, 37)]
    base = e14.bot_trades(rows, "gold")
    for f in e15.FILTERS:
        kept = [t for t in base if not e15.removed_by(f, t, ctx, 0.3)]
        assert 0 <= len(kept) <= len(base)
    for g in e15.GESTION:
        if g in ("G39", "G40"):
            continue
        out = [x for x in (e15.manage(g, t, ctx) for t in base) if x is not None]
        assert out
        for x in out:
            assert x.exit_ts > x.entry_ts and x.gross_points() / x.risk >= -1.5
    assert len(e15.day_limits(base)) <= len(base)
    assert all(a.risk >= b.risk for a, b in zip(e15.half_size(base, ctx), base))


def test_setups_produce_valid_trades():
    c = make_candles(n=12000, drift=0.0001, noise=0.0015, seed=11)
    ctx = e15.Ctx(c)
    for s in e15.SETUPS:
        tr = e15.setup_trades(s, "nasdaq", ctx)
        for t in tr:
            assert t.risk > 0 and t.exit_ts >= t.entry_ts
            assert t.gross_points() / t.risk >= -1.5
        ts = [t.entry_ts for t in tr]
        assert ts == sorted(ts)


def test_stoch_and_risk_curve():
    c = make_candles(n=100, seed=2)
    k = e15.stoch_k(c)
    assert all(x is None or 0 <= x <= 100 for x in k) and k[-1] is not None
    r = e15.risk_curve([(1, -1.0), (2, -1.0), (3, 2.0)], 10.0)
    assert r["max_drawdown_pct"] == 19.0 and abs(r["final"] - 0.81 * 1.2) < 1e-9
