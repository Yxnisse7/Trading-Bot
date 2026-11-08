"""Essai 72 (HYPOTHESES.md) : cassure d'ouverture de Toby Crabel après une veille ID/NR4.

Veille ID/NR4 = contenue dans l'avant-veille et plus petite amplitude des 4 dernières séances.
Jour J : stop d'achat ouverture + marge, stop de vente ouverture − marge (marge = moyenne 10 séances de
min(haut − ouverture, ouverture − bas)), stop de protection = l'autre niveau, sortie à la clôture.

    python -m trading_bot.essai72          → data/essai72.json

Données hors dépôt : data/history/long/raw69/XAUUSD_*.csv → gold_1m.npz, {nasdaq,sp500,dax}_1m.npz, btc_30m.npz.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from .config import DATA_DIR
from .essai33 import LONG, UTC, Bars, z_threshold
from .essai64 import ny_minutes
from .essai71 import berlin_minutes, load_dax

FEES = {"gold": 0.30, "nasdaq": 1.3, "sp500": 0.6, "dax": 2.0}     # points aller-retour
BTC_FEE = 0.0006                                                   # fraction aller-retour
EXPECTED = {"gold": 1380, "nasdaq": 390, "sp500": 390, "dax": 510, "btc": 48}
STRETCH_N = 10
SPLIT = date(2020, 1, 1)
N_MONKEYS = 1000
N_CELLS = 7                                    # essais 72 et 73 ensemble
OUT = Path(DATA_DIR) / "essai72.json"


def load_gold() -> Bars:
    npz = LONG / "gold_1m.npz"
    if not npz.exists():
        rows = []
        for f in sorted((LONG / "raw69").glob("XAUUSD_*.csv")):
            for line in f.read_text(encoding="ascii", errors="ignore").splitlines():
                p = line.strip().split(";")
                if len(p) < 5 or len(p[0]) != 15:
                    continue
                t = datetime.strptime(p[0], "%Y%m%d %H%M%S").replace(tzinfo=UTC) + timedelta(hours=5)
                rows.append((int(t.timestamp()), *(float(x) for x in p[1:5])))
        a = np.array(sorted(set(rows)), dtype=float)
        np.savez_compressed(npz, ts=a[:, 0].astype(np.int64), o=a[:, 1], h=a[:, 2], l=a[:, 3], c=a[:, 4])
    return Bars.load(npz.name)


def session_ids(asset: str, b: Bars) -> np.ndarray:
    """Numéro de séance (date ordinale) de chaque bougie, −1 hors séance."""
    if asset == "btc":
        return (b.ts // 86400).astype(np.int64) + date(1970, 1, 1).toordinal()
    if asset == "dax":
        mins, wd, day = berlin_minutes(b.ts)
        return np.where((mins >= 540) & (mins < 1050) & (wd < 5), day, -1)
    if asset == "gold":                         # journée CME : 18:00 → 17:00 New York, datée du lendemain
        mins, wd, day = ny_minutes(b.ts + 6 * 3600)
        return np.where((mins < 23 * 60) & (wd < 5), day, -1)
    mins, wd, day = ny_minutes(b.ts)
    return np.where((mins >= 570) & (mins < 960) & (wd < 5), day, -1)


def sessions(asset: str, b: Bars) -> list[dict[str, Any]]:
    sid = session_ids(asset, b)
    idx = np.flatnonzero(sid >= 0)
    cut = np.flatnonzero(np.diff(sid[idx])) + 1
    out = []
    for a, z in zip(np.r_[0, cut], np.r_[cut, len(idx)]):
        seg = idx[a:z]
        if len(seg) < 0.6 * EXPECTED[asset]:
            continue
        out.append({"day": date.fromordinal(int(sid[seg[0]])), "a": int(seg[0]), "z": int(seg[-1]) + 1,
                    "o": float(b.o[seg[0]]), "h": float(b.h[seg].max()), "l": float(b.l[seg].min()),
                    "c": float(b.c[seg[-1]])})
    return out


def cost(asset: str, price: float) -> float:
    return price * BTC_FEE if asset == "btc" else FEES[asset]


def day_trade(asset: str, b: Bars, s: dict[str, Any], stretch: float, fee_mult: float = 1.0) -> dict[str, Any] | None:
    """Trade du jour s (ou None si aucun niveau touché). R net, 1 R = 2 × marge."""
    up, dn = s["o"] + stretch, s["o"] - stretch
    hi, lo, op = b.h[s["a"]:s["z"]], b.l[s["a"]:s["z"]], b.o[s["a"]:s["z"]]
    touch = np.flatnonzero((hi >= up) | (lo <= dn))
    if not len(touch):
        return None
    k = int(touch[0])
    risk = 2 * stretch
    c = cost(asset, s["o"]) * fee_mult
    if hi[k] >= up and lo[k] <= dn:                       # les deux dans la même bougie : perte de 1 R
        return {"r": -1 - c / risk, "s": 0}
    sign = 1 if hi[k] >= up else -1
    entry = max(up, op[k]) if sign > 0 else min(dn, op[k])
    stop = dn if sign > 0 else up
    rest_lo, rest_hi = lo[k + 1:], hi[k + 1:]
    hit = np.flatnonzero(rest_lo <= stop) if sign > 0 else np.flatnonzero(rest_hi >= stop)
    if len(hit):
        o = float(op[k + 1 + hit[0]])
        exit_ = min(o, stop) if sign > 0 else max(o, stop)
    else:
        exit_ = s["c"]
    return {"r": (sign * (exit_ - entry) - c) / risk, "s": sign}


def run_asset(asset: str, b: Bars, rng: np.random.Generator) -> dict[str, Any]:
    ss = sessions(asset, b)
    rows = []
    for k in range(max(STRETCH_N, 4), len(ss)):
        if (ss[k]["day"] - ss[k - 1]["day"]).days > 5:       # trou de données
            continue
        stretch = float(np.mean([min(x["h"] - x["o"], x["o"] - x["l"]) for x in ss[k - STRETCH_N:k]]))
        if stretch <= 0:
            continue
        p1, p2 = ss[k - 1], ss[k - 2]
        rng4 = [x["h"] - x["l"] for x in ss[k - 4:k]]
        idnr4 = p1["h"] <= p2["h"] and p1["l"] >= p2["l"] and rng4[-1] <= min(rng4)
        t = day_trade(asset, b, ss[k], stretch)
        if t is None:
            continue
        t2 = day_trade(asset, b, ss[k], stretch, 2.0)
        rows.append({"day": ss[k]["day"], "r": t["r"], "r2": t2["r"], "idnr4": idnr4})
    allr = np.array([x["r"] for x in rows])
    flt = [x for x in rows if x["idnr4"]]
    r = np.array([x["r"] for x in flt])
    first = r[[x["day"] < SPLIT for x in flt]]
    second = r[[x["day"] >= SPLIT for x in flt]]
    monkeys = np.array([allr[rng.choice(len(allr), size=len(r), replace=False)].mean() for _ in range(N_MONKEYS)])
    sd = float(r.std(ddof=1)) if len(r) > 1 else 0.0
    z = float(r.mean() / sd * np.sqrt(len(r))) if sd else 0.0
    out = {"sessions": len(ss), "period": [str(ss[0]["day"]), str(ss[-1]["day"])],
           "all_days": {"n": len(allr), "mean_r": round(float(allr.mean()), 4), "win": round(float((allr > 0).mean()), 3),
                        "r_2014_2019": round(float(allr[[x["day"] < SPLIT for x in rows]].mean()), 4),
                        "r_2020_2026": round(float(allr[[x["day"] >= SPLIT for x in rows]].mean()), 4)},
           "n": len(r), "mean_r": round(float(r.mean()), 4), "win": round(float((r > 0).mean()), 3),
           "r_2014_2019": round(float(first.mean()), 4) if len(first) else None,
           "r_2020_2026": round(float(second.mean()), 4) if len(second) else None,
           "mean_r_fees_x2": round(float(np.mean([x["r2"] for x in flt])), 4),
           "beats_monkeys": int(np.sum(monkeys < r.mean())), "z": round(z, 2), "z_needed": round(z_threshold(N_CELLS), 2)}
    out["passes"] = bool(out["n"] >= 200 and (out["r_2014_2019"] or 0) > 0 and (out["r_2020_2026"] or 0) > 0
                         and out["mean_r_fees_x2"] > 0 and out["beats_monkeys"] >= 950 and z >= out["z_needed"])
    years: dict[int, float] = {}
    for x in flt:
        years[x["day"].year] = years.get(x["day"].year, 0.0) + x["r"]
    out["by_year"] = {y: round(float(v), 2) for y, v in sorted(years.items())}
    return out


def run() -> dict[str, Any]:
    rng = np.random.default_rng(72)
    loaders = {"gold": load_gold, "nasdaq": lambda: Bars.load("nasdaq_1m.npz"),
               "sp500": lambda: Bars.load("sp500_1m.npz"), "dax": load_dax, "btc": lambda: Bars.load("btc_30m.npz")}
    out: dict[str, Any] = {"essai": 72, "rule": "veille ID/NR4 → cassure ouverture ± marge 10 séances, stop autre niveau, "
                                                "sortie clôture", "fees": {**FEES, "btc": "0,06 %"}}
    for asset, load in loaders.items():
        out[asset] = run_asset(asset, load(), rng)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    res = run()
    for a in ("gold", "nasdaq", "sp500", "dax", "btc"):
        x, base = res[a], res[a]["all_days"]
        print(a, x["period"], f"tous les jours n={base['n']} R={base['mean_r']} ({base['r_2014_2019']}/{base['r_2020_2026']})")
        print(f"   ID/NR4 n={x['n']} R={x['mean_r']} gagn={x['win']} moitiés={x['r_2014_2019']}/{x['r_2020_2026']} "
              f"frais×2={x['mean_r_fees_x2']} singes={x['beats_monkeys']} z={x['z']}/{x['z_needed']} passe={x['passes']}")
        print("   ", x["by_year"])
