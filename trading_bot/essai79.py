"""Essai 79 (HYPOTHESES.md) : petites anomalies peu connues, jamais testées chez nous (10/11/2026), 17 cellules.

L1/L2 effet du déjeuner (S&P, Nasdaq), G1 trou du week-end comblé (or, euro, GBPUSD, Nasdaq, DAX), C1 trou CME
(Bitcoin, Ethereum), T1 mardi de retournement (S&P, Nasdaq), V1 VIX étiré (S&P, Nasdaq), B1 retard
Ethereum/Solana sur le Bitcoin.

    python -m trading_bot.essai78_data     → données (hors dépôt)
    python -m trading_bot.essai79          → data/essai79.json (et data/history/long/essai79_trades.pkl pour l'essai 80)
"""
from __future__ import annotations

import json
import pickle
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from . import essai78 as e78
from . import strategies as sl
from .config import DATA_DIR
from .essai33 import LONG, Bars, z_threshold
from .essai64 import ny_minutes
from .essai69 import half_days

UTC = timezone.utc
OUT = Path(DATA_DIR) / "essai79.json"
TRADES = LONG / "essai79_trades.pkl"
N_CELLS = 17


# ---------------------------------------------------------------- outils

def session_atr(b: Bars, mins, day, lo_m: int, hi_m: int, n: int = 14) -> dict[int, float]:
    """ATR n jours des séances [lo_m, hi_m) (minutes NY), connu AVANT chaque jour : {jour ordinal: atr}."""
    m = (mins >= lo_m) & (mins < hi_m)
    idx = np.flatnonzero(m)
    cut = np.flatnonzero(np.diff(day[idx])) + 1
    rows = []
    for a, z in zip(np.r_[0, cut], np.r_[cut, len(idx)]):
        seg = idx[a:z]
        if len(seg) < 12:
            continue
        rows.append((int(day[seg[0]]), float(b.h[seg].max()), float(b.l[seg].min()), float(b.c[seg[-1]])))
    out, trs = {}, []
    for k in range(1, len(rows)):
        d, h, lo, c = rows[k]
        pc = rows[k - 1][3]
        if len(trs) >= n:
            out[d] = float(np.mean(trs[-n:]))
        trs.append(max(h - lo, abs(h - pc), abs(lo - pc)))
    return out


def follow(b: Bars, i: int, sign: int, entry: float, stop: float, target: float | None, end_i: int,
           exit_at_open: bool = True) -> tuple[int, float, str]:
    """Position ouverte à l'ouverture de la bougie i ; stop prioritaire ; sortie à l'ouverture de end_i
    (ou à la clôture de end_i − 1 si exit_at_open est faux)."""
    for k in range(i, min(end_i, len(b.ts))):
        if (b.l[k] <= stop) if sign > 0 else (b.h[k] >= stop):
            return k, float(min(stop, b.o[k]) if sign > 0 else max(stop, b.o[k])) if k > i else stop, "stop"
        if target is not None and ((b.h[k] >= target) if sign > 0 else (b.l[k] <= target)):
            return k, float(max(target, b.o[k]) if sign > 0 else min(target, b.o[k])) if k > i else target, "objectif"
    k = min(end_i, len(b.ts) - 1)
    return (k, float(b.o[k]), "heure") if exit_at_open else (k - 1, float(b.c[k - 1]), "heure")


def trade(name, asset, b, i, j, sign, entry, px, risk, why) -> sl.Trade:
    return sl.Trade(name, asset, "long" if sign > 0 else "short", int(b.ts[i]), int(b.ts[j]) + 300, entry, px, risk, why)


def by_minute(mins, day, wd) -> dict[tuple[int, int], int]:
    out: dict[tuple[int, int], int] = {}
    for k in range(len(mins)):
        out.setdefault((int(day[k]), int(mins[k])), k)
    return out


# ---------------------------------------------------------------- L1 / L2 effet du déjeuner

def lunch(asset: str, b: Bars, long_only: bool) -> list[sl.Trade]:
    mins, wd, day = ny_minutes(b.ts)
    atr = session_atr(b, mins, day, 570, 960)
    at = by_minute(mins, day, wd)
    out = []
    for d in sorted(set(day[(wd < 5)].tolist())):
        dd = date.fromordinal(d)
        if dd in half_days(dd.year) or d not in atr:
            continue
        i11, i12, i14 = at.get((d, 660)), at.get((d, 720)), at.get((d, 840))
        if i11 is None or i12 is None or i14 is None:
            continue
        risk = 0.25 * atr[d]
        if not long_only:
            e = float(b.o[i11])
            j, px, why = follow(b, i11, -1, e, e + risk, None, i12)
            out.append(trade("L1", asset, b, i11, j, -1, e, px, risk, why))
        e = float(b.o[i12])
        j, px, why = follow(b, i12, 1, e, e - risk, None, i14)
        out.append(trade("L1" if not long_only else "L2", asset, b, i12, j, 1, e, px, risk, why))
    return out


