"""Essai 57 (HYPOTHESES.md) : méthodes de day trading courantes (demande de Yanisse, 26/10/2026).
  J1 « Silver Bullet » ICT : creux de prix (FVG) dans la fenêtre, limite au milieu, stop 1re bougie, 2 R, fin 16:00 NY
  J3 « Red to Green » : retour au-dessus (ou sous) de la clôture de la veille le matin, objectif le haut (bas) de la veille

    python -m trading_bot.essai57          → data/essai57.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np

from . import strategies as sl
from .essai21 import Bars, bot_cost, judge, real_rs
from .essai32 import candles_for

HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())


def manage(c, name, asset, k0, side, entry, stop, tgt, end_ts, entry_ts):
    long = side == "long"
    risk = abs(entry - stop)
    k = k0 + 1
    while k < len(c) and c[k].ts < end_ts:
        b = c[k]
        if (b.low <= stop) if long else (b.high >= stop):
            return sl.Trade(name, asset, side, entry_ts, b.ts + 300, entry, min(stop, b.open) if long else max(stop, b.open), risk, "stop")
        if (b.high >= tgt) if long else (b.low <= tgt):
            return sl.Trade(name, asset, side, entry_ts, b.ts + 300, entry, max(tgt, b.open) if long else min(tgt, b.open), risk, "objectif")
        k += 1
    last = c[k - 1]
    return sl.Trade(name, asset, side, entry_ts, last.ts + 300, entry, last.close, risk, "heure")


def silver_bullet(c, s, asset, name, h0, h1):
    out = []
    for d in sl._days(c):
        a, b, end = sl._ny_ts(d, h0, 0), sl._ny_ts(d, h1, 0), sl._ny_ts(d, 16, 0)
        k = s.at(a)
        if k is None:
            continue
        setup = None
        while k < len(c) and c[k].ts < b:
            if setup is None and k >= 2 and c[k - 2].ts >= a - 600:
                x, z = c[k - 2], c[k]
                if z.low > x.high:
                    setup = ("long", (z.low + x.high) / 2, x.low, k)
                elif z.high < x.low:
                    setup = ("short", (z.high + x.low) / 2, x.high, k)
            elif setup is not None and k > setup[3]:
                side, mid, stop, _ = setup
                if (c[k].low <= mid) if side == "long" else (c[k].high >= mid):
                    px = min(mid, c[k].open) if side == "long" else max(mid, c[k].open)
                    risk = abs(px - stop)
                    if risk > 0 and ((px > stop) if side == "long" else (px < stop)):
                        tgt = px + 2 * risk if side == "long" else px - 2 * risk
                        # même bougie : le stop passe d'abord (prudence)
                        if (c[k].low <= stop) if side == "long" else (c[k].high >= stop):
                            out.append(sl.Trade(name, asset, side, c[k].ts, c[k].ts + 300, px, stop, risk, "stop"))
                        else:
                            out.append(manage(c, name, asset, k, side, px, stop, tgt, end, c[k].ts))
                    break
            k += 1
    return out


def red_to_green(c, s, asset, name):
    out = []
    days = sl._days(c)
    for d0, d in zip(days, days[1:]):
        kc = s.at(sl._ny_ts(d0, 15, 55))
        k = s.at(sl._ny_ts(d, 9, 30))
        if kc is None or k is None:
            continue
        pc = c[kc].close
        k_open = s.at(sl._ny_ts(d0, 9, 30))
        if k_open is None:
            continue
        ph = max(x.high for x in c[k_open:kc + 1])
        pl = min(x.low for x in c[k_open:kc + 1])
        o = c[k].open
        if o == pc:
            continue
        long = o < pc
        lo, hi = c[k].low, c[k].high
        end, last = sl._ny_ts(d, 16, 0), sl._ny_ts(d, 11, 0)
        j = k + 1
        while j < len(c) and c[j].ts + 300 <= last:
            lo, hi = min(lo, c[j].low), max(hi, c[j].high)
            if (c[j].close > pc) if long else (c[j].close < pc):
                e = c[j].close
                stop = lo if long else hi
                risk = abs(e - stop)
                if risk <= 0:
                    break
                tgt = max(ph, e + risk) if long else min(pl, e - risk)
                out.append(manage(c, name, asset, j, "long" if long else "short", e, stop, tgt, end, c[j].ts + 300))
                break
            j += 1
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    eng = Engine(load_config())
    store, cfg, root = eng.store, eng.cfg, eng.store.dir
    cells = [("J1a Silver Bullet Nasdaq 10-11", "nasdaq", lambda c, s: silver_bullet(c, s, "nasdaq", "J1a", 10, 11)),
             ("J1b Silver Bullet or 10-11", "gold", lambda c, s: silver_bullet(c, s, "gold", "J1b", 10, 11)),
             ("J1c Silver Bullet or 3-4 Londres", "gold", lambda c, s: silver_bullet(c, s, "gold", "J1c", 3, 4)),
             ("J3a Red to Green Nasdaq", "nasdaq", lambda c, s: red_to_green(c, s, "nasdaq", "J3a")),
             ("J3b Red to Green S&P 500", "sp500", lambda c, s: red_to_green(c, s, "sp500", "J3b"))]
    z_thr = NormalDist().inv_cdf(1 - 0.05 / len(cells))
    out = {"essai": 57, "z_seuil": round(z_thr, 2)}
    cache = {}
    for name, asset, fn in cells:
        if asset not in cache:
            c = candles_for(asset, store, root)
            cache[asset] = (c, sl._Series(c), Bars(c))
        c, s, bars = cache[asset]
        tr = sorted((t for t in fn(c, s) if t.risk > 0), key=lambda t: t.entry_ts)
        cost, label = bot_cost(asset, cfg)
        rs, rs2 = real_rs(tr, cost), real_rs(tr, lambda e: 2 * cost(e))
        early = np.array([t.entry_ts < HALF for t in tr])
        m = judge(f"essai57:{name[:3]}", asset, tr, bars, cost)
        a = m.get("all", {})
        years = {}
        for t, r in zip(tr, rs):
            years.setdefault(datetime.fromtimestamp(t.entry_ts, timezone.utc).year, []).append(r)
        v = {"trades": len(tr), "R": round(float(rs.mean()), 3), "gagnants": round(float((rs > 0).mean()), 3),
             "2014-2019": round(float(rs[early].mean()), 3), "2020+": round(float(rs[~early].mean()), 3),
             "frais_x2": round(float(rs2.mean()), 3), "ventes": sum(1 for t in tr if t.direction == "short"),
             "annees_positives": f"{sum(1 for v in years.values() if np.mean(v) > 0)}/{len(years)}",
             "singes": {k: a.get(k) for k in ("monkeys_r", "beaten", "z")}, "frais": label}
        v["passe"] = bool(len(tr) >= 200 and v["2014-2019"] > 0 and v["2020+"] > 0 and v["frais_x2"] > 0
                          and (a.get("beaten") or 0) >= 950 and (a.get("z") or 0) > z_thr)
        out[name] = v
        print(name, json.dumps(v, ensure_ascii=False), flush=True)
    (Path(root) / "essai57.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
