"""Essai 40 (HYPOTHESES.md) : méthode ICT « BPR / IFVG » d'un trader TikTok, codée sur le Nasdaq 2014-2026.

    python -m trading_bot.essai40          → data/essai40.json
    python -m trading_bot.essai40 --topstep → data/essai40b.json (comptes Topstep neufs)
"""
from __future__ import annotations

import zlib
from datetime import datetime, time, timezone
from statistics import NormalDist
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np

PARIS = ZoneInfo("Europe/Paris")
UTC = timezone.utc
HALF = int(datetime(2020, 1, 1, tzinfo=UTC).timestamp())
RECENT = int(datetime(2024, 10, 20, tzinfo=UTC).timestamp())
N_MONKEYS = 1000
MIN_TRADES = 200
LOOK_M5 = 12          # FVG M5 opposé de moins d'1 h
TOUCH = 6             # zone HTF touchée dans les 30 dernières minutes
HTF_LIFE = 48 * 3600  # FVG HTF formé dans les 48 h
SWING = 6             # stop sur l'extrême des 6 dernières bougies
MORNING = ((9, 0), (11, 0))
AFTERNOON = ((14, 30), (17, 0))
EXIT = time(22, 0)

# nom → (déclencheur, zone HTF en heures ou None, Fibo, objectif R, fenêtres)
CELLS: dict[str, tuple[str, int | None, bool, float, tuple]] = {
    "C1 IFVG + FVG H1 + Fibo, 2 R": ("ifvg", 1, True, 2.0, (MORNING, AFTERNOON)),
    "C2 BPR strict + FVG H1 + Fibo": ("bpr", 1, True, 2.0, (MORNING, AFTERNOON)),
    "C3 IFVG + FVG H4 + Fibo": ("ifvg", 4, True, 2.0, (MORNING, AFTERNOON)),
    "C4 IFVG + FVG H1, sans Fibo": ("ifvg", 1, False, 2.0, (MORNING, AFTERNOON)),
    "C5 IFVG + Fibo, sans zone HTF": ("ifvg", None, True, 2.0, (MORNING, AFTERNOON)),
    "C6 comme C1, objectif 1,5 R": ("ifvg", 1, True, 1.5, (MORNING, AFTERNOON)),
    "C7 comme C1, objectif 3 R": ("ifvg", 1, True, 3.0, (MORNING, AFTERNOON)),
    "C8 comme C1, matin seul": ("ifvg", 1, True, 2.0, (MORNING,)),
    "C9 comme C1, après-midi seul": ("ifvg", 1, True, 2.0, (AFTERNOON,)),
}


class Bars:
    def __init__(self, candles):
        self.ts = np.array([c.ts for c in candles], dtype=np.int64)
        self.op = np.array([c.open for c in candles])
        self.hi = np.array([c.high for c in candles])
        self.lo = np.array([c.low for c in candles])
        self.cl = np.array([c.close for c in candles])
        n = len(self.ts)
        loc = [datetime.fromtimestamp(int(t), PARIS) for t in self.ts]
        self.day = np.array([d.toordinal() for d in (x.date() for x in loc)], dtype=np.int64)
        self.minute = np.array([x.hour * 60 + x.minute for x in loc], dtype=np.int64)
        # fin forcée : première bougie à 22h Paris ou après, le même jour
        self.exit_at = np.full(n, n - 1, dtype=np.int64)
        nxt = n - 1
        for i in range(n - 1, -1, -1):
            if self.minute[i] >= EXIT.hour * 60 or (i + 1 < n and self.day[i + 1] != self.day[i]):
                nxt = i
            self.exit_at[i] = nxt
        # milieu de l'amplitude de la veille (jour Paris)
        self.mid_prev = np.full(n, np.nan)
        days, start = np.unique(self.day, return_index=True)
        ends = list(start[1:]) + [n]
        prev = np.nan
        for s, e in zip(start, ends):
            self.mid_prev[s:e] = prev
            prev = (self.hi[s:e].max() + self.lo[s:e].min()) / 2


