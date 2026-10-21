"""Essai 41 (HYPOTHESES.md) : le Nasdaq le matin, avant l'ouverture de Wall Street (demandé par Yanisse le 21/10/2026).

Nasdaq 2014-2026 (data/history/long/nasdaq_5m.json + data/history/nasdaq_5m.json), heures de Paris, toutes les
sorties au plus tard à 15h00 Paris. Contrôles de l'essai 24.

    python -m trading_bot.essai41          → data/essai41.json
"""
from __future__ import annotations

import dataclasses
import json
from datetime import date, datetime, time, timedelta, timezone
from statistics import NormalDist
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np

from . import essai14 as e14
from . import essai15 as e15
from . import essai22 as e22
from . import strategies as sl
from .essai21 import Bars, bot_cost, judge
from .essai23 import load
from .essai24 import checks

PARIS = ZoneInfo("Europe/Paris")
SAFETY = 0.005              # stop de sécurité 0,5 % (M4-M7)
MORNING_UTC = (6, 13)


class Px:
    def __init__(self, candles):
        self.ts = np.array([c.ts for c in candles], dtype=np.int64)
        self.op = np.array([c.open for c in candles])
        self.hi = np.array([c.high for c in candles])
        self.lo = np.array([c.low for c in candles])
        self.cl = np.array([c.close for c in candles])
        d0 = datetime.fromtimestamp(int(self.ts[0]), PARIS).date()
        d1 = datetime.fromtimestamp(int(self.ts[-1]), PARIS).date()
        self.days = [d0 + timedelta(days=i) for i in range((d1 - d0).days + 1)]

    def at(self, d: date, hh: int, mm: int = 0, tol: int = 600) -> int | None:
        t = int(datetime.combine(d, time(hh, mm), PARIS).timestamp())
        i = int(np.searchsorted(self.ts, t))
        return i if i < len(self.ts) and self.ts[i] - t <= tol else None


def trade(p: Px, name: str, a: int, z: int, s: int, stop: float) -> sl.Trade | None:
    """Entrée à l'ouverture de la bougie a, sortie au stop ou à l'ouverture de la bougie z."""
    e = float(p.op[a])
    risk = (e - stop) * s
    if risk <= 0 or z <= a:
        return None
    hit = np.flatnonzero(p.lo[a:z] <= stop) if s > 0 else np.flatnonzero(p.hi[a:z] >= stop)
    if len(hit):
        k = a + int(hit[0])
        return sl.Trade(name, "nasdaq", "long" if s > 0 else "short", int(p.ts[a]), int(p.ts[k]) + 300, e,
                        float(stop), risk, "sl")
    return sl.Trade(name, "nasdaq", "long" if s > 0 else "short", int(p.ts[a]), int(p.ts[z]), e, float(p.op[z]),
                    risk, "heure")


def breakout(p: Px, name: str, r0: tuple[int, int], r1: tuple[int, int], last: tuple[int, int], stop_mode: str):
    out = []
    for d in p.days:
        if d.weekday() >= 5:
            continue
        i0, i1, iz, iend = p.at(d, *r0), p.at(d, *r1), p.at(d, *last), p.at(d, 15, 0)
        if None in (i0, i1, iz, iend) or not i0 < i1 < iz <= iend:
            continue
        hi, lo = float(p.hi[i0:i1].max()), float(p.lo[i0:i1].min())
        for k in range(i1, iz):
            s = 1 if p.cl[k] > hi else -1 if p.cl[k] < lo else 0
            if s:
                stop = (hi + lo) / 2 if stop_mode == "milieu" else (lo if s > 0 else hi)
                t = trade(p, name, k + 1, iend, s, stop)
                if t:
                    out.append(t)
                break
    return out


