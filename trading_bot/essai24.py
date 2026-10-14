"""Essai 24 (HYPOTHESES.md) : les 54 stratégies sur 2014-2026 d'un seul bloc, avec tous les contrôles à la fois.

Bougies : data/history/long/<actif>_5m.json (essai 23) suivies de data/history/<actif>_5m.json. Bot : trades rejoués
des essais 23 et 14 mis bout à bout.

    python -m trading_bot.essai24          → data/essai24.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable

from . import essai14 as e14
from . import essai15 as e15
from . import essai17 as e17
from . import essai22 as e22
from . import strategies as sl
from .essai21 import FILTER_CELLS, Bars, bot_cost, judge, real_rs
from .essai23 import load

ASSETS = ("gold", "nasdaq", "sp500", "bitcoin")
MIN_TRADES = 200
HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
RECENT = int(datetime(2024, 10, 14, tzinfo=timezone.utc).timestamp())
GRID_NAMES = ("donchian_day", "donchian_1h", "A1", "G40", "S25")


def _mean(xs) -> float | None:
    xs = list(xs)
    return float(sum(xs) / len(xs)) if xs else None


def checks(trades: list[sl.Trade], cost, keys, closes, last_year: int) -> dict[str, Any]:
    """Contrôles 1 à 7 sur les trades d'une cellule (déjà triés, sans « fin des données »)."""
    rs = [float(x) for x in real_rs(trades, cost)] if trades else []
    n = len(rs)
    mean = _mean(rs)
    gains, losses = sum(x for x in rs if x > 0), -sum(x for x in rs if x < 0)
    pf = gains / losses if losses > 0 else None
    years: dict[int, list[float]] = {}
    for t, r in zip(trades, rs):
        years.setdefault(datetime.fromtimestamp(t.entry_ts, timezone.utc).year, []).append(r)
    first_year = min(years) if years else 0
    full = {y: v for y, v in years.items() if first_year < y < last_year or (y == first_year == 2014)}
    pos = sum(1 for v in full.values() if sum(v) > 0)
    before = _mean(r for t, r in zip(trades, rs) if t.entry_ts < HALF)
    after = _mean(r for t, r in zip(trades, rs) if t.entry_ts >= HALF)
    recent = _mean(r for t, r in zip(trades, rs) if t.entry_ts >= RECENT)
    fees2 = _mean((t.gross_points() - 2 * cost(t.entry)) / t.risk for t in trades)
    reg: dict[str, list[float]] = {"hausse": [], "baisse": [], "plat": []}
    for t, r in zip(trades, rs):
        g = e22.regime(t.entry_ts, keys, closes)
        if g:
            reg[g].append(r)
    regimes = {k: {"n": len(v), "mean_r": None if not v else round(sum(v) / len(v), 4)} for k, v in reg.items()}
    c = {
        "200 trades": n >= MIN_TRADES,
        "R > 0 et PF ≥ 1,1": (mean or 0) > 0 and (pf or 0) >= 1.1,
        "60 % des années": bool(full) and pos >= 0.6 * len(full),
        "deux moitiés": (before or 0) > 0 and (after or 0) > 0,
        "2 dernières années": (recent or 0) > 0,
        "frais doublés": (fees2 or 0) > 0,
        "2 régimes sur 3": sum(1 for v in regimes.values() if v["n"] >= 30 and v["mean_r"] > 0) >= 2,
    }
    r4 = lambda x: None if x is None else round(x, 4)          # noqa: E731
    return {"n": n, "mean_r": r4(mean), "profit_factor": None if pf is None else round(pf, 2),
            "positive_years": f"{pos}/{len(full)}",
            "years": {str(y): round(sum(v) / len(v), 4) for y, v in sorted(years.items())},
            "before_2020": r4(before), "since_2020": r4(after), "last_2_years": r4(recent), "fees_x2": r4(fees2),
            "regimes": regimes, "checks": c}