def htf_touch(b: Bars, hours: int) -> tuple[np.ndarray, np.ndarray]:
    """Bougies 5 min où un FVG HTF haussier (bull) / baissier (bear) non comblé a été touché il y a ≤ 30 min."""
    n = len(b.ts)
    step = hours * 3600
    key = b.ts // step
    ks, first = np.unique(key, return_index=True)
    last = np.append(first[1:], n)
    H = np.array([b.hi[s:e].max() for s, e in zip(first, last)])
    L = np.array([b.lo[s:e].min() for s, e in zip(first, last)])
    bull = np.zeros(n, bool)
    bear = np.zeros(n, bool)
    for j in range(2, len(ks)):
        if ks[j] - ks[j - 2] != 2:
            continue
        a = last[j]                                   # connu à la clôture de la bougie HTF j
        if a >= n:
            break
        z = int(np.searchsorted(b.ts, b.ts[a] + HTF_LIFE))
        if L[j] > H[j - 2]:                           # FVG haussier [H[j-2], L[j]]
            bot, top = H[j - 2], L[j]
            hit = np.flatnonzero(b.lo[a:z] <= top)
            if len(hit):
                k = a + int(hit[0])
                if b.cl[k] >= bot:
                    end = min(k + TOUCH, n)
                    filled = np.flatnonzero(b.cl[k:end] < bot)
                    bull[k:k + (int(filled[0]) if len(filled) else end - k)] = True
        if H[j] < L[j - 2]:                           # FVG baissier [H[j], L[j-2]]
            bot, top = H[j], L[j - 2]
            hit = np.flatnonzero(b.hi[a:z] >= bot)
            if len(hit):
                k = a + int(hit[0])
                if b.cl[k] <= top:
                    end = min(k + TOUCH, n)
                    filled = np.flatnonzero(b.cl[k:end] > top)
                    bear[k:k + (int(filled[0]) if len(filled) else end - k)] = True
    return bull, bear


def m5_signals(b: Bars, kind: str) -> np.ndarray:
    """+1 / −1 à la clôture de la bougie i qui donne le déclencheur, 0 sinon."""
    n = len(b.ts)
    sig = np.zeros(n, np.int8)
    hi, lo, cl = b.hi, b.lo, b.cl
    up = np.zeros(n, bool); dn = np.zeros(n, bool)          # FVG haussier / baissier formé à la bougie k
    up[2:] = lo[2:] > hi[:-2]
    dn[2:] = hi[2:] < lo[:-2]
    for i in range(LOOK_M5 + 2, n):
        if b.day[i] != b.day[i - LOOK_M5]:
            continue
        ks = range(i - LOOK_M5, i)
        if kind == "ifvg":
            for k in ks:
                if dn[k] and cl[i] > lo[k - 2] >= cl[i - 1]:      # FVG baissier clôturé à travers
                    sig[i] = 1
                    break
                if up[k] and cl[i] < hi[k - 2] <= cl[i - 1]:
                    sig[i] = -1
                    break
        else:
            if up[i]:
                zb, zt = hi[i - 2], lo[i]
                if any(dn[k] and hi[k] < zt and lo[k - 2] > zb for k in ks):
                    sig[i] = 1
            elif dn[i]:
                zb, zt = hi[i], lo[i - 2]
                if any(up[k] and hi[k - 2] < zt and lo[k] > zb for k in ks):
                    sig[i] = -1
    return sig


def in_windows(minute: np.ndarray, windows) -> np.ndarray:
    ok = np.zeros(len(minute), bool)
    for (h0, m0), (h1, m1) in windows:
        ok |= (minute >= h0 * 60 + m0) & (minute < h1 * 60 + m1)
    return ok


def simulate(b: Bars, s: int, a: int, stop: float, target: float) -> tuple[int, float]:
    z = int(b.exit_at[a])
    for k in range(a, z):
        if (s > 0 and b.lo[k] <= stop) or (s < 0 and b.hi[k] >= stop):
            return k, stop
        if (s > 0 and b.hi[k] >= target) or (s < 0 and b.lo[k] <= target):
            return k, target
    return z, float(b.op[z])


