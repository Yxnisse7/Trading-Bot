"""Essai 62 (HYPOTHESES.md) : memecoins pump.fun, copier un portefeuille et sortir à un petit gain net fixe.

    python -m trading_bot.essai62    → data/essai62.json

Données hors dépôt (data/history/pumpfun/) : early.npz, streamer.parquet (AlxCooks) et copy_signals.parquet
(100 meilleurs portefeuilles de juin), voir essais 38, 60 et 61.
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import NormalDist

import numpy as np

from .config import DATA_DIR
from .essai38 import (DELAY, FEE, HALF, MAX_HOLD, MIN_TRADES, N_MONKEYS, NET_FEE, OUT_END, OUT_START, PF_DIR,
                      SIGNAL_WINDOW, STAKE, stats)
from .essai60 import DUR_BINS, TEST_START, WEEK2

COPY_DELAY = 1.0
GAINS = {"G5": 5.0, "G10": 10.0, "G20": 20.0}
N_CELLS = 6
Z_MIN = NormalDist().inv_cdf(1 - 0.05 / N_CELLS)


def run_tp(ts, p, vs, vt, j, end_ts, gain, sell_at, fee=FEE, fee_mult=1.0):
    """Rendement net (%) : vente dès +gain % net possible, sinon à sell_at (heure), au plus tard 60 min.
    Renvoie (rendement, gain touché ?)."""
    fee, net = fee * fee_mult, NET_FEE * fee_mult
    deadline = min(ts[j] + MAX_HOLD, end_ts)
    hi = np.searchsorted(ts, deadline, side="right")
    x = STAKE * (1 - fee)
    held = x / (p[j] * (1 + x / vs[j]))
    cost = STAKE + NET_FEE

    def ret(e):
        return 100 * (held * p[e] / (1 + held / vt[e]) * (1 - fee) - net - cost) / cost

    seg = np.arange(j, hi)
    vals = 100 * (held * p[seg] / (1 + held / vt[seg]) * (1 - fee) - net - cost) / cost
    hit = np.flatnonzero(vals >= gain)
    if len(hit):
        e = min(np.searchsorted(ts, ts[j + hit[0]] + DELAY, side="left"), hi - 1)
        if sell_at is None or ts[j + hit[0]] < sell_at:
            return ret(max(e, j)), True
    if sell_at is not None and sell_at < deadline:
        e = min(np.searchsorted(ts, sell_at, side="left"), hi - 1)
        return ret(max(e, j)), False
    return ret(hi - 1), False


def main() -> None:
    import pandas as pd

    d = np.load(PF_DIR / "early.npz")
    TS, P, VS, VT, start = d["ts"], d["p"], d["vs"], d["vt"], d["start"]
    launch, grad, mints = d["launch"], d["grad"], d["mints"]
    end_all = TS.max()
    ok = ~((launch >= OUT_START) & (launch < OUT_END)) & (launch < end_all - 70 * 60)
    tokens = np.flatnonzero(ok)
    ok_set = set(tokens.tolist())
    day = ((launch - launch[ok].min()) // 86400).astype(int)
    rng = np.random.default_rng(62)
    idx_of = {m: i for i, m in enumerate(mints)}

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

    def monkeys_for(key, gain, dbin):
        ck = (key, gain, dbin)
        if ck not in cache:
            vals = []
            for mt, mj in pool.get(key, []):
                marr = arrays(mt)
                vals.append(run_tp(*marr, mj, grad[mt], gain, marr[0][mj] + dbin)[0])
            cache[ck] = np.array(vals)
        return cache[ck]

    sources = {}
    st_ = pd.read_parquet(PF_DIR / "streamer.parquet")
    sources["S1"] = ([(idx_of[m], b, None if pd.isna(s) else float(s)) for m, b, s in zip(st_.mint, st_.bts, st_.sts)
                      if m in idx_of and idx_of[m] in ok_set], False)
    sig = pd.read_parquet(PF_DIR / "copy_signals.parquet").sort_values("bts")
    first = sig[sig.rk <= 100].drop_duplicates("mint")
    sources["S2"] = ([(idx_of[m], b, None if pd.isna(s) else float(s)) for m, b, s in zip(first.mint, first.bts, first.sts)
                      if m in idx_of and idx_of[m] in ok_set and launch[idx_of[m]] >= TEST_START], True)
    cells = {}
    for sname, (base, weeks) in sources.items():
        for gname, gain in GAINS.items():
            r, r2, lt, hits, mk_sum, used = [], [], [], 0, np.zeros(N_MONKEYS), 0
            for t, b, s in base:
                arr = arrays(t)
                j = np.searchsorted(arr[0], b + COPY_DELAY, side="left")
                if j >= len(arr[0]) or arr[0][j] >= grad[t]:
                    continue
                sell_at = None if s is None else s + COPY_DELAY
                v, h = run_tp(*arr, j, grad[t], gain, sell_at)
                r.append(v)
                hits += h
                r2.append(run_tp(*arr, j, grad[t], gain, sell_at, fee_mult=2.0)[0])
                lt.append(launch[t])
                dur = MAX_HOLD if sell_at is None else max(sell_at - arr[0][j], 0.0)
                dbin = float(DUR_BINS[np.abs(DUR_BINS - dur).argmin()])
                key = (day[t], min(int((arr[0][j] - launch[t]) // 30), len(age_bins) - 1))
                o = monkeys_for(key, gain, dbin)
                if len(o):
                    mk_sum += o[rng.integers(0, len(o), N_MONKEYS)]
                    used += 1
            r, r2, lt = np.array(r), np.array(r2), np.array(lt)
            monkeys = mk_sum / max(used, 1)
            beaten = int((r.mean() > monkeys).sum())
            z = float((r.mean() - monkeys.mean()) / monkeys.std()) if monkeys.std() > 0 else 0.0
            if weeks:
                parts = {"semaine_1": r[lt < WEEK2], "semaine_2": r[lt >= WEEK2]}
            else:
                last7 = lt >= end_all - 7 * 86400 - 70 * 60
                parts = {"moitie_1": r[lt < HALF], "moitie_2": r[lt >= HALF], "7_derniers_jours": r[last7]}
            st = stats(r)
            checks = {"trades": st["n"] >= MIN_TRADES, "net": st["moy"] > 0 and (st["pf"] or 0) >= 1.1,
                      **{k: bool(len(v) and v.mean() > 0) for k, v in parts.items()},
                      "frais_x2": bool(r2.mean() > 0), "singes": beaten >= 950}
            cells[f"{sname}_{gname}"] = {
                **st, "gain_touche_pct": round(100 * hits / max(len(r), 1), 1),
                "frais_x2": round(float(r2.mean()), 3),
                **{k: round(float(v.mean()), 3) if len(v) else None for k, v in parts.items()},
                "singes_battus": beaten, "singes_moy": round(float(monkeys.mean()), 3), "z": round(z, 2),
                "controles": checks, "prouvee": all(checks.values()) and z > Z_MIN}
            print(sname, gname, cells[f"{sname}_{gname}"], flush=True)
    out = {"essai": 62, "seuil_z": round(Z_MIN, 2), "cellules": cells}
    Path(DATA_DIR, "essai62.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
