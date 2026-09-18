"""Construction d'un signal exploitable (entrée, TP, SL) à partir d'une évaluation.

Calibrage des niveaux :
  - base : range horaire moyen des 24 dernières heures (bougies 5 min)
  - TP = 60 % du range, ramené devant le niveau clé le plus proche s'il est plus près
  - SL = 40 % du range, ou juste au-delà du niveau clé opposé s'il est proche,
    en conservant le ratio risque / rendement minimal
  - contrôle de faisabilité : simulation Monte-Carlo sur la volatilité réalisée,
    le signal est refusé si TP ou SL ont peu de chances d'être touchés sous ~1 h
"""
from __future__ import annotations

import uuid
from datetime import timedelta
from zoneinfo import ZoneInfo

from . import indicators as ind
from .analysis import Assessment, confidence_label
from .config import AssetConfig, Config
from .models import Signal, iso, parse_iso, utcnow

_LABELS = {
    "trend_5m": "tendance de base", "trend_15m": "tendance ×3", "trend_1h": "tendance ×12",
    "adx": "tendance forte (ADX)", "vwap": "prix du bon côté du VWAP",
    "rsi": "RSI en momentum", "macd": "MACD en expansion", "level": "niveau clé favorable",
    "volume": "volume anormal",
    "orb": "cassure du range d'ouverture",
    "pdhl": "cassure des extrêmes de la veille",
    "corr": "marché meneur favorable",
}


def horizon_label(minutes: int) -> str:
    return f"{minutes // 60} h" if minutes % 60 == 0 else f"{minutes} min"


def round_to_tick(value: float, tick: float) -> float:
    if tick <= 0:
        return value
    return round(round(value / tick) * tick, 6)


def criterion_label(c: str, base_minutes: int = 5) -> str:
    if c in ("trend_5m", "trend_15m", "trend_1h"):
        mult = {"trend_5m": 1, "trend_15m": 3, "trend_1h": 12}[c]
        return f"tendance {horizon_label(base_minutes * mult)}"
    return _LABELS.get(c, c)


def compute_levels(a: Assessment, cfg: Config) -> tuple[float, float, list[str]]:
    """Distances TP et SL (en prix) à partir du range horaire et des niveaux clés.

    Renvoie (tp_dist, sl_dist, raisons_de_refus). Distances nulles si refus.
    """
    hr = a.hourly_range or 0.0
    price = a.price
    reasons: list[str] = []
    if hr <= 0:
        return 0.0, 0.0, ["range horaire indisponible"]

    min_tp = cfg.min_tp_range_fraction * hr
    tp_dist = min(cfg.max_tp_range_fraction * hr, cfg.tp_range_fraction * hr)

    # Cible ramenée devant le niveau clé le plus proche dans le sens du trade
    if a.direction == "long" and a.resistance is not None:
        tp_dist = min(tp_dist, (a.resistance - price) * 0.9)
    if a.direction == "short" and a.support is not None:
        tp_dist = min(tp_dist, (price - a.support) * 0.9)
    if tp_dist < min_tp:
        reasons.append("niveau clé trop proche dans le sens du trade : pas de place pour une cible réaliste")
        return 0.0, 0.0, reasons

    # Stop : fraction du range, réduit si besoin pour conserver le ratio minimal
    sl_dist = min(cfg.sl_range_fraction * hr, tp_dist / cfg.min_risk_reward)
    sl_dist = max(sl_dist, cfg.min_sl_range_fraction * hr)

    # Stop placé juste au-delà du niveau clé opposé s'il est proche (évite le stop « dans le bruit »)
    buffer = 0.08 * hr
    if a.direction == "long" and a.support is not None:
        beyond = (price - a.support) + buffer
        if sl_dist < beyond <= tp_dist / cfg.min_risk_reward:
            sl_dist = beyond
    if a.direction == "short" and a.resistance is not None:
        beyond = (a.resistance - price) + buffer
        if sl_dist < beyond <= tp_dist / cfg.min_risk_reward:
            sl_dist = beyond

    if sl_dist <= 0 or tp_dist / sl_dist < cfg.min_risk_reward:
        reasons.append(f"ratio risque / rendement insuffisant ({tp_dist / sl_dist if sl_dist else 0:.2f})")
        return 0.0, 0.0, reasons
    return tp_dist, sl_dist, reasons


