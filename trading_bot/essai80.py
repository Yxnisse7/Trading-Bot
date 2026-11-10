"""Essai 80 (HYPOTHESES.md) : règles de gestion propres aux challenges de prop firm (10/11/2026), 15 cellules.

Panier joué seulement dans la journée (compatible Topstep) : zone de bruit v2 Nasdaq + L1 effet du déjeuner S&P 500 et
Nasdaq (essai 79), plus les cellules des essais 78-79 jouées dans la journée qui passent (aucune au 10/11 : voir
data/essai78.json et data/essai79.json). Règles M0-M4 × 100/200/300 $ par R ; simulation Topstep 50K de l'essai 76.

    python -m trading_bot.essai80          → data/essai80.json   (après essai79, qui écrit essai79_trades.pkl)
"""
from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from . import essai78 as e78
from . import strategies as sl
from .config import DATA_DIR
from .essai76 import day_of, funded_topstep, mondays, run_topstep, summarize
from .essai79 import TRADES as T79

UTC = timezone.utc
OUT = Path(DATA_DIR) / "essai80.json"
CAP, TARGET, MLL, FEE = 50_000, 3_000, 2_000, 49
RULES = ("M0", "M1", "M2", "M3", "M4")
BUDGETS = (100, 200, 300)


def basket() -> list[dict[str, Any]]:
    rows = []
    b = e78.bars5("nasdaq")
    for t in sl.noise_area_v2(sl._Series(e78.candles(b)), "nasdaq"):
        if t.reason != "fin des données" and t.risk > 0:
            rows.append({"strat": "zone_v2", "ts": t.entry_ts, "exit_ts": t.exit_ts,
                         "r": (t.gross_points() - e78.cost("nasdaq", t.entry)) / t.risk})
    saved = pickle.load(T79.open("rb"))
    for key in ("L1_sp500", "L1_nasdaq"):
        asset = key.split("_")[1]
        for t in saved[key]:
            rows.append({"strat": key, "ts": t["entry_ts"], "exit_ts": t["exit_ts"],
                         "r": ((t["exit"] - t["entry"]) * (1 if t["direction"] == "long" else -1)
                               - e78.cost(asset, t["entry"])) / t["risk"]})
    return sorted(rows, key=lambda x: x["ts"])


def take(rows: list[dict], rule: str) -> list[dict]:
    """Applique la règle de gestion jour par jour (jour de séance Topstep) ; un trade à la fois par stratégie."""
    out, busy = [], {}
    by_day: dict = {}
    for t in rows:
        by_day.setdefault(day_of(t["ts"]), []).append(t)
    for d in sorted(by_day):
        taken: list[dict] = []
        for t in by_day[d]:
            if busy.get(t["strat"], 0) > t["ts"]:
                continue
            done = sum(x["r"] for x in taken if x["exit_ts"] <= t["ts"])
            if rule in ("M1", "M3") and done <= -1:
                continue
            if rule in ("M2", "M3") and done >= 1:
                continue
            if rule == "M4" and taken:
                continue
            taken.append(t)
            busy[t["strat"]] = t["exit_ts"]
        out += taken
    return out


def run() -> dict[str, Any]:
    rows = basket()
    out: dict[str, Any] = {"essai": 80, "panier": {}, "cellules": {}}
    for s in sorted({r["strat"] for r in rows}):
        rs = np.array([r["r"] for r in rows if r["strat"] == s])
        out["panier"][s] = {"n": len(rs), "R": round(float(rs.mean()), 4)}
    starts = mondays()
    for rule in RULES:
        tr = take(rows, rule)
        rs = np.array([t["r"] for t in tr])
        for budget in BUDGETS:
            agg: dict = {}
            for t in tr:
                d = day_of(t["exit_ts"])
                agg[d] = agg.get(d, 0.0) + t["r"] * budget
            days = sorted(agg.items())
            results = []
            for s in starts:
                r = run_topstep(days, s, CAP, TARGET, MLL)
                f = funded_topstep(days, r["end"], CAP, MLL) if r["ok"] else None
                results.append((s, r, f))
            row = summarize(results, lambda r: FEE * (r["days"] // 30 + 1))
            row.update({"trades": len(rs), "R_moyen": round(float(rs.mean()), 4),
                        "pire_jour_R": round(min(agg.values()) / budget, 2)})
            out["cellules"][f"{rule} | {budget} $/R"] = row
            print(rule, budget, row["réussite"], row["réussite_2014_2019"], row["réussite_2020_2025"],
                  row["jouable"], flush=True)
    out["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    run()