def trades(b: Bars, cell, cost_pct: float, touch: dict) -> list[dict[str, Any]]:
    kind, htf, fibo, rr, windows = cell
    sig = m5_signals(b, kind) if kind not in touch else touch[kind]
    touch[kind] = sig
    win = in_windows(b.minute, windows)
    if htf is not None:
        bull, bear = touch.setdefault(f"h{htf}", htf_touch(b, htf))
    out = []
    n = len(b.ts)
    busy_until = -1
    day_state: dict[int, list[int]] = {}
    for i in np.flatnonzero(sig != 0):
        s = int(sig[i])
        a = i + 1
        if a >= n or i <= busy_until or not win[i] or b.day[a] != b.day[i] or b.exit_at[a] <= a:
            continue
        losses, wins = day_state.get(int(b.day[i]), [0, 0])
        if losses >= 2 or wins >= 1:
            continue
        if htf is not None and not (bull[i] if s > 0 else bear[i]):
            continue
        if fibo and (np.isnan(b.mid_prev[i]) or (s > 0 and b.cl[i] > b.mid_prev[i]) or (s < 0 and b.cl[i] < b.mid_prev[i])):
            continue
        e = float(b.op[a])
        stop = float(b.lo[i - SWING + 1:i + 1].min() if s > 0 else b.hi[i - SWING + 1:i + 1].max())
        risk = (e - stop) * s
        if risk <= 0:
            continue
        target = e + s * rr * risk
        k, px = simulate(b, s, a, stop, target)
        r = (px - e) * s / risk - cost_pct / 100 * e / risk
        out.append({"i": a, "exit": k, "sign": s, "stop_pct": risk / e, "rr": rr, "r": r,
                    "gross": (px - e) * s / risk, "cost_r": cost_pct / 100 * e / risk})
        busy_until = k
        st = day_state.setdefault(int(b.day[i]), [0, 0])
        st[0 if r < 0 else 1] += 1
    return out


def monkeys(b: Bars, tr: list[dict[str, Any]], cost_pct: float, rng) -> np.ndarray:
    """Même heure de la journée, n'importe quel jour, même sens, même stop en %, même objectif, même sortie à 22h."""
    total = np.zeros(N_MONKEYS)
    count = np.zeros(N_MONKEYS)
    first, lastd = int(b.ts[0]) // 86400 + 1, int(b.ts[-1]) // 86400 - 2
    for t in tr:
        tod = int(b.ts[t["i"]]) % 86400
        starts = rng.integers(first, lastd, N_MONKEYS) * 86400 + tod
        ia = np.clip(np.searchsorted(b.ts, starts), 0, len(b.ts) - 2)
        ok = (b.ts[ia] - starts) <= 600
        z = b.exit_at[ia]
        s = t["sign"]
        e = b.op[ia]
        risk = t["stop_pct"] * e
        stop = e - s * risk
        tgt = e + s * t["rr"] * risk
        px = b.op[z].copy()
        open_ = np.ones(N_MONKEYS, bool)
        for step in range(0, int((z - ia).max()) + 1):
            k = np.minimum(ia + step, len(b.ts) - 1)
            live = open_ & (k < z)
            if not live.any():
                break
            hs = live & ((b.lo[k] <= stop) if s > 0 else (b.hi[k] >= stop))
            px[hs] = stop[hs]; open_ &= ~hs
            live &= ~hs
            ht = live & ((b.hi[k] >= tgt) if s > 0 else (b.lo[k] <= tgt))
            px[ht] = tgt[ht]; open_ &= ~ht
        r = (px - e) * s / risk - cost_pct / 100 * e / risk
        total += np.where(ok, r, 0.0)
        count += ok
    return total / np.maximum(count, 1)


