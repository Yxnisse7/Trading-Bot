"""Essai 18 (HYPOTHESES.md) : scalping de quelques minutes sur l'or, règles reformulées.

Bougies 1 min Dukascopy (or au comptant), contexte 5 min, 15 min et 1 h reconstruit à partir d'elles. 4 entrées
(et leur réunion) × 2 sorties, un seul trade à la fois, frais d'un compte ECN fixes en $ par once. Une décision ne
lit que des bougies closes : signal sur la clôture d'une bougie 1 min, entrée à l'ouverture de la suivante.
"""
from __future__ import annotations

import json
import lzma
import struct
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from . import essai14 as e14
from . import indicators as ind
from . import strategies as sl
from .models import Candle
from .providers import history as hist

N_TRIALS = 384
COST_USD = 0.30            # écart achat-vente + commission + glissement, par once et par aller-retour
NY = ZoneInfo("America/New_York")
ENTRIES = ("R1", "R2", "R3", "R4", "R1-R4")
EXITS = ("X1", "X2")
MAX_HOLD = 3600
STOP_PAD = 0.25
LEVEL_STEP = 10.0


# ---------------------------------------------------------------- données
def download(path: Path, start: date, end: date, pause: float = 0.3, deadline: float | None = None) -> dict[str, int]:
    """Bougies 1 min BID de l'or, gardées par jour (du plus récent au plus ancien) ; reprend là où il s'est arrêté."""
    cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"scale": 1000.0, "days": {}}
    d = end
    while d > start:
        d -= timedelta(days=1)
        if deadline is not None and time.time() > deadline:
            break
        if d.weekday() == 5 or d.isoformat() in cache["days"]:
            continue
        raw = hist._get(f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{d.year}/{d.month - 1:02d}/{d.day:02d}/BID_candles_min_1.bi5")
        day0 = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
        try:
            rows = [[c.ts, c.open, c.high, c.low, c.close, c.volume]
                    for c in (hist.parse_dukascopy_candles(raw, day0, cache["scale"]) if raw else [])]
        except (lzma.LZMAError, struct.error):
            continue
        cache["days"][d.isoformat()] = rows
        time.sleep(pause)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache), encoding="utf-8")
    return {"days": len(cache["days"]), "with_data": sum(1 for v in cache["days"].values() if v)}


def load(path: Path) -> list[Candle]:
    cache = json.loads(path.read_text(encoding="utf-8"))
    out = {r[0]: Candle(*r) for rows in cache["days"].values() for r in rows}
    return [out[k] for k in sorted(out)]


# ---------------------------------------------------------------- indicateurs
def stochastic(c: list[Candle], period: int = 21, k_smooth: int = 3, d_smooth: int = 3):
    raw: list[float] = []
    for i in range(len(c)):
        if i < period - 1:
            raw.append(50.0)
            continue
        w = c[i - period + 1:i + 1]
        hi, lo = max(x.high for x in w), min(x.low for x in w)
        raw.append(100 * (c[i].close - lo) / (hi - lo) if hi > lo else 50.0)
    k = [v if v is not None else 50.0 for v in ind.sma(raw, k_smooth)]
    d = [v if v is not None else 50.0 for v in ind.sma(k, d_smooth)]
    return k, d


class Frame:
    """Une unité de temps : bougies, MM20, RSI 21, ATR 14, et l'index de la dernière bougie close à un instant."""

    def __init__(self, candles: list[Candle], step: int):
        self.c, self.step = candles, step
        closes = [x.close for x in candles]
        self.ma20 = ind.sma(closes, 20)
        self.rsi = ind.rsi(closes, 21)
        self.atr = ind.atr(candles, 14)
        self.ts = [x.ts for x in candles]

    def last_closed(self, now: int, start: int) -> int:
        """Index de la dernière bougie close à `now`, en avançant depuis `start` (appels croissants)."""
        j = start
        while j + 1 < len(self.c) and self.ts[j + 1] + self.step <= now:
            j += 1
        return j if j < len(self.c) and self.ts[j] + self.step <= now else -1


