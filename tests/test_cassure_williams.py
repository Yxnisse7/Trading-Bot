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


def test_crabel_nr4_trades_breakout_after_inside_narrow_day():
    """Veille ID/NR4 → achat à ouverture + marge, sortie à la clôture de la séance CME (17:00 New York)."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from trading_bot import strategies as sl
    from trading_bot.models import Candle
    ny = ZoneInfo("America/New_York")
    candles = []
    start = datetime(2026, 9, 1, 18, 0, tzinfo=ny)          # mardi 18:00 → séance du mercredi
    ranges = [10, 10, 10, 10, 10, 10, 10, 10, 10, 9, 8, 4, 10]   # avant-dernière séance contenue et la plus étroite
    day = start
    for n, rg in enumerate(ranges):
        while day.weekday() in (4, 5) and day.hour == 18:     # pas de séance démarrant vendredi/samedi soir
            day += timedelta(days=1)
        for k in range(276):                                   # 23 h de bougies 5 min
            t = int((day + timedelta(minutes=5 * k)).timestamp())
            o = 100.0
            if n == len(ranges) - 1 and k >= 10:               # dernière séance : monte franchement
                o = 100.0 + k * 0.05
            half = rg / 2 if k == 1 and n < len(ranges) - 1 else 0.5
            candles.append(Candle(t, o, o + half, o - half, o))
        day += timedelta(days=1)
    tr = sl.crabel_nr4(sl._Series(candles), "gold")
    assert len(tr) == 1
    assert tr[0].direction == "long" and tr[0].exit > tr[0].entry
