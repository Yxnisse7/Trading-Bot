"""Page « Labo » du site : courbes des stratégies testées (résultat cumulé avec et sans frais, creux, années, singes).

Rejoue les trades sur les bougies longues (data/history/long, essai 23) et écrit des fichiers légers pour le site :
docs/labo/index.json (liste et mini-courbes) et docs/labo/cells/<id>.json (détail d'une cellule).

    python -m trading_bot.labo            → réel + essai 32 + essai 24
    python -m trading_bot.labo --only reel
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np

from . import essai15 as e15
from . import essai17 as e17
from . import essai32 as e32
from . import strategies as sl
from .essai21 import Bars, bot_cost, monkey_rs

N_POINTS = 240          # points gardés par courbe
N_SPARK = 40
N_MONKEYS = 500         # singes pour l'éventail (essai 21 : 1 000 pour le verdict)
NAMES = {"bot": "Bot classique", "noise_area": "Zone de bruit", "noise_area_v2": "Zone de bruit v2", "donchian_1h": "Donchian 1 h",
         "swing_w3": "Repli W3", "cassure_williams": "Cassure Williams", "nuit_asie": "Nuit asiatique", "creux_repris_15m": "Creux repris",
         "donchian_day": "Donchian jour", "double7": "Double 7"}
ASSET_NAMES = {"gold": "Or", "nasdaq": "Nasdaq 100", "sp500": "S&P 500", "bitcoin": "Bitcoin", "ethereum": "Ethereum",
               "oil": "Pétrole", "euro": "Euro / dollar", "dax": "DAX"}
LIVE = [("noise_area", "nasdaq", "prouvée à l'essai 24, en réel depuis le 14/10"),
        ("noise_area_v2", "nasdaq", "prouvée à l'essai 24, en réel depuis le 14/10"),
        ("donchian_1h", "bitcoin", "prouvée à l'essai 24, en réel depuis le 14/10"),
        ("swing_w3", "bitcoin", "prouvée à l'essai 24, en réel depuis le 14/10"),
        ("cassure_williams", "bitcoin", "prouvée à l'essai 30, en réel depuis le 14/10"),
        ("nuit_asie", "gold", "prouvée à l'essai 27, en réel depuis le 14/10"),
        ("bot", "nasdaq", "en réel avec les sorties de l'essai 29 (stop × 1,5, objectif 3, 24 h)")]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def pick(n: int, k: int) -> np.ndarray:
    return np.unique(np.linspace(0, n - 1, min(n, k)).round().astype(int)) if n else np.array([], dtype=int)


def r2(a) -> list[float]:
    return [round(float(x), 2) for x in a]


def series(trades: list[sl.Trade], cost: Callable[[float], float]) -> tuple[np.ndarray, np.ndarray]:
    gross = np.array([t.gross_points() / t.risk for t in trades])
    net = np.array([(t.gross_points() - cost(t.entry)) / t.risk for t in trades])
    return net, gross


def describe(cell_id: str, group: str, title: str, asset: str, trades: list[sl.Trade], cost, *, verdict: str, note: str = "",
             bars: Bars | None = None, compare: tuple[str, np.ndarray] | None = None, seed: int = 0) -> tuple[dict, dict]:
    """(ligne de l'index, détail) d'une cellule."""
    net, gross = series(trades, cost)
    n = len(net)
    cum, cum_g = np.cumsum(net), np.cumsum(gross)
    dd = cum - np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:]
    idx = pick(n, N_POINTS)
    ts = [t.entry_ts for t in trades]
    years: dict[str, list[float]] = {}
    for t, x in zip(ts, net):
        years.setdefault(str(datetime.fromtimestamp(t, timezone.utc).year), []).append(float(x))
    wins, losses = net[net > 0].sum(), -net[net < 0].sum()
    stats = {"n": n, "mean_r": round(float(net.mean()), 3) if n else None, "gross_r": round(float(gross.mean()), 3) if n else None,
             "total_r": round(float(cum[-1]), 1) if n else 0.0, "total_gross_r": round(float(cum_g[-1]), 1) if n else 0.0,
             "pf": round(float(wins / losses), 2) if losses else None, "win_rate": round(float((net > 0).mean()), 3) if n else None,
             "max_dd": round(float(dd.min()), 1) if n else 0.0,
             "first": datetime.fromtimestamp(ts[0], timezone.utc).strftime("%Y-%m-%d") if n else None,
             "last": datetime.fromtimestamp(ts[-1], timezone.utc).strftime("%Y-%m-%d") if n else None}
    detail: dict[str, Any] = {"id": cell_id, "group": group, "title": title, "asset": asset, "verdict": verdict, "note": note,
                              "stats": stats, "x": [int(ts[i]) for i in idx], "i": [int(i) + 1 for i in idx],
                              "net": r2(cum[idx]), "gross": r2(cum_g[idx]), "dd": r2(dd[idx]),
                              "years": {y: round(sum(v), 1) for y, v in sorted(years.items())}}
    if compare is not None:
        detail["compare"] = {"label": compare[0], "net": r2(np.cumsum(compare[1])[idx])}
    if bars is not None and n:
        rng = np.random.default_rng(seed)
        mk = np.stack([monkey_rs(t, bars, cost, rng, N_MONKEYS) for t in trades])      # trades × singes
        mk = np.nan_to_num(mk, nan=0.0)
        paths = np.cumsum(mk, axis=0)[idx]
        p = np.percentile(paths, [5, 50, 95], axis=1)
        means = mk.mean(axis=0)
        detail["monkeys"] = {"n": N_MONKEYS, "p5": r2(p[0]), "p50": r2(p[1]), "p95": r2(p[2]),
                             "beaten": int((means < net.mean()).sum())}
    sp = pick(n, N_SPARK)
    row = {"id": cell_id, "group": group, "title": title, "asset": asset, "verdict": verdict, "n": n,
           "mean_r": stats["mean_r"], "total_r": stats["total_r"], "spark": r2(cum[sp])}
    return row, detail


def live_trades(name: str, key: str, store, root, candles) -> list[sl.Trade]:
    if name == "bot":
        trades = e32.bot_base(key, store, root, store.load_history(key)[0].ts)
        if key in e32.EXIT_OVERRIDE:
            trades = e32.override(trades, candles, key)
    else:
        trades = sl.run_all(key, candles, only=[name])
    return sorted((t for t in trades if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)


def run(store, cfg, root: Path, only: str | None = None, log=print) -> dict[str, Any]:
    out_dir = Path(sl.__file__).resolve().parent.parent / "docs" / "labo"
    (out_dir / "cells").mkdir(parents=True, exist_ok=True)
    index_f = out_dir / "index.json"
    index = json.loads(index_f.read_text(encoding="utf-8")) if index_f.exists() else {"groups": [], "cells": []}
    groups: dict[str, dict] = {g["id"]: g for g in index["groups"]}
    rows: dict[str, dict] = {r["id"]: r for r in index["cells"]}
    cache: dict[str, Any] = {}

    def candles(key):
        if key not in cache:
            c = e32.candles_for(key, store, root)
            cache[key] = (c, Bars(c))
        return cache[key]

    def emit(row, detail):
        rows[row["id"]] = row
        (out_dir / "cells" / f"{row['id']}.json").write_text(json.dumps(detail, ensure_ascii=False, separators=(",", ":")),
                                                             encoding="utf-8")

    if only in (None, "reel", "essai32"):
        e32_res = json.loads((root / "essai32.json").read_text(encoding="utf-8"))["cells"]
        for k, (name, key, note) in enumerate(LIVE):
            c, bars = candles(key)
            trades = live_trades(name, key, store, root, c)
            cost, _ = bot_cost(key, cfg)
            title = f"{NAMES[name]} · {ASSET_NAMES[key]}"
            if only in (None, "reel"):
                emit(*describe(f"reel-{name}-{key}", "reel", title, key, trades, cost, verdict="en réel", note=note,
                               bars=bars, seed=k))
                log(f"réel : {title} ({len(trades)} trades)")
            if only in (None, "essai32"):
                ts, op, hi, lo = bars.ts, bars.o, bars.h, bars.l
                base, _ = series(trades, cost)
                for v, label in e32.VARIANTS.items():
                    managed = [e32.manage(t, v, ts, op, hi, lo) for t in trades]
                    moved = [sl.Trade(t.strategy, t.asset, t.direction, t.entry_ts, x, t.entry, px, t.risk, why)
                             for t, (px, x, why) in zip(trades, managed)]
                    st = e32_res.get(f"{name}:{key}:{v}", {}).get("status", "?")
                    emit(*describe(f"e32-{name}-{key}-{v}", "essai32", f"{title} · {label}", key, moved, cost,
                                   verdict=st, note="courbe grise : la version actuelle (SL fixe)", compare=("SL fixe", base)))
        groups["reel"] = {"id": "reel", "title": "En réel", "sub": "les stratégies qui envoient des signaux, rejouées sur 2014-2026"}
        groups["essai32"] = {"id": "essai32", "title": "Essai 32 · réajuster le SL", "sub": "4 façons de bouger le stop, comparées au SL fixe"}

    if only in (None, "essai24"):
        res = json.loads((root / "essai24.json").read_text(encoding="utf-8"))["cells"]
        for key in ("gold", "nasdaq", "sp500", "bitcoin"):
            c, _ = candles(key)
            ctx = e15.Ctx(c)
            other = None
            if key in ("nasdaq", "sp500"):
                ok = "sp500" if key == "nasdaq" else "nasdaq"
                other = e15.Ctx(candles(ok)[0])
            base = e32.bot_base(key, store, root, store.load_history(key)[0].ts)     # bot rejoué, sorties d'origine
            cost, _ = bot_cost(key, cfg)
            for name, trades in e17.cells(key, c, c, ctx, other, base, cfg.assets[key].cost_pct):
                trades = sorted((t for t in trades if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
                v = res.get(f"{name}:{key}", {})
                m = v.get("monkeys") or {}
                note = (f"{v.get('positive_years', '?')} années positives · singes battus : {m.get('beaten', '?')}/1000"
                        if v else "")
                emit(*describe(f"e24-{slug(name)}-{key}", "essai24", f"{NAMES.get(name, name)} · {ASSET_NAMES[key]}", key, trades,
                               cost, verdict=v.get("status", "?"), note=note))
            log(f"essai 24 : {key} fait")
        groups["essai24"] = {"id": "essai24", "title": "Essai 24 · 54 stratégies × 4 marchés",
                             "sub": "2014-2026 d'un bloc, frais du bot, tous les contrôles"}

    order = ["reel", "essai32", "essai24"]
    out = {"updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
           "groups": [groups[g] for g in order if g in groups],
           "cells": sorted(rows.values(), key=lambda r: (order.index(r["group"]) if r["group"] in order else 99,
                                                         r["group"] != "reel" and -(r["total_r"] or 0)))}
    index_f.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    eng = Engine(load_config())
    out = run(eng.store, eng.cfg, eng.store.dir, only=only, log=lambda s: print(s, flush=True))
    print(f"{len(out['cells'])} cellules")


if __name__ == "__main__":
    main()
