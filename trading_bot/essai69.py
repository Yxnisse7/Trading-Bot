"""Essai 69 (HYPOTHESES.md) : retournement après une fin de séance violente sur les indices US.

Idée (Baltussen, Da, Lammers et Martens) : un fort mouvement de 15:30 à 16:00 New York se résorbe en partie dans
les 2 séances suivantes.

    python -m trading_bot.essai69          → data/essai69.json

Données hors dépôt : data/history/long/raw69/{NSXUSD,SPXUSD}_*.csv (HistData 1 min, heure fixe UTC−5),
converties une fois en data/history/long/{nasdaq,sp500}_1m.npz.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from .config import DATA_DIR
from .essai33 import LONG, NY, UTC, Bars, z_threshold
from .essai64 import ny_minutes

PAIRS = {"nasdaq": "NSXUSD", "sp500": "SPXUSD"}
SPREAD = {"nasdaq": 1.3, "sp500": 0.6}       # points, aller-retour (estimation CFD Vantage)
FIN_RATE, NIGHTS = 0.05, 2                    # financement prudent : 2 nuits à 5 %/an du nominal
PCT, LOOKBACK, ATR_N = 80, 120, 14
SPLIT = date(2020, 1, 1)
N_MONKEYS = 1000
CELLS = ("A", "B", "C")
OUT = Path(DATA_DIR) / "essai69.json"


def half_days(y: int) -> set[date]:
    """Séances écourtées à 13:00 : 3 juillet (jour ouvré), lendemain de Thanksgiving, 24 décembre."""
    out = {date(y, 7, 3), date(y, 12, 24)}
    nov = [date(y, 11, d) for d in range(1, 31) if date(y, 11, d).weekday() == 3]
    out.add(nov[3] + timedelta(days=1))
    return {d for d in out if d.weekday() < 5}


def load(asset: str) -> Bars:
    npz = LONG / f"{asset}_1m.npz"
    if not npz.exists():
        rows = []
        for f in sorted((LONG / "raw69").glob(f"{PAIRS[asset]}_*.csv")):
            for line in f.read_text(encoding="ascii", errors="ignore").splitlines():
                p = line.strip().split(";")
                if len(p) < 5 or len(p[0]) != 15:
                    continue
                t = datetime.strptime(p[0], "%Y%m%d %H%M%S").replace(tzinfo=UTC) + timedelta(hours=5)
                rows.append((int(t.timestamp()), *(float(x) for x in p[1:5])))
        a = np.array(sorted(set(rows)), dtype=float)
        np.savez_compressed(npz, ts=a[:, 0].astype(np.int64), o=a[:, 1], h=a[:, 2], l=a[:, 3], c=a[:, 4])
    return Bars.load(npz.name)


def sessions(b: Bars) -> list[dict[str, Any]]:
    """Séances normales : index des bougies utiles (heure de New York) et amplitude 09:30-16:00."""
    mins, wd, day = ny_minutes(b.ts)
    want = {929: "c1529", 959: "c1559", 965: "o1605", 575: "o0935"}
    found: dict[int, dict[str, int]] = {}
    for m, key in ((929, "c1529"), (959, "c1559"), (965, "o1605"), (575, "o0935")):
        for i in np.flatnonzero(mins == m):
            found.setdefault(int(day[i]), {})[key] = int(i)
    rth = (mins >= 570) & (mins < 960)
    hi: dict[int, float] = {}
    lo: dict[int, float] = {}
    idx = np.flatnonzero(rth)
    if len(idx):
        cut = np.flatnonzero(np.diff(day[idx])) + 1
        for a, z in zip(np.r_[0, cut], np.r_[cut, len(idx)]):
            seg = idx[a:z]
            d = int(day[seg[0]])
            hi[d], lo[d] = float(b.h[seg].max()), float(b.l[seg].min())
    out = []
    for d in sorted(found):
        f = found[d]
        dd = date.fromordinal(d)
        if dd.weekday() >= 5 or dd in half_days(dd.year) or not {"c1529", "c1559"} <= set(f) or d not in hi:
            continue
        out.append({"day": dd, **f, "range": hi[d] - lo[d]})
    del want
    return out


def signals(b: Bars, ss: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for k, s in enumerate(ss):
        r = b.c[s["c1559"]] / b.c[s["c1529"]] - 1
        s["ret"] = float(r)
        if k < LOOKBACK or k + 2 >= len(ss) or k < ATR_N:
            continue
        past = np.abs([x["ret"] for x in ss[k - LOOKBACK:k]])
        atr = float(np.mean([x["range"] for x in ss[k - ATR_N:k]]))
        if abs(r) > np.percentile(past, PCT) and atr > 0:
            out.append({"k": k, "dir": -1 if r > 0 else 1, "atr": atr})
    return out


def trade(b: Bars, ss: list[dict[str, Any]], k: int, d: int, atr: float, cell: str, spread: float,
          fee_mult: float = 1.0) -> float | None:
    """R net d'un trade du sens d (+1 achat) déclenché à la séance k."""
    if cell == "B":
        if k + 1 >= len(ss) or "o0935" not in ss[k + 1]:
            return None
        i = ss[k + 1]["o0935"]
    else:
        if "o1605" not in ss[k]:
            return None
        i = ss[k]["o1605"]
    j = ss[k + 2]["c1559"]
    if (b.ts[j] - b.ts[i]) > 5 * 86400:          # trou de données (pas la vraie 2e séance suivante)
        return None
    e, x = float(b.o[i]), float(b.c[j])
    if cell == "C":
        stop = e - d * atr
        seg = b.l[i:j + 1] if d > 0 else b.h[i:j + 1]
        hit = np.flatnonzero(seg <= stop) if d > 0 else np.flatnonzero(seg >= stop)
        if len(hit):
            first = i + int(hit[0])
            o = float(b.o[first])
            x = min(o, stop) if d > 0 else max(o, stop)   # un trou au-delà du stop sort au prix d'ouverture
    cost = (spread + FIN_RATE * NIGHTS / 365 * e) * fee_mult
    return (d * (x - e) - cost) / atr