def run(store, cfg, root: Path, log: Callable[[str], None] = print) -> dict[str, Any]:
    out: dict[str, Any] = {"essai": 24, "cells": {}}
    for key in ASSETS:
        old = load(root / "history" / "long" / f"{key}_5m.json")
        new = store.load_history(key)
        real = [c for c in old if c.ts < new[0].ts] + new
        ctx = e15.Ctx(real)
        other = None
        if key in ("nasdaq", "sp500"):
            ok = "sp500" if key == "nasdaq" else "nasdaq"
            o_new = store.load_history(ok)
            other = e15.Ctx([c for c in load(root / "history" / "long" / f"{ok}_5m.json") if c.ts < o_new[0].ts] + o_new)
        rows = json.loads((root / "history" / "long" / f"essai23_bot_{key}.json").read_text(encoding="utf-8"))
        start = datetime.fromtimestamp(new[0].ts, timezone.utc).isoformat()
        rows = [r for r in rows if r["created_at"] < start.replace("+00:00", "Z")]
        rows += store._read(root / "history" / f"essai14_bot_{key}.json", None) or []
        base = sorted(e14.bot_trades(rows, key), key=lambda t: t.entry_ts)
        cost, label = bot_cost(key, cfg)
        bars = Bars(real)
        keys, closes = e22.daily_closes(ctx)
        last_year = datetime.fromtimestamp(real[-1].ts, timezone.utc).year
        for name, trades in e17.cells(key, real, real, ctx, other, base, cfg.assets[key].cost_pct):
            trades = sorted((t for t in trades if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
            v = checks(trades, cost, keys, closes, last_year)
            m = judge(name, key, trades, bars, cost, base)
            a, f = m.get("all") or {}, m.get("filter_monkeys")
            v["monkeys"] = {"beaten": a.get("beaten"), "z": a.get("z"),
                            "filter_beaten": None if f is None else f.get("beaten")}
            v["checks"]["singes"] = (a.get("beaten") or 0) >= 950 and (
                name not in FILTER_CELLS or f is None or f.get("beaten", 0) >= 950)
            if name in GRID_NAMES:
                cell = f"{name}:{key}"
                grid = e22.DONCHIAN_GRID if name.startswith("donchian") else e22.GRIDS[f"{name}:" + {
                    "A1": "gold", "G40": "gold", "S25": "nasdaq"}[name]]
                cur = (20, 10) if name.startswith("donchian") else e22.CURRENT[f"{name}:" + {
                    "A1": "gold", "G40": "gold", "S25": "nasdaq"}[name]]
                e22.GRIDS.setdefault(cell, grid)
                e22.CURRENT.setdefault(cell, cur)
                g = e22.check(cell, ctx, base, cost)
                v["grid"] = {"positive": g["grid_positive"], "neighbours": g["neighbours"],
                             "walk_forward": {k: g["walk_forward"].get(k) for k in ("n", "mean_r", "positive_windows")}}
                v["checks"]["plateau"] = g["checks"]["plateau"]
                v["checks"]["walk-forward"] = g["checks"]["walk-forward > 0"]
            v.update({"idea": name, "asset": key, "fees": label, "robust": all(v["checks"].values())})
            out["cells"][f"{name}:{key}"] = v
            log(line(v))
    judged = [v for v in out["cells"].values() if v["monkeys"]["z"] is not None]
    z_thr = NormalDist().inv_cdf(1 - 0.05 / max(1, len(judged)))
    out["z_threshold"] = round(z_thr, 2)
    for v in out["cells"].values():
        v["status"] = ("prouvée" if v["robust"] and (v["monkeys"]["z"] or 0) > z_thr
                       else "robuste" if v["robust"] else "pas robuste")
    return out


def line(v: dict[str, Any]) -> str:
    failed = [k for k, ok in v["checks"].items() if not ok]
    return (f"{v['idea']:17s} {v['asset']:8s} n={v['n']:5d} {v['mean_r']} PF {v['profit_factor']} années "
            f"{v['positive_years']} 2014-19 {v['before_2020']} 2020+ {v['since_2020']} récent {v['last_2_years']} "
            f"singes {v['monkeys']['beaten']} → {'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    out = run(eng.store, eng.cfg, eng.store.dir, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    for k, v in out["cells"].items():
        if v["status"] != "pas robuste":
            print(f"{k:28s} {v['status']}", flush=True)
    eng.store._write(eng.store.dir / "essai24.json", out)


if __name__ == "__main__":
    main()
