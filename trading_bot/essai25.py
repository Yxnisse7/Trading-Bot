"""Essai 25 (HYPOTHESES.md) : faire apprendre le bot principal sur 2014-2026, jugé sur des années cachées.

Chaque signal du bot rejoué (essais 23 et 14) devient une ligne : ce que le bot voyait à l'entrée → R net du trade.
Pour chaque année de 2017 à 2026, le modèle apprend sur les années d'avant seulement, puis garde, dans l'année
suivante qu'il n'a jamais vue, les signaux dont le R prévu est > 0.

    python -m trading_bot.essai25          → data/essai25.json
"""
from __future__ import annotations

import json
import zlib
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable

import numpy as np

from . import essai14 as e14
from . import essai22 as e22
from . import essai24 as e24
from .essai21 import Bars, bot_cost, judge
from .essai23 import load

from .bot_model import ASSETS, CRITERIA, CTX
from .bot_model import features as _features

FIRST_TEST_YEAR = 2017
HALF = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp())
N_MONKEYS = 1000


def features(row: dict[str, Any], key: str) -> list[float]:
    return _features(row.get("criteria"), row.get("meta"), row["created_at"], row.get("score"), row["direction"], key)


def dataset(store, cfg, root: Path) -> dict[str, Any]:
    """Lignes (actif, trade, entrées, R net), et les bougies 2014-2026 de chaque actif."""
    out: dict[str, Any] = {"rows": [], "candles": {}}
    for key in ASSETS:
        new = store.load_history(key)
        out["candles"][key] = [c for c in load(root / "history" / "long" / f"{key}_5m.json") if c.ts < new[0].ts] + new
        start = datetime.fromtimestamp(new[0].ts, timezone.utc).isoformat().replace("+00:00", "Z")
        rows = [r for r in json.loads((root / "history" / "long" / f"essai23_bot_{key}.json").read_text(encoding="utf-8"))
                if r["created_at"] < start]
        rows += store._read(root / "history" / f"essai14_bot_{key}.json", None) or []
        cost, _ = bot_cost(key, cfg)
        for r in rows:
            tr = e14.bot_trades([r], key)
            if not tr or tr[0].reason == "fin des données":
                continue
            t = tr[0]
            out["rows"].append((key, t, features(r, key), (t.gross_points() - cost(t.entry)) / t.risk))
    out["rows"].sort(key=lambda z: z[1].entry_ts)
    return out


def models() -> dict[str, Callable[[], Any]]:
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return {"poids": lambda: make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
            "arbres": lambda: HistGradientBoostingRegressor(max_iter=200, max_depth=3, learning_rate=0.05,
                                                            random_state=0)}


def walk_forward(rows, make) -> tuple[np.ndarray, dict[int, Any]]:
    """R prévu pour chaque ligne d'une année ≥ 2017, avec un modèle qui n'a vu que les années d'avant."""
    years = np.array([datetime.fromtimestamp(t.entry_ts, timezone.utc).year for _, t, _, _ in rows])
    X = np.array([x for _, _, x, _ in rows], dtype=float)
    y = np.array([r for _, _, _, r in rows], dtype=float)
    pred = np.full(len(rows), np.nan)
    fitted = {}
    for yr in range(FIRST_TEST_YEAR, int(years.max()) + 1):
        tr, te = years < yr, years == yr
        if not te.any() or not tr.any():
            continue
        m = make()
        m.fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
        fitted[yr] = m
    return pred, fitted


def year_monkeys(kept_idx: np.ndarray, pool_idx: np.ndarray, rs: np.ndarray, years: np.ndarray, seed: str) -> dict:
    """Filtres au hasard : chaque année, autant de signaux tirés au hasard parmi ceux du bot que le modèle en garde."""
    rng = np.random.default_rng(zlib.crc32(seed.encode()))
    real = float(rs[kept_idx].mean())
    sums, n = np.zeros(N_MONKEYS), len(kept_idx)
    for yr in np.unique(years[kept_idx]):
        k = int((years[kept_idx] == yr).sum())
        pool = pool_idx[years[pool_idx] == yr]
        picks = np.argsort(rng.random((N_MONKEYS, len(pool))), axis=1)[:, :k]
        sums += rs[pool][picks].sum(1)
    means = sums / n
    sd = float(means.std(ddof=1))
    return {"real_r": round(real, 4), "monkeys_r": round(float(means.mean()), 4),
            "beaten": int((means < real).sum()), "z": round((real - float(means.mean())) / sd, 2) if sd > 0 else None}


