"""Essai 71 (HYPOTHESES.md) : le DAX rattrape le mouvement américain de la veille.

Signal : S&P 500 entre la clôture du DAX (17:30 Francfort) et la clôture américaine (16:00 New York).
Trade : DAX le lendemain, ouverture 09:05 → 17:30 Francfort, dans le sens du signal.

    python -m trading_bot.essai71          → data/essai71.json

Données hors dépôt : data/history/long/raw69/GRXEUR_*.csv (HistData 1 min, heure fixe UTC−5),
converties une fois en data/history/long/dax_1m.npz ; sp500_1m.npz (essai 69).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np

from .config import DATA_DIR
from .essai33 import LONG, UTC, Bars, z_threshold
from .essai64 import ny_minutes

BERLIN = ZoneInfo("Europe/Berlin")
COST = 2.0                                     # points DAX, aller-retour
PCT, LOOKBACK, ATR_N = 80, 120, 14
SPLIT = date(2020, 1, 1)
N_MONKEYS = 1000
N_CELLS = 4                                    # essais 70 et 71 ensemble
CELLS = ("D1", "D2")
OUT = Path(DATA_DIR) / "essai71.json"


def load_dax() -> Bars:
    npz = LONG / "dax_1m.npz"
    if not npz.exists():
        rows = []
        for f in sorted((LONG / "raw69").glob("GRXEUR_*.csv")):
            for line in f.read_text(encoding="ascii", errors="ignore").splitlines():
                p = line.strip().split(";")
                if len(p) < 5 or len(p[0]) != 15:
                    continue
                t = datetime.strptime(p[0], "%Y%m%d %H%M%S").replace(tzinfo=UTC) + timedelta(hours=5)
                rows.append((int(t.timestamp()), *(float(x) for x in p[1:5])))
        a = np.array(sorted(set(rows)), dtype=float)
        np.savez_compressed(npz, ts=a[:, 0].astype(np.int64), o=a[:, 1], h=a[:, 2], l=a[:, 3], c=a[:, 4])
    return Bars.load(npz.name)


def berlin_minutes(ts: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Minute de la journée, jour de la semaine et date, à l'heure de Francfort."""
    mins, wd, day = np.empty(len(ts), np.int32), np.empty(len(ts), np.int8), np.empty(len(ts), np.int32)
    hour = ts // 3600
    cut = np.flatnonzero(np.diff(hour)) + 1
    for a, b in zip(np.r_[0, cut], np.r_[cut, len(ts)]):
        d = datetime.fromtimestamp(int(ts[a]), UTC).astimezone(BERLIN)
        mins[a:b] = d.hour * 60 + (ts[a:b] % 3600) // 60
        wd[a:b] = d.weekday()
        day[a:b] = d.toordinal()
    return mins, wd, day


def dax_sessions(b: Bars) -> list[dict[str, Any]]:
    """Séances DAX : ouverture de la bougie 09:05, clôture de la bougie 17:29, amplitude 09:00-17:30, heure UTC de 17:29."""
    mins, wd, day = berlin_minutes(b.ts)
    rth = (mins >= 540) & (mins < 1050) & (wd < 5)
    idx = np.flatnonzero(rth)
    out = []
    cut = np.flatnonzero(np.diff(day[idx])) + 1
    for a, z in zip(np.r_[0, cut], np.r_[cut, len(idx)]):
        seg = idx[a:z]
        m = mins[seg]
        i0 = seg[m == 545]
        i1 = seg[m == 1049]
        if not len(i0) or not len(i1):
            continue
        out.append({"day": date.fromordinal(int(day[seg[0]])), "open": float(b.o[i0[0]]),
                    "close": float(b.c[i1[0]]), "t_close": int(b.ts[i1[0]]) + 60,
                    "range": float(b.h[seg].max() - b.l[seg].min())})
    return out


def us_moves(dax: list[dict[str, Any]]) -> dict[date, float]:
    """Pour chaque jour DAX : rendement du S&P de la clôture DAX (17:30 Francfort) à 16:00 New York, même jour."""
    sp = Bars.load("sp500_1m.npz")
    mins, wd, day = ny_minutes(sp.ts)
    close_ny: dict[int, int] = {int(day[i]): int(i) for i in np.flatnonzero(mins == 959)}
    out = {}
    for s in dax:
        d = s["day"].toordinal()
        if d not in close_ny:
            continue
        j = int(np.searchsorted(sp.ts, s["t_close"] - 60))        # bougie S&P 17:29 Francfort
        if j >= len(sp.ts) or sp.ts[j] != s["t_close"] - 60:
            continue
        k = close_ny[d]
        if k <= j:
            continue
        out[s["day"]] = float(sp.c[k] / sp.c[j] - 1)
    return out


