"""Laboratoire de stratégies : exécution prudente, ORB, aucun biais de futur, frais Topstep."""
from datetime import date, datetime, timezone

from trading_bot import strategies as st
from trading_bot.models import Candle

from conftest import make_candles


def test_stop_has_priority_and_gaps_fill_at_the_open():
    bars = [Candle(0, 100, 100, 100, 100, 1), Candle(300, 100, 103, 98, 101, 1), Candle(600, 95, 96, 94, 95, 1)]
    # même bougie : stop (99) et objectif (102) touchés → stop
    assert st.simulate(bars, 0, "long", 100, 99, target=102) == (99, 1, "stop")
    # ouverture sous le stop : sortie au prix d'ouverture, pas au stop
    assert st.simulate(bars[1:], 0, "long", 101, 97) == (95, 1, "stop")


def test_orb5_follows_the_first_new_york_candle():
    d = date(2026, 6, 2)                                        # mardi, heure d'été : 9:30 NY = 13:30 UTC
    t0 = int(datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc).timestamp())
    assert st._ny_ts(d, 9, 30) == t0
    bars = [Candle(t0 - 300, 99, 100, 99, 100, 1), Candle(t0, 100, 102, 99.5, 101.5, 1)]   # 1re bougie verte
    price = 101.5
    for k in range(1, 80):                                       # montée régulière jusqu'après 16:00
        bars.append(Candle(t0 + 300 * k, price, price + 0.3, price - 0.1, price + 0.2, 1))
        price += 0.2
    trades = st.orb5(st._Series(bars), "nasdaq")
    assert len(trades) == 1
    t = trades[0]
    assert (t.direction, t.entry, t.risk) == ("long", 101.5, 2.0)          # stop au plus bas de la bougie
    assert t.reason == "heure" and t.exit_ts == st._ny_ts(d, 16, 0)


def test_no_lookahead_trades_closed_before_the_cut_are_identical():
    start = int(datetime(2026, 3, 2, 0, 0, tzinfo=timezone.utc).timestamp())   # lundi
    candles = make_candles(n=288 * 20, drift=0.00002, noise=0.0012, seed=5, start_ts=start)
    full = st.run_all("nasdaq", candles)
    cut = 288 * 14
    part = st.run_all("nasdaq", candles[:cut])
    limit = candles[cut - 1].ts + 300
    key = lambda t: (t.strategy, t.entry_ts, t.direction, round(t.entry, 6), t.exit_ts, round(t.exit, 6))
    done_full = sorted(key(t) for t in full if t.exit_ts < limit - 3600)
    done_part = sorted(key(t) for t in part if t.exit_ts < limit - 3600)
    assert done_full and done_full == done_part
    assert {t.strategy for t in full} >= {"orb5", "donchian_1h", "rsi2_1h", "london_breakout"}


def test_topstep_costs_are_converted_to_points_per_micro():
    t = st.Trade("orb5", "nasdaq", "long", 0, 300, 20000.0, 20010.0, 5.0, "heure")
    r = st.trade_rs(t, 0.01, (1.72, 2.0))                       # 1,72 $ par micro, 2 $ le point
    assert round(r["gross"], 4) == 2.0
    assert round(r["net_bot"], 4) == round((10 - 2.0) / 5, 4)      # 0,01 % de 20 000 = 2 points
    assert round(r["net_topstep"], 4) == round((10 - 0.86) / 5, 4)


def test_gap_uses_previous_new_york_close_not_the_overnight_bar():
    d = date(2026, 6, 2)
    prev_close_ts = st._ny_ts(date(2026, 6, 1), 15, 55)
    bars = [Candle(prev_close_ts, 100, 100, 100, 100, 1)]
    t = prev_close_ts + 300
    while t < st._ny_ts(d, 9, 30):                      # nuit : le prix glisse à 99,5 (écart de −0,5 %)
        bars.append(Candle(t, 99.5, 99.5, 99.5, 99.5, 1))
        t += 300
    bars.append(Candle(t, 99.5, 99.6, 99.4, 99.5, 1))   # 9:30
    for k in range(1, 40):
        bars.append(Candle(t + 300 * k, 99.5, 99.7 + 0.02 * k, 99.45, 99.6 + 0.02 * k, 1))
    trades = st.gap_fade(st._Series(bars), "nasdaq")
    assert len(trades) == 1 and trades[0].direction == "long" and trades[0].reason == "objectif"