def run(store, cfg, root: Path, log: Callable[[str], None] = print) -> dict[str, Any]:
    data = dataset(store, cfg, root)
    rows = data["rows"]
    years = np.array([datetime.fromtimestamp(t.entry_ts, timezone.utc).year for _, t, _, _ in rows])
    rs = np.array([r for _, _, _, r in rows])
    assets = np.array([k for k, _, _, _ in rows])
    out: dict[str, Any] = {"essai": 25, "n_rows": len(rows), "cells": {}, "baseline": {}}
    oos = years >= FIRST_TEST_YEAR
    for key in ASSETS:
        sel = oos & (assets == key)
        out["baseline"][key] = {"n": int(sel.sum()), "mean_r": round(float(rs[sel].mean()), 4)}
        log(f"bot seul {key:8s} 2017-2026 n={int(sel.sum())} {rs[sel].mean():+.4f} R")
    old_half = e24.HALF
    e24.HALF = HALF
    try:
        for mname, make in models().items():
            pred, fitted = walk_forward(rows, make)
            for key in ASSETS:
                pool = np.flatnonzero(oos & (assets == key))
                kept = pool[pred[pool] > 0]
                trades = [rows[i][1] for i in kept]
                cost, label = bot_cost(key, cfg)
                candles = data["candles"][key]
                closes = {}
                for c in candles:
                    closes[datetime.fromtimestamp(c.ts, e24.sl.NY).date()] = c.close
                keys = sorted(closes)
                v = e24.checks(trades, cost, keys, [closes[k] for k in keys],
                               datetime.fromtimestamp(candles[-1].ts, timezone.utc).year)
                if len(kept) >= 30:
                    m = judge(f"essai25_{mname}", key, trades, Bars(candles), cost)
                    fm = year_monkeys(kept, pool, rs, years, f"essai25:{mname}:{key}")
                else:
                    m, fm = {}, {"beaten": None, "z": None}
                a = m.get("all") or {}
                v["monkeys"] = {"beaten": a.get("beaten"), "z": a.get("z")}
                v["filter_monkeys"] = fm
                v["checks"]["singes"] = (a.get("beaten") or 0) >= 950
                v["checks"]["filtres au hasard"] = (fm.get("beaten") or 0) >= 950
                v.update({"model": mname, "asset": key, "fees": label, "kept_share": round(len(kept) / max(1, len(pool)), 3),
                          "robust": all(v["checks"].values())})
                out["cells"][f"{mname}:{key}"] = v
                failed = [k for k, ok in v["checks"].items() if not ok]
                log(f"{mname:7s} {key:8s} garde {len(kept):5d}/{len(pool)} {v['mean_r']} PF {v['profit_factor']} années "
                    f"{v['positive_years']} 2017-21 {v['before_2020']} 2022+ {v['since_2020']} récent {v['last_2_years']} "
                    f"singes {a.get('beaten')} filtres {fm.get('beaten')} → {'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")
            if mname == "poids" and fitted:
                last = fitted[max(fitted)]
                coef = last.named_steps["ridge"].coef_
                names = list(CRITERIA) + [f"ctx_{k}" for k in CTX] + ["ctx_présent", "score", "sens", "heure_sin",
                                                                       "heure_cos"] + [f"actif_{a}" for a in ASSETS]
                out["weights_last_year"] = {n: round(float(c), 4) for n, c in sorted(zip(names, coef), key=lambda z: -abs(z[1]))}
    finally:
        e24.HALF = old_half
    z_thr = NormalDist().inv_cdf(1 - 0.05 / max(1, len(out["cells"])))
    out["z_threshold"] = round(z_thr, 2)
    for v in out["cells"].values():
        v["status"] = ("prouvé" if v["robust"] and (v["filter_monkeys"].get("z") or 0) > z_thr
                       else "robuste" if v["robust"] else "pas robuste")
    return out


def train_final(store, cfg, root: Path) -> dict[str, Any]:
    """Modèle d'arbres de l'essai 25 entraîné sur tous les signaux 2014-2026, pour le bot en direct."""
    import pickle

    import sklearn

    from .bot_model import PATH
    rows = dataset(store, cfg, root)["rows"]
    m = models()["arbres"]()
    m.fit(np.array([x for _, _, x, _ in rows], dtype=float), np.array([r for _, _, _, r in rows], dtype=float))
    info = {"n_rows": len(rows), "sklearn": sklearn.__version__,
            "last_entry": datetime.fromtimestamp(rows[-1][1].entry_ts, timezone.utc).isoformat()}
    PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PATH, "wb") as f:
        pickle.dump({"model": m, **info}, f)
    return info


def main() -> None:
    import sys

    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    if "--train" in sys.argv:
        print(train_final(eng.store, eng.cfg, eng.store.dir))
        return
    out = run(eng.store, eng.cfg, eng.store.dir, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    for k, v in out["cells"].items():
        print(f"{k:20s} {v['status']}", flush=True)
    eng.store._write(eng.store.dir / "essai25.json", out)


if __name__ == "__main__":
    main()
