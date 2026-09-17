"""Suivi automatique des signaux ouverts : TP touché, SL touché ou expiration après 1 h."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .models import Candle, Signal, iso, parse_iso, utcnow

log = logging.getLogger(__name__)


def resolve_with_candles(sig: Signal, candles: list[Candle]) -> tuple[str, float, datetime] | None:
    """Parcourt les bougies postérieures au signal ; renvoie (statut, prix, heure) si résolu.

    Convention prudente : si TP et SL sont touchés dans la même bougie, on compte le SL.
    """
    start = int(parse_iso(sig.created_at).timestamp())
    expiry = parse_iso(sig.expires_at)
    for c in candles:
        if c.ts < start:
            continue
        cdt = datetime.fromtimestamp(c.ts, tz=timezone.utc)
        if cdt > expiry:
            break
        if sig.direction == "long":
            hit_sl = c.low <= sig.stop_loss
            hit_tp = c.high >= sig.take_profit
        else:
            hit_sl = c.high >= sig.stop_loss
            hit_tp = c.low <= sig.take_profit
        if hit_sl:
            return "sl", sig.stop_loss, cdt
        if hit_tp:
            return "tp", sig.take_profit, cdt
    return None


def resolve_with_price(sig: Signal, price: float, now: datetime) -> tuple[str, float, datetime] | None:
    if sig.direction == "long":
        if price <= sig.stop_loss:
            return "sl", price, now
        if price >= sig.take_profit:
            return "tp", price, now
    else:
        if price >= sig.stop_loss:
            return "sl", price, now
        if price <= sig.take_profit:
            return "tp", price, now
    return None


def close_signal(sig: Signal, status: str, price: float, when: datetime) -> Signal:
    sig.status = status
    sig.closed_at = iso(when)
    sig.close_price = price
    sign = 1.0 if sig.direction == "long" else -1.0
    sig.pnl_pct = round(sign * (price - sig.entry) / sig.entry * 100.0, 4)
    sig.duration_minutes = max(0, int((when - parse_iso(sig.created_at)).total_seconds() // 60))
    return sig


def update_signal(sig: Signal, candles: list[Candle] | None, price: float | None,
                  now: datetime | None = None) -> Signal | None:
    """Renvoie le signal clôturé s'il vient d'être résolu, sinon None."""
    now = now or utcnow()
    outcome = None
    if candles:
        outcome = resolve_with_candles(sig, candles)
    if outcome is None and price is not None:
        outcome = resolve_with_price(sig, price, now)
    if outcome is not None:
        status, px, when = outcome
        return close_signal(sig, status, px, when)
    if now >= parse_iso(sig.expires_at):
        if price is None:
            if candles:
                price = candles[-1].close
            else:
                log.warning("expiration de %s sans prix disponible : clôture à l'entrée", sig.id)
                price = sig.entry
        return close_signal(sig, "expired", price, now)
    return None


def format_outcome(sig: Signal, tz: str = "Europe/Paris") -> str:
    closed = parse_iso(sig.closed_at).astimezone(ZoneInfo(tz)) if sig.closed_at else None
    icon = {"tp": "✅ TP TOUCHÉ", "sl": "❌ SL TOUCHÉ", "expired": "⏱️ EXPIRÉ (sans issue)"}[sig.status]
    lines = [f"{icon} — {sig.asset_label} {sig.direction.upper()} (id {sig.id})"]
    if closed:
        lines.append(f"Heure : {closed:%d/%m/%Y %H:%M:%S} ({tz})")
    lines.append(f"Entrée {sig.entry} → clôture {sig.close_price} | P&L {sig.pnl_pct:+.3f} %")
    lines.append(f"Durée réelle : {sig.duration_minutes} min")
    return "\n".join(lines)
