"""Essai 43 (HYPOTHESES.md) : le bot classique tenu plus longtemps, sur tous les marchés (demandé par Yanisse le 21/10/2026).

Jusqu'ici le bot n'était jugé que sur 1 h. L'essai 42 a montré que, tenu jusqu'à 24 h, il tient sur le Nasdaq. Ici, pour
chaque marché 2014-2026 :
1. on calcule une fois toutes les entrées possibles du bot (analyse à chaque quart d'heure de sa plage horaire) ;
2. pour chaque façon de sortir, on rejoue comme en réel : un seul signal ouvert, règles de la journée, refroidissement
   compté depuis la clôture, stop sauté par un trou compté au vrai prix.

    python -m trading_bot.essai43 gold     → data/essai43_gold.json (un marché ; à lancer en parallèle)
    python -m trading_bot.essai43 all      → data/essai43.json (assemble les marchés, seuil z corrigé)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable
from zoneinfo import ZoneInfo

import numpy as np

from . import essai24 as e24
from . import signals
from . import strategies as sl
from .essai21 import Bars, bot_cost, judge
from .essai23 import load

PARIS = ZoneInfo("Europe/Paris")
MARKETS = ("nasdaq", "gold", "sp500", "bitcoin", "oil", "euro")
TOPSTEP_CLOSE = time(22, 10)          # 15h10 heure de Chicago : tout doit être fermé sur Topstep
DAY = 86400
VARIANTS = {
    "V0 sorties du bot, 1 h": (None, None, "bot"),
    "V1 sorties du bot, jusqu'à la fermeture Topstep": (None, None, "topstep"),
    "V2 sorties du bot, 24 h (MT5)": (None, None, "24h"),
    "V3 stop ×1,5 objectif 3, jusqu'à la fermeture Topstep": (1.5, 3.0, "topstep"),
    "V4 stop ×1,5 objectif 3, 24 h (MT5)": (1.5, 3.0, "24h"),
}


def candles_of(store, root: Path, key: str):
    old = load(root / "history" / "long" / f"{key}_5m.json")
    new = store.load_history(key) or []
    return [c for c in old if not new or c.ts < new[0].ts] + new


def candidates(cfg, candles, root: Path, key: str, log: Callable[[str], None], step: int = 3, warmup: int = 300,
               lookback: int = 1440) -> list[list[Any]]:
    """Toutes les entrées que le bot proposerait, sans la politique : [indice, émis, sens, entrée, stop, objectif, fin]."""
    from .analysis import assess
    from .models import parse_iso
    cache = root / "history" / "long" / f"essai43_cand_{key}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    asset = cfg.assets[key]
    saved, signals.EXIT_OVERRIDE = signals.EXIT_OVERRIDE, {}
    out = []
    try:
        for i in range(warmup, len(candles) - 12, step):
            now = datetime.fromtimestamp(candles[i].ts + 300, tz=timezone.utc)
            if asset.session_utc and not (asset.session_utc[0] <= now.hour < asset.session_utc[1]):
                continue
            a = assess(asset, candles[max(0, i + 1 - lookback): i + 1], cfg, None, base_minutes=5)
            if cfg.long_only and a.direction == "short":
                continue
            sig, _ = signals.build_signal(asset, a, cfg, "essai 43", now, simulate=True)
            if sig is not None:
                out.append([i, int(now.timestamp()), sig.direction, sig.entry, sig.stop_loss, sig.take_profit,
                            int(parse_iso(sig.expires_at).timestamp())])
            if i % 30000 < step:
                log(f"{key} : {i}/{len(candles)} bougies, {len(out)} entrées possibles")
    finally:
        signals.EXIT_OVERRIDE = saved
    cache.write_text(json.dumps(out), encoding="utf-8")
    return out


def end_of(created: int, mode: str, bot_end: int) -> int | None:
    if mode == "bot":
        return bot_end
    if mode == "24h":
        return created + DAY
    p = datetime.fromtimestamp(created, PARIS)
    if p.weekday() >= 5 or p.time() >= TOPSTEP_CLOSE:
        return None                                   # Topstep fermé à cette heure-là
    close = int(datetime.combine(p.date(), TOPSTEP_CLOSE, PARIS).timestamp())
    return min(close, created + DAY)


class Path5:
    def __init__(self, candles):
        self.ts = np.array([c.ts for c in candles], dtype=np.int64)
        self.op = np.array([c.open for c in candles])
        self.hi = np.array([c.high for c in candles])
        self.lo = np.array([c.low for c in candles])
        self.cl = np.array([c.close for c in candles])


def exit_of(p: Path5, i: int, s: int, stop: float, tp: float, end: int) -> tuple[int, float, str]:
    """(indice de sortie, prix, raison) ; niveau sauté par un trou exécuté à l'ouverture."""
    a = i + 1
    b = max(a + 1, int(np.searchsorted(p.ts, end)))
    b = min(b, len(p.ts))
    gaps = np.flatnonzero(np.diff(p.ts[a - 1:b]) > 4 * DAY)
    if len(gaps):
        b = a + int(gaps[0])
    lo, hi, op = p.lo[a:b], p.hi[a:b], p.op[a:b]
    hit_sl = np.flatnonzero(lo <= stop) if s > 0 else np.flatnonzero(hi >= stop)
    hit_tp = np.flatnonzero(hi >= tp) if s > 0 else np.flatnonzero(lo <= tp)
    k_sl = int(hit_sl[0]) if len(hit_sl) else None
    k_tp = int(hit_tp[0]) if len(hit_tp) else None
    if k_sl is not None and (k_tp is None or k_sl <= k_tp):
        return a + k_sl, float(min(stop, op[k_sl]) if s > 0 else max(stop, op[k_sl])), "sl"
    if k_tp is not None:
        return a + k_tp, float(max(tp, op[k_tp]) if s > 0 else min(tp, op[k_tp])), "tp"
    j = max(a, b - 1)
    return j, float(p.cl[j]), "expired"


