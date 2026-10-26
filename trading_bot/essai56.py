"""Essai 56 (HYPOTHESES.md) : taille adaptée à l'agitation du marché sur la zone de bruit v2 et le Double 7 (Nasdaq).
  T0 risque fixe 1 %  ·  T1 1 % × repère / agitation  ·  T2 1 % × agitation / repère  (bornes 0,5 %-2 %)

    python -m trading_bot.essai56          → data/essai56.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import strategies as sl
from .essai21 import bot_cost, real_rs
from .essai32 import candles_for
from .essai52 import daily_trades
from .essai55 import HALF, day_table


def stats(pct):
    eq = np.cumsum(pct)
    dd = float(np.max(np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]))
    tot = float(eq[-1]) if len(eq) else 0.0
    return tot, dd, tot / dd if dd > 0 else None


def main() -> None:
    from .config import load_config
    from .engine import Engine
    eng = Engine(load_config())
    store, cfg, root = eng.store, eng.cfg, eng.store.dir
    c = candles_for("nasdaq", store, root)
    days, _cl, rg = day_table(c, sl.NY)
    pos = {d: n for n, d in enumerate(days)}
    cost, _ = bot_cost("nasdaq", cfg)
    sets = {"zone de bruit v2": sl.run_all("nasdaq", c, only=["noise_area_v2"]), "Double 7": daily_trades(c, "nasdaq", "R3")}
    out = {"essai": 56}
    rng = np.random.default_rng(56)
    for name, tr in sets.items():
        tr = sorted((t for t in tr if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
        ratio = []
        keep = []
        for t in tr:
            n = pos.get(datetime.fromtimestamp(t.entry_ts, sl.NY).date())
            if n is None or n < 265:
                continue
            a14 = rg[n - 14:n].mean()
            med = np.median([rg[m - 14:m].mean() for m in range(n - 250, n)])
            keep.append(t)
            ratio.append(a14 / med)
        rs = real_rs(keep, cost)
        ratio = np.array(ratio)
        early = np.array([t.entry_ts < HALF for t in keep])
        sizes = {"T0 fixe 1 %": np.ones(len(rs)), "T1 plus petit quand ça bouge": np.clip(1 / ratio, 0.5, 2.0),
                 "T2 plus grand quand ça bouge": np.clip(ratio, 0.5, 2.0)}
        res = {}
        for code, s in sizes.items():
            pct = rs * s
            tot, dd, rr = stats(pct)
            t1, d1, r1 = stats(pct[early])
            t2, d2, r2 = stats(pct[~early])
            years = {}
            for t, p in zip(keep, pct):
                y = datetime.fromtimestamp(t.entry_ts, timezone.utc).year
                years[y] = years.get(y, 0) + p
            v = {"trades": len(pct), "gain_total_pct": round(tot, 1), "baisse_max_pct": round(dd, 1),
                 "gain_sur_baisse": round(rr, 2) if rr else None,
                 "2014-2019": [round(t1, 1), round(d1, 1), round(r1, 2) if r1 else None],
                 "2020+": [round(t2, 1), round(d2, 1), round(r2, 2) if r2 else None],
                 "par_an_pct": {y: round(p, 1) for y, p in sorted(years.items())}}
            if not code.startswith("T0"):
                rand = []
                for _ in range(1000):
                    sh = rng.permutation(s)
                    rand.append(stats(rs * sh)[2] or 0)
                v["bat_tailles_hasard"] = int(np.sum(np.array(rand) < (rr or 0)))
                b = res["T0 fixe 1 %"]
                v["passe"] = bool(r1 and r2 and b["2014-2019"][2] and r1 > b["2014-2019"][2] and r2 > b["2020+"][2]
                                  and v["bat_tailles_hasard"] >= 950)
            res[code] = v
            print(name, code, json.dumps(v, ensure_ascii=False), flush=True)
        out[name] = res
    (Path(root) / "essai56.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
