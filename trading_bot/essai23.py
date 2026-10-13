"""Essai 23 (HYPOTHESES.md) : toutes nos stratégies (les 54 de l'essai 17) rejouées sur 2014-2024, années jamais
regardées. Bougies dans data/history/long/<actif>_5m.json (Dukascopy, Binance pour le Bitcoin).

    python -m trading_bot.essai23          → data/essai23.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import essai14 as e14
from . import essai15 as e15
from . import essai17 as e17
from . import strategies as sl
from .essai21 import Bars, bot_cost, judge, real_rs
from .models import Candle

ASSETS = ("gold", "nasdaq", "sp500", "bitcoin")
MIN_TRADES = 100


def load(path: Path) -> list[Candle]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [Candle(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])) for r in rows]


def verdict(trades: list[sl.Trade], cost) -> dict[str, Any]:
    trades = sorted((t for t in trades if t.reason != "fin des données" and t.risk > 0), key=lambda t: t.entry_ts)
    rs = real_rs(trades, cost) if trades else []
    n = len(trades)
    mean = float(sum(rs) / n) if n else None
    gains, losses = float(sum(x for x in rs if x > 0)), float(-sum(x for x in rs if x < 0))
    pf = gains / losses if losses > 0 else None
    years: dict[int, list[float]] = {}
    for t, r in zip(trades, rs):
        years.setdefault(datetime.fromtimestamp(t.entry_ts, timezone.utc).year, []).append(float(r))
    full = {y: v for y, v in years.items() if 2015 <= y <= 2023 or (y == 2014 and len(years) > 1)}
    by_year = {str(y): {"n": len(v), "mean_r": round(sum(v) / len(v), 4)} for y, v in sorted(years.items())}
    pos = sum(1 for v in full.values() if sum(v) > 0)
    holds = n >= MIN_TRADES and (mean or 0) > 0 and (pf or 0) >= 1.1 and bool(full) and pos >= len(full) / 2
    return {"n": n, "mean_r": None if mean is None else round(mean, 4), "profit_factor": None if pf is None else round(pf, 2),
            "years": by_year, "positive_years": f"{pos}/{len(full)}", "status": "tient" if holds else "ne tient pas"}


def run(store, cfg, root: Path, log: Callable[[str], None] = print) -> dict[str, Any]:
    from .backtest import run_backtest
    out: dict[str, Any] = {"essai": 23, "cells": {}}
    data = {k: load(p) for k in ASSETS if (p := root / "history" / "long" / f"{k}_5m.json").exists()}
    ctxs = {k: e15.Ctx(c) for k, c in data.items()}
    for key, ctx in ctxs.items():
        real = ctx.m5.c
        cost, label = bot_cost(key, cfg)
        cache = root / "history" / "long" / f"essai23_bot_{key}.json"
        if cache.exists():
            rows = json.loads(cache.read_text(encoding="utf-8"))
        else:
            rows = run_backtest(cfg.assets[key], real, cfg)["trades"]
            cache.write_text(json.dumps(rows), encoding="utf-8")
        base = e14.bot_trades(rows, key)
        other = ctxs.get({"nasdaq": "sp500", "sp500": "nasdaq"}.get(key, ""))
        bars = Bars(real)
        first = datetime.fromtimestamp(real[0].ts, timezone.utc).date().isoformat()
        for name, trades in e17.cells(key, real, real, ctx, other, base, cfg.assets[key].cost_pct):
            v = verdict(trades, cost)
            m = judge(name, key, trades, bars, cost, base)
            v.update({"idea": name, "asset": key, "fees": label, "from": first,
                      "monkeys_beaten": (m.get("all") or {}).get("beaten"),
                      "filter_monkeys_beaten": (m.get("filter_monkeys") or {}).get("beaten")})
            out["cells"][f"{name}:{key}"] = v
            log(f"{name:17s} {key:8s} n={v['n']:5d} {v['mean_r']} PF {v['profit_factor']} années + {v['positive_years']} "
                f"singes {v['monkeys_beaten']} → {v['status']}")
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .models import iso, utcnow
    eng = Engine(load_config())
    out = run(eng.store, eng.cfg, eng.store.dir, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    eng.store._write(eng.store.dir / "essai23.json", out)


if __name__ == "__main__":
    main()
