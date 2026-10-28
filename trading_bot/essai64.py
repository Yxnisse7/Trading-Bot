"""Essai 64 (HYPOTHESES.md) : acheter l'or juste après la pause quotidienne du CME (idée du canal MQL5).

    python -m trading_bot.essai64          → data/essai64.json

Données hors dépôt : data/history/long/gold_1m.npz (HistData XAUUSD 1 min, UTC).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from .config import DATA_DIR
from .essai33 import HALF, NY, UTC, Bars, z_threshold

N_MONKEYS = 1000
STOP_MULT = 1.5
FEE_OPEN, FEE_NORMAL = 0.90, 0.45        # $ l'once aller-retour : écart élargi à la réouverture / écart normal
CELLS = {"R1": {"delay": 0, "hold": 120, "stop": True, "fee": FEE_OPEN},
         "R2": {"delay": 0, "hold": 60, "stop": True, "fee": FEE_OPEN},
         "R3": {"delay": 5, "hold": 120, "stop": True, "fee": FEE_NORMAL},
         "R4": {"delay": 0, "hold": 120, "stop": False, "fee": FEE_OPEN}}


def ny_minutes(ts: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Minute de la journée, jour de la semaine (lundi = 0) et date, à l'heure de New York."""
    mins, wd, day = np.empty(len(ts), np.int32), np.empty(len(ts), np.int8), np.empty(len(ts), np.int32)
    hour = ts // 3600
    cut = np.flatnonzero(np.diff(hour)) + 1
    for a, b in zip(np.r_[0, cut], np.r_[cut, len(ts)]):
        d = datetime.fromtimestamp(int(ts[a]), UTC).astimezone(NY)
        base = d.hour * 60
        mins[a:b] = base + (ts[a:b] % 3600) // 60
        wd[a:b] = d.weekday()
        day[a:b] = d.toordinal()
    return mins, wd, day


def hourly_range(b: Bars) -> tuple[np.ndarray, np.ndarray]:
    h = b.resample(3600)
    rng = h.h - h.l
    avg = np.convolve(rng, np.ones(14) / 14, mode="full")[:len(rng)]
    avg[:13] = np.nan
    return h.ts, avg


def trade(b: Bars, i: int, hold: int, stop_dist: float, use_stop: bool, fee: float) -> float | None:
    """R net d'un achat à l'ouverture de la bougie i, sorti à l'ouverture de i + hold (ou au stop)."""
    end = i + hold
    if end >= len(b.ts) or b.ts[end] - b.ts[i] > (hold + 30) * 60:
        return None                                   # trou dans les données (week-end, jour férié)
    e = float(b.o[i])
    stop = e - stop_dist
    px = float(b.o[end])
    if use_stop:
        lo = b.l[i:end]
        hit = np.flatnonzero(lo <= stop)
        if len(hit):
            k = i + int(hit[0])
            px = min(stop, float(b.o[k])) if k > i else stop
    return (px - e - fee) / stop_dist


def checks(rs: np.ndarray, ts: np.ndarray, r_fee2: np.ndarray, monkeys: np.ndarray, z_need: float) -> dict[str, Any]:
    yrs = np.array([datetime.fromtimestamp(int(x), UTC).year for x in ts])
    last = int(yrs.max())
    years = {int(y): round(float(rs[yrs == y].mean()), 3) for y in sorted(set(yrs)) if y < last}
    z = float(rs.mean() / (rs.std(ddof=1) / np.sqrt(len(rs))))
    beat = float((monkeys < rs.mean()).mean())
    first, second = rs[ts < HALF], rs[ts >= HALF]
    out = {"trades": int(len(rs)), "R": round(float(rs.mean()), 3), "gagnants": round(float((rs > 0).mean()), 2),
           "z": round(z, 2), "singes_R": round(float(monkeys.mean()), 3), "bat_singes": round(beat, 3),
           "avant_2020": round(float(first.mean()), 3), "depuis_2020": round(float(second.mean()), 3),
           "annees_positives": round(float(np.mean([v > 0 for v in years.values()])), 2),
           "frais_doubles_R": round(float(r_fee2.mean()), 3), "annees": years}
    ok = (out["R"] > 0 and z >= z_need and beat >= 0.95 and out["avant_2020"] > 0 and out["depuis_2020"] > 0
          and out["annees_positives"] >= 0.6 and out["frais_doubles_R"] > 0)
    out["verdict"] = "passe" if ok else "ne passe pas"
    return out


def run(b: Bars, seed: int = 64) -> dict[str, Any]:
    mins, wd, day = ny_minutes(b.ts)
    hts, havg = hourly_range(b)
    reopen = np.flatnonzero((mins >= 18 * 60) & (np.r_[-1, mins[:-1]] < 18 * 60) & np.isin(wd, [6, 0, 1, 2, 3])
                            & (np.r_[0, np.diff(b.ts)] >= 30 * 60))
    rng = np.random.default_rng(seed)
    z_need = z_threshold(len(CELLS))
    res: dict[str, Any] = {"reouvertures": int(len(reopen)), "seuil_z": round(z_need, 2)}
    for name, c in CELLS.items():
        rs, r2, ts, pools = [], [], [], []
        for i0 in reopen:
            i = i0 + c["delay"]
            j = int(np.searchsorted(hts, b.ts[i0], side="right")) - 2   # dernière heure close avant la pause
            if j < 0 or not np.isfinite(havg[j]) or havg[j] <= 0:
                continue
            dist = STOP_MULT * float(havg[j])
            r = trade(b, i, c["hold"], dist, c["stop"], c["fee"])
            if r is None:
                continue
            rs.append(r)
            r2.append(r - c["fee"] / dist)
            ts.append(int(b.ts[i]))
            # singes : même jour de séance (de 19:00 à 16:00 le lendemain, heure de New York), heure au hasard
            a, z = np.searchsorted(b.ts, [b.ts[i0] + 3600, b.ts[i0] + 21 * 3600])
            span = np.arange(a, z)[mins[a:z] % 60 == 0]
            got = [x for x in (trade(b, int(k), c["hold"], dist, c["stop"], FEE_NORMAL) for k in span) if x is not None]
            pools.append(np.array(got) if got else np.array([np.nan]))
        rs_a, ts_a, r2_a = np.array(rs), np.array(ts), np.array(r2)
        mk = np.array([np.nanmean([p[rng.integers(len(p))] for p in pools]) for _ in range(N_MONKEYS)])
        res[name] = {**c, **checks(rs_a, ts_a, r2_a, mk, z_need)}
        print(name, {k: v for k, v in res[name].items() if k != "annees"}, flush=True)
    return res


def main() -> None:
    from .essai33 import LONG
    b = Bars.load("gold_1m.npz")
    print("bougies", len(b.ts), datetime.fromtimestamp(int(b.ts[0]), UTC), datetime.fromtimestamp(int(b.ts[-1]), UTC),
          "dossier", LONG)
    res = run(b)
    (Path(DATA_DIR) / "essai64.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
