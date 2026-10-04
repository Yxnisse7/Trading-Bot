"""Setups d'entrée pré-enregistrés (voir HYPOTHESES.md), testés en backtest et en ombre.

Contrairement au score de critères du bot, chaque setup porte UNE idée, avec quelques réglages en
chiffres ronds, un stop placé sur une structure de prix et des critères d'abandon écrits d'avance.

- setup_repli : repli dans une tendance forte (ADX 15 min ≥ 30) vers l'EMA 20, entrée à la reprise.
- setup_vwap  : sans tendance (ADX 15 min < 20), prix à plus de 2 ATR de la VWAP du jour, retour visé.

Sans biais de futur : les indicateurs sont calculés une fois sur toute la série, mais à la bougie i
on ne lit que des valeurs déjà connues à sa clôture (bougies 15 min entièrement closes, VWAP cumulée
jusqu'à i incluse).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from . import indicators as ind
from .config import AssetConfig
from .models import Candle, Signal, iso, parse_iso
from .tracker import close_signal, resolve_with_candles

SETUPS = {
    "setup_repli": "setup A : repli dans une tendance forte",
    "setup_vwap": "setup B : retour à la VWAP sans tendance",
}
WINDOW = 6            # bougies regardées pour le repli et pour le stop
HOLD_BARS = 24        # durée maximale : 2 h
WARMUP = 300          # bougies avant de juger (EMA 50 et ADX en 15 min disponibles)


@dataclass
class Prepared:
    candles: list[Candle]
    ema20: list[float | None]
    atr: list[float | None]
    adx15: list[float | None]          # valeur de la dernière bougie 15 min close, alignée sur chaque bougie 5 min
    pdi15: list[float | None]
    mdi15: list[float | None]
    ema50_15: list[float | None]
    vwap: list[float | None]


def prepare(candles: list[Candle]) -> Prepared:
    closes = [c.close for c in candles]
    ema20 = ind.ema(closes, 20)
    atr = ind.atr(candles, 14)
    c15 = ind.resample(candles, 15)
    adx, pdi, mdi = ind.adx(c15, 14)
    ema50 = ind.ema([c.close for c in c15], 50)
    adx15, pdi15, mdi15, e50 = [], [], [], []
    k = -1
    for c in candles:
        # dernière bougie 15 min entièrement close à la clôture de cette bougie 5 min
        while k + 1 < len(c15) and c15[k + 1].ts + 900 <= c.ts + 300:
            k += 1
        ok = k >= 0
        adx15.append(adx[k] if ok else None)
        pdi15.append(pdi[k] if ok else None)
        mdi15.append(mdi[k] if ok else None)
        e50.append(ema50[k] if ok else None)
    # VWAP du jour (UTC), cumulée jusqu'à la bougie incluse ; volume nul : moyenne simple du prix typique
    vwap: list[float | None] = []
    day, pv, vol, tp_sum, n = None, 0.0, 0.0, 0.0, 0
    for c in candles:
        d = c.ts // 86400
        if d != day:
            day, pv, vol, tp_sum, n = d, 0.0, 0.0, 0.0, 0
        tp = (c.high + c.low + c.close) / 3.0
        pv += tp * c.volume
        vol += c.volume
        tp_sum += tp
        n += 1
        vwap.append(pv / vol if vol > 0 else tp_sum / n)
    return Prepared(candles, ema20, atr, adx15, pdi15, mdi15, e50, vwap)


def detect(p: Prepared, i: int, setup: str) -> dict[str, Any] | None:
    """Setup déclenché à la clôture de la bougie i ? Renvoie direction, entrée, stop, objectif."""
    if i < max(WARMUP, WINDOW) or i >= len(p.candles):
        return None
    c, prev = p.candles[i], p.candles[i - 1]
    atr, adx, e20 = p.atr[i], p.adx15[i], p.ema20[i]
    if not atr or adx is None or e20 is None:
        return None
    lows = [x.low for x in p.candles[i - WINDOW + 1: i + 1]]
    highs = [x.high for x in p.candles[i - WINDOW + 1: i + 1]]
    entry = c.close
    if setup == "setup_repli":
        pdi, mdi, e50 = p.pdi15[i], p.mdi15[i], p.ema50_15[i]
        if adx < 30 or pdi is None or mdi is None or e50 is None:
            return None
        if pdi > mdi and entry > e50:
            touched = any(p.candles[j].low <= (p.ema20[j] or 0) for j in range(i - WINDOW + 1, i + 1))
            if touched and entry > e20 and entry > prev.high:
                stop = min(lows) - 0.1 * atr
                risk = entry - stop
                if 0.5 * atr <= risk <= 2.5 * atr:
                    return {"direction": "long", "entry": entry, "stop": stop, "target": entry + 1.5 * risk}
        if mdi > pdi and entry < e50:
            touched = any(p.candles[j].high >= (p.ema20[j] or float("inf")) for j in range(i - WINDOW + 1, i + 1))
            if touched and entry < e20 and entry < prev.low:
                stop = max(highs) + 0.1 * atr
                risk = stop - entry
                if 0.5 * atr <= risk <= 2.5 * atr:
                    return {"direction": "short", "entry": entry, "stop": stop, "target": entry - 1.5 * risk}
        return None
    if setup == "setup_vwap":
        vw = p.vwap[i]
        if adx >= 20 or vw is None:
            return None
        if entry - vw > 2 * atr and entry < prev.low:
            stop = max(highs) + 0.1 * atr
            risk, reward = stop - entry, entry - vw
            if risk > 0 and reward >= risk:
                return {"direction": "short", "entry": entry, "stop": stop, "target": vw}
        if vw - entry > 2 * atr and entry > prev.high:
            stop = min(lows) - 0.1 * atr
            risk, reward = entry - stop, vw - entry
            if risk > 0 and reward >= risk:
                return {"direction": "long", "entry": entry, "stop": stop, "target": vw}
        return None
    raise ValueError(f"setup inconnu : {setup}")


def make_signal(asset: AssetConfig, setup: str, hit: dict[str, Any], now: datetime, source: str) -> Signal:
    entry, sl, tp = hit["entry"], hit["stop"], hit["target"]
    rr = abs(tp - entry) / abs(entry - sl) if entry != sl else 0.0
    d = asset.price_decimals
    return Signal(
        id=uuid.uuid4().hex[:10], asset=asset.key, asset_label=asset.label, direction=hit["direction"],
        entry=round(entry, d), take_profit=round(tp, d), stop_loss=round(sl, d), risk_reward=round(rr, 2),
        confidence="moyen", score=0.0, criteria=[setup], rationale=SETUPS[setup], news_context="",
        created_at=iso(now), expires_at=iso(now + timedelta(minutes=5 * HOLD_BARS)),
        source=source, horizon="2h", horizon_minutes=5 * HOLD_BARS, meta={"setup": setup, "variant": setup},
    )


def run_setup_backtest(asset: AssetConfig, candles: list[Candle], setup: str,
                       start_ts: int | None = None) -> list[Signal]:
    """Rejoue un setup sur toute la série : une position à la fois, session de l'actif respectée,
    issue sur les 24 bougies suivantes (SL prioritaire si TP et SL dans la même bougie), frais déduits."""
    p = prepare(candles)
    out: list[Signal] = []
    i, n = WARMUP, len(candles)
    while i < n - 1:
        c = candles[i]
        now = datetime.fromtimestamp(c.ts + 300, tz=timezone.utc)
        if start_ts is not None and c.ts < start_ts:
            i += 1
            continue
        if asset.session_utc and not (asset.session_utc[0] <= now.hour < asset.session_utc[1]):
            i += 1
            continue
        hit = detect(p, i, setup)
        if hit is None:
            i += 1
            continue
        sig = make_signal(asset, setup, hit, now, "backtest")
        future = candles[i + 1: i + 1 + HOLD_BARS]
        if not future:
            break
        outcome = resolve_with_candles(sig, future)
        if outcome is None:
            last = future[-1]
            close_signal(sig, "expired", last.close, datetime.fromtimestamp(last.ts + 300, tz=timezone.utc), asset.cost_pct)
        else:
            close_signal(sig, outcome[0], outcome[1], outcome[2], asset.cost_pct)
        out.append(sig)
        # une seule position à la fois : on reprend après la sortie
        end = parse_iso(sig.closed_at).timestamp() if sig.closed_at else c.ts + 300 * HOLD_BARS
        while i < n and candles[i].ts + 300 <= end:
            i += 1
    return out


# ---------------------------------------------------------------- évaluation (critères de HYPOTHESES.md)
KILL = {"min_trades": 100, "min_profit_factor": 1.1, "min_second_half_ratio": 0.5,
        "min_robustness": 0.6, "min_plateau": 0.5}


def _stats(rs: list[float]) -> dict[str, Any]:
    if not rs:
        return {"n": 0, "mean_r": None, "profit_factor": None, "win_rate": None, "total_r": None}
    gains, losses = sum(r for r in rs if r > 0), -sum(r for r in rs if r < 0)
    return {"n": len(rs), "mean_r": round(sum(rs) / len(rs), 4),
            "profit_factor": round(gains / losses, 2) if losses > 0 else None,
            "win_rate": round(sum(1 for r in rs if r > 0) / len(rs), 4), "total_r": round(sum(rs), 2)}


def evaluate(assets: dict[str, AssetConfig], candles_by_asset: dict[str, list[Candle]], source: str) -> dict[str, Any]:
    """Backtest des deux setups sur chaque actif, moitiés chronologiques, tests de résistance, verdict."""
    from .learning import trade_r
    from .stress import stress_test

    out: dict[str, Any] = {"source": source, "setups": {}}
    for setup, label in SETUPS.items():
        results, rows = {}, []
        per_asset = {}
        for key, candles in candles_by_asset.items():
            if key not in assets or len(candles) < WARMUP + HOLD_BARS:
                continue
            sigs = run_setup_backtest(assets[key], candles, setup)
            results[key] = {"asset": key, "trades": [s.to_dict() for s in sigs]}
            rs = [(s.created_at, trade_r(s, net=True)) for s in sigs]
            rs = [(t, r) for t, r in rs if r is not None]
            rows += rs
            per_asset[key] = _stats([r for _, r in rs]) | {
                "period": f"{datetime.fromtimestamp(candles[0].ts, tz=timezone.utc):%d/%m/%Y} → "
                          f"{datetime.fromtimestamp(candles[-1].ts, tz=timezone.utc):%d/%m/%Y}"}
        rows.sort()
        half = len(rows) // 2
        first, second = _stats([r for _, r in rows[:half]]), _stats([r for _, r in rows[half:]])
        total = _stats([r for _, r in rows])
        stress = stress_test(results, candles_by_asset, {k: a.cost_pct for k, a in assets.items()}) if rows else {}
        checks = {
            "échantillon ≥ 100 trades": total["n"] >= KILL["min_trades"],
            "gain net moyen > 0": (total["mean_r"] or 0) > 0,
            "facteur de profit ≥ 1,1": (total["profit_factor"] or 0) >= KILL["min_profit_factor"],
            "même signe dans les deux moitiés": bool(first["mean_r"] and second["mean_r"]
                                                    and first["mean_r"] * second["mean_r"] > 0),
            "2de moitié ≥ 50 % de la 1re": bool(first["mean_r"] and second["mean_r"] and first["mean_r"] > 0
                                                and second["mean_r"] >= KILL["min_second_half_ratio"] * first["mean_r"]),
            "≥ 60 % des scénarios dégradés gagnants": (stress.get("robustness") or 0) >= KILL["min_robustness"],
            "≥ 50 % des réglages stop × objectif gagnants": (stress.get("plateau") or 0) >= KILL["min_plateau"],
        }
        passed = all(checks.values())
        out["setups"][setup] = {
            "label": label, "total": total, "first_half": first, "second_half": second, "by_asset": per_asset,
            "stress": {k: stress.get(k) for k in ("scenarios", "grid", "grid_sl", "grid_tp", "robustness", "plateau")},
            "checks": checks, "passed": passed,
            "verdict": "à suivre en ombre" if passed else "abandon (critères non remplis)",
        }
    return out