class Ctx:
    def __init__(self, m1: list[Candle]):
        self.m1 = m1
        closes = [x.close for x in m1]
        self.ma20, self.ma50 = ind.sma(closes, 20), ind.sma(closes, 50)
        self.k, self.d = stochastic(m1)
        vols = [x.volume for x in m1]
        self.vol20 = [None] + ind.sma(vols, 20)[:-1]          # moyenne des 20 bougies précédentes
        self.f5, self.f15, self.f60 = Frame(ind.resample(m1, 5), 300), Frame(ind.resample(m1, 15), 900), Frame(ind.resample(m1, 60), 3600)
        self.i5, self.i15, self.i60 = [], [], []
        p5 = p15 = p60 = 0
        for c in m1:
            now = c.ts + 60
            a, b, h = self.f5.last_closed(now, p5), self.f15.last_closed(now, p15), self.f60.last_closed(now, p60)
            self.i5.append(a)
            self.i15.append(b)
            self.i60.append(h)
            p5, p15, p60 = max(a, 0), max(b, 0), max(h, 0)


# ---------------------------------------------------------------- règles
def _trend(f: Frame, j: int, d: int) -> bool:
    if j < 3 or f.ma20[j] is None or f.ma20[j - 3] is None or f.rsi[j] is None:
        return False
    return (d * (f.c[j].close - f.ma20[j]) > 0 and d * (f.ma20[j] - f.ma20[j - 3]) > 0
            and d * (f.rsi[j] - 50) > 0)


def context_ok(x: Ctx, i: int, d: int) -> bool:
    j5, j15, j60 = x.i5[i], x.i15[i], x.i60[i]
    if j5 < 0 or j15 < 0 or j60 < 0 or not (_trend(x.f5, j5, d) and _trend(x.f15, j15, d)):
        return False
    h = x.f60
    if h.ma20[j60] is None or d * (h.c[j60].close - h.ma20[j60]) <= 0:
        return False
    a5 = x.f5.atr[j5]
    return a5 is not None and d * (x.f5.c[j5].close - x.f5.ma20[j5]) < 2 * a5


def hours_ok(ts: int) -> bool:
    """Instant du signal (clôture de la bougie 1 min) : 7:00-20:00 UTC en semaine (19:00 le vendredi), hors annonces."""
    u = datetime.fromtimestamp(ts, timezone.utc)
    if u.weekday() >= 5 or not 7 <= u.hour < (19 if u.weekday() == 4 else 20):
        return False
    n = datetime.fromtimestamp(ts, NY)
    m = n.hour * 60 + n.minute
    return not (8 * 60 + 25 <= m < 8 * 60 + 45 or 9 * 60 + 55 <= m < 10 * 60 + 5)


def r1(x: Ctx, i: int, d: int) -> bool:
    """Repli sur la MM20 1 min, au-dessus de la MM50, stochastique qui repart dans le sens de la tendance."""
    if i < 5 or x.ma50[i - 4] is None:
        return False
    c = x.m1
    touched = any(d * ((c[j].low if d > 0 else c[j].high) - x.ma20[j]) <= 0 for j in range(i - 4, i + 1))
    above = all(d * (c[j].close - x.ma50[j]) > 0 for j in range(i - 4, i + 1))
    k0, d0, k1, d1 = x.k[i - 1], x.d[i - 1], x.k[i], x.d[i]
    cross = d * (k0 - d0) <= 0 < d * (k1 - d1) and d * (k1 - 50) < 0
    return touched and above and cross and d * (c[i].close - x.ma20[i]) > 0


def r2(x: Ctx, i: int, d: int) -> bool:
    """Cassure d'une pause de 4 bougies 5 min, avec du volume."""
    j5 = x.i5[i]
    if j5 < 3 or x.f5.atr[j5] is None or x.vol20[i] is None or i < 1:
        return False
    w = x.f5.c[j5 - 3:j5 + 1]
    hi, lo = max(b.high for b in w), min(b.low for b in w)
    if hi - lo > x.f5.atr[j5]:
        return False
    edge = hi if d > 0 else lo
    c = x.m1
    return d * (c[i].close - edge) > 0 >= d * (c[i - 1].close - edge) and c[i].volume > 1.5 * x.vol20[i]


