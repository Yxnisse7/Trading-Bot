"""Rapport Markdown (data/REPORT.md) : état courant, statistiques et enseignements."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .config import DISCLAIMER, Config
from .learning import analyze
from .models import Signal, parse_iso


def _pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.0%}"


def _table(title: str, rows: dict[str, dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    out = [f"### {title}", "", "| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for k, st in rows.items():
        out.append(f"| {k} | {st['n']} | {st['tp']} | {st['sl']} | {st['expired']} | {_pct(st['win_rate'])} | {st['avg_pnl_pct']:+.3f} % |")
    out.append("")
    return out


def build_report(all_signals: list[Signal], cfg: Config, adjustments: dict[str, Any] | None = None,
                 backtests: dict[str, dict[str, Any]] | None = None, now: datetime | None = None) -> str:
    tz = ZoneInfo(cfg.timezone)
    now = now or datetime.now(tz)
    open_sigs = [s for s in all_signals if s.status == "open"]
    closed = [s for s in all_signals if s.status != "open"]
    rep = analyze(closed)
    overall = rep["overall"]
    pnl_cum = sum(s.pnl_pct or 0 for s in closed)
    edge_txt = "n/a" if rep["edge"] is None else f"{rep['edge']:+.0%}"

    lines = [
        "# Trading-Bot — rapport",
        "",
        f"_Mis à jour le {now.astimezone(tz):%d/%m/%Y à %H:%M} ({cfg.timezone})._",
        "",
        "## Vue d'ensemble",
        "",
        f"- Trades clôturés : **{len(closed)}**",
        f"- Taux de réussite cumulé (TP / (TP+SL)) : **{_pct(overall['win_rate']) if overall else 'n/a'}**"
        f" — hasard attendu {_pct(rep['neutral_win_rate'])}, avantage **{edge_txt}**",
        f"- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **{pnl_cum:+.2f} %** (brut {rep['pnl_gross_pct']:+.2f} %)",
        f"- Signaux ouverts : **{len(open_sigs)}**",
        "",
    ]
    if open_sigs:
        lines += ["## Signaux ouverts", "", "| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Expire |", "|---|---|---|---:|---:|---:|---|---|"]
        for s in open_sigs:
            c = parse_iso(s.created_at).astimezone(tz)
            e = parse_iso(s.expires_at).astimezone(tz)
            lines.append(f"| {c:%d/%m %H:%M} | {s.asset_label} | {s.direction} | {s.entry} | {s.take_profit} | {s.stop_loss} | {s.confidence} | {e:%H:%M} |")
        lines.append("")
    if closed:
        lines += ["## Statistiques", ""]
        lines += _table("Par actif", rep["by_asset"])
        lines += _table("Par sens", rep["by_direction"])
        lines += _table("Par confiance", rep["by_confidence"])
        lines += _table("Par critère technique", rep["by_criterion"])
        lines += _table("Par contexte d'actualité", rep["by_news"])
        lines += _table("Par heure d'émission (UTC)", rep["by_hour_utc"])
        lines += ["## Derniers trades", "", "| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |", "|---|---|---|---:|---:|---|---:|---:|"]
        for s in sorted(closed, key=lambda x: x.created_at, reverse=True)[:30]:
            c = parse_iso(s.created_at).astimezone(tz)
            res = {"tp": "✅ TP", "sl": "❌ SL", "expired": "⏱️ expiré"}[s.status]
            lines.append(f"| {c:%d/%m %H:%M} | {s.asset_label} | {s.direction} | {s.entry} | {s.close_price} | {res} | {s.pnl_pct:+.2f} % | {s.duration_minutes} min |")
        lines.append("")
    if adjustments and adjustments.get("weights"):
        lines += ["## Apprentissage", "", "| Critère | Poids actuel |", "|---|---:|"]
        for k, v in adjustments["weights"].items():
            lines.append(f"| {k} | {v} |")
        if adjustments.get("avoid_hours_utc"):
            lines.append(f"\nTranches horaires évitées (UTC) : {adjustments['avoid_hours_utc']}")
        if adjustments.get("notes"):
            lines += ["", "Dernières notes :", ""] + [f"- {n}" for n in adjustments["notes"][-8:]]
        lines.append("")
    if backtests:
        lines += ["## Backtests (données historiques 5 min)", "", "| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for k, b in backtests.items():
            edge = "n/a" if b.get("edge") is None else f"{b['edge']:+.0%}"
            lines.append(f"| {b.get('asset_label', k)} | {b.get('period', '-')} | {b['n']} | {b['tp']} | {b['sl']} | {b['expired']} | {_pct(b['win_rate'])} | {_pct(b.get('neutral_win_rate'))} | {edge} | {b['pnl_pct']:+.2f} % | {b['expectancy_pct']:+.3f} % |")
        lines.append("")
    lines += ["---", "", DISCLAIMER, ""]
    return "\n".join(lines)
