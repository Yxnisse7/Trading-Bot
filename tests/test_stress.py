"""Tests de résistance : les trades du backtest rejoués dans des conditions dégradées."""
from datetime import datetime, timezone

from trading_bot.models import Candle, iso
from trading_bot.stress import replay, stress_test

T0 = int(datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc).timestamp())


def _candles(path):
    """Bougies 5 min à partir de T0 : (plus haut, plus bas, clôture)."""
    return [Candle(T0 + i * 300, c, h, lo, c) for i, (h, lo, c) in enumerate(path)]


def _trade(entry=100.0, tp=102.0, sl=99.0, direction="long", bar=0, horizon=12):
    created = T0 + (bar + 1) * 300                      # clôture de la bougie `bar`
    return {"direction": direction, "entry": entry, "take_profit": tp, "stop_loss": sl,
            "created_at": iso(datetime.fromtimestamp(created, tz=timezone.utc)),
            "expires_at": iso(datetime.fromtimestamp(created + horizon * 300, tz=timezone.utc))}


def _index(cs):
    return {c.ts: i for i, c in enumerate(cs)}


def test_reference_tight_stop_and_costs():
    # monte doucement jusqu'à 102 en passant par 99,4 : TP touché en référence
    cs = _candles([(100, 100, 100), (100.2, 99.4, 99.8), (101, 99.8, 100.9), (102.1, 100.8, 102), (102, 101.5, 101.8)])
    t = _trade()
    assert replay(t, cs, _index(cs), 0.0) == 2.0                        # +2 points pour 1 de risque
    assert replay(t, cs, _index(cs), 0.1) < 2.0                         # frais déduits
    assert replay(t, cs, _index(cs), 0.1, cost=2.0) < replay(t, cs, _index(cs), 0.1)
    assert replay(t, cs, _index(cs), 0.0, sl=0.5) == -1.0               # stop à 99,5 : touché par le creux à 99,4


def test_delayed_entry_keeps_notified_levels_or_is_missed():
    cs = _candles([(100, 100, 100), (101, 100, 101), (101.6, 100.9, 101.5), (102.2, 101.4, 102.1), (102, 101.8, 102)])
    t = _trade()
    late = replay(t, cs, _index(cs), 0.0, delay=1)                     # entrée à 101, TP 102 : +1 point
    assert abs(late - 1.0) < 1e-9
    gone = _candles([(100, 100, 100), (102.5, 100, 102.4), (103, 102, 102.8)])
    assert replay(t, gone, _index(gone), 0.0, delay=1) == "missed"      # le prix a déjà dépassé l'objectif


def test_expiry_closes_at_the_last_bar_of_the_horizon():
    cs = _candles([(100, 100, 100)] + [(100.5, 99.6, 100.2)] * 3 + [(100.9, 99.5, 100.8)])
    t = _trade(horizon=3)                                                # bougies 1 à 3 seulement
    assert abs(replay(t, cs, _index(cs), 0.0) - 0.2) < 1e-9


def test_stress_test_verdict_and_grid():
    cs = _candles([(100, 100, 100), (100.2, 99.4, 99.8), (101, 99.8, 100.9), (102.1, 100.8, 102)] * 5)
    trades = [_trade(bar=4 * k) | {"entry": 100.0} for k in range(5)]
    out = stress_test({"nasdaq": {"asset": "nasdaq", "trades": trades}}, {"nasdaq": cs}, {"nasdaq": 0.0})
    assert out["n_trades"] == 5 and out["scenarios"][0]["key"] == "base"
    assert out["scenarios"][0]["mean_r"] > 0
    assert len(out["grid"]) == 15 and out["verdict"] in ("robuste", "fragile", "tres_fragile")
    assert stress_test({}, {}, {}) == {}
