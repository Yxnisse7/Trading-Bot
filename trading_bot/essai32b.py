"""Essai 32 b (HYPOTHESES.md, à titre d'information, demandé par Yanisse le 20/10/2026) : le « vrai » break even.

Dans l'essai 32, le stop était remis pile au prix d'entrée : touché, le trade perdait encore les frais. Ici le stop
est posé à l'entrée + les frais aller-retour (spread et commission compris), donc une sortie au break even vaut
vraiment 0. On le déclenche quand le trade a gagné +0,5 R, +1 R, +1,5 R ou +2 R (clôture de bougie 5 min).

    python -m trading_bot.essai32b          → data/essai32b.json
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from statistics import NormalDist
from typing import Any

import numpy as np

from . import strategies as sl
from .essai21 import bot_cost
from .essai32 import STRATS, bot_base, candles_for, judge, override
from .signals import EXIT_OVERRIDE

TRIGGERS = {"BE0.5": 0.5, "BE1": 1.0, "BE1.5": 1.5, "BE2": 2.0}


def manage_be(t: sl.Trade, trigger: float, fee: float, ts, op, hi, lo) -> tuple[float, int, str]:
    """Sortie avec un stop posé à entrée + frais dès que le meilleur gain atteint `trigger` R."""
    sign = 1 if t.direction == "long" else -1
    be = t.entry + sign * fee
    j = int(np.searchsorted(ts, t.entry_ts)) + 1
    armed, best = False, -math.inf
    while j < len(ts) and ts[j] <= t.exit_ts:
        last = ts[j] == t.exit_ts
        if last and t.exit == op[j]:
            break
        if armed and ((lo[j] <= be) if sign > 0 else (hi[j] >= be)):
            px = min(be, op[j]) if sign > 0 else max(be, op[j])
            return float(px), int(ts[j]), "stop géré"
        if last:
            break
        best = max(best, (hi[j] - t.entry) if sign > 0 else (t.entry - lo[j]))
        armed = armed or best >= trigger * t.risk
        j += 1
    return t.exit, t.exit_ts, t.reason


def run(store, cfg, root, log=print) -> dict[str, Any]:
    out: dict[str, Any] = {"essai": "32b", "variants": {k: f"stop à entrée + frais dès +{v:g} R".replace(".", ",")
                                                         for k, v in TRIGGERS.items()}, "cells": {}}
    cache: dict[str, Any] = {}
    for name, key in STRATS:
        if key not in cache:
            c = candles_for(key, store, root)
            cache[key] = (c, np.array([x.ts for x in c], dtype=np.int64), np.array([x.open for x in c]),
                          np.array([x.high for x in c]), np.array([x.low for x in c]))
        candles, ts, op, hi, lo = cache[key]
        if name == "bot":
            trades = bot_base(key, store, root, store.load_history(key)[0].ts)
            if key in EXIT_OVERRIDE:
                trades = override(trades, candles, key)
        else:
            trades = sl.run_all(key, candles, only=[name])
        trades = sorted((t for t in trades if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
        cost, _ = bot_cost(key, cfg)
        last_year = datetime.fromtimestamp(int(ts[-1]), timezone.utc).year
        for v, trig in TRIGGERS.items():
            managed = [manage_be(t, trig, cost(t.entry), ts, op, hi, lo) for t in trades]
            r = judge(trades, managed, cost, last_year)
            r.update({"strategy": name, "asset": key, "variant": v})
            out["cells"][f"{name}:{key}:{v}"] = r
            log(f"{name:16s} {key:7s} {v:5s} n={r['n']:5d} actuel {r['current_r']:+.3f} → {r['variant_r']:+.3f} R "
                f"(écart {r['diff_r']:+.3f}, z {r['z']:+.2f}, sorties au BE {r['moved_exit']:.0%})")
    z_thr = NormalDist().inv_cdf(1 - 0.05 / len(out["cells"]))
    out["z_threshold"] = round(z_thr, 2)
    for r in out["cells"].values():
        ok = all(r["checks"].values())
        r["status"] = "prouvée" if ok and r["z"] > z_thr else "robuste" if ok else "pas mieux"
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    out = run(eng.store, eng.cfg, eng.store.dir, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    eng.store._write(eng.store.dir / "essai32b.json", out)


if __name__ == "__main__":
    main()
