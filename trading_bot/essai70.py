"""Essai 70 (HYPOTHESES.md) : convergence d'un écart entre deux marchés proches (paires).

P1 Nasdaq / S&P 500 (CFD HistData 1 min → 30 min, 09:30-16:00 New York) et P2 Bitcoin / Ethereum (Binance 30 min).

    python -m trading_bot.essai70          → data/essai70.json

Données hors dépôt : data/history/long/{nasdaq,sp500}_1m.npz (essai 69), {btc,eth}_30m.npz (Binance).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

from .config import DATA_DIR
from .essai33 import Bars, z_threshold
from .essai64 import ny_minutes

FORM_DAYS, Z_IN, Z_OUT, Z_STOP, MAX_BARS = 60, 2.0, 0.5, 3.0, 8
N_MONKEYS = 1000
N_CELLS = 4                                    # essais 70 et 71 ensemble
OUT = Path(DATA_DIR) / "essai70.json"


def index_30m(asset: str) -> dict[tuple[int, int], float]:
    """Clôture de chaque demi-heure 09:30-16:00 New York : {(jour, n° de bougie 0-12): clôture}."""
    b = Bars.load(f"{asset}_1m.npz")
    mins, wd, day = ny_minutes(b.ts)
    keep = (mins >= 570) & (mins < 960) & (wd < 5)
    out: dict[tuple[int, int], float] = {}
    for i in np.flatnonzero(keep):
        out[(int(day[i]), int((mins[i] - 570) // 30))] = float(b.c[i])   # la dernière minute de la demi-heure gagne
    return out


def pair_indices() -> dict[str, np.ndarray]:
    a, b = index_30m("nasdaq"), index_30m("sp500")
    keys = sorted(set(a) & set(b))
    day = np.array([k[0] for k in keys])
    slot = np.array([k[1] for k in keys])
    return {"day": day, "slot": slot, "a": np.array([a[k] for k in keys]), "b": np.array([b[k] for k in keys]),
            "last_slot": 12, "split": date(2020, 1, 1), "kind": "indices"}


def pair_crypto() -> dict[str, np.ndarray]:
    x, y = Bars.load("btc_30m.npz"), Bars.load("eth_30m.npz")
    common, ia, ib = np.intersect1d(x.ts, y.ts, return_indices=True)
    day = (common // 86400).astype(int) + date(1970, 1, 1).toordinal()
    return {"day": day, "slot": ((common % 86400) // 1800).astype(int), "a": x.c[ia], "b": y.c[ib],
            "last_slot": None, "split": date(2022, 1, 1), "kind": "crypto", "ts": common}


def calibrate(p: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pour chaque bougie : alpha, bêta et écart type du résidu estimés sur les 60 jours d'avant (figés pour la journée)."""
    la, lb, day = np.log(p["a"]), np.log(p["b"]), p["day"]
    days = np.unique(day)
    start = np.searchsorted(day, days)
    alpha, beta, sd = (np.full(len(day), np.nan) for _ in range(3))
    for k in range(FORM_DAYS, len(days)):
        lo, hi = start[k - FORM_DAYS], start[k]
        end = start[k + 1] if k + 1 < len(days) else len(day)
        x, y = lb[lo:hi], la[lo:hi]
        if len(x) < 100:
            continue
        bt, al = np.polyfit(x, y, 1)
        res = y - (al + bt * x)
        s = float(res.std(ddof=1))
        if s <= 0:
            continue
        alpha[hi:end], beta[hi:end], sd[hi:end] = al, bt, s
    return alpha, beta, sd


def costs(p: dict[str, Any], i, beta):
    """Frais aller-retour des deux jambes, en unités de log (≈ fraction du nominal de A)."""
    if p["kind"] == "indices":
        return 1.3 / p["a"][i] + np.abs(beta) * 0.6 / p["b"][i]
    return 0.0006 * (1 + np.abs(beta))


def leg(p: dict[str, Any], i, u, s, beta):
    la, lb = p["la"], p["lb"]
    return s * ((la[u] - la[i]) - beta * (lb[u] - lb[i]))


def prepare(p: dict[str, Any]) -> dict[str, Any]:
    p["la"], p["lb"] = np.log(p["a"]), np.log(p["b"])
    p["cal"] = calibrate(p)
    return p