def judge(rs: list[float], days: list[date]) -> dict[str, Any]:
    a = np.array(rs)
    first = a[[d < SPLIT for d in days]]
    second = a[[d >= SPLIT for d in days]]
    return {"n": len(a), "mean_r": round(float(a.mean()), 4) if len(a) else None,
            "win": round(float((a > 0).mean()), 3) if len(a) else None,
            "total_r": round(float(a.sum()), 2),
            "r_2014_2019": round(float(first.mean()), 4) if len(first) else None,
            "r_2020_2026": round(float(second.mean()), 4) if len(second) else None}


def run_asset(asset: str, rng: np.random.Generator) -> dict[str, Any]:
    b = load(asset)
    ss = sessions(b)
    sig = signals(b, ss)
    res: dict[str, Any] = {"sessions": len(ss), "signals": len(sig),
                           "period": [str(ss[0]["day"]), str(ss[-1]["day"])]}
    pool = list(range(max(LOOKBACK, ATR_N), len(ss) - 2))
    for cell in CELLS:
        rows = []
        for s in sig:
            r = trade(b, ss, s["k"], s["dir"], s["atr"], cell, SPREAD[asset])
            if r is not None:
                r2 = trade(b, ss, s["k"], s["dir"], s["atr"], cell, SPREAD[asset], 2.0)
                rows.append((ss[s["k"]]["day"], s["dir"], r, r2, s["atr"]))
        rs = [x[2] for x in rows]
        out = judge(rs, [x[0] for x in rows])
        out["mean_r_fees_x2"] = round(float(np.mean([x[3] for x in rows])), 4) if rows else None
        for side, d in (("achats", 1), ("ventes", -1)):
            sub = [x for x in rows if x[1] == d]
            out[side] = judge([x[2] for x in sub], [x[0] for x in sub])
        # singes : mêmes sens, même mécanique, séances tirées au hasard
        atr_of = {}
        for k in pool:
            atr_of[k] = float(np.mean([x["range"] for x in ss[k - ATR_N:k]]))
        cache: dict[tuple[int, int], float | None] = {}
        means = []
        dirs = [x[1] for x in rows]
        for _ in range(N_MONKEYS):
            vals = []
            for d, k in zip(dirs, rng.choice(pool, size=len(dirs))):
                key = (int(k), d)
                if key not in cache:
                    cache[key] = trade(b, ss, int(k), d, atr_of[int(k)], cell, SPREAD[asset])
                if cache[key] is not None:
                    vals.append(cache[key])
            means.append(np.mean(vals) if vals else 0.0)
        beat = int(np.sum(np.array(means) < (out["mean_r"] or -9)))
        out["beats_monkeys"] = beat
        z = z_threshold(len(CELLS) * len(PAIRS))
        sd = float(np.std(rs, ddof=1)) if len(rs) > 1 else 0.0
        out["z"] = round(float(np.mean(rs)) / sd * np.sqrt(len(rs)), 2) if sd else None
        out["z_needed"] = round(z, 2)
        out["passes"] = bool(out["n"] >= 200 and (out["r_2014_2019"] or 0) > 0 and (out["r_2020_2026"] or 0) > 0
                             and (out["mean_r_fees_x2"] or 0) > 0 and beat >= 950 and (out["z"] or 0) >= z)
        years: dict[int, list[float]] = {}
        for x in rows:
            years.setdefault(x[0].year, []).append(x[2])
        out["by_year"] = {y: round(float(np.sum(v)), 2) for y, v in sorted(years.items())}
        res[cell] = out
    return res


def run() -> dict[str, Any]:
    rng = np.random.default_rng(69)
    out: dict[str, Any] = {"essai": 69, "rule": f"|rendement 15:30-16:00| > {PCT}e percentile des {LOOKBACK} séances, "
                                                "sens inverse, sortie 16:00 à la 2e séance suivante",
                           "spread_pts": SPREAD, "financing": f"{NIGHTS} nuits à {FIN_RATE:.0%}/an"}
    for asset in PAIRS:
        out[asset] = run_asset(asset, rng)
    out["transferable"] = {c: bool(out["nasdaq"][c]["passes"] and out["sp500"][c]["passes"]) for c in CELLS}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    r = run()
    for a in PAIRS:
        print(a, r[a]["sessions"], "séances", r[a]["signals"], "signaux", r[a]["period"])
        for c in CELLS:
            x = r[a][c]
            print(f"  {c}: n={x['n']} R={x['mean_r']} gagn={x['win']} 14-19={x['r_2014_2019']} 20-26={x['r_2020_2026']} "
                  f"frais×2={x['mean_r_fees_x2']} singes={x['beats_monkeys']} z={x['z']}/{x['z_needed']} "
                  f"achats={x['achats']['mean_r']} ventes={x['ventes']['mean_r']} passe={x['passes']}")
    print("transférable", r["transferable"])
