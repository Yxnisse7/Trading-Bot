"""Essai 74 (HYPOTHESES.md) : quatre pistes d'amélioration du bot classique, sur 5 marchés.

A. retirer une règle à la fois ; B. refuser les signaux dont les frais pèsent trop face au stop ; C. veille calme de
Crabel (ID/NR4, NR4) ; D. seuil du filtre appris (arbres réentraînés chaque année sur le passé).

Méthode : chaque décision du bot (toutes les 15 min en séance, 2014-2026) est enregistrée une fois avec ses votes
(`analysis.assess(trace=...)`), puis chaque variante rejoue la décision (`analysis.decide`), la politique et l'issue
exactement comme `backtest.run_backtest`.

    python -m trading_bot.essai74 trace     → data/history/long/essai74_trace_<marché>.pkl (long, 4 cœurs)
    python -m trading_bot.essai74           → data/essai74.json

Données hors dépôt : data/history/long/{nasdaq,sp500,gold,dax}_1m.npz (HistData), btc_5m.npz (Binance).
"""
from __future__ import annotations

import json
import os
import pickle
import sys
from dataclasses import replace
from datetime import date, datetime, timezone
from multiprocessing import Pool, get_context
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")    # arbres sklearn + processus fils : évite le blocage OpenMP

from .config import DATA_DIR, load_config
from .essai33 import LONG, Bars
from .models import Candle

MARKETS = ("nasdaq", "sp500", "dax", "gold", "bitcoin")
VOTES = ("trend_5m", "trend_15m", "trend_1h", "adx", "vwap", "rsi", "macd", "level", "volume", "orb", "pdhl")
RULES = ("adx_min", "rsi_extreme", "activity", "extension", "opposite", "contradiction", "atr_ratio", "p_resolution")
VARIANTS = ([f"A_{v}" for v in VOTES] + [f"A_{r}" for r in RULES] + ["B_0.10", "B_0.15", "B_0.20"]
            + ["C1_idnr4", "C2_nr4"] + ["D_0.00", "D_0.05", "D_0.10", "D_0.15"])
N_TESTS = len(VARIANTS) * len(MARKETS)
FINAL = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
D_START = {"bitcoin": 2020}                 # première année jugée par le filtre appris (2017 ailleurs)
GROUPS = {"nasdaq": "indices", "sp500": "indices", "dax": "indices", "gold": "gold", "bitcoin": "bitcoin"}
STEP, WARMUP, LOOKBACK = 3, 300, 1440
OUT = Path(DATA_DIR) / "essai74.json"


# ---------------------------------------------------------------- données

def _candles(b: Bars, with_volume: bool) -> list[Candle]:
    v = b.v if (with_volume and b.v is not None) else np.zeros(len(b.ts))
    return [Candle(int(t), float(o), float(h), float(l), float(c), float(x))
            for t, o, h, l, c, x in zip(b.ts, b.o, b.h, b.l, b.c, v)]


def market(key: str, cfg):
    """(réglages de l'actif, bougies 5 min, frais en points pour un prix d'entrée)."""
    from . import essai17 as e17
    from .essai21 import bot_cost
    if key == "dax":
        e17.enable_european_sessions()
        acfg = e17.asset_config(cfg, "dax")
        candles = e17.remap(_candles(Bars.load("dax_1m.npz").resample(300), False))
        pct = acfg.cost_pct
        return acfg, candles, (lambda e: pct / 100 * e)
    if key == "bitcoin":
        candles = _candles(Bars.load("btc_5m.npz"), True)
    else:
        name = {"nasdaq": "nasdaq_1m.npz", "sp500": "sp500_1m.npz", "gold": "gold_1m.npz"}[key]
        candles = _candles(Bars.load(name).resample(300), False)
    return cfg.assets[key], candles, bot_cost(key, cfg)[0]


def trace_path(key: str) -> Path:
    return LONG / f"essai74_trace_{key}.pkl"


