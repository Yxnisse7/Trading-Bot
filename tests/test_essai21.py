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
