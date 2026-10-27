"""Essai 63 (HYPOTHESES.md) : faire apprendre les 6 stratégies en réel (demande de Yanisse, 27/10/2026).

A. L'arbitre : un modèle d'arbres (comme l'essai 25) dit « on prend » ou « on saute » chaque trade, à partir de ce
   qu'on sait avant l'entrée (volatilité, mouvement du jour, tendance, forme récente de la stratégie, heure, jour,
   sens, jour d'annonce). Walk-forward annuel. A1 : un modèle pour les 6 stratégies ; A2 : un modèle par stratégie.
B. Le chef d'orchestre : la mise de chaque trade suit la forme récente de sa stratégie (trades déjà clos).
   B1 bandit (0,25 + 1,75 × P(moyenne > 0), oubli 0,97) ; B2 ×2 / ×0,5 selon les 20 derniers trades ;
   B3 coupée quand les 10 derniers trades font < 0 R (idée de Yanisse).
Singes : 1 000 ; seuil z 2,33.

    python -m trading_bot.essai63          → data/essai63.json
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import NormalDist

import numpy as np

from . import strategies as sl
from .essai21 import bot_cost
from .essai23 import load

LIVE = [("noise_area_v2", "nasdaq"), ("double7", "nasdaq"), ("nuit_asie", "gold"),
        ("donchian_1h", "bitcoin"), ("swing_w3", "bitcoin"), ("cassure_williams", "bitcoin")]
Z = 2.33
N_MONKEYS = 1000
DAY = 86400
FEATURES = ["vol_ratio", "day_range", "ret20", "vs_ma200h", "form10", "form20", "hour", "weekday", "direction", "news"]


# ---------------------------------------------------------------- ce qu'on sait avant l'entrée
class Market:
    def __init__(self, candles):
        self.ts = np.array([c.ts for c in candles], dtype=np.int64)
        h = np.array([c.high for c in candles])
        lo = np.array([c.low for c in candles])
        self.c = np.array([c.close for c in candles])
        prev = np.concatenate([[self.c[0]], self.c[:-1]])
        tr = np.maximum(h, prev) - np.minimum(lo, prev)
        self.tr_cum = np.concatenate([[0.0], np.cumsum(tr)])
        self.c_cum = np.concatenate([[0.0], np.cumsum(self.c)])
        days = self.ts // DAY
        self.day_hi: dict[int, float] = {}
        self.day_lo: dict[int, float] = {}
        for d, x, y in zip(days, h, lo):
            self.day_hi[d] = max(self.day_hi.get(d, -1e18), x)
            self.day_lo[d] = min(self.day_lo.get(d, 1e18), y)
        self.days = np.array(sorted(self.day_hi))
        self.h, self.lo = h, lo

    def _mean(self, cum, i0, i1):
        return (cum[i1] - cum[i0]) / (i1 - i0) if i1 > i0 else math.nan

    def daily_atr(self, d: int) -> float:
        k = np.searchsorted(self.days, d)
        prev = self.days[max(0, k - 20):k]
        return float(np.mean([self.day_hi[x] - self.day_lo[x] for x in prev])) if len(prev) >= 5 else math.nan

    def features(self, entry_ts: int) -> dict[str, float]:
        i = int(np.searchsorted(self.ts, entry_ts - 300, side="right"))      # bougies closes avant l'entrée
        if i < 50:
            return {}
        last = self.c[i - 1]
        h1 = int(np.searchsorted(self.ts, entry_ts - 3600, side="left"))
        d20 = int(np.searchsorted(self.ts, entry_ts - 20 * DAY, side="left"))
        h200 = int(np.searchsorted(self.ts, entry_ts - 200 * 3600, side="left"))
        d = entry_ts // DAY
        datr = self.daily_atr(d)
        d0 = int(np.searchsorted(self.ts, d * DAY, side="left"))
        rng = (self.h[d0:i].max() - self.lo[d0:i].min()) if i > d0 else 0.0
        c20 = self.c[d20] if d20 < i else math.nan
        return {"vol_ratio": self._mean(self.tr_cum, h1, i) / self._mean(self.tr_cum, d20, i),
                "day_range": rng / datr if datr else math.nan,
                "ret20": (last - c20) / datr if datr else math.nan,
                "vs_ma200h": (last - self._mean(self.c_cum, h200, i)) / datr if datr else math.nan}


def news_days(root: Path) -> set[date]:
    out: set[date] = set()
    data = json.loads((root / "macro_events_2010_2024.json").read_text(encoding="utf-8"))
    for kind in ("nfp", "cpi", "fomc"):
        out |= {date.fromisoformat(x) for x in data[kind]}
    return out


def year_of(ts: int) -> int:
    return datetime.fromtimestamp(ts, timezone.utc).year


# ---------------------------------------------------------------- outils de verdict
def max_dd(x: np.ndarray) -> float:
    cum = np.cumsum(x)
    return float((cum - np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:]).min()) if len(x) else 0.0


def zstat(x: np.ndarray) -> float:
    if len(x) < 2 or x.std(ddof=1) == 0:
        return 0.0
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))))


def verdict(z: float, beaten: float, years_better: float, dd_new: float, dd_base: float) -> str:
    ok = z >= Z and beaten >= 0.95 and years_better >= 0.6 and dd_new >= dd_base
    return "passe" if ok else "écartée"


# ---------------------------------------------------------------- A. l'arbitre
def arbitre(rows: list[dict], pooled: bool, rng: np.random.Generator) -> dict:
    from sklearn.ensemble import HistGradientBoostingRegressor
    names = sorted({r["strategy"] for r in rows})
    first = {s: min(year_of(r["entry_ts"]) for r in rows if r["strategy"] == s) for s in names}

    def x_of(r):
        return [r[f] for f in FEATURES] + ([1.0 if r["strategy"] == s else 0.0 for s in names] if pooled else [])

    keep = {}
    groups = [names] if pooled else [[s] for s in names]
    for grp in groups:
        sub = [r for r in rows if r["strategy"] in grp]
        for y in sorted({year_of(r["entry_ts"]) for r in sub}):
            test = [r for r in sub if year_of(r["entry_ts"]) == y and y >= first[r["strategy"]] + 3]
            if not test:
                continue
            cut = int(datetime(y, 1, 1, tzinfo=timezone.utc).timestamp())
            train = [r for r in sub if r["exit_ts"] < cut]
            if len(train) < 30:
                continue
            m = HistGradientBoostingRegressor(max_iter=200, max_depth=3, learning_rate=0.05, random_state=0)
            m.fit(np.array([x_of(r) for r in train]), np.array([r["r"] for r in train]))
            pred = m.predict(np.array([x_of(r) for r in test]))
            for r, p in zip(test, pred):
                keep[r["id"]] = bool(p > 0)
    test = [r for r in rows if r["id"] in keep]
    rs = np.array([r["r"] for r in test])
    k = np.array([keep[r["id"]] for r in test])
    gain = np.where(k, 0.0, -rs)                 # ce que l'arbitre ajoute, trade par trade (sauter un perdant = +)
    # singes : même part sautée dans chaque stratégie et chaque année
    cells: dict[tuple, list[int]] = {}
    for i, r in enumerate(test):
        cells.setdefault((r["strategy"], year_of(r["entry_ts"])), []).append(i)
    mk = np.empty(N_MONKEYS)
    for j in range(N_MONKEYS):
        kk = np.zeros(len(test), dtype=bool)
        for idx in cells.values():
            n_keep = int(k[idx].sum())
            kk[rng.choice(idx, n_keep, replace=False)] = True
        mk[j] = rs[kk].sum()
    years = sorted({year_of(r["entry_ts"]) for r in test})
    yy = np.array([year_of(r["entry_ts"]) for r in test])
    better = [rs[(yy == y) & k].sum() > rs[yy == y].sum() for y in years if ((yy == y) & ~k).any()]
    by_strat = {}
    for s in names:
        idx = np.array([r["strategy"] == s for r in test])
        if idx.any():
            by_strat[s] = {"n": int(idx.sum()), "gardés": int((idx & k).sum()), "R_tous": round(float(rs[idx].mean()), 3),
                           "R_gardés": round(float(rs[idx & k].mean()), 3) if (idx & k).any() else None}
    z = zstat(gain)
    beaten = float((mk < rs[k].sum()).mean())
    yb = float(np.mean(better)) if better else 0.0
    dd_new, dd_base = max_dd(np.where(k, rs, 0.0)), max_dd(rs)
    return {"trades_testés": len(test), "gardés": int(k.sum()), "R_tous": round(float(rs.mean()), 3),
            "R_gardés": round(float(rs[k].mean()), 3) if k.any() else None,
            "total_tous": round(float(rs.sum()), 1), "total_gardés": round(float(rs[k].sum()), 1),
            "R_sautés": round(float(rs[~k].mean()), 3) if (~k).any() else None, "z": round(z, 2),
            "singes_battus": round(beaten, 3), "années_mieux": f"{sum(better)}/{len(better)}",
            "pire_baisse": round(dd_new, 1), "pire_baisse_tous": round(dd_base, 1), "par_stratégie": by_strat,
            "verdict": verdict(z, beaten, yb, dd_new, dd_base)}


# ---------------------------------------------------------------- B. le chef d'orchestre
def weights(rows: list[dict], rule: str) -> np.ndarray:
    """Mise de chaque trade (ordre de `rows`, chronologique), d'après les trades de la même stratégie déjà clos."""
    w = np.ones(len(rows))
    hist: dict[str, list[tuple[int, float]]] = {}
    for i, r in enumerate(rows):
        past = [x for t, x in hist.get(r["strategy"], []) if t < r["entry_ts"]]
        if rule == "B1":
            if len(past) >= 5:
                lam = 0.97 ** np.arange(len(past))[::-1]
                p = np.array(past)
                m = (lam * p).sum() / lam.sum()
                var = (lam * (p - m) ** 2).sum() / lam.sum()
                neff = lam.sum() ** 2 / (lam ** 2).sum()
                se = math.sqrt(var / neff) if var > 0 else 1e-9
                w[i] = 0.25 + 1.75 * NormalDist().cdf(m / se)
            else:
                w[i] = 0.25 + 1.75 * 0.5
        elif rule == "B2":
            if len(past) >= 20:
                w[i] = 2.0 if sum(past[-20:]) > 0 else 0.5
        elif rule == "B3":
            if len(past) >= 10 and sum(past[-10:]) < 0:
                w[i] = 0.0
        hist.setdefault(r["strategy"], []).append((r["exit_ts"], r["r"]))
    return w


