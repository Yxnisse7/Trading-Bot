"""Backtest : rejoue la logique de signal sur l'historique 5 min (jusqu'à 60 jours sur Yahoo).

Sans biais de futur : à chaque pas, seules les bougies déjà clôturées sont utilisées
pour l'analyse ; l'issue est déterminée sur les 12 bougies suivantes (1 h), SL prioritaire
si TP et SL sont touchés dans la même bougie. Les règles de la politique (maximum
quotidien, refroidissement, arrêt après pertes) sont appliquées comme en production.
L'actualité n'est pas rejouée (non disponible historiquement) : les résultats sont donc
légèrement optimistes sur ce point.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .analysis import assess
from .config import AssetConfig, Config
from .models import Candle, Signal, parse_iso
from .signals import build_signal
from .tracker import resolve_with_candles, close_signal

log = logging.getLogger(__name__)


def _policy_allows(asset: AssetConfig, sigs: list[Signal], now: datetime, cfg: Config) -> bool:
    tz = ZoneInfo(cfg.timezone)
    today = now.astimezone(tz).date()
    todays = [s for s in sigs if parse_iso(s.created_at).astimezone(tz).date() == today]
    if len(todays) >= cfg.max_signals_per_asset_per_day:
        return False
    if sum(1 for s in todays if s.status == "sl") >= cfg.max_losses_per_asset_per_day:
        return False
    if sigs:
        last = sigs[-1]
        cooldown = cfg.cooldown_after_loss_minutes if last.status == "sl" else cfg.cooldown_minutes
        if now - parse_iso(last.created_at) < timedelta(minutes=cooldown):
            return False
    if asset.session_utc and not (asset.session_utc[0] <= now.hour < asset.session_utc[1]):
        return False
    return True


def run_backtest(asset: AssetConfig, candles: list[Candle], cfg: Config, *, step: int = 3,
                 warmup: int = 300, weights: dict[str, float] | None = None,
                 simulate: bool = True) -> dict[str, Any]:
    """Rejoue l'historique toutes les `step` bougies (3 = 15 min). Renvoie statistiques + trades."""
    horizon = max(1, cfg.signal_lifetime_minutes // 5)
    sigs: list[Signal] = []
    rejected: dict[str, int] = {}
    i = warmup
    while i < len(candles) - horizon:
        window = candles[: i + 1]
        now = datetime.fromtimestamp(candles[i].ts + 300, tz=timezone.utc)  # clôture de la bougie i
        if _policy_allows(asset, sigs, now, cfg):
            a = assess(asset, window, cfg, weights)
            sig, why = build_signal(asset, a, cfg, "backtest (actualité non rejouée)", now, simulate=simulate)
            if sig is None:
                key = why[-1].split(" (")[0] if why else "inconnu"
                rejected[key] = rejected.get(key, 0) + 1
            else:
                # entrée = clôture de la bougie i ; issue sur les bougies i+1 .. i+horizon
                future = candles[i + 1: i + 1 + horizon]
                outcome = resolve_with_candles(sig, future)
                if outcome is None:
                    last = future[-1]
                    close_signal(sig, "expired", last.close, datetime.fromtimestamp(last.ts + 300, tz=timezone.utc))
                else:
                    status, px, when = outcome
                    close_signal(sig, status, px, when)
                sigs.append(sig)
        i += step
    return summarize(asset, candles, sigs, rejected)


def summarize(asset: AssetConfig, candles: list[Candle], sigs: list[Signal], rejected: dict[str, int]) -> dict[str, Any]:
    tp = sum(1 for s in sigs if s.status == "tp")
    sl = sum(1 for s in sigs if s.status == "sl")
    exp = sum(1 for s in sigs if s.status == "expired")
    pnl = sum(s.pnl_pct or 0 for s in sigs)
    start = datetime.fromtimestamp(candles[0].ts, tz=timezone.utc) if candles else None
    end = datetime.fromtimestamp(candles[-1].ts, tz=timezone.utc) if candles else None
    gains = [s.pnl_pct for s in sigs if (s.pnl_pct or 0) > 0]
    losses = [s.pnl_pct for s in sigs if (s.pnl_pct or 0) < 0]
    profit_factor = (sum(gains) / abs(sum(losses))) if losses and gains else None
    # série de pertes maximale
    worst_streak = streak = 0
    for s in sigs:
        streak = streak + 1 if s.status == "sl" else 0
        worst_streak = max(worst_streak, streak)
    return {
        "asset": asset.key, "asset_label": asset.label,
        "period": f"{start:%d/%m/%Y} → {end:%d/%m/%Y}" if start and end else "-",
        "n": len(sigs), "tp": tp, "sl": sl, "expired": exp,
        "win_rate": (tp / (tp + sl)) if tp + sl else None,
        "pnl_pct": round(pnl, 4),
        "expectancy_pct": round(pnl / len(sigs), 4) if sigs else 0.0,
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
        "max_losing_streak": worst_streak,
        "rejected": dict(sorted(rejected.items(), key=lambda kv: -kv[1])),
        "trades": [s.to_dict() for s in sigs],
    }


def format_backtest(b: dict[str, Any]) -> str:
    wr = "n/a" if b["win_rate"] is None else f"{b['win_rate']:.0%}"
    pf = "n/a" if b["profit_factor"] is None else str(b["profit_factor"])
    lines = [
        f"🧪 BACKTEST — {b['asset_label']} ({b['period']})",
        f"Signaux : {b['n']} | TP : {b['tp']} | SL : {b['sl']} | Expirés : {b['expired']}",
        f"Taux de réussite : {wr} | P&L cumulé : {b['pnl_pct']:+.2f} % | Espérance / trade : {b['expectancy_pct']:+.3f} %",
        f"Profit factor : {pf} | Pire série de stops : {b['max_losing_streak']}",
    ]
    if b["rejected"]:
        lines.append("Principaux motifs de refus :")
        for k, v in list(b["rejected"].items())[:6]:
            lines.append(f"  • {k} : {v}")
    return "\n".join(lines)
