from trading_bot import essai16 as e16

from conftest import make_candles


def test_swing_trades_are_valid_and_sequential():
    c = make_candles(n=20000, drift=0.0002, noise=0.0015, seed=7)
    ctx = e16.Ctx(c)
    for w in e16.VARIANTS:
        tr = e16.trades(w, "bitcoin", ctx)
        assert tr, w
        for a, b in zip(tr, tr[1:]):
            assert b.entry_ts >= a.exit_ts
        for t in tr:
            assert t.risk > 0 and 0 < t.exit_ts - t.entry_ts <= e16.MAX_HOLD + 900
            assert t.gross_points() / t.risk >= -1.5
        v = e16.verdict(tr, 0.06, "bitcoin")
        assert v["status"].startswith(("écarté", "validé", "prouvé"))


def test_index_positions_never_cross_the_weekend():
    c = make_candles(n=20000, drift=0.0002, noise=0.0015, seed=7)
    ctx = e16.Ctx(c)
    from datetime import datetime
    from trading_bot import strategies as sl
    for t in e16.trades("W3", "nasdaq", ctx):
        a, b = datetime.fromtimestamp(t.entry_ts, sl.NY), datetime.fromtimestamp(t.exit_ts, sl.NY)
        assert (b.date() - a.date()).days <= 5 and not (a.weekday() == 4 and a.hour >= 12)
        assert a.isocalendar()[1] == b.isocalendar()[1] or b.weekday() == 5 and b.hour == 0
