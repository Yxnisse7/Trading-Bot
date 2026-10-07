"""Essai 10 (HYPOTHESES.md) : la règle `donchian_day` sur 17 autres contrats CME, avec leurs frais TopstepX.

Données : Yahoo Finance, bougies de 1 h des contrats « =F » (contrat le plus proche), environ 2 ans et demi,
gardées hors du dépôt (`data/history/<marché>_1h.json`). La règle n'est pas modifiée : seule la liste des
marchés change. Contrôles fixés d'avance : changements de contrat (séances avec un saut d'ouverture), et
« jouable » (le stop d'un seul contrat ne dépasse pas le risque visé).
"""
from __future__ import annotations

import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DATA_DIR
from .models import Candle, iso, utcnow

# marché : (symbole Yahoo, nom, contrat Topstep, frais aller-retour $, valeur d'un tick $, valeur d'un point $)
MARKETS: dict[str, tuple[str, str, str, float, float, float]] = {
    "silver": ("SI=F", "Argent", "SIL", 2.72, 5.0, 1_000.0),
    "copper": ("HG=F", "Cuivre", "MHG", 1.92, 1.25, 2_500.0),
    "platinum": ("PL=F", "Platine", "PL", 4.32, 5.0, 50.0),
    "crude": ("CL=F", "Pétrole", "MCL", 1.92, 1.0, 100.0),
    "natgas": ("NG=F", "Gaz naturel", "MNG", 2.12, 1.0, 1_000.0),
    "heating_oil": ("HO=F", "Fioul", "HO", 4.02, 4.2, 42_000.0),
    "gasoline": ("RB=F", "Essence", "RB", 4.02, 4.2, 42_000.0),
    "tnote10": ("ZN=F", "Taux US 10 ans", "ZN", 2.62, 15.625, 1_000.0),
    "tbond30": ("ZB=F", "Taux US 30 ans", "ZB", 2.76, 31.25, 1_000.0),
    "corn": ("ZC=F", "Maïs", "ZC", 5.28, 12.5, 50.0),
    "soybeans": ("ZS=F", "Soja", "ZS", 5.28, 12.5, 50.0),
    "wheat": ("ZW=F", "Blé", "ZW", 5.28, 12.5, 50.0),
    "eur": ("6E=F", "Euro", "M6E", 1.00, 1.25, 12_500.0),
    "gbp": ("6B=F", "Livre sterling", "M6B", 1.00, 0.625, 6_250.0),
    "aud": ("6A=F", "Dollar australien", "M6A", 1.00, 1.0, 10_000.0),
    "jpy": ("6J=F", "Yen", "6J", 4.22, 6.25, 12_500_000.0),
    "cad": ("6C=F", "Dollar canadien", "6C", 4.22, 5.0, 100_000.0),
}
CONTROL = {"gold_yahoo": ("GC=F", "Or (contrôle, données Yahoo)", "MGC", 1.92, 1.0, 10.0)}
N_TRIALS = 94
SPLIT = datetime(2025, 9, 28, tzinfo=timezone.utc)
JUMP_FACTOR = 5.0          # séance « avec saut » : écart d'ouverture > 5 fois l'écart médian du marché
JUMP_BARS = 3              # trades entrés dans les 3 premières bougies de ces séances : retirés au contrôle
TRADABLE_SHARE = 0.80


def history_file(key: str) -> Path:
    return Path(DATA_DIR) / "history" / f"{key}_1h.json"


def fetch_1h(symbol: str, get=None) -> list[Candle]:
    """Bougies de 1 h sur 730 jours. Le dernier point de Yahoo (cotation en cours, horodatage non aligné sur la
    minute) est écarté ; les bougies décalées d'une demi-heure (céréales) sont gardées."""
    if get is None:
        from .providers.http import get_json as get
    data = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
               params={"interval": "60m", "range": "730d", "includePrePost": "false"}, timeout=60)
    r = data["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    out = []
    for i, t in enumerate(r["timestamp"]):
        o, h, lo, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
        if None in (o, h, lo, c) or int(t) % 60:
            continue
        out.append(Candle(int(t), float(o), float(h), float(lo), float(c), float((q.get("volume") or [0] * (i + 1))[i] or 0)))
    return out


def load(key: str, symbol: str, refresh: bool = False, get=None) -> list[Candle]:
    f = history_file(key)
    if f.exists() and not refresh:
        return [Candle(*r) for r in json.loads(f.read_text(encoding="utf-8"))]
    candles = fetch_1h(symbol, get)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps([[c.ts, c.open, c.high, c.low, c.close, c.volume] for c in candles]), encoding="utf-8")
    return candles


def jump_entries(candles: list[Candle]) -> set[int]:
    """Horodatages de fin des 3 premières bougies des séances qui s'ouvrent avec un saut (changement de
    contrat possible) : un trade entré à ces moments est retiré au contrôle."""
    starts = [i for i in range(1, len(candles)) if candles[i].ts - candles[i - 1].ts > 3600]
    gaps = [abs(candles[i].open - candles[i - 1].close) for i in starts]
    med = statistics.median(gaps) if gaps else 0.0
    out: set[int] = set()
    for i, g in zip(starts, gaps):
        if med > 0 and g > JUMP_FACTOR * med:
            for k in range(i, min(i + JUMP_BARS, len(candles))):
                out.add(candles[k].ts + 3600)
    return out


