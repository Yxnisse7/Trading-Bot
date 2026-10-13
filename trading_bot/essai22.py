"""Essai 22 (HYPOTHESES.md) : les autres contrôles de la vidéo sur les stratégies qu'on suit encore.

Plateau des réglages, centaines de trades, régimes de marché (hausse / baisse / plat), walk-forward (meilleur réglage
des 6 mois précédents joué sur les 3 mois suivants), frais doublés. Aucun réglage n'est changé : on regarde
seulement si le réglage actuel tient.

    python -m trading_bot.essai22          → data/essai22.json
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from itertools import product
from typing import Any, Callable

from . import essai14 as e14
from . import essai15 as e15
from . import strategies as sl
from .essai21 import bot_cost

MIN_TRADES = 30
WF_TRAIN, WF_TEST = 182 * 86400, 91 * 86400
REGIME_Z = 0.5

DONCHIAN_GRID = {"entry_n": (10, 15, 20, 25, 30), "exit_n": (5, 10, 15)}
GRIDS: dict[str, dict[str, tuple]] = {
    "donchian_day:gold": DONCHIAN_GRID, "donchian_1h:gold": DONCHIAN_GRID, "donchian_1h:bitcoin": DONCHIAN_GRID,
    "A1:gold": {"atr": (1.0, 1.25, 1.5, 1.75, 2.0)},
    "G40:gold": {"max_trades": (2, 3, 4, 5), "max_losses": (1, 2, 3)},
    "S25:nasdaq": {"lookback": (6, 8, 10, 12, 15), "window": (1, 2, 3)},
}
CURRENT = {"donchian_day:gold": (20, 10), "donchian_1h:gold": (20, 10), "donchian_1h:bitcoin": (20, 10),
           "A1:gold": (1.5,), "G40:gold": (3, 2), "S25:nasdaq": (10, 2)}


def trades_for(cell: str, params: tuple, ctx: e15.Ctx, base: list[sl.Trade]) -> list[sl.Trade]:
    name, asset = cell.split(":")
    if name in ("donchian_day", "donchian_1h"):
        return sl.donchian_1h(ctx.m5.c, asset, entry_n=params[0], exit_n=params[1], day_close=name == "donchian_day")
    if name == "A1":
        old, e14.A1_ATR = e14.A1_ATR, params[0]
        try:
            return [t for t in base if not e14.removed_by("A1", t, ctx, None)]
        finally:
            e14.A1_ATR = old
    if name == "G40":
        return e15.day_limits(base, params[0], params[1])
    if name == "S25":
        old = e15.S25_LOOKBACK, e15.S25_WINDOW
        e15.S25_LOOKBACK, e15.S25_WINDOW = params
        try:
            return e15.setup_trades("S25", asset, ctx)
        finally:
            e15.S25_LOOKBACK, e15.S25_WINDOW = old
    raise ValueError(cell)


def mean_r(trades: list[sl.Trade], cost: Callable[[float], float], mult: float = 1.0) -> float | None:
    rs = [(t.gross_points() - mult * cost(t.entry)) / t.risk for t in trades]
    return sum(rs) / len(rs) if rs else None


def neighbours(grid: dict[str, tuple], cur: tuple) -> list[tuple]:
    axes = list(grid.values())
    out = []
    for k, ax in enumerate(axes):
        i = ax.index(cur[k])
        for j in (i - 1, i + 1):
            if 0 <= j < len(ax):
                out.append(tuple(ax[j] if m == k else cur[m] for m in range(len(cur))))
    return out


def daily_closes(ctx: e15.Ctx) -> tuple[list, list[float]]:
    days: dict[Any, float] = {}
    for c in ctx.m5.c:
        days[datetime.fromtimestamp(c.ts, sl.NY).date()] = c.close
    keys = sorted(days)
    return keys, [days[k] for k in keys]


def regime(ts: int, keys: list, closes: list[float]) -> str | None:
    """Marché des 20 jours précédant l'entrée : rendement divisé par son agitation normale sur 20 jours."""
    d = datetime.fromtimestamp(ts, sl.NY).date()
    lo, hi = 0, len(keys)
    while lo < hi:                                   # jours strictement avant celui de l'entrée
        mid = (lo + hi) // 2
        if keys[mid] < d:
            lo = mid + 1
        else:
            hi = mid
    if lo < 21:
        return None
    c = closes[lo - 21:lo]
    rets = [math.log(c[i] / c[i - 1]) for i in range(1, 21)]
    m = sum(rets) / 20
    sd = math.sqrt(sum((r - m) ** 2 for r in rets) / 19) * math.sqrt(20)
    if sd <= 0:
        return None
    z = math.log(c[-1] / c[0]) / sd
    return "hausse" if z > REGIME_Z else "baisse" if z < -REGIME_Z else "plat"


