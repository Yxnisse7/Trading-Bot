"""Essai 45 (HYPOTHESES.md) : prendre un gain fixe (+0,5 R, +1 R, +1,5 R, +2 R) au lieu de la sortie actuelle.

Demandé par Yanisse le 22/10/2026 : des trades Bitcoin passés à +100 $ avant de finir au stop. Même entrée, même stop,
même sortie d'origine ; on ajoute seulement un objectif de gain fixe en R. Avec 5 % de risque sur 1 000 $ (≈ 50 $),
+100 $ ≈ +2 R. Comparaison trade par trade, mêmes contrôles que l'essai 32.

    python -m trading_bot.essai45          → data/essai45.json
"""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import NormalDist
from typing import Any

import numpy as np

from . import essai32 as e32
from . import strategies as sl
from .essai21 import bot_cost
from .signals import EXIT_OVERRIDE

STRATS = [("cassure_williams", "bitcoin"), ("donchian_1h", "bitcoin"), ("swing_w3", "bitcoin"),
          ("noise_area_v2", "nasdaq"), ("nuit_asie", "gold"), ("bot", "nasdaq")]
TARGETS = (0.5, 1.0, 1.5, 2.0)


def take(t: sl.Trade, k: float, ts, op, hi, lo) -> tuple[float, int, str]:
    """Sortie à +k R si le prix l'atteint avant la sortie d'origine (la sortie d'origine passe d'abord sur sa bougie)."""
    sign = 1 if t.direction == "long" else -1
    target = t.entry + sign * k * t.risk
    j = int(np.searchsorted(ts, t.entry_ts)) + 1
    while j < len(ts) and ts[j] < t.exit_ts:
        if (hi[j] >= target) if sign > 0 else (lo[j] <= target):
            px = max(target, op[j]) if sign > 0 else min(target, op[j])
            return float(px), int(ts[j]), "stop géré"          # nom gardé pour e32.judge (part des sorties changées)
        j += 1
    return t.exit, t.exit_ts, t.reason


def run(store, cfg, root, log=print) -> dict[str, Any]:
    out: dict[str, Any] = {"essai": 45, "targets": TARGETS, "cells": {}}
    cache: dict[str, Any] = {}
    for name, key in STRATS:
        if key not in cache:
            c = e32.candles_for(key, store, root)
            cache[key] = (c, np.array([x.ts for x in c], dtype=np.int64), np.array([x.open for x in c]),
                          np.array([x.high for x in c]), np.array([x.low for x in c]))
        candles, ts, op, hi, lo = cache[key]
        if name == "bot":
            trades = e32.bot_base(key, store, root, store.load_history(key)[0].ts)
            if key in EXIT_OVERRIDE:
                trades = e32.override(trades, candles, key)
        else:
            trades = sl.run_all(key, candles, only=[name])
        trades = sorted((t for t in trades if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
        cost, _ = bot_cost(key, cfg)
        last_year = datetime.fromtimestamp(int(ts[-1]), timezone.utc).year
        for k in TARGETS:
            managed = [take(t, k, ts, op, hi, lo) for t in trades]
            r = e32.judge(trades, managed, cost, last_year)
            r.update({"strategy": name, "asset": key, "target_r": k})
            out["cells"][f"{name}:{key}:+{k}R"] = r
            failed = [c for c, ok in r["checks"].items() if not ok]
            log(f"{name:16s} {key:7s} +{k:<3} R n={r['n']:5d} actuel {r['current_r']:+.3f} → {r['variant_r']:+.3f} R "
                f"(écart {r['diff_r']:+.3f}, z {r['z']:+.2f}, sorties avancées {r['moved_exit']:.0%}, "
                f"années {r['years_better']}) {'OK' if not failed else 'échoue : ' + ', '.join(failed)}")
    z_thr = NormalDist().inv_cdf(1 - 0.05 / len(out["cells"]))
    out["z_threshold"] = round(z_thr, 2)
    for r in out["cells"].values():
        ok = all(r["checks"].values())
        r["status"] = "prouvée" if ok and r["z"] > z_thr else "robuste" if ok else "pas mieux"
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    out = run(eng.store, eng.cfg, eng.store.dir, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    eng.store._write(eng.store.dir / "essai45.json", out)


if __name__ == "__main__":
    main()
