"""Essai 29 (HYPOTHESES.md) : mêmes entrées que le bot (2014-2026), autres stops et objectifs.

    python -m trading_bot.essai29          → data/essai29.json
"""
from __future__ import annotations

import zlib
from datetime import datetime, timezone
from statistics import NormalDist
from typing import Any

import numpy as np

from . import essai25 as e25
from . import strategies as sl
from .essai21 import bot_cost

HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
RECENT = int(datetime(2024, 10, 14, tzinfo=timezone.utc).timestamp())
N_MONKEYS = 200
FAMILY1 = [(m, k) for m in (0.5, 1, 1.5, 2, 3) for k in (0.5, 1, 1.5, 2, 3, 5)]       # stop × bot, objectif × stop
FAMILY2 = [(p, k) for p in (1, 2, 5, 10) for k in (1, 2, 3)]                          # stop en %, objectif × stop
DAY, DAYS20 = 86400, 20 * 86400


class Paths:
    """Pour chaque entrée : plus grand gain et plus grande perte atteints depuis l'entrée, bougie par bougie."""

    def __init__(self, ts, hi, lo, cl, i0: int, entry: float, sign: int, horizon: int):
        j = int(np.searchsorted(ts, ts[i0] + horizon))
        h, l = hi[i0:j], lo[i0:j]
        up, down = ((h - entry), (entry - l)) if sign > 0 else ((entry - l), (h - entry))
        self.U, self.D = np.maximum.accumulate(up), np.maximum.accumulate(down)
        self.last = (cl[j - 1] - entry) * sign

    def exit(self, stop: float, target: float) -> tuple[float, str]:
        i_s = int(np.searchsorted(self.D, stop))
        i_t = int(np.searchsorted(self.U, target))
        n = len(self.D)
        if i_s < n and i_s <= i_t:
            return -stop, "stop"
        if i_t < n:
            return target, "objectif"
        return float(self.last), "heure"


def evaluate(t, p1: Paths, p20: Paths, cost) -> dict[tuple[int, float, float], tuple[int, float, float, str]]:
    """Pour un signal : (entrée ts, R net, R frais doublés, sortie) dans chaque réglage."""
    out = {}
    c = cost(t.entry)
    for family, grid, p in ((1, FAMILY1, p1), (2, FAMILY2, p20)):
        for a, k in grid:
            stop = t.risk * a if family == 1 else t.entry * a / 100
            if stop <= 0:
                continue
            g, why = p.exit(stop, stop * k)
            out[(family, a, k)] = (t.entry_ts, (g - c) / stop, (g - 2 * c) / stop, why)
    return out


def checks(rows, last_year: int) -> dict[str, Any]:
    ts = np.array([r[0] for r in rows]); r = np.array([r[1] for r in rows]); r2 = np.array([x[2] for x in rows])
    why = [x[3] for x in rows]
    years: dict[int, list[float]] = {}
    for t, x in zip(ts, r):
        years.setdefault(datetime.fromtimestamp(int(t), timezone.utc).year, []).append(float(x))
    full = {y: v for y, v in years.items() if y < last_year}
    pos = sum(1 for v in full.values() if sum(v) > 0)
    gains, losses = r[r > 0].sum(), -r[r < 0].sum()
    m = lambda sel: round(float(r[sel].mean()), 4) if sel.any() else None  # noqa: E731
    v = {"n": len(r), "mean_r": round(float(r.mean()), 4), "profit_factor": round(float(gains / losses), 2) if losses else None,
         "tp_rate": round(why.count("objectif") / len(why), 3), "sl_rate": round(why.count("stop") / len(why), 3),
         "time_rate": round(why.count("heure") / len(why), 3), "positive_years": f"{pos}/{len(full)}",
         "before_2020": m(ts < HALF), "since_2020": m(ts >= HALF), "last_2_years": m(ts >= RECENT),
         "fees_x2": round(float(r2.mean()), 4)}
    v["checks"] = {"200 trades": len(r) >= 200, "R > 0 et PF ≥ 1,1": v["mean_r"] > 0 and (v["profit_factor"] or 0) >= 1.1,
                   "60 % des années": pos >= 0.6 * len(full),
                   "deux moitiés": (v["before_2020"] or 0) > 0 and (v["since_2020"] or 0) > 0,
                   "2 dernières années": (v["last_2_years"] or 0) > 0, "frais doublés": v["fees_x2"] > 0}
    return v