def walk_forward(by_params: dict[tuple, list[sl.Trade]], cur: tuple, cost) -> dict[str, Any]:
    all_ts = [t.entry_ts for ts in by_params.values() for t in ts]
    if not all_ts:
        return {"n": 0}
    start, end = min(all_ts), max(all_ts)
    t0, oos, picks = start + WF_TRAIN, [], []
    while t0 < end:
        def score(p):
            tr = [t for t in by_params[p] if t0 - WF_TRAIN <= t.entry_ts < t0]
            return mean_r(tr, cost) if len(tr) >= 10 else None
        scored = [(s, p) for p in by_params if (s := score(p)) is not None]
        best = max(scored)[1] if scored else cur
        part = [t for t in by_params[best] if t0 <= t.entry_ts < t0 + WF_TEST]
        oos += part
        picks.append({"from": datetime.fromtimestamp(t0, timezone.utc).date().isoformat(), "params": list(best),
                      "n": len(part), "mean_r": None if not part else round(mean_r(part, cost), 4)})
        t0 += WF_TEST
    r = mean_r(oos, cost)
    return {"n": len(oos), "mean_r": None if r is None else round(r, 4), "windows": picks,
            "positive_windows": sum(1 for w in picks if (w["mean_r"] or 0) > 0)}


def check(cell: str, ctx: e15.Ctx, base: list[sl.Trade], cost) -> dict[str, Any]:
    grid, cur = GRIDS[cell], CURRENT[cell]
    by_params = {p: [t for t in trades_for(cell, p, ctx, base) if t.reason != "fin des données" and t.risk > 0]
                 for p in product(*grid.values())}
    table = {",".join(map(str, p)): {"n": len(tr), "mean_r": None if not tr else round(mean_r(tr, cost), 4)}
             for p, tr in by_params.items()}
    judged = [v for v in table.values() if v["n"] >= MIN_TRADES]
    wins = sum(1 for v in judged if v["mean_r"] > 0)
    nb = {",".join(map(str, p)): table[",".join(map(str, p))] for p in neighbours(grid, cur)}
    plateau = bool(judged) and wins >= 2 * len(judged) / 3 and all(
        v["n"] >= MIN_TRADES and v["mean_r"] > 0 for v in nb.values())
    trades = by_params[cur]
    keys, closes = daily_closes(ctx)
    reg: dict[str, list[sl.Trade]] = {"hausse": [], "baisse": [], "plat": []}
    for t in trades:
        g = regime(t.entry_ts, keys, closes)
        if g:
            reg[g].append(t)
    regimes = {k: {"n": len(v), "mean_r": None if not v else round(mean_r(v, cost), 4)} for k, v in reg.items()}
    counted = [v for v in regimes.values() if v["n"] >= MIN_TRADES]
    wf = walk_forward(by_params, cur, cost)
    fees2 = mean_r(trades, cost, 2.0)
    checks = {
        "plateau": plateau,
        "au moins 200 trades": len(trades) >= 200,
        "gagne dans 2 régimes": sum(1 for v in counted if v["mean_r"] > 0) >= 2,
        "walk-forward > 0": (wf.get("mean_r") or 0) > 0,
        "frais doublés > 0": (fees2 or 0) > 0,
    }
    return {"cell": cell, "current": list(cur), "n": len(trades), "mean_r": round(mean_r(trades, cost) or 0, 4),
            "grid": table, "grid_positive": f"{wins}/{len(judged)}", "neighbours": nb, "regimes": regimes,
            "walk_forward": wf, "fees_x2_mean_r": None if fees2 is None else round(fees2, 4),
            "checks": checks, "robust": all(checks.values())}


def run(store, cfg, log: Callable[[str], None] = print) -> dict[str, Any]:
    out: dict[str, Any] = {"essai": 22, "cells": {}}
    ctxs: dict[str, e15.Ctx] = {}
    for cell in GRIDS:
        asset = cell.split(":")[1]
        if asset not in ctxs:
            candles = store.load_history(asset)
            if not candles:
                continue
            ctxs[asset] = e15.Ctx(candles)
        ctx = ctxs[asset]
        rows = store._read(store.dir / "history" / f"essai14_bot_{asset}.json", None) or []
        base = e14.bot_trades(rows, asset)
        cost, _ = bot_cost(asset, cfg)
        v = check(cell, ctx, base, cost)
        out["cells"][cell] = v
        log(f"{cell:20s} n={v['n']:4d} {v['mean_r']:+.3f} R | grille {v['grid_positive']} voisins "
            f"{ {k: x['mean_r'] for k, x in v['neighbours'].items()} } | régimes "
            f"{ {k: (x['n'], x['mean_r']) for k, x in v['regimes'].items()} } | walk-forward {v['walk_forward'].get('mean_r')} "
            f"({v['walk_forward'].get('positive_windows')}/{len(v['walk_forward'].get('windows', []))} trimestres) | "
            f"frais ×2 {v['fees_x2_mean_r']} → {'ROBUSTE' if v['robust'] else [k for k, ok in v['checks'].items() if not ok]}")
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    out = run(eng.store, eng.cfg, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    eng.store._write(eng.store.dir / "essai22.json", out)


if __name__ == "__main__":
    main()
