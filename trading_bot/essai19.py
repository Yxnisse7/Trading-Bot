"""Essai 19 (HYPOTHESES.md) : scalping de quelques secondes sur l'or, sur les ticks Dukascopy.

Entrée sur un départ brusque dans le sens du contexte 5 et 15 min, sortie à +X, stop à −S ou au bout de 60 s.
Exécution au prix milieu plus les frais de Vantage RAW (écart 0,15 $ payé à moitié à chaque bout, commission
0,06 $), ou, pour information, aux vrais prix acheteur et vendeur Dukascopy.
"""
from __future__ import annotations

import lzma
import struct
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, NamedTuple

from . import essai18 as e18
from . import strategies as sl
from .models import Candle

N_TRIALS = 390
SPLIT = int(datetime(2026, 9, 21, tzinfo=timezone.utc).timestamp())
HALF_SPREAD = 0.075
COMMISSION = 0.06
TARGETS = (0.10, 0.30, 0.60)
STOPS = (0.50, 1.00)
LOOKBACK_MS, BURST_MS, BURST_USD = 60_000, 10_000, 0.30
MAX_HOLD_MS, PAUSE_MS = 60_000, 10_000
SCALE = 1000.0


class Tick(NamedTuple):
    ms: int          # millisecondes UTC
    bid: float
    ask: float

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2


def parse_hour(raw: bytes, hour_ms: int) -> list[Tick]:
    """Fichier HHh_ticks.bi5 : LZMA, enregistrements de 20 octets (ms depuis l'heure, ask, bid, volumes)."""
    data = lzma.decompress(raw)
    out = []
    for off in range(0, len(data) - 19, 20):
        ms, ask, bid, _, _ = struct.unpack(">3i2f", data[off:off + 20])
        out.append(Tick(hour_ms + ms, bid / SCALE, ask / SCALE))
    return out


def load(folder: Path) -> list[Tick]:
    """Un fichier AAAA-MM-JJ_HH.bi5 par heure (vide si absent)."""
    out: list[Tick] = []
    for f in sorted(folder.glob("*.bi5")):
        raw = f.read_bytes()
        if not raw:
            continue
        day, hour = f.stem.split("_")
        h0 = int(datetime.fromisoformat(day).replace(hour=int(hour), tzinfo=timezone.utc).timestamp()) * 1000
        try:
            out += parse_hour(raw, h0)
        except (lzma.LZMAError, struct.error):
            continue
    return out


def candles(ticks: list[Tick], step: int) -> list[Candle]:
    out: list[Candle] = []
    for t in ticks:
        k = t.ms // 1000 // step * step
        m = t.mid
        if out and out[-1].ts == k:
            c = out[-1]
            out[-1] = Candle(k, c.open, max(c.high, m), min(c.low, m), m, c.volume + 1)
        else:
            out.append(Candle(k, m, m, m, m, 1))
    return out


class Context:
    """Tendance 5 et 15 min (mêmes règles que l'essai 18), lue sur les bougies closes à un instant donné."""

    def __init__(self, ticks: list[Tick]):
        self.f5 = e18.Frame(candles(ticks, 300), 300)
        self.f15 = e18.Frame(candles(ticks, 900), 900)
        self.p5 = self.p15 = 0

    def ok(self, now: int, d: int) -> bool:
        j5, j15 = self.f5.last_closed(now, self.p5), self.f15.last_closed(now, self.p15)
        self.p5, self.p15 = max(j5, 0), max(j15, 0)
        return j5 >= 0 and j15 >= 0 and e18._trend(self.f5, j5, d) and e18._trend(self.f15, j15, d)


