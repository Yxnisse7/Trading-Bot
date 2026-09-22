"""Analyse de l'historique : quels setups gagnent, et ajustement des poids de sélection."""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from .analysis import CRITERION_FAMILIES, DEFAULT_WEIGHTS
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
        "by_horizon": stats_by(closed, lambda s: [s.horizon or "1h"]),
        "expired": expired_stats(closed),
    }


def expired_stats(closed: list[Signal]) -> dict[str, Any]:
    """Trades expirés : part terminée dans le bon sens et P&L moyen (sortie au temps)."""
    exp = [s for s in closed if s.status == "expired"]
    if not exp:
        return {"n": 0, "in_favor": None, "avg_pnl_pct": None}
    favor = sum(1 for s in exp if (s.pnl_gross_pct or 0) > 0)
    return {"n": len(exp), "in_favor": round(favor / len(exp), 4),
            "avg_pnl_pct": round(sum(s.pnl_pct or 0 for s in exp) / len(exp), 4)}


# ------------------------------------------------------------------ apprentissage v2
#
# Principes :
# 1. Recalcul complet : à chaque passage, les poids sont recalculés à partir de TOUS les trades
#    clôturés, en partant des poids par défaut. Aucune mémoire des poids précédents : les mêmes
#    trades donnent toujours les mêmes poids, et aucun trade n'est compté deux fois.
# 2. Marge de sécurité : un poids ne bouge que de la part de l'écart qui dépasse ce que le bruit
#    peut expliquer (écart − z × erreur type). Peu de trades → grande marge → poids par défaut.
# 3. Résultat en R : gain ou perte rapporté au risque pris, trades expirés compris. Sous le hasard,
#    l'espérance brute d'un trade est nulle quelle que soit la position du TP et du SL : c'est la
#    référence. Comparer le brut à zéro revient à comparer le net au coût du hasard, frais compris.
# 4. Sources pondérées : un trade réel compte plus qu'un fantôme, qui compte plus qu'un backtest.
# 5. Familles : les critères qui mesurent la même information sont jugés ensemble.
# 6. Socle global + correction par actif : un actif ne s'écarte du global que si sa différence
#    dépasse, elle aussi, la marge de sécurité.

REAL_SOURCES = ("bot", "manual", "request")
VARIANT_LABELS = {
    "hors_session": "indices le matin européen",
    "horizon_3h": "horizon ~3 h",
    "confiance_moyenne": "confiance moyenne",
}


def trade_r(s: Signal, net: bool = False) -> float | None:
    """Résultat d'un trade clôturé en multiples du risque pris (R). Brut de frais par défaut."""
    if s.status not in ("tp", "sl", "expired") or not s.entry:
        return None
    risk_pct = abs(s.entry - s.stop_loss) / s.entry * 100.0
    pnl = s.pnl_pct if net else (s.pnl_gross_pct if s.pnl_gross_pct is not None else s.pnl_pct)
    if not risk_pct or pnl is None:
        return None
    return pnl / risk_pct


def weighted_stats(pairs: list[tuple[float, float]]) -> dict[str, float] | None:
    """Moyenne pondérée, taille d'échantillon équivalente et erreur type de la moyenne."""
    pairs = [(r, w) for r, w in pairs if w > 0]
    total = sum(w for _, w in pairs)
    if total <= 0:
        return None
    mean = sum(r * w for r, w in pairs) / total
    n_eff = total * total / sum(w * w for _, w in pairs)
    var = sum(w * (r - mean) ** 2 for r, w in pairs) / total
    if n_eff > 1:
        var *= n_eff / (n_eff - 1)
    se = math.sqrt(var / n_eff) if n_eff > 0 else float("inf")
    return {"n": len(pairs), "n_eff": round(n_eff, 1), "mean": mean, "se": se}


def proven(mean: float, se: float, z: float) -> float:
    """Part de l'écart au-delà de la marge de sécurité (0 si l'écart s'explique par le bruit)."""
    return math.copysign(max(0.0, abs(mean) - z * se), mean)


