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


# ---------------------------------------------------------------------------
# Indicateurs additionnels : ADX (force de tendance), VWAP, volatilité réalisée,
# simulation de barrières (faisabilité d'un TP/SL dans un horizon donné).
# ---------------------------------------------------------------------------

def adx(candles: Sequence[Candle], period: int = 14) -> tuple[list[float | None], list[float | None], list[float | None]]:
    """ADX de Wilder. Renvoie (ADX, +DI, -DI), None tant que non calculable."""
    n = len(candles)
    out_adx: list[float | None] = [None] * n
    out_pdi: list[float | None] = [None] * n
    out_mdi: list[float | None] = [None] * n
    if n < 2 * period + 1:
        return out_adx, out_pdi, out_mdi
    tr = true_range(candles)
    pdm = [0.0] * n
    mdm = [0.0] * n
    for i in range(1, n):
        up = candles[i].high - candles[i - 1].high
        down = candles[i - 1].low - candles[i].low
        pdm[i] = up if (up > down and up > 0) else 0.0
        mdm[i] = down if (down > up and down > 0) else 0.0
    # lissage de Wilder (sommes lissées)
    s_tr = sum(tr[1:period + 1])
    s_pdm = sum(pdm[1:period + 1])
    s_mdm = sum(mdm[1:period + 1])
    dx_values: list[float] = []
    adx_prev: float | None = None
    for i in range(period, n):
        if i > period:
            s_tr = s_tr - s_tr / period + tr[i]
            s_pdm = s_pdm - s_pdm / period + pdm[i]
            s_mdm = s_mdm - s_mdm / period + mdm[i]
        if s_tr == 0:
            continue
        pdi = 100.0 * s_pdm / s_tr
        mdi = 100.0 * s_mdm / s_tr
        out_pdi[i] = pdi
        out_mdi[i] = mdi
        denom = pdi + mdi
        dx = 100.0 * abs(pdi - mdi) / denom if denom else 0.0
        if adx_prev is None:
            dx_values.append(dx)
            if len(dx_values) == period:
                adx_prev = sum(dx_values) / period
                out_adx[i] = adx_prev
        else:
            adx_prev = (adx_prev * (period - 1) + dx) / period
            out_adx[i] = adx_prev
    return out_adx, out_pdi, out_mdi


def vwap(candles: Sequence[Candle], since_ts: int) -> float | None:
    """VWAP depuis `since_ts` (prix typique pondéré par le volume). None si volume nul."""
    pv = 0.0
    vol = 0.0
    for c in candles:
        if c.ts < since_ts:
            continue
        tp = (c.high + c.low + c.close) / 3.0
        pv += tp * c.volume
        vol += c.volume
    if vol <= 0:
        return None
    return pv / vol


def realized_volatility(closes: Sequence[float], lookback: int = 48) -> float | None:
    """Écart-type des rendements logarithmiques par bougie sur `lookback` bougies."""
    if len(closes) < lookback + 1:
        return None
    rets = []
    for i in range(len(closes) - lookback, len(closes)):
        if closes[i - 1] > 0 and closes[i] > 0:
            rets.append(math.log(closes[i] / closes[i - 1]))
    if len(rets) < 10:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var)


def barrier_probabilities(price: float, tp: float, sl: float, sigma_per_step: float,
                          steps: int = 12, paths: int = 3000, seed: int = 12345) -> tuple[float, float]:
    """Simulation Monte-Carlo (marche aléatoire sans dérive, volatilité réalisée).

    Renvoie (p_resolution, p_tp_first) :
      - p_resolution : probabilité que TP ou SL soit touché avant la fin de l'horizon
      - p_tp_first   : probabilité que le TP soit touché avant le SL (sur l'horizon)
    Sert de test de faisabilité : si le marché ne bouge statistiquement pas assez
    pour atteindre l'un des deux niveaux en ~1 h, le signal n'a pas lieu d'être.
    """
    import random

    if sigma_per_step <= 0 or steps <= 0 or paths <= 0:
        return 0.0, 0.0
    long = tp > price
    rnd = random.Random(seed)
    resolved = 0
    tp_first = 0
    log_tp = math.log(tp / price)
    log_sl = math.log(sl / price)
    for _ in range(paths):
        x = 0.0
        for _ in range(steps):
            x += rnd.gauss(0.0, sigma_per_step)
            if long:
                if x >= log_tp:
                    resolved += 1
                    tp_first += 1
                    break
                if x <= log_sl:
                    resolved += 1
                    break
            else:
                if x <= log_tp:
                    resolved += 1
                    tp_first += 1
                    break
                if x >= log_sl:
                    resolved += 1
                    break
    return resolved / paths, tp_first / paths


