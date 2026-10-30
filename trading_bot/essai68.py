"""Essai 68 (HYPOTHESES.md) : la nuit asiatique sur l'or, sautée après une forte baisse.

    python -m trading_bot.essai68          → data/essai68.json

Données hors dépôt : data/history/long/gold_5m.json (HistData 2014 → 09/2024), puis data/candles/gold_5m.json.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import numpy as np

from .config import DATA_DIR
from .essai23 import load
from .essai33 import z_threshold
from .essai65 import daily_closes, judge, rows


def add_moves(base: list[dict[str, Any]], candles) -> None:
    closes = daily_closes(candles)
    days = sorted(closes)
    idx = {d: i for i, d in enumerate(days)}
    for x in base:
        i = idx[x["d"]]
        cl = [closes[d] for d in days[i - 21:i + 1]]
        ch = np.diff(cl) / np.array(cl[:-1])
        x["day"] = float(ch[-1])
        x["w5"] = cl[-1] / cl[-6] - 1
        x["vol20"] = float(np.mean(np.abs(ch[:-1])))


def main() -> None:
    long = load(Path(DATA_DIR) / "history" / "long" / "gold_5m.json")
    new = load(Path(DATA_DIR) / "candles" / "gold_5m.json")
    candles = [c for c in long if c.ts < new[0].ts] + new
    base = rows(candles)
    add_moves(base, candles)
    rng = random.Random(68)
    cells = {
        "N0 toutes les nuits": lambda x: True,
        "D1 sauter si jour <= -1 %": lambda x: x["day"] > -0.01,
        "D2 sauter si jour <= -2 %": lambda x: x["day"] > -0.02,
        "W1 sauter si 5 jours <= -3 %": lambda x: x["w5"] > -0.03,
        "W2 sauter si 5 jours <= -5 %": lambda x: x["w5"] > -0.05,
        "V1 sauter si jour <= -2 x moyenne 20 j": lambda x: x["day"] > -2 * x["vol20"],
    }
    res: dict[str, Any] = {"essai": 68, "z_threshold": round(z_threshold(5), 2),
                           "first": str(base[0]["d"]), "last": str(base[-1]["d"]), "cells": {}}
    for name, key in cells.items():
        c = judge(base, key, rng)
        skipped = [x for x in base if not key(x)]
        c["skipped"] = len(skipped)
        c["skipped_2020"] = round(float(np.mean([x["r"] for x in skipped if x["ts"] >= 1577836800])), 4) \
            if any(x["ts"] >= 1577836800 for x in skipped) else None
        c["passe"] = bool(c["kept"] < c["n"] and c["kept_2014_2019"] > c["base_2014_2019"]
                          and c["kept_2020"] > c["base_2020"] and (c["skipped_r"] or 0) < 0
                          and c["random_beaten"] >= 950)
        res["cells"][name] = c
        print(f"{name:40s} sautées {c['skipped']:4d} (R {c['skipped_r']}) gardées R {c['mean_r']:+.4f} "
              f"(toutes {c['base_r']:+.4f}) 14-19 {c['kept_2014_2019']:+.4f}/{c['base_2014_2019']:+.4f} "
              f"20+ {c['kept_2020']:+.4f}/{c['base_2020']:+.4f} hasard {c['random_beaten']} → {'PASSE' if c['passe'] else 'non'}")
    (Path(DATA_DIR) / "essai68.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str),
                                                  encoding="utf-8")


if __name__ == "__main__":
    main()
