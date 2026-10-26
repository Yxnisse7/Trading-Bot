"""Essai 38 (HYPOTHESES.md) : memecoins pump.fun, entrer après la montée du début, sortir à la chute.

    python -m trading_bot.essai38 --prep DOSSIER   → data/history/pumpfun/early.npz (depuis le corpus Hugging Face)
    python -m trading_bot.essai38                  → data/essai38.json
    python -m trading_bot.essai38 --essai39        → data/essai39.json (filtres des « bons » coins)

Données hors dépôt : corpus « PumpFun Launch-to-Graduation Corpus » (Slinky21, CC BY 4.0), fichiers tokens.parquet
et trades/*.parquet. --prep garde les 75 premières minutes de chaque coin (duckdb nécessaire pour cette étape).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np

from .config import DATA_DIR

UTC = timezone.utc
STAKE = 0.5                # SOL par trade
FEE = 0.0125               # par côté : plateforme 0,95 % + créateur 0,30 %
NET_FEE = 0.001            # SOL de réseau par transaction
DELAY = 2.0                # s entre le déclencheur et notre ordre
SIGNAL_WINDOW = 600        # s après le lancement
MAX_HOLD = 3600            # s
N_MONKEYS = 1000
MIN_TRADES = 200
OUT_START = datetime(2026, 7, 2, 23, tzinfo=UTC).timestamp()   # panne du 3 juillet
OUT_END = datetime(2026, 7, 4, tzinfo=UTC).timestamp()
HALF = datetime(2026, 6, 25, tzinfo=UTC).timestamp()
ENTRIES = {"K1": 1.0, "K2": 2.0, "K3": 3.0, "K5": 5.0}
EXITS = {"T20": ("trail", 0.20), "T40": ("trail", 0.40), "M5": ("time", 300.0)}
PF_DIR = Path(DATA_DIR) / "history" / "pumpfun"
N_CELLS = len(ENTRIES) * len(EXITS)
Z_MIN = NormalDist().inv_cdf(1 - 0.05 / N_CELLS)


def prep(src: Path) -> None:
    import duckdb

    con = duckdb.connect()
    con.sql("SET memory_limit='10GB'; SET preserve_insertion_order=false")
    con.sql(f"""create table tok as select row_number() over () - 1 id, mint, epoch(detected_at) launch,
                coalesce(epoch(graduated_at), 1e12) grad,
                coalesce(initial_top10_pct_corrected <= 25 and initial_top1_pct_corrected <= 10
                         and dev_buy_pct_corrected <= 5 and creator_past_rugs = 0
                         and not coalesce(top10_pct_suspect, false), false) clean,
                case when is_mayhem_mode then 2e9 else 1e9 end supply
                from '{src}/tokens.parquet' where detected_at is not null""")
    tr = con.sql(f"""
        select k.id, epoch(t.event_time) ts, t.price_sol p, t.v_sol_bonding_curve / 1e9 vs,
               t.v_tokens_bonding_curve / 1e6 vt
        from '{src}/trades/*.parquet' t join tok k using (mint)
        where t.price_sol > 0 and t.v_sol_bonding_curve > 0 and t.v_tokens_bonding_curve > 0
          and t.seconds_since_launch <= 4500
        order by k.id, ts""").fetchnumpy()
    tok = con.sql("select id, mint, launch, grad, clean, supply from tok order by id").fetchnumpy()
    ids = tr["id"].astype(np.int64)
    present = np.unique(ids)
    start = np.searchsorted(ids, present)
    PF_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(PF_DIR / "early.npz", ts=tr["ts"], p=tr["p"], vs=tr["vs"], vt=tr["vt"],
             start=np.append(start, len(ids)), keep=np.ones(len(present), bool),
             launch=tok["launch"][present], grad=tok["grad"][present],
             clean=tok["clean"][present], supply=tok["supply"][present], mints=tok["mint"][present].astype(str))


def buy_tokens(p: float, vs: float) -> float:
    x = STAKE * (1 - FEE)
    return x / (p * (1 + x / vs))


def sell_sol(tokens: float, p: float, vt: float) -> float:
    return tokens * p / (1 + tokens / vt) * (1 - FEE)


def result(ts, p, vs, vt, j: int, end_ts: float, exit_rule, fee_mult: float = 1.0) -> float:
    """Rendement net (%) d'une entrée exécutée à l'échange j."""
    kind, arg = exit_rule
    deadline = min(ts[j] + MAX_HOLD, end_ts)
    hi = np.searchsorted(ts, deadline, side="right")
    trigger = None
    if kind == "trail":
        seg = p[j:hi]
        hit = np.flatnonzero(seg < (1 - arg) * np.maximum.accumulate(seg))
        if len(hit):
            trigger = ts[j + hit[0]]
    elif ts[j] + arg < deadline:
        trigger = ts[j] + arg
    if trigger is not None:
        e = np.searchsorted(ts, trigger + DELAY, side="left")
        if e >= hi:
            e = hi - 1
    else:
        e = hi - 1
    e = max(e, j)
    tokens = buy_tokens(p[j], vs[j])
    out = sell_sol(tokens, p[e], vt[e])
    if fee_mult != 1.0:
        extra = (fee_mult - 1) * (FEE * STAKE + FEE * out + 2 * NET_FEE)
    else:
        extra = 0.0
    cost = STAKE + NET_FEE
    return 100 * (out - NET_FEE - cost - extra) / cost


def stats(r: np.ndarray) -> dict:
    gains, losses = r[r > 0].sum(), -r[r < 0].sum()
    srt = np.sort(r)
    return {"n": int(len(r)), "moy": round(float(r.mean()), 3) if len(r) else None,
            "mediane": round(float(np.median(r)), 2) if len(r) else None,
            "pf": round(float(gains / losses), 3) if losses > 0 else None,
            "perdants_pct": round(100 * float((r < 0).mean()), 1) if len(r) else None,
            "sans_5pct_meilleurs": round(float(srt[: int(len(r) * 0.95)].mean()), 3) if len(r) > 20 else None}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep", type=Path)
    ap.add_argument("--essai39", action="store_true", help="filtres des bons coins (essai 39)")
    a = ap.parse_args()
    if a.prep:
        prep(a.prep)
        return
    d = np.load(PF_DIR / "early.npz")
    TS, P, VS, VT, start = d["ts"], d["p"], d["vs"], d["vt"], d["start"]
    launch, grad, keep = d["launch"], d["grad"], d["keep"]
    end_all = TS.max()
    ok = keep & ~((launch >= OUT_START) & (launch < OUT_END)) & (launch < end_all - 70 * 60)
    tokens = np.flatnonzero(ok)
    day = ((launch - launch[ok].min()) // 86400).astype(int)
    rng = np.random.default_rng(38)

    def arrays(t):
        s, e = start[t], start[t + 1]
        return TS[s:e], P[s:e], VS[s:e], VT[s:e]

    # entrées réelles : (coin, cellule d'entrée) → indice de l'échange exécuté et âge
    real = {k: [] for k in ENTRIES}
    for t in tokens:
        ts, p, vs, vt = arrays(t)
        if len(ts) < 2:
            continue
        for name, mult in ENTRIES.items():
            if mult == 1.0:
                trig = ts[0]
            else:
                win = np.flatnonzero((p >= mult * p[0]) & (ts <= launch[t] + SIGNAL_WINDOW))
                if not len(win):
                    continue
                trig = ts[win[0]]
            j = np.searchsorted(ts, trig + DELAY, side="left")
            if j < len(ts) and ts[j] < grad[t]:
                real[name].append((t, j, ts[j] - launch[t]))

    # réserve des singes : par jour et tranche d'âge de 30 s, jusqu'à 300 coins tirés au hasard
    age_bins = np.arange(0, SIGNAL_WINDOW + 61, 30)
    pool: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for t in rng.permutation(tokens):
        ts = TS[start[t]:start[t + 1]]
        ages = ts - launch[t]
        for b, a0 in enumerate(age_bins):
            key = (day[t], b)
            lst = pool.setdefault(key, [])
            if len(lst) >= 300:
                continue
            j = np.searchsorted(ages, a0, side="left")
            if j < len(ts) and ages[j] <= a0 + 60 and ts[j] < grad[t]:
                lst.append((t, j))
    pool_res: dict[tuple[int, int, str], np.ndarray] = {}

    def monkey_outcomes(key, xname):
        if (key[0], key[1], xname) not in pool_res:
            out = [result(*arrays(t), j, grad[t], EXITS[xname]) for t, j in pool.get(key, [])]
            pool_res[(key[0], key[1], xname)] = np.array(out)
        return pool_res[(key[0], key[1], xname)]

    cells = {}
    if a.essai39:
        clean, supply = d["clean"], d["supply"]
        filters = {
            "F1": lambda t, j: bool(clean[t]),
            "F2": lambda t, j: P[start[t] + j] * supply[t] >= 100,
            "F3": lambda t, j: bool(clean[t]) and P[start[t] + j] * supply[t] >= 100,
        }
        plan = [(f"{fn}_{en}_{xn}", [x for x in real[en] if fx(x[0], x[1])], xn)
                for fn, fx in filters.items() for en in ("K2", "K3", "K5") for xn in ("T20", "T40")]
        z_min = NormalDist().inv_cdf(1 - 0.05 / len(plan))
    else:
        plan = [(f"{en}_{xn}", lst, xn) for en, lst in real.items() for xn in EXITS]
        z_min = Z_MIN
    for cname, lst, xname in plan:
        rule = EXITS[xname]
        if True:
            r, r2, halves, keys = [], [], [], []
            for t, j, age in lst:
                arr = arrays(t)
                r.append(result(*arr, j, grad[t], rule))
                r2.append(result(*arr, j, grad[t], rule, fee_mult=2.0))
                halves.append(launch[t])
                keys.append((day[t], min(int(age // 30), len(age_bins) - 1)))
            r, r2, lt = np.array(r), np.array(r2), np.array(halves)
            # singes : chaque tirage remplace chaque trade par un coin au hasard du même jour et du même âge
            uniq = {k: monkey_outcomes(k, xname) for k in set(keys)}
            usable = np.array([len(uniq[k]) > 0 for k in keys])
            idx = np.flatnonzero(usable)
            sums = np.zeros(N_MONKEYS)
            for i in idx:
                o = uniq[keys[i]]
                sums += o[rng.integers(0, len(o), N_MONKEYS)]
            monkeys = sums / max(len(idx), 1)
            real_mean = r[idx].mean() if len(idx) else np.nan
            beaten = int((real_mean > monkeys).sum())
            z = float((real_mean - monkeys.mean()) / monkeys.std()) if monkeys.std() > 0 else 0.0
            last7 = lt >= end_all - 7 * 86400 - 70 * 60
            st = stats(r)
            checks = {
                "trades": st["n"] >= MIN_TRADES,
                "net": st["n"] > 0 and st["moy"] > 0 and (st["pf"] or 0) >= 1.1,
                "moitie_1": bool(len(r[lt < HALF]) and r[lt < HALF].mean() > 0),
                "moitie_2": bool(len(r[lt >= HALF]) and r[lt >= HALF].mean() > 0),
                "7_derniers_jours": bool(last7.any() and r[last7].mean() > 0),
                "frais_x2": bool(len(r2) and r2.mean() > 0),
                "singes": beaten >= 950,
            }
            cells[cname] = {
                **st, "frais_x2": round(float(r2.mean()), 3) if len(r2) else None,
                "moitie_1": round(float(r[lt < HALF].mean()), 3) if (lt < HALF).any() else None,
                "moitie_2": round(float(r[lt >= HALF].mean()), 3) if (lt >= HALF).any() else None,
                "7_derniers_jours": round(float(r[last7].mean()), 3) if last7.any() else None,
                "singes_battus": beaten, "singes_moy": round(float(monkeys.mean()), 3), "z": round(z, 2),
                "controles": checks, "prouvee": all(checks.values()) and z > z_min,
            }
            print(cname, cells[cname], flush=True)
    num = 39 if a.essai39 else 38
    out = {"essai": num, "seuil_z": round(z_min, 2), "coins": int(len(tokens)), "cellules": cells}
    Path(DATA_DIR, f"essai{num}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