def build_trace(key: str) -> str:
    """Toutes les décisions du bot (une toutes les 15 min en séance), avec les votes avant décision."""
    from .analysis import assess
    cfg = load_config()
    acfg, candles, _ = market(key, cfg)
    horizon = 12
    steps = []
    i = WARMUP
    while i < len(candles) - horizon:
        now = candles[i].ts + 300
        hour = (now // 3600) % 24
        if not acfg.session_utc or acfg.session_utc[0] <= hour < acfg.session_utc[1]:
            tr: dict[str, Any] = {}
            a = assess(acfg, candles[max(0, i + 1 - LOOKBACK): i + 1], cfg, trace=tr)
            a.details = {}
            steps.append((i, a, tr))
        i += STEP
    with trace_path(key).open("wb") as f:
        pickle.dump(steps, f, protocol=5)
    return f"{key}: {len(steps)} décisions"


# ---------------------------------------------------------------- veille calme (Crabel)

def calm_days(key: str) -> dict[date, tuple[bool, bool]]:
    """Séance du jour → (veille ID/NR4, veille NR4), séances définies comme à l'essai 72."""
    from . import essai72 as e72
    loaders = {"gold": e72.load_gold, "nasdaq": lambda: Bars.load("nasdaq_1m.npz"),
               "sp500": lambda: Bars.load("sp500_1m.npz"), "dax": lambda: Bars.load("dax_1m.npz"),
               "bitcoin": lambda: Bars.load("btc_30m.npz")}
    ss = e72.sessions("btc" if key == "bitcoin" else key, loaders[key]())
    out = {}
    for k in range(4, len(ss)):
        p1, p2 = ss[k - 1], ss[k - 2]
        rng = [x["h"] - x["l"] for x in ss[k - 4:k]]
        nr4 = rng[-1] <= min(rng)
        out[ss[k]["day"]] = (nr4 and p1["h"] <= p2["h"] and p1["l"] >= p2["l"], nr4)
    return out


def session_day(key: str, ts: int) -> date:
    from .strategies import NY
    if key == "bitcoin":
        return datetime.fromtimestamp(ts, timezone.utc).date()
    if key == "gold":
        return datetime.fromtimestamp(ts + 6 * 3600, NY).date()
    return datetime.fromtimestamp(ts, NY).date()          # DAX : horloge transposée = date de Paris


# ---------------------------------------------------------------- rejeu d'une variante

_BARRIER: dict[tuple, tuple[float, float]] = {}


def _cache_barrier() -> None:
    """La probabilité de résolution (Monte-Carlo à graine fixe) est la même pour les mêmes niveaux : on la garde."""
    from . import indicators as ind
    if getattr(ind.barrier_probabilities, "cached", False):
        return
    raw = ind.barrier_probabilities

    def cached(price, tp, sl, sigma_per_step, steps=12, paths=3000, seed=12345):
        k = (price, tp, sl, sigma_per_step, steps, paths, seed)
        if k not in _BARRIER:
            _BARRIER[k] = raw(price, tp, sl, sigma_per_step, steps, paths, seed)
        return _BARRIER[k]
    cached.cached = True
    ind.barrier_probabilities = cached

def replay(key: str, variant: str, steps, candles, acfg, cfg, cost, calm=None, models=None) -> list[dict[str, Any]]:
    from .analysis import decide
    from .backtest import _policy_allows
    from .bot_model import ASSETS_26, features
    from .context import walk_excursion
    from .models import parse_iso
    from .signals import build_signal
    from .tracker import close_signal, resolve_with_candles

    _cache_barrier()
    disabled = frozenset({variant[2:]}) if variant.startswith("A_") else frozenset()
    vcfg = cfg
    if "atr_ratio" in disabled:
        vcfg = replace(cfg, max_atr_ratio=1e9)
    if "p_resolution" in disabled:
        vcfg = replace(cfg, min_resolution_probability=0.0)
    past: list[tuple[int, int, str, str]] = []
    out = []
    for i, a, tr in steps:
        now = datetime.fromtimestamp(candles[i].ts + 300, tz=timezone.utc)
        if not _policy_allows(acfg, past, now, cfg):
            continue
        if disabled & set(VOTES + RULES[:6]) and tr:
            direction, reasons = decide(tr["votes"], tr["reasons"], tr["corr_veto"], a.price, tr["e20"],
                                        a.hourly_range, cfg, disabled)
            votes = {d: {k: v for k, v in vs.items() if k not in disabled} for d, vs in tr["votes"].items()}
            a = replace(a, direction=direction, reasons_rejected=reasons,
                        score=round(sum(votes[direction].values()), 2) if direction else 0.0,
                        criteria=sorted(votes[direction]) if direction else [])
        if cfg.long_only and a.direction == "short":
            a = replace(a, direction=None)
        sig, _ = build_signal(acfg, a, vcfg, "backtest", now, simulate=True)
        if sig is None or not _policy_allows(acfg, past, now, cfg, 5, sig.direction):
            continue
        risk = abs(sig.entry - sig.stop_loss)
        if variant.startswith("B_") and cost(sig.entry) / risk > float(variant[2:]):
            continue
        if variant.startswith("C"):
            flags = calm.get(session_day(key, int(now.timestamp())))
            if not flags or not flags[0 if variant.startswith("C1") else 1]:
                continue
        pred = None
        if variant.startswith("D_"):
            m = models.get(now.year)
            if m is None:
                continue
            row = sig.to_dict()
            x = features(row.get("criteria"), row.get("meta"), row["created_at"], row.get("score"),
                         row["direction"], key, ASSETS_26)
            pred = float(m.predict(np.array([x]))[0])
            if pred <= float(variant[2:]):
                continue
        exp = int(parse_iso(sig.expires_at).timestamp())
        j = i + 1
        while j < len(candles) and candles[j].ts < exp:
            j += 1
        future = candles[i + 1: max(j, i + 2)]
        outcome = resolve_with_candles(sig, future)
        walk_excursion(sig, future, outcome[2] if outcome else None)
        if outcome is None:
            last = future[-1]
            close_signal(sig, "expired", last.close, datetime.fromtimestamp(last.ts + 300, tz=timezone.utc),
                         acfg.cost_pct)
        else:
            close_signal(sig, outcome[0], outcome[1], outcome[2], acfg.cost_pct)
        past.append((int(now.timestamp()), int(parse_iso(sig.closed_at).timestamp()), sig.status, sig.direction))
        sign = 1 if sig.direction == "long" else -1
        gross = sign * (sig.close_price - sig.entry)
        c = cost(sig.entry)
        out.append({"ts": int(now.timestamp()), "r": (gross - c) / risk, "r2": (gross - 2 * c) / risk,
                    "pred": pred, "row": sig.to_dict() if variant == "REF" else None})
    return out


# ---------------------------------------------------------------- jugement

def _month(ts: int) -> tuple[int, int]:
    d = datetime.fromtimestamp(ts, timezone.utc)
    return d.year, d.month


def stats(trs: list[dict[str, Any]]) -> dict[str, Any]:
    r = np.array([t["r"] for t in trs])
    if not len(r):
        return {"n": 0, "total_r": 0.0, "total_r_x2": 0.0, "mean_r": None, "max_dd": 0.0}
    eq = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(np.r_[0, eq])[1:] - eq)) if len(eq) else 0.0
    return {"n": len(r), "total_r": round(float(r.sum()), 2), "total_r_x2": round(float(sum(t["r2"] for t in trs)), 2),
            "mean_r": round(float(r.mean()), 4), "win": round(float((r > 0).mean()), 3), "max_dd": round(dd, 2)}