def replay(cfg, key: str, p: Path5, cands: list[list[Any]], variant: tuple) -> list[sl.Trade]:
    from .backtest import _policy_allows
    stop_x, target_x, mode = variant
    asset = cfg.assets[key]
    past: list[tuple[int, int, str, str]] = []
    out = []
    for i, created, direction, entry, stop, tp, bot_end in cands:
        end = end_of(created, mode, bot_end)
        if end is None or end <= created:
            continue
        now = datetime.fromtimestamp(created, timezone.utc)
        if not _policy_allows(asset, past, now, cfg, 5, direction):
            continue
        s = 1 if direction == "long" else -1
        if stop_x:
            dist = abs(entry - stop) * stop_x
            stop, tp = entry - s * dist, entry + s * dist * target_x
        j, px, why = exit_of(p, i, s, stop, tp, end)
        closed = int(p.ts[j]) + 300
        past.append((created, closed, why, direction))
        out.append(sl.Trade("bot", key, direction, created, closed, float(entry), px, abs(entry - stop), why))
    return out


def run_market(store, cfg, root: Path, key: str, log: Callable[[str], None] = print) -> dict[str, Any]:
    candles = candles_of(store, root, key)
    cands = candidates(cfg, candles, root, key, log)
    p = Path5(candles)
    cost, label = bot_cost(key, cfg)
    closes = {}
    for c in candles:
        closes[datetime.fromtimestamp(c.ts, sl.NY).date()] = c.close
    keys = sorted(closes)
    last_year = datetime.fromtimestamp(candles[-1].ts, timezone.utc).year
    bars = Bars(candles)
    out: dict[str, Any] = {"essai": 43, "asset": key, "fees": label, "n_candidates": len(cands), "cells": {}}
    for name, variant in VARIANTS.items():
        trades = [t for t in replay(cfg, key, p, cands, variant) if t.risk > 0]
        v = e24.checks(trades, cost, keys, [closes[k] for k in keys], last_year)
        m = judge(f"essai43_{key}_{name[:2]}", key, trades, bars, cost) if len(trades) >= 30 else {}
        a = m.get("all") or {}
        v["monkeys"] = {"beaten": a.get("beaten"), "z": a.get("z")}
        v["checks"]["singes"] = (a.get("beaten") or 0) >= 950
        v["robust"] = all(v["checks"].values())
        v["mean_minutes"] = round(float(np.mean([(t.exit_ts - t.entry_ts) / 60 for t in trades])), 1) if trades else None
        out["cells"][name] = v
        failed = [k for k, ok in v["checks"].items() if not ok]
        log(f"{key:8s} {name:55s} n={v['n']:5d} {v['mean_r']} R PF {v['profit_factor']} années {v['positive_years']} "
            f"durée {v['mean_minutes']} min singes {a.get('beaten')} z {a.get('z')} → "
            f"{'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")
    return out


def assemble(root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"essai": 43, "markets": {}}
    for key in MARKETS:
        f = root / f"essai43_{key}.json"
        if f.exists():
            out["markets"][key] = json.loads(f.read_text(encoding="utf-8"))
    n = sum(len(m["cells"]) for m in out["markets"].values())
    z_thr = NormalDist().inv_cdf(1 - 0.05 / max(1, n))
    out["z_threshold"] = round(z_thr, 2)
    for m in out["markets"].values():
        for v in m["cells"].values():
            v["status"] = ("prouvée" if v["robust"] and (v["monkeys"]["z"] or 0) > z_thr
                           else "robuste" if v["robust"] else "pas robuste")
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "all":
        out = assemble(eng.store.dir)
        for key, m in out["markets"].items():
            for k, v in m["cells"].items():
                print(f"{key:8s} {k:55s} {v['mean_r']} R n={v['n']} {v['status']}", flush=True)
        name = "essai43.json"
    else:
        out = run_market(eng.store, eng.cfg, eng.store.dir, arg, log=lambda s: print(s, flush=True))
        name = f"essai43_{arg}.json"
    out["updated_at"] = iso(utcnow())
    eng.store._write(eng.store.dir / name, out)


if __name__ == "__main__":
    main()
