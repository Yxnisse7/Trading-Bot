"""Essai 30, B10 : cassure Larry Williams sur le Bitcoin (jour UTC, ouverture + 0,5 × amplitude de la veille)."""
from datetime import datetime, timezone

from trading_bot import strategies as sl
from trading_bot.models import Candle

T0 = int(datetime(2026, 10, 12, tzinfo=timezone.utc).timestamp())


def _candles(day2: list[float], low2: float | None = None) -> list[Candle]:
    out = [Candle(T0 + 300 * k, 1000.0, 1050.0 if k == 100 else 1000.0, 950.0 if k == 200 else 1000.0, 1000.0, 1.0)
           for k in range(288)]                       # veille : amplitude 100
    for k, p in enumerate(day2):
        out.append(Candle(T0 + 86400 + 300 * k, p, p + 1, low2 if low2 is not None and k == 60 else p - 1, p, 1.0))
    return out


def test_buys_at_level_sells_at_midnight():
    day2 = [1000.0] * 24 + [1060.0] * 264 + [1070.0] * 2        # 02:00 : au-dessus de 1 050, puis minuit passé
    tr = sl.cassure_williams(sl._Series(_candles(day2)), "bitcoin")
    assert len(tr) == 1
    t = tr[0]
    assert t.direction == "long" and t.entry == 1060.0 and t.risk == 60.0        # ouverte au-dessus du niveau
    assert t.reason == "minuit" and t.exit == 1070.0
    assert datetime.fromtimestamp(t.exit_ts, timezone.utc).hour == 0


def test_stop_at_day_open_and_open_position():
    day2 = [1000.0] * 24 + [1060.0] * 264 + [1070.0]
    assert sl.cassure_williams(sl._Series(_candles(day2, low2=990.0)), "bitcoin")[0].reason == "stop"
    assert sl.cassure_williams(sl._Series(_candles(day2[:100])), "bitcoin")[0].reason == "fin des données"


def test_no_breakout_no_trade():
    assert sl.cassure_williams(sl._Series(_candles([1000.0] * 288)), "bitcoin") == []