def compare(var: list[dict], ref: list[dict], lo: int, hi: int, z_need: float) -> dict[str, Any]:
    v = [t for t in var if lo <= t["ts"] < hi]
    f = [t for t in ref if lo <= t["ts"] < hi]
    sv, sf = stats(v), stats(f)
    months = sorted({_month(t["ts"]) for t in v + f} | {(y, m) for y in range(datetime.fromtimestamp(lo, timezone.utc).year,
                     datetime.fromtimestamp(hi - 1, timezone.utc).year + 1) for m in range(1, 13)
                     if lo <= datetime(y, m, 1, tzinfo=timezone.utc).timestamp() < hi})
    mv, mf = {}, {}
    for t in v:
        mv[_month(t["ts"])] = mv.get(_month(t["ts"]), 0.0) + t["r"]
    for t in f:
        mf[_month(t["ts"])] = mf.get(_month(t["ts"]), 0.0) + t["r"]
    diff = np.array([mv.get(m, 0.0) - mf.get(m, 0.0) for m in months])
    sd = float(diff.std(ddof=1)) if len(diff) > 1 else 0.0
    z = float(diff.mean() / sd * np.sqrt(len(diff))) if sd > 0 else 0.0
    yv, yf = {}, {}
    for t in v:
        yv[_month(t["ts"])[0]] = yv.get(_month(t["ts"])[0], 0.0) + t["r"]
    for t in f:
        yf[_month(t["ts"])[0]] = yf.get(_month(t["ts"])[0], 0.0) + t["r"]
    years = sorted(set(yv) | set(yf))
    better = sum(1 for y in years if yv.get(y, 0.0) > yf.get(y, 0.0) + 1e-9)
    worse = sum(1 for y in years if yv.get(y, 0.0) < yf.get(y, 0.0) - 1e-9)
    same = sv["n"] == sf["n"] and abs(sv["total_r"] - sf["total_r"]) < 1e-6
    out = {"variant": sv, "reference": sf, "years_better": better, "years_worse": worse, "z_monthly": round(z, 2),
           "z_needed": round(z_need, 2), "identical": same,
           "by_year": {y: [round(yv.get(y, 0.0), 2), round(yf.get(y, 0.0), 2)] for y in years}}
    out["passes"] = bool(not same and sv["total_r"] > sf["total_r"] and sv["total_r_x2"] > sf["total_r_x2"]
                         and sv["max_dd"] <= 1.10 * sf["max_dd"] + 1e-9 and better > worse and z >= z_need)
    return out


