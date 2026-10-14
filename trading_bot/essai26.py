"""Essai 26 (HYPOTHESES.md) : le bot appris par marché seul, par groupe d'indices, ou tous ensemble (DAX en plus).

Même modèle d'arbres et mêmes années cachées que l'essai 25 ; seules changent les lignes sur lesquelles chaque modèle
apprend. Le DAX est rejoué sur l'horloge européenne de l'essai 17 (bougies HistData 2014-2024 puis les nôtres).

    python -m trading_bot.essai26          → data/essai26.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable

import numpy as np

from . import essai14 as e14
from . import essai17 as e17
from . import essai24 as e24
from . import essai25 as e25
from .bot_model import features as _features
from .essai21 import Bars, judge
from .essai23 import load

ASSETS = ("gold", "nasdaq", "sp500", "dax", "bitcoin")
MODES = {
    "seul": [("gold",), ("nasdaq",), ("sp500",), ("dax",), ("bitcoin",)],
    "groupe indices": [("nasdaq", "sp500", "dax")],
    "tout ensemble": [ASSETS],
}


def features(row: dict[str, Any], key: str) -> list[float]:
    """Entrées de l'essai 25, avec l'actif codé sur les 5 marchés (le DAX compris)."""
    x = _features(row.get("criteria"), row.get("meta"), row["created_at"], row.get("score"), row["direction"], key)
    return x[:-4] + [1.0 if key == a else 0.0 for a in ASSETS]


def dax_rows(store, cfg, root: Path, log: Callable[[str], None]) -> tuple[list, list, Callable[[float], float]]:
    """Signaux du bot sur le DAX 2014-2026 (horloge européenne), bougies transposées, frais du bot en %."""
    from .backtest import run_backtest
    e17.enable_european_sessions()
    acfg = e17.asset_config(cfg, "dax")
    new = store.load_history("dax")
    real = [c for c in load(root / "history" / "long" / "dax_5m.json") if c.ts < new[0].ts] + new
    candles = e17.remap(real)
    start = datetime.fromtimestamp(e17.remap(new[:1])[0].ts, timezone.utc).isoformat().replace("+00:00", "Z")
    cache = root / "history" / "long" / "essai26_bot_dax.json"
    if cache.exists():
        rows = json.loads(cache.read_text(encoding="utf-8"))
    else:
        log("bot rejoué sur le DAX 2014-2024…")
        rows = run_backtest(acfg, [c for c in candles if c.ts < e17.remap(new[:1])[0].ts], cfg)["trades"]
        cache.write_text(json.dumps(rows), encoding="utf-8")
    rows = [r for r in rows if r["created_at"] < start]
    recent = store._read(root / "history" / "essai17_bot_dax.json", None)
    if recent is None:
        recent = run_backtest(acfg, e17.remap(new), cfg)["trades"]
        store._write(root / "history" / "essai17_bot_dax.json", recent)
    rows += recent
    pct = acfg.cost_pct
    return rows, candles, (lambda e: pct / 100 * e)


def dataset(store, cfg, root: Path, log) -> dict[str, Any]:
    base = e25.dataset(store, cfg, root)
    data: dict[str, Any] = {"candles": dict(base["candles"]), "costs": {}, "rows": []}
    for key in e25.ASSETS:
        data["costs"][key] = e25.bot_cost(key, cfg)[0]
    # mêmes lignes que l'essai 25, entrées recalculées avec le DAX dans le codage de l'actif
    raw: dict[tuple[str, int], dict] = {}
    for key in e25.ASSETS:
        new = store.load_history(key)
        start = datetime.fromtimestamp(new[0].ts, timezone.utc).isoformat().replace("+00:00", "Z")
        rows = [r for r in json.loads((root / "history" / "long" / f"essai23_bot_{key}.json").read_text(encoding="utf-8"))
                if r["created_at"] < start]
        rows += store._read(root / "history" / f"essai14_bot_{key}.json", None) or []
        for r in rows:
            tr = e14.bot_trades([r], key)
            if tr:
                raw[(key, tr[0].entry_ts)] = r
    for key, t, _, rr in base["rows"]:
        data["rows"].append((key, t, features(raw[(key, t.entry_ts)], key), rr))
    rows, candles, cost = dax_rows(store, cfg, root, log)
    data["candles"]["dax"], data["costs"]["dax"] = candles, cost
    for r in rows:
        tr = e14.bot_trades([r], "dax")
        if not tr or tr[0].reason == "fin des données":
            continue
        t = tr[0]
        data["rows"].append(("dax", t, features(r, "dax"), (t.gross_points() - cost(t.entry)) / t.risk))
    data["rows"].sort(key=lambda z: z[1].entry_ts)
    return data


def correlations(candles: dict[str, list]) -> dict[str, dict[str, float]]:
    """Corrélation des rendements journaliers (clôture du jour UTC), 2014-2026."""
    daily = {}
    for k, cs in candles.items():
        last: dict[str, float] = {}
        for c in cs:
            last[datetime.fromtimestamp(c.ts, timezone.utc).date().isoformat()] = c.close
        days = sorted(last)
        daily[k] = {d: last[d] / last[p] - 1 for p, d in zip(days, days[1:])}
    out: dict[str, dict[str, float]] = {}
    for a in candles:
        out[a] = {}
        for b in candles:
            common = sorted(set(daily[a]) & set(daily[b]))
            x, y = np.array([daily[a][d] for d in common]), np.array([daily[b][d] for d in common])
            out[a][b] = round(float(np.corrcoef(x, y)[0, 1]), 2)
    return out


def run(store, cfg, root: Path, log: Callable[[str], None] = print) -> dict[str, Any]:
    data = dataset(store, cfg, root, log)
    rows = data["rows"]
    years = np.array([datetime.fromtimestamp(t.entry_ts, timezone.utc).year for _, t, _, _ in rows])
    rs = np.array([r for _, _, _, r in rows])
    assets = np.array([k for k, _, _, _ in rows])
    oos = years >= e25.FIRST_TEST_YEAR
    out: dict[str, Any] = {"essai": 26, "n_rows": len(rows), "cells": {}, "baseline": {},
                           "correlations": correlations(data["candles"])}
    for key in ASSETS:
        sel = oos & (assets == key)
        out["baseline"][key] = {"n": int(sel.sum()), "mean_r": round(float(rs[sel].mean()), 4)}
        log(f"bot seul {key:8s} 2017-2026 n={int(sel.sum())} {rs[sel].mean():+.4f} R")
    make = e25.models()["arbres"]
    old_half = e24.HALF
    e24.HALF = e25.HALF
    try:
        for mode, groups in MODES.items():
            for group in groups:
                idx = np.flatnonzero(np.isin(assets, group))
                pred_sub, _ = e25.walk_forward([rows[i] for i in idx], make)
                pred = np.full(len(rows), np.nan)
                pred[idx] = pred_sub
                for key in group:
                    pool = np.flatnonzero(oos & (assets == key))
                    kept = pool[pred[pool] > 0]
                    trades = [rows[i][1] for i in kept]
                    cost, candles = data["costs"][key], data["candles"][key]
                    closes = {}
                    for c in candles:
                        closes[datetime.fromtimestamp(c.ts, e24.sl.NY).date()] = c.close
                    keys = sorted(closes)
                    v = e24.checks(trades, cost, keys, [closes[k] for k in keys],
                                   datetime.fromtimestamp(candles[-1].ts, timezone.utc).year)
                    if len(kept) >= 30:
                        m = judge(f"essai26_{mode}", key, trades, Bars(candles), cost)
                        fm = e25.year_monkeys(kept, pool, rs, years, f"essai26:{mode}:{key}")
                    else:
                        m, fm = {}, {"beaten": None, "z": None}
                    a = m.get("all") or {}
                    v["monkeys"] = {"beaten": a.get("beaten"), "z": a.get("z")}
                    v["filter_monkeys"] = fm
                    v["checks"]["singes"] = (a.get("beaten") or 0) >= 950
                    v["checks"]["filtres au hasard"] = (fm.get("beaten") or 0) >= 950
                    v.update({"mode": mode, "asset": key, "kept_share": round(len(kept) / max(1, len(pool)), 3),
                              "robust": all(v["checks"].values())})
                    out["cells"][f"{mode}:{key}"] = v
                    failed = [k for k, ok in v["checks"].items() if not ok]
                    log(f"{mode:14s} {key:8s} garde {len(kept):5d}/{len(pool)} {v['mean_r']} PF {v['profit_factor']} "
                        f"années {v['positive_years']} 2017-21 {v['before_2020']} 2022+ {v['since_2020']} "
                        f"récent {v['last_2_years']} singes {a.get('beaten')} filtres {fm.get('beaten')} z {fm.get('z')} → "
                        f"{'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")
    finally:
        e24.HALF = old_half
    z_thr = NormalDist().inv_cdf(1 - 0.05 / max(1, len(out["cells"])))
    out["z_threshold"] = round(z_thr, 2)
    for v in out["cells"].values():
        v["status"] = ("prouvé" if v["robust"] and (v["filter_monkeys"].get("z") or 0) > z_thr
                       else "robuste" if v["robust"] else "pas robuste")
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    out = run(eng.store, eng.cfg, eng.store.dir, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    for k, v in out["cells"].items():
        print(f"{k:24s} {v['status']}", flush=True)
    print(json.dumps(out["correlations"]), flush=True)
    eng.store._write(eng.store.dir / "essai26.json", out)


if __name__ == "__main__":
    main()
