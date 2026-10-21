"""Essai 42 (HYPOTHESES.md) : le bot classique Nasdaq rejoué comme en réel, et son filtre modèle revérifié.

Point 1 de la relecture Perplexity (21/10/2026) : l'ancien backtest jugeait chaque signal sur 1 h (le Nasdaq tient
24 h depuis l'essai 29) et connaissait trop tôt l'issue des signaux pour la politique. `backtest.run_backtest` est
corrigé ; on rejoue le Nasdaq 2014-2026 et on regarde si le filtre de l'essai 26 (groupe indices, appris sur les
anciennes lignes) tient encore sur les trades réellement joués.

    python -m trading_bot.essai42          → data/essai42.json
    python -m trading_bot.essai42 b        → data/essai42b.json (42 b : stop sauté par un trou compté au vrai prix)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable

import numpy as np

from . import essai14 as e14
from . import essai24 as e24
from . import essai25 as e25
from . import essai26 as e26
from .essai21 import Bars, judge

KEY = "nasdaq"
SUFFIX = ""
GROUP = e26.MODES["groupe indices"][0]


def new_rows(store, cfg, root: Path, candles, log: Callable[[str], None]) -> list[dict[str, Any]]:
    from .backtest import run_backtest
    cache = root / "history" / "long" / f"essai42{SUFFIX}_bot_nasdaq.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    log("bot Nasdaq rejoué 2014-2026 avec le backtest corrigé…")
    rows = run_backtest(cfg.assets[KEY], candles, cfg)["trades"]
    cache.write_text(json.dumps(rows), encoding="utf-8")
    return rows


def run(store, cfg, root: Path, log: Callable[[str], None] = print) -> dict[str, Any]:
    data = e26.dataset(store, cfg, root, log)
    candles, cost = data["candles"][KEY], data["costs"][KEY]
    old = data["rows"]
    new = []
    for r in new_rows(store, cfg, root, candles, log):
        tr = e14.bot_trades([r], KEY)
        if tr and r.get("closed_at") and int(datetime.fromisoformat(r["closed_at"].replace("Z", "+00:00")).timestamp()) \
                < candles[-1].ts:
            t = tr[0]
            new.append((KEY, t, e26.features(r, KEY), (t.gross_points() - cost(t.entry)) / t.risk))
    new.sort(key=lambda z: z[1].entry_ts)

    def year(t) -> int:
        return datetime.fromtimestamp(t.entry_ts, timezone.utc).year

    o_years = np.array([year(t) for _, t, _, _ in old])
    o_assets = np.array([k for k, _, _, _ in old])
    n_years = np.array([year(t) for _, t, _, _ in new])
    n_rs = np.array([r for _, _, _, r in new])
    n_oos = np.flatnonzero(n_years >= e25.FIRST_TEST_YEAR)
    make = e25.models()["arbres"]

    # N2 : modèle « groupe indices » appris sur les anciennes lignes (années d'avant), appliqué aux nouvelles
    g = np.flatnonzero(np.isin(o_assets, GROUP))
    Xo = np.array([old[i][2] for i in g], dtype=float)
    yo = np.array([old[i][3] for i in g], dtype=float)
    Xn = np.array([x for _, _, x, _ in new], dtype=float)
    pred_old = np.full(len(new), np.nan)
    for yr in range(e25.FIRST_TEST_YEAR, int(n_years.max()) + 1):
        tr, te = o_years[g] < yr, n_years == yr
        if tr.any() and te.any():
            m = make()
            m.fit(Xo[tr], yo[tr])
            pred_old[te] = m.predict(Xn[te])
    # N3 : modèle appris sur les nouvelles lignes Nasdaq seules
    pred_new, _ = e25.walk_forward(new, make)

    o_oos = np.flatnonzero((o_assets == KEY) & (o_years >= e25.FIRST_TEST_YEAR))
    cells = {
        "N0 ancien rejeu (sortie 1 h), brut": ([old[i][1] for i in o_oos], None),
        "N1 nouveau rejeu (comme en réel), brut": ([new[i][1] for i in n_oos], None),
        "N2 nouveau rejeu + filtre actuel (appris sur l'ancien)": (None, n_oos[pred_old[n_oos] > 0]),
        "N3 nouveau rejeu + filtre réappris sur le nouveau": (None, n_oos[pred_new[n_oos] > 0]),
    }
    closes = {}
    for c in candles:
        closes[datetime.fromtimestamp(c.ts, e24.sl.NY).date()] = c.close
    keys = sorted(closes)
    last_year = datetime.fromtimestamp(candles[-1].ts, timezone.utc).year
    out: dict[str, Any] = {"essai": f"42{SUFFIX}", "asset": KEY, "n_old": int(len(o_oos)), "n_new": int(len(n_oos)), "cells": {}}
    old_half = e24.HALF
    e24.HALF = e25.HALF
    try:
        for name, (trades, kept) in cells.items():
            if kept is not None:
                trades = [new[i][1] for i in kept]
            trades = sorted(trades, key=lambda t: t.entry_ts)
            v = e24.checks(trades, cost, keys, [closes[k] for k in keys], last_year)
            m = judge(f"essai42_{name[:2]}", KEY, trades, Bars(candles), cost) if len(trades) >= 30 else {}
            a = m.get("all") or {}
            v["monkeys"] = {"beaten": a.get("beaten"), "z": a.get("z")}
            v["checks"]["singes"] = (a.get("beaten") or 0) >= 950
            if kept is not None:
                fm = e25.year_monkeys(kept, n_oos, n_rs, n_years, f"essai42:{name[:2]}") if len(kept) >= 30 else \
                    {"beaten": None, "z": None}
                v["filter_monkeys"] = fm
                v["checks"]["filtres au hasard"] = (fm.get("beaten") or 0) >= 950
                v["kept_share"] = round(len(kept) / max(1, len(n_oos)), 3)
            v["mean_minutes"] = round(float(np.mean([(t.exit_ts - t.entry_ts) / 60 for t in trades])), 1) if trades \
                else None
            v["robust"] = all(v["checks"].values())
            out["cells"][name] = v
            failed = [k for k, ok in v["checks"].items() if not ok]
            log(f"{name:55s} n={v['n']:5d} {v['mean_r']} R PF {v['profit_factor']} années {v['positive_years']} "
                f"durée {v['mean_minutes']} min singes {a.get('beaten')} filtres {(v.get('filter_monkeys') or {}).get('beaten')} "
                f"→ {'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")
    finally:
        e24.HALF = old_half
    z_thr = NormalDist().inv_cdf(1 - 0.05 / len(out["cells"]))
    out["z_threshold"] = round(z_thr, 2)
    for v in out["cells"].values():
        z = (v.get("filter_monkeys") or v["monkeys"]).get("z") or 0
        v["status"] = "prouvé" if v["robust"] and z > z_thr else "robuste" if v["robust"] else "pas robuste"
    return out


def main() -> None:
    import sys
    global SUFFIX
    SUFFIX = "".join(sys.argv[1:2])
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    out = run(eng.store, eng.cfg, eng.store.dir, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    for k, v in out["cells"].items():
        print(f"{k:55s} {v['status']}", flush=True)
    eng.store._write(eng.store.dir / f"essai42{SUFFIX}.json", out)


if __name__ == "__main__":
    main()
