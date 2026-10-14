"""Essai 27 (HYPOTHESES.md) : l'or la nuit, idées trouvées sur le web (Blose et al. 2018, heures asiatiques).

    python -m trading_bot.essai27          → data/essai27.json
"""
from __future__ import annotations

import zlib
from datetime import datetime, time, timedelta, timezone
from statistics import NormalDist
from typing import Any

import numpy as np

from . import strategies as sl
from .essai23 import load

FEE = 0.30                     # $ l'once aller-retour, Vantage RAW
HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
RECENT = int(datetime(2024, 10, 14, tzinfo=timezone.utc).timestamp())
N_MONKEYS = 1000
CELLS = {                      # nom : (heure d'entrée NY, heure de sortie NY, sortie le lendemain, sens)
    "N1 nuit COMEX": (time(13, 30), time(8, 20), True, 1),
    "N2 heures asiatiques": (time(18, 0), time(3, 0), True, 1),
    "N3 vente le jour": (time(8, 20), time(13, 30), False, -1),
}


def _at(ts: np.ndarray, t: int) -> int | None:
    i = int(np.searchsorted(ts, t))
    return i if i < len(ts) and ts[i] - t <= 1800 else None


def trades(ts, opens, days, cell) -> list[tuple[int, int, int]]:
    """(indice d'entrée, indice de sortie, début du jour NY) pour chaque jour de semaine."""
    t_in, t_out, next_day, _ = cell
    out = []
    for d in days:
        if d.weekday() > 4 or (next_day and d.weekday() == 4 and t_out < t_in):
            continue
        d_out = d + timedelta(days=1) if next_day else d
        a = _at(ts, int(datetime.combine(d, t_in, sl.NY).timestamp()))
        b = _at(ts, int(datetime.combine(d_out, t_out, sl.NY).timestamp()))
        if a is not None and b is not None and b > a:
            out.append((a, b, int(datetime.combine(d, time(0), sl.NY).timestamp())))
    return out


def run(candles) -> dict[str, Any]:
    ts = np.array([c.ts for c in candles], dtype=np.int64)
    op = np.array([c.open for c in candles])
    days = sorted({datetime.fromtimestamp(t, sl.NY).date() for t in ts[::12]})
    last_year = datetime.fromtimestamp(int(ts[-1]), timezone.utc).year
    out: dict[str, Any] = {"essai": 27, "fee_usd_oz": FEE, "cells": {}}
    for name, cell in CELLS.items():
        sign = cell[3]
        tr = trades(ts, op, days, cell)
        a = np.array([x[0] for x in tr]); b = np.array([x[1] for x in tr]); d0 = np.array([x[2] for x in tr])
        gross = sign * (op[b] - op[a]) / op[a] * 100
        fee = FEE / op[a] * 100
        net = gross - fee
        t_in = ts[a]
        yrs: dict[int, list[float]] = {}
        for t, r in zip(t_in, net):
            yrs.setdefault(datetime.fromtimestamp(int(t), timezone.utc).year, []).append(float(r))
        full = {y: v for y, v in yrs.items() if y < last_year}
        pos = sum(1 for v in full.values() if sum(v) > 0)
        # singes : même jour, heure tirée au hasard, même durée, même sens
        rng = np.random.default_rng(zlib.crc32(f"essai27:{name}".encode()))
        dur = ts[b] - ts[a]
        starts = d0[:, None] + rng.integers(0, 288, (len(tr), N_MONKEYS)) * 300
        ia = np.clip(np.searchsorted(ts, starts), 0, len(ts) - 1)
        ib = np.clip(np.searchsorted(ts, starts + dur[:, None]), 0, len(ts) - 1)
        mk = sign * (op[ib] - op[ia]) / op[ia] * 100 - FEE / op[ia] * 100
        means = mk.mean(0)
        sd = float(means.std(ddof=1))
        real = float(net.mean())
        v = {"n": len(tr), "gross_pct": round(float(gross.mean()), 4), "net_pct": round(real, 4),
             "positive_years": f"{pos}/{len(full)}",
             "years": {str(y): round(sum(v) / len(v), 4) for y, v in sorted(yrs.items())},
             "before_2020": round(float(net[t_in < HALF].mean()), 4),
             "since_2020": round(float(net[t_in >= HALF].mean()), 4),
             "last_2_years": round(float(net[t_in >= RECENT].mean()), 4),
             "fees_x2": round(float((gross - 2 * fee).mean()), 4),
             "monkeys": {"mean_pct": round(float(means.mean()), 4), "beaten": int((means < real).sum()),
                         "z": round((real - float(means.mean())) / sd, 2) if sd > 0 else None}}
        v["checks"] = {"> 0": real > 0, "60 % des années": pos >= 0.6 * len(full),
                       "deux moitiés": v["before_2020"] > 0 and v["since_2020"] > 0,
                       "2 dernières années": v["last_2_years"] > 0, "frais doublés": v["fees_x2"] > 0,
                       "singes": v["monkeys"]["beaten"] >= 950}
        v["robust"] = all(v["checks"].values())
        out["cells"][name] = v
    z_thr = NormalDist().inv_cdf(1 - 0.05 / len(CELLS))
    out["z_threshold"] = round(z_thr, 2)
    for v in out["cells"].values():
        v["status"] = ("prouvé" if v["robust"] and (v["monkeys"]["z"] or 0) > z_thr
                       else "robuste" if v["robust"] else "pas robuste")
    return out


def main() -> None:
    import json

    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    new = eng.store.load_history("gold")
    candles = [c for c in load(eng.store.dir / "history" / "long" / "gold_5m.json") if c.ts < new[0].ts] + new
    out = run(candles)
    out["updated_at"] = iso(utcnow())
    for k, v in out["cells"].items():
        print(k, json.dumps({x: v[x] for x in v if x != "years"}, ensure_ascii=False), flush=True)
        print("  années", v["years"], flush=True)
    eng.store._write(eng.store.dir / "essai27.json", out)


if __name__ == "__main__":
    main()
