"""Essai 20 (HYPOTHESES.md) : rebond après une bougie 5 min d'épuisement sur l'or (idée de Yanisse).

Bougies 1 min Dukascopy (celles de l'essai 18), bougies 5 min reconstruites ; frais Vantage RAW 0,21 $ par once.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from . import essai14 as e14
from . import essai18 as e18
from . import indicators as ind
from . import strategies as sl
from .models import Candle

N_TRIALS = 394
COST_USD = 0.21
SIZE_MULT = 2.0
NEAR_LEVEL = 1.0
CONFIRM_USD = 0.20
CONFIRM_MIN = 5
STOP_PAD = 0.25
MAX_HOLD = 1800
LEVEL_STEP = 10.0


def exhaustion(m5: list[Candle], k: int) -> int:
    """+1 : bougie de baisse d'épuisement (on cherche un achat) ; −1 : bougie de hausse ; 0 sinon."""
    if k < 20:
        return 0
    avg = sum(c.range for c in m5[k - 20:k]) / 20
    c = m5[k]
    if avg <= 0 or c.range < SIZE_MULT * avg or c.close == c.open:
        return 0
    return 1 if c.close < c.open else -1


def on_level(m5: list[Candle], k: int, d: int) -> bool:
    """Le bout de la mèche passe à moins de 1 $ d'un chiffre rond ou de l'extrême des 3 h précédentes,
    et la clôture reste du bon côté de ce niveau."""
    c = m5[k]
    tip = c.low if d > 0 else c.high
    prev = m5[max(0, k - 36):k]
    if not prev:
        return False
    levels = [round(tip / LEVEL_STEP) * LEVEL_STEP,
              min(x.low for x in prev) if d > 0 else max(x.high for x in prev)]
    return any(abs(tip - lv) <= NEAR_LEVEL and d * (c.close - lv) > 0 for lv in levels)


def simulate(m1: list[Candle], with_level: bool, target_r: float) -> list[sl.Trade]:
    m5 = ind.resample(m1, 5)
    idx = {c.ts: i for i, c in enumerate(m1)}
    out: list[sl.Trade] = []
    busy_until = 0
    for k, c5 in enumerate(m5):
        close_ts = c5.ts + 300
        if close_ts < busy_until or not e18.hours_ok(close_ts):
            continue
        d = exhaustion(m5, k)
        if not d or (with_level and not on_level(m5, k, d)):
            continue
        j = idx.get(close_ts)                                       # première minute après la bougie 5 min
        if j is None:
            continue
        entry_i = None
        for a in range(j, min(j + CONFIRM_MIN, len(m1) - 1)):
            if m1[a].ts - close_ts >= CONFIRM_MIN * 60:
                break
            if d * (m1[a].close - c5.close) >= CONFIRM_USD:
                entry_i = a + 1
                break
        if entry_i is None or m1[entry_i].ts - m1[entry_i - 1].ts > 300:
            continue
        entry = m1[entry_i].open
        stop = (c5.low - STOP_PAD) if d > 0 else (c5.high + STOP_PAD)
        dist = d * (entry - stop)
        if dist <= 0:
            continue
        res = manage(m1, entry_i, d, entry, stop, entry + d * target_r * dist)
        if res is None:
            break
        px, ei, reason = res
        out.append(sl.Trade(f"epuisement_{'niveau' if with_level else 'tout'}_{target_r:g}R", "gold",
                            "long" if d > 0 else "short", m1[entry_i].ts, m1[ei].ts + 60, entry, px, dist, reason))
        busy_until = m1[ei].ts + 60
    return out


def manage(m1: list[Candle], e: int, d: int, entry: float, stop: float, target: float):
    for j in range(e, len(m1)):
        b = m1[j]
        if j > e and b.ts - m1[j - 1].ts > 300:                 # trou dans les données : dernière clôture
            return m1[j - 1].close, j - 1, "durée"
        if b.ts - m1[e].ts >= MAX_HOLD:
            return b.open, j, "durée"
        if d * ((b.low if d > 0 else b.high) - stop) <= 0:
            return stop, j, "stop"
        if d * ((b.high if d > 0 else b.low) - target) >= 0:
            return target, j, "objectif"
    return None


def verdict(trades: list[sl.Trade]) -> dict[str, Any]:
    cost = (COST_USD, 1.0)
    disc = sl.evaluate(trades, 0.0, cost, start_ts=e14.SPLIT)
    conf = sl.evaluate(trades, 0.0, cost, end_ts=e14.SPLIT)
    both = sl.evaluate(trades, 0.0, cost)
    ok_d, ok_c = sl.discovery_pass(disc), sl.confirmation_pass(conf)
    status = ("prouvé" if sl.proven(both, N_TRIALS) else "validé") if ok_d and ok_c else (
        "écarté (découverte)" if not ok_d else "écarté (confirmation)")
    wins = sum(1 for t in trades if t.gross_points() - COST_USD > 0)
    days = len({datetime.fromtimestamp(t.entry_ts, timezone.utc).date() for t in trades}) or 1
    return {"discovery": disc, "confirmation": conf, "all": both, "status": status,
            "win_rate": round(wins / len(trades), 3) if trades else None,
            "trades_per_active_day": round(len(trades) / days, 2),
            "avg_stop_usd": round(sum(t.risk for t in trades) / len(trades), 2) if trades else None}


def run(m1: list[Candle], log: Callable[[str], None] = print) -> dict[str, Any]:
    out: dict[str, Any] = {"essai": 20, "split": "2025-09-28", "n_trials": N_TRIALS, "cost_usd": COST_USD, "cells": {}}
    for with_level in (True, False):
        for tr in (1.0, 2.0):
            v = verdict(simulate(m1, with_level, tr))
            name = f"{'niveau' if with_level else 'sans_niveau'}_{tr:g}R"
            out["cells"][name] = v
            d, c, a = v["discovery"], v["confirmation"], v["all"]
            log(f"{name:15s} découverte n={d['n']} {d['net']['mean_r']} PF {d['net']['profit_factor']} moitiés "
                f"{d['first_half']['mean_r']}/{d['second_half']['mean_r']} | confirmation n={c['n']} {c['net']['mean_r']} "
                f"PF {c['net']['profit_factor']} | 24 mois {a['net']['mean_r']} ± {a['net']['se']} brut {a['gross']['mean_r']} "
                f"| réussite {v['win_rate']} stop moyen {v['avg_stop_usd']} $ → {v['status']}")
    return out