def fit_models(refs: dict[str, list[dict]], cost_of: dict[str, Any]) -> dict[str, dict[int, Any]]:
    """Arbres de l'essai 25, un par groupe et par année, appris sur les signaux de référence des années d'avant."""
    from .bot_model import ASSETS_26, features
    from .essai25 import models
    make = models()["arbres"]
    out: dict[str, dict[int, Any]] = {}
    for key in MARKETS:
        group = [k for k in MARKETS if GROUPS[k] == GROUPS[key]]
        rows = []
        for k in group:
            for t in refs[k]:
                r = t["row"]
                rows.append((datetime.fromtimestamp(t["ts"], timezone.utc).year,
                             features(r.get("criteria"), r.get("meta"), r["created_at"], r.get("score"), r["direction"],
                                      k, ASSETS_26), t["r"]))
        first = D_START.get(key, 2017)
        last = max(y for y, _, _ in rows)
        out[key] = {}
        for y in range(first, last + 1):
            tr = [(x, r) for yy, x, r in rows if yy < y]
            if len(tr) < 200:
                continue
            m = make()
            m.fit(np.array([x for x, _ in tr]), np.array([r for _, r in tr]))
            out[key][y] = m
    return out


def run_market(args) -> tuple[str, dict[str, Any]]:
    key, models = args
    done = LONG / f"essai74_res_{key}.pkl"
    if done.exists():
        with done.open("rb") as f:
            return key, pickle.load(f)
    cfg = load_config()
    acfg, candles, cost = market(key, cfg)
    with trace_path(key).open("rb") as f:
        steps = pickle.load(f)
    calm = calm_days(key)
    ref = replay(key, "REF", steps, candles, acfg, cfg, cost)
    res: dict[str, list[dict]] = {"REF": ref}
    for v in VARIANTS:
        if v.startswith("D_") and models is None:
            continue
        res[v] = replay(key, v, steps, candles, acfg, cfg, cost, calm, (models or {}).get(key))
        print(f"{key} {v} {len(res[v])} trades", flush=True)
    with done.open("wb") as f:
        pickle.dump(res, f, protocol=5)
    return key, res


