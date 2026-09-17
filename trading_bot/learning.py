"""Analyse de l'historique : quels setups gagnent, et ajustement des poids de sélection."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from .analysis import DEFAULT_WEIGHTS
from .config import Config
from .models import Signal, parse_iso


def _wins_losses(sigs: list[Signal]) -> tuple[int, int, int]:
    tp = sum(1 for s in sigs if s.status == "tp")
    sl = sum(1 for s in sigs if s.status == "sl")
    exp = sum(1 for s in sigs if s.status == "expired")
    return tp, sl, exp


def win_rate(sigs: list[Signal]) -> float | None:
    """Taux de réussite = TP / (TP + SL). Les expirés sont comptés à part (P&L réel conservé)."""
    tp, sl, _ = _wins_losses(sigs)
    if tp + sl == 0:
        return None
    return tp / (tp + sl)


def stats_by(sigs: list[Signal], key_fn) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[Signal]] = defaultdict(list)
    for s in sigs:
        for k in key_fn(s):
            groups[k].append(s)
    out = {}
    for k, group in sorted(groups.items()):
        tp, sl, exp = _wins_losses(group)
        out[k] = {"n": len(group), "tp": tp, "sl": sl, "expired": exp,
                  "win_rate": win_rate(group),
                  "avg_pnl_pct": round(sum(s.pnl_pct or 0 for s in group) / len(group), 4)}
    return out


def neutral_win_rate(sigs: list[Signal]) -> float | None:
    """Taux de réussite attendu sans avantage (marche aléatoire) : moyenne de SL / (TP + SL)."""
    vals = []
    for s in sigs:
        tp_d, sl_d = abs(s.take_profit - s.entry), abs(s.entry - s.stop_loss)
        if tp_d + sl_d > 0:
            vals.append(sl_d / (tp_d + sl_d))
    return round(sum(vals) / len(vals), 4) if vals else None


def analyze(history: list[Signal]) -> dict[str, Any]:
    closed = [s for s in history if s.status != "open"]
    wr = win_rate(closed)
    neutral = neutral_win_rate(closed)
    return {
        "total": len(closed),
        "overall": stats_by(closed, lambda s: ["tous"]).get("tous"),
        "neutral_win_rate": neutral,
        "edge": round(wr - neutral, 4) if (wr is not None and neutral is not None) else None,
        "pnl_gross_pct": round(sum(s.pnl_gross_pct or 0 for s in closed), 4),
        "pnl_net_pct": round(sum(s.pnl_pct or 0 for s in closed), 4),
        "by_asset": stats_by(closed, lambda s: [s.asset]),
        "by_direction": stats_by(closed, lambda s: [s.direction]),
        "by_confidence": stats_by(closed, lambda s: [s.confidence]),
        "by_criterion": stats_by(closed, lambda s: s.criteria),
        "by_news": stats_by(closed, lambda s: ["actualité calme" if "calme" in (s.news_context or "").lower() else "actualité chargée"]),
        "by_hour_utc": stats_by(closed, lambda s: [f"{parse_iso(s.created_at).hour:02d}h"]),
    }


def learn(history: list[Signal], cfg: Config, current: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ajuste les poids des critères en fonction de leur taux de réussite historique.

    - critère avec win rate < seuil faible (sur >= N trades) → poids réduit (min 0.25)
    - critère avec win rate > seuil fort → poids augmenté (max 1.5)
    - sinon retour progressif vers le poids par défaut
    """
    current = current or {"weights": {}, "notes": []}
    weights = {k: float(current.get("weights", {}).get(k, v)) for k, v in DEFAULT_WEIGHTS.items()}
    report = analyze(history)
    notes: list[str] = []
    for crit, st in report["by_criterion"].items():
        if crit not in weights:
            continue
        n = st["tp"] + st["sl"]
        wr = st["win_rate"]
        if n < cfg.learning_min_trades or wr is None:
            continue
        old = weights[crit]
        if wr < cfg.learning_weak_win_rate:
            weights[crit] = max(0.25, round(old * 0.85, 3))
            notes.append(f"{crit}: win rate {wr:.0%} sur {n} trades → poids {old} → {weights[crit]}")
        elif wr > cfg.learning_strong_win_rate:
            weights[crit] = min(1.5, round(old * 1.10, 3))
            notes.append(f"{crit}: win rate {wr:.0%} sur {n} trades → poids {old} → {weights[crit]}")
        else:
            target = DEFAULT_WEIGHTS[crit]
            weights[crit] = round(old + (target - old) * 0.5, 3)
    # Tranches horaires à éviter : win rate < 30 % sur >= N trades
    avoid_hours = []
    for hour, st in report["by_hour_utc"].items():
        n = st["tp"] + st["sl"]
        if n >= cfg.learning_min_trades and st["win_rate"] is not None and st["win_rate"] < 0.30:
            avoid_hours.append(int(hour[:2]))
            notes.append(f"tranche {hour} UTC : win rate {st['win_rate']:.0%} sur {n} trades → évitée")
    closed = [s for s in history if s.status != "open"]
    by_source = {}
    for s in closed:
        by_source[s.source] = by_source.get(s.source, 0) + 1
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "weights": weights,
        "avoid_hours_utc": sorted(avoid_hours),
        "notes": notes[-20:],
        "sample": report["total"],
        "sample_by_source": by_source,
    }
