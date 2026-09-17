"""Analyse technique multi-unités de temps et score de confiance.

Chaque critère aligné apporte un poids au score. Les poids peuvent être ajustés
par le module d'apprentissage (data/adjustments.json).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import indicators as ind
from .config import AssetConfig, Config
from .models import Candle

# Poids par défaut de chaque critère (modifiables par l'apprentissage)
DEFAULT_WEIGHTS: dict[str, float] = {
    "trend_5m": 1.0,       # EMA20 > EMA50 sur 5 min (ou inverse)
    "trend_15m": 1.0,      # EMA20 > EMA50 sur 15 min
    "trend_1h": 1.0,       # prix au-dessus / en dessous de l'EMA20 sur 1h
    "rsi": 1.0,            # RSI 5m dans une zone de momentum sain (55-70 long / 30-45 short)
    "macd": 1.0,           # histogramme MACD du bon côté et en expansion
    "level": 1.0,          # proximité d'un support (long) / résistance (short) récent
    "volume": 0.75,        # volume anormalement élevé (z-score > 1.5)
}


@dataclass
class Assessment:
    asset: str
    price: float
    direction: str | None            # long / short / None
    score: float
    criteria: list[str]              # critères alignés pour la direction retenue
    details: dict[str, str] = field(default_factory=dict)
    hourly_range: float | None = None
    atr: float | None = None
    support: float | None = None
    resistance: float | None = None
    reasons_rejected: list[str] = field(default_factory=list)

    @property
    def n_criteria(self) -> int:
        return len(self.criteria)


def _dir_from(cond_long: bool, cond_short: bool) -> str | None:
    if cond_long and not cond_short:
        return "long"
    if cond_short and not cond_long:
        return "short"
    return None


def assess(asset: AssetConfig, candles_5m: list[Candle], cfg: Config,
           weights: dict[str, float] | None = None) -> Assessment:
    """Évalue l'actif : direction dominante, critères alignés, score pondéré."""
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    if len(candles_5m) < 80:
        return Assessment(asset.key, candles_5m[-1].close if candles_5m else 0.0, None, 0.0, [],
                          reasons_rejected=["historique 5m insuffisant"])

    closes = [c.close for c in candles_5m]
    price = closes[-1]
    c15 = ind.resample(candles_5m, 15)
    c60 = ind.resample(candles_5m, 60)

    votes: dict[str, dict[str, float]] = {"long": {}, "short": {}}
    details: dict[str, str] = {}

    # --- Tendance 5m : EMA20 vs EMA50 + pente
    e20 = ind.ema(closes, 20)
    e50 = ind.ema(closes, 50)
    if e20[-1] is not None and e50[-1] is not None:
        d = _dir_from(e20[-1] > e50[-1] and price > e20[-1], e20[-1] < e50[-1] and price < e20[-1])
        details["trend_5m"] = f"EMA20 {e20[-1]:.2f} / EMA50 {e50[-1]:.2f}"
        if d:
            votes[d]["trend_5m"] = w["trend_5m"]

    # --- Tendance 15m
    closes15 = [c.close for c in c15]
    e20_15 = ind.ema(closes15, 20)
    e50_15 = ind.ema(closes15, 50)
    if e20_15[-1] is not None and e50_15[-1] is not None:
        d = _dir_from(e20_15[-1] > e50_15[-1], e20_15[-1] < e50_15[-1])
        details["trend_15m"] = f"EMA20 {e20_15[-1]:.2f} / EMA50 {e50_15[-1]:.2f}"
        if d:
            votes[d]["trend_15m"] = w["trend_15m"]

    # --- Tendance 1h : prix vs EMA20 1h (ou EMA10 si peu d'historique)
    closes60 = [c.close for c in c60]
    period60 = 20 if len(closes60) >= 25 else 10
    e_60 = ind.ema(closes60, period60)
    if e_60[-1] is not None:
        d = _dir_from(price > e_60[-1] * 1.0005, price < e_60[-1] * 0.9995)
        details["trend_1h"] = f"prix vs EMA{period60} 1h {e_60[-1]:.2f}"
        if d:
            votes[d]["trend_1h"] = w["trend_1h"]

    # --- RSI 5m : momentum sain, pas d'extrême (on évite d'acheter du sur-acheté)
    r = ind.rsi(closes, 14)
    if r[-1] is not None:
        rv = r[-1]
        details["rsi"] = f"RSI14 5m = {rv:.1f}"
        if 52 <= rv <= 70:
            votes["long"]["rsi"] = w["rsi"]
        elif 30 <= rv <= 48:
            votes["short"]["rsi"] = w["rsi"]

    # --- MACD 5m : histogramme du bon côté et en expansion (2 dernières barres)
    _, _, hist = ind.macd(closes)
    if len(hist) >= 3 and hist[-1] is not None and hist[-2] is not None and hist[-3] is not None:
        details["macd"] = f"hist MACD = {hist[-1]:.4f}"
        if hist[-1] > 0 and hist[-1] >= hist[-2] >= hist[-3]:
            votes["long"]["macd"] = w["macd"]
        elif hist[-1] < 0 and hist[-1] <= hist[-2] <= hist[-3]:
            votes["short"]["macd"] = w["macd"]

    # --- Volatilité : ATR et range horaire moyen
    a = ind.atr(candles_5m, cfg.atr_period)
    atr_v = a[-1]
    hourly_range = ind.average_hourly_range(candles_5m, hours=24)

    # --- Niveaux clés (supports / résistances sur 15m)
    highs, lows = ind.pivot_levels(c15, 3, 3)
    support = ind.nearest_level(price, lows, above=False)
    resistance = ind.nearest_level(price, highs, above=True)
    if hourly_range and hourly_range > 0:
        tol = 0.35 * hourly_range
        near_support = support is not None and (price - support) <= tol
        near_resistance = resistance is not None and (resistance - price) <= tol
        # Long : on est proche d'un support ET on a de la place jusqu'à la résistance
        room_up = resistance is None or (resistance - price) >= cfg.tp_range_fraction * hourly_range
        room_down = support is None or (price - support) >= cfg.tp_range_fraction * hourly_range
        details["level"] = f"support {support if support else '-'} / résistance {resistance if resistance else '-'}"
        if near_support and room_up:
            votes["long"]["level"] = w["level"]
        if near_resistance and room_down:
            votes["short"]["level"] = w["level"]
        # Pas de place vers la cible = pénalité forte (on n'enlève rien, on refuse plus bas)
        if not room_up:
            votes["long"].pop("level", None)
            votes["long"]["_blocked"] = 0.0
        if not room_down:
            votes["short"].pop("level", None)
            votes["short"]["_blocked"] = 0.0

    # --- Volume anormal (confirme la direction de la dernière bougie)
    vols = [c.volume for c in candles_5m]
    z = ind.volume_zscore(vols, 20)
    if z is not None and any(v > 0 for v in vols[-21:]):
        details["volume"] = f"z-score volume = {z:.2f}"
        if z >= 1.5:
            last = candles_5m[-1]
            if last.close > last.open:
                votes["long"]["volume"] = w["volume"]
            elif last.close < last.open:
                votes["short"]["volume"] = w["volume"]

    # --- Direction retenue : celle qui a le plus de score, sans ambiguïté
    def total(d: str) -> float:
        return sum(v for k, v in votes[d].items() if not k.startswith("_"))

    sl, ss = total("long"), total("short")
    reasons: list[str] = []
    direction: str | None
    if sl == ss:
        direction = None
        reasons.append("marché indécis (signaux long/short équilibrés)")
    elif sl > ss:
        direction = "long"
    else:
        direction = "short"

    # Refus si des critères contradictoires majeurs : tendance 15m opposée
    if direction and "trend_15m" in votes["short" if direction == "long" else "long"]:
        reasons.append("tendance 15m opposée à la direction envisagée")
        direction = None
    if direction and "_blocked" in votes[direction]:
        reasons.append("niveau clé trop proche dans le sens du trade (pas de place pour le TP)")
        direction = None

    score = total(direction) if direction else 0.0
    criteria = sorted(k for k in votes[direction] if not k.startswith("_")) if direction else []
    return Assessment(asset.key, price, direction, round(score, 2), criteria, details,
                      hourly_range, atr_v, support, resistance, reasons)


def confidence_label(score: float, n_criteria: int, cfg: Config) -> str | None:
    """faible (None) / moyen / fort."""
    if n_criteria < cfg.min_criteria or score < cfg.min_score:
        return None
    if score >= cfg.strong_score and n_criteria >= cfg.min_criteria + 1:
        return "fort"
    return "moyen"