def timed(p: Px, name: str, ref: tuple[tuple[int, int], tuple[int, int]], entry: tuple[int, int],
          exit_: tuple[int, int], follow: bool, prev_day: bool = False):
    out = []
    for d in p.days:
        if d.weekday() >= 5:
            continue
        rd = d - timedelta(days=3 if d.weekday() == 0 else 1) if prev_day else d
        i0, i1 = p.at(rd, *ref[0]), p.at(d, *ref[1])
        a, z = p.at(d, *entry), p.at(d, *exit_)
        if None in (i0, i1, a, z) or not i0 < i1 <= a < z:
            continue
        move = p.op[i1] - p.op[i0]
        if move == 0:
            continue
        s = (1 if move > 0 else -1) * (1 if follow else -1)
        e = float(p.op[a])
        t = trade(p, name, a, z, s, e * (1 - s * SAFETY))
        if t:
            out.append(t)
    return out


def cells(p: Px) -> dict[str, list[sl.Trade]]:
    return {
        "M2 cassure du range de la nuit": breakout(p, "M2", (1, 0), (8, 0), (13, 0), "milieu"),
        "M3 cassure de Francfort 9h-9h30": breakout(p, "M3", (9, 0), (9, 30), (13, 0), "autre côté"),
        "M4 suite de la nuit": timed(p, "M4", ((22, 0), (9, 0)), (9, 0), (15, 0), True, prev_day=True),
        "M5 contre la nuit": timed(p, "M5", ((22, 0), (9, 0)), (9, 0), (15, 0), False, prev_day=True),
        "M6 contre Francfort 9h-9h30": timed(p, "M6", ((9, 0), (9, 30)), (9, 30), (15, 0), False),
        "M7 sens de la matinée, 14h-15h25": timed(p, "M7", ((9, 0), (14, 0)), (14, 0), (15, 25), True),
    }


def run(store, cfg, root, log=print) -> dict[str, Any]:
    from .backtest import run_backtest
    old = load(root / "history" / "long" / "nasdaq_5m.json")
    new = store.load_history("nasdaq")
    real = [c for c in old if not new or c.ts < new[0].ts] + new
    p = Px(real)
    cache = root / "history" / "long" / "essai41_bot_nasdaq_matin.json"
    if cache.exists():
        rows = json.loads(cache.read_text(encoding="utf-8"))
    else:
        asset = dataclasses.replace(cfg.assets["nasdaq"], session_utc=MORNING_UTC)
        rows = run_backtest(asset, real, cfg)["trades"]
        cache.write_text(json.dumps(rows), encoding="utf-8")
    all_cells = {"M1 bot classique le matin (6h-13h UTC)": e14.bot_trades(rows, "nasdaq"), **cells(p)}
    cost, label = bot_cost("nasdaq", cfg)
    bars = Bars(real)
    keys, closes = e22.daily_closes(e15.Ctx(real))
    last_year = datetime.fromtimestamp(real[-1].ts, timezone.utc).year
    out: dict[str, Any] = {"essai": 41, "asset": "nasdaq", "fees": label, "cells": {}}
    for name, trades in all_cells.items():
        trades = sorted((t for t in trades if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
        v = checks(trades, cost, keys, closes, last_year)
        m = judge(name, "nasdaq", trades, bars, cost)
        a = m.get("all") or {}
        v["monkeys"] = {"beaten": a.get("beaten"), "z": a.get("z")}
        v["checks"]["singes"] = (a.get("beaten") or 0) >= 950
        v["robust"] = all(v["checks"].values())
        out["cells"][name] = v
        failed = [k for k, ok in v["checks"].items() if not ok]
        log(f"{name:40s} n={v['n']:5d} {v['mean_r']} R PF {v['profit_factor']} années {v['positive_years']} "
            f"2014-19 {v['before_2020']} 2020+ {v['since_2020']} récent {v['last_2_years']} singes {a.get('beaten')} "
            f"z {a.get('z')} → {'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")
    z_thr = NormalDist().inv_cdf(1 - 0.05 / len(out["cells"]))
    out["z_threshold"] = round(z_thr, 2)
    for v in out["cells"].values():
        v["status"] = ("prouvée" if v["robust"] and (v["monkeys"]["z"] or 0) > z_thr
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
        print(f"{k:40s} {v['status']}", flush=True)
    eng.store._write(eng.store.dir / "essai41.json", out)


if __name__ == "__main__":
    main()
