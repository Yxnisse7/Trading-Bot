"""Essai 76 (HYPOTHESES.md) : peut-on réussir un challenge de prop firm avec nos stratégies prouvées ? (10/11/2026)

T : type Topstep Trading Combine (futures micro, pas de nuit, perte max suiveuse sur la fin de journée).
F : type challenge CFD en 2 phases avec nuits permises (+10 % puis +5 %, perte du jour 5 %, perte totale 10 %).
Un challenge démarre chaque lundi 2014-2025, jusqu'à réussite, échec ou 12 mois ; puis 12 mois en compte financé.

    python -m trading_bot.essai76 trades    → data/history/long/essai76_trades.pkl (après `essai74 trace nasdaq`)
    python -m trading_bot.essai76           → data/essai76.json

Données hors dépôt : data/history/long/{nasdaq,gold}_1m.npz (HistData), btc_5m.npz (Binance), essai74_trace_nasdaq.pkl.
"""
from __future__ import annotations

import json
import os
import pickle
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")

from . import strategies as sl
from .config import DATA_DIR, load_config
from .essai21 import bot_cost
from .essai33 import LONG, Bars

CHI = ZoneInfo("America/Chicago")
OUT = Path(DATA_DIR) / "essai76.json"
TRADES = LONG / "essai76_trades.pkl"
STRATS = {"nasdaq": ("noise_area_v2", "double7"), "gold": ("nuit_asie",),
          "bitcoin": ("donchian_1h", "swing_w3", "cassure_williams")}
MNQ = 2.0                                   # $ par point, micro Nasdaq
SPLIT = date(2020, 1, 1)

T_SIZES = {"50K": (50_000, 3_000, 2_000, 50, 49), "100K": (100_000, 6_000, 3_000, 100, 99),
           "150K": (150_000, 9_000, 4_500, 150, 149)}            # capital, objectif, perte max, micros, $/mois
T_BUDGETS = (100, 200, 300, 400)                                   # $ par trade pour 50K (×2, ×3 au-dessus)
F_RISKS = (0.25, 0.5, 0.75, 1.0)                                   # % du capital de départ par trade
F_FEE = 0.0069                                                     # frais du challenge ≈ 0,69 % du capital (indicatif)
SHARE = 0.9


# ---------------------------------------------------------------- trades

def _bars(asset: str) -> Bars:
    if asset == "bitcoin":
        return Bars.load("btc_5m.npz")
    from .essai72 import load_gold
    return (load_gold() if asset == "gold" else Bars.load("nasdaq_1m.npz")).resample(300)


def _candles(b: Bars):
    from .models import Candle
    return [Candle(int(t), float(o), float(h), float(lo), float(c), 0.0)
            for t, o, h, lo, c in zip(b.ts, b.o, b.h, b.l, b.c)]


def cutoff(ts: int) -> int:
    """15:08 heure de Chicago le jour de séance du trade (séance futures : 17:00 la veille → 15:10)."""
    d = datetime.fromtimestamp(ts, CHI)
    day = d.date() + (timedelta(days=1) if d.time() >= time(17, 0) else timedelta(0))
    return int(datetime.combine(day, time(15, 8), CHI).timestamp())


def resim(b1: Bars, entry_ts: int, entry: float, stop: float, target: float | None, long: bool,
          end_ts: int) -> tuple[int, float]:
    """Rejoue un trade sur les bougies 1 min : stop prioritaire, sortie à la clôture de la bougie de `end_ts`."""
    i = int(np.searchsorted(b1.ts, entry_ts, side="left"))
    j = int(np.searchsorted(b1.ts, end_ts, side="left"))
    for k in range(i, min(j, len(b1.ts))):
        if (b1.l[k] <= stop) if long else (b1.h[k] >= stop):
            return int(b1.ts[k]) + 60, stop
        if target is not None and ((b1.h[k] >= target) if long else (b1.l[k] <= target)):
            return int(b1.ts[k]) + 60, target
    k = max(i, min(j, len(b1.ts)) - 1)
    return int(b1.ts[k]) + 60, float(b1.c[k])


