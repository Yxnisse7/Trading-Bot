"""Apprentissage par contexte, règles de sortie et filtres testés hors échantillon.

1. Contexte chiffré : chaque signal (réel, en ombre ou de backtest) garde quelques mesures prises à
   l'entrée (`meta["ctx"]`) : force de tendance, RSI, écarts au VWAP et à l'EMA20, volatilité, activité,
   taille du range, frais rapportés au risque, minutes depuis l'ouverture américaine, jour.
   L'apprentissage coupe chaque mesure en tranches et repère celles qui perdent nettement
   (même marge de sécurité que les tranches horaires). Rien n'est filtré d'office : voir 3.

2. Excursions : pendant le suivi, chaque trade garde son gain maximal et sa perte maximale en R, et
   l'on note si, après avoir atteint +0,5 / +0,8 / +1 R, il est revenu au prix d'entrée
   (`meta["exc"]`). On en déduit ce qu'aurait donné un stop remonté à l'entrée après ces seuils.
   Simple mesure : une règle de sortie touche les vrais trades, elle n'est jamais activée seule.

3. Filtres testés hors échantillon : un signal réel qui tombe dans une tranche évitée (ou autour de
   l'ouverture américaine) reste envoyé, mais il est marqué (`meta["filters"]`). Le filtre n'est
   appliqué que si, sur les trades marqués APRÈS la mise en place du test, les trades écartés font
   nettement pire que les autres (au moins 100 trades gardés, 20 écartés, écart prouvé).
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from . import indicators as ind
from .config import Config
from .models import Signal, parse_iso

# ------------------------------------------------------------------ 1. contexte
FEATURES = {
    "adx": "force de tendance (ADX 15 min)",
    "rsi_dir": "RSI dans le sens du trade",
    "vwap_ext": "écart au VWAP dans le sens du trade (en range)",
    "ema_ext": "écart à l'EMA20 dans le sens du trade (en range)",
    "atr_ratio": "volatilité du moment / moyenne 24 h",
    "activity": "activité de l'heure / moyenne",
    "range_pct": "taille du range (%)",
    "cost_r": "frais rapportés au risque (R)",
    "us_open_min": "minutes depuis l'ouverture américaine",
    "weekday": "jour de la semaine",
}
DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
US_OPEN_BINS = [(-1e9, -30.0, "plus de 30 min avant l'ouverture US"), (-30.0, 90.0, "de 30 min avant à 1 h 30 après"),
                (90.0, 1e9, "plus de 1 h 30 après l'ouverture US")]
US_OPEN_WINDOW = (-30.0, 90.0)          # 15:00 → 17:00 à Paris (ouverture à 15:30)
US_OPEN_ASSETS = ("nasdaq", "sp500", "gold")


def signal_context(features: dict[str, float], direction: str, entry: float, stop: float, cost_pct: float,
                   range_pct: float, now: datetime) -> dict[str, float]:
    """Mesures du contexte, orientées dans le sens du trade (positif = dans le sens du trade)."""
    sign = 1.0 if direction == "long" else -1.0
    ctx: dict[str, float] = {}
    if "adx" in features:
        ctx["adx"] = features["adx"]
    if "rsi" in features:
        ctx["rsi_dir"] = round(features["rsi"] if direction == "long" else 100.0 - features["rsi"], 2)
    for raw, key in (("vwap_dev", "vwap_ext"), ("ema_dev", "ema_ext")):
        if raw in features:
            ctx[key] = round(sign * features[raw], 4)
    for key in ("atr_ratio", "activity"):
        if key in features:
            ctx[key] = features[key]
    ctx["range_pct"] = round(range_pct, 4)
    risk_pct = abs(entry - stop) / entry * 100.0 if entry else 0.0
    if risk_pct > 0:
        ctx["cost_r"] = round(cost_pct / risk_pct, 4)
    ts = int(now.timestamp())
    ctx["us_open_min"] = round((ts - ind.us_open_ts(ts)) / 60.0, 1)
    ctx["weekday"] = now.weekday()
    return ctx


def in_us_open_window(asset_key: str, when: datetime) -> bool:
    """Entrée entre 30 min avant et 1 h 30 après l'ouverture américaine, sur les indices et l'or."""
    if asset_key not in US_OPEN_ASSETS:
        return False
    ts = int(when.timestamp())
    minutes = (ts - ind.us_open_ts(ts)) / 60.0
    return US_OPEN_WINDOW[0] <= minutes < US_OPEN_WINDOW[1]


def _weighted(pairs: list[tuple[float, float]]) -> dict[str, float] | None:
    from .learning import weighted_stats
    return weighted_stats(pairs)


def _tercile_cuts(values: list[float]) -> list[float]:
    v = sorted(values)
    if len(v) < 3:
        return []
    return [v[len(v) // 3], v[2 * len(v) // 3]]


def _fmt(v: float) -> str:
    return (f"{v:.2f}" if abs(v) < 10 else f"{v:.0f}").replace(".", ",")


def _buckets(feature: str, values: list[float]) -> list[tuple[float, float, str]]:
    if feature == "weekday":
        return [(d, d + 1, DAYS[d]) for d in sorted({int(x) for x in values})]
    if feature == "us_open_min":
        return list(US_OPEN_BINS)
    cuts = _tercile_cuts(values)
    if len(cuts) < 2 or cuts[0] == cuts[1]:
        return []
    lo, hi = cuts
    return [(-1e9, lo, f"bas (< {_fmt(lo)})"), (lo, hi, f"milieu ({_fmt(lo)} à {_fmt(hi)})"), (hi, 1e9, f"haut (≥ {_fmt(hi)})")]


def context_report(rows: list[tuple[Signal, float, float]], cfg: Config) -> dict[str, Any]:
    """Résultat moyen (R brut) par tranche de chaque mesure ; tranches nettement perdantes à éviter.

    `rows` : (signal, R brut, poids de la source). Le test est le même que pour les tranches horaires :
    une tranche n'est « à éviter » que si même sa borne haute (moyenne + marge) reste sous zéro."""
    with_ctx = [(s, r, w) for s, r, w in rows if (s.meta or {}).get("ctx")]
    out: dict[str, Any] = {"n": len(with_ctx), "features": {}, "avoid": []}
    z = cfg.learning_hours_z
    for feat, label in FEATURES.items():
        vals = [(s.meta["ctx"][feat], r, w) for s, r, w in with_ctx if s.meta["ctx"].get(feat) is not None]
        if not vals:
            continue
        buckets = []
        for lo, hi, blabel in _buckets(feat, [v for v, _, _ in vals]):
            st = _weighted([(r, w) for v, r, w in vals if lo <= v < hi])
            if not st:
                continue
            avoid = st["n_eff"] >= cfg.learning_min_trades and st["mean"] + z * st["se"] < 0
            buckets.append({"label": blabel, "lo": lo, "hi": hi, "n": st["n"], "n_eff": st["n_eff"],
                            "mean_r": round(st["mean"], 4), "margin_r": round(z * st["se"], 4), "avoid": avoid})
            if avoid:
                out["avoid"].append({"feature": feat, "lo": lo, "hi": hi, "label": f"{label} : {blabel}",
                                     "mean_r": round(st["mean"], 4), "n": st["n"]})
        if buckets:
            out["features"][feat] = {"label": label, "buckets": buckets}
    return out


