"""Tests de résistance du backtest (méthode « backtest-expert » : chercher ce qui casse la stratégie).

Les trades du backtest sont rejoués sur les mêmes bougies 5 min dans des conditions moins favorables :
frais plus élevés, stop et objectif déplacés, entrée retardée (sur Topstep, l'entrée arrive plusieurs
minutes après le signal, les données Yahoo des contrats CME ayant 10 min de retard). Une stratégie
robuste reste rentable sur une large zone de réglages (« plateau ») ; une stratégie fragile ne tient
qu'à un réglage précis.

Conventions (identiques au backtest) : SL prioritaire si TP et SL sont touchés dans la même bougie,
expiration à l'heure prévue du signal. Entrée retardée : les niveaux notifiés (TP, SL) restent ceux
du signal, la taille aussi ; si le prix a déjà dépassé l'un d'eux à l'entrée, le trade est « manqué ».
Le résultat est exprimé en R du risque prévu (distance stop ajustée du scénario).
"""
from __future__ import annotations

from typing import Any

from .models import Candle, parse_iso

SCENARIOS: list[tuple[str, str, dict[str, float]]] = [
    ("base", "Référence (backtest)", {}),
    ("frais_1_5", "Frais × 1,5", {"cost": 1.5}),
    ("frais_2", "Frais × 2", {"cost": 2.0}),
    ("stop_50", "Stop 50 % plus serré", {"sl": 0.5}),
    ("stop_75", "Stop 25 % plus serré", {"sl": 0.75}),
    ("stop_125", "Stop 25 % plus large", {"sl": 1.25}),
    ("stop_150", "Stop 50 % plus large", {"sl": 1.5}),
    ("tp_75", "Objectif 25 % plus proche", {"tp": 0.75}),
    ("tp_125", "Objectif 25 % plus loin", {"tp": 1.25}),
    ("retard_1", "Entrée 5 min plus tard", {"delay": 1}),
    ("retard_2", "Entrée 10 min plus tard", {"delay": 2}),
    ("pire", "Entrée 10 min plus tard + frais × 2", {"delay": 2, "cost": 2.0}),
]
GRID_SL = (0.5, 0.75, 1.0, 1.25, 1.5)
GRID_TP = (0.75, 1.0, 1.25)


def replay(t: dict[str, Any], candles: list[Candle], index: dict[int, int], cost_pct: float, *,
           sl: float = 1.0, tp: float = 1.0, delay: int = 0, cost: float = 1.0) -> float | str | None:
    """Résultat net (en R) d'un trade de backtest rejoué ; « missed » si l'entrée retardée arrive trop tard,
    None si les bougies manquent."""
    created = int(parse_iso(t["created_at"]).timestamp())
    i = index.get(created - 300)                     # bougie dont la clôture a déclenché le signal
    if i is None or not t.get("entry") or not t.get("stop_loss") or not t.get("take_profit"):
        return None
    sign = 1.0 if t["direction"] == "long" else -1.0
    entry0 = float(t["entry"])
    risk = abs(entry0 - float(t["stop_loss"])) * sl
    stop = entry0 - sign * risk
    target = entry0 + sign * abs(float(t["take_profit"]) - entry0) * tp
    if risk <= 0:
        return None
    j = i + int(delay)
    if j >= len(candles):
        return None
    entry = entry0 if not delay else candles[j].close
    if delay and (sign * (entry - target) >= 0 or sign * (entry - stop) <= 0):
        return "missed"
    expiry = int(parse_iso(t["expires_at"]).timestamp()) if t.get("expires_at") else created + 3600
    exit_px = None
    last = None
    for c in candles[j + 1:]:
        if c.ts >= expiry:                            # la bougie qui ouvre à l'expiration n'en fait plus partie
            break
        last = c
        hit_sl = c.low <= stop if sign > 0 else c.high >= stop
        hit_tp = c.high >= target if sign > 0 else c.low <= target
        if hit_sl:
            exit_px = stop
            break
        if hit_tp:
            exit_px = target
            break
    if exit_px is None:
        if last is None:
            return None
        exit_px = last.close                          # expiration
    # en points, comme sur un contrat à terme : même taille de position qu'au signal
    net_points = sign * (exit_px - entry) - cost_pct * cost / 100.0 * entry
    return net_points / risk


