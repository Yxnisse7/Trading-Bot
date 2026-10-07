"""Alerte de décrochage des stratégies suivies en ombre (essai 7 de HYPOTHESES.md).

Les trades réels de chaque stratégie en ombre sont comparés à ce que son backtest de 24 mois laissait
attendre : 5 000 tirages de n trades consécutifs dans la référence (bootstrap en blocs, les séries de
pertes restent groupées), puis le rang du gain cumulé réel et de sa pire baisse parmi ces tirages.
Seuils fixés d'avance ; message Telegram quand l'état s'aggrave. Skills : live-vs-backtest-drift-monitoring,
monte-carlo-trade-resampling-and-drawdown-distribution.
"""
from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

from .models import iso, utcnow

DRAWS = 5_000
BLOCK = 5                 # longueur moyenne des blocs tirés (en trades)
WATCH_N, DRIFT_N = 5, 10  # trades réels minimum avant « à surveiller » / « décroché »
WATCH, DRIFT = 0.05, 0.01
VARIANT = "horizon_3h_gold"
LABELS = {"donchian_1h:gold": "Donchian 1 h · or", "donchian_1h:bitcoin": "Donchian 1 h · Bitcoin",
          "donchian_day:gold": "Donchian fermé chaque soir · or",
          VARIANT: "Horizon 3 h · or"}
RANK = {"trop tôt": 0, "dans la norme": 0, "à surveiller": 1, "décroché": 2}


def max_drawdown(rs: list[float]) -> float:
    """Pire baisse depuis un sommet du gain cumulé, en R (positive)."""
    peak = cum = worst = 0.0
    for r in rs:
        cum += r
        peak = max(peak, cum)
        worst = max(worst, peak - cum)
    return worst


def resample(ref: list[float], n: int, rng: random.Random) -> list[float]:
    """n trades consécutifs tirés dans la référence, par blocs de longueur aléatoire (moyenne BLOCK)."""
    out, i = [], rng.randrange(len(ref))
    for _ in range(n):
        out.append(ref[i])
        i = rng.randrange(len(ref)) if rng.random() < 1 / BLOCK else (i + 1) % len(ref)
    return out


def _midrank(x: float, xs: list[float]) -> float:
    below = sum(1 for v in xs if v < x)
    equal = sum(1 for v in xs if v == x)
    return (below + 0.5 * equal) / len(xs)


def status_of(n: int, cum_pct: float, dd_pct: float) -> str:
    if n >= DRIFT_N and (cum_pct < DRIFT or dd_pct > 1 - DRIFT):
        return "décroché"
    if n < WATCH_N:
        return "trop tôt"
    if cum_pct < WATCH or dd_pct > 1 - WATCH:
        return "à surveiller"
    return "dans la norme"


def compare(ref: list[float], live: list[float], draws: int = DRAWS, seed: int = 7) -> dict[str, Any]:
    n = len(live)
    out: dict[str, Any] = {"n": n, "cum_r": round(sum(live), 4), "dd_r": round(max_drawdown(live), 4),
                           "ref_n": len(ref), "ref_mean_r": round(sum(ref) / len(ref), 4) if ref else None}
    if not n or len(ref) < 30:
        return out | {"status": "trop tôt", "cum_pct": None, "dd_pct": None}
    rng = random.Random(seed)
    sims = [resample(ref, n, rng) for _ in range(draws)]
    cums, dds = sorted(sum(s) for s in sims), sorted(max_drawdown(s) for s in sims)
    cum_pct, dd_pct = _midrank(sum(live), cums), _midrank(max_drawdown(live), dds)
    q = lambda xs, p: xs[min(len(xs) - 1, int(p * len(xs)))]  # noqa: E731
    return out | {"cum_pct": round(cum_pct, 4), "dd_pct": round(dd_pct, 4), "status": status_of(n, cum_pct, dd_pct),
                  "band": {"cum_p5": round(q(cums, 0.05), 3), "cum_p50": round(q(cums, 0.5), 3),
                           "cum_p95": round(q(cums, 0.95), 3), "dd_p95": round(q(dds, 0.95), 3)}}


def live_series(lab_shadow: dict[str, Any], signals: list) -> dict[str, list[float]]:
    """R nets Topstep des trades clos en ombre, dans l'ordre : laboratoire et variante horizon_3h_gold."""
    from .topstep_odds import r_from_signal
    out = {}
    for name, rec in lab_shadow.items():
        out[name] = [t["r_topstep"] for t in sorted(rec.get("trades", []), key=lambda t: t["entry_ts"])
                     if t.get("status") == "closed" and t.get("r_topstep") is not None]
    rows = sorted((s for s in signals if s.source == "shadow" and (s.meta or {}).get("variant") == VARIANT
                   and s.status in ("tp", "sl", "expired")), key=lambda s: s.created_at)
    out[VARIANT] = [r for r in (r_from_signal(s.to_dict()) for s in rows) if r is not None]
    return out