def judge_all(res: dict[str, dict[str, list[dict]]]) -> dict[str, Any]:
    z_need = NormalDist().inv_cdf(1 - 0.05 / N_TESTS)
    out: dict[str, Any] = {}
    for key in MARKETS:
        ref = res[key]["REF"]
        start = min(t["ts"] for t in ref)
        dlo = int(datetime(D_START.get(key, 2017), 1, 1, tzinfo=timezone.utc).timestamp())
        cells = {"REF": {"research": stats([t for t in ref if t["ts"] < FINAL]),
                         "final": stats([t for t in ref if t["ts"] >= FINAL])}}
        for v in VARIANTS:
            lo = dlo if v.startswith("D_") else start
            c = compare(res[key][v], ref, lo, FINAL, z_need)
            if c["passes"]:
                end = max(t["ts"] for t in ref) + 1
                c["final"] = compare(res[key][v], ref, FINAL, end, 0.0)
                c["final_ok"] = c["final"]["variant"]["total_r"] >= c["final"]["reference"]["total_r"]
            cells[v] = c
        out[key] = cells
    return out


def run() -> dict[str, Any]:
    with Pool(4) as pool:                         # Bitcoin d'abord : le plus long
        base = dict(pool.map(run_market, [(k, None) for k in ("bitcoin", "gold", "nasdaq", "sp500", "dax")], chunksize=1))
    cost_of = {}
    models = fit_models({k: base[k]["REF"] for k in MARKETS}, cost_of)
    with get_context("spawn").Pool(4) as pool:   # les arbres ont déjà tourné ici : pas de fork
        dres = dict(pool.map(run_d, [(k, models[k]) for k in ("bitcoin", "gold", "nasdaq", "sp500", "dax")], chunksize=1))
    for k in MARKETS:
        base[k].update(dres[k])
    out = {"essai": 74, "variants": VARIANTS, "n_tests": N_TESTS, "final_from": "2025-01-01",
           "markets": judge_all(base)}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


def run_d(args) -> tuple[str, dict[str, list[dict]]]:
    key, models = args
    done = LONG / f"essai74_resD_{key}.pkl"
    if done.exists():
        with done.open("rb") as f:
            return key, pickle.load(f)
    cfg = load_config()
    acfg, candles, cost = market(key, cfg)
    with trace_path(key).open("rb") as f:
        steps = pickle.load(f)
    res = {v: replay(key, v, steps, candles, acfg, cfg, cost, None, models) for v in VARIANTS if v.startswith("D_")}
    with done.open("wb") as f:
        pickle.dump(res, f, protocol=5)
    return key, res


def report(out: dict[str, Any]) -> None:
    for key, cells in out["markets"].items():
        r = cells["REF"]["research"]
        print(f"\n{key} : référence recherche n={r['n']} total={r['total_r']} R moyen={r['mean_r']} baisse max={r['max_dd']}")
        for v in VARIANTS:
            c = cells[v]
            s, f = c["variant"], c["reference"]
            tag = "identique" if c["identical"] else ("PASSE" if c["passes"] else "")
            print(f"  {v:16s} n={s['n']:5d} total={s['total_r']:8.2f} (réf {f['total_r']:8.2f}) ×2={s['total_r_x2']:8.2f} "
                  f"dd={s['max_dd']:6.2f} ({f['max_dd']:6.2f}) ans +{c['years_better']}/-{c['years_worse']} "
                  f"z={c['z_monthly']:5.2f}/{c['z_needed']} {tag}"
                  + (f" final {c['final']['variant']['total_r']} vs {c['final']['reference']['total_r']}" if c.get("final") else ""))


if __name__ == "__main__":
    if sys.argv[1:2] == ["trace"]:
        with Pool(4) as p:
            for msg in p.imap_unordered(build_trace, sys.argv[2:] or list(MARKETS)):
                print(msg, flush=True)
    else:
        report(run())