def simulate(p: dict[str, Any]) -> list[dict[str, Any]]:
    alpha, beta, sd = p["cal"]
    la, lb, day = p["la"], p["lb"], p["day"]
    z = (la - (alpha + beta * lb)) / sd
    trades, i, n = [], 0, len(day)
    while i < n - 1:
        if np.isnan(z[i]) or abs(z[i]) <= Z_IN or (p["last_slot"] is not None and p["slot"][i] >= p["last_slot"]):
            i += 1
            continue
        s = -1 if z[i] > 0 else 1
        u = i + 1
        while u < n:
            if p["kind"] == "indices" and day[u] != day[i]:
                u -= 1                             # jamais de nuit : sortie à la dernière bougie du jour
                break
            if p["kind"] == "crypto" and p["ts"][u] - p["ts"][i] > (u - i) * 1800 + 3600:
                break                              # trou de données
            zz = (la[u] - (alpha[i] + beta[i] * lb[u])) / sd[i]   # mêmes alpha/bêta que l'entrée
            if abs(zz) < Z_OUT or abs(zz) > Z_STOP or u - i >= MAX_BARS:
                break
            u += 1
        u = min(u, n - 1)
        if u <= i:
            i += 1
            continue
        gross = leg(p, i, u, s, beta[i])
        c = costs(p, i, beta[i])
        trades.append({"i": i, "u": u, "s": s, "hold": u - i, "day": date.fromordinal(int(day[i])),
                       "r": (gross - c) / sd[i], "gross": gross / sd[i], "r_x2": (gross - 2 * c) / sd[i], "beta": float(beta[i])})
        i = u + 1
    return trades


def monkeys(p: dict[str, Any], trades: list[dict[str, Any]], rng: np.random.Generator) -> list[float]:
    alpha, beta, sd = p["cal"]
    ok = ~np.isnan(sd)
    day, n = p["day"], len(p["day"])
    pools: dict[int, np.ndarray] = {}
    for h in {t["hold"] for t in trades}:
        idx = np.flatnonzero(ok[:n - h])
        idx = idx[day[idx + h] == day[idx]] if p["kind"] == "indices" else idx
        pools[h] = idx
    total = np.zeros(N_MONKEYS)
    for t in trades:                               # pour chaque trade, 1000 singes d'un coup
        i = rng.choice(pools[t["hold"]], size=N_MONKEYS)
        u = i + t["hold"]
        total += (leg(p, i, u, t["s"], beta[i]) - costs(p, i, beta[i])) / sd[i]
    return list(total / len(trades))


def judge(p: dict[str, Any], trades: list[dict[str, Any]], rng: np.random.Generator) -> dict[str, Any]:
    r = np.array([t["r"] for t in trades])
    first = r[[t["day"] < p["split"] for t in trades]]
    second = r[[t["day"] >= p["split"] for t in trades]]
    m = monkeys(p, trades, rng) if trades else []
    sdv = float(r.std(ddof=1)) if len(r) > 1 else 0.0
    zv = float(r.mean() / sdv * np.sqrt(len(r))) if sdv else 0.0
    out = {"n": len(r), "mean_r": round(float(r.mean()), 4),
           "gross_r": round(float(np.mean([t["gross"] for t in trades])), 4), "win": round(float((r > 0).mean()), 3),
           "first_half": round(float(first.mean()), 4) if len(first) else None,
           "second_half": round(float(second.mean()), 4) if len(second) else None,
           "mean_r_fees_x2": round(float(np.mean([t["r_x2"] for t in trades])), 4),
           "beats_monkeys": int(np.sum(np.array(m) < r.mean())), "z": round(zv, 2),
           "z_needed": round(z_threshold(N_CELLS), 2), "avg_hold_bars": round(float(np.mean([t["hold"] for t in trades])), 2),
           "split": str(p["split"])}
    out["passes"] = bool(out["n"] >= 200 and (out["first_half"] or 0) > 0 and (out["second_half"] or 0) > 0
                         and out["mean_r_fees_x2"] > 0 and out["beats_monkeys"] >= 950 and zv >= out["z_needed"])
    years: dict[int, float] = {}
    for t in trades:
        years[t["day"].year] = years.get(t["day"].year, 0.0) + t["r"]
    out["by_year"] = {y: round(float(v), 2) for y, v in sorted(years.items())}
    return out


def run() -> dict[str, Any]:
    rng = np.random.default_rng(70)
    out: dict[str, Any] = {"essai": 70, "rule": f"z > {Z_IN} → vendre l'écart, sortie |z| < {Z_OUT}, > {Z_STOP} "
                                                f"ou {MAX_BARS} bougies 30 min ; calibrage {FORM_DAYS} jours"}
    for name, build in (("P1_nasdaq_sp500", pair_indices), ("P2_btc_eth", pair_crypto)):
        p = prepare(build())
        tr = simulate(p)
        out[name] = judge(p, tr, rng)
        out[name]["period"] = [str(date.fromordinal(int(p["day"][0]))), str(date.fromordinal(int(p["day"][-1])))]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    r = run()
    for k in ("P1_nasdaq_sp500", "P2_btc_eth"):
        x = r[k]
        print(k, x["period"], f"n={x['n']} R={x['mean_r']} brut={x['gross_r']} gagn={x['win']} moitiés={x['first_half']}/{x['second_half']} "
              f"frais×2={x['mean_r_fees_x2']} singes={x['beats_monkeys']} z={x['z']}/{x['z_needed']} "
              f"tenue={x['avg_hold_bars']} passe={x['passes']}")
        print("   ", x["by_year"])