def closed_candles(candles: Sequence[Candle], now_ts: int, step_seconds: int = 300) -> list[Candle]:
    """Écarte la bougie en cours de formation (son ouverture + durée dépasse `now_ts`)."""
    return [c for c in candles if c.ts + step_seconds <= now_ts]


def average_range(candles: Sequence[Candle], bucket_seconds: int, buckets: int = 24, min_fill: float = 0.5) -> float | None:
    """Range moyen (high - low) par tranche de `bucket_seconds`, sur les `buckets` dernières tranches.

    Généralise `average_hourly_range` à un horizon quelconque (ex. 3 h = 10 800 s).
    Une tranche n'est comptée que si elle contient au moins `min_fill` de ses bougies attendues.
    """
    if not candles or len(candles) < 2:
        return None
    step = min(b.ts - a.ts for a, b in zip(candles, candles[1:]) if b.ts > a.ts)
    expected = max(1, bucket_seconds // step)
    groups: dict[int, list[Candle]] = {}
    for c in candles:
        groups.setdefault(c.ts // bucket_seconds, []).append(c)
    ranges = []
    for key in sorted(groups)[-buckets:]:
        g = groups[key]
        if len(g) < expected * min_fill:
            continue
        ranges.append(max(x.high for x in g) - min(x.low for x in g))
    if not ranges:
        return None
    return sum(ranges) / len(ranges)


def activity_profile(candles_5m: Sequence[Candle]) -> dict[int, float]:
    """Profil d'activité par heure UTC : range moyen relatif de l'heure / moyenne de toutes les heures.

    1.0 = heure moyenne ; 0.5 = heure deux fois plus calme que la moyenne. Calculé sur les données
    disponibles (5 jours en production, 60 jours en backtest hors ligne).
    """
    sums: dict[int, list[float]] = {}
    for c in candles_5m:
        if c.close > 0:
            hour = (c.ts // 3600) % 24
            sums.setdefault(hour, []).append((c.high - c.low) / c.close)
    if not sums:
        return {}
    means = {h: sum(v) / len(v) for h, v in sums.items() if v}
    overall = sum(means.values()) / len(means)
    if overall <= 0:
        return {}
    return {h: round(m / overall, 3) for h, m in means.items()}


def day_extremes(candles: Sequence[Candle], day_index: int) -> tuple[float, float] | None:
    """Plus haut / plus bas d'un jour UTC (day_index = ts // 86400)."""
    day = [c for c in candles if c.ts // 86400 == day_index]
    if not day:
        return None
    return max(c.high for c in day), min(c.low for c in day)


def session_range(candles: Sequence[Candle], start_ts: int, end_ts: int) -> tuple[float, float] | None:
    """Plus haut / plus bas des bougies dont l'ouverture est dans [start_ts, end_ts[."""
    part = [c for c in candles if start_ts <= c.ts < end_ts]
    if not part:
        return None
    return max(c.high for c in part), min(c.low for c in part)


def pct_change(candles: Sequence[Candle], minutes: int) -> float | None:
    """Variation en % de la clôture sur les `minutes` dernières minutes (bougies 5 min)."""
    if len(candles) < 2:
        return None
    last = candles[-1]
    target = last.ts - minutes * 60
    ref = next((c for c in reversed(candles) if c.ts <= target), None)
    if ref is None or ref.close <= 0:
        return None
    return (last.close - ref.close) / ref.close * 100.0