def chef(rows: list[dict], rule: str, rng: np.random.Generator) -> dict:
    rs = np.array([r["r"] for r in rows])
    w = weights(rows, rule)
    scale = len(w) / w.sum()
    res = w * rs * scale
    months = np.array([datetime.fromtimestamp(r["entry_ts"], timezone.utc).strftime("%Y-%m") for r in rows])
    um = sorted(set(months))
    diff_m = np.array([res[months == m].sum() - rs[months == m].sum() for m in um])
    strat = np.array([r["strategy"] for r in rows])
    mk = np.empty(N_MONKEYS)
    for j in range(N_MONKEYS):
        ww = w.copy()
        for s in set(strat):
            idx = np.where(strat == s)[0]
            ww[idx] = rng.permutation(w[idx])
        mk[j] = (ww * rs).sum() * len(ww) / ww.sum()
    yy = np.array([year_of(r["entry_ts"]) for r in rows])
    years = sorted(set(yy))
    better = [res[yy == y].sum() > rs[yy == y].sum() for y in years]
    z = zstat(diff_m)
    beaten = float((mk < res.sum()).mean())
    yb = float(np.mean(better))
    dd_new, dd_base = max_dd(res), max_dd(rs)
    return {"trades": len(rows), "mise_min": round(float(w.min()), 2), "mise_max": round(float(w.max()), 2),
            "part_coupée": round(float((w == 0).mean()), 3), "total_égal": round(float(rs.sum()), 1),
            "total_chef": round(float(res.sum()), 1), "R_égal": round(float(rs.mean()), 3), "R_chef": round(float(res.mean()), 3),
            "z_mois": round(z, 2), "singes_battus": round(beaten, 3), "années_mieux": f"{sum(better)}/{len(better)}",
            "pire_baisse": round(dd_new, 1), "pire_baisse_égal": round(dd_base, 1),
            "par_année": {int(y): [round(float(rs[yy == y].sum()), 1), round(float(res[yy == y].sum()), 1)] for y in years},
            "verdict": verdict(z, beaten, yb, dd_new, dd_base)}


