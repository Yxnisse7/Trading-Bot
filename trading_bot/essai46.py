"""Essai 46 (HYPOTHESES.md) : la « grille » d'une vidéo TikTok (robot dit HFT sur l'or), rejouée sur 2014-2026.

Robot : un panier d'achats et un panier de ventes tournent en même temps sur l'or. Chaque panier ajoute une position
tous les STEP $ contre lui, sans stop, et se ferme en entier quand le prix revient TP $ au-delà de son prix moyen
(donc « toujours en positif »). Compte de 1 000 $, levier 1:500, coupure du courtier à 50 % de marge, frais Vantage
RAW (0,30 $ par once aller-retour). Bougies 5 min parcourues ouverture → plus bas → plus haut → clôture (bougie
haussière) ou ouverture → plus haut → plus bas → clôture (baissière).

On lance le robot le premier lundi de chaque mois et on le suit au plus 6 mois : combien de temps avant que le compte
saute, ou avant −300 $ (la limite du démo).

    python -m trading_bot.essai46          → data/essai46.json
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np

from .essai23 import load

BALANCE = 1000.0
OZ = 100.0                 # onces par lot
LEVERAGE = 500.0
STOP_OUT = 0.5             # coupure quand fonds / marge < 50 %
COST = 0.30                # $ par once, aller-retour
STEP, TP = 3.0, 1.0
LIMIT = -300.0
HORIZON = 182 * 86400
VARIANTS = {"G1 lots fixes 0,05": (0.05, 1.0), "G2 lots ×1,5 à chaque palier (martingale)": (0.05, 1.5)}
MAX_LOT = 50.0


class Basket:
    def __init__(self, sign: int, lot0: float, mult: float):
        self.sign, self.lot0, self.mult = sign, lot0, mult
        self.pos: list[tuple[float, float]] = []          # (prix, lot)

    def lots(self) -> float:
        return sum(lot for _, lot in self.pos)

    def avg(self) -> float:
        return sum(p * lot for p, lot in self.pos) / self.lots()

    def floating(self, px: float) -> float:
        return sum((px - p) * self.sign * lot * OZ for p, lot in self.pos)

    def open(self, px: float) -> float:
        lot = min(MAX_LOT, round(self.lot0 * self.mult ** len(self.pos), 2))
        self.pos.append((px, lot))
        return COST * OZ * lot


def run_one(px_path: np.ndarray, t_path: np.ndarray, lot0: float, mult: float) -> dict[str, Any]:
    """`px_path` : suite de prix (4 par bougie) ; renvoie le parcours du compte."""
    bal = BALANCE
    baskets = [Basket(1, lot0, mult), Basket(-1, lot0, mult)]
    for b in baskets:
        bal -= b.open(px_path[0])
    t0 = t_path[0]
    hit_limit = None
    closes = 0
    for k in range(1, len(px_path)):
        px = px_path[k]
        for b in baskets:
            # ajouts : un palier tous les STEP $ contre le panier (plusieurs si le prix saute)
            last = b.pos[-1][0]
            while (last - px) * b.sign >= STEP:
                last = last - b.sign * STEP
                bal -= b.open(last)
            # fermeture du panier en gain
            if (px - b.avg()) * b.sign >= TP:
                bal += b.floating(px)
                closes += 1
                b.pos = []
                bal -= b.open(px)
        eq = bal + sum(b.floating(px) for b in baskets)
        margin = sum(b.lots() for b in baskets) * OZ * px / LEVERAGE
        if hit_limit is None and eq - BALANCE <= LIMIT:
            hit_limit = int(t_path[k] - t0)
        if eq <= 0 or eq / margin < STOP_OUT:
            return {"blown_after_days": round((t_path[k] - t0) / 86400, 1), "limit_after_days":
                    round(hit_limit / 86400, 1), "result": round(max(eq, 0.0) - BALANCE, 2), "baskets_closed": closes,
                    "max_lots": round(max(b.lots() for b in baskets), 2)}
    eq = bal + sum(b.floating(px_path[-1]) for b in baskets)
    return {"blown_after_days": None, "limit_after_days": None if hit_limit is None else round(hit_limit / 86400, 1),
            "result": round(eq - BALANCE, 2), "baskets_closed": closes,
            "max_lots": round(max(b.lots() for b in baskets), 2)}


def path(candles, i0: int, i1: int) -> tuple[np.ndarray, np.ndarray]:
    px, ts = [], []
    for c in candles[i0:i1]:
        seq = (c.open, c.low, c.high, c.close) if c.close >= c.open else (c.open, c.high, c.low, c.close)
        px += seq
        ts += [c.ts] * 4
    return np.array(px), np.array(ts)


def run(store, root, log=print) -> dict[str, Any]:
    old = load(root / "history" / "long" / "gold_5m.json")
    new = store.load_history("gold") or []
    candles = [c for c in old if not new or c.ts < new[0].ts] + new
    ts = np.array([c.ts for c in candles], dtype=np.int64)
    out: dict[str, Any] = {"essai": 46, "params": {"step": STEP, "tp": TP, "balance": BALANCE, "cost_per_oz": COST,
                                                    "leverage": LEVERAGE, "limit": LIMIT}, "cells": {}}
    starts = []
    d = datetime.fromtimestamp(int(ts[0]), timezone.utc).replace(day=1, hour=0, minute=0, second=0) + timedelta(days=32)
    end = datetime.fromtimestamp(int(ts[-1]), timezone.utc)
    while d < end - timedelta(days=30):
        first = d.replace(day=1)
        monday = first + timedelta(days=(7 - first.weekday()) % 7, hours=8)
        starts.append(monday)
        d = (first + timedelta(days=32)).replace(day=1)
    for name, (lot0, mult) in VARIANTS.items():
        runs = []
        for s in starts:
            i0 = int(np.searchsorted(ts, int(s.timestamp())))
            i1 = int(np.searchsorted(ts, int(s.timestamp()) + HORIZON))
            if i1 - i0 < 1000:
                continue
            p, t = path(candles, i0, i1)
            r = run_one(p, t, lot0, mult)
            r["start"] = s.date().isoformat()
            runs.append(r)
        blown = [r["blown_after_days"] for r in runs if r["blown_after_days"] is not None]
        limit = [r["limit_after_days"] for r in runs if r["limit_after_days"] is not None]
        cell = {
            "runs": len(runs),
            "blown_share": round(len(blown) / len(runs), 3),
            "blown_within_7_days": round(sum(1 for x in blown if x <= 7) / len(runs), 3),
            "blown_within_30_days": round(sum(1 for x in blown if x <= 30) / len(runs), 3),
            "median_days_to_blow": float(np.median(blown)) if blown else None,
            "limit_share": round(len(limit) / len(runs), 3),
            "median_days_to_limit": float(np.median(limit)) if limit else None,
            "mean_result": round(float(np.mean([r["result"] for r in runs])), 2),
            "median_result": round(float(np.median([r["result"] for r in runs])), 2),
            "survivors_mean_result": round(float(np.mean([r["result"] for r in runs if r["blown_after_days"] is None]
                                                         or [0.0])), 2),
            "runs_detail": runs,
        }
        out["cells"][name] = cell
        log(f"{name:45s} {len(runs)} départs · compte sauté {cell['blown_share']:.0%} (en 7 j {cell['blown_within_7_days']:.0%}, "
            f"en 30 j {cell['blown_within_30_days']:.0%}, médiane {cell['median_days_to_blow']} j) · −300 $ atteint "
            f"{cell['limit_share']:.0%} (médiane {cell['median_days_to_limit']} j) · résultat moyen {cell['mean_result']} $, "
            f"médian {cell['median_result']} $, survivants {cell['survivors_mean_result']} $")
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    out = run(eng.store, eng.store.dir, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    eng.store._write(eng.store.dir / "essai46.json", out)


if __name__ == "__main__":
    main()
