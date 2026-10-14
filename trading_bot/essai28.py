"""Essai 28 (HYPOTHESES.md) : d'autres stratégies courtes sur l'or, trouvées par une recherche large.

    python -m trading_bot.essai28          → data/essai28.json
"""
from __future__ import annotations

import json
import zlib
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Callable
from zoneinfo import ZoneInfo

import numpy as np

from . import macro_history
from . import strategies as sl

FEE = 0.30
HALF = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
RECENT = int(datetime(2024, 10, 14, tzinfo=timezone.utc).timestamp())
N_MONKEYS = 1000
MIN_TRADES = 100
LONDON = ZoneInfo("Europe/London")
C_STOP, C_TARGET = 0.9, 0.8          # % du prix


class Bars:
    def __init__(self, candles):
        self.ts = np.array([c.ts for c in candles], dtype=np.int64)
        self.op = np.array([c.open for c in candles])
        self.hi = np.array([c.high for c in candles])
        self.lo = np.array([c.low for c in candles])
        self.cl = np.array([c.close for c in candles])
        self.days = sorted({datetime.fromtimestamp(int(t), sl.NY).date() for t in self.ts[::12]})

    def at(self, t: int) -> int | None:
        i = int(np.searchsorted(self.ts, t))
        return i if i < len(self.ts) and self.ts[i] - t <= 1800 else None

    def span(self, t0: int, t1: int) -> tuple[int, int]:
        return int(np.searchsorted(self.ts, t0)), int(np.searchsorted(self.ts, t1))


def _ts(d: date, hh: int, mm: int, tz=sl.NY) -> int:
    return int(datetime.combine(d, time(hh, mm), tz).timestamp())


Trade = tuple[int, int, float, int]          # indice d'entrée (à l'ouverture), indice de sortie, prix de sortie, sens


def timed(b: Bars, hin, hout, sign: int, tz=sl.NY, days=None) -> list[Trade]:
    out = []
    for d in days if days is not None else b.days:
        if d.weekday() > 4:
            continue
        a, z = b.at(_ts(d, *hin, tz)), b.at(_ts(d, *hout, tz))
        if a is not None and z is not None and z > a:
            out.append((a, z, float(b.op[z]), sign))
    return out


def false_break(b: Bars, side: int) -> list[Trade]:
    """C1 (side=1) : passe sous le plus bas de la séance d'avant puis clôture au-dessus → achat. C2 (side=-1) : miroir."""
    out = []
    prev = None
    for d in b.days:
        if d.weekday() > 4:
            continue
        s0, s1 = b.span(_ts(d - timedelta(days=1), 18, 0), _ts(d, 17, 0))
        if s1 - s0 < 100:
            prev = None
            continue
        if prev is not None:
            ph, pl = prev
            last_entry, flat = _ts(d, 16, 0), b.at(_ts(d, 16, 55))
            for k in range(s0, s1 - 1):
                if b.ts[k] >= last_entry or flat is None:
                    break
                hit = (b.lo[k] < pl < b.cl[k]) if side == 1 else (b.hi[k] > ph > b.cl[k])
                if not hit:
                    continue
                ia = k + 1
                e = b.op[ia]
                stop = e * (1 - side * C_STOP / 100)
                tgt = e * (1 + side * C_TARGET / 100)
                px, ib = float(b.op[flat]), flat
                for j in range(ia, flat):
                    if (b.lo[j] <= stop) if side == 1 else (b.hi[j] >= stop):
                        px, ib = stop, j
                        break
                    if (b.hi[j] >= tgt) if side == 1 else (b.lo[j] <= tgt):
                        px, ib = tgt, j
                        break
                if ib > ia:
                    out.append((ia, ib, px, side))
                break
        prev = (float(b.hi[s0:s1].max()), float(b.lo[s0:s1].min()))
    return out


def event_trades(b: Bars, dates: list[str], hev, hin, hout, follow: bool) -> list[Trade]:
    """Entrée à hin dans le sens (follow) ou contre le sens du mouvement depuis l'annonce (hev) ; sortie à hout."""
    out = []
    for s in dates:
        d = date.fromisoformat(s)
        ev, a, z = b.at(_ts(d, *hev)), b.at(_ts(d, *hin)), b.at(_ts(d, *hout))
        if ev is None or a is None or z is None or z <= a:
            continue
        move = b.op[a] - b.op[ev]
        if move == 0:
            continue
        sign = (1 if move > 0 else -1) * (1 if follow else -1)
        out.append((a, z, float(b.op[z]), sign))
    return out