def _units() -> dict[str, tuple[str, ...]]:
    """Unités évaluées : chaque famille d'un bloc, puis chaque critère isolé."""
    in_family = {c for members in CRITERION_FAMILIES.values() for c in members}
    units = dict(CRITERION_FAMILIES)
    for c in DEFAULT_WEIGHTS:
        if c not in in_family:
            units[c] = (c,)
    return units


def _unit_label(unit: str) -> str:
    members = CRITERION_FAMILIES.get(unit)
    return f"{unit} ({', '.join(members)})" if members else unit


def _fmt_r(v: float) -> str:
    return f"{v:+.2f} R".replace(".", ",")


def _fmt_m(v: float) -> str:
    return f"± {v:.2f} R".replace(".", ",")


def variant_report(closed: list[Signal], cfg: Config) -> dict[str, Any]:
    """Compare chaque variante testée en fantôme aux signaux réels du bot, sur le gain net."""
    base = [trade_r(s, net=True) for s in closed if s.source == "bot"]
    base = [r for r in base if r is not None]
    base_mean = sum(base) / len(base) if base else None
    out: dict[str, Any] = {"baseline": {"n": len(base), "mean_net_r": round(base_mean, 4) if base_mean is not None else None},
                           "variants": {}, "promoted": []}
    for key, label in VARIANT_LABELS.items():
        rs = [trade_r(s, net=True) for s in closed if s.source == "shadow" and (s.meta or {}).get("variant") == key]
        rs = [r for r in rs if r is not None]
        mean = sum(rs) / len(rs) if rs else None
        ready = (len(rs) >= cfg.variant_min_trades and len(base) >= cfg.variant_baseline_min_trades
                 and mean is not None and base_mean is not None and mean >= base_mean)
        out["variants"][key] = {"label": label, "n": len(rs), "mean_net_r": round(mean, 4) if mean is not None else None,
                                "promoted": ready, "missing": max(0, cfg.variant_min_trades - len(rs))}
        if ready:
            out["promoted"].append(key)
    return out