def build_trades() -> list[dict]:
    cfg = load_config()
    rows: list[dict] = []
    for asset, names in STRATS.items():
        cost = bot_cost(asset, cfg)[0]
        for t in sl.run_all(asset, _candles(_bars(asset)), only=list(names)):
            if t.reason == "fin des données" or t.risk <= 0:
                continue
            c = cost(t.entry)
            rows.append({"strat": t.strategy, "asset": asset, "ts": t.entry_ts, "exit_ts": t.exit_ts,
                         "risk": t.risk, "r": (t.gross_points() - c) / t.risk})
        print(asset, sum(1 for r in rows if r["asset"] == asset), flush=True)
    # bot classique Nasdaq : trades de référence de l'essai 74 (24 h), puis version fermée à 15:08 Chicago
    from . import essai74 as e74
    acfg, candles, cost = e74.market("nasdaq", cfg)
    steps = pickle.load(e74.trace_path("nasdaq").open("rb"))
    ref = e74.replay("nasdaq", "REF", steps, candles, acfg, cfg, cost)
    b1 = Bars.load("nasdaq_1m.npz")
    for x in ref:
        row = x["row"]
        ts, entry, stop = int(x["ts"]), float(row["entry"]), float(row["stop_loss"])
        tp = row.get("take_profit")
        long = row["direction"] == "long"
        risk = abs(entry - stop)
        if risk <= 0:
            continue
        c = cost(entry)
        ex24, px24 = resim(b1, ts, entry, stop, tp, long, ts + 86400)
        rows.append({"strat": "bot", "asset": "nasdaq", "ts": ts, "exit_ts": ex24, "risk": risk,
                     "r": ((px24 - entry) * (1 if long else -1) - c) / risk, "r_ref": x["r"]})
        cut = cutoff(ts)
        if cut > ts:
            exc, pxc = resim(b1, ts, entry, stop, tp, long, cut)
            rows.append({"strat": "bot_jour", "asset": "nasdaq", "ts": ts, "exit_ts": exc, "risk": risk,
                         "r": ((pxc - entry) * (1 if long else -1) - c) / risk})
    print("bot", sum(1 for r in rows if r["strat"] == "bot"), flush=True)
    with TRADES.open("wb") as f:
        pickle.dump(rows, f, protocol=5)
    return rows


# ---------------------------------------------------------------- challenges

def day_of(ts: int) -> date:
    """Jour de séance (convention Topstep : la séance commence à 17:00 Chicago la veille)."""
    d = datetime.fromtimestamp(ts, CHI)
    return d.date() + (timedelta(days=1) if d.time() >= time(17, 0) else timedelta(0))


def pnl_events(trades: list[dict], dollars) -> list[tuple[date, float]]:
    """(jour de sortie, gain en $) pour chaque trade pris ; `dollars(trade)` → gain en $ ou None (sauté)."""
    out = []
    busy: dict[str, int] = {}
    for t in sorted(trades, key=lambda x: x["ts"]):
        if busy.get(t["strat"], 0) > t["ts"]:            # un seul trade à la fois par stratégie
            continue
        g = dollars(t)
        if g is None:
            continue
        busy[t["strat"]] = t["exit_ts"]
        out.append((day_of(t["exit_ts"]), g))
    return out


def daily(events: list[tuple[date, float]]) -> list[tuple[date, float]]:
    agg: dict[date, float] = {}
    for d, g in events:
        agg[d] = agg.get(d, 0.0) + g
    return sorted(agg.items())


