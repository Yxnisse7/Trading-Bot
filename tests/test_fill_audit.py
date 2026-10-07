"""Faisabilité des prix d'exécution du backtest : sauts de prix, sorties hors bougie, stops minuscules."""
from trading_bot import fill_audit as fa
from trading_bot import strategies as sl
from trading_bot.models import Candle

T0 = 1_780_000_000


def _candles(rows):
    return [Candle(T0 + 300 * i, *r) for i, r in enumerate(rows)]


def _trade(status, closed_bar, close_price, **kw):
    t = {"status": status, "direction": "long", "entry": 100.0, "stop_loss": 98.0, "take_profit": 104.0,
         "created_at": _iso(T0 + 300), "closed_at": _iso(T0 + 300 * closed_bar), "close_price": close_price}
    return t | kw


def _iso(ts):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_gap_through_stop_is_costed_at_the_open():
    c = _candles([(100, 100.5, 99.5, 100), (100, 101, 99.8, 100.2), (96, 97, 95, 96.5)])
    idx = {x.ts: i for i, x in enumerate(c)}
    a = fa.audit_trade(_trade("sl", 2, 98.0), c, idx, 0.25)
    assert a["gap"] and a["gap_r"] == -1.0 and a["outside"]        # 98 n'a jamais coté : ouverture à 96
    assert a["entry_r"] == 0.0


def test_same_bar_target_and_stop_and_tiny_stop_are_flagged():
    c = _candles([(100, 100.5, 99.5, 100), (100, 105, 97, 100)])
    idx = {x.ts: i for i, x in enumerate(c)}
    a = fa.audit_trade(_trade("sl", 1, 98.0), c, idx, 0.25)
    assert a["both"] and not a["gap"] and not a["outside"]
    tiny = fa.audit_trade(_trade("sl", 1, 98.0, stop_loss=99.5), c, idx, 0.25)
    assert tiny["tiny"]


def test_trimmed_backtest_trades_rebuild_their_exit():
    c = _candles([(100, 100.5, 99.5, 100), (100, 101, 99.8, 100.2), (100, 104.5, 99.9, 104)])
    t = _trade("tp", 2, None, duration_minutes=5, pnl_gross_pct=4.0)
    del t["closed_at"], t["close_price"]
    res = fa.audit({"x": {"asset": "x", "trades": [t]}}, {"x": c}, {"x": 0.25})
    assert res["total"]["n"] == 1 and res["total"]["outside"] == 0 and res["total"]["gaps"] == 0


def test_lab_trades_stay_inside_their_bars():
    c = _candles([(100, 101, 99, 100)] * 30)
    good = sl.Trade("orb5", "x", "long", c[2].ts, c[5].ts, 100.0, 100.5, 1.0, "objectif")
    bad = sl.Trade("orb5", "x", "long", c[2].ts, c[5].ts, 100.0, 103.0, 1.0, "objectif")
    out = fa.audit_lab([good, bad], c, 0.25, set())
    assert out["orb5"]["n"] == 2 and out["orb5"]["outside"] == 1 and out["orb5"]["tiny"] == 0
