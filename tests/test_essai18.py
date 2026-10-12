from datetime import datetime, timezone

from trading_bot import essai18 as e18
from trading_bot.models import Candle

T0 = int(datetime(2026, 10, 6, 13, 0, tzinfo=timezone.utc).timestamp())   # mardi 9:00 à New York


def bars(prices):
    """(plus haut, plus bas) par minute, ouverture et clôture au milieu."""
    return [Candle(T0 + 60 * k, (h + l) / 2, h, l, (h + l) / 2, 10.0) for k, (h, l) in enumerate(prices)]


def test_stop_counted_first_when_stop_and_target_in_same_minute():
    c = bars([(100.5, 99.5), (102, 98)])
    px, j, reason = e18.manage(c, 0, 1, 100.0, 99.0, 1.0, "X1")
    assert (px, j, reason) == (99.0, 1, "stop")


def test_x1_takes_target_at_one_r():
    c = bars([(100.2, 99.8), (101.2, 100.1)])
    assert e18.manage(c, 0, 1, 100.0, 99.0, 1.0, "X1") == (101.0, 1, "objectif")


def test_x2_half_at_target_then_trailing_stop():
    # objectif à 101 (minute 1), le prix monte jusqu'à 104 puis redescend sous le plus bas des 5 dernières minutes
    c = bars([(100.2, 99.8), (101.2, 100.6), (102, 101.5), (103, 102.5), (104, 103.5), (104, 103.6),
              (104, 103.7), (104, 103.8), (104, 103.9), (103.6, 102.0)])
    px, j, reason = e18.manage(c, 0, 1, 100.0, 99.0, 1.0, "X2")
    assert reason == "suiveur" and j == 9
    assert px == (101.0 + 103.5) / 2          # moitié à l'objectif, moitié au plus bas des 5 minutes précédentes


def test_x2_rest_exits_at_entry_if_same_minute_goes_back():
    c = bars([(100.2, 99.8), (101.2, 99.95)])
    assert e18.manage(c, 0, 1, 100.0, 99.0, 1.0, "X2") == (100.5, 1, "objectif")


def test_max_duration_closes_after_one_hour():
    c = bars([(100.2, 99.8)] * 70)
    px, j, reason = e18.manage(c, 0, 1, 100.0, 99.0, 1.0, "X1")
    assert reason == "durée" and j == 60 and px == 100.0


def test_hours_skip_us_releases_and_weekend():
    assert e18.hours_ok(T0)                                   # 9:00 New York
    assert not e18.hours_ok(T0 - 30 * 60)                     # 8:30 New York : annonces
    sat = int(datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc).timestamp())
    assert not e18.hours_ok(sat)
    late = int(datetime(2026, 10, 6, 20, 5, tzinfo=timezone.utc).timestamp())
    assert not e18.hours_ok(late)
