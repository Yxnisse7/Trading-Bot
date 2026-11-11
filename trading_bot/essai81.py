"""Essai 81 : les autres marchés comme filtre de nos stratégies (pré-enregistré dans HYPOTHESES.md le 11/11/2026).

    python -m trading_bot.essai81 data     → télécharge VIX, taux 10 ans, dollar (FRED) et financement BTC (Binance)
    python -m trading_bot.essai81          → data/essai81.json

Question de Yanisse : que donner à l'agent IA en plus des prix du marché tradé ? Avant de lui confier ces chiffres,
on mesure s'ils trient quoi que ce soit : valeur de la veille, seuil calculé sur le passé seulement.
"""
from __future__ import annotations

import csv
import io
import json
import pickle
import sys
import urllib.request
import zipfile
from bisect import bisect_left
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from .config import DATA_DIR
from .essai33 import LONG

NY = ZoneInfo("America/New_York")
RAW = LONG / "essai81"
OUT = Path(DATA_DIR) / "essai81.json"
TRADES = LONG / "essai76_trades.pkl"
SOURCES = ("noise_area_v2", "bot", "donchian_1h", "cassure_williams", "W3", "nuit_asie")
BTC = ("donchian_1h", "cassure_williams", "W3")
FRED = {"vix": "VIXCLS", "us10y": "DGS10", "dollar": "DTWEXBGS"}
WINDOW, FUND_WINDOW = 250, 270
Z_MIN, N_MIN, CELLS = 3.2, 100, 33
SPLIT, SPLIT_FUND = date(2020, 1, 1), date(2023, 1, 1)
FLAGS = {"F1": "VIX haut", "F2": "VIX qui bondit", "F3": "VIX très bas", "F4": "taux 10 ans qui bouge fort",
         "F5": "dollar qui bouge fort", "F6": "financement Bitcoin extrême"}