def judge(b: Bars, tr: list[dict[str, Any]], name: str, cost_pct: float) -> dict[str, Any]:
    if not tr:
        return {"n": 0, "checks": {"200 trades": False}, "robust": False}
    last_year = datetime.fromtimestamp(int(b.ts[-1]), UTC).year
    r = np.array([t["r"] for t in tr]); g = np.array([t["gross"] for t in tr]); c = np.array([t["cost_r"] for t in tr])
    t_in = b.ts[np.array([t["i"] for t in tr])]
    yrs: dict[int, list[float]] = {}
    for t, x in zip(t_in, r):
        yrs.setdefault(datetime.fromtimestamp(int(t), UTC).year, []).append(float(x))
    full = {y: v for y, v in yrs.items() if 2014 < y < last_year}
    pos = sum(1 for v in full.values() if sum(v) > 0)
    means = monkeys(b, tr, cost_pct, np.random.default_rng(zlib.crc32(f"essai40:{name}".encode())))
    sd = float(means.std(ddof=1))
    real = float(r.mean())
    mean = lambda m: round(float(r[m].mean()), 4) if m.any() else None  # noqa: E731
    v = {"n": len(tr), "net_r": round(real, 4), "gross_r": round(float(g.mean()), 4), "cost_r": round(float(c.mean()), 4),
         "win_rate": round(float((r > 0).mean()), 3), "stop_pct": round(float(np.median([t["stop_pct"] for t in tr])) * 100, 3),
         "positive_years": f"{pos}/{len(full)}",
         "years": {str(y): round(sum(x) / len(x), 3) for y, x in sorted(yrs.items())},
         "before_2020": mean(t_in < HALF), "since_2020": mean(t_in >= HALF), "last_2_years": mean(t_in >= RECENT),
         "fees_x2": round(float((r - c).mean()), 4),
         "monkeys": {"mean_r": round(float(means.mean()), 4), "beaten": int((means < real).sum()),
                     "z": round((real - float(means.mean())) / sd, 2) if sd > 0 else None}}
    v["checks"] = {"200 trades": len(tr) >= MIN_TRADES, "> 0": real > 0, "60 % des années": pos >= 0.6 * len(full),
                   "deux moitiés": (v["before_2020"] or 0) > 0 and (v["since_2020"] or 0) > 0,
                   "2 dernières années": (v["last_2_years"] or 0) > 0, "frais doublés": v["fees_x2"] > 0,
                   "singes": v["monkeys"]["beaten"] >= 950}
    v["robust"] = all(v["checks"].values())
    return v


def run(candles, cost_pct: float, log=print) -> dict[str, Any]:
    b = Bars(candles)
    out: dict[str, Any] = {"essai": 40, "asset": "nasdaq", "cost_pct": cost_pct, "cells": {}}
    cache: dict = {}
    for name, cell in CELLS.items():
        v = judge(b, trades(b, cell, cost_pct, cache), name, cost_pct)
        out["cells"][name] = v
        failed = [k for k, ok in v["checks"].items() if not ok]
        log(f"{name:34s} n={v['n']:5d} net {v.get('net_r', 0):+.3f} R brut {v.get('gross_r', 0):+.3f} "
            f"gagnants {v.get('win_rate')} stop {v.get('stop_pct')} % années {v.get('positive_years')} "
            f"av.2020 {v.get('before_2020')} depuis {v.get('since_2020')} récent {v.get('last_2_years')} "
            f"frais×2 {v.get('fees_x2')} singes {v.get('monkeys', {}).get('beaten')} z {v.get('monkeys', {}).get('z')} → "
            f"{'ROBUSTE' if not failed else 'échoue : ' + ', '.join(failed)}")
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
    cfg = load_config()
    eng = Engine(cfg)
    new = eng.store.load_history("nasdaq")
    candles = [c for c in load(eng.store.dir / "history" / "long" / "nasdaq_5m.json") if not new or c.ts < new[0].ts] + new
    out = run(candles, cfg.assets["nasdaq"].cost_pct, log=lambda s: print(s, flush=True))
    out["updated_at"] = iso(utcnow())
    for k, v in out["cells"].items():
        print(f"{k:34s} {v['status']}", flush=True)
    eng.store._write(eng.store.dir / "essai40.json", out)




