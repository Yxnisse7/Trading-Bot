"""Essai 11 : tendance journalière (Donchian 55/20, momentum 12 mois), défi CFD et suivi en ombre."""
import math
from datetime import datetime, timezone

from trading_bot import trend_daily as td
from trading_bot.models import Candle

T0 = int(datetime(2006, 1, 2, tzinfo=timezone.utc).timestamp())


def _bars(n=900, drift=0.002, seed=1.0):
    out, px = [], 100.0
    for k in range(n):
        px *= 1 + drift * (1 if (k // 150) % 3 else -1) + 0.004 * math.sin(k * seed)
        out.append(Candle(T0 + k * 86_400, px, px * 1.001, px * 0.999, px))
    return out


def test_donchian_trades_have_r_and_daily_marks_add_up():
    bars = _bars()
    trades, daily = td.donchian(bars, "X")
    assert trades and all(t["why"] in ("stop", "canal") for t in trades)
    assert abs(sum(t["r"] for t in trades) - sum(daily.values())) < 1e-6
    assert all(t["risk"] > 0 and t["exit_ts"] >= t["entry_ts"] for t in trades)


def test_challenge_counts_passes_and_breaches():
    up = [(k, 1.0) for k in range(400)]                 # +1 R par jour
    res = td.challenge(up, 500.0, step_days=50)
    assert res["pass"] == 1.0 and res["days_p50"] == 15          # +5 000 $ en 10 jours puis +2 500 $ en 5 jours
    crash = [(0, -6.0)] + [(k, 0.0) for k in range(1, 40)]
    assert td.challenge(crash, 500.0, step_days=100)["fails"]["perte journalière"] == 1


def test_momentum_and_shadow_month_roll():
    series = {"A": _bars(900, 0.002, 1.0), "B": _bars(900, -0.001, 2.0)}
    res = td.tsmom(series)
    assert {"kept", "first_half", "second_half", "scale_10"} <= set(res)
    state = {}
    now = datetime(2026, 10, 7, tzinfo=timezone.utc)
    td.shadow_update(state, series, 0.5, now)
    assert len(state["months"]) == 1 and state["months"][0]["result"] is None
    td.shadow_update(state, series, 0.5, now)                       # même mois : rien ne change
    assert len(state["months"]) == 1
    later = {k: v + [Candle(v[-1].ts + 40 * 86_400, v[-1].close, v[-1].close, v[-1].close, v[-1].close * 1.1)]
             for k, v in series.items()}
    td.shadow_update(state, later, 0.5, now)
    assert len(state["months"]) == 2 and state["months"][0]["result"] is not None