# ---------------------------------------------------------------- lancement
def build_rows(root: Path, store, cfg) -> list[dict]:
    news = news_days(root)
    rows: list[dict] = []
    cache = {}
    for name, key in LIVE:
        if key not in cache:
            old = load(root / "history" / "long" / f"{key}_5m.json")
            new = store.load_history(key)
            c = [x for x in old if x.ts < new[0].ts] + new
            cache[key] = (c, Market(c))
        c, mkt = cache[key]
        cost, _ = bot_cost(key, cfg)
        if name == "double7":                  # version de l'essai 52 (la version « réel » attend des jours complets)
            from . import essai52
            raw = essai52.daily_trades(c, key, "R3")
        else:
            raw = sl.run_all(key, c, only=[name])
        trades = sorted((t for t in raw if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
        for t in trades:
            f = mkt.features(t.entry_ts)
            if not f:
                continue
            dt = datetime.fromtimestamp(t.entry_ts, timezone.utc)
            rows.append({"id": f"{name}:{t.entry_ts}", "strategy": name, "asset": key, "entry_ts": t.entry_ts,
                         "exit_ts": t.exit_ts, "r": (t.gross_points() - cost(t.entry)) / t.risk,
                         "hour": dt.hour, "weekday": dt.weekday(), "direction": 1.0 if t.direction == "long" else -1.0,
                         "news": 1.0 if datetime.fromtimestamp(t.entry_ts, sl.NY).date() in news else 0.0, **f})
        print(f"{name} {key} : {len(trades)} trades", flush=True)
    rows.sort(key=lambda r: r["entry_ts"])
    hist: dict[str, list[tuple[int, float]]] = {}
    for r in rows:                                      # forme récente : trades de la stratégie déjà clos
        past = [x for t, x in hist.get(r["strategy"], []) if t < r["entry_ts"]]
        r["form10"] = float(np.mean(past[-10:])) if len(past) >= 5 else math.nan
        r["form20"] = float(np.mean(past[-20:])) if len(past) >= 10 else math.nan
        hist.setdefault(r["strategy"], []).append((r["exit_ts"], r["r"]))
    return rows


def main() -> None:
    from .config import load_config
    from .engine import Engine
    eng = Engine(load_config())
    root = Path(__file__).resolve().parent.parent / "data"
    rows = build_rows(root, eng.store, eng.cfg)
    rng = np.random.default_rng(63)
    out = {"essai": 63, "z": Z, "singes": N_MONKEYS, "trades": len(rows),
           "stratégies": {n: {"n": sum(r["strategy"] == n for r in rows),
                              "R": round(float(np.mean([r["r"] for r in rows if r["strategy"] == n])), 3)} for n, _ in LIVE},
           "cells": {}}
    out["cells"]["A1"] = arbitre(rows, True, rng)
    print("A1", out["cells"]["A1"]["verdict"], flush=True)
    out["cells"]["A2"] = arbitre(rows, False, rng)
    print("A2", out["cells"]["A2"]["verdict"], flush=True)
    for rule in ("B1", "B2", "B3"):
        out["cells"][rule] = chef(rows, rule, rng)
        print(rule, out["cells"][rule]["verdict"], flush=True)
    (root / "essai63.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
