"""Essai 78 (HYPOTHESES.md) : nos stratégies prouvées sur des marchés jamais testés (10/11/2026).

    python -m trading_bot.essai78_data     → données (hors dépôt, data/history/long/)
    python -m trading_bot.essai78          → data/essai78.json

Grille fixée d'avance (40 cellules) ; règles = code de strategies.py, avec une copie paramétrée par séance locale
pour la zone de bruit v2, Double 7 et Crabel sur les indices étrangers.
"""
from __future__ import annotations

import json
import os
import sys
from bisect import bisect_left
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

import numpy as np

from . import essai52
from . import strategies as sl
from .config import DATA_DIR
from .essai33 import LONG, Bars, z_threshold
from .models import Candle

UTC = timezone.utc
OUT = Path(DATA_DIR) / "essai78.json"
SPLIT = int(datetime(2020, 1, 1, tzinfo=UTC).timestamp())
N_CELLS = 40
N_MONKEYS = 1000

# frais aller-retour : ("pts", valeur) en points de prix, ("pct", valeur) en % du prix
FEES = {"sp500": ("pts", 0.6), "gold": ("pts", 0.30), "euro": ("pts", 0.0001), "dax": ("pts", 2.0),
        "btc": ("pct", 0.06), "silver": ("pts", 0.035), "nikkei": ("pts", 10.0), "ftse": ("pts", 2.0), "cac": ("pts", 2.0),
        "hangseng": ("pts", 10.0), "asx": ("pts", 2.0), "brent": ("pts", 0.05), "gbpusd": ("pts", 0.00012),
        "usdjpy": ("pts", 0.012), "russell": ("pts", 1.0), "eth": ("pct", 0.06), "sol": ("pct", 0.08),
        "nasdaq": ("pts", 1.3)}
# séance locale : (fuseau, ouverture, clôture)
LOCAL = {"nikkei": ("Asia/Tokyo", (9, 0), (15, 0)), "hangseng": ("Asia/Hong_Kong", (9, 30), (16, 0)),
         "asx": ("Australia/Sydney", (10, 0), (16, 0)), "ftse": ("Europe/London", (8, 0), (16, 30)),
         "cac": ("Europe/Paris", (9, 0), (17, 30)), "nasdaq": ("America/New_York", (9, 30), (16, 0))}
GRID = {**{m: ("zone_v2_locale", "double7_local", "crabel_local", "donchian_1h")
           for m in ("nikkei", "ftse", "cac", "hangseng", "asx")},
        "russell": ("double7_jour",),
        "silver": ("nuit_asie", "crabel_nr4", "donchian_1h", "cassure_williams"),
        **{m: ("donchian_1h", "cassure_williams", "crabel_nr4") for m in ("brent", "gbpusd", "usdjpy")},
        **{m: ("donchian_1h", "cassure_williams", "swing_w3") for m in ("eth", "sol")}}


# ---------------------------------------------------------------- données

def bars5(asset: str) -> Bars:
    if asset in ("eth", "sol", "btc"):
        return Bars.load(f"{asset}_5m.npz")
    return Bars.load(f"{asset}_1m.npz").resample(300)


def candles(b: Bars) -> list[Candle]:
    v = b.v if b.v is not None else np.zeros(len(b.ts))
    return [Candle(int(t), float(o), float(h), float(lo), float(c), float(x))
            for t, o, h, lo, c, x in zip(b.ts, b.o, b.h, b.l, b.c, v)]


def cost(asset: str, price: float) -> float:
    kind, v = FEES[asset]
    return v if kind == "pts" else price * v / 100


# ---------------------------------------------------------------- séances locales

def _lts(tz: ZoneInfo, d: date, hm: tuple[int, int]) -> int:
    return int(datetime.combine(d, time(*hm), tz).timestamp())