def run_topstep(days: list[tuple[date, float]], start: date, cap: float, target: float, mll: float,
                months: int = 12) -> dict:
    end = start + timedelta(days=30 * months)
    bal, floor, best, total, ndays = cap, cap - mll, 0.0, 0.0, 0
    for d, g in days:
        if d < start:
            continue
        if d > end:
            break
        bal += g
        ndays += 1
        total = bal - cap
        best = max(best, g)
        if bal <= floor:
            return {"ok": False, "days": (d - start).days, "end": d}
        floor = min(cap, max(floor, bal - mll))
        if total >= target and best < 0.5 * total:
            return {"ok": True, "days": (d - start).days, "end": d}
    return {"ok": False, "days": (end - start).days, "end": end, "timeout": True}


def funded_topstep(days, start: date, cap: float, mll: float, months: int = 12) -> dict:
    """Compte financé : même perte max suiveuse ; gain retiré à la fin (part du trader)."""
    end = start + timedelta(days=30 * months)
    half = start + timedelta(days=182)
    bal, floor, at6 = cap, cap - mll, None
    for d, g in days:
        if d <= start:
            continue
        if d > end:
            break
        if at6 is None and d > half:
            at6 = bal - cap
        bal += g
        if bal <= floor:
            return {"blown": True, "gain6": max(0.0, at6 or 0.0) * SHARE, "gain12": 0.0}
        floor = min(cap, max(floor, bal - mll))
    at6 = bal - cap if at6 is None else at6
    return {"blown": False, "gain6": max(0.0, at6) * SHARE, "gain12": max(0.0, bal - cap) * SHARE}


def run_ftmo(days, start: date, cap: float, months: int = 12) -> dict:
    end = start + timedelta(days=30 * months)
    phase, base, ndays, t0 = 1, cap, 0, start
    for d, g in days:
        if d < t0:
            continue
        if d > end:
            break
        base += g
        ndays += 1
        if g <= -0.05 * cap or base <= 0.9 * cap:
            return {"ok": False, "days": (d - start).days, "end": d}
        goal = 0.10 if phase == 1 else 0.05
        if base - cap >= goal * cap and ndays >= 4:
            if phase == 2:
                return {"ok": True, "days": (d - start).days, "end": d}
            phase, base, ndays, t0 = 2, cap, 0, d + timedelta(days=1)
    return {"ok": False, "days": (end - start).days, "end": end, "timeout": True}


def funded_ftmo(days, start: date, cap: float, months: int = 12) -> dict:
    end, half = start + timedelta(days=30 * months), start + timedelta(days=182)
    bal, at6 = cap, None
    for d, g in days:
        if d <= start:
            continue
        if d > end:
            break
        if at6 is None and d > half:
            at6 = bal - cap
        bal += g
        if g <= -0.05 * cap or bal <= 0.9 * cap:
            return {"blown": True, "gain6": max(0.0, at6 or 0.0) * SHARE, "gain12": 0.0}
    at6 = bal - cap if at6 is None else at6
    return {"blown": False, "gain6": max(0.0, at6) * SHARE, "gain12": max(0.0, bal - cap) * SHARE}


def mondays() -> list[date]:
    d, out = date(2014, 1, 6), []
    while d <= date(2025, 10, 27):
        out.append(d)
        d += timedelta(days=7)
    return out


