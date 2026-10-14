"""Essai 32 (HYPOTHESES.md) : réajuster le stop pendant le trade, sur les stratégies qui tournent en réel (2014-2026).

Même entrée et même sortie d'origine ; un stop de gestion est ajouté par-dessus, déplacé à la clôture de chaque
bougie 5 min (resserré seulement). On compare trade par trade avec la version actuelle.

    python -m trading_bot.essai32          → data/essai32.json
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from statistics import NormalDist
from typing import Any

import numpy as np

from . import essai14 as e14
from . import strategies as sl
from .essai21 import bot_cost
from .essai23 import load
from .signals import EXIT_OVERRIDE

HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
RECENT = int(datetime(2024, 10, 14, tzinfo=timezone.utc).timestamp())
STRATS = [("noise_area", "nasdaq"), ("noise_area_v2", "nasdaq"), ("donchian_1h", "bitcoin"), ("swing_w3", "bitcoin"),
          ("cassure_williams", "bitcoin"), ("nuit_asie", "gold"), ("bot", "gold"), ("bot", "nasdaq")]
VARIANTS = {"A": "stop à l'entrée dès +1 R", "B": "stop à l'entrée dès +0,5 R",
            "C": "stop suiveur à 1 R du meilleur prix", "D": "stop à +1 R dès +2 R"}


def new_stop(v: str, entry: float, risk: float, sign: int, fav: float) -> float | None:
    """Stop de gestion (prix) après une bougie, `fav` = meilleur gain atteint en points ; None = pas encore."""
    if v == "A":
        return entry if fav >= risk else None
    if v == "B":
        return entry if fav >= 0.5 * risk else None
    if v == "C":
        return entry + sign * (fav - risk)
    if v == "D":
        return entry + sign * risk if fav >= 2 * risk else None
    raise ValueError(v)


def manage(t: sl.Trade, v: str, ts, op, hi, lo) -> tuple[float, int, str]:
    """(prix de sortie, horodatage, raison) avec le stop de gestion `v` posé sur le trade d'origine."""
    sign = 1 if t.direction == "long" else -1
    j = int(np.searchsorted(ts, t.entry_ts)) + 1
    stop, best = None, -math.inf
    while j < len(ts) and ts[j] <= t.exit_ts:
        last = ts[j] == t.exit_ts
        if last and t.exit == op[j]:                     # sortie d'origine à l'ouverture : elle passe d'abord
            break
        if stop is not None and ((lo[j] <= stop) if sign > 0 else (hi[j] >= stop)):
            px = min(stop, op[j]) if sign > 0 else max(stop, op[j])
            return float(px), int(ts[j]), "stop géré"
        if last:
            break
        best = max(best, (hi[j] - t.entry) if sign > 0 else (t.entry - lo[j]))
        s = new_stop(v, t.entry, t.risk, sign, best)
        if s is not None:
            stop = s if stop is None else (max(stop, s) if sign > 0 else min(stop, s))
        j += 1
    return t.exit, t.exit_ts, t.reason


def candles_for(key: str, store, root):
    old = load(root / "history" / "long" / f"{key}_5m.json")
    new = store.load_history(key)
    return [c for c in old if c.ts < new[0].ts] + new


def bot_base(key: str, store, root, new_start: int) -> list[sl.Trade]:
    rows = json.loads((root / "history" / "long" / f"essai23_bot_{key}.json").read_text(encoding="utf-8"))
    start = datetime.fromtimestamp(new_start, timezone.utc).isoformat().replace("+00:00", "Z")
    rows = [r for r in rows if r["created_at"] < start]
    rows += store._read(root / "history" / f"essai14_bot_{key}.json", None) or []
    return sorted(e14.bot_trades(rows, key), key=lambda t: t.entry_ts)


def override(trades: list[sl.Trade], candles, key: str) -> list[sl.Trade]:
    """Bot classique Nasdaq tel qu'en réel : stop × 1,5, objectif 3 fois ce stop, 24 h au plus (essai 29)."""
    sx, tx, minutes = EXIT_OVERRIDE[key]
    ts = [c.ts for c in candles]
    out = []
    for t in trades:
        i0 = int(np.searchsorted(ts, t.entry_ts))
        if i0 < 1 or i0 >= len(ts) - 1:
            continue
        sign = 1 if t.direction == "long" else -1
        risk = t.risk * sx
        px, j, why = sl.simulate(candles, i0 - 1, t.direction, t.entry, t.entry - sign * risk,
                                 target=t.entry + sign * risk * tx, exit_ts=t.entry_ts + minutes * 60)
        why = {"stop": "stop", "objectif": "objectif", "heure": "heure"}.get(why, why)
        out.append(sl.Trade("bot", key, t.direction, t.entry_ts, candles[j].ts, t.entry, px, risk, why))
    return out


