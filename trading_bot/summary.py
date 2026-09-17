"""Résumé quotidien (signaux, résultats, taux de réussite, enseignements)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from .config import DISCLAIMER, Config
from .learning import analyze, win_rate
from .models import Signal, parse_iso


def _fmt_wr(wr: float | None) -> str:
    return "n/a" if wr is None else f"{wr:.0%}"


def _classify(good: list[str], bad: list[str], label: str, st: dict[str, Any]) -> None:
    n = st["tp"] + st["sl"]
    if n >= 3 and st["win_rate"] is not None:
        if st["win_rate"] >= 0.55:
            good.append(f"{label} ({st['win_rate']:.0%} sur {n})")
        elif st["win_rate"] <= 0.40:
            bad.append(f"{label} ({st['win_rate']:.0%} sur {n})")


def daily_summary(all_signals: list[Signal], cfg: Config, day: date | None = None,
                  adjustments: dict[str, Any] | None = None) -> str:
    tz = ZoneInfo(cfg.timezone)
    day = day or datetime.now(tz).date()
    todays = [s for s in all_signals if parse_iso(s.created_at).astimezone(tz).date() == day]
    closed_today = [s for s in todays if s.status != "open"]
    still_open = [s for s in todays if s.status == "open"]
    tp = sum(1 for s in closed_today if s.status == "tp")
    sl = sum(1 for s in closed_today if s.status == "sl")
    exp = sum(1 for s in closed_today if s.status == "expired")
    cumulative = [s for s in all_signals if s.status != "open"]
    pnl_day = sum(s.pnl_pct or 0 for s in closed_today)
    pnl_cum = sum(s.pnl_pct or 0 for s in cumulative)

    lines = [
        f"📊 RÉSUMÉ QUOTIDIEN — {day:%d/%m/%Y} ({cfg.timezone})",
        "",
        f"Signaux proposés : {len(todays)}",
        f"Gagnants (TP) : {tp} | Perdants (SL) : {sl} | Expirés sans issue : {exp} | Encore ouverts : {len(still_open)}",
        f"Taux de réussite du jour : {_fmt_wr(win_rate(closed_today))} (TP / (TP+SL))",
        f"Taux de réussite cumulé : {_fmt_wr(win_rate(cumulative))} sur {len(cumulative)} trades clôturés",
        f"P&L théorique (somme des % par trade) : jour {pnl_day:+.2f} % | cumulé {pnl_cum:+.2f} %",
        "",
    ]
    if todays:
        lines.append("Détail du jour :")
        for s in sorted(todays, key=lambda x: x.created_at):
            t = parse_iso(s.created_at).astimezone(tz)
            res = {"tp": "✅ TP", "sl": "❌ SL", "expired": "⏱️ expiré", "open": "⏳ ouvert"}[s.status]
            pnl = f"{s.pnl_pct:+.2f} %" if s.pnl_pct is not None else "-"
            dur = f"{s.duration_minutes} min" if s.duration_minutes is not None else "-"
            lines.append(f"  {t:%H:%M} {s.asset_label} {s.direction} @ {s.entry} → {res} ({pnl}, {dur}, conf. {s.confidence})")
        lines.append("")

    rep = analyze(all_signals)
    good: list[str] = []
    bad: list[str] = []
    for crit, st in rep["by_criterion"].items():
        _classify(good, bad, f"critère {crit}", st)
    for asset, st in rep["by_asset"].items():
        _classify(good, bad, f"actif {asset}", st)
    for conf, st in rep["by_confidence"].items():
        _classify(good, bad, f"confiance {conf}", st)
    lines.append("Ce qui a bien fonctionné : " + (", ".join(good) if good else "pas encore assez de données"))
    lines.append("Ce qui a mal fonctionné : " + (", ".join(bad) if bad else "rien de significatif"))
    lines.append("")
    if adjustments and adjustments.get("notes"):
        lines.append("Ajustements prévus pour demain :")
        lines.extend(f"  • {n}" for n in adjustments["notes"][-5:])
        if adjustments.get("avoid_hours_utc"):
            lines.append(f"  • tranches horaires évitées (UTC) : {adjustments['avoid_hours_utc']}")
    else:
        lines.append("Ajustements prévus pour demain : aucun (critères actuels conservés).")
    lines += ["", DISCLAIMER]
    return "\n".join(lines)