def learn(history: list[Signal], cfg: Config, current: dict[str, Any] | None = None) -> dict[str, Any]:
    """Recalcule entièrement les poids à partir de tous les trades clôturés (`current` est ignoré :
    aucune mémoire des poids précédents, par construction)."""
    closed = [s for s in history if s.status != "open"]
    src_w = cfg.learning_source_weights
    rows = [(s, r, float(src_w.get(s.source, 0.0))) for s in closed for r in [trade_r(s)] if r is not None]
    units = _units()
    weights = dict(DEFAULT_WEIGHTS)
    stats: dict[str, Any] = {}
    moved: list[str] = []

    # --- Socle global
    unit_mult: dict[str, float] = {}
    for unit, members in units.items():
        st = weighted_stats([(r, w) for s, r, w in rows if set(members) & set(s.criteria)])
        mult = 1.0
        if st and st["n_eff"] >= cfg.learning_min_trades:
            p = proven(st["mean"], st["se"], cfg.learning_z)
            mult = min(1.5, max(0.25, 1.0 + cfg.learning_gain * p))
        unit_mult[unit] = mult
        for c in members:
            weights[c] = round(min(1.5, max(min(0.25, DEFAULT_WEIGHTS[c]), DEFAULT_WEIGHTS[c] * mult)), 3)
        if st:
            stats[unit] = {"members": list(members), "n": st["n"], "n_eff": st["n_eff"],
                           "mean_r": round(st["mean"], 4), "margin_r": round(cfg.learning_z * st["se"], 4),
                           "multiplier": round(mult, 3)}
            if mult != 1.0:
                moved.append(f"{_unit_label(unit)} : {_fmt_r(st['mean'])} {_fmt_m(cfg.learning_z * st['se'])} sur "
                             f"{st['n_eff']:.0f} trades éq. → poids " + f"×{mult:.2f}".replace(".", ","))

    # --- Correction par actif : seulement si l'écart au global dépasse sa propre marge
    by_asset: dict[str, dict[str, float]] = {}
    asset_notes: list[str] = []
    for asset in sorted({s.asset for s, _, _ in rows}):
        aw = dict(weights)
        for unit, members in units.items():
            g = stats.get(unit)
            st = weighted_stats([(r, w) for s, r, w in rows if s.asset == asset and set(members) & set(s.criteria)])
            if not g or not st or st["n_eff"] < cfg.learning_asset_min_trades:
                continue
            p = proven(st["mean"] - g["mean_r"], st["se"], cfg.learning_z)
            if p == 0.0:
                continue
            mult = min(1.5, max(0.5, 1.0 + cfg.learning_gain * p))
            for c in members:
                aw[c] = round(min(1.5, max(min(0.25, DEFAULT_WEIGHTS[c]), weights[c] * mult)), 3)
            asset_notes.append(f"{asset}, {_unit_label(unit)} : {_fmt_r(st['mean'])} contre {_fmt_r(g['mean_r'])} "
                               f"en global sur {st['n_eff']:.0f} trades éq. → poids " + f"×{mult:.2f}".replace(".", ",") + " sur cet actif")
        by_asset[asset] = aw

    # --- Tranches horaires nettement perdantes (brut, donc pires que le hasard)
    avoid_hours = []
    for hour in range(24):
        st = weighted_stats([(r, w) for s, r, w in rows if parse_iso(s.created_at).hour == hour])
        if st and st["n_eff"] >= cfg.learning_min_trades and st["mean"] + cfg.learning_hours_z * st["se"] < 0:
            avoid_hours.append(hour)
            moved.append(f"tranche {hour:02d}h UTC : {_fmt_r(st['mean'])} sur {st['n_eff']:.0f} trades éq. → évitée")

    # --- Vue d'ensemble par source et variantes
    overview = {}
    for label, pred in (("réels", lambda s: s.source in REAL_SOURCES), ("fantômes", lambda s: s.source == "shadow"),
                        ("backtest", lambda s: s.source == "backtest")):
        st = weighted_stats([(r, 1.0) for s, r, _ in rows if pred(s)])
        if st:
            overview[label] = {"n": st["n"], "mean_r": round(st["mean"], 4), "margin_r": round(cfg.learning_z * st["se"], 4)}
    variants = variant_report(closed, cfg) if cfg.variants_enabled else {"variants": {}, "promoted": []}

    notes: list[str] = []
    real = overview.get("réels")
    if real:
        notes.append(f"trades réels : {_fmt_r(real['mean_r'])} {_fmt_m(real['margin_r'])} par trade avant frais "
                     f"sur {real['n']} trades (0 R = hasard)")
    notes += moved or ["aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés"]
    notes += asset_notes
    for key, v in variants.get("variants", {}).items():
        if v["promoted"]:
            notes.append(f"variante « {v['label']} » promue : {_fmt_r(v['mean_net_r'])} net sur {v['n']} trades, "
                         f"au moins aussi bien que les signaux réels")
        elif v["n"]:
            notes.append(f"variante « {v['label']} » en test : {v['n']} trades, {_fmt_r(v['mean_net_r'])} net"
                         + (f", encore {v['missing']} trades avant décision" if v["missing"] else ", pas meilleure que les signaux réels"))

    by_source: dict[str, int] = {}
    for s in closed:
        by_source[s.source] = by_source.get(s.source, 0) + 1
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "method": "v2 : recalcul complet, marge de sécurité, résultats en R, sources pondérées",
        "weights": weights,
        "weights_by_asset": by_asset,
        "avoid_hours_utc": avoid_hours,
        "stats": stats,
        "overview": overview,
        "variants": variants.get("variants", {}),
        "baseline": variants.get("baseline"),
        "promoted_variants": variants.get("promoted", []),
        "notes": notes[:20],
        "sample": len(closed),
        "sample_by_source": by_source,
    }
