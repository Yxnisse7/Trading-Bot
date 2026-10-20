"""Résumé quotidien (HTML Telegram) : chiffres du jour, chaque trade, enseignements, apprentissage.

Le résumé reste complet (tous les trades du jour) mais n'annonce comme résultat que ce qui est
statistiquement significatif face au hasard ; le reste est présenté comme une piste à confirmer.
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from .config import Config
from .learning import analyze, neutral_win_rate, win_rate
from .messages import CRIT_TEXT, esc, pct, price, rate
from .models import Signal, parse_iso
from .pc_link import LABELS

DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
TREND = {"trend_5m": "tendance 5 min", "trend_15m": "tendance 15 min", "trend_1h": "tendance 1 h"}


def _crit_label(c: str) -> str:
    return TREND.get(c) or CRIT_TEXT.get(c, c)


def _groups(sigs: list[Signal], key) -> dict[str, list[Signal]]:
    out: dict[str, list[Signal]] = {}
    for s in sigs:
        for k in key(s):
            out.setdefault(k, []).append(s)
    return out


def _verdicts(closed: list[Signal], labels: dict[str, str]) -> tuple[list[str], list[str]]:
    """(significatifs, pistes) : écart au hasard avec au moins 3 trades décidés (TP ou SL).
    Significatif = écart au-delà de 1,96 écart-type (même seuil que l'apprentissage)."""
    sig_list, leads = [], []
    for kind, groups in labels.items():
        for name, group in groups.items():
            tp = sum(1 for s in group if s.status == "tp")
            sl = sum(1 for s in group if s.status == "sl")
            n = tp + sl
            wr, p = win_rate(group), neutral_win_rate(group)
            if n < 3 or wr is None or p is None:
                continue
            gap = wr - p
            se = math.sqrt(p * (1 - p) / n) if 0 < p < 1 else 1.0
            text = f"{esc(name)} : {rate(wr)} sur {n}, hasard {rate(p)}"
            arrow = "↑" if gap > 0 else "↓"
            if abs(gap) >= 1.96 * se:
                sig_list.append(f"{arrow} {text}")
            elif abs(gap) >= 0.10:
                leads.append(f"{arrow} {text}")
    return sig_list, leads


def lab_week_lines(lab_shadow: dict[str, Any], cfg: Config) -> list[str]:
    """Point de la semaine sur les stratégies du laboratoire suivies en ombre (frais Topstep)."""
    if not lab_shadow:
        return []
    out = ["", "<b>🧪 Laboratoire en ombre · point de la semaine</b>"]
    for rec in lab_shadow.values():
        asset = cfg.assets.get(rec.get("asset"))
        name = re.sub(r" \(.*\)$", "", asset.label) if asset else rec.get("asset", "")
        opened = next((t for t in rec.get("trades", []) if t.get("status") == "open"), None)
        n, m = rec.get("n") or 0, rec.get("mean_r")
        line = f"• {esc(rec.get('strategy', ''))} · {esc(name)} : "
        line += (f"{n} trade{'s' if n > 1 else ''} clôturé{'s' if n > 1 else ''}, {m:+.2f} R en moyenne".replace(".", ",")
                 if n else "aucun trade clôturé")
        if opened:
            line += f" · en cours : {'achat' if opened['direction'] == 'long' else 'vente'}"
        out.append(line)
    out.append("Suivi silencieux : aucune notification de trade, uniquement ce point du dimanche.")
    return out


def lab_day(lab_shadow: dict[str, Any], cfg: Config, day: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Trades réels des stratégies (annoncés sur Telegram) clôturés ce jour-là, et ceux encore ouverts."""
    tz = ZoneInfo(cfg.timezone)
    closed, opened = [], []
    for rec in (lab_shadow or {}).values():
        for t in rec.get("trades") or []:
            if not t.get("notified_entry") or t.get("pc_absent"):
                continue
            row = dict(t, strategy=rec.get("strategy", ""), asset=rec.get("asset", ""))
            if t.get("status") == "closed" and t.get("exit_ts") and \
                    datetime.fromtimestamp(t["exit_ts"], tz).date() == day:
                closed.append(row)
            elif t.get("status") == "open" and datetime.fromtimestamp(t["entry_ts"], tz).date() <= day:
                opened.append(row)
    return sorted(closed, key=lambda t: t["exit_ts"]), sorted(opened, key=lambda t: t["entry_ts"])


def _r(v: float) -> str:
    return f"{v:+.2f} R".replace(".", ",").replace("-", "−")


def _lab_line(t: dict[str, Any], cfg: Config, tz: ZoneInfo, day: date) -> str:
    asset = cfg.assets.get(t["asset"])
    name = re.sub(r" \(.*\)$", "", asset.label) if asset else t["asset"]
    dg = max(2, asset.price_decimals) if asset else 2
    long = t["direction"] == "long"
    at = datetime.fromtimestamp(t["entry_ts"], tz)
    head = (f"{at:%H:%M}" if at.date() == day else f"{at:%d/%m %H:%M}") + (f" {'↗️' if long else '↘️'} {esc(name)} "
            f"{'achat' if long else 'vente'} {price(t['entry'], dg)} · {esc(LABELS.get(t['strategy'], t['strategy']))}")
    if t.get("status") == "open":
        return head + " · ⏳ en cours"
    r = t.get("r_topstep") or 0.0
    move = (t["exit"] / t["entry"] - 1) * 100.0 * (1 if long else -1) if t.get("exit") and t.get("entry") else None
    return head + f" · {'✅' if r > 0 else '❌'} {_r(r)}" + (f" ({pct(move)})" if move is not None else "")


def daily_summary(all_signals: list[Signal], cfg: Config, day: date | None = None,
                  adjustments: dict[str, Any] | None = None, lab_shadow: dict[str, Any] | None = None) -> str:
    tz = ZoneInfo(cfg.timezone)
    day = day or datetime.now(tz).date()
    shadow_today = [s for s in all_signals if s.source == "shadow" and parse_iso(s.created_at).astimezone(tz).date() == day]
    all_signals = [s for s in all_signals if s.source != "shadow"]
    todays = [s for s in all_signals if parse_iso(s.created_at).astimezone(tz).date() == day]
    closed_today = [s for s in todays if s.status != "open"]
    still_open = [s for s in todays if s.status == "open"]
    tp = sum(1 for s in closed_today if s.status == "tp")
    sl = sum(1 for s in closed_today if s.status == "sl")
    exp = sum(1 for s in closed_today if s.status == "expired")
    cumulative = [s for s in all_signals if s.status != "open"]
    pnl_day = sum(s.pnl_pct or 0 for s in closed_today)
    pnl_cum = sum(s.pnl_pct or 0 for s in cumulative)
    wr_day, wr_cum, neutral_cum = win_rate(closed_today), win_rate(cumulative), neutral_win_rate(cumulative)

    # 20/10 : le résumé ne comptait que le bot classique ; les stratégies en réel (la plupart des trades) manquaient
    lab_closed, lab_open = lab_day(lab_shadow or {}, cfg, day)
    lab_r = sum(t.get("r_topstep") or 0.0 for t in lab_closed)
    wins = sum(1 for t in lab_closed if (t.get("r_topstep") or 0) > 0)
    lines = [
        f"<b>📊 RÉSUMÉ QUOTIDIEN · {DAYS[day.weekday()]} {day:%d/%m/%Y}</b>",
        f"<b>Stratégies : {len(lab_closed)} trade{'s' if len(lab_closed) > 1 else ''} clôturé"
        f"{'s' if len(lab_closed) > 1 else ''} · {wins} gagnant{'s' if wins > 1 else ''}, "
        f"{len(lab_closed) - wins} perdant{'s' if len(lab_closed) - wins > 1 else ''} · {_r(lab_r)}</b>",
        f"<b>Bot classique : {tp} TP, {sl} SL, {exp} expirés · {pct(pnl_day)}</b>",
    ]
    if lab_closed or lab_open:
        lines += [_lab_line(t, cfg, tz, day) for t in lab_closed + lab_open]
        lines.append("<i>1 R = la perte prévue au SL (≈ 245 $ sur Topstep).</i>")
    lines += [
        "",
        "<b>Bot classique</b>",
        f"Signaux proposés : {len(todays)}" + (f", dont {len(still_open)} encore ouverts" if still_open else ""),
        f"Réussite du jour : {rate(wr_day)} (TP sur TP + SL)",
        f"Réussite cumulée : {rate(wr_cum)} sur {len(cumulative)} trades clôturés"
        + (f", hasard attendu {rate(neutral_cum)}" if cumulative else ""),
        f"Résultat net des coûts (somme des % par trade) : jour {pct(pnl_day)} · cumulé {pct(pnl_cum)}",
        f"Trades testés en ombre aujourd'hui, sans toucher au compte : {len(shadow_today)}",
    ]
    if todays:
        lines += ["", "<b>Détail du jour</b>"]
        for s in sorted(todays, key=lambda x: x.created_at):
            t = parse_iso(s.created_at).astimezone(tz)
            res = {"tp": "✅ TP", "sl": "❌ SL", "expired": "⏱️ expiré", "open": "⏳ en cours"}[s.status]
            arrow = "↗️" if s.direction == "long" else "↘️"
            name = re.sub(r" \(.*\)$", "", s.asset_label)
            word = "achat" if s.direction == "long" else "vente"
            asset = cfg.assets.get(s.asset)
            dg = max(2, asset.price_decimals) if asset else 2
            detail = [res + (f" {pct(s.pnl_pct)}" if s.pnl_pct is not None else "")]
            if s.duration_minutes is not None:
                detail.append(f"{s.duration_minutes} min")
            if s.source != "bot":
                detail.append({"manual": "manuel", "request": "proposition"}.get(s.source, s.source))
            me = (s.meta or {}).get("manual_exit")
            if me:
                detail.append(f"arrêté à la main à {pct(me.get('pnl_pct'))}")
            lines.append(f"{t:%H:%M} {arrow} {esc(name)} {word} {price(s.entry, dg)} · " + " · ".join(detail))

    rep = analyze(all_signals)
    lines += ["", "<b>Ce que disent les chiffres</b>"]
    ex = rep["expired"]
    if ex["n"] >= 5:
        lines.append(f"Trades expirés (cumul) : {ex['n']}, {rate(ex['in_favor'])} terminés dans le bon sens, "
                     f"résultat moyen {pct(ex['avg_pnl_pct'], 3)} : "
                     + ("une sortie au temps serait favorable." if ex["avg_pnl_pct"] > 0 else "la sortie au temps n'apporte rien."))
    for h, st in rep["by_horizon"].items():
        if st["tp"] + st["sl"] >= 3:
            hl = re.sub(r"(\d)h$", r"\1 h", h)
            lines.append(f"Horizon {esc(hl)} : {st['n']} trades, réussite {rate(st['win_rate'])}, résultat moyen {pct(st['avg_pnl_pct'], 3)}")
    labels = {
        "actif": {re.sub(r" \(.*\)$", "", g[0].asset_label): g for g in _groups(cumulative, lambda s: [s.asset]).values()},
        "critère": {_crit_label(k): g for k, g in _groups(cumulative, lambda s: s.criteria).items()},
        "sens": {("achats" if k == "long" else "ventes"): g for k, g in _groups(cumulative, lambda s: [s.direction]).items()},
    }
    significant, leads = _verdicts(cumulative, labels)
    lines.append("Significatif face au hasard : " + ("" if significant else "rien pour l'instant"))
    lines.extend(f"• {v}" for v in significant)
    if leads:
        lines.append("Pistes à confirmer, trop peu de trades pour conclure :")
        lines.extend(f"• {v}" for v in leads)

    lines.append("")
    if adjustments and adjustments.get("notes"):
        lines.append("<b>Apprentissage</b> (recalculé sur tous les trades)")
        lines.extend(f"• {esc(n)}" for n in adjustments["notes"][:8])
        if adjustments.get("avoid_hours_utc"):
            lines.append(f"• tranches horaires évitées (UTC) : {esc(adjustments['avoid_hours_utc'])}")
    else:
        lines.append("<b>Apprentissage</b> : aucun ajustement, critères actuels conservés.")
    if day.weekday() == 6:
        lines += lab_week_lines(lab_shadow or {}, cfg)
    return "\n".join(lines)

