import lzma
import struct

from trading_bot import essai19 as e19
from trading_bot.essai19 import Tick

T0 = 1_791_900_000_000


def ticks(mids, step_ms=1000):
    return [Tick(T0 + k * step_ms, m - 0.05, m + 0.05) for k, m in enumerate(mids)]


def test_target_counts_vantage_costs():
    # entrée au milieu 100 + 0,075 ; sortie quand milieu − 0,075 ≥ entrée + 0,30
    t, j = e19._trade(ticks([100.0, 100.2, 100.46]), 0, 1, 0.30, 0.50, False)
    assert t.reason == "objectif" and j == 2
    assert round(t.gross_points(), 3) == 0.31


def test_stop_and_short_side():
    t, _ = e19._trade(ticks([100.0, 100.2, 100.5]), 0, -1, 0.30, 0.50, False)
    assert t.reason == "stop" and t.direction == "short"


def test_exit_after_sixty_seconds():
    t, j = e19._trade(ticks([100.0] * 70), 0, 1, 0.30, 0.50, False)
    assert t.reason == "durée" and j == 60


def test_dukascopy_mode_pays_real_spread():
    t, _ = e19._trade(ticks([100.0] * 70), 0, 1, 0.30, 0.50, True)
    assert round(t.gross_points(), 3) == -0.10


def test_parse_hour():
    raw = lzma.compress(struct.pack(">3i2f", 1500, 4100250, 4100100, 1.0, 1.0), format=lzma.FORMAT_ALONE)
    assert e19.parse_hour(raw, T0) == [Tick(T0 + 1500, 4100.1, 4100.25)]