def evaluate_market(key: str, spec: tuple, candles: list[Candle]) -> dict[str, Any]:
    from . import strategies as sl
    from .topstep_odds import holding_stats, weekdays_between
    _sym, label, product, fee, tick, pv = spec
    tcost = (fee + tick, pv)
    tr = sorted((t for t in sl.donchian_day(candles, key) if t.reason != "fin des données"), key=lambda t: t.entry_ts)
    split = int(SPLIT.timestamp())
    disc = sl.evaluate(tr, 0.0, tcost, start_ts=split)
    conf = sl.evaluate(tr, 0.0, tcost, end_ts=split)
    both = sl.evaluate(tr, 0.0, tcost)
    ok = sl.discovery_pass(disc) and sl.confirmation_pass(conf)
    jumps = jump_entries(candles)
    clean = [t for t in tr if t.entry_ts not in jumps]
    ok_clean = sl.discovery_pass(sl.evaluate(clean, 0.0, tcost, start_ts=split)) and \
        sl.confirmation_pass(sl.evaluate(clean, 0.0, tcost, end_ts=split))
    stops = sorted(t.risk * pv for t in tr)
    tradable = {str(r): (sum(1 for x in stops if x <= r) / len(stops) >= TRADABLE_SHARE) if stops else False
                for r in (250, 500)}
    if ok and ok_clean:
        status = "prouvé" if sl.proven(both, N_TRIALS) else "validé"
    elif ok:
        status = "écarté (sauts de contrat)"
    else:
        status = "écarté (découverte)" if not sl.discovery_pass(disc) else "écarté (confirmation)"
    start = datetime.fromtimestamp(candles[0].ts, timezone.utc)
    end = datetime.fromtimestamp(candles[-1].ts, timezone.utc)
    return {"key": key, "label": label, "product": product, "fees": fee + tick, "status": status,
            "discovery": disc, "confirmation": conf, "all": both, "trades_removed_jumps": len(tr) - len(clean),
            "median_stop_usd": round(statistics.median(stops), 1) if stops else None, "tradable": tradable,
            "holding": holding_stats(tr), "trades_per_day": round(len(tr) / weekdays_between(start, end), 3),
            "period": [iso(start)[:10], iso(end)[:10]],
            "r": [(t.entry_ts, round(sl.trade_rs(t, 0.0, tcost)["net_topstep"], 4)) for t in tr]}


def run(refresh: bool = False, get=None, engine=None, pause: float = 0.5) -> dict[str, Any]:
    from .topstep_odds import run_engine, weekdays_between
    engine = engine or run_engine
    cells: dict[str, Any] = {}
    for key, spec in {**MARKETS, **CONTROL}.items():
        try:
            candles = load(key, spec[0], refresh, get)
        except Exception as exc:  # noqa: BLE001 — un marché indisponible n'arrête pas l'essai
            cells[key] = {"key": key, "label": spec[1], "status": f"données indisponibles ({str(exc)[:80]})"}
            continue
        if len(candles) < 500:
            cells[key] = {"key": key, "label": spec[1], "status": "historique trop court"}
            continue
        cells[key] = evaluate_market(key, spec, candles)
        if pause:
            time.sleep(pause)
    keep = [k for k, c in cells.items() if k in MARKETS and c.get("status") in ("validé", "prouvé")
            and c["tradable"].get("500")]
    basket = keep + (["gold_yahoo"] if "r" in cells.get("gold_yahoo", {}) else [])
    out: dict[str, Any] = {"essai": 10, "split": SPLIT.date().isoformat(), "n_trials": N_TRIALS,
                           "updated_at": iso(utcnow()), "portfolio": None,
                           "markets": {k: {kk: vv for kk, vv in c.items() if kk != "r"} for k, c in cells.items()}}
    if keep:
        rows = sorted(x for k in basket for x in cells[k]["r"])
        rs = [r for _, r in rows]
        split = int(SPLIT.timestamp())
        first = [r for ts, r in rows if ts < split]
        second = [r for ts, r in rows if ts >= split]
        start = datetime.fromtimestamp(rows[0][0], timezone.utc)
        end = datetime.fromtimestamp(rows[-1][0], timezone.utc)
        tpd = round(len(rs) / weekdays_between(start, end), 3)
        m = sum(rs) / len(rs)
        port = {"markets": basket, "n": len(rs), "mean_r": round(m, 4), "trades_per_day": tpd,
                "mean_r_confirmation": round(sum(first) / len(first), 4) if first else None,
                "mean_r_discovery": round(sum(second) / len(second), 4) if second else None, "rSeries": rs}
        port["kept"] = bool(first and second and sum(first) > 0 and sum(second) > 0)
        try:
            sim = engine([{"key": "portfolio", "label": "portefeuille", "rSeries": rs, "tradesPerDay": tpd},
                          {"key": "witness", "label": "témoin", "rSeries": [round(r - m, 4) for r in rs], "tradesPerDay": tpd}],
                         risks=(250.0, 500.0, 750.0), paths=4000)
            by = {p["key"]: p for p in sim["profiles"]}
            port["combine"] = [{"risk": a["risk"], "pass": a["pass"], "pass10": a["pass10"], "funded_days": a.get("fundedDays"),
                                "first_payout": a.get("firstPayout"), "witness_pass": b["pass"], "witness_pass10": b["pass10"]}
                               for a, b in zip(by["portfolio"]["risks"], by["witness"]["risks"])]
            best = max(port["combine"], key=lambda x: x["pass10"] - x["witness_pass10"])
            port["fast"] = port["kept"] and best["pass10"] >= best["witness_pass10"] + 0.10
        except Exception as exc:  # noqa: BLE001
            port["combine_error"] = str(exc)
        out["portfolio"] = port
    return out