def build_signal(asset: AssetConfig, a: Assessment, cfg: Config, news_context: str,
                 now=None, *, simulate: bool = True) -> tuple[Signal | None, list[str]]:
    """Renvoie (signal, raisons_de_refus). Un signal n'est produit que si tout converge."""
    reasons: list[str] = list(a.reasons_rejected)
    now = now or utcnow()

    if a.direction is None:
        reasons.append("aucune direction dominante")
        return None, reasons
    if cfg.contrarian:
        from dataclasses import replace
        a = replace(a, direction="short" if a.direction == "long" else "long")

    conf = confidence_label(a.score, a.n_criteria, cfg)
    if conf is None:
        reasons.append(f"convergence insuffisante (score {a.score}, {a.n_criteria} critère(s) aligné(s))")
        return None, reasons
    if cfg.min_confidence == "fort" and conf != "fort":
        reasons.append("confiance moyenne alors que « fort » est exigé")
        return None, reasons

    hr = a.hourly_range
    if not hr or hr <= 0:
        reasons.append("range horaire indisponible")
        return None, reasons

    hr_pct = hr / a.price * 100.0
    if hr_pct < asset.min_hourly_range_pct:
        reasons.append(f"volatilité horaire trop faible ({hr_pct:.3f} %) : cible inatteignable en 1 h")
        return None, reasons
    if hr_pct > asset.max_hourly_range_pct:
        reasons.append(f"volatilité horaire anormale ({hr_pct:.2f} %) : marché instable")
        return None, reasons
    if a.atr_ratio is not None and a.atr_ratio > cfg.max_atr_ratio:
        reasons.append(f"volatilité instantanée anormale (ATR ×{a.atr_ratio:.1f} vs moyenne 24 h) : mouvement inexpliqué")
        return None, reasons

    tp_dist, sl_dist, why = compute_levels(a, cfg)
    if why:
        reasons.extend(why)
        return None, reasons

    entry = round_to_tick(a.price, asset.tick_size)
    if a.direction == "long":
        tp = round_to_tick(entry + tp_dist, asset.tick_size)
        sl = round_to_tick(entry - sl_dist, asset.tick_size)
    else:
        tp = round_to_tick(entry - tp_dist, asset.tick_size)
        sl = round_to_tick(entry + sl_dist, asset.tick_size)
    if tp == entry or sl == entry:
        reasons.append("niveaux TP / SL confondus avec l'entrée après arrondi")
        return None, reasons
    rr = abs(tp - entry) / abs(entry - sl)
    if rr < cfg.min_risk_reward:
        reasons.append(f"ratio risque / rendement insuffisant après arrondi ({rr:.2f})")
        return None, reasons
    tp_pct = abs(tp - entry) / entry * 100.0
    if asset.cost_pct > 0 and tp_pct < cfg.min_tp_to_cost_ratio * asset.cost_pct:
        reasons.append(f"cible trop petite face aux coûts ({tp_pct:.2f} % pour {asset.cost_pct:.2f} % de frais)")
        return None, reasons

    # Faisabilité statistique sur l'horizon (marche aléatoire, volatilité réalisée par bougie de base)
    horizon = a.horizon_minutes or cfg.signal_lifetime_minutes
    hlabel = horizon_label(horizon)
    p_res = p_tp = None
    if simulate and a.sigma_5m:
        steps = max(1, horizon // max(1, a.base_minutes))
        p_res, p_tp = ind.barrier_probabilities(entry, tp, sl, a.sigma_5m, steps=steps)
        if p_res < cfg.min_resolution_probability:
            reasons.append(f"faible probabilité de résolution sous {hlabel} ({p_res:.0%}) : marché trop calme pour ces niveaux")
            return None, reasons

    tech = ", ".join(criterion_label(c, a.base_minutes) for c in a.criteria)
    rationale = (f"{'Achat' if a.direction == 'long' else 'Vente'} : {tech}. "
                 f"Range moyen sur {hlabel} ≈ {hr:.{asset.price_decimals}f} ({hr_pct:.2f} %), "
                 f"TP = {tp_dist / hr * 100:.0f} % du range, SL = {sl_dist / hr * 100:.0f} % du range"
                 + (f", probabilité de résolution sous {hlabel} ≈ {p_res:.0%}" if p_res is not None else "") + ".")

    sig = Signal(
        id=uuid.uuid4().hex[:10],
        asset=asset.key, asset_label=asset.label, direction=a.direction,
        entry=entry, take_profit=tp, stop_loss=sl, risk_reward=round(rr, 2),
        confidence=conf, score=a.score, criteria=list(a.criteria),
        rationale=rationale, news_context=news_context,
        created_at=iso(now), expires_at=iso(now + timedelta(minutes=horizon)),
        hourly_range=round(hr, 6), horizon=("1h" if horizon <= 60 else hlabel.replace(" ", "")), horizon_minutes=horizon,
        meta={"details": a.details, "support": a.support, "resistance": a.resistance,
              "atr_5m": a.atr, "atr_ratio": a.atr_ratio, "hourly_range_pct": round(hr_pct, 4), "adx_15m": a.adx_15m,
              "sigma_5m": a.sigma_5m, "p_resolution": p_res, "p_tp_neutral": p_tp,
              "activity_ratio": a.activity_ratio, "base_minutes": a.base_minutes},
    )
    return sig, reasons


def format_signal(sig: Signal, tz: str = "Europe/Paris") -> str:
    zone = ZoneInfo(tz)
    created = parse_iso(sig.created_at).astimezone(zone)
    expires = parse_iso(sig.expires_at).astimezone(zone)
    arrow = "🟢 LONG" if sig.direction == "long" else "🔴 SHORT"
    kind = "SCALP ~1 h" if (sig.horizon_minutes or 60) <= 60 else f"INTRADAY ~{horizon_label(sig.horizon_minutes)}"
    risk_pct = abs(sig.entry - sig.stop_loss) / sig.entry * 100.0
    reward_pct = abs(sig.take_profit - sig.entry) / sig.entry * 100.0
    lines = [
        f"📡 SIGNAL {arrow} — {sig.asset_label} — {kind}",
        f"Heure : {created:%d/%m/%Y %H:%M} ({tz}) — id {sig.id}",
        f"Entrée visée : {sig.entry}",
        f"Take Profit  : {sig.take_profit} (+{reward_pct:.2f} %)",
        f"Stop Loss    : {sig.stop_loss} (−{risk_pct:.2f} %)",
        f"Risque / rendement : {sig.risk_reward}",
        f"Confiance : {sig.confidence.upper()} (score {sig.score}, {len(sig.criteria)} critères alignés)",
        f"Justification : {sig.rationale}",
        f"Actualité : {sig.news_context}",
        f"Durée estimée : ~{horizon_label(sig.horizon_minutes or 60)} — valable jusqu'à {expires:%H:%M} ({tz}), puis expiration automatique",
    ]
    return "\n".join(lines)
