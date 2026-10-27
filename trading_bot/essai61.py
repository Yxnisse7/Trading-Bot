"""Essai 61 (HYPOTHESES.md) : memecoins pump.fun, copier le portefeuille public du streamer AlxCooks.

    python -m trading_bot.essai61    → data/essai61.json

Données hors dépôt (data/history/pumpfun/) : early.npz (`essai38 --prep`) et streamer.parquet (son premier achat
dans chaque coin pendant les 10 premières minutes, et sa première vente ensuite, tirés du corpus avec duckdb).
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import NormalDist

import numpy as np

from .config import DATA_DIR
from .essai38 import DELAY, FEE, HALF, MAX_HOLD, MIN_TRADES, N_MONKEYS, OUT_END, OUT_START, PF_DIR, SIGNAL_WINDOW, stats
from .essai60 import AXIOM, DUR_BINS, run

DELAYS = {"D1": 1.0, "D3": 3.0, "D10": 10.0}
N_CELLS = 6
Z_MIN = NormalDist().inv_cdf(1 - 0.05 / N_CELLS)


def main() -> None:
    import pandas as pd

    d = np.load(PF_DIR / "early.npz")
    TS, P, VS, VT, start = d["ts"], d["p"], d["vs"], d["vt"], d["start"]
    launch, grad, mints = d["launch"], d["grad"], d["mints"]
    end_all = TS.max()
    ok = ~((launch >= OUT_START) & (launch < OUT_END)) & (launch < end_all - 70 * 60)
    tokens = np.flatnonzero(ok)
    day = ((launch - launch[ok].min()) // 86400).astype(int)
    rng = np.random.default_rng(61)
    idx_of = {m: i for i, m in enumerate(mints)}
    fee = FEE + AXIOM

    def arrays(t):
        s, e = start[t], start[t + 1]
        return TS[s:e], P[s:e], VS[s:e], VT[s:e]

    age_bins = np.arange(0, SIGNAL_WINDOW + 61, 30)
    pool: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for t in rng.permutation(tokens):
        ts = TS[start[t]:start[t + 1]]
        ages = ts - launch[t]
        for b, a0 in enumerate(age_bins):
            lst = pool.setdefault((day[t], b), [])
            if len(lst) >= 300:
                continue
            j = np.searchsorted(ages, a0, side="left")
            if j < len(ts) and ages[j] <= a0 + 60 and ts[j] < grad[t]:
                lst.append((t, j))
    cache: dict = {}

    def monkeys_for(key, kind, arg, dbin):
        ck = (key, kind, arg, dbin)
        if ck not in cache:
            vals = []
            for mt, mj in pool.get(key, []):
                marr = arrays(mt)
                vals.append(run(*marr, mj, grad[mt], kind, marr[0][mj] + dbin if kind == "at" else arg, fee))
            cache[ck] = np.array(vals)
        return cache[ck]

    sig = pd.read_parquet(PF_DIR / "streamer.parquet")
    ok_set = set(tokens.tolist())
    base = [(idx_of[m], b, None if pd.isna(s) else float(s)) for m, b, s in zip(sig.mint, sig.bts, sig.sts)
            if m in idx_of and idx_of[m] in ok_set]
    # son propre résultat (information) : entrée à son achat, sortie à sa vente, frais pump.fun seuls
    own = []
    for t, b, s in base:
        ts = TS[start[t]:start[t + 1]]
        j = max(np.searchsorted(ts, b, side="left"), 0)
        if j < len(ts) and ts[j] < grad[t]:
            own.append(run(*arrays(t), j, grad[t], "at", None if s is None else s - DELAY, FEE))
    cells: dict = {"info_son_resultat": stats(np.array(own))}
    for dname, delay in DELAYS.items():
        for xname in ("X1", "T20"):
            r, r2, lt, mk_sum, used = [], [], [], np.zeros(N_MONKEYS), 0
            for t, b, s in base:
                arr = arrays(t)
                j = np.searchsorted(arr[0], b + delay, side="left")
                if j >= len(arr[0]) or arr[0][j] >= grad[t]:
                    continue
                if xname == "X1":
                    kind, arg = "at", (None if s is None else s + delay - DELAY)
                    dur = MAX_HOLD if s is None else max(s + delay - arr[0][j], 0.0)
                    dbin = float(DUR_BINS[np.abs(DUR_BINS - dur).argmin()])
                else:
                    kind, arg, dbin = "trail", 0.20, None
                r.append(run(*arr, j, grad[t], kind, arg, fee))
                r2.append(run(*arr, j, grad[t], kind, arg, fee, 2.0))
                lt.append(launch[t])
                key = (day[t], min(int((arr[0][j] - launch[t]) // 30), len(age_bins) - 1))
                o = monkeys_for(key, kind, arg if kind == "trail" else None, dbin)
                if len(o):
                    mk_sum += o[rng.integers(0, len(o), N_MONKEYS)]
                    used += 1
            r, r2, lt = np.array(r), np.array(r2), np.array(lt)
            monkeys = mk_sum / max(used, 1)
            beaten = int((r.mean() > monkeys).sum())
            z = float((r.mean() - monkeys.mean()) / monkeys.std()) if monkeys.std() > 0 else 0.0
            last7 = lt >= end_all - 7 * 86400 - 70 * 60
            parts = {"moitie_1": r[lt < HALF], "moitie_2": r[lt >= HALF], "7_derniers_jours": r[last7]}
            st = stats(r)
            checks = {"trades": st["n"] >= MIN_TRADES, "net": st["moy"] > 0 and (st["pf"] or 0) >= 1.1,
                      **{k: bool(len(v) and v.mean() > 0) for k, v in parts.items()},
                      "frais_x2": bool(r2.mean() > 0), "singes": beaten >= 950}
            cells[f"{dname}_{xname}"] = {
                **st, "frais_x2": round(float(r2.mean()), 3),
                **{k: round(float(v.mean()), 3) if len(v) else None for k, v in parts.items()},
                "singes_battus": beaten, "singes_moy": round(float(monkeys.mean()), 3), "z": round(z, 2),
                "controles": checks, "prouvee": all(checks.values()) and z > Z_MIN}
            print(dname, xname, cells[f"{dname}_{xname}"], flush=True)
    out = {"essai": 61, "seuil_z": round(Z_MIN, 2), "cellules": cells}
    Path(DATA_DIR, "essai61.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
