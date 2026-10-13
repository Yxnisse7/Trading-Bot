import numpy as np

from trading_bot import essai21 as e21
from trading_bot import strategies as sl
from trading_bot.models import Candle


def _flat(n=2000, px=100.0):
    return [Candle(1_700_000_000 + 300 * i, px, px + 1, px - 1, px, 0) for i in range(n)]


def test_monkeys_on_flat_market_exit_at_time_with_zero_gain():
    bars = e21.Bars(_flat())
    t = sl.Trade("x", "gold", "long", bars.ts[100], bars.ts[110], 100.0, 100.0, 5.0, "heure")
    rs = e21.monkey_rs(t, bars, lambda _e: 0.0, np.random.default_rng(1), m=50)
    assert np.allclose(rs, 0.0)


def test_monkeys_hit_stop_first_and_pay_fees():
    bars = e21.Bars(_flat())
    t = sl.Trade("x", "gold", "short", bars.ts[100], bars.ts[110], 100.0, 99.5, 0.5, "objectif")
    rs = e21.monkey_rs(t, bars, lambda _e: 0.1, np.random.default_rng(1), m=50)
    assert np.allclose(rs, (-0.5 - 0.1) / 0.5)        # stop et objectif dans la même bougie : compté en stop


def test_essai22_neighbours_and_regime():
    from datetime import date, timedelta
    from trading_bot import essai22 as e22
    assert sorted(e22.neighbours({"a": (10, 20, 30), "b": (5, 10)}, (20, 10))) == [(10, 10), (20, 5), (30, 10)]
    keys = [date(2026, 1, 1) + timedelta(days=i) for i in range(30)]
    up = [100 * 1.01 ** i * (1.002 if i % 2 else 0.998) for i in range(30)]
    ts = int(__import__("datetime").datetime(2026, 1, 29, 15, tzinfo=__import__("datetime").timezone.utc).timestamp())
    assert e22.regime(ts, keys, up) == "hausse"
