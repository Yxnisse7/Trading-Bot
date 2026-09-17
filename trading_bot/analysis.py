"""Analyse technique multi-unités de temps et score de confiance.

Chaque critère aligné apporte un poids au score. Les poids peuvent être ajustés
par le module d'apprentissage (data/adjustments.json).

Critères évalués (direction long / short) :
  trend_5m   EMA20 vs EMA50 sur 5 min, prix du bon côté de l'EMA20
  trend_15m  EMA20 vs EMA50 sur 15 min
  trend_1h   prix vs EMA20 sur 1 h
  adx        force de tendance sur 15 min (ADX) avec +DI / -DI dans le sens du trade
  vwap       prix au-dessus (long) / en dessous (short) du VWAP de la journée
  rsi        RSI 5 min en zone de momentum sain (ni sur-acheté, ni sur-vendu)
  macd       histogramme MACD 5 min du bon côté et en expansion
  level      proximité d'un support (long) / d'une résistance (short) avec de la place vers la cible
  volume     volume anormal confirmant la dernière bougie
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import indicators as ind
from .config import AssetConfig, Config
from .models import Candle

# Poids par défaut de chaque critère (modifiables par l'apprentissage)
DEFAULT_WEIGHTS: dict[str, float] = {
    "trend_5m": 1.0,
    "trend_15m": 1.0,
    "trend_1h": 1.0,
    "adx": 1.0,
    "vwap": 0.75,
    "rsi": 1.0,
    "macd": 1.0,
    "level": 1.0,
    "volume": 0.75,
}

MIN_CANDLES_5M = 80


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
    sigma_5m: float | None = None    # volatilité réalisée par bougie 5 min (log-rendements)
    adx_15m: float | None = None
    atr_ratio: float | None = None   # ATR actuel / ATR moyen des 24 dernières heures
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


def _fmt(v: float | None, d: int = 2) -> str:
    return "-" if v is None else f"{v:.{d}f}"


def key_levels(c15: list[Candle], c60: list[Candle], price: float, hourly_range: float) -> tuple[list[float], list[float]]:
    """Résistances / supports : pivots 15 min et 1 h + extrêmes de la veille, dans un rayon de 3 ranges horaires."""
    highs15, lows15 = ind.pivot_levels(c15, 4, 4)
    highs60, lows60 = ind.pivot_levels(c60, 3, 3)
    highs = highs15 + highs60
    lows = lows15 + lows60
    # extrêmes de la journée précédente (UTC)
    if c60:
        last_day = c60[-1].ts // 86400
        prev = [c for c in c60 if c.ts // 86400 == last_day - 1]
        if prev:
            highs.append(max(c.high for c in prev))
            lows.append(min(c.low for c in prev))
    radius = 3.0 * hourly_range
    highs = sorted({h for h in highs if abs(h - price) <= radius})
    lows = sorted({lo for lo in lows if abs(lo - price) <= radius})
    return highs, lows


def assess(asset: AssetConfig, candles_5m: list[Candle], cfg: Config,
           weights: dict[str, float] | None = None) -> Assessment:
    """Évalue l'actif : direction dominante, critères alignés, score pondéré."""
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update({k: float(v) for k, v in weights.items() if k in w})

    if len(candles_5m) < MIN_CANDLES_5M:
        return Assessment(asset.key, candles_5m[-1].close if candles_5m else 0.0, None, 0.0, [],
                          reasons_rejected=["historique 5 min insuffisant"])

    closes = [c.close for c in candles_5m]
    price = closes[-1]
    c15 = ind.resample(candles_5m, 15)
    c60 = ind.resample(candles_5m, 60)

    votes: dict[str, dict[str, float]] = {"long": {}, "short": {}}
    details: dict[str, str] = {}
    reasons: list[str] = []

    # --- Tendance 5 min : EMA20 vs EMA50, prix du bon côté de l'EMA20
    e20 = ind.ema(closes, 20)
    e50 = ind.ema(closes, 50)
    if e20[-1] is not None and e50[-1] is not None:
        d = _dir_from(e20[-1] > e50[-1] and price > e20[-1], e20[-1] < e50[-1] and price < e20[-1])
        details["trend_5m"] = f"EMA20 {_fmt(e20[-1])} / EMA50 {_fmt(e50[-1])}"
        if d:
            votes[d]["trend_5m"] = w["trend_5m"]

    # --- Tendance 15 min
    closes15 = [c.close for c in c15]
    e20_15 = ind.ema(closes15, 20)
    e50_15 = ind.ema(closes15, 50)
    if e20_15[-1] is not None and e50_15[-1] is not None:
        d = _dir_from(e20_15[-1] > e50_15[-1], e20_15[-1] < e50_15[-1])
        details["trend_15m"] = f"EMA20 {_fmt(e20_15[-1])} / EMA50 {_fmt(e50_15[-1])}"
        if d:
            votes[d]["trend_15m"] = w["trend_15m"]

    # --- Tendance 1 h : prix vs EMA20 1 h (EMA10 si l'historique est court)
    closes60 = [c.close for c in c60]
    period60 = 20 if len(closes60) >= 25 else 10
    e_60 = ind.ema(closes60, period60)
    if e_60[-1] is not None:
        d = _dir_from(price > e_60[-1] * 1.0005, price < e_60[-1] * 0.9995)
        details["trend_1h"] = f"prix vs EMA{period60} 1 h {_fmt(e_60[-1])}"
        if d:
            votes[d]["trend_1h"] = w["trend_1h"]

    # --- Force de tendance (ADX 15 min) : filtre anti-range + direction via +DI / -DI
    adx_v, pdi, mdi = ind.adx(c15, 14)
    adx_last = adx_v[-1] if adx_v else None
    if adx_last is not None and pdi[-1] is not None and mdi[-1] is not None:
        details["adx"] = f"ADX15 {adx_last:.1f} (+DI {pdi[-1]:.1f} / -DI {mdi[-1]:.1f})"
        if adx_last >= cfg.min_adx:
            d = _dir_from(pdi[-1] > mdi[-1], mdi[-1] > pdi[-1])
            if d:
                votes[d]["adx"] = w["adx"]
        else:
            reasons.append(f"pas de tendance exploitable (ADX 15 min {adx_last:.1f} < {cfg.min_adx})")

    # --- VWAP de la journée (UTC)
    day_start = candles_5m[-1].ts // 86400 * 86400
    vw = ind.vwap(candles_5m, day_start)
    if vw is not None and vw > 0:
        details["vwap"] = f"VWAP jour {_fmt(vw)}"
        d = _dir_from(price > vw * 1.0003, price < vw * 0.9997)
        if d:
            votes[d]["vwap"] = w["vwap"]

    # --- RSI 5 min : momentum sain, pas d'extrême
    r = ind.rsi(closes, 14)
    if r[-1] is not None:
        rv = r[-1]
        details["rsi"] = f"RSI14 5 min {rv:.1f}"
        if 52 <= rv <= 70:
            votes["long"]["rsi"] = w["rsi"]
        elif 30 <= rv <= 48:
            votes["short"]["rsi"] = w["rsi"]
        elif rv > 78 or rv < 22:
            reasons.append(f"RSI extrême ({rv:.0f}) : risque de retournement")

    # --- MACD 5 min : histogramme du bon côté et en expansion sur 3 barres
    _, _, hist = ind.macd(closes)
    if len(hist) >= 3 and None not in (hist[-1], hist[-2], hist[-3]):
        details["macd"] = f"histogramme MACD {hist[-1]:.4f}"
        if hist[-1] > 0 and hist[-1] >= hist[-2] >= hist[-3]:
            votes["long"]["macd"] = w["macd"]
        elif hist[-1] < 0 and hist[-1] <= hist[-2] <= hist[-3]:
            votes["short"]["macd"] = w["macd"]

    # --- Volatilité : ATR, range horaire moyen, volatilité réalisée
    a = ind.atr(candles_5m, cfg.atr_period)
    atr_v = a[-1]
    recent = [x for x in a[-288:] if x is not None]
    atr_ratio = (atr_v / (sum(recent) / len(recent))) if (atr_v and recent and sum(recent) > 0) else None
    hourly_range = ind.average_hourly_range(candles_5m, hours=24)
    sigma = ind.realized_volatility(closes, 48)

    # --- Niveaux clés
    support = resistance = None
    if hourly_range and hourly_range > 0:
        highs, lows = key_levels(c15, c60, price, hourly_range)
        support = ind.nearest_level(price, lows, above=False)
        resistance = ind.nearest_level(price, highs, above=True)
        tol = 0.35 * hourly_range
        near_support = support is not None and (price - support) <= tol
        near_resistance = resistance is not None and (resistance - price) <= tol
        room_up = resistance is None or (resistance - price) >= cfg.tp_range_fraction * hourly_range
        room_down = support is None or (price - support) >= cfg.tp_range_fraction * hourly_range
        details["level"] = f"support {_fmt(support, asset.price_decimals)} / résistance {_fmt(resistance, asset.price_decimals)}"
        if near_support and room_up:
            votes["long"]["level"] = w["level"]
        if near_resistance and room_down:
            votes["short"]["level"] = w["level"]

    # --- Volume anormal confirmant la dernière bougie
    vols = [c.volume for c in candles_5m]
    z = ind.volume_zscore(vols, 20)
    if z is not None and any(v > 0 for v in vols[-21:]):
        details["volume"] = f"z-score volume {z:.2f}"
        if z >= 1.5:
            last = candles_5m[-1]
            if last.close > last.open:
                votes["long"]["volume"] = w["volume"]
            elif last.close < last.open:
                votes["short"]["volume"] = w["volume"]

    # --- Direction retenue : score dominant, sans ambiguïté ni contradiction majeure
    def total(d: str) -> float:
        return sum(votes[d].values())

    sl, ss = total("long"), total("short")
    direction: str | None
    if sl == ss:
        direction = None
        reasons.append("marché indécis (signaux long / short équilibrés)")
    elif sl > ss:
        direction = "long"
    else:
        direction = "short"

    if direction:
        opposite = "short" if direction == "long" else "long"
        if "trend_15m" in votes[opposite]:
            reasons.append("tendance 15 min opposée à la direction envisagée")
            direction = None
        elif "adx" in votes[opposite]:
            reasons.append("directionnel ADX (+DI / -DI) opposé à la direction envisagée")
            direction = None
        elif total(opposite) >= 0.5 * total(direction):
            reasons.append("trop de critères contradictoires")
            direction = None
    if direction and any(r.startswith("pas de tendance") or r.startswith("RSI extrême") for r in reasons):
        direction = None

    score = round(total(direction), 2) if direction else 0.0
    criteria = sorted(votes[direction]) if direction else []
    return Assessment(asset.key, price, direction, score, criteria, details,
                      hourly_range, atr_v, support, resistance, sigma, adx_last, atr_ratio, reasons)


def confidence_label(score: float, n_criteria: int, cfg: Config) -> str | None:
    """None (faible) / "moyen" / "fort"."""
    if n_criteria < cfg.min_criteria or score < cfg.min_score:
        return None
    if score >= cfg.strong_score and n_criteria >= cfg.min_criteria + 2:
        return "fort"
    return "moyen"
