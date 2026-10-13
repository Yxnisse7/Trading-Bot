from trading_bot import essai20 as e20
from trading_bot.models import Candle

T0 = 1_791_900_000


def c5(k, o, h, l, cl):
    return Candle(T0 + 300 * k, o, h, l, cl)


def test_exhaustion_needs_twice_the_average_range():
    m5 = [c5(k, 100, 101, 100, 100.5) for k in range(20)] + [c5(20, 101, 101, 98.9, 99.2)]
    assert e20.exhaustion(m5, 20) == 1
    m5[-1] = c5(20, 101, 101, 99.5, 99.8)
    assert e20.exhaustion(m5, 20) == 0


def test_level_must_hold():
    prev = [c5(k, 4195, 4196, 4190, 4195) for k in range(36)]
    held = prev + [c5(36, 4192, 4192, 4180.5, 4183)]          # mèche près de 4 180, clôture au-dessus
    broke = prev + [c5(36, 4192, 4192, 4178.5, 4179)]         # clôture sous 4 180
    assert e20.on_level(held, 36, 1) and not e20.on_level(broke, 36, 1)


def test_manage_stop_first_and_duration():
    m1 = [Candle(T0 + 60 * k, 100, 100.5, 99.5, 100) for k in range(40)]
    assert e20.manage(m1, 0, 1, 100, 99.6, 101) == (99.6, 0, "stop")
    assert e20.manage(m1, 0, 1, 100, 99, 101) == (100, 30, "durée")