def download() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for name, sid in FRED.items():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd=2012-06-01"
        (RAW / f"{name}.csv").write_bytes(urllib.request.urlopen(url, timeout=60).read())
        print(name, "ok", flush=True)
    rows = []
    for y in range(2020, 2027):
        for m in range(1, 13):
            url = ("https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/"
                   f"BTCUSDT-fundingRate-{y}-{m:02d}.zip")
            try:
                z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(url, timeout=60).read()))
            except Exception:                                    # mois pas encore publié
                continue
            for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), "utf-8")):
                if r and r[0].isdigit():
                    rows.append((int(r[0]) // 1000, float(r[2])))
    rows.sort()
    (RAW / "funding.json").write_text(json.dumps(rows))
    print("financement", len(rows), flush=True)


def series(name: str) -> tuple[list[date], np.ndarray]:
    days, vals = [], []
    for r in csv.reader((RAW / f"{name}.csv").read_text().splitlines()[1:]):
        try:
            vals.append(float(r[1]))
        except (ValueError, IndexError):
            continue
        days.append(date.fromisoformat(r[0]))
    return days, np.array(vals)


def pct_rank(x: np.ndarray, window: int) -> np.ndarray:
    """Rang (0-1) de chaque valeur parmi les `window` valeurs PRÉCÉDENTES ; nan tant que la fenêtre n'est pas pleine."""
    out = np.full(len(x), np.nan)
    for i in range(window, len(x)):
        out[i] = float(np.mean(x[i - window:i] < x[i]))
    return out


def daily_flags() -> dict[str, tuple[list[date], np.ndarray]]:
    dv, vix = series("vix")
    dt, ten = series("us10y")
    dd, usd = series("dollar")
    rk = pct_rank(vix, WINDOW)
    jump = np.concatenate([[np.nan], vix[1:] / vix[:-1] - 1])
    m10 = np.abs(np.concatenate([[np.nan] * 5, ten[5:] - ten[:-5]]))
    musd = np.abs(np.concatenate([[np.nan] * 5, usd[5:] / usd[:-5] - 1]))
    r10 = pct_rank(np.nan_to_num(m10), WINDOW)
    rusd = pct_rank(np.nan_to_num(musd), WINDOW)
    r10[:WINDOW + 5] = np.nan
    rusd[:WINDOW + 5] = np.nan
    nan = np.isnan
    return {"F1": (dv, np.where(nan(rk), np.nan, rk > 0.8)), "F2": (dv, np.where(nan(jump), np.nan, jump >= 0.10)),
            "F3": (dv, np.where(nan(rk), np.nan, rk < 0.2)), "F4": (dt, np.where(nan(r10), np.nan, r10 > 0.8)),
            "F5": (dd, np.where(nan(rusd), np.nan, rusd > 0.8))}


def funding_flag() -> tuple[list[int], np.ndarray]:
    rows = json.loads((RAW / "funding.json").read_text())
    ts = [r[0] for r in rows]
    rk = pct_rank(np.abs(np.array([r[1] for r in rows])), FUND_WINDOW)
    return ts, np.where(np.isnan(rk), np.nan, rk > 0.8)


def cell(r: np.ndarray, f: np.ndarray, days: list[date], split: date) -> dict:
    """Écart entre trades signalés et non signalés, et son signe dans chaque moitié."""
    def stat(mask):
        a, b = r[mask & (f == 1)], r[mask & (f == 0)]
        if len(a) < 2 or len(b) < 2:
            return {"n": int(len(a)), "r": None, "autres": None, "z": None}
        se = float(np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)))
        return {"n": int(len(a)), "r": round(float(a.mean()), 3), "autres": round(float(b.mean()), 3),
                "z": round(float((a.mean() - b.mean()) / se), 2) if se > 0 else None}
    ok = ~np.isnan(f)
    first = np.array([d < split for d in days])
    tout, h1, h2 = stat(ok), stat(ok & first), stat(ok & ~first)
    same = (h1["z"] is not None and h2["z"] is not None and h1["z"] < 0 and h2["z"] < 0)
    passe = bool(tout["n"] >= N_MIN and tout["r"] is not None and tout["r"] < 0 and tout["z"] <= -Z_MIN and same)
    piste = bool(not passe and same and h1["z"] <= -2 and h2["z"] <= -2)
    return {"tout": tout, "avant": h1, "apres": h2, "passe": passe, "piste": piste}


def run() -> dict:
    trades = [t for t in pickle.load(open(TRADES, "rb")) if t["strat"] in SOURCES]
    flags = daily_flags()
    fts, ff = funding_flag()
    res = {"cells": {}, "n_cells": 0}
    for s in SOURCES:
        ts = [t for t in trades if t["strat"] == s]
        r = np.array([t["r"] for t in ts])
        days = [datetime.fromtimestamp(t["ts"], NY).date() for t in ts]
        for k, (dd, fv) in flags.items():
            idx = [bisect_left(dd, d) - 1 for d in days]            # dernière séance AVANT le jour du trade
            f = np.array([fv[i] if i >= 0 else np.nan for i in idx])
            res["cells"][f"{s}:{k}"] = cell(r, f, days, SPLIT)
        if s in BTC:
            idx = [bisect_left(fts, t["ts"]) - 1 for t in ts]       # dernier financement réglé avant l'entrée
            f = np.array([ff[i] if i >= 0 else np.nan for i in idx])
            res["cells"][f"{s}:F6"] = cell(r, f, days, SPLIT_FUND)
    res["n_cells"] = len(res["cells"])
    res["passent"] = [k for k, c in res["cells"].items() if c["passe"]]
    res["pistes"] = [k for k, c in res["cells"].items() if c["piste"]]
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "data":
        download()
    else:
        out = run()
        for k, c in out["cells"].items():
            t, a, b = c["tout"], c["avant"], c["apres"]
            print(f"{k:22s} n {t['n']:4d} R {t['r']} autres {t['autres']} z {t['z']} | avant z {a['z']} | après z {b['z']}"
                  f"{'  PASSE' if c['passe'] else '  piste' if c['piste'] else ''}")
        print(out["n_cells"], "cellules ; passent :", out["passent"], "; pistes :", out["pistes"])