def _summary(rs: list[float], missed: int) -> dict[str, Any]:
    if not rs:
        return {"n": 0, "missed": missed, "mean_r": None, "total_r": None, "win_rate": None, "profit_factor": None}
    gains, losses = sum(r for r in rs if r > 0), -sum(r for r in rs if r < 0)
    return {"n": len(rs), "missed": missed, "mean_r": round(sum(rs) / len(rs), 4), "total_r": round(sum(rs), 2),
            "win_rate": round(sum(1 for r in rs if r > 0) / len(rs), 4),
            "profit_factor": round(gains / losses, 2) if losses > 0 else None}


def _run(trades: list[tuple[dict, list[Candle], dict[int, int], float]], **kw) -> dict[str, Any]:
    rs, missed = [], 0
    for t, candles, index, cost_pct in trades:
        r = replay(t, candles, index, cost_pct, **kw)
        if r == "missed":
            missed += 1
        elif r is not None:
            rs.append(r)
    return _summary(rs, missed)


def stress_test(results: dict[str, Any], candles_by_asset: dict[str, list[Candle]],
                cost_by_asset: dict[str, float]) -> dict[str, Any]:
    """`results` : sortie du backtest (clé → résultat avec ses trades). Renvoie scénarios, grille et verdict."""
    trades = []
    indexes = {k: {c.ts: i for i, c in enumerate(cs)} for k, cs in candles_by_asset.items()}
    for res in results.values():
        key = res.get("asset")
        if key not in candles_by_asset:
            continue
        for t in res.get("trades", []):
            trades.append((t, candles_by_asset[key], indexes[key], cost_by_asset.get(key, 0.0)))
    if not trades:
        return {}
    scenarios = []
    for key, label, kw in SCENARIOS:
        scenarios.append({"key": key, "label": label, **_run(trades, **kw)})
    grid = [{"sl": s, "tp": p, **{k: v for k, v in _run(trades, sl=s, tp=p).items() if k in ("n", "mean_r")}}
            for s in GRID_SL for p in GRID_TP]
    base = scenarios[0]["mean_r"]
    others = [s for s in scenarios[1:] if s["mean_r"] is not None]
    profitable = sum(1 for s in others if s["mean_r"] > 0)
    grid_ok = [g for g in grid if g["mean_r"] is not None]
    plateau = sum(1 for g in grid_ok if g["mean_r"] > 0) / len(grid_ok) if grid_ok else None
    robustness = profitable / len(others) if others else None
    if base is None or base <= 0:
        verdict, text = "aucun_avantage", ("La stratégie perd déjà dans le backtest de référence : il n'y a pas "
                                           "encore d'avantage à protéger. Les scénarios montrent jusqu'où ça empire.")
    elif robustness is not None and robustness >= 0.6 and (plateau or 0) >= 0.6:
        verdict, text = "robuste", ("Le gain résiste à la plupart des conditions dégradées et à une large zone "
                                    "de réglages : bon signe, à confirmer en réel.")
    elif robustness is not None and robustness >= 0.3:
        verdict, text = "fragile", ("Le gain ne tient que dans une partie des scénarios : l'avantage dépend "
                                    "de réglages ou de conditions précises.")
    else:
        verdict, text = "tres_fragile", ("Le gain disparaît dès que les conditions se dégradent : "
                                         "probablement un réglage chanceux plutôt qu'un vrai avantage.")
    return {"n_trades": len(trades), "scenarios": scenarios, "grid": grid, "grid_sl": list(GRID_SL),
            "grid_tp": list(GRID_TP), "robustness": round(robustness, 3) if robustness is not None else None,
            "plateau": round(plateau, 3) if plateau is not None else None, "verdict": verdict, "verdict_text": text}
