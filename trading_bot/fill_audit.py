"""Faisabilité des prix d'exécution du backtest (skill fill-feasibility-and-impossible-fill-detection).

Lancé après chaque backtest complet, sur les mêmes bougies 5 min. Pour chaque trade clos, on vérifie :
  - le prix de sortie est-il dans la bougie de sortie (entre son plus bas et son plus haut) ?
  - saut de prix : la bougie ouvre déjà au-delà du stop. Le backtest compte le stop exact, alors qu'un ordre
    stop serait exécuté à l'ouverture, plus loin : on mesure ce coût en R ;
  - même bougie : objectif et stop touchés dans la même bougie (le backtest compte le stop, par prudence) ;
  - stop minuscule : moins de 4 ticks entre l'entrée et le stop (irréalisable avec un tick de glissement) ;
  - entrée : écart entre le prix d'entrée du backtest (clôture de la bougie du signal) et l'ouverture de la
    bougie suivante, la première où un ordre réel peut passer.
Le volume n'est pas vérifié : 1 à 50 micro-contrats restent très loin du volume des contrats CME, et les
volumes Yahoo et CFD ne sont pas ceux du contrat Topstep.
"""
from __future__ import annotations

from typing import Any

from .models import Candle, parse_iso

MIN_TICKS = 4


def audit_trade(t: dict[str, Any], candles: list[Candle], index: dict[int, int], tick: float | None) -> dict[str, Any] | None:
    if t.get("status") not in ("tp", "sl", "expired") or not t.get("entry") or not t.get("stop_loss"):
        return None
    entry, stop, target = float(t["entry"]), float(t["stop_loss"]), float(t["take_profit"])
    risk = abs(entry - stop)
    long = t["direction"] == "long"
    created = int(parse_iso(t["created_at"]).timestamp())
    # trades allégés de backtest_trades.json : sortie déduite de la durée et du résultat brut
    closed = int(parse_iso(t["closed_at"]).timestamp()) if t.get("closed_at") else (
        created + 60 * int(t["duration_minutes"]) if t.get("duration_minutes") is not None else None)
    px = t.get("close_price")
    if px is None and t.get("pnl_gross_pct") is not None:
        px = {"tp": target, "sl": stop}.get(t["status"], entry * (1 + (1 if long else -1) * t["pnl_gross_pct"] / 100))
    if risk <= 0 or closed is None or px is None:
        return None
    out: dict[str, Any] = {"status": t["status"], "gap_r": 0.0, "gap": False, "both": False, "outside": False,
                           "tiny": bool(tick and risk < MIN_TICKS * tick), "entry_r": None}
    i = index.get(created - 300)
    if i is not None and i + 1 < len(candles):
        out["entry_r"] = ((candles[i + 1].open - entry) if long else (entry - candles[i + 1].open)) / risk
    k = index.get(closed) if t["status"] != "expired" else index.get(closed - 300)
    if k is None:
        return out
    b, px = candles[k], float(px)
    tol = max(tick / 2 if tick else 0.0, abs(px) * 2e-6)      # demi-tick, et arrondi des résultats enregistrés
    out["outside"] = not (b.low - tol <= px <= b.high + tol)
    if t["status"] == "sl":
        out["gap"] = (b.open < stop - tol) if long else (b.open > stop + tol)
        if out["gap"]:
            out["gap_r"] = -abs(stop - b.open) / risk
        out["both"] = (b.high >= target) if long else (b.low <= target)
    return out


def audit(results: dict[str, Any], candles_by_asset: dict[str, list[Candle]],
          tick_by_asset: dict[str, float | None]) -> dict[str, Any]:
    """`results` : sortie du backtest (clé → résultat avec ses trades)."""
    per: dict[str, list[dict[str, Any]]] = {}
    for res in results.values():
        key = res.get("asset")
        candles = candles_by_asset.get(key)
        if not candles:
            continue
        index = {c.ts: i for i, c in enumerate(candles)}
        rows = [a for a in (audit_trade(t, candles, index, tick_by_asset.get(key)) for t in res.get("trades", [])) if a]
        per.setdefault(key, []).extend(rows)

    def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(rows)
        sl = [r for r in rows if r["status"] == "sl"]
        gaps = [r for r in rows if r["gap"]]
        entries = [r["entry_r"] for r in rows if r["entry_r"] is not None]
        return {"n": n, "sl": len(sl), "outside": sum(r["outside"] for r in rows), "gaps": len(gaps),
                "gap_cost_r": round(sum(r["gap_r"] for r in rows) / n, 4) if n else None,
                "worst_gap_r": round(min((r["gap_r"] for r in gaps), default=0.0), 3),
                "both": sum(r["both"] for r in sl), "tiny": sum(r["tiny"] for r in rows),
                "entry_r": round(sum(entries) / len(entries), 4) if entries else None}

    all_rows = [r for rows in per.values() for r in rows]
    if not all_rows:
        return {}
    return {"total": summary(all_rows), "assets": {k: summary(v) for k, v in per.items()}}


def _span(candles: list[Candle], ts: list[int], start: int, end: int) -> tuple[float, float, Candle | None]:
    """Plus bas, plus haut et première bougie 5 min de [start, end)."""
    from bisect import bisect_left
    a, b = bisect_left(ts, start), bisect_left(ts, end)
    if a >= b:
        return float("nan"), float("nan"), None
    part = candles[a:b]
    return min(c.low for c in part), max(c.high for c in part), part[0]


def audit_lab(trades: list, candles: list[Candle], tick: float | None, hourly: set[str]) -> dict[str, Any]:
    """Stratégies du laboratoire (strategies.simulate) : entrée et sortie dans leur bougie (1 h ou 5 min),
    écart entre l'entrée et l'ouverture suivante (première exécution possible d'un ordre au marché)."""
    ts = [c.ts for c in candles]
    rows = []
    for t in trades:
        if t.reason == "fin des données" or t.risk <= 0:
            continue
        sec = 3600 if t.strategy in hourly else 300
        tol = max(tick / 2 if tick else 0.0, abs(t.exit) * 2e-6)
        lo, hi, _ = _span(candles, ts, t.exit_ts - sec, t.exit_ts)
        elo, ehi, _ = _span(candles, ts, t.entry_ts - sec, t.entry_ts)
        _, _, nxt = _span(candles, ts, t.entry_ts, t.entry_ts + 4 * 86400)
        sign = 1 if t.direction == "long" else -1
        rows.append({"strategy": t.strategy, "outside": not (lo - tol <= t.exit <= hi + tol),
                     "entry_outside": not (elo - tol <= t.entry <= ehi + tol),
                     "entry_r": sign * (nxt.open - t.entry) / t.risk if nxt else None,
                     "tiny": bool(tick and t.risk < MIN_TICKS * tick)})
    out: dict[str, Any] = {}
    for name in sorted({r["strategy"] for r in rows}):
        rs = [r for r in rows if r["strategy"] == name]
        e = [r["entry_r"] for r in rs if r["entry_r"] is not None]
        out[name] = {"n": len(rs), "outside": sum(r["outside"] for r in rs),
                     "entry_outside": sum(r["entry_outside"] for r in rs), "tiny": sum(r["tiny"] for r in rs),
                     "entry_r": round(sum(e) / len(e), 4) if e else None,
                     "entry_r_big": sum(1 for x in e if x > 0.25)}
    return out