def zone_v2_locale(s: "sl._Series", asset: str, lookback: int = 14) -> list[sl.Trade]:
    """Copie de strategies.noise_area(realistic_stop=True) avec la séance locale du marché au lieu de 9:30-16:00 NY.
    Sans volume (HistData), le VWAP devient une moyenne simple des prix typiques, comme pour le témoin Nasdaq."""
    tz_name, op, cl = LOCAL[asset]
    tz = ZoneInfo(tz_name)
    atr15 = sl._atr15(s)
    out: list[sl.Trade] = []
    days = sl._days(s.c, tz)
    moves: dict[date, dict[int, float]] = {}
    for d in days:
        i0 = s.at(_lts(tz, d, op))
        if i0 is None:
            continue
        o, m, k, end = s.c[i0].open, {}, i0, _lts(tz, d, cl)
        while k < len(s.c) and s.c[k].ts < end:
            m[(s.c[k].ts + 300 - s.c[i0].ts) // 60] = abs(s.c[k].close / o - 1)
            k += 1
        moves[d] = m
    hist: list[date] = []
    prev_day: date | None = None
    for d in days:
        i0 = s.at(_lts(tz, d, op))
        pc_i = None
        if prev_day is not None:
            pc_i = s.last_before(_lts(tz, prev_day, cl))
            if pc_i is not None and s.c[pc_i].ts < _lts(tz, prev_day, cl) - 1800:
                pc_i = None
        if i0 is None or pc_i is None or len(hist) < lookback:
            if d in moves:
                hist.append(d)
                prev_day = d
            continue
        past = hist[-lookback:]
        o, pc = s.c[i0].open, s.c[pc_i].close
        hi_base, lo_base = max(o, pc), min(o, pc)

        def bounds(minute: int, past=past, hi_base=hi_base, lo_base=lo_base):
            vals = [moves[p][minute] for p in past if minute in moves[p]]
            if len(vals) < lookback // 2:
                return None
            sig = sum(vals) / len(vals)
            return hi_base * (1 + sig), lo_base * (1 - sig)

        t_open, end = _lts(tz, d, op), _lts(tz, d, cl)
        marks = list(range(t_open + 1800, end - 1800 + 1, 1800))
        vwap_pv = vwap_v = 0.0
        k, pos = i0, None
        while k < len(s.c) and s.c[k].ts < end:
            b = s.c[k]
            if pos is not None and k > pos[4]:
                hard = pos[1] - pos[3] if pos[0] == "long" else pos[1] + pos[3]
                if (b.low <= hard) if pos[0] == "long" else (b.high >= hard):
                    px = min(hard, b.open) if pos[0] == "long" else max(hard, b.open)
                    out.append(sl.Trade("zone_v2_locale", asset, pos[0], s.c[pos[4]].ts + 300, b.ts + 300, pos[1], px,
                                        pos[3], "stop"))
                    pos = None
            tp = (b.high + b.low + b.close) / 3
            vwap_pv += tp * max(b.volume, 1.0)
            vwap_v += max(b.volume, 1.0)
            close_t = b.ts + 300
            if close_t in marks:
                bd = bounds((close_t - s.c[i0].ts) // 60)
                vw = vwap_pv / vwap_v
                if bd:
                    ub, lb = bd
                    if pos is None:
                        if (b.close > ub or b.close < lb) and atr15[k]:
                            long = b.close > ub
                            stop = max(ub, vw) if long else min(lb, vw)
                            risk = max(abs(b.close - stop), atr15[k])
                            pos = ("long" if long else "short", b.close, stop, risk, k)
                    else:
                        long = pos[0] == "long"
                        stop = max(ub, vw) if long else min(lb, vw)
                        if (b.close < stop) if long else (b.close > stop):
                            out.append(sl.Trade("zone_v2_locale", asset, pos[0], s.c[pos[4]].ts + 300, close_t,
                                                pos[1], b.close, pos[3], "bornes"))
                            pos = None
            k += 1
        if pos is not None:
            last = s.c[k - 1]
            out.append(sl.Trade("zone_v2_locale", asset, pos[0], s.c[pos[4]].ts + 300, last.ts + 300, pos[1],
                                last.close, pos[3], "heure"))
        hist.append(d)
        prev_day = d
    return out


def double7_local(c: list[Candle], asset: str) -> list[sl.Trade]:
    """essai52 R3 (Double 7) avec les bougies du jour prises sur la séance locale."""
    tz_name, op, cl = LOCAL[asset]
    tz = ZoneInfo(tz_name)
    lo_m, hi_m = op[0] * 60 + op[1], cl[0] * 60 + cl[1]

    def key(ts: int, _asset: str):
        d = datetime.fromtimestamp(ts, tz)
        m = d.hour * 60 + d.minute
        return d.date() if lo_m <= m < hi_m and d.weekday() < 5 else None

    old = essai52.day_key
    essai52.day_key = key
    try:
        return essai52.daily_trades(c, asset, "R3")
    finally:
        essai52.day_key = old


def crabel_local(s: "sl._Series", asset: str, stretch_n: int = 10) -> list[sl.Trade]:
    """strategies.crabel_nr4 sur la séance locale (au lieu de la journée CME)."""
    tz_name, op, cl = LOCAL[asset]
    tz = ZoneInfo(tz_name)
    lo_m, hi_m = op[0] * 60 + op[1], cl[0] * 60 + cl[1]
    sess: list[dict[str, Any]] = []
    for j, t in enumerate(s.ts):
        d = datetime.fromtimestamp(t, tz)
        m = d.hour * 60 + d.minute
        if not (lo_m <= m < hi_m) or d.weekday() >= 5:
            continue
        if not sess or sess[-1]["day"] != d.date() or j != sess[-1]["z"]:
            if sess and sess[-1]["day"] == d.date():
                sess[-1]["z"] = j + 1
                continue
            sess.append({"day": d.date(), "a": j, "z": j + 1})
        else:
            sess[-1]["z"] = j + 1
    need = 0.6 * (hi_m - lo_m) / 5
    for x in sess:
        bars = s.c[x["a"]:x["z"]]
        x.update(o=bars[0].open, h=max(b.high for b in bars), l=min(b.low for b in bars), n=len(bars))
    sess = [x for x in sess if x["n"] >= need]
    out = []
    for k in range(stretch_n, len(sess)):
        cur, p1, p2 = sess[k], sess[k - 1], sess[k - 2]
        if (cur["day"] - p1["day"]).days > 5:
            continue
        ranges = [x["h"] - x["l"] for x in sess[k - 4:k]]
        if not (p1["h"] <= p2["h"] and p1["l"] >= p2["l"] and ranges[-1] <= min(ranges)):
            continue
        stretch = sum(min(x["h"] - x["o"], x["o"] - x["l"]) for x in sess[k - stretch_n:k]) / stretch_n
        if stretch <= 0:
            continue
        up, dn = cur["o"] + stretch, cur["o"] - stretch
        k0 = next((j for j in range(cur["a"], cur["z"]) if s.c[j].high >= up or s.c[j].low <= dn), None)
        if k0 is None:
            continue
        bar = s.c[k0]
        if bar.high >= up and bar.low <= dn:
            out.append(sl.Trade("crabel_local", asset, "long", s.ts[k0], s.ts[k0] + 300, up, dn, 2 * stretch, "stop"))
            continue
        long = bar.high >= up
        entry = max(up, bar.open) if long else min(dn, bar.open)
        stop = dn if long else up
        px, j, why = None, k0, "clôture"
        for j in range(k0 + 1, cur["z"]):
            b = s.c[j]
            if (long and b.low <= stop) or (not long and b.high >= stop):
                px, why = (min(b.open, stop) if long else max(b.open, stop)), "stop"
                break
        if px is None:
            j = cur["z"] - 1
            px = s.c[j].close
        out.append(sl.Trade("crabel_local", asset, "long" if long else "short", s.ts[k0], s.ts[j] + 300, entry, px,
                            2 * stretch, why))
    return out


def double7_jour(rows: list[list[float]], asset: str) -> list[sl.Trade]:
    """Double 7 sur bougies journalières (Russell, Yahoo) : même règle que essai52 R3, stop testé sur le bas du jour."""
    ts = np.array([r[0] for r in rows], dtype=np.int64)
    o, hi, lo, cl = (np.array([r[k] for r in rows]) for k in (1, 2, 3, 4))
    n = len(cl)
    tr = np.maximum(hi[1:] - lo[1:], np.maximum(abs(hi[1:] - cl[:-1]), abs(lo[1:] - cl[:-1])))
    out, i = [], 200
    while i < n - 1:
        s200 = cl[i - 199:i + 1].mean()
        atr = tr[i - 14:i].mean()
        if not (cl[i] > s200 and cl[i] <= cl[i - 6:i + 1].min()):
            i += 1
            continue
        entry, risk = cl[i], 2 * atr
        stop = entry - risk
        px = why = None
        j = i
        for j in range(i + 1, min(n, i + 11)):
            if lo[j] <= stop:
                px, why = min(stop, o[j]), "stop"
                break
            if cl[j] >= cl[j - 6:j + 1].max() or j == i + 10:
                px, why = cl[j], "règle"
                break
        if px is None:
            break
        out.append(sl.Trade("double7_jour", asset, "long", int(ts[i]) + 72000, int(ts[j]) + 72000, entry, px, risk, why))
        i = j + 1
    return out


# ---------------------------------------------------------------- jugement

def monkeys(b: Bars, tr: list[dict], cost_fn: Callable, rng, n: int = N_MONKEYS) -> np.ndarray:
    """Comme essai33.monkeys_bracket (n'importe quel jour, même heure UTC, même sens, même stop en %, même durée),
    sans objectif, et avec le réservoir de départs filtré pour la durée de chaque trade."""
    by_tod: dict[int, np.ndarray] = {}
    out = np.zeros((len(tr), n))
    for j, t in enumerate(tr):
        tod = int(b.tod[t["i"]])
        if tod not in by_tod:
            by_tod[tod] = np.flatnonzero(b.tod == tod)
        pool = by_tod[tod]
        mb, sg, sp = t["max"], t["sign"], t["stop_pct"]
        pool = pool[pool < len(b.ts) - mb - 1]
        starts = pool[rng.integers(0, len(pool), n)]
        e = b.o[starts]
        stop = e * (1 - sg * sp)
        tp = t.get("target_pct") or 0.0
        target = e * (1 + sg * tp)
        exit_px = b.o[starts + mb].copy()
        fs = np.full(n, mb)
        ft = np.full(n, mb)
        for k0 in range(0, mb, 512):                      # par blocs pour limiter la mémoire
            win = starts[:, None] + np.arange(k0, min(mb, k0 + 512))[None, :]
            hs = (b.l[win] <= stop[:, None]) if sg > 0 else (b.h[win] >= stop[:, None])
            fs = np.where((fs == mb) & hs.any(1), k0 + hs.argmax(1), fs)
            if tp:
                ht = (b.h[win] >= target[:, None]) if sg > 0 else (b.l[win] <= target[:, None])
                ft = np.where((ft == mb) & ht.any(1), k0 + ht.argmax(1), ft)
        exit_px = np.where(ft < fs, target, exit_px)
        exit_px = np.where((fs <= ft) & (fs < mb), stop, exit_px)
        out[j] = cost_fn(sg * (exit_px - e), e, e * sp)
    return out.mean(0)


def judge(asset: str, tr: list[sl.Trade], b: Bars | None, rng, z_need: float, mult: float = 1.0,
          targets: dict[int, float] | None = None) -> dict[str, Any]:
    """`mult` : frais multipliés d'office ; `targets` : objectif (prix) par heure d'entrée, repris par les singes."""
    tr = [t for t in tr if t.reason != "fin des données" and t.risk > 0]
    if len(tr) < 2:
        return {"n": len(tr), "passe": False, "verdict": "trop peu de trades"}
    r = np.array([(t.gross_points() - mult * cost(asset, t.entry)) / t.risk for t in tr])
    r2 = np.array([(t.gross_points() - 2 * mult * cost(asset, t.entry)) / t.risk for t in tr])
    ts = np.array([t.entry_ts for t in tr])
    sd = float(r.std(ddof=1))
    z = float(r.mean() / sd * np.sqrt(len(r))) if sd else 0.0
    years: dict[int, float] = {}
    for t, x in zip(tr, r):
        y = datetime.fromtimestamp(t.entry_ts, UTC).year
        years[y] = years.get(y, 0.0) + float(x)
    out: dict[str, Any] = {
        "n": len(r), "R": round(float(r.mean()), 4), "gagnants": round(float((r > 0).mean()), 3),
        "total_R": round(float(r.sum()), 1),
        "R_2014_2019": round(float(r[ts < SPLIT].mean()), 4) if (ts < SPLIT).any() else None,
        "R_2020_2026": round(float(r[ts >= SPLIT].mean()), 4) if (ts >= SPLIT).any() else None,
        "R_frais_x2": round(float(r2.mean()), 4), "R_brut": round(float(np.mean([t.gross_points() / t.risk for t in tr])), 4),
        "z": round(z, 2), "z_requis": round(z_need, 2),
        "annees": {y: round(v, 1) for y, v in sorted(years.items())},
        "periode": [datetime.fromtimestamp(int(ts.min()), UTC).strftime("%Y-%m"),
                    datetime.fromtimestamp(int(ts.max()), UTC).strftime("%Y-%m")]}
    pre = (out["n"] >= 200 and out["R"] > 0 and (out["R_2014_2019"] or 0) > 0 and (out["R_2020_2026"] or 0) > 0
           and out["R_frais_x2"] > 0)
    out["singes_battus"] = None
    if pre and b is not None:
        rows = []
        for t, x in zip(tr, r):
            i = int(np.searchsorted(b.ts, t.entry_ts))
            nb = max(1, int(np.searchsorted(b.ts, t.exit_ts) - i))
            if i + nb + 1 >= len(b.ts):
                continue
            rows.append({"i": i, "max": nb, "stop_pct": t.risk / t.entry, "target_pct": abs(targets[t.entry_ts] - t.entry) / t.entry if targets else 0.0,
                         "sign": 1 if t.direction == "long" else -1})
        kind, v = FEES[asset]
        if kind == "pts":
            cf = lambda move, e, risk, v=v * mult: (move - v) / risk
        else:
            cf = lambda move, e, risk, v=v * mult: (move - e * v / 100) / risk
        mk = monkeys(b, rows, cf, rng, N_MONKEYS)
        out["singes_battus"] = int((mk < out["R"]).sum())
        out["singes_moyen"] = round(float(mk.mean()), 4)
    out["passe"] = bool(pre and (out["singes_battus"] or 0) >= 950 and z >= z_need)
    out["verdict"] = "PASSE" if out["passe"] else ("contrôles OK, singes ou z non" if pre else "écartée")
    return out


def run_market(asset: str, rng, z_need: float) -> dict[str, Any]:
    res: dict[str, Any] = {}
    if asset == "russell":
        rows = json.loads((LONG / "yahoo78.json").read_text())["russell"]
        rows = [r for r in rows if r[0] >= int(datetime(2013, 1, 1, tzinfo=UTC).timestamp())]
        tr = [t for t in double7_jour(rows, asset) if t.entry_ts >= int(datetime(2014, 1, 1, tzinfo=UTC).timestamp())]
        res["double7_jour"] = judge(asset, tr, None, rng, z_need)
        res["double7_jour"]["note"] = "bougies jour : pas de singes possibles (même heure), jugé sans eux"
        r = res["double7_jour"]
        if r["n"] >= 200 and r["R"] > 0 and (r["R_2014_2019"] or 0) > 0 and (r["R_2020_2026"] or 0) > 0 \
                and r["R_frais_x2"] > 0 and r["z"] >= z_need:
            r["passe"], r["verdict"] = False, "contrôles OK, singes impossibles"
        return res
    b = bars5(asset)
    c = candles(b)
    s = sl._Series(c)
    for strat in GRID.get(asset, ()) or ():
        if strat == "zone_v2_locale":
            tr = zone_v2_locale(s, asset)
        elif strat == "double7_local":
            tr = double7_local(c, asset)
        elif strat == "crabel_local":
            tr = crabel_local(s, asset)
        elif strat in sl.RUNNERS_5M:
            tr = sl.RUNNERS_5M[strat](s, asset)
        else:
            tr = sl.RUNNERS_1H[strat](c, asset)
        res[strat] = judge(asset, tr, b, rng, z_need)
        print(asset, strat, {k: res[strat][k] for k in ("n", "R", "R_2014_2019", "R_2020_2026", "R_frais_x2", "z",
                                                         "singes_battus", "verdict") if k in res[strat]}, flush=True)
    return res


def run(only: list[str] | None = None) -> dict[str, Any]:
    rng = np.random.default_rng(78)
    z_need = z_threshold(N_CELLS)
    out = json.loads(OUT.read_text()) if OUT.exists() and only else {}
    out.update({"essai": 78, "cellules": N_CELLS, "z_requis": round(z_need, 2), "frais": FEES})
    for asset in only or [*GRID, "temoin_nasdaq"]:
        if asset == "temoin_nasdaq":
            b = bars5("nasdaq")
            s = sl._Series(candles(b))
            out[asset] = {"zone_v2_locale": judge("nasdaq", zone_v2_locale(s, "nasdaq"), b, rng, z_need),
                          "noise_area_v2_prod": judge("nasdaq", sl.noise_area_v2(s, "nasdaq"), b, rng, z_need)}
            print(asset, out[asset]["zone_v2_locale"]["R"], out[asset]["noise_area_v2_prod"]["R"], flush=True)
            continue
        try:
            out[asset] = run_market(asset, rng, z_need)
        except FileNotFoundError as e:
            out[asset] = {"erreur": f"données absentes : {e}"}
            print(asset, "données absentes", flush=True)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    out["updated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    run(sys.argv[1:] or None)