def judge(base: list[sl.Trade], managed: list[tuple[float, int, str]], cost, last_year: int) -> dict[str, Any]:
    r0 = np.array([(t.gross_points() - cost(t.entry)) / t.risk for t in base])
    r1 = np.array([((px - t.entry) * (1 if t.direction == "long" else -1) - cost(t.entry)) / t.risk
                   for t, (px, _, _) in zip(base, managed)])
    d = r1 - r0
    ets = np.array([t.entry_ts for t in base])
    years: dict[int, list[float]] = {}
    for t, x in zip(ets, d):
        years.setdefault(datetime.fromtimestamp(int(t), timezone.utc).year, []).append(float(x))
    full = {y: v for y, v in years.items() if y < last_year}
    pos = sum(1 for v in full.values() if sum(v) > 0)
    m = lambda a, sel: round(float(a[sel].mean()), 4) if sel.any() else None  # noqa: E731
    sd = float(d.std(ddof=1)) if len(d) > 1 else 0.0
    z = float(d.mean()) / (sd / math.sqrt(len(d))) if sd > 0 else 0.0
    v = {"n": len(d), "current_r": round(float(r0.mean()), 4), "variant_r": round(float(r1.mean()), 4),
         "diff_r": round(float(d.mean()), 4), "z": round(z, 2),
         "moved_exit": round(sum(1 for x in managed if x[2] == "stop géré") / len(d), 3),
         "diff_before_2020": m(d, ets < HALF), "diff_since_2020": m(d, ets >= HALF),
         "diff_last_2_years": m(d, ets >= RECENT), "years_better": f"{pos}/{len(full)}",
         "years": {str(y): round(sum(x) / len(x), 4) for y, x in sorted(years.items())}}
    v["checks"] = {"écart > 0": v["diff_r"] > 0,
                   "deux moitiés": (v["diff_before_2020"] or 0) > 0 and (v["diff_since_2020"] or 0) > 0,
                   "2 dernières années": (v["diff_last_2_years"] or 0) > 0,
                   "60 % des années": pos >= 0.6 * len(full),
                   "variante R > 0": v["variant_r"] > 0}
    return v


def run(store, cfg, root, log=print) -> dict[str, Any]:
    out: dict[str, Any] = {"essai": 32, "variants": VARIANTS, "cells": {}}
    cache: dict[str, Any] = {}
    for name, key in STRATS:
        if key not in cache:
            c = candles_for(key, store, root)
            cache[key] = (c, np.array([x.ts for x in c], dtype=np.int64), np.array([x.open for x in c]),
                          np.array([x.high for x in c]), np.array([x.low for x in c]))
        candles, ts, op, hi, lo = cache[key]
        if name == "bot":
            new_start = store.load_history(key)[0].ts
            trades = bot_base(key, store, root, new_start)
            if key in EXIT_OVERRIDE:
                trades = override(trades, candles, key)
        else:
            trades = sl.run_all(key, candles, only=[name])
        trades = sorted((t for t in trades if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
        cost, _ = bot_cost(key, cfg)
        last_year = datetime.fromtimestamp(int(ts[-1]), timezone.utc).year
        for v in VARIANTS:
            managed = [manage(t, v, ts, op, hi, lo) for t in trades]
            r = judge(trades, managed, cost, last_year)
            r.update({"strategy": name, "asset": key, "variant": v})
            out["cells"][f"{name}:{key}:{v}"] = r
            failed = [c for c, ok in r["checks"].items() if not ok]
            log(f"{name:16s} {key:7s} {v} n={r['n']:5d} actuel {r['current_r']:+.3f} → {r['variant_r']:+.3f} R "
                f"(écart {r['diff_r']:+.3f}, z {r['z']:+.2f}, sorties avancées {r['moved_exit']:.0%}, "
                f"années {r['years_better']}, récent {r['diff_last_2_years']}) "
                f"{'OK' if not failed else 'échoue : ' + ', '.join(failed)}")
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
    print(f"seuil z {out['z_threshold']}")
    for k, v in out["cells"].items():
        if v["status"] != "pas mieux":
            print(f"{k:32s} {v['status']}", flush=True)
    eng.store._write(eng.store.dir / "essai32.json", out)


if __name__ == "__main__":
    main()