def r3(x: Ctx, i: int, d: int) -> bool:
    """Le RSI 21 en 5 min est revenu vers 50, puis une bougie 1 min repart au-delà de la précédente."""
    j5 = x.i5[i]
    if j5 < 2 or i < 1:
        return False
    zone = [x.f5.rsi[j] for j in range(j5 - 2, j5 + 1)]
    if any(v is None for v in zone):
        return False
    near = any((45 <= v <= 52) if d > 0 else (48 <= v <= 55) for v in zone)
    c = x.m1
    return near and d * (c[i].close - (c[i - 1].high if d > 0 else c[i - 1].low)) > 0


def r4(x: Ctx, i: int, d: int) -> bool:
    """Chiffre rond (tous les 10 $) cassé dans les 30 dernières minutes, retesté sans clôturer de l'autre côté."""
    j5 = x.i5[i]
    if j5 < 0 or x.f5.atr[j5] is None or i < 31:
        return False
    c = x.m1
    if not (d * (c[i].close - c[i].open) > 0 and d * (c[i].close - (c[i - 1].high if d > 0 else c[i - 1].low)) > 0):
        return False
    for j in range(i - 1, i - 31, -1):
        a, b = c[j - 1].close, c[j].close
        lvl = (b // LEVEL_STEP) * LEVEL_STEP if d > 0 else -((-b) // LEVEL_STEP) * LEVEL_STEP
        if not d * (b - lvl) > 0 >= d * (a - lvl):
            continue
        after = c[j:i + 1]
        if any(d * (y.close - lvl) < 0 for y in after):
            return False
        back = min(y.low for y in after[1:]) if d > 0 else max(y.high for y in after[1:])
        return d * (back - lvl) <= 0.3 * x.f5.atr[j5]
    return False


RULES: dict[str, Callable[[Ctx, int, int], bool]] = {"R1": r1, "R2": r2, "R3": r3, "R4": r4}


def signal(entry: str, x: Ctx, i: int) -> int:
    """+1 achat, −1 vente, 0 rien."""
    names = ("R1", "R2", "R3", "R4") if entry == "R1-R4" else (entry,)
    for d in (1, -1):
        if context_ok(x, i, d) and any(RULES[n](x, i, d) for n in names):
            return d
    return 0


# ---------------------------------------------------------------- exécution
def _close_ts(ts: int) -> int:
    u = datetime.fromtimestamp(ts, timezone.utc)
    return int(u.replace(hour=20, minute=30, second=0).timestamp())


def simulate(x: Ctx, entry: str, exit_: str) -> list[sl.Trade]:
    c, out, i, n = x.m1, [], 60, len(x.m1)
    while i < n - 1:
        if not hours_ok(c[i].ts + 60):
            i += 1
            continue
        d = signal(entry, x, i)
        if not d:
            i += 1
            continue
        j5 = x.i5[i]
        a5 = x.f5.atr[j5]
        e_bar = i + 1
        if c[e_bar].ts - c[i].ts > 300:                        # trou dans les données (week-end, coupure)
            i += 1
            continue
        entry_px = c[e_bar].open
        w = c[i - 9:i + 1]
        stop = (min(b.low for b in w) - STOP_PAD) if d > 0 else (max(b.high for b in w) + STOP_PAD)
        dist = d * (entry_px - stop)
        if dist < 0.5 * a5:
            dist = 0.5 * a5
            stop = entry_px - d * dist
        if dist > 1.5 * a5:
            i += 1
            continue
        j60 = x.i60[i]
        w60 = x.f60.c[max(0, j60 - 23):j60 + 1]
        wall = max(b.high for b in w60) if d > 0 else min(b.low for b in w60)
        if d * (wall - entry_px) > 0 and d * (wall - entry_px) < 1.5 * dist:
            i += 1
            continue
        t = manage(c, e_bar, d, entry_px, stop, dist, exit_)
        if t is None:
            break
        exit_px, exit_i, reason = t
        out.append(sl.Trade(f"{entry}_{exit_}", "gold", "long" if d > 0 else "short", c[e_bar].ts,
                            c[exit_i].ts + 60 if reason in ("stop", "objectif", "suiveur") else c[exit_i].ts,
                            entry_px, exit_px, dist, reason))
        i = exit_i + 1
    return out


def manage(c: list[Candle], e: int, d: int, entry: float, stop: float, dist: float, exit_: str):
    """Renvoie (prix de sortie équivalent pour toute la position, index de la bougie de sortie, raison)."""
    target = entry + d * dist
    limit_ts = min(c[e].ts + MAX_HOLD, _close_ts(c[e].ts))
    half = None                                               # prix de la 1re moitié une fois l'objectif touché
    for j in range(e, len(c)):
        b = c[j]
        if j > e and b.ts - c[j - 1].ts > 300:                 # trou dans les données : sortie à la dernière clôture
            return _fill(half, c[j - 1].close), j - 1, "durée"
        if b.ts >= limit_ts:
            return _fill(half, b.open), j, "durée"
        if half is not None and j - e >= 1:
            lows = c[max(e, j - 5):j]
            trail = min(y.low for y in lows) if d > 0 else max(y.high for y in lows)
            stop = max(stop, trail) if d > 0 else min(stop, trail)
        hit_stop = d * ((b.low if d > 0 else b.high) - stop) <= 0
        if half is None:
            hit_target = d * ((b.high if d > 0 else b.low) - target) >= 0
            if hit_stop:
                return _fill(None, stop), j, "stop"
            if hit_target:
                if exit_ == "X1":
                    return target, j, "objectif"
                half, stop = target, entry
                if d * ((b.low if d > 0 else b.high) - entry) <= 0:      # même bougie : reste sorti à l'entrée (prudent)
                    return _fill(half, entry), j, "objectif"
            continue
        if hit_stop:
            return _fill(half, stop), j, "suiveur"
    return None


def _fill(half: float | None, px: float) -> float:
    return px if half is None else (half + px) / 2


# ---------------------------------------------------------------- verdict
def verdict(trades: list[sl.Trade]) -> dict[str, Any]:
    cost = (COST_USD, 1.0)
    disc = sl.evaluate(trades, 0.0, cost, start_ts=e14.SPLIT)
    conf = sl.evaluate(trades, 0.0, cost, end_ts=e14.SPLIT)
    both = sl.evaluate(trades, 0.0, cost)
    ok_d, ok_c = sl.discovery_pass(disc), sl.confirmation_pass(conf)
    status = ("prouvé" if sl.proven(both, N_TRIALS) else "validé") if ok_d and ok_c else (
        "écarté (découverte)" if not ok_d else "écarté (confirmation)")
    days = len({datetime.fromtimestamp(t.entry_ts, timezone.utc).date() for t in trades}) or 1
    reasons: dict[str, int] = {}
    for t in trades:
        reasons[t.reason] = reasons.get(t.reason, 0) + 1
    avg_stop = sum(t.risk for t in trades) / len(trades) if trades else None
    return {"discovery": disc, "confirmation": conf, "all": both, "status": status,
            "trades_per_active_day": round(len(trades) / days, 2), "exits": reasons,
            "avg_stop_usd": round(avg_stop, 2) if avg_stop else None,
            "cost_r": round(COST_USD / avg_stop, 3) if avg_stop else None}


def run(m1: list[Candle], log: Callable[[str], None] = print) -> dict[str, Any]:
    x = Ctx(m1)
    out: dict[str, Any] = {"essai": 18, "split": "2025-09-28", "n_trials": N_TRIALS, "cost_usd": COST_USD,
                           "first": datetime.fromtimestamp(m1[0].ts, timezone.utc).date().isoformat(),
                           "last": datetime.fromtimestamp(m1[-1].ts, timezone.utc).date().isoformat(),
                           "cells": {}}
    for e in ENTRIES:
        for xx in EXITS:
            v = verdict(simulate(x, e, xx))
            out["cells"][f"{e}_{xx}"] = v
            d, c, a = v["discovery"], v["confirmation"], v["all"]
            log(f"{e:6s} {xx} découverte n={d['n']:5d} {d['net']['mean_r']} PF {d['net']['profit_factor']} "
                f"moitiés {d['first_half']['mean_r']}/{d['second_half']['mean_r']} | confirmation n={c['n']:5d} "
                f"{c['net']['mean_r']} PF {c['net']['profit_factor']} | 24 mois {a['net']['mean_r']} ± {a['net']['se']} "
                f"brut {a['gross']['mean_r']} | {v['trades_per_active_day']}/jour stop moyen {v['avg_stop_usd']} $ "
                f"frais {v['cost_r']} R → {v['status']}")
    return out