def judge(b: Bars, tr: list[Trade], name: str) -> dict[str, Any]:
    last_year = datetime.fromtimestamp(int(b.ts[-1]), timezone.utc).year
    a = np.array([x[0] for x in tr]); z = np.array([x[1] for x in tr])
    px = np.array([x[2] for x in tr]); sg = np.array([x[3] for x in tr])
    e = b.op[a]
    gross = sg * (px - e) / e * 100
    fee = FEE / e * 100
    net = gross - fee
    t_in = b.ts[a]
    yrs: dict[int, list[float]] = {}
    for t, r in zip(t_in, net):
        yrs.setdefault(datetime.fromtimestamp(int(t), timezone.utc).year, []).append(float(r))
    full = {y: v for y, v in yrs.items() if y < last_year}
    pos = sum(1 for v in full.values() if sum(v) > 0)
    rng = np.random.default_rng(zlib.crc32(f"essai28:{name}".encode()))
    d0 = np.array([_ts(datetime.fromtimestamp(int(t), sl.NY).date(), 0, 0) for t in t_in])
    dur = b.ts[z] - b.ts[a]
    starts = d0[:, None] + rng.integers(0, 288, (len(tr), N_MONKEYS)) * 300
    ia = np.clip(np.searchsorted(b.ts, starts), 0, len(b.ts) - 1)
    ib = np.clip(np.searchsorted(b.ts, starts + dur[:, None]), 0, len(b.ts) - 1)
    mk = sg[:, None] * (b.op[ib] - b.op[ia]) / b.op[ia] * 100 - FEE / b.op[ia] * 100
    means = mk.mean(0)
    sd = float(means.std(ddof=1))
    real = float(net.mean())
    mean = lambda m: round(float(net[m].mean()), 4) if m.any() else None  # noqa: E731
    v = {"n": len(tr), "gross_pct": round(float(gross.mean()), 4), "net_pct": round(real, 4),
         "positive_years": f"{pos}/{len(full)}",
         "years": {str(y): round(sum(x) / len(x), 4) for y, x in sorted(yrs.items())},
         "before_2020": mean(t_in < HALF), "since_2020": mean(t_in >= HALF), "last_2_years": mean(t_in >= RECENT),
         "fees_x2": round(float((gross - 2 * fee).mean()), 4),
         "monkeys": {"mean_pct": round(float(means.mean()), 4), "beaten": int((means < real).sum()),
                     "z": round((real - float(means.mean())) / sd, 2) if sd > 0 else None}}
    v["checks"] = {"100 trades": len(tr) >= MIN_TRADES, "> 0": real > 0, "60 % des années": pos >= 0.6 * len(full),
                   "deux moitiés": (v["before_2020"] or 0) > 0 and (v["since_2020"] or 0) > 0,
                   "2 dernières années": (v["last_2_years"] or 0) > 0, "frais doublés": v["fees_x2"] > 0,
                   "singes": v["monkeys"]["beaten"] >= 950}
    v["robust"] = all(v["checks"].values())
    return v


def cells(b: Bars, root: Path) -> dict[str, Callable[[], list[Trade]]]:
    ev = json.loads((root / "macro_events_2010_2024.json").read_text(encoding="utf-8"))
    fomc = sorted(set(ev["fomc"]) | set(macro_history.FOMC))
    nfp = sorted(set(ev["nfp"]) | set(macro_history.NFP))
    return {
        "A vente du matin": lambda: timed(b, (3, 0), (10, 0), -1),
        "B achat de l'après-midi": lambda: timed(b, (11, 0), (16, 55), 1),
        "C1 faux cassage du plus bas": lambda: false_break(b, 1),
        "C2 faux cassage du plus haut": lambda: false_break(b, -1),
        "D suite de la Fed": lambda: event_trades(b, fomc, (14, 0), (14, 5), (16, 0), True),
        "E avant les fixings de Londres": lambda: sorted(timed(b, (10, 0), (10, 30), -1, LONDON)
                                                        + timed(b, (14, 30), (15, 0), -1, LONDON)),
        "F retournement après l'emploi": lambda: event_trades(b, nfp, (8, 30), (8, 45), (11, 0), False),
    }


def run(candles, root: Path, log=print) -> dict[str, Any]:
    b = Bars(candles)
    out: dict[str, Any] = {"essai": 28, "fee_usd_oz": FEE, "cells": {}}
    for name, fn in cells(b, root).items():
        v = judge(b, fn(), name)
        out["cells"][name] = v
        failed = [k for k, ok in v["checks"].items() if not ok]
        log(f"{name:32s} n={v['n']:5d} net {v['net_pct']:+.4f} % brut {v['gross_pct']:+.4f} années {v['positive_years']} "
            f"av.2020 {v['before_2020']} depuis {v['since_2020']} récent {v['last_2_years']} frais×2 {v['fees_x2']} "
            f"singes {v['monkeys']['beaten']} z {v['monkeys']['z']} → {'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")
    z_thr = NormalDist().inv_cdf(1 - 0.05 / len(out["cells"]))
    out["z_threshold"] = round(z_thr, 2)
    for v in out["cells"].values():
        v["status"] = ("prouvé" if v["robust"] and (v["monkeys"]["z"] or 0) > z_thr
                       else "robuste" if v["robust"] else "pas robuste")
    return out


def main() -> None:
    from .config import load_config
    from .engine import Engine
    from .essai23 import load
    from .models import iso, utcnow
    eng = Engine(load_config())
    new = eng.store.load_history("gold")
    candles = [c for c in load(eng.store.dir / "history" / "long" / "gold_5m.json") if c.ts < new[0].ts] + new
    out = run(candles, eng.store.dir, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    for k, v in out["cells"].items():
        print(f"{k:32s} {v['status']}", flush=True)
    eng.store._write(eng.store.dir / "essai28.json", out)


if __name__ == "__main__":
    main()
