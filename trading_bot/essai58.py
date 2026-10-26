"""Essais 58 et 59 (HYPOTHESES.md), demandés par Yanisse le 26/10/2026.
  58 : bot classique — Nasdaq jours agités (B1) ou taille selon l'agitation (B2) ; or, 1er signal du jour avec stop ×2 / ×3 (G1, G2)
  59 : mise de 1 %, 2 %, 5 %, 10 % du solde sur nos 7 stratégies en réel (information)

    python -m trading_bot.essai58          → data/essai58.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import essai24 as e24
from . import essai43 as e43
from . import strategies as sl
from .essai21 import Bars, bot_cost, judge, real_rs
from .essai32 import candles_for
from .essai52 import daily_trades
from .essai55 import HALF, day_table
from .essai56 import stats

DAY = 86400


def ratios(c, trades):
    days, _cl, rg = day_table(c, sl.NY)
    pos = {d: n for n, d in enumerate(days)}
    out = []
    for t in trades:
        n = pos.get(datetime.fromtimestamp(t.entry_ts, sl.NY).date())
        if n is None or n < 265:
            out.append(None)
            continue
        a14 = rg[n - 14:n].mean()
        med = np.median([rg[m - 14:m].mean() for m in range(n - 250, n)])
        out.append(a14 / med)
    return out


def replay(cfg, key, store, root, variant, first_of_day=False):
    c = e43.candles_of(store, root, key)
    cands = e43.candidates(cfg, c, root, key, print)
    if first_of_day:
        seen, keep = set(), []
        for x in cands:
            d = datetime.fromtimestamp(x[1], sl.NY).date()
            if d not in seen:
                seen.add(d)
                keep.append(x)
        cands = keep
    orig = e43.end_of
    e43.end_of = lambda created, mode, bot_end: created + mode if isinstance(mode, int) else orig(created, mode, bot_end)
    try:
        trades = [t for t in e43.replay(cfg, key, e43.Path5(c), cands, variant) if t.risk > 0]
    finally:
        e43.end_of = orig
    return c, trades


def verdict(name, key, c, trades, cost):
    closes = {}
    for x in c:
        closes[datetime.fromtimestamp(x.ts, sl.NY).date()] = x.close
    keys = sorted(closes)
    v = e24.checks(trades, cost, keys, [closes[k] for k in keys], datetime.fromtimestamp(c[-1].ts, timezone.utc).year)
    a = judge(f"essai58_{name}", key, trades, Bars(c), cost).get("all") or {}
    v["monkeys"] = {"beaten": a.get("beaten"), "z": a.get("z")}
    v["checks"]["singes"] = (a.get("beaten") or 0) >= 950
    v["robust"] = all(v["checks"].values())
    print(name, v["n"], v["mean_r"], v["profit_factor"], v["positive_years"], a.get("beaten"), a.get("z"),
          [k for k, ok in v["checks"].items() if not ok], flush=True)
    return v


def compound(rs, pct):
    bal, peak, dd = 1000.0, 1000.0, 0.0
    for r in rs:
        bal *= max(0.0, 1 + pct / 100 * r)
        peak = max(peak, bal)
        dd = max(dd, 1 - bal / peak if peak > 0 else 1)
    return bal, dd


def main() -> None:
    from .config import load_config
    from .engine import Engine
    eng = Engine(load_config())
    store, cfg, root = eng.store, eng.cfg, eng.store.dir
    out: dict = {"essai": "58-59"}
    rng = np.random.default_rng(58)

    # ---- 58 Nasdaq
    cost, _ = bot_cost("nasdaq", cfg)
    c, n24 = replay(cfg, "nasdaq", store, root, (1.5, 3.0, DAY))
    n24 = sorted(n24, key=lambda t: t.entry_ts)
    ra = ratios(c, n24)
    sel = [(t, r) for t, r in zip(n24, ra) if r is not None]
    tr = [t for t, _ in sel]
    rr = np.array([r for _, r in sel])
    rs = real_rs(tr, cost)
    keep = rr >= 1
    b1 = [t for t, k in zip(tr, keep) if k]
    v = verdict("B1", "nasdaq", c, b1, cost)
    rand = np.array([rs[rng.choice(len(rs), int(keep.sum()), replace=False)].mean() for _ in range(1000)])
    v["R_N24"] = round(float(rs.mean()), 4)
    v["bat_filtres_hasard"] = int((rand < rs[keep].mean()).sum())
    v["passe"] = bool(v["robust"] and rs[keep].mean() > rs.mean() and v["bat_filtres_hasard"] >= 950)
    out["B1 bot Nasdaq jours agités"] = v
    early = np.array([t.entry_ts < HALF for t in tr])
    size = np.clip(rr, 0.5, 2.0)
    res = {}
    for code, s in (("N24 taille fixe", np.ones(len(rs))), ("B2 taille selon l'agitation", size)):
        pct = rs * s
        tot, dd, ratio = stats(pct)
        r1, r2 = stats(pct[early])[2], stats(pct[~early])[2]
        res[code] = {"trades": len(pct), "gain_total_pct": round(tot, 1), "baisse_max_pct": round(dd, 1),
                     "gain_sur_baisse": round(ratio, 2) if ratio else None,
                     "2014-2019": round(r1, 2) if r1 else None, "2020+": round(r2, 2) if r2 else None}
    hz = [stats(rs * rng.permutation(size))[2] or 0 for _ in range(1000)]
    b = res["B2 taille selon l'agitation"]
    b["bat_tailles_hasard"] = int(np.sum(np.array(hz) < (b["gain_sur_baisse"] or 0)))
    f = res["N24 taille fixe"]
    b["passe"] = bool(b["2014-2019"] and f["2014-2019"] and b["2014-2019"] > f["2014-2019"] and b["2020+"] > f["2020+"]
                      and b["bat_tailles_hasard"] >= 950)
    out["B2"] = res
    print("B2", json.dumps(res, ensure_ascii=False), flush=True)

    # ---- 58 or
    cost_g, _ = bot_cost("gold", cfg)
    for code, sx in (("G1", 2.0), ("G2", 3.0)):
        cg, tg = replay(cfg, "gold", store, root, (sx, 2.0, DAY), first_of_day=True)
        out[f"{code} bot or 1er signal, stop ×{sx:g}, objectif 2"] = verdict(code, "gold", cg, tg, cost_g)

    # ---- 59 mise
    sets = {"bot Nasdaq": ("nasdaq", n24)}
    for strat, key in (("noise_area_v2", "nasdaq"), ("cassure_williams", "bitcoin"), ("donchian_1h", "bitcoin"),
                       ("swing_w3", "bitcoin"), ("nuit_asie", "gold")):
        cc = candles_for(key, store, root)
        sets[f"{strat} {key}"] = (key, sl.run_all(key, cc, only=[strat]))
    sets["double7 nasdaq"] = ("nasdaq", daily_trades(candles_for("nasdaq", store, root), "nasdaq", "R3"))
    mise = {}
    for name, (key, trs) in sets.items():
        trs = sorted((t for t in trs if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
        r = real_rs(trs, bot_cost(key, cfg)[0])
        row = {"trades": len(r), "R": round(float(r.mean()), 3)}
        for pct in (1, 2, 5, 10):
            bal, dd = compound(r, pct)
            sims = [compound(rng.permutation(r), pct) for _ in range(1000)]
            row[f"{pct} %"] = {"solde_final": round(bal), "pire_baisse_pct": round(100 * dd),
                               "hasard_mediane_solde": round(float(np.median([s[0] for s in sims]))),
                               "risque_moitie_pct": round(100 * np.mean([s[1] >= 0.5 for s in sims]), 1),
                               "risque_90_pct": round(100 * np.mean([s[1] >= 0.9 for s in sims]), 1)}
        mise[name] = row
        print("59", name, json.dumps(row, ensure_ascii=False), flush=True)
    out["59 mise"] = mise
    (Path(root) / "essai58.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
