"""Essai 27, N2 : achat de l'or à 18:00 (New York) du lundi au jeudi, vente à 03:00, stop de sécurité à 1 %."""
from datetime import datetime

from trading_bot import strategies as sl
from trading_bot.models import Candle


def _candles(start: datetime, n: int, low_at: int | None = None) -> list[Candle]:
    t0 = int(start.timestamp())
    out = []
    for k in range(n):
        p = 4000.0 + k * 0.1
        out.append(Candle(t0 + 300 * k, p, p + 1, 3950.0 if k == low_at else p - 1, p + 0.05, 1.0))
    return out


def test_buys_at_six_sells_at_three():
    c = _candles(datetime(2026, 10, 13, 17, 0, tzinfo=sl.NY), 12 * 12)     # mardi 17:00 → mercredi 05:00
    tr = sl.nuit_asie(sl._Series(c), "gold")
    assert len(tr) == 1
    t = tr[0]
    assert datetime.fromtimestamp(t.entry_ts, sl.NY).hour == 18
    assert datetime.fromtimestamp(t.exit_ts, sl.NY).hour == 3 and t.reason == "matin"
    assert t.direction == "long" and abs(t.risk - t.entry * 0.01) < 1e-9 and t.exit > t.entry


def test_stop_and_open_position():
    c = _candles(datetime(2026, 10, 13, 17, 0, tzinfo=sl.NY), 12 * 12, low_at=30)
    assert sl.nuit_asie(sl._Series(c), "gold")[0].reason == "stop"
    c = _candles(datetime(2026, 10, 13, 17, 0, tzinfo=sl.NY), 12 * 4)      # données jusqu'à 21:00
    assert sl.nuit_asie(sl._Series(c), "gold")[0].reason == "fin des données"


def test_no_entry_on_friday():
    c = _candles(datetime(2026, 10, 16, 17, 0, tzinfo=sl.NY), 12 * 4)      # vendredi
    assert sl.nuit_asie(sl._Series(c), "gold") == []
