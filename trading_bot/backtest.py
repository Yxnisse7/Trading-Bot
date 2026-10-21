"""Backtest : rejoue la logique de signal sur l'historique 5 min (jusqu'à 60 jours sur Yahoo).

Sans biais de futur : à chaque pas, seules les bougies déjà clôturées sont utilisées
pour l'analyse ; l'issue est déterminée sur les bougies suivantes jusqu'à l'expiration du signal
(1 h, 3 h, ou 24 h sur le Nasdaq avec EXIT_OVERRIDE), SL prioritaire si TP et SL sont touchés dans
la même bougie. Les règles de la politique (maximum quotidien, un seul signal ouvert, refroidissement,
arrêt après pertes, pas de retour dans le sens d'un stop) sont appliquées comme en production
(engine._policy_block) : un signal n'a de statut qu'une fois clos (essai 42).
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
from .context import walk_excursion
from .models import Candle, Signal, parse_iso
from .signals import build_signal
from .tracker import resolve_with_candles, close_signal

log = logging.getLogger(__name__)


KEEP = 3 * 86400        # signaux plus vieux que 3 jours : sans effet sur la politique


def _policy_allows(asset: AssetConfig, past: list[tuple[int, int, str, str]], now: datetime, cfg: Config,
                   base_minutes: int = 5, direction: str | None = None) -> bool:
    """`past` : (émis, clos, statut, sens) des signaux déjà émis, en secondes ; seul ce qui est clos à `now` est connu."""
    t = int(now.timestamp())
    tz = ZoneInfo(cfg.timezone)
    today = now.astimezone(tz).date()
    recent = [p for p in past[-200:] if p[0] >= t - KEEP]
    if any(p[1] > t for p in recent):
        return False                                    # un signal est encore ouvert
    todays = [p for p in recent if datetime.fromtimestamp(p[0], tz).date() == today]
    cap = cfg.max_signals_per_asset_per_day if base_minutes == 5 else cfg.max_long_signals_per_asset_per_day
    if len(todays) >= cap:
        return False
    if sum(1 for p in todays if p[2] == "sl") >= cfg.max_losses_per_asset_per_day:
        return False
    if recent and t - recent[-1][0] < cfg.cooldown_minutes * 60:
        return False
    stops = [p for p in recent if p[2] == "sl"]
    if stops and t - max(p[1] for p in stops) < cfg.cooldown_after_loss_minutes * 60:
        return False
    if direction and cfg.same_direction_after_loss_minutes > 0 and any(
            p[3] == direction and t - p[1] < cfg.same_direction_after_loss_minutes * 60 for p in stops):
        return False
    if asset.session_utc and not (asset.session_utc[0] <= now.hour < asset.session_utc[1]):
        return False
    return True


def run_backtest(asset: AssetConfig, candles: list[Candle], cfg: Config, *, step: int = 3,
                 warmup: int = 300, weights: dict[str, float] | None = None,
                 simulate: bool = True, lookback: int = 1440, base_minutes: int = 5) -> dict[str, Any]:
    """Rejoue l'historique toutes les `step` bougies 5 min (3 = 15 min). Renvoie statistiques + trades.

    `lookback` : nombre de bougies vues par l'analyse à chaque pas (1 440 = 5 jours, comme en production).
    `base_minutes` : 5 (horizon ~1 h) ou 15 (horizon ~3 h, issue sur 36 bougies 5 min).
    """
    horizon = max(1, 12 * base_minutes // 5)
    sigs: list[Signal] = []
    past: list[tuple[int, int, str, str]] = []
    rejected: dict[str, int] = {}
    i = warmup
    while i < len(candles) - horizon:
        window = candles[max(0, i + 1 - lookback): i + 1]
        now = datetime.fromtimestamp(candles[i].ts + 300, tz=timezone.utc)  # clôture de la bougie i
        if _policy_allows(asset, past, now, cfg, base_minutes):
            a = assess(asset, window, cfg, weights, base_minutes=base_minutes)
            if cfg.long_only and a.direction == "short":
                a.reasons_rejected.append("achat seulement : tendance baissière ignorée")
                a.direction = None
            sig, why = build_signal(asset, a, cfg, "backtest (actualité non rejouée)", now, simulate=simulate)
            if sig is not None and not _policy_allows(asset, past, now, cfg, base_minutes, sig.direction):
                sig, why = None, ["stop récent dans ce sens"]
            if sig is None:
                key = why[-1].split(" (")[0] if why else "inconnu"
                rejected[key] = rejected.get(key, 0) + 1
            else:
                # entrée = clôture de la bougie i ; issue sur les bougies i+1 .. expiration du signal
                exp = int(parse_iso(sig.expires_at).timestamp())
                j = i + 1
                while j < len(candles) and candles[j].ts < exp:
                    j += 1
                future = candles[i + 1: max(j, i + 2)]
                outcome = resolve_with_candles(sig, future)
                walk_excursion(sig, future, outcome[2] if outcome else None)
                if outcome is None:
                    last = future[-1]
                    close_signal(sig, "expired", last.close, datetime.fromtimestamp(last.ts + 300, tz=timezone.utc), asset.cost_pct)
                else:
                    status, px, when = outcome
                    close_signal(sig, status, px, when, asset.cost_pct)
                sigs.append(sig)
                past.append((int(now.timestamp()), int(parse_iso(sig.closed_at).timestamp()), sig.status, sig.direction))
        i += step
    res = summarize(asset, candles, sigs, rejected)
    res["horizon"] = "1h" if base_minutes == 5 else f"{12 * base_minutes // 60}h"
    return res


def neutral_win_rate(sigs: list[Signal]) -> float | None:
    """Taux de réussite attendu sans aucun avantage (marche aléatoire) : SL / (TP + SL) en moyenne."""
    vals = []
    for s in sigs:
        tp_d, sl_d = abs(s.take_profit - s.entry), abs(s.entry - s.stop_loss)
        if tp_d + sl_d > 0:
            vals.append(sl_d / (tp_d + sl_d))
    return round(sum(vals) / len(vals), 4) if vals else None


def summarize(asset: AssetConfig, candles: list[Candle], sigs: list[Signal], rejected: dict[str, int]) -> dict[str, Any]:
    tp = sum(1 for s in sigs if s.status == "tp")
    sl = sum(1 for s in sigs if s.status == "sl")
    exp = sum(1 for s in sigs if s.status == "expired")
    pnl = sum(s.pnl_pct or 0 for s in sigs)
    pnl_gross = sum(s.pnl_gross_pct or 0 for s in sigs)
    neutral = neutral_win_rate(sigs)
    win_rate = (tp / (tp + sl)) if tp + sl else None
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
        "win_rate": win_rate,
        "neutral_win_rate": neutral,
        "edge": round(win_rate - neutral, 4) if (win_rate is not None and neutral is not None) else None,
        "pnl_pct": round(pnl, 4),
        "pnl_gross_pct": round(pnl_gross, 4),
        "expectancy_pct": round(pnl / len(sigs), 4) if sigs else 0.0,
        "profit_factor": round(profit_factor, 2) if profit_factor is not None else None,
        "max_losing_streak": worst_streak,
        "rejected": dict(sorted(rejected.items(), key=lambda kv: -kv[1])),
        "trades": [s.to_dict() for s in sigs],
    }


def format_backtest(b: dict[str, Any]) -> str:
    wr = "n/a" if b["win_rate"] is None else f"{b['win_rate']:.0%}"
    pf = "n/a" if b["profit_factor"] is None else str(b["profit_factor"])
    neutral = "n/a" if b.get("neutral_win_rate") is None else f"{b['neutral_win_rate']:.0%}"
    edge = "n/a" if b.get("edge") is None else f"{b['edge']:+.0%}"
    lines = [
        f"🧪 BACKTEST — {b['asset_label']} — horizon {b.get('horizon', '1h')} ({b['period']})",
        f"Signaux : {b['n']} | TP : {b['tp']} | SL : {b['sl']} | Expirés : {b['expired']}",
        f"Taux de réussite : {wr} (hasard attendu {neutral}, avantage {edge})",
        f"P&L net cumulé : {b['pnl_pct']:+.2f} % (brut {b.get('pnl_gross_pct', b['pnl_pct']):+.2f} %) | Espérance nette / trade : {b['expectancy_pct']:+.3f} %",
        f"Profit factor : {pf} | Pire série de stops : {b['max_losing_streak']}",
    ]
    if b["rejected"]:
        lines.append("Principaux motifs de refus :")
        for k, v in list(b["rejected"].items())[:6]:
            lines.append(f"  • {k} : {v}")
    return "\n".join(lines)
