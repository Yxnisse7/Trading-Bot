"""Rapport Markdown (data/REPORT.md) : état courant, statistiques et enseignements."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .config import DISCLAIMER, Config
from .learning import analyze, neutral_win_rate, stats_by
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


SOURCE_LABELS = {"bot": "signaux du bot", "manual": "demandes manuelles", "shadow": "signaux fantômes", "backtest": "backtest"}


def build_report(all_signals: list[Signal], cfg: Config, adjustments: dict[str, Any] | None = None,
                 backtests: dict[str, dict[str, Any]] | None = None, now: datetime | None = None) -> str:
    tz = ZoneInfo(cfg.timezone)
    now = now or datetime.now(tz)
    visible = [s for s in all_signals if s.source != "shadow"]
    shadow_closed = [s for s in all_signals if s.source == "shadow" and s.status != "open"]
    shadow_open = [s for s in all_signals if s.source == "shadow" and s.status == "open"]
    open_sigs = [s for s in visible if s.status == "open"]
    closed = [s for s in visible if s.status != "open"]
    rep = analyze(closed)
    rep_shadow = analyze(shadow_closed)
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
        f"- Signaux fantômes (suivis en silence pour l'apprentissage) : **{len(shadow_closed)}** clôturés, "
        f"{len(shadow_open)} ouverts, taux de réussite {_pct(rep_shadow['overall']['win_rate']) if rep_shadow['overall'] else 'n/a'}"
        f" (hasard attendu {_pct(rep_shadow['neutral_win_rate'])})",
        "",
    ]
    if open_sigs:
        lines += ["## Signaux ouverts", "", "| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |", "|---|---|---|---:|---:|---:|---|---|---|"]
        for s in open_sigs:
            c = parse_iso(s.created_at).astimezone(tz)
            e = parse_iso(s.expires_at).astimezone(tz)
            lines.append(f"| {c:%d/%m %H:%M} | {s.asset_label} | {s.direction} | {s.entry} | {s.take_profit} | {s.stop_loss} | {s.confidence} | {SOURCE_LABELS.get(s.source, s.source)} | {e:%H:%M} |")
        lines.append("")
    if closed:
        lines += ["## Statistiques", ""]
        lines += _table("Par actif", rep["by_asset"])
        lines += _table("Par sens", rep["by_direction"])
        lines += _table("Par confiance", rep["by_confidence"])
        lines += _table("Par critère technique", rep["by_criterion"])
        lines += _table("Par contexte d'actualité", rep["by_news"])
        lines += _table("Par heure d'émission (UTC)", rep["by_hour_utc"])
        lines += _table("Par source", stats_by(closed, lambda s: [SOURCE_LABELS.get(s.source, s.source)]))
    if shadow_closed:
        lines += ["## Signaux fantômes (apprentissage)", "",
                  "Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.", ""]
        lines += _table("Fantômes par critère", rep_shadow["by_criterion"])
        lines += _table("Fantômes par actif", rep_shadow["by_asset"])
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


# ---------------------------------------------------------------------------
# Données de l'interface (data/dashboard.json)
# ---------------------------------------------------------------------------

CRITERION_LABELS = {
    "trend_5m": "Tendance 5 min", "trend_15m": "Tendance 15 min", "trend_1h": "Tendance 1 h",
    "adx": "Force de tendance (ADX)", "vwap": "VWAP", "rsi": "RSI", "macd": "MACD",
    "level": "Niveau clé", "volume": "Volume anormal",
}


def _sig_row(s: Signal, tz: ZoneInfo) -> dict[str, Any]:
    c = parse_iso(s.created_at).astimezone(tz)
    return {
        "id": s.id, "asset": s.asset, "asset_label": s.asset_label, "direction": s.direction,
        "entry": s.entry, "take_profit": s.take_profit, "stop_loss": s.stop_loss, "risk_reward": s.risk_reward,
        "confidence": s.confidence, "score": s.score, "criteria": s.criteria, "source": s.source,
        "status": s.status, "pnl_pct": s.pnl_pct, "pnl_gross_pct": s.pnl_gross_pct,
        "duration_minutes": s.duration_minutes, "close_price": s.close_price,
        "created_at": s.created_at, "created_local": f"{c:%d/%m %H:%M}",
        "expires_at": s.expires_at, "rationale": s.rationale, "news_context": s.news_context,
    }


def _stats(sigs: list[Signal]) -> dict[str, Any]:
    tp = sum(1 for s in sigs if s.status == "tp")
    sl = sum(1 for s in sigs if s.status == "sl")
    exp = sum(1 for s in sigs if s.status == "expired")
    n = len(sigs)
    wr = (tp / (tp + sl)) if tp + sl else None
    neutral = neutral_win_rate(sigs)
    return {"n": n, "tp": tp, "sl": sl, "expired": exp, "win_rate": wr, "neutral_win_rate": neutral,
            "edge": (round(wr - neutral, 4) if (wr is not None and neutral is not None) else None),
            "pnl_pct": round(sum(s.pnl_pct or 0 for s in sigs), 4),
            "avg_pnl_pct": round(sum(s.pnl_pct or 0 for s in sigs) / n, 4) if n else 0.0}


def build_dashboard(all_signals: list[Signal], cfg: Config, adjustments: dict[str, Any] | None,
                    backtests: dict[str, Any] | None, state: dict[str, Any] | None,
                    now: datetime | None = None) -> dict[str, Any]:
    tz = ZoneInfo(cfg.timezone)
    now = now or datetime.now(tz)
    closed_all = [s for s in all_signals if s.status != "open"]
    visible_closed = [s for s in closed_all if s.source != "shadow"]
    open_sigs = [s for s in all_signals if s.status == "open"]
    weights = (adjustments or {}).get("weights", {})

    criteria = []
    for key, label in CRITERION_LABELS.items():
        with_crit = [s for s in closed_all if key in s.criteria]
        by_source = {src: _stats([s for s in with_crit if s.source == src]) for src in ("bot", "manual", "shadow")}
        last = sorted(with_crit, key=lambda s: s.created_at, reverse=True)[:8]
        criteria.append({"key": key, "label": label, "weight": weights.get(key), "stats": _stats(with_crit),
                         "by_source": by_source, "last_trades": [_sig_row(s, tz) for s in last]})

    assets = []
    for key, asset in cfg.assets.items():
        mine = [s for s in visible_closed if s.asset == key]
        assets.append({"key": key, "label": asset.label, "stats": _stats(mine),
                       "shadow": _stats([s for s in closed_all if s.asset == key and s.source == "shadow"]),
                       "open": sum(1 for s in open_sigs if s.asset == key and s.source != "shadow"),
                       "session_utc": list(asset.session_utc) if asset.session_utc else None,
                       "cost_pct": asset.cost_pct})

    return {
        "updated_at": now.astimezone(tz).isoformat(),
        "timezone": cfg.timezone,
        "overview": {"visible": _stats(visible_closed), "shadow": _stats([s for s in closed_all if s.source == "shadow"]),
                     "open": len([s for s in open_sigs if s.source != "shadow"]),
                     "open_shadow": len([s for s in open_sigs if s.source == "shadow"])},
        "by_source": {src: _stats([s for s in closed_all if s.source == src]) for src in ("bot", "manual", "shadow")},
        "assets": assets,
        "criteria": criteria,
        "open_signals": [_sig_row(s, tz) for s in sorted(open_sigs, key=lambda s: s.created_at, reverse=True)],
        "recent_trades": [_sig_row(s, tz) for s in sorted(visible_closed, key=lambda s: s.created_at, reverse=True)[:40]],
        "backtests": backtests or {},
        "adjustments": {"notes": (adjustments or {}).get("notes", []), "avoid_hours_utc": (adjustments or {}).get("avoid_hours_utc", []),
                        "sample": (adjustments or {}).get("sample")},
        "state": state or {},
        "limits": {"max_signals_per_asset_per_day": cfg.max_signals_per_asset_per_day,
                   "max_open_signals": cfg.max_open_signals, "cooldown_minutes": cfg.cooldown_minutes},
    }
