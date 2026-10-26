"""Essai 54 (HYPOTHESES.md) : nouvelles stratégies d'indices tirées des études (demande de Yanisse, 26/10/2026).
Nasdaq et S&P 500, bougies 5 min 2014-2026 (celles de l'essai 52), achats seulement, frais et singes de l'essai 21.
  O1 la nuit : achat 16:00 New York, vente à l'ouverture de 9:30 de la séance suivante, stop 1 %
  M1 fin de mois : achat clôture de l'avant-dernier jour de bourse, vente clôture du 3e jour du mois suivant, stop 2 ATR 14 j
  F1 veille de la Fed : achat 14:00 la veille, vente 13:55 le jour de la décision, stop 1 %

    python -m trading_bot.essai54          → data/essai54.json
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

from . import strategies as sl
from .essai21 import Bars, bot_cost, judge, real_rs
from .essai23 import load
from .essai52 import daily

HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
ASSETS = ("nasdaq", "sp500")
FOMC_2025_2026 = ["2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29",
                  "2025-12-10", "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16"]


def hold(c, s, name, asset, k0, k_exit, entry, risk, exit_open):
    """Achat à `entry` (clôture de la bougie k0), sortie à l'ouverture (exit_open) ou à la clôture de k_exit ; stop touché
    avant sur les bas des bougies (exécuté au pire du stop et de l'ouverture)."""
    stop = entry - risk
    for k in range(k0 + 1, k_exit + 1):
        if exit_open and k == k_exit:
            break
        if c[k].low <= stop:
            return sl.Trade(name, asset, "long", c[k0].ts + 300, c[k].ts + 300, entry, min(stop, c[k].open), risk, "stop")
    px = c[k_exit].open if exit_open else c[k_exit].close
    return sl.Trade(name, asset, "long", c[k0].ts + 300, c[k_exit].ts + (0 if exit_open else 300), entry, px, risk, "règle")


def night(c, s, asset):
    out = []
    days = sl._days(c)
    for d0, d1 in zip(days, days[1:]):
        k0 = s.at(sl._ny_ts(d0, 15, 55))
        k1 = s.at(sl._ny_ts(d1, 9, 30))
        if k0 is None or k1 is None or (d1 - d0).days > 4:
            continue
        e = c[k0].close
        out.append(hold(c, s, "O1", asset, k0, k1, e, 0.01 * e, True))
    return out


def month_end(c, s, asset):
    D = daily(c, asset)
    cl = np.array([r[4] for r in D])
    hi, lo = np.array([r[2] for r in D]), np.array([r[3] for r in D])
    tr = np.maximum(hi[1:] - lo[1:], np.maximum(abs(hi[1:] - cl[:-1]), abs(lo[1:] - cl[:-1])))
    out = []
    for i in range(15, len(D) - 4):
        m = (D[i][0].year, D[i][0].month)
        if (D[i + 1][0].year, D[i + 1][0].month) != m or (D[i + 2][0].year, D[i + 2][0].month) == m:
            continue                                     # i = avant-dernier jour du mois
        j = i + 4                                        # dernier jour (i+1), puis 1er, 2e, 3e jours du mois suivant
        if (D[j][0].year, D[j][0].month) == m:
            continue
        atr = tr[i - 14:i].mean()
        out.append(hold(c, s, "M1", asset, D[i][6], D[j][6], cl[i], 2 * atr, False))
    return out


def fed_eve(c, s, asset):
    ev = json.loads((Path(sl.__file__).resolve().parent.parent / "data" / "macro_events_2010_2024.json")
                    .read_text(encoding="utf-8"))["fomc"]
    out = []
    days = sl._days(c)
    pos = {d: n for n, d in enumerate(days)}
    for ds in sorted(set(ev) | set(FOMC_2025_2026)):
        d = date.fromisoformat(ds)
        if d not in pos or pos[d] == 0:
            continue
        prev = days[pos[d] - 1]
        k0 = s.at(sl._ny_ts(prev, 13, 55))
        k1 = s.at(sl._ny_ts(d, 13, 50))
        if k0 is None or k1 is None:
            continue
        e = c[k0].close
        out.append(hold(c, s, "F1", asset, k0, k1, e, 0.01 * e, False))
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    eng = Engine(load_config())
    root = Path(__file__).resolve().parent.parent / "data"
    out = {"essai": 54}
    for asset in ASSETS:
        old = load(root / "history" / "long" / f"{asset}_5m.json")
        new = eng.store.load_history(asset)
        c = [x for x in old if x.ts < new[0].ts] + new
        s = sl._Series(c)
        bars = Bars(c)
        cost, label = bot_cost(asset, eng.cfg)
        for rule, fn in (("O1", night), ("M1", month_end), ("F1", fed_eve)):
            tr = sorted((t for t in fn(c, s, asset) if t.risk > 0), key=lambda t: t.entry_ts)
            if not tr:
                continue
            rs = real_rs(tr, cost)
            rs2 = real_rs(tr, lambda e: 2 * cost(e))
            early = np.array([t.entry_ts < HALF for t in tr])
            m = judge(f"essai54:{rule}", asset, tr, bars, cost)
            years = {}
            for t, r in zip(tr, rs):
                years.setdefault(datetime.fromtimestamp(t.entry_ts, timezone.utc).year, []).append(r)
            v = {"trades": len(tr), "R": round(float(rs.mean()), 3), "gagnants": round(float((rs > 0).mean()), 3),
                 "2014-2019": round(float(rs[early].mean()), 3) if early.any() else None,
                 "2020+": round(float(rs[~early].mean()), 3) if (~early).any() else None,
                 "frais_x2": round(float(rs2.mean()), 3),
                 "pct_par_trade": round(float(np.mean([(t.gross_points() - cost(t.entry)) / t.entry * 100 for t in tr])), 4),
                 "annees_positives": f"{sum(1 for v in years.values() if np.mean(v) > 0)}/{len(years)}",
                 "stops": sum(1 for t in tr if t.reason == "stop"), "frais": label,
                 "singes": {k: m.get("all", {}).get(k) for k in ("monkeys_r", "beaten", "z")}}
            out[f"{rule} {asset}"] = v
            print(rule, asset, json.dumps(v, ensure_ascii=False), flush=True)
    (root / "essai54.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
