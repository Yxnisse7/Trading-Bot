"""Essai 21 (HYPOTHESES.md) : le test des 1000 singes.

Pour chaque cellule (une stratégie sur un actif), on garde le sens, la distance du stop, l'objectif et la durée de
chaque trade réel, mais l'entrée est tirée au hasard à la même heure de la journée (heure de New York), n'importe où
dans les 24 mois. 1 000 singes par cellule ; la cellule « bat les singes » si son R net moyen dépasse au moins 950
d'entre eux. Pour les filtres (qui ne font que retirer des trades du bot), un second témoin tire au hasard le même
nombre de trades parmi ceux du bot.

    python -m trading_bot.essai21          → data/essai21.json
"""
from __future__ import annotations

import zlib
from datetime import datetime, timezone
from statistics import NormalDist
from typing import Any, Callable

import numpy as np

from . import essai14 as e14
from . import essai15 as e15
from . import essai17 as e17
from . import strategies as sl
from .models import Candle

N_MONKEYS = 1000
MIN_TRADES = 30
ASSETS = ("gold", "nasdaq", "sp500", "bitcoin")
TARGET_REASONS = {"objectif", "tp", "target"}
FILTER_CELLS = set(e14.FILTERS) | set(e15.FILTERS) | {"G40"}
GAP = 4 * 86400


class Bars:
    """Bougies en tableaux, et pour chaque heure de New York la liste des bougies qui y commencent."""

    def __init__(self, candles: list[Candle]):
        self.ts = np.array([c.ts for c in candles], dtype=np.int64)
        self.o = np.array([c.open for c in candles])
        self.h = np.array([c.high for c in candles])
        self.l = np.array([c.low for c in candles])
        self.c = np.array([c.close for c in candles])
        hours = np.array([datetime.fromtimestamp(int(t), sl.NY).hour for t in self.ts])
        self.by_hour = {hh: np.flatnonzero(hours == hh) for hh in range(24)}
        gap = np.zeros(len(self.ts), dtype=np.int64)
        gap[1:] = np.diff(self.ts) > GAP
        self.gaps = np.cumsum(gap)                      # nombre de trous jusqu'à la bougie i incluse

    def index(self, ts: int) -> int:
        return int(np.searchsorted(self.ts, ts, side="left"))


def shape(t: sl.Trade, bars: Bars) -> tuple[int, int, float | None]:
    """Heure de New York de l'entrée, nombre de bougies tenues, distance de l'objectif (si sorti à l'objectif)."""
    i, j = bars.index(t.entry_ts), bars.index(t.exit_ts)
    nb = max(1, min(j, len(bars.ts) - 1) - i + 1)
    tp = getattr(t, "tp", None)                         # trades du bot : leur objectif, même s'il n'a pas été touché
    if tp:
        tgt = abs(tp - t.entry)
    else:
        tgt = abs(t.exit - t.entry) if t.reason in TARGET_REASONS and t.gross_points() > 0 else None
    return datetime.fromtimestamp(t.entry_ts, sl.NY).hour, nb, tgt


