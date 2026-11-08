"""Essai 73 (HYPOTHESES.md) : asymétrie des rendements (Rob Carver) sur 32 marchés en cours journaliers.

Chaque vendredi : skew des 250 derniers rendements journaliers. K1 : achat du tiers le plus asymétrique vers le
bas, vente du tiers le plus asymétrique vers le haut. K2 : achat si skew < 0, vente si skew > 0. Tenue 1 semaine.

    python -m trading_bot.essai73          → data/essai73.json

Données hors dépôt : data/history/long/yahoo_daily73.json (Yahoo, clôtures journalières 2004 → 10/2026).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .config import DATA_DIR
from .essai33 import LONG, z_threshold

SKEW_N, VOL_N = 250, 60
FEE, FEE_CRYPTO, FIN = 0.0005, 0.0010, 0.03
SPLIT = date(2015, 1, 1)
N_MONKEYS = 1000
N_CELLS = 7
CLEAN = {"ES=F", "NQ=F", "YM=F", "RTY=F", "^GDAXI", "^STOXX50E", "^FTSE", "^N225", "^HSI",
         "EURUSD=X", "GBPUSD=X", "JPY=X", "AUDUSD=X", "CHF=X", "CAD=X", "BTC-USD", "ETH-USD"}
OUT = Path(DATA_DIR) / "essai73.json"


def load() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    raw = json.loads((LONG / "yahoo_daily73.json").read_text(encoding="utf-8"))
    out = {}
    for t, rows in raw.items():
        by_day: dict[int, float] = {}
        for ts, c in rows:
            by_day[datetime.fromtimestamp(ts, timezone.utc).date().toordinal()] = float(c)
        d = np.array(sorted(by_day))
        out[t] = (d, np.array([by_day[x] for x in d]))
    return out


def skew(x: np.ndarray) -> float:
    m, s = x.mean(), x.std()
    return float(((x - m) ** 3).mean() / s ** 3) if s > 0 else 0.0


def weekly_table(data: dict[str, tuple[np.ndarray, np.ndarray]]) -> list[dict[str, Any]]:
    """Pour chaque vendredi : skew, écart type 60 j et rendement de la semaine suivante de chaque marché actif."""
    first = date(2004, 1, 2)
    fridays = [first + timedelta(days=7 * k) for k in range(2000)]
    end = max(int(d[-1]) for d, _ in data.values())
    weeks = []
    for f, g in zip(fridays, fridays[1:]):
        if g.toordinal() > end:
            break
        row: dict[str, Any] = {"day": f, "m": {}}
        for t, (d, c) in data.items():
            i = int(np.searchsorted(d, f.toordinal(), side="right")) - 1
            j = int(np.searchsorted(d, g.toordinal(), side="right")) - 1
            if i < SKEW_N + 1 or j <= i or f.toordinal() - d[i] > 4 or g.toordinal() - d[j] > 4:
                continue
            past = c[i - SKEW_N:i + 1]
            if np.any(past <= 0) or c[j] <= 0:
                ret = c[i - SKEW_N + 1:i + 1] / c[i - SKEW_N:i] - 1
            else:
                ret = np.diff(past) / past[:-1]
            sd = float(ret[-VOL_N:].std(ddof=1))
            if sd <= 0 or c[i] == 0:
                continue
            row["m"][t] = {"skew": skew(ret), "sd": sd, "next": float(c[j] / c[i] - 1)}
        if row["m"]:
            weeks.append(row)
    return weeks


def positions(week: dict[str, Any], cell: str) -> dict[str, int]:
    m = week["m"]
    if cell == "K2":
        return {t: (1 if v["skew"] < 0 else -1) for t, v in m.items() if v["skew"] != 0}
    names = sorted(m, key=lambda t: m[t]["skew"])
    k = len(names) // 3
    if k == 0:
        return {}
    return {**{t: 1 for t in names[:k]}, **{t: -1 for t in names[-k:]}}


def run_cell(weeks: list[dict[str, Any]], cell: str, rng: np.random.Generator) -> dict[str, Any]:
    prev: dict[str, int] = {}
    rows = []
    for w in weeks:
        pos = positions(w, cell)
        if not pos:
            prev = {}
            continue
        gross, net, net2, clean = [], [], [], []
        for t, p in pos.items():
            v = w["m"][t]
            g = p * v["next"] / v["sd"]
            fee = FEE_CRYPTO if t in ("BTC-USD", "ETH-USD") else FEE
            c = (fee * abs(p - prev.get(t, 0)) + FIN / 52) / v["sd"]
            gross.append(g)
            net.append(g - c)
            net2.append(g - 2 * c)
            if t in CLEAN:
                clean.append(g - c)
        # sorties des marchés qui ne sont plus tenus (frais de sortie, répartis sur la semaine)
        exit_cost = sum((FEE_CRYPTO if t in ("BTC-USD", "ETH-USD") else FEE) / w["m"][t]["sd"]
                        for t in prev if t not in pos and t in w["m"])
        n = len(pos)
        longs = sum(1 for p in pos.values() if p > 0)
        rows.append({"day": w["day"], "gross": float(np.mean(gross)), "net": float(np.mean(net)) - exit_cost / n,
                     "net2": float(np.mean(net2)) - 2 * exit_cost / n, "clean": float(np.mean(clean)) if clean else None,
                     "longs": longs, "shorts": n - longs, "week": w})
        prev = pos
    net = np.array([x["net"] for x in rows])
    gross_mean = float(np.mean([x["gross"] for x in rows]))
    monkeys = np.empty(N_MONKEYS)
    for k in range(N_MONKEYS):
        vals = []
        for x in rows:
            m = x["week"]["m"]
            names = list(m)
            pick = rng.permutation(len(names))[:x["longs"] + x["shorts"]]
            signs = np.r_[np.ones(x["longs"]), -np.ones(x["shorts"])]
            vals.append(float(np.mean([s * m[names[i]]["next"] / m[names[i]]["sd"] for s, i in zip(signs, pick)])))
        monkeys[k] = np.mean(vals)
    first = net[[x["day"] < SPLIT for x in rows]]
    second = net[[x["day"] >= SPLIT for x in rows]]
    sd = float(net.std(ddof=1))
    z = float(net.mean() / sd * np.sqrt(len(net)))
    clean = [x["clean"] for x in rows if x["clean"] is not None]
    out = {"weeks": len(rows), "mean_r_week": round(float(net.mean()), 4), "gross_r_week": round(gross_mean, 4),
           "sharpe_year": round(float(net.mean() / sd * np.sqrt(52)), 2), "win_weeks": round(float((net > 0).mean()), 3),
           "first_half": round(float(first.mean()), 4), "second_half": round(float(second.mean()), 4),
           "mean_r_fees_x2": round(float(np.mean([x["net2"] for x in rows])), 4),
           "clean_markets": round(float(np.mean(clean)), 4) if clean else None,
           "beats_monkeys": int(np.sum(monkeys < gross_mean)), "z": round(z, 2), "z_needed": round(z_threshold(N_CELLS), 2),
           "avg_positions": round(float(np.mean([x["longs"] + x["shorts"] for x in rows])), 1)}
    out["passes"] = bool(out["weeks"] >= 200 and out["first_half"] > 0 and out["second_half"] > 0
                         and out["mean_r_fees_x2"] > 0 and out["beats_monkeys"] >= 950 and z >= out["z_needed"]
                         and (out["clean_markets"] or 0) > 0)
    years: dict[int, float] = {}
    for x in rows:
        years[x["day"].year] = years.get(x["day"].year, 0.0) + x["net"]
    out["by_year"] = {y: round(float(v), 2) for y, v in sorted(years.items())}
    return out


def run() -> dict[str, Any]:
    rng = np.random.default_rng(73)
    data = load()
    weeks = weekly_table(data)
    out: dict[str, Any] = {"essai": 73, "markets": sorted(data), "period": [str(weeks[0]["day"]), str(weeks[-1]["day"])],
                           "unit": "rendement de la semaine / écart type journalier 60 j, moyenne par position"}
    for cell in ("K1", "K2"):
        out[cell] = run_cell(weeks, cell, rng)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    r = run()
    print(r["period"], len(r["markets"]), "marchés")
    for c in ("K1", "K2"):
        x = r[c]
        print(f"{c}: semaines={x['weeks']} R/sem={x['mean_r_week']} brut={x['gross_r_week']} sharpe={x['sharpe_year']} "
              f"moitiés={x['first_half']}/{x['second_half']} frais×2={x['mean_r_fees_x2']} propres={x['clean_markets']} "
              f"singes={x['beats_monkeys']} z={x['z']}/{x['z_needed']} pos={x['avg_positions']} passe={x['passes']}")
        print("   ", x["by_year"])