def context_hits(ctx: dict[str, float] | None, learned: dict[str, Any] | None) -> list[str]:
    """Tranches évitées (apprises) dans lesquelles tombe ce contexte."""
    if not ctx or not learned:
        return []
    return [a["label"] for a in learned.get("avoid", [])
            if ctx.get(a["feature"]) is not None and a["lo"] <= ctx[a["feature"]] < a["hi"]]


# ------------------------------------------------------------------ 2. excursions
EXIT_RULES = (0.5, 0.8, 1.0)


def new_excursion() -> dict[str, Any]:
    return {"mfe": 0.0, "mae": 0.0, "armed": {str(x): False for x in EXIT_RULES},
            "be": {str(x): False for x in EXIT_RULES}, "last_ts": None}


def excursion_step(sig: Signal, st: dict[str, Any], high: float, low: float) -> None:
    """Met à jour gain / perte maximaux (en R) avec une bougie (ou un prix : high = low).

    Stop à l'entrée après +x R : armé à la clôture de la bougie qui atteint +x R (le bot ne réagit
    qu'entre deux passages), déclenché si une bougie suivante revient au prix d'entrée."""
    risk = abs(sig.entry - sig.stop_loss)
    if risk <= 0:
        return
    if sig.direction == "long":
        fav, adv = (high - sig.entry) / risk, (sig.entry - low) / risk
    else:
        fav, adv = (sig.entry - low) / risk, (high - sig.entry) / risk
    for x in EXIT_RULES:
        k = str(x)
        if st["armed"][k] and not st["be"][k] and adv >= 0:
            st["be"][k] = True
    st["mfe"] = round(max(st["mfe"], fav), 4)
    st["mae"] = round(max(st["mae"], adv), 4)
    for x in EXIT_RULES:
        if fav >= x:
            st["armed"][str(x)] = True