def monkeys(trades, bars, family, a, k, cost, real: float, seed: str) -> dict[str, Any]:
    """Entrées au hasard comme à l'essai 21 : n'importe quel jour de 2014-2026, à la même heure (UTC), même sens,
    même stop et objectif. (Le même jour que le signal aurait triché : le sens du bot suit le mouvement du jour.)"""
    ts, hi, lo, cl = bars
    rng = np.random.default_rng(zlib.crc32(seed.encode()))
    hours = (ts // 3600) % 24
    pools = {h: np.flatnonzero(hours[:-1] == h) + 1 for h in range(24)}
    sums = np.zeros(N_MONKEYS)
    n = 0
    for t, i0 in trades:
        sign = 1 if t.direction == "long" else -1
        for m, i in enumerate(rng.choice(pools[int(hours[i0])], N_MONKEYS)):
            e = cl[i - 1]
            p = Paths(ts, hi, lo, cl, int(i), float(e), sign, DAY if family == 1 else DAYS20)
            stop = t.risk / t.entry * e * a if family == 1 else e * a / 100      # même stop en % du prix
            g, _ = p.exit(stop, stop * k)
            sums[m] += (g - cost(e)) / stop
        n += 1
    means = sums / max(1, n)
    sd = float(means.std(ddof=1))
    return {"mean_r": round(float(means.mean()), 4), "beaten": int((means < real).sum()),
            "z": round((real - float(means.mean())) / sd, 2) if sd > 0 else None}


def run(store, cfg, root, log=print) -> dict[str, Any]:
    data = e25.dataset(store, cfg, root)
    out: dict[str, Any] = {"essai": 29, "cells": {}}
    for key in e25.ASSETS:
        candles = data["candles"][key]
        ts = np.array([c.ts for c in candles], dtype=np.int64)
        hi = np.array([c.high for c in candles]); lo = np.array([c.low for c in candles])
        cl = np.array([c.close for c in candles])
        bars = (ts, hi, lo, cl)
        cost, _ = bot_cost(key, cfg)
        last_year = datetime.fromtimestamp(int(ts[-1]), timezone.utc).year
        trades, results = [], {}
        for k_, t, _, _ in data["rows"]:
            if k_ != key:
                continue
            i0 = int(np.searchsorted(ts, t.entry_ts))
            if i0 >= len(ts) - 1:
                continue
            sign = 1 if t.direction == "long" else -1
            trades.append((t, i0))
            res = evaluate(t, Paths(ts, hi, lo, cl, i0, t.entry, sign, DAY),
                           Paths(ts, hi, lo, cl, i0, t.entry, sign, DAYS20), cost)
            for cell, row in res.items():
                results.setdefault(cell, []).append(row)
        log(f"{key}: {len(trades)} signaux")
        for family, grid in ((1, FAMILY1), (2, FAMILY2)):
            for a, k in grid:
                name = f"{key}:{'stop ×' if family == 1 else 'stop '}{a}{'' if family == 1 else ' %'}:objectif {k}"
                v = checks(results[(family, a, k)], last_year)
                v.update({"asset": key, "family": family, "stop": a, "target_x": k})
                if all(v["checks"].values()):
                    v["monkeys"] = monkeys(trades, bars, family, a, k, cost, v["mean_r"], f"essai29:{name}")
                    v["checks"]["singes"] = v["monkeys"]["beaten"] >= 190
                out["cells"][name] = v
                failed = [c for c, ok in v["checks"].items() if not ok]
                log(f"{name:40s} n={v['n']:5d} {v['mean_r']:+.3f} R PF {v['profit_factor']} TP {v['tp_rate']:.0%} "
                    f"SL {v['sl_rate']:.0%} heure {v['time_rate']:.0%} années {v['positive_years']} "
                    f"{'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")
    z_thr = NormalDist().inv_cdf(1 - 0.05 / len(out["cells"]))
    out["z_threshold"] = round(z_thr, 2)
    for v in out["cells"].values():
        robust = all(v["checks"].values())
        v["status"] = ("prouvé" if robust and ((v.get("monkeys") or {}).get("z") or 0) > z_thr
                       else "robuste" if robust else "pas robuste")
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    out = run(eng.store, eng.cfg, eng.store.dir, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    for k, v in out["cells"].items():
        if v["status"] != "pas robuste":
            print(f"{k:40s} {v['status']}", flush=True)
    eng.store._write(eng.store.dir / "essai29.json", out)


if __name__ == "__main__":
    main()