# ---------------------------------------------------------------- T1 mardi de retournement

def tuesday(asset: str, b: Bars) -> list[sl.Trade]:
    mins, wd, day = ny_minutes(b.ts)
    atr = session_atr(b, mins, day, 570, 960)
    at = by_minute(mins, day, wd)
    out = []
    for d in sorted(set(day[wd == 0].tolist())):
        fri, tue = d - 3, d + 1
        im, if_, it = at.get((d, 955)), at.get((fri, 955)), at.get((tue, 955))
        if im is None or if_ is None or it is None or d not in atr:
            continue
        if not b.c[im] < b.c[if_]:
            continue
        e, risk = float(b.c[im]), atr[d]
        j, px, why = follow(b, im + 1, 1, e, e - risk, None, it + 1, exit_at_open=False)
        out.append(sl.Trade("T1", asset, "long", int(b.ts[im]) + 300, int(b.ts[j]) + 300, e, px, risk, why))
    return out


# ---------------------------------------------------------------- V1 VIX étiré (Connors)

def vix_stretch(asset: str, b: Bars, vix: dict[int, float]) -> list[sl.Trade]:
    mins, wd, day = ny_minutes(b.ts)
    at = by_minute(mins, day, wd)
    atr = session_atr(b, mins, day, 570, 960)
    days = [d for d in sorted(set(day[wd < 5].tolist())) if at.get((d, 955)) is not None]
    cl = np.array([b.c[at[(d, 955)]] for d in days])
    vx = np.array([vix.get(d, np.nan) for d in days])
    out, k = [], 200
    while k < len(days) - 1:
        if np.isnan(vx[k - 12:k + 1]).any() or days[k] not in atr:
            k += 1
            continue
        ma10 = [np.mean(vx[i - 9:i + 1]) for i in (k - 2, k - 1, k)]
        ok = all(vx[i] >= 1.05 * m for i, m in zip((k - 2, k - 1, k), ma10)) and cl[k] > cl[k - 199:k + 1].mean()
        if not ok:
            k += 1
            continue
        e, risk = float(cl[k]), 2 * atr[days[k]]
        stop = e - risk
        ik = at[(days[k], 955)]
        px = why = None
        jj = k
        for jj in range(k + 1, min(len(days), k + 11)):
            a, z = at[(days[jj - 1], 955)] + 1, at[(days[jj], 955)] + 1
            hit = next((x for x in range(a, z) if b.l[x] <= stop), None)
            if hit is not None:
                px, why, jx = float(min(stop, b.o[hit])), "stop", hit
                break
            seg = cl[jj - 2:jj + 1]
            up, dn = np.maximum(np.diff(seg), 0).sum(), np.maximum(-np.diff(seg), 0).sum()
            rsi = 100.0 if dn == 0 else 100 - 100 / (1 + up / dn)
            if rsi > 65 or jj == k + 10:
                px, why, jx = float(cl[jj]), "règle", z - 1
                break
        if px is None:
            break
        out.append(sl.Trade("V1", asset, "long", int(b.ts[ik]) + 300, int(b.ts[jx]) + 300, e, px, risk, why))
        k = jj + 1
    return out


# ---------------------------------------------------------------- G1 trou du week-end

def weekend_gap(asset: str, b: Bars) -> tuple[list[sl.Trade], dict[int, float]]:
    mins, wd, day = ny_minutes(b.ts)
    # jours de 24 h commençant à 17:00 New York
    d24 = ny_minutes(b.ts + 7 * 3600)[2]
    atr = session_atr(b, np.zeros(len(b.ts), np.int32), d24, 0, 1)
    out, targets = [], {}
    gaps = np.flatnonzero(np.diff(b.ts) >= 40 * 3600) + 1
    for i in gaps:
        if wd[i] not in (6, 0):                       # réouverture du dimanche soir (ou lundi)
            continue
        fc, o = float(b.c[i - 1]), float(b.o[i])
        a = atr.get(int(d24[i]))
        gap = o - fc
        if a is None or abs(gap) < 0.1 * a:
            continue
        sign = -1 if gap > 0 else 1
        risk = abs(gap)
        stop = o - sign * risk
        mon = int(d24[i]) if wd[i] == 6 else int(day[i])
        mon = mon if date.fromordinal(mon).weekday() == 0 else mon + 1
        end = np.flatnonzero((day == mon) & (mins >= 720))
        end_i = int(end[0]) if len(end) else min(i + 288, len(b.ts) - 1)
        j, px, why = follow(b, i, sign, o, stop, fc, end_i)
        t = trade("G1", asset, b, i, j, sign, o, px, risk, why)
        out.append(t)
        targets[t.entry_ts] = fc
    return out, targets


# ---------------------------------------------------------------- C1 trou CME (crypto)