def monkey_rs(t: sl.Trade, bars: Bars, cost_pts: Callable[[float], float], rng: np.random.Generator,
              m: int = N_MONKEYS) -> np.ndarray:
    """R nets de m faux trades : même sens, même stop, même objectif, même durée, entrée au hasard à la même heure."""
    hour, nb, tgt = shape(t, bars)
    pool = bars.by_hour[hour]
    pool = pool[pool + nb <= len(bars.ts)]
    pool = pool[bars.gaps[pool + nb - 1] == bars.gaps[pool]]
    if not len(pool):
        return np.full(m, np.nan)
    k = rng.choice(pool, size=m)
    idx = k[:, None] + np.arange(nb)[None, :]
    entry = bars.o[k]
    long = t.direction == "long"
    sign = 1.0 if long else -1.0
    stop = entry - sign * t.risk
    O, H, L = bars.o[idx], bars.h[idx], bars.l[idx]
    hit_s = (L <= stop[:, None]) if long else (H >= stop[:, None])
    s_at = np.where(hit_s.any(1), hit_s.argmax(1), nb)
    if tgt is not None:
        target = entry + sign * tgt
        hit_t = (H >= target[:, None]) if long else (L <= target[:, None])
        t_at = np.where(hit_t.any(1), hit_t.argmax(1), nb)
    else:
        target, t_at = None, np.full(m, nb)
    rows = np.arange(m)
    px = bars.c[k + nb - 1].copy()                          # sortie à la clôture au bout de la durée
    by_t = t_at < s_at                                      # stop prioritaire dans la même bougie
    if target is not None and by_t.any():
        o = O[rows[by_t], t_at[by_t]]
        px[by_t] = np.maximum(target[by_t], o) if long else np.minimum(target[by_t], o)
    by_s = s_at < nb
    by_s &= ~by_t
    if by_s.any():
        o = O[rows[by_s], s_at[by_s]]
        px[by_s] = np.minimum(stop[by_s], o) if long else np.maximum(stop[by_s], o)
    return (sign * (px - entry) - np.array([cost_pts(e) for e in entry])) / t.risk


def real_rs(trades: list[sl.Trade], cost_pts: Callable[[float], float]) -> np.ndarray:
    return np.array([(t.gross_points() - cost_pts(t.entry)) / t.risk for t in trades])


