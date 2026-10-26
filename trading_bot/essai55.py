"""Essai 55 (HYPOTHESES.md) : améliorer les stratégies en réel (demande de Yanisse, 26/10/2026).
  Z1/Z2 zone de bruit v2 Nasdaq seulement les jours agités / calmes
  W1/W2 cassure Williams Bitcoin seulement au-dessus de la moyenne 100 / 50 jours
  N4/N8/N12 bot classique Nasdaq (stop ×1,5, objectif 3) tenu 4 h / 8 h / 12 h au lieu de 24 h

    python -m trading_bot.essai55          → data/essai55.json
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

HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())


def day_table(candles, tz):
    """Par jour (fuseau tz) : clôture et amplitude en % ; listes triées."""
    days, cl, rng = [], [], []
    for c in candles:
        d = datetime.fromtimestamp(c.ts, tz).date()
        if days and days[-1] == d:
            hi[-1], lo[-1], cl[-1] = max(hi[-1], c.high), min(lo[-1], c.low), c.close
        else:
            if days:
                rng.append((hi[-1] - lo[-1]) / cl[-1])
            else:
                hi, lo = [], []
            days.append(d)
            hi.append(c.high)
            lo.append(c.low)
            cl.append(c.close)
    rng.append((hi[-1] - lo[-1]) / cl[-1])
    return days, np.array(cl), np.array(rng)


def filter_test(name, trades, keep, cost):
    rs = real_rs(trades, cost)
    keep = np.array(keep, bool)
    early = np.array([t.entry_ts < HALF for t in trades])
    k = int(keep.sum())
    rng = np.random.default_rng(55)
    rand = np.array([rs[rng.choice(len(rs), k, replace=False)].mean() for _ in range(1000)]) if 0 < k < len(rs) else np.array([0.0])
    v = {"trades_strategie": len(rs), "R_strategie": round(float(rs.mean()), 3), "gardes": k,
         "R_gardes": round(float(rs[keep].mean()), 3) if k else None,
         "2014-2019": [round(float(rs[early].mean()), 3), round(float(rs[keep & early].mean()), 3) if (keep & early).any() else None],
         "2020+": [round(float(rs[~early].mean()), 3), round(float(rs[keep & ~early].mean()), 3) if (keep & ~early).any() else None],
         "bat_filtres_hasard": int((rand < rs[keep].mean()).sum()) if k else 0}
    v["passe"] = bool(k >= 200 and v["R_gardes"] > v["R_strategie"] and v["2014-2019"][1] is not None
                      and v["2014-2019"][1] > v["2014-2019"][0] and v["2020+"][1] > v["2020+"][0]
                      and v["bat_filtres_hasard"] >= 950)
    print(name, json.dumps(v, ensure_ascii=False), flush=True)
    return v


def main() -> None:
    from .config import load_config
    from .engine import Engine
    eng = Engine(load_config())
    store, cfg, root = eng.store, eng.cfg, eng.store.dir
    out = {"essai": 55}

    # ---- zone de bruit v2 Nasdaq : jours agités / calmes
    c = candles_for("nasdaq", store, root)
    tr = sorted((t for t in sl.run_all("nasdaq", c, only=["noise_area_v2"]) if t.reason != "fin des données" and t.risk > 0),
                key=lambda t: t.entry_ts)
    days, _cl, rg = day_table(c, sl.NY)
    pos = {d: n for n, d in enumerate(days)}
    cost, _ = bot_cost("nasdaq", cfg)
    agit, ok = [], []
    for t in tr:
        n = pos[datetime.fromtimestamp(t.entry_ts, sl.NY).date()]
        if n < 265:
            agit.append(False)
            ok.append(False)
            continue
        a14 = rg[n - 14:n].mean()
        med = np.median([rg[m - 14:m].mean() for m in range(n - 250, n)])
        agit.append(a14 >= med)
        ok.append(True)
    tr_ok = [t for t, o in zip(tr, ok) if o]
    ag = [a for a, o in zip(agit, ok) if o]
    out["Z1 zone de bruit, jours agités"] = filter_test("Z1", tr_ok, ag, cost)
    out["Z2 zone de bruit, jours calmes"] = filter_test("Z2", tr_ok, [not a for a in ag], cost)

    # ---- cassure Williams Bitcoin : au-dessus de la moyenne 100 / 50 jours
    c = candles_for("bitcoin", store, root)
    tr = sorted((t for t in sl.run_all("bitcoin", c, only=["cassure_williams"]) if t.reason != "fin des données" and t.risk > 0),
                key=lambda t: t.entry_ts)
    days, cl, _ = day_table(c, timezone.utc)
    pos = {d: n for n, d in enumerate(days)}
    cost, _ = bot_cost("bitcoin", cfg)
    for code, w in (("W1", 100), ("W2", 50)):
        keep, sel = [], []
        for t in tr:
            n = pos[datetime.fromtimestamp(t.entry_ts, timezone.utc).date()]
            if n <= w:
                continue
            sel.append(t)
            prev = cl[n - 1]
            keep.append(prev > cl[n - w:n].mean() if t.direction == "long" else prev < cl[n - w:n].mean())
        out[f"{code} Williams, moyenne {w} j"] = filter_test(code, sel, keep, cost)

    # ---- bot classique Nasdaq : durée
    c = e43.candles_of(store, root, "nasdaq")
    cands = e43.candidates(cfg, c, root, "nasdaq", print)
    p = e43.Path5(c)
    cost, _ = bot_cost("nasdaq", cfg)
    closes = {}
    for x in c:
        closes[datetime.fromtimestamp(x.ts, sl.NY).date()] = x.close
    keys = sorted(closes)
    last_year = datetime.fromtimestamp(c[-1].ts, timezone.utc).year
    bars = Bars(c)
    orig = e43.end_of
    e43.end_of = lambda created, mode, bot_end: created + mode if isinstance(mode, int) else orig(created, mode, bot_end)
    try:
        for code, hours in (("N4", 4), ("N8", 8), ("N12", 12), ("N24 référence", 24)):
            trades = [t for t in e43.replay(cfg, "nasdaq", p, cands, (1.5, 3.0, hours * 3600)) if t.risk > 0]
            v = e24.checks(trades, cost, keys, [closes[k] for k in keys], last_year)
            m = judge(f"essai55_{code}", "nasdaq", trades, bars, cost)
            a = m.get("all") or {}
            v["monkeys"] = {"beaten": a.get("beaten"), "z": a.get("z")}
            v["checks"]["singes"] = (a.get("beaten") or 0) >= 950
            v["robust"] = all(v["checks"].values())
            out[f"{code} bot Nasdaq {hours} h"] = v
            print(code, v["n"], v["mean_r"], v["profit_factor"], v["positive_years"], a.get("beaten"), a.get("z"),
                  [k for k, ok in v["checks"].items() if not ok], flush=True)
    finally:
        e43.end_of = orig
    (Path(root) / "essai55.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