def summarize(results: list[tuple[date, dict, dict | None]], fee_of) -> dict:
    def part(rs):
        ok = [r for _, r, _ in rs if r["ok"]]
        return round(len(ok) / len(rs), 3) if rs else None
    ok = [(s, r, f) for s, r, f in results if r["ok"]]
    rate = len(ok) / len(results)
    fees = [fee_of(r) for _, r, _ in results]
    cost_per_pass = (sum(fees) / len(fees)) / rate if rate else None
    g6 = [f["gain6"] for _, _, f in ok if f]
    g12 = [f["gain12"] for _, _, f in ok if f]
    blown = [f["blown"] for _, _, f in ok if f]
    first = [x for x in results if x[0] < SPLIT]
    second = [x for x in results if x[0] >= SPLIT]
    out = {"départs": len(results), "réussite": round(rate, 3), "réussite_2014_2019": part(first),
           "réussite_2020_2025": part(second),
           "échecs_temps": round(sum(1 for _, r, _ in results if r.get("timeout")) / len(results), 3),
           "jours_médians_réussite": median([r["days"] for _, r, _ in ok]) if ok else None,
           "coût_moyen_réussite": None if cost_per_pass is None else round(cost_per_pass),
           "financé_gain_médian_6_mois": round(median(g6)) if g6 else None,
           "financé_gain_médian_12_mois": round(median(g12)) if g12 else None,
           "financé_comptes_perdus_12_mois": round(sum(blown) / len(blown), 3) if blown else None}
    out["jouable"] = bool(out["réussite_2014_2019"] is not None and out["réussite_2014_2019"] >= 0.5
                          and (out["réussite_2020_2025"] or 0) >= 0.5 and g6
                          and out["financé_gain_médian_6_mois"] > (out["coût_moyen_réussite"] or 1e18))
    return out


def run() -> dict:
    rows = pickle.load(TRADES.open("rb"))
    starts = mondays()
    res: dict = {"essai": 76, "trades": {}, "T": {}, "F": {}}
    for s in sorted({r["strat"] for r in rows}):
        rs = [r["r"] for r in rows if r["strat"] == s]
        res["trades"][s] = {"n": len(rs), "R_moyen": round(float(np.mean(rs)), 3)}
    portfolios_t = {"T-A zone v2": ("noise_area_v2",), "T-B zone v2 + bot fermé 15:08": ("noise_area_v2", "bot_jour")}
    for pname, strats in portfolios_t.items():
        tr = [r for r in rows if r["strat"] in strats]
        for size, (cap, target, mll, micros, fee) in T_SIZES.items():
            k = cap // 50_000
            for budget in T_BUDGETS:
                b = budget * k

                def dollars(t, b=b, micros=micros):
                    one = t["risk"] * MNQ
                    n = int(b // one)
                    if n == 0:
                        n = 1 if one <= 1.5 * b else 0
                    n = min(n, micros)
                    return None if n == 0 else t["r"] * t["risk"] * MNQ * n
                days = daily(pnl_events(tr, dollars))
                results = []
                for s in starts:
                    r = run_topstep(days, s, cap, target, mll)
                    f = funded_topstep(days, r["end"], cap, mll) if r["ok"] else None
                    results.append((s, r, f))
                row = summarize(results, lambda r, fee=fee: fee * (r["days"] // 30 + 1))
                row["trades_par_mois"] = round(len(days) and sum(1 for _ in pnl_events(tr, dollars)) / (12.8 * 12), 1)
                res["T"][f"{pname} | {size} | {b} $/trade"] = row
                print(pname, size, b, row["réussite"], row["jouable"], flush=True)
    portfolios_f = {"F-A toutes en réel": ("noise_area_v2", "double7", "bot", "donchian_1h", "swing_w3",
                                           "cassure_williams", "nuit_asie"),
                    "F-B Nasdaq seul": ("noise_area_v2", "double7", "bot")}
    cap = 100_000
    for pname, strats in portfolios_f.items():
        tr = [r for r in rows if r["strat"] in strats]
        for risk in F_RISKS:
            def dollars(t, risk=risk):
                return t["r"] * risk / 100 * cap
            days = daily(pnl_events(tr, dollars))
            results = []
            for s in starts:
                r = run_ftmo(days, s, cap)
                f = funded_ftmo(days, r["end"], cap) if r["ok"] else None
                results.append((s, r, f))
            row = summarize(results, lambda r: F_FEE * cap)
            res["F"][f"{pname} | {risk} %/trade"] = row
            print(pname, risk, row["réussite"], row["jouable"], flush=True)
    res["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    if sys.argv[1:2] == ["trades"]:
        build_trades()
    else:
        run()
