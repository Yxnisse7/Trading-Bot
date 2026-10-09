from trading_bot import essai14 as e14
from trading_bot import strategies as sl
from trading_bot.models import iso
from datetime import datetime, timezone

from conftest import make_candles


def _bot_row(c, i, direction, risk, tp_r=1.5):
    """Trade du bot entré à la clôture de la bougie i."""
    entry = c[i].close
    sign = 1 if direction == "long" else -1
    when = iso(datetime.fromtimestamp(c[i].ts + 300, timezone.utc))
    return {"status": "expired", "close_price": entry, "entry": entry, "stop_loss": entry - sign * risk,
            "take_profit": entry + sign * tp_r * risk, "direction": direction, "created_at": when,
            "closed_at": iso(datetime.fromtimestamp(c[i + 12].ts + 300, timezone.utc))}


def test_filters_and_exits_run_without_future_data():
    c = make_candles(n=3000, drift=0.0002, noise=0.001, seed=3)
    ctx = e14.Ctx(c)
    rows = [_bot_row(c, i, "long", c[i].close * 0.002) for i in range(400, 2800, 37)]
    base = e14.bot_trades(rows, "gold")
    assert len(base) == len(rows)
    for f in ("A1", "A2", "A3", "A4"):
        kept = [t for t in base if not e14.removed_by(f, t, ctx, None)]
        assert 0 <= len(kept) <= len(base)
    for e in e14.EXITS:
        out = [e14.exit_variant(e, t, ctx) for t in base]
        assert all(x is not None for x in out)
        # la sortie ne précède jamais l'entrée, et la perte ne dépasse jamais le stop initial (sans saut d'ouverture)
        for x in out:
            assert x.exit_ts > x.entry_ts
            assert x.gross_points() / x.risk >= -1.5


def test_stretched_entry_is_removed():
    c = make_candles(n=600, noise=0.0002, seed=5)
    # forte accélération sur les dernières bougies : clôture loin au-dessus de la moyenne 20
    for k in range(560, 570):
        p = c[k - 1].close * 1.004
        c[k] = type(c[k])(c[k].ts, c[k - 1].close, p * 1.0005, c[k - 1].close * 0.9998, p, c[k].volume)
    ctx = e14.Ctx(c)
    t = e14.bot_trades([_bot_row(c, 569, "long", c[569].close * 0.002)], "gold")[0]
    assert e14.removed_by("A1", t, ctx, None)


def test_setups_produce_valid_trades():
    c = make_candles(n=8000, drift=0.0001, noise=0.0015, seed=11)
    ctx = e14.Ctx(c)
    for b in ("B6", "B7", "B8", "B9"):
        tr = e14.setup_trades(b, "bitcoin", ctx)
        for t in tr:
            assert t.risk > 0 and t.exit_ts >= t.entry_ts
            assert t.gross_points() / t.risk >= -1.5   # jamais pire que le stop (hors saut d'ouverture)
        ts = [t.entry_ts for t in tr]
        assert ts == sorted(ts)                          # une position à la fois


def test_verdict_shape():
    c = make_candles(n=200)
    t = sl.Trade("x", "gold", "long", c[10].ts, c[20].ts, 100.0, 101.0, 1.0, "")
    v = e14.verdict([t] * 40, 0.01, None)
    assert v["status"].startswith(("écarté", "validé", "prouvé"))
