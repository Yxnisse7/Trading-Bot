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


def test_day_limit_flag_and_shadow_runner():
    from datetime import datetime, timezone
    from trading_bot import context as ctxmod
    from trading_bot import strategies as sl
    from trading_bot.models import Signal
    now = datetime(2026, 10, 9, 16, 0, tzinfo=timezone.utc)

    def sig(i, status, pnl):
        s = Signal.__new__(Signal)
        s.asset, s.source, s.status, s.pnl_pct = "gold", "bot", status, pnl
        s.created_at = f"2026-10-09T1{3 + i}:00:00Z"
        return s
    assert not ctxmod.day_limit_hit("gold", [sig(0, "tp", 0.1)], now)
    assert ctxmod.day_limit_hit("gold", [sig(0, "sl", -0.1), sig(1, "sl", -0.1)], now)
    assert ctxmod.day_limit_hit("gold", [sig(i, "tp", 0.1) for i in range(3)], now)
    c = make_candles(n=3000, drift=0.0001, noise=0.0015, seed=11)
    assert ("creux_repris_15m", "nasdaq") in sl.SHADOW
    assert sl.RUNNERS_1H["creux_repris_15m"](c, "nasdaq") == e15.setup_trades("S25", "nasdaq", e15.Ctx(c))