def _fmt_r(x: float) -> str:
    return f"{x:+.1f}".replace(".", ",").replace("-", "−") + " R"


def alert_text(name: str, res: dict[str, Any]) -> str:
    label = LABELS.get(name, name)
    why = []
    if res.get("cum_pct") is not None and res["cum_pct"] < WATCH:
        why.append(f"gain cumulé {_fmt_r(res['cum_r'])} : seuls {res['cum_pct'] * 100:.0f} % des tirages du backtest font pire")
    if res.get("dd_pct") is not None and res["dd_pct"] > 1 - WATCH:
        why.append(f"pire baisse {_fmt_r(-res['dd_r'])} : plus profonde que {res['dd_pct'] * 100:.0f} % des tirages")
    head = "🔴 Décrochage" if res["status"] == "décroché" else "🟠 À surveiller"
    end = ("La variante ne peut pas être promue tant que dure le décrochage."
           if name == VARIANT else "Stratégie en ombre seulement : aucun signal réel n'est concerné.")
    return (f"{head} : {label} (suivi en ombre)\n{res['n']} trades réels ; " + " ; ".join(why) + ".\n"
            "Cause possible : un avantage qui s'efface, des données différentes du backtest ou un bug, à "
            f"vérifier à la main. {end}")


def run(lab_shadow: dict[str, Any], signals: list, reference: dict[str, Any], previous: dict[str, Any],
        now: datetime | None = None, send=None) -> dict[str, Any] | None:
    """Recalcule l'état de chaque stratégie en ombre si un trade s'est clos ; envoie un message quand l'état
    s'aggrave. Renvoie le nouvel état (None : rien n'a changé)."""
    live = live_series(lab_shadow, signals)
    prev = previous.get("cells", {})
    if previous and all(prev.get(k, {}).get("n") == len(v) for k, v in live.items() if k in reference):
        return None
    cells = {}
    for name, rs in live.items():
        ref = (reference.get(name) or {}).get("rSeries")
        if not ref:
            continue
        res = compare(ref, rs) | {"label": LABELS.get(name, name), "ref_period": reference[name].get("period")}
        before = prev.get(name, {})
        if send and RANK[res["status"]] > RANK.get(before.get("status", "trop tôt"), 0):
            send(alert_text(name, res))
        res["since_status"] = before.get("since_status") if before.get("status") == res["status"] else iso(now or utcnow())
        cells[name] = res
    return {"updated_at": iso(now or utcnow()), "cells": cells}


def blocked(state: dict[str, Any]) -> set[str]:
    """Variantes dont la promotion est suspendue (décrochées)."""
    return {k for k, c in (state.get("cells") or {}).items() if k == VARIANT and c.get("status") == "décroché"}


def build_reference(store, cfg) -> dict[str, Any]:
    """R du backtest de 24 mois de chaque stratégie en ombre (historique long, gardé hors du dépôt)."""
    from . import strategies as sl
    from .backtest import run_backtest
    from .topstep import FEES, PRODUCTS
    from .topstep_odds import r_from_signal
    out: dict[str, Any] = {}
    for (strat, key), _since in sl.SHADOW.items():
        candles = store.load_history(key)
        if not candles:
            continue
        runner = sl.RUNNERS_1H.get(strat)
        trades = sorted(runner(candles, key), key=lambda t: t.entry_ts)
        trades = [t for t in trades if t.reason != "fin des données"]
        tcost = (sum(FEES[key]), PRODUCTS[key][1])
        out[f"{strat}:{key}"] = {"rSeries": [round(sl.trade_rs(t, 0.0, tcost)["net_topstep"], 4) for t in trades],
                                 "period": [iso(datetime.fromtimestamp(candles[0].ts, timezone.utc))[:10],
                                            iso(datetime.fromtimestamp(candles[-1].ts, timezone.utc))[:10]]}
    gold = store.load_history("gold")
    if gold:
        res = run_backtest(cfg.assets["gold"], gold, cfg, base_minutes=cfg.long_horizon_base_minutes)
        rows = sorted(res["trades"], key=lambda s: s["created_at"])
        out[VARIANT] = {"rSeries": [r for r in (r_from_signal(s) for s in rows) if r is not None],
                        "period": [rows[0]["created_at"][:10], rows[-1]["created_at"][:10]] if rows else None}
    return out | {"built_at": iso(utcnow())} if out else out