def judge(name: str, asset: str, trades: list[sl.Trade], bars: Bars, cost_pts: Callable[[float], float],
          base: list[sl.Trade] | None = None) -> dict[str, Any]:
    trades = sorted((t for t in trades if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
    out: dict[str, Any] = {"idea": name, "asset": asset, "n": len(trades)}
    if len(trades) < MIN_TRADES:
        out["status"] = "pas de verdict (moins de 30 trades)"
        return out
    rng = np.random.default_rng(zlib.crc32(f"essai21:{name}:{asset}".encode()))
    real = real_rs(trades, cost_pts)
    mk = np.vstack([monkey_rs(t, bars, cost_pts, rng) for t in trades])     # trades × singes
    keep = ~np.isnan(mk[:, 0])
    disc = np.array([t.entry_ts >= e14.SPLIT for t in trades])

    def compare(sel: np.ndarray) -> dict[str, Any]:
        sel = sel & keep
        if sel.sum() < MIN_TRADES:
            return {"n": int(sel.sum())}
        r, means = float(real[sel].mean()), mk[sel].mean(0)
        sd = float(means.std(ddof=1))
        return {"n": int(sel.sum()), "real_r": round(r, 4), "monkeys_r": round(float(means.mean()), 4),
                "monkeys_p95": round(float(np.percentile(means, 95)), 4), "monkeys_sd": round(sd, 4),
                "beaten": int((means < r).sum()), "z": round((r - float(means.mean())) / sd, 2) if sd > 0 else None}

    out["all"] = compare(np.ones(len(trades), bool))
    out["discovery"] = compare(disc)
    out["confirmation"] = compare(~disc)
    if base is not None and name in FILTER_CELLS:
        b = real_rs(sorted((t for t in base if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts), cost_pts)
        n = len(trades)
        if n < len(b):
            picks = np.argsort(rng.random((N_MONKEYS, len(b))), axis=1)[:, :n]
            means = b[picks].mean(1)
            r = float(real.mean())
            out["filter_monkeys"] = {"base_n": len(b), "base_r": round(float(b.mean()), 4),
                                     "monkeys_p95": round(float(np.percentile(means, 95)), 4),
                                     "beaten": int((means < r).sum())}
    return out


def status(cells: dict[str, dict[str, Any]]) -> int:
    """Verdicts : bat les singes (≥ 950 sur 1000), « nettement » au-delà du seuil corrigé du nombre de cellules."""
    judged = [v for v in cells.values() if "all" in v and "beaten" in v["all"]]
    z_thr = NormalDist().inv_cdf(1 - 0.05 / max(1, len(judged)))
    for v in judged:
        a, f = v["all"], v.get("filter_monkeys")
        ok = a["beaten"] >= 950 and (f is None or f["beaten"] >= 950)
        strong = ok and (a["z"] or 0) > z_thr
        v["status"] = "bat nettement les singes" if strong else "bat les singes" if ok else "ne bat pas les singes"
    return len(judged)


def bot_cost(asset: str, cfg) -> tuple[Callable[[float], float], str]:
    from .topstep import FEES, PRODUCTS
    if asset in e14.FUTURES:
        pts = sum(FEES[asset]) / PRODUCTS[asset][1]
        return (lambda _e: pts), "Topstep"
    pct = cfg.assets[asset].cost_pct
    return (lambda e: pct / 100 * e), "bot"


def run(store, cfg, log: Callable[[str], None] = print) -> dict[str, Any]:
    from . import essai18 as e18
    from . import essai20 as e20
    out: dict[str, Any] = {"essai": 21, "n_monkeys": N_MONKEYS, "split": "2025-09-28", "cells": {}}
    ctxs = {k: e15.Ctx(c) for k in ASSETS if (c := store.load_history(k))}
    for key, ctx in ctxs.items():
        real = ctx.m5.c
        bars = Bars(real)
        cost, cost_label = bot_cost(key, cfg)
        rows = store._read(store.dir / "history" / f"essai14_bot_{key}.json", None)
        if rows is None:
            from .backtest import run_backtest
            rows = run_backtest(cfg.assets[key], real, cfg)["trades"]
        base = e14.bot_trades(rows, key)
        other = ctxs.get({"nasdaq": "sp500", "sp500": "nasdaq"}.get(key, ""))
        for name, trades in e17.cells(key, real, real, ctx, other, base, cfg.assets[key].cost_pct):
            v = judge(name, key, trades, bars, cost, base)
            v["fees"] = cost_label
            out["cells"][f"{name}:{key}"] = v
            log(line(v))
    path = store.dir / "history" / "gold_1m_days.json"
    if path.exists():
        m1 = e18.load(path)
        bars = Bars(m1)
        x = e18.Ctx(m1)
        for e in e18.ENTRIES:
            for xx in e18.EXITS:
                v = judge(f"{e}_{xx}", "gold_1m", e18.simulate(x, e, xx), bars, lambda _e: e18.COST_USD)
                out["cells"][f"essai18_{e}_{xx}:gold"] = v
                log(line(v))
        for with_level in (True, False):
            for tr in (1.0, 2.0):
                name = f"{'niveau' if with_level else 'sans_niveau'}_{tr:g}R"
                v = judge(name, "gold_1m", e20.simulate(m1, with_level, tr), bars, lambda _e: e20.COST_USD)
                out["cells"][f"essai20_{name}:gold"] = v
                log(line(v))
    out["n_judged"] = status(out["cells"])
    return out


def line(v: dict[str, Any]) -> str:
    a = v.get("all") or {}
    if "beaten" not in a:
        return f"{v['idea']:17s} {v['asset']:8s} n={v['n']:5d} → pas de verdict"
    f = v.get("filter_monkeys")
    fx = f" | filtre au hasard p95 {f['monkeys_p95']} battu {f['beaten']}/1000" if f else ""
    d, c = v["discovery"], v["confirmation"]
    return (f"{v['idea']:17s} {v['asset']:8s} n={a['n']:5d} réel {a['real_r']} | singes {a['monkeys_r']} "
            f"(p95 {a['monkeys_p95']}) battus {a['beaten']}/1000 z {a['z']} | découverte {d.get('beaten')} "
            f"confirmation {c.get('beaten')}{fx}")


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    out = run(eng.store, eng.cfg, log=lambda s: print(s, flush=True))
    for k, v in out["cells"].items():
        if "status" in v and "all" in v and "beaten" in v["all"]:
            print(f"{k:28s} {v['status']}", flush=True)
    out["updated_at"] = iso(utcnow())
    eng.store._write(eng.store.dir / "essai21.json", out)


if __name__ == "__main__":
    main()