def trade(ss: list[dict[str, Any]], k: int, d: int, atr: float, fee_mult: float = 1.0) -> tuple[float, float]:
    """R net (entrée 09:05 de la séance k+1, sortie 17:30) et trou déjà passé, dans le sens d."""
    nxt, prev = ss[k + 1], ss[k]
    r = (d * (nxt["close"] - nxt["open"]) - COST * fee_mult) / atr
    gap = d * (nxt["open"] - prev["close"]) / atr
    return r, gap


def judge(rs: np.ndarray, days: list[date]) -> dict[str, Any]:
    first = rs[[d < SPLIT for d in days]]
    second = rs[[d >= SPLIT for d in days]]
    return {"n": len(rs), "mean_r": round(float(rs.mean()), 4) if len(rs) else None,
            "win": round(float((rs > 0).mean()), 3) if len(rs) else None,
            "first_half": round(float(first.mean()), 4) if len(first) else None,
            "second_half": round(float(second.mean()), 4) if len(second) else None}


def run() -> dict[str, Any]:
    rng = np.random.default_rng(71)
    ss = dax_sessions(load_dax())
    mv = us_moves(ss)
    atr = {k: float(np.mean([x["range"] for x in ss[k - ATR_N:k]])) for k in range(ATR_N, len(ss))}
    ok = [k for k in range(max(ATR_N, 1), len(ss) - 1)
          if ss[k]["day"] in mv and (ss[k + 1]["day"] - ss[k]["day"]).days <= 4 and atr[k] > 0]
    out: dict[str, Any] = {"essai": 71, "sessions": len(ss), "days_with_signal": len(ok),
                           "period": [str(ss[0]["day"]), str(ss[-1]["day"])],
                           "rule": "S&P 17:30 Francfort → 16:00 NY ; DAX lendemain 09:05 → 17:30 dans le même sens",
                           "cost_pts": COST}
    pool = ok
    for cell in CELLS:
        rows = []
        for n, k in enumerate(ok):
            m = mv[ss[k]["day"]]
            if m == 0:
                continue
            if cell == "D2":
                past = [abs(mv[ss[q]["day"]]) for q in ok[max(0, n - LOOKBACK):n]]
                if len(past) < LOOKBACK or abs(m) <= np.percentile(past, PCT):
                    continue
            d = 1 if m > 0 else -1
            r, gap = trade(ss, k, d, atr[k])
            r2, _ = trade(ss, k, d, atr[k], 2.0)
            rows.append((ss[k + 1]["day"], d, r, r2, gap, ss[k + 1]["close"] - ss[k + 1]["open"]))
        rs = np.array([x[2] for x in rows])
        res = judge(rs, [x[0] for x in rows])
        res["mean_r_fees_x2"] = round(float(np.mean([x[3] for x in rows])), 4)
        res["gap_already_passed_r"] = round(float(np.mean([x[4] for x in rows])), 4)
        res["gap_in_signal_direction"] = round(float(np.mean([x[4] > 0 for x in rows])), 3)
        for side, dd in (("achats", 1), ("ventes", -1)):
            sub = [x for x in rows if x[1] == dd]
            res[side] = judge(np.array([x[2] for x in sub]), [x[0] for x in sub])
        dirs = np.array([x[1] for x in rows])
        pk = np.array(pool)
        move = np.array([ss[k + 1]["close"] - ss[k + 1]["open"] for k in pk])
        at = np.array([atr[k] for k in pk])
        means = np.empty(N_MONKEYS)
        for t in range(N_MONKEYS):
            pick = rng.integers(0, len(pk), size=len(dirs))
            means[t] = float(np.mean((dirs * move[pick] - COST) / at[pick]))
        res["beats_monkeys"] = int(np.sum(means < rs.mean()))
        sd = float(rs.std(ddof=1))
        res["z"] = round(float(rs.mean() / sd * np.sqrt(len(rs))), 2)
        res["z_needed"] = round(z_threshold(N_CELLS), 2)
        res["passes"] = bool(res["n"] >= 200 and (res["first_half"] or 0) > 0 and (res["second_half"] or 0) > 0
                             and res["mean_r_fees_x2"] > 0 and res["beats_monkeys"] >= 950
                             and res["z"] >= res["z_needed"])
        years: dict[int, float] = {}
        for x in rows:
            years[x[0].year] = years.get(x[0].year, 0.0) + x[2]
        res["by_year"] = {y: round(v, 2) for y, v in sorted(years.items())}
        out[cell] = res
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    r = run()
    print(r["sessions"], "séances", r["days_with_signal"], "jours avec signal", r["period"])
    for c in CELLS:
        x = r[c]
        print(f"{c}: n={x['n']} R={x['mean_r']} gagn={x['win']} moitiés={x['first_half']}/{x['second_half']} "
              f"frais×2={x['mean_r_fees_x2']} trou={x['gap_already_passed_r']} ({x['gap_in_signal_direction']}) "
              f"singes={x['beats_monkeys']} z={x['z']}/{x['z_needed']} achats={x['achats']['mean_r']} "
              f"ventes={x['ventes']['mean_r']} passe={x['passes']}")
        print("   ", x["by_year"])
