"""Construction d'un signal exploitable (entrée, TP, SL) à partir d'une évaluation."""
from __future__ import annotations

import uuid
from datetime import timedelta

from .analysis import Assessment, confidence_label
from .config import AssetConfig, Config
from .models import Signal, iso, utcnow


def round_to_tick(value: float, tick: float) -> float:
    if tick <= 0:
        return value
    return round(round(value / tick) * tick, 6)


def build_signal(asset: AssetConfig, a: Assessment, cfg: Config, news_context: str,
                 now=None) -> tuple[Signal | None, list[str]]:
    """Renvoie (signal, raisons_de_refus). Un signal n'est produit que si tout converge."""
    reasons: list[str] = list(a.reasons_rejected)
    now = now or utcnow()

    if a.direction is None:
        reasons.append("aucune direction dominante")
        return None, reasons

    conf = confidence_label(a.score, a.n_criteria, cfg)
    if conf is None:
        reasons.append(f"convergence insuffisante (score {a.score}, {a.n_criteria} critère(s))")
        return None, reasons
    if cfg.min_confidence == "fort" and conf != "fort":
        reasons.append("confiance moyenne alors que 'fort' est exigé")
        return None, reasons

    hr = a.hourly_range
    if not hr or hr <= 0:
        reasons.append("range horaire indisponible")
        return None, reasons

    hr_pct = hr / a.price * 100.0
    if hr_pct < asset.min_hourly_range_pct:
        reasons.append(f"volatilité horaire trop faible ({hr_pct:.3f} %) : TP inatteignable en 1h")
        return None, reasons
    if hr_pct > asset.max_hourly_range_pct:
        reasons.append(f"volatilité horaire anormale ({hr_pct:.2f} %) : marché instable")
        return None, reasons

    # ATR de sécurité : si l'ATR 5m explose par rapport au range horaire moyen, on s'abstient
    if a.atr and a.atr * 12 > 2.5 * hr:
        reasons.append("ATR 5m récent >> range horaire moyen : volatilité inexpliquée")
        return None, reasons

    tp_dist = cfg.tp_range_fraction * hr
    sl_dist = cfg.sl_range_fraction * hr

    # On borne le TP entre un minimum (bruit) et un maximum (réaliste sous 1h)
    tp_dist = max(cfg.min_tp_range_fraction * hr, min(cfg.max_tp_range_fraction * hr, tp_dist))

    # Si un niveau clé se trouve juste avant la cible, on la ramène légèrement devant lui
    if a.direction == "long" and a.resistance and a.resistance - a.price < tp_dist:
        tp_dist = (a.resistance - a.price) * 0.9
    if a.direction == "short" and a.support and a.price - a.support < tp_dist:
        tp_dist = (a.price - a.support) * 0.9
    if tp_dist < cfg.min_tp_range_fraction * hr:
        reasons.append("cible trop proche après ajustement sur le niveau clé")
        return None, reasons

    rr = tp_dist / sl_dist if sl_dist > 0 else 0.0
    if rr < cfg.min_risk_reward:
        reasons.append(f"ratio risque/rendement insuffisant ({rr:.2f})")
        return None, reasons

    entry = round_to_tick(a.price, asset.tick_size)
    if a.direction == "long":
        tp = round_to_tick(entry + tp_dist, asset.tick_size)
        sl = round_to_tick(entry - sl_dist, asset.tick_size)
    else:
        tp = round_to_tick(entry - tp_dist, asset.tick_size)
        sl = round_to_tick(entry + sl_dist, asset.tick_size)
    if tp == entry or sl == entry:
        reasons.append("niveaux TP/SL confondus avec l'entrée après arrondi")
        return None, reasons

    rr = abs(tp - entry) / abs(entry - sl)
    tech = ", ".join(_criterion_label(c) for c in a.criteria)
    rationale = (f"{'Achat' if a.direction == 'long' else 'Vente'} : {tech}. "
                 f"Range horaire moyen ≈ {hr:.{asset.price_decimals}f} "
                 f"({hr_pct:.2f} %), TP = {tp_dist / hr * 100:.0f} % du range, SL = {sl_dist / hr * 100:.0f} %.")

    sig = Signal(
        id=uuid.uuid4().hex[:10],
        asset=asset.key, asset_label=asset.label, direction=a.direction,
        entry=entry, take_profit=tp, stop_loss=sl, risk_reward=round(rr, 2),
        confidence=conf, score=a.score, criteria=list(a.criteria),
        rationale=rationale, news_context=news_context,
        created_at=iso(now), expires_at=iso(now + timedelta(minutes=cfg.signal_lifetime_minutes)),
        hourly_range=round(hr, 6),
        meta={"details": a.details, "support": a.support, "resistance": a.resistance,
              "atr_5m": a.atr, "hourly_range_pct": round(hr_pct, 4)},
    )
    return sig, reasons


_LABELS = {
    "trend_5m": "tendance 5m", "trend_15m": "tendance 15m", "trend_1h": "tendance 1h",
    "rsi": "RSI en momentum", "macd": "MACD en expansion", "level": "niveau clé favorable",
    "volume": "volume anormal",
}


def _criterion_label(c: str) -> str:
    return _LABELS.get(c, c)


def format_signal(sig: Signal, tz: str = "Europe/Paris") -> str:
    from zoneinfo import ZoneInfo

    from .models import parse_iso

    created = parse_iso(sig.created_at).astimezone(ZoneInfo(tz))
    arrow = "🟢 LONG" if sig.direction == "long" else "🔴 SHORT"
    lines = [
        f"📡 SIGNAL {arrow} — {sig.asset_label}",
        f"Heure : {created:%d/%m/%Y %H:%M} ({tz}) — id {sig.id}",
        f"Entrée visée : {sig.entry}",
        f"Take Profit  : {sig.take_profit}",
        f"Stop Loss    : {sig.stop_loss}",
        f"Risque/Rendement : {sig.risk_reward}",
        f"Confiance : {sig.confidence.upper()} (score {sig.score})",
        f"Justification : {sig.rationale}",
        f"Actualité : {sig.news_context}",
        f"Validité : ~{60} min (expire {parse_iso(sig.expires_at).astimezone(ZoneInfo(tz)):%H:%M})",
    ]
    return "\n".join(lines)