def cme_gap(asset: str, b: Bars) -> tuple[list[sl.Trade], dict[int, float]]:
    mins, wd, day = ny_minutes(b.ts)
    ct = mins - 60                                     # Chicago = New York − 1 h
    at = by_minute(ct, day, wd)
    out, targets = [], {}
    for d in sorted(set(day[wd == 4].tolist())):
        i_f, i_s = at.get((d, 955)), at.get((d + 2, 1020))
        i_end = at.get((d + 7, 960))
        if i_f is None or i_s is None or i_end is None:
            continue
        pf, ps = float(b.c[i_f]), float(b.o[i_s])
        if abs(ps / pf - 1) < 0.01:
            continue
        sign = -1 if ps > pf else 1
        risk = abs(ps - pf)
        j, px, why = follow(b, i_s, sign, ps, ps - sign * risk, pf, i_end)
        t = trade("C1", asset, b, i_s, j, sign, ps, px, risk, why)
        out.append(t)
        targets[t.entry_ts] = pf
    return out, targets


# ---------------------------------------------------------------- B1 retard sur le Bitcoin

def lead_lag(asset: str, alt: Bars, btc: Bars) -> list[sl.Trade]:
    common, ia, ib = np.intersect1d(alt.ts, btc.ts, return_indices=True)
    rb = np.r_[0, btc.c[ib][1:] / btc.c[ib][:-1] - 1]
    ra = np.r_[0, alt.c[ia][1:] / alt.c[ia][:-1] - 1]
    contiguous = np.r_[False, np.diff(common) == 300]
    cs_b, cs_a = np.r_[0, np.cumsum(np.abs(rb))], np.r_[0, np.cumsum(np.abs(ra))]
    out, k = [], 289
    n = len(common)
    while k < n - 8:
        avg_b = (cs_b[k] - cs_b[k - 288]) / 288
        avg_a = (cs_a[k] - cs_a[k - 288]) / 288
        if not contiguous[k] or avg_b <= 0 or avg_a <= 0 or abs(rb[k]) < 3 * avg_b:
            k += 1
            continue
        sign = 1 if rb[k] > 0 else -1
        if ra[k] * sign >= 0.5 * abs(rb[k]):
            k += 1
            continue
        i = int(ia[k + 1])
        if alt.ts[i] != common[k] + 300:
            k += 1
            continue
        e = float(alt.o[i])
        risk = 3 * avg_a * e
        j, px, why = follow(alt, i, sign, e, e - sign * risk, None, i + 6)
        out.append(trade("B1", asset, alt, i, j, sign, e, px, risk, why))
        k += 7
    return out


# ---------------------------------------------------------------- run

def vix_daily() -> dict[int, float] | None:
    f = LONG / "yahoo78.json"
    if not f.exists():
        return None
    rows = json.loads(f.read_text()).get("vix")
    if not rows:
        return None
    from zoneinfo import ZoneInfo
    ny = ZoneInfo("America/New_York")
    return {datetime.fromtimestamp(r[0], ny).toordinal(): r[4] for r in rows}


def run() -> dict[str, Any]:
    rng = np.random.default_rng(79)
    z = z_threshold(N_CELLS)
    out: dict[str, Any] = {"essai": 79, "cellules": N_CELLS, "z_requis": round(z, 2)}
    keep: dict[str, list] = {}
    bars = {}

    def get(a):
        if a not in bars:
            bars[a] = e78.bars5(a)
        return bars[a]

    def show(cell, res):
        out[cell] = res
        print(cell, {k: res.get(k) for k in ("n", "R", "R_2014_2019", "R_2020_2026", "R_frais_x2", "z",
                                              "singes_battus", "verdict")}, flush=True)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    for a in ("sp500", "nasdaq"):
        b = get(a)
        for name, lo in (("L1", False), ("L2", True)):
            tr = lunch(a, b, lo)
            keep[f"{name}_{a}"] = tr
            show(f"{name} {a}", e78.judge(a, tr, b, rng, z))
        tr = tuesday(a, b)
        show(f"T1 {a}", e78.judge(a, tr, b, rng, z))
        vix = vix_daily()
        if vix:
            show(f"V1 {a}", e78.judge(a, vix_stretch(a, b, vix), b, rng, z))
        else:
            out[f"V1 {a}"] = {"verdict": "abandonnée : VIX Yahoo indisponible", "passe": False}
    for a in ("gold", "euro", "gbpusd", "nasdaq", "dax"):
        b = get(a)
        tr, tg = weekend_gap(a, b)
        res = e78.judge(a, tr, b, rng, z, mult=2.0, targets=tg)
        res["R_frais_x4"] = res.pop("R_frais_x2")
        show(f"G1 {a}", res)
    for a in ("btc", "eth"):
        b = get(a)
        tr, tg = cme_gap(a, b)
        show(f"C1 {a}", e78.judge(a, tr, b, rng, z, targets=tg))
    btc = get("btc")
    for a in ("eth", "sol"):
        b = get(a)
        show(f"B1 {a}", e78.judge(a, lead_lag(a, b, btc), b, rng, z))
    with TRADES.open("wb") as f:
        pickle.dump({k: [t.__dict__ for t in v] for k, v in keep.items()}, f)
    out["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    run()