def topstep(b: Bars, tr: list[dict[str, Any]], since: int = 0, risk_usd: float = 300.0) -> dict[str, Any]:
    """Un compte Topstep 50K neuf ouvert chaque jour de bourse, qui prend les trades de `tr` à partir de ce jour."""
    from .topstep import FEES, PRODUCTS, RULES
    per_pt = PRODUCTS["nasdaq"][1]
    fee = FEES["nasdaq"][0] + FEES["nasdaq"][1]
    rows = []
    for t in tr:
        e = float(b.op[t["i"]])
        risk_pts = t["stop_pct"] * e
        n = min(int(risk_usd // (risk_pts * per_pt)), RULES["max_micros"])
        if n < 1:
            continue
        rows.append((int(b.day[t["i"]]), n * per_pt * t["gross"] * risk_pts - n * fee))
    days = sorted({int(d) for d in b.day[b.ts >= since]})
    out = {"passed": 0, "failed": 0, "open": 0, "days_to_pass": [], "days_to_fail": []}
    k0 = 0
    for d0 in days:
        while k0 < len(rows) and rows[k0][0] < d0:
            k0 += 1
        start = RULES["start_balance"]
        bal, mll, peak, cur, day_pnl, best, traded = start, start - RULES["max_loss"], start, None, 0.0, 0.0, 0
        verdict = None
        for d, pnl in rows[k0:]:
            if d != cur:
                if cur is not None:
                    peak = max(peak, bal)
                    mll = min(start, max(mll, peak - RULES["max_loss"]))
                    best = max(best, day_pnl)
                cur, day_pnl = d, 0.0
                traded += 1
            bal += pnl
            day_pnl += pnl
            if bal <= mll or day_pnl <= -RULES["daily_loss"]:
                verdict = "failed"
                break
            profit = bal - start
            if profit >= max(RULES["profit_target"], max(best, day_pnl) / RULES["consistency"]):
                verdict = "passed"
                break
        if verdict is None:
            out["open"] += 1
        else:
            out[verdict] += 1
            out[f"days_to_{'pass' if verdict == 'passed' else 'fail'}"].append(traded)
    tot = out["passed"] + out["failed"]
    return {"accounts": len(days), "passed_pct": round(100 * out["passed"] / tot, 1) if tot else None,
            "failed_pct": round(100 * out["failed"] / tot, 1) if tot else None, "still_open": out["open"],
            "median_days_to_pass": float(np.median(out["days_to_pass"])) if out["days_to_pass"] else None,
            "median_days_to_fail": float(np.median(out["days_to_fail"])) if out["days_to_fail"] else None,
            "trades_with_size": len(rows)}


def main_topstep() -> None:
    from .config import load_config
    from .engine import Engine
    from .essai23 import load
    from .models import iso, utcnow
    cfg = load_config()
    eng = Engine(cfg)
    new = eng.store.load_history("nasdaq")
    candles = [c for c in load(eng.store.dir / "history" / "long" / "nasdaq_5m.json") if not new or c.ts < new[0].ts] + new
    b = Bars(candles)
    cache: dict = {}
    out: dict[str, Any] = {"essai": "40b", "updated_at": iso(utcnow()), "cells": {}}
    for name in ("C1 IFVG + FVG H1 + Fibo, 2 R", "C2 BPR strict + FVG H1 + Fibo"):
        tr = trades(b, CELLS[name], cfg.assets["nasdaq"].cost_pct, cache)
        out["cells"][name] = {"2014-2026": topstep(b, tr), "depuis 2020": topstep(b, tr, HALF)}
        print(name, out["cells"][name], flush=True)
    eng.store._write(eng.store.dir / "essai40b.json", out)


if __name__ == "__main__":
    import sys
    main_topstep() if "--topstep" in sys.argv else main()