def simulate(ticks: list[Tick], target: float, stop: float, dukascopy_spread: bool = False) -> list[sl.Trade]:
    ctx = Context(ticks)
    hi: deque[tuple[int, float]] = deque()
    lo: deque[tuple[int, float]] = deque()
    back = 0                                                  # premier tick des 10 dernières secondes
    out: list[sl.Trade] = []
    free_at = 0
    n = len(ticks)
    i = 0
    while i < n - 1:
        t = ticks[i]
        m = t.mid
        while hi and hi[0][0] <= t.ms - LOOKBACK_MS:
            hi.popleft()
        while lo and lo[0][0] <= t.ms - LOOKBACK_MS:
            lo.popleft()
        while back < i and ticks[back + 1].ms <= t.ms - BURST_MS:
            back += 1
        d = 0
        if t.ms >= free_at and hi and lo and ticks[back].ms <= t.ms - BURST_MS and t.ms - ticks[back].ms < 2 * BURST_MS:
            move = m - ticks[back].mid
            if m > hi[0][1] and move >= BURST_USD:
                d = 1
            elif m < lo[0][1] and -move >= BURST_USD:
                d = -1
        while hi and hi[-1][1] <= m:
            hi.pop()
        hi.append((t.ms, m))
        while lo and lo[-1][1] >= m:
            lo.pop()
        lo.append((t.ms, m))
        if d and e18.hours_ok(t.ms // 1000) and ctx.ok(t.ms // 1000, d):
            res = _trade(ticks, i + 1, d, target, stop, dukascopy_spread)
            if res is None:
                break
            out.append(res[0])
            free_at = ticks[res[1]].ms + PAUSE_MS
        i += 1
    return out


def _px(t: Tick, side: int, duka: bool) -> float:
    """Prix payé : side +1 = on achète, −1 = on vend."""
    if duka:
        return t.ask if side > 0 else t.bid
    return t.mid + side * HALF_SPREAD


def _trade(ticks: list[Tick], e: int, d: int, target: float, stop: float, duka: bool):
    entry_t = ticks[e]
    entry = _px(entry_t, d, duka)
    for j in range(e, len(ticks)):
        t = ticks[j]
        out = _px(t, -d, duka)
        pnl = d * (out - entry)
        if t.ms - entry_t.ms >= MAX_HOLD_MS or t.ms - ticks[j - 1].ms > 300_000:
            reason = "durée"
        elif pnl >= target:
            reason = "objectif"
        elif pnl <= -stop:
            reason = "stop"
        else:
            continue
        return sl.Trade(f"X{target}_S{stop}", "gold", "long" if d > 0 else "short", entry_t.ms // 1000,
                        t.ms // 1000, entry, out, stop, reason), j
    return None


def verdict(trades: list[sl.Trade]) -> dict[str, Any]:
    cost = (COMMISSION, 1.0)
    disc = sl.evaluate(trades, 0.0, cost, start_ts=SPLIT)
    conf = sl.evaluate(trades, 0.0, cost, end_ts=SPLIT)
    both = sl.evaluate(trades, 0.0, cost)
    ok_d, ok_c = sl.discovery_pass(disc), sl.confirmation_pass(conf)
    status = ("prouvé" if sl.proven(both, N_TRIALS) else "validé") if ok_d and ok_c else (
        "écarté (découverte)" if not ok_d else "écarté (confirmation)")
    days = len({datetime.fromtimestamp(t.entry_ts, timezone.utc).date() for t in trades}) or 1
    wins = sum(1 for t in trades if t.gross_points() - COMMISSION > 0)
    usd = [t.gross_points() - COMMISSION for t in trades]
    reasons: dict[str, int] = {}
    for t in trades:
        reasons[t.reason] = reasons.get(t.reason, 0) + 1
    return {"discovery": disc, "confirmation": conf, "all": both, "status": status,
            "trades_per_day": round(len(trades) / days, 1), "win_rate": round(wins / len(trades), 3) if trades else None,
            "usd_per_oz_total": round(sum(usd), 2), "usd_per_trade": round(sum(usd) / len(usd), 3) if usd else None,
            "exits": reasons}


def run(ticks: list[Tick], log: Callable[[str], None] = print) -> dict[str, Any]:
    out: dict[str, Any] = {"essai": 19, "split": "2026-09-21", "n_trials": N_TRIALS, "ticks": len(ticks),
                           "first": datetime.fromtimestamp(ticks[0].ms / 1000, timezone.utc).date().isoformat(),
                           "last": datetime.fromtimestamp(ticks[-1].ms / 1000, timezone.utc).date().isoformat(),
                           "cells": {}, "info_dukascopy_spread": {}}
    for x in TARGETS:
        for s in STOPS:
            for duka, key in ((False, "cells"), (True, "info_dukascopy_spread")):
                v = verdict(simulate(ticks, x, s, duka))
                out[key][f"X{x}_S{s}"] = v
                d, c, a = v["discovery"], v["confirmation"], v["all"]
                log(f"{'Dukascopy' if duka else 'Vantage  '} X={x} S={s} découverte n={d['n']} {d['net']['mean_r']} "
                    f"PF {d['net']['profit_factor']} moitiés {d['first_half']['mean_r']}/{d['second_half']['mean_r']} | "
                    f"confirmation n={c['n']} {c['net']['mean_r']} PF {c['net']['profit_factor']} | total {a['net']['mean_r']} "
                    f"| {v['trades_per_day']}/jour réussite {v['win_rate']} {v['usd_per_trade']} $/once/trade "
                    f"→ {v['status']}")
    return out
