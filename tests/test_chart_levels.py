"""Niveaux du jour publiés pour l'onglet Graphique du site (lecture seulement)."""
from datetime import datetime, timezone

from trading_bot import strategies as sl
from trading_bot.models import Candle


def _flat(start: datetime, days: int, price=100.0, step=300):
    t0 = int(start.timestamp())
    return [Candle(t0 + i * step, price, price + 1, price - 1, price) for i in range(days * 86400 // step)]


def test_williams_level_is_day_open_plus_half_previous_range():
    c = _flat(datetime(2026, 10, 26, tzinfo=timezone.utc), 3)
    lv = sl.chart_levels("cassure_williams", c)
    assert lv["kind"] == "level"
    assert lv["stop"] == 100.0 and lv["range"] == 2.0 and lv["level"] == 101.0
    assert lv["to"] - lv["from"] == 86400


def test_donchian_channel_and_nuit_window():
    c = _flat(datetime(2026, 10, 26, tzinfo=timezone.utc), 4)
    ch = sl.chart_levels("donchian_1h", c)
    assert ch["kind"] == "channel" and len(ch["points"]) == 48 and ch["points"][-1][1:] == [101.0, 99.0]
    win = sl.chart_levels("nuit_asie", c)
    assert win["kind"] == "window" and win["to"] - win["from"] == 9 * 3600
    assert win["entry"] == 100.0 and win["stop"] == 99.0


def test_no_levels_without_enough_history_or_for_other_strategies():
    c = _flat(datetime(2026, 10, 26, tzinfo=timezone.utc), 3)
    assert sl.chart_levels("noise_area_v2", c) is None       # 14 séances nécessaires
    assert sl.chart_levels("swing_w3", c) is None
    assert sl.chart_levels("cassure_williams", []) is None
