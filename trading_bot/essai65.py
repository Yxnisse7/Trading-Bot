"""Essai 65 (HYPOTHESES.md) : la nuit asiatique sur l'or, filtrée par la tendance ou par les annonces.

    python -m trading_bot.essai65          → data/essai65.json

Données hors dépôt : data/history/long/gold_5m.json (HistData 2014 → 09/2024), puis data/candles/gold_5m.json.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

from . import strategies as sl
from .config import DATA_DIR
from .essai23 import load
from .essai33 import z_threshold

FEE = 0.30                      # $ l'once aller-retour
HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
NEWS_END = datetime(2024, 9, 20).date()
N_RANDOM = 1000


def daily_closes(candles) -> dict:
    """Clôture de chaque séance (dernière bougie avant 17:00 New York), indexée par la date New York."""
    out = {}
    for c in candles:
        t = datetime.fromtimestamp(c.ts, sl.NY)
        if t.hour < 17:
            out[t.date()] = c.close
    return out


def news_days() -> set:
    ev = json.loads((Path(DATA_DIR) / "macro_events_2010_2024.json").read_text(encoding="utf-8"))
    return {datetime.fromisoformat(d).date() for k in ("nfp", "cpi", "fomc") for d in ev[k]}


def rows(candles) -> list[dict[str, Any]]:
    trades = [t for t in sl.nuit_asie(sl._Series(candles), "gold") if t.reason != "fin des données"]
    closes = daily_closes(candles)
    days = sorted(closes)
    idx = {d: i for i, d in enumerate(days)}
    news = news_days()
    out = []
    for t in trades:
        d = datetime.fromtimestamp(t.entry_ts, sl.NY).date()
        if d not in idx or idx[d] < 50:
            continue
        i = idx[d]                                    # clôture de 17:00 du jour d'entrée (l'entrée est à 18:00)
        cl = [closes[x] for x in days[i - 50:i + 1]]
        last = cl[-1]
        r = (t.exit - t.entry - FEE) / t.risk
        out.append({"ts": t.entry_ts, "d": d, "r": r,
                    "T1": last > np.mean(cl[-20:]), "T2": last > np.mean(cl[-50:]),
                    "T3": last > cl[-2], "T4": last > cl[-6],
                    "A1": d not in news, "A2": (d + timedelta(days=1)) not in news,
                    "news_ok": d <= NEWS_END})
    return out


def judge(base: list[dict], key, rng: random.Random) -> dict[str, Any]:
    keep = [x for x in base if key(x)]
    rs = np.array([x["r"] for x in base]); kr = np.array([x["r"] for x in keep])
    n, k = len(base), len(keep)
    half = lambda xs, early: [x["r"] for x in xs if (x["ts"] < HALF) == early]
    m = lambda a: float(np.mean(a)) if len(a) else None
    rand = [float(np.mean(rng.sample(list(rs), k))) for _ in range(N_RANDOM)] if 0 < k < n else []
    beaten = sum(m(kr) > x for x in rand)
    z = (m(kr) - float(np.mean(rand))) / (float(np.std(rand)) or 1) if rand else None
    years: dict[int, list[float]] = {}
    for x in keep:
        years.setdefault(datetime.fromtimestamp(x["ts"], timezone.utc).year, []).append(x["r"])
    res = {"n": n, "kept": k, "mean_r": round(m(kr), 4), "base_r": round(m(rs), 4),
           "kept_2014_2019": round(m(half(keep, True)), 4), "base_2014_2019": round(m(half(base, True)), 4),
           "kept_2020": round(m(half(keep, False)), 4), "base_2020": round(m(half(base, False)), 4),
           "skipped_r": round(m([x["r"] for x in base if not key(x)]), 4) if k < n else None,
           "random_beaten": beaten, "z": round(z, 2) if z is not None else None,
           "years": {y: round(float(np.mean(v)), 3) for y, v in sorted(years.items())}}
    res["passe"] = bool(k >= 200 and res["mean_r"] > res["base_r"] and res["kept_2014_2019"] > res["base_2014_2019"]
                        and res["kept_2020"] > res["base_2020"] and beaten >= 950)
    return res


def main() -> None:
    long = load(Path(DATA_DIR) / "history" / "long" / "gold_5m.json")
    new = load(Path(DATA_DIR) / "candles" / "gold_5m.json")
    candles = [c for c in long if c.ts < new[0].ts] + new
    base = rows(candles)
    rng = random.Random(65)
    news_base = [x for x in base if x["news_ok"]]
    cells = {
        "N0 toutes les nuits": (base, lambda x: True),
        "T1 au-dessus moyenne 20 j": (base, lambda x: x["T1"]),
        "T2 au-dessus moyenne 50 j": (base, lambda x: x["T2"]),
        "T3 veille en hausse": (base, lambda x: x["T3"]),
        "T4 au-dessus d'il y a 5 j": (base, lambda x: x["T4"]),
        "A1 pas la nuit après une annonce": (news_base, lambda x: x["A1"]),
        "A2 pas la nuit avant une annonce": (news_base, lambda x: x["A2"]),
        "C1 T1 + A1": (news_base, lambda x: x["T1"] and x["A1"]),
    }
    res: dict[str, Any] = {"essai": 65, "fee_usd_oz": FEE, "z_threshold": round(z_threshold(7), 2),
                           "first": str(base[0]["d"]), "last": str(base[-1]["d"]), "cells": {}}
    for name, (b, key) in cells.items():
        res["cells"][name] = judge(b, key, rng)
        c = res["cells"][name]
        print(f"{name:34s} gardées {c['kept']:4d}/{c['n']} R {c['mean_r']:+.4f} (toutes {c['base_r']:+.4f}) "
              f"14-19 {c['kept_2014_2019']:+.4f}/{c['base_2014_2019']:+.4f} 20+ {c['kept_2020']:+.4f}/{c['base_2020']:+.4f} "
              f"sautées {c['skipped_r']} hasard {c['random_beaten']} z {c['z']} → {'PASSE' if c['passe'] else 'non'}")
    (Path(DATA_DIR) / "essai65.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str),
                                                  encoding="utf-8")


if __name__ == "__main__":
    main()
