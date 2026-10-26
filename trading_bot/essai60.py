"""Essai 60 (HYPOTHESES.md) : memecoins pump.fun, copier les meilleurs portefeuilles, sortir en 3 lots.

    python -m trading_bot.essai60    → data/essai60.json

Données hors dépôt (data/history/pumpfun/) : early.npz (`essai38 --prep`), copy_signals.parquet et
top_wallets.parquet (classement des portefeuilles de juin, achats copiés de juillet, faits avec duckdb sur le corpus).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np

from .config import DATA_DIR
from .essai38 import (DELAY, ENTRIES, FEE, HALF, MAX_HOLD, MIN_TRADES, N_MONKEYS, NET_FEE, OUT_END, OUT_START,
                      PF_DIR, SIGNAL_WINDOW, STAKE, stats)

UTC = timezone.utc
AXIOM = 0.01                # par côté, en plus de pump.fun
TEST_START = datetime(2026, 7, 1, tzinfo=UTC).timestamp()
WEEK2 = datetime(2026, 7, 8, tzinfo=UTC).timestamp()
N_CELLS = 9
DUR_BINS = np.array([10, 30, 60, 120, 300, 600, 1200, 3600], float)   # durées des singes de X1 (s)
Z_MIN = NormalDist().inv_cdf(1 - 0.05 / N_CELLS)


def run(ts, p, vs, vt, j, end_ts, kind, arg=None, fee=FEE, fee_mult=1.0) -> float:
    """Rendement net (%) d'une entrée exécutée à l'échange j. kind : trail (arg = 0,20), at (arg = heure de vente),
    lots (1/3 à ×2, 1/3 à ×3, reste au suiveur 20 %)."""
    fee = fee * fee_mult
    net = NET_FEE * fee_mult
    deadline = min(ts[j] + MAX_HOLD, end_ts)
    hi = np.searchsorted(ts, deadline, side="right")
    seg = p[j:hi]

    def exec_idx(trigger_ts):
        e = np.searchsorted(ts, trigger_ts + DELAY, side="left")
        return max(min(e, hi - 1), j)

    x = STAKE * (1 - fee)
    held = x / (p[j] * (1 + x / vs[j]))
    proceeds, txs = 0.0, 1
    events = []                                    # (heure, part des jetons de départ, tout le reste ?)
    trail_hit = np.flatnonzero(seg < 0.8 * np.maximum.accumulate(seg)) if kind in ("trail", "lots") else []
    if kind == "trail":
        trail_hit = np.flatnonzero(seg < (1 - arg) * np.maximum.accumulate(seg))
    if len(trail_hit):
        events.append((ts[j + trail_hit[0]], 1.0, True))
    if kind == "at" and arg is not None and arg < deadline:
        events.append((arg, 1.0, True))
    if kind == "lots":
        for mult in (2.0, 3.0):
            h = np.flatnonzero(seg >= mult * p[j])
            if len(h):
                events.append((ts[j + h[0]], 1 / 3, False))
    start_tokens = held
    for t_ev, part, all_rest in sorted(events):
        if held <= 0:
            break
        e = exec_idx(t_ev)
        q = held if all_rest else min(held, start_tokens * part)
        proceeds += q * p[e] / (1 + q / vt[e]) * (1 - fee)
        held -= q
        txs += 1
    if held > 0:
        e = hi - 1
        proceeds += held * p[e] / (1 + held / vt[e]) * (1 - fee)
        txs += 1
    cost = STAKE + NET_FEE
    return 100 * (proceeds - (txs - 1) * net - cost) / cost


def main() -> None:
    import pandas as pd

    d = np.load(PF_DIR / "early.npz")
    TS, P, VS, VT, start = d["ts"], d["p"], d["vs"], d["vt"], d["start"]
    launch, grad, mints = d["launch"], d["grad"], d["mints"]
    end_all = TS.max()
    ok = ~((launch >= OUT_START) & (launch < OUT_END)) & (launch < end_all - 70 * 60)
    tokens = np.flatnonzero(ok)
    day = ((launch - launch[ok].min()) // 86400).astype(int)
    rng = np.random.default_rng(60)
    idx_of = {m: i for i, m in enumerate(mints)}

    def arrays(t):
        s, e = start[t], start[t + 1]
        return TS[s:e], P[s:e], VS[s:e], VT[s:e]

    # réserve des singes (comme l'essai 38) : jour × tranche d'âge de 30 s, 300 coins au plus
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

    def evaluate(name, trades, fee, weeks):
        """trades : liste de (coin, j, kind, arg, durée pour les singes ou None)."""
        r, r2, lt, keys, mk = [], [], [], [], []
        for t, j, kind, arg, _ in trades:
            arr = arrays(t)
            r.append(run(*arr, j, grad[t], kind, arg, fee))
            r2.append(run(*arr, j, grad[t], kind, arg, fee, 2.0))
            lt.append(launch[t])
            age = arr[0][j] - launch[t]
            keys.append((day[t], min(int(age // 30), len(age_bins) - 1)))
        r, r2, lt = np.array(r), np.array(r2), np.array(lt)
        sums, used = np.zeros(N_MONKEYS), []
        for i, (t, j, kind, arg, dur) in enumerate(trades):
            cands = pool.get(keys[i], [])
            if not cands:
                continue
            dbin = None if kind != "at" else float(DUR_BINS[np.abs(DUR_BINS - (dur or MAX_HOLD)).argmin()])
            ck = (keys[i], kind, arg, dbin, fee)
            if ck not in cache:
                vals = []
                for mt, mj in cands:
                    marr = arrays(mt)
                    a2 = marr[0][mj] + dbin if kind == "at" else arg
                    vals.append(run(*marr, mj, grad[mt], kind, a2, fee))
                cache[ck] = np.array(vals)
            o = cache[ck]
            sums += o[rng.integers(0, len(o), N_MONKEYS)]
            used.append(i)
        monkeys = sums / max(len(used), 1)
        real_mean = r[used].mean() if used else np.nan
        beaten = int((real_mean > monkeys).sum())
        z = float((real_mean - monkeys.mean()) / monkeys.std()) if monkeys.std() > 0 else 0.0
        st = stats(r)
        parts = {}
        if weeks:
            parts["semaine_1"] = r[lt < WEEK2]
            parts["semaine_2"] = r[lt >= WEEK2]
        else:
            last7 = lt >= end_all - 7 * 86400 - 70 * 60
            parts["moitie_1"], parts["moitie_2"], parts["7_derniers_jours"] = r[lt < HALF], r[lt >= HALF], r[last7]
        checks = {"trades": st["n"] >= MIN_TRADES, "net": st["n"] > 0 and st["moy"] > 0 and (st["pf"] or 0) >= 1.1,
                  **{k: bool(len(v) and v.mean() > 0) for k, v in parts.items()},
                  "frais_x2": bool(len(r2) and r2.mean() > 0), "singes": beaten >= 950}
        cell = {**st, "frais_x2": round(float(r2.mean()), 3) if len(r2) else None,
                **{k: round(float(v.mean()), 3) if len(v) else None for k, v in parts.items()},
                "singes_battus": beaten, "singes_moy": round(float(monkeys.mean()), 3), "z": round(z, 2),
                "controles": checks, "prouvee": all(checks.values()) and z > Z_MIN}
        print(name, cell, flush=True)
        return cell

    cells = {}
    # partie A : copie des portefeuilles
    sig = pd.read_parquet(PF_DIR / "copy_signals.parquet").sort_values("bts")
    test_ok = set(t for t in tokens if launch[t] >= TEST_START)
    for wname, rank in (("W100", 100), ("W1000", 1000)):
        first = sig[sig.rk <= rank].drop_duplicates("mint")
        base = []
        for m, bts, sts in zip(first.mint, first.bts, first.sts):
            t = idx_of.get(m)
            if t is None or t not in test_ok:
                continue
            ts = TS[start[t]:start[t + 1]]
            j = np.searchsorted(ts, bts + DELAY, side="left")
            if j < len(ts) and ts[j] < grad[t]:
                base.append((t, j, None if pd.isna(sts) else float(sts)))
        for xname in ("X1", "T20", "L3"):
            trades = []
            for t, j, sts in base:
                if xname == "X1":
                    dur = (sts + DELAY - TS[start[t] + j]) if sts is not None else MAX_HOLD
                    trades.append((t, j, "at", sts, max(dur, 0.0)))
                elif xname == "T20":
                    trades.append((t, j, "trail", 0.20, None))
                else:
                    trades.append((t, j, "lots", None, None))
            cells[f"{wname}_{xname}"] = evaluate(f"{wname}_{xname}", trades, FEE + AXIOM, weeks=True)
    # partie B : sortie en 3 lots sur les entrées de l'essai 38
    for ename in ("K2", "K3", "K5"):
        mult = ENTRIES[ename]
        trades = []
        for t in tokens:
            ts, p = TS[start[t]:start[t + 1]], P[start[t]:start[t + 1]]
            if len(ts) < 2:
                continue
            win = np.flatnonzero((p >= mult * p[0]) & (ts <= launch[t] + SIGNAL_WINDOW))
            if not len(win):
                continue
            j = np.searchsorted(ts, ts[win[0]] + DELAY, side="left")
            if j < len(ts) and ts[j] < grad[t]:
                trades.append((t, j, "lots", None, None))
        cells[f"{ename}_L3"] = evaluate(f"{ename}_L3", trades, FEE, weeks=False)
        axiom = np.array([run(*arrays(t), j, grad[t], "lots", None, FEE + AXIOM) for t, j, *_ in trades])
        cells[f"{ename}_L3"]["info_frais_axiom"] = round(float(axiom.mean()), 3)
    out = {"essai": 60, "seuil_z": round(Z_MIN, 2), "cellules": cells}
    Path(DATA_DIR, "essai60.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
