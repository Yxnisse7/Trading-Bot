"""Indicateurs techniques en Python pur (aucune dépendance numpy/pandas).

Toutes les fonctions prennent des listes de floats ou de Candle et renvoient
des listes de même longueur (None tant que l'indicateur n'est pas calculable).
"""
from __future__ import annotations

import math
from typing import Sequence

from .models import Candle


def sma(values: Sequence[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if period <= 0:
        return out
    total = 0.0
    for i, v in enumerate(values):
        total += v
        if i >= period:
            total -= values[i - period]
        if i >= period - 1:
            out[i] = total / period
    return out


def ema(values: Sequence[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return out
    k = 2.0 / (period + 1)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(values: Sequence[float], period: int = 14) -> list[float | None]:
    """RSI de Wilder."""
    out: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return out
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        d = values[i] - values[i - 1]
        if d >= 0:
            gains += d
        else:
            losses -= d
    avg_gain = gains / period
    avg_loss = losses / period

    def _rsi(g: float, l: float) -> float:
        if l == 0:
            return 100.0
        rs = g / l
        return 100.0 - 100.0 / (1.0 + rs)

    out[period] = _rsi(avg_gain, avg_loss)
    for i in range(period + 1, len(values)):
        d = values[i] - values[i - 1]
        gain = max(d, 0.0)
        loss = max(-d, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = _rsi(avg_gain, avg_loss)
    return out


def macd(values: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """Renvoie (ligne MACD, ligne signal, histogramme)."""
    ef = ema(values, fast)
    es = ema(values, slow)
    line: list[float | None] = [None] * len(values)
    for i in range(len(values)):
        if ef[i] is not None and es[i] is not None:
            line[i] = ef[i] - es[i]
    valid = [v for v in line if v is not None]
    sig_valid = ema(valid, signal)
    sig: list[float | None] = [None] * len(values)
    hist: list[float | None] = [None] * len(values)
    j = 0
    for i in range(len(values)):
        if line[i] is None:
            continue
        sig[i] = sig_valid[j]
        if sig[i] is not None:
            hist[i] = line[i] - sig[i]
        j += 1
    return line, sig, hist


def true_range(candles: Sequence[Candle]) -> list[float]:
    out: list[float] = []
    for i, c in enumerate(candles):
        if i == 0:
            out.append(c.high - c.low)
        else:
            pc = candles[i - 1].close
            out.append(max(c.high - c.low, abs(c.high - pc), abs(c.low - pc)))
    return out


def atr(candles: Sequence[Candle], period: int = 14) -> list[float | None]:
    """ATR de Wilder."""
    tr = true_range(candles)
    out: list[float | None] = [None] * len(candles)
    if len(tr) < period:
        return out
    prev = sum(tr[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(tr)):
        prev = (prev * (period - 1) + tr[i]) / period
        out[i] = prev
    return out


def volume_zscore(volumes: Sequence[float], lookback: int = 20) -> float | None:
    """Z-score du dernier volume par rapport aux `lookback` précédents."""
    if len(volumes) < lookback + 1:
        return None
    window = list(volumes[-lookback - 1:-1])
    last = volumes[-1]
    mean = sum(window) / len(window)
    var = sum((v - mean) ** 2 for v in window) / len(window)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (last - mean) / std


def pivot_levels(candles: Sequence[Candle], left: int = 3, right: int = 3) -> tuple[list[float], list[float]]:
    """Détection de swing highs (résistances) et swing lows (supports)."""
    highs: list[float] = []
    lows: list[float] = []
    n = len(candles)
    for i in range(left, n - right):
        h = candles[i].high
        l = candles[i].low
        if all(h > candles[j].high for j in range(i - left, i)) and all(h >= candles[j].high for j in range(i + 1, i + right + 1)):
            highs.append(h)
        if all(l < candles[j].low for j in range(i - left, i)) and all(l <= candles[j].low for j in range(i + 1, i + right + 1)):
            lows.append(l)
    return highs, lows


def nearest_level(price: float, levels: Sequence[float], above: bool) -> float | None:
    cands = [lv for lv in levels if (lv > price if above else lv < price)]
    if not cands:
        return None
    return min(cands) if above else max(cands)


def average_hourly_range(candles_5m: Sequence[Candle], hours: int = 24) -> float | None:
    """Range moyen (high-low) par tranche d'une heure, sur les `hours` dernières heures.

    Les bougies 5 minutes sont regroupées par heure de clôture (12 bougies).
    C'est la base pour calibrer un TP/SL atteignable en ~1h.
    """
    if len(candles_5m) < 12:
        return None
    buckets: dict[int, list[Candle]] = {}
    for c in candles_5m:
        buckets.setdefault(c.ts // 3600, []).append(c)
    ranges = []
    for key in sorted(buckets)[-hours:]:
        group = buckets[key]
        if len(group) < 6:  # heure trop incomplète
            continue
        ranges.append(max(x.high for x in group) - min(x.low for x in group))
    if not ranges:
        return None
    return sum(ranges) / len(ranges)


def resample(candles: Sequence[Candle], minutes: int) -> list[Candle]:
    """Agrège des bougies (ex. 5m) vers une unité de temps supérieure (15m, 60m)."""
    step = minutes * 60
    buckets: dict[int, list[Candle]] = {}
    for c in candles:
        buckets.setdefault(c.ts // step * step, []).append(c)
    out = []
    for key in sorted(buckets):
        g = buckets[key]
        out.append(Candle(ts=key, open=g[0].open, high=max(x.high for x in g),
                          low=min(x.low for x in g), close=g[-1].close,
                          volume=sum(x.volume for x in g)))
    return out


def slope(values: Sequence[float | None], lookback: int = 5) -> float | None:
    """Pente relative (variation en % sur `lookback` points) d'une série d'indicateur."""
    vals = [v for v in values if v is not None]
    if len(vals) <= lookback or vals[-1 - lookback] == 0:
        return None
    return (vals[-1] - vals[-1 - lookback]) / abs(vals[-1 - lookback]) * 100.0
