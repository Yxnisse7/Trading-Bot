from trading_bot import indicators as ind
from trading_bot.models import Candle

from conftest import make_candles


def test_sma_ema_lengths_and_values():
    v = [1, 2, 3, 4, 5, 6]
    s = ind.sma(v, 3)
    assert s[:2] == [None, None]
    assert s[2] == 2 and s[-1] == 5
    e = ind.ema(v, 3)
    assert e[1] is None and e[2] == 2
    assert e[-1] is not None and 4.5 < e[-1] < 6


def test_rsi_bounds_and_direction():
    up = [float(i) for i in range(1, 40)]
    r = ind.rsi(up, 14)
    assert r[-1] == 100.0
    down = [float(40 - i) for i in range(1, 40)]
    assert ind.rsi(down, 14)[-1] == 0.0
    mixed = [100 + (i % 3) for i in range(60)]
    assert 0 <= ind.rsi(mixed, 14)[-1] <= 100


def test_macd_hist_positive_in_uptrend():
    closes = [c.close for c in make_candles(300, drift=0.001, noise=0.0001)]
    _, _, hist = ind.macd(closes)
    assert hist[-1] is not None and hist[-1] > 0


def test_atr_and_hourly_range_positive():
    candles = make_candles(300)
    a = ind.atr(candles, 14)
    assert a[-1] is not None and a[-1] > 0
    hr = ind.average_hourly_range(candles, 24)
    assert hr is not None and hr > a[-1]  # le range horaire dépasse l'ATR 5m


def test_resample_15m_groups_three_candles():
    candles = make_candles(30)
    c15 = ind.resample(candles, 15)
    assert len(c15) in (10, 11)
    assert all(x.high >= x.low for x in c15)
    assert c15[0].open == candles[0].open


def test_pivots_and_nearest_level():
    candles = [Candle(i * 300, 10, 10, 10, 10) for i in range(10)]
    candles[5] = Candle(5 * 300, 10, 12, 10, 10)    # swing high
    candles[2] = Candle(2 * 300, 10, 10, 8, 10)     # swing low (gauche = 0,1 ; droite = 3,4,5)
    highs, lows = ind.pivot_levels(candles, 2, 2)
    assert 12 in highs and 8 in lows
    assert ind.nearest_level(10, [8, 12, 15], above=True) == 12
    assert ind.nearest_level(10, [8, 12, 15], above=False) == 8


def test_volume_zscore():
    vols = [100.0] * 20 + [100.0]
    assert ind.volume_zscore(vols, 20) == 0.0
    vols = [100.0 + (i % 2) for i in range(20)] + [500.0]
    assert ind.volume_zscore(vols, 20) > 3