def walk_excursion(sig: Signal, candles: list, until: datetime | None) -> None:
    """Parcourt les bougies postérieures à l'entrée (jusqu'à `until` inclus), une seule fois chacune."""
    st = (sig.meta or {}).get("exc") or new_excursion()
    start = int(parse_iso(sig.created_at).timestamp())
    end = int(until.timestamp()) if until else None
    last = st.get("last_ts")
    for c in candles or []:
        if c.ts < start or (last is not None and c.ts <= last) or (end is not None and c.ts > end):
            continue
        excursion_step(sig, st, c.high, c.low)
        st["last_ts"] = c.ts
    if sig.meta is None:
        sig.meta = {}
    sig.meta["exc"] = st


def rule_r(s: Signal, r: float, x: float) -> float:
    """R du trade si le stop avait été remonté à l'entrée après +x R (0 R s'il est revenu à l'entrée)."""
    exc = (s.meta or {}).get("exc") or {}
    return 0.0 if (exc.get("be") or {}).get(str(x)) else r


def exit_report(closed: list[Signal], cfg: Config) -> dict[str, Any]:
    """Ce qu'auraient donné les règles de sortie, sur les trades dont les excursions sont connues."""
    from .learning import trade_r
    groups = {"réels et en ombre": lambda s: s.source != "backtest", "backtest": lambda s: s.source == "backtest"}
    out: dict[str, Any] = {}
    for gname, pred in groups.items():
        rows = []
        for s in closed:
            if not pred(s) or not (s.meta or {}).get("exc"):
                continue
            g, n = trade_r(s), trade_r(s, net=True)
            if g is None or n is None:
                continue
            rows.append((s, g, g - n))          # (signal, R brut, coût en R)
        if not rows:
            continue
        sl = [s for s, _, _ in rows if s.status == "sl"]
        cur = sum(g - c for _, g, c in rows) / len(rows)
        entry = {"n": len(rows), "current_net_r": round(cur, 4),
                 "mfe_median": round(sorted(s.meta["exc"]["mfe"] for s, _, _ in rows)[len(rows) // 2], 3),
                 "sl_reached": {str(x): sum(1 for s in sl if s.meta["exc"]["mfe"] >= x) for x in EXIT_RULES},
                 "n_sl": len(sl), "rules": {}}
        for x in EXIT_RULES:
            rr = [rule_r(s, g, x) - c for s, g, c in rows]
            mean = sum(rr) / len(rr)
            diffs = [a - (g - c) for a, (_, g, c) in zip(rr, rows)]
            md = sum(diffs) / len(diffs)
            sd = math.sqrt(sum((d - md) ** 2 for d in diffs) / max(1, len(diffs) - 1)) if len(diffs) > 1 else float("inf")
            margin = cfg.learning_z * sd / math.sqrt(len(diffs)) if len(diffs) > 1 else float("inf")
            entry["rules"][str(x)] = {"net_r": round(mean, 4), "diff_r": round(md, 4), "margin_r": round(margin, 4),
                                      "better": len(rows) >= cfg.variant_min_trades and md - margin > 0}
        out[gname] = entry
    return out


# ------------------------------------------------------------------ 3. filtres
FILTERS = {
    "sans_ouverture_us": "pas d'entrée sur les indices et l'or de 15:00 à 17:00 (ouverture US)",
    "filtre_contexte": "contextes appris comme perdants évités",
    "sans_etirement_or": "or : pas d'entrée à plus de 1,5 ATR de la moyenne 20 en 5 min (essai 14)",
    "limites_jour_or": "or : 3 trades par jour au plus, arrêt après 2 pertes (essai 15)",
}


def day_limit_hit(asset_key: str, sigs: list[Signal], now: datetime, max_trades: int = 3, max_losses: int = 2) -> bool:
    """Essai 15, G40 : déjà `max_trades` signaux réels ce jour (heure de New York) sur l'actif, ou `max_losses` pertes."""
    from zoneinfo import ZoneInfo
    ny = ZoneInfo("America/New_York")
    day = now.astimezone(ny).date()
    same = [s for s in sigs if s.asset == asset_key and s.source == "bot" and s.created_at
            and parse_iso(s.created_at).astimezone(ny).date() == day]
    losses = sum(1 for s in same if s.status == "sl" or (s.status == "expired" and (s.pnl_pct or 0) < 0))
    return len(same) >= max_trades or losses >= max_losses


def stretched(candles, direction: str, limit: float = 1.5) -> bool:
    """Essai 14, filtre A1 : dernière clôture 5 min à plus de `limit` ATR 14 de sa moyenne 20, dans le sens du trade."""
    if len(candles) < 21:
        return False
    sma, atr = ind.sma([c.close for c in candles], 20)[-1], ind.atr(candles, 14)[-1]
    if sma is None or not atr:
        return False
    return (candles[-1].close - sma) * (1 if direction == "long" else -1) > limit * atr


def filter_report(closed: list[Signal], cfg: Config, z: float | None = None) -> dict[str, Any]:
    """Compare, sur les trades réels marqués depuis la mise en place du test, les trades qu'un filtre
    aurait écartés à ceux qu'il garde (gain net en R)."""
    from .learning import trade_r
    trial = {k for k, a in cfg.assets.items() if a.trial}
    base = [(s, trade_r(s, net=True)) for s in closed
            if s.source == "bot" and s.asset not in trial and (s.meta or {}).get("filters_checked")]
    base = [(s, r) for s, r in base if r is not None]
    out: dict[str, Any] = {}
    for key, label in FILTERS.items():
        out_r = [r for s, r in base if key in (s.meta.get("filters") or [])]
        kept = [r for s, r in base if key not in (s.meta.get("filters") or [])]
        mo = sum(out_r) / len(out_r) if out_r else None
        mk = sum(kept) / len(kept) if kept else None
        promoted = False
        if len(kept) >= cfg.variant_min_trades and len(out_r) >= 20 and mo is not None and mk is not None:
            var = lambda xs, m: sum((x - m) ** 2 for x in xs) / max(1, len(xs) - 1)  # noqa: E731
            se = math.sqrt(var(out_r, mo) / len(out_r) + var(kept, mk) / len(kept))
            promoted = mk - mo > (z if z is not None else cfg.learning_z) * se
        out[key] = {"label": label, "n": len(kept) + len(out_r), "n_out": len(out_r), "n_kept": len(kept),
                    "mean_out_r": round(mo, 4) if mo is not None else None,
                    "mean_kept_r": round(mk, 4) if mk is not None else None,
                    "missing": max(0, cfg.variant_min_trades - len(kept)), "promoted": promoted}
    return out


def us_open_history(closed: list[Signal]) -> dict[str, Any]:
    """Pour information : trades passés (réels, puis backtest) dans la fenêtre de l'ouverture US ou non."""
    from .learning import trade_r
    out = {}
    for name, pred in (("réels", lambda s: s.source in ("bot", "manual", "request")), ("backtest", lambda s: s.source == "backtest")):
        rows = [(s, trade_r(s, net=True)) for s in closed if pred(s) and s.asset in US_OPEN_ASSETS]
        rows = [(s, r) for s, r in rows if r is not None]
        inside = [r for s, r in rows if in_us_open_window(s.asset, parse_iso(s.created_at))]
        other = [r for s, r in rows if not in_us_open_window(s.asset, parse_iso(s.created_at))]
        if rows:
            out[name] = {"n_in": len(inside), "mean_in_r": round(sum(inside) / len(inside), 4) if inside else None,
                         "n_out": len(other), "mean_out_r": round(sum(other) / len(other), 4) if other else None}
    return out
