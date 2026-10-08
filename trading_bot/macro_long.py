"""Essai 13 (HYPOTHESES.md) : l'essai 12 rejoué sur 2010-2024, période jamais regardée.

Annonces : `data/macro_events_2010_2024.json` (emploi et inflation depuis 2010, décisions prévues de la Fed
depuis 2013). Prix : bougies 1 min Dukascopy regroupées en 5 min, seulement la veille, le jour et le lendemain de
chaque annonce, gardées hors du dépôt (`data/history/events_<actif>_5m.json`). Le téléchargement reprend là où
il s'est arrêté.
"""
from __future__ import annotations

import json
import logging
import lzma
import struct
import time
from datetime import date, datetime, time as dtime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from . import macro_drift as md
from .config import DATA_DIR, ROOT_DIR
from .models import Candle, iso, utcnow
from .providers import history as hist

log = logging.getLogger(__name__)
NY = ZoneInfo("America/New_York")
EVENTS_FILE = ROOT_DIR / "data" / "macro_events_2010_2024.json"
ASSETS = ("gold", "sp500", "nasdaq", "euro")
H1_SPLIT = int(datetime(2017, 4, 1, tzinfo=timezone.utc).timestamp())
FOMC_SPLIT = int(datetime(2019, 1, 1, tzinfo=timezone.utc).timestamp())
N_TRIALS = 108


def events(path: Path = EVENTS_FILE) -> list[tuple[int, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for kind in ("nfp", "cpi", "fomc"):
        hh, mm = (int(x) for x in data["times_ny"][kind].split(":"))
        for d in data[kind]:
            out.append((int(datetime.combine(date.fromisoformat(d), dtime(hh, mm), NY).timestamp()), kind))
    return sorted(out)


def needed_days(evs: list[tuple[int, str]]) -> list[date]:
    """La veille ouvrée (ATR), le jour et le lendemain ouvré (sortie du lendemain) de chaque annonce."""
    days: set[date] = set()
    for ts, _ in evs:
        d = datetime.fromtimestamp(ts, NY).date()
        prev = d - timedelta(days=1)
        while prev.weekday() >= 5:
            prev -= timedelta(days=1)
        nxt = d + timedelta(days=1)
        while nxt.weekday() >= 5:
            nxt += timedelta(days=1)
        days |= {prev, d, nxt}
    return sorted(days)


def cache_file(asset: str) -> Path:
    return Path(DATA_DIR) / "history" / f"events_{asset}_1m_days.json"


def _scale(sym: str, reference: float | None) -> float:
    """Échelle des prix entiers Dukascopy, fixée sur un jour récent (elle ne change pas d'une année à l'autre)."""
    d = date.today() - timedelta(days=14)
    for _ in range(10):
        while d.weekday() >= 5:
            d -= timedelta(days=1)
        raw = hist._get(f"https://datafeed.dukascopy.com/datafeed/{sym}/{d.year}/{d.month - 1:02d}/{d.day:02d}/BID_candles_min_1.bi5")
        if raw:
            return hist.detect_scale(raw, reference)
        d -= timedelta(days=1)
    raise RuntimeError(f"échelle Dukascopy introuvable pour {sym}")


def download(asset: str, days: list[date], reference: float | None, pause: float = 0.3,
             deadline: float | None = None) -> dict[str, Any]:
    """Télécharge les jours manquants (bougies 1 min gardées par jour, regroupées en 5 min à la lecture)."""
    f = cache_file(asset)
    cache = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"scale": None, "days": {}}
    sym = hist.DUKASCOPY[asset]
    if not cache.get("scale"):
        cache["scale"] = _scale(sym, reference)
    todo = [d for d in days if d.isoformat() not in cache["days"]]
    for n, d in enumerate(todo):
        if deadline is not None and time.time() > deadline:
            break
        raw = hist._get(f"https://datafeed.dukascopy.com/datafeed/{sym}/{d.year}/{d.month - 1:02d}/{d.day:02d}/BID_candles_min_1.bi5")
        rows = []
        if raw:
            start = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
            try:
                rows = [[c.ts, c.open, c.high, c.low, c.close] for c in hist.parse_dukascopy_candles(raw, start, cache["scale"])]
            except (lzma.LZMAError, struct.error) as exc:
                log.warning("Dukascopy %s %s illisible (%s)", sym, d, exc)
        cache["days"][d.isoformat()] = rows
        if n % 50 == 49:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(cache), encoding="utf-8")
        time.sleep(pause)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(cache), encoding="utf-8")
    return {"asset": asset, "days": len(cache["days"]), "with_data": sum(1 for v in cache["days"].values() if v),
            "missing": len([d for d in days if d.isoformat() not in cache["days"]])}


def load_candles(asset: str) -> list[Candle]:
    f = cache_file(asset)
    if not f.exists():
        return []
    cache = json.loads(f.read_text(encoding="utf-8"))
    one = sorted((Candle(r[0], r[1], r[2], r[3], r[4]) for rows in cache["days"].values() for r in rows), key=lambda c: c.ts)
    return hist.resample_5m(one)


def judge(rows: list[dict[str, Any]], split: int) -> dict[str, Any]:
    rs = [r["r_day"] for r in rows]
    s_all = md.summary(rs)
    s1 = md.summary([r["r_day"] for r in rows if r["ts"] < split])
    s2 = md.summary([r["r_day"] for r in rows if r["ts"] >= split])
    kept = bool(s_all["n"] >= 20 and (s_all["mean"] or 0) > 0 and (s_all["t"] or 0) >= 2
                and (s1["mean"] or 0) > 0 and (s2["mean"] or 0) > 0)
    med = sorted(r["reaction_atr"] for r in rows)[len(rows) // 2] if rows else 0
    return {"kept": kept, "all": s_all, "half1": s1, "half2": s2,
            "strong": md.summary([r["r_day"] for r in rows if r["reaction_atr"] >= med]),
            "next_day": md.summary([r["r_next"] for r in rows if "r_next" in r])}


def run() -> dict[str, Any]:
    evs = events()
    out: dict[str, Any] = {"essai": 13, "updated_at": iso(utcnow()), "n_trials": N_TRIALS, "assets": {}}
    for asset in ASSETS:
        candles = load_candles(asset)
        if not candles:
            out["assets"][asset] = {"error": "pas de bougies téléchargées"}
            continue
        rows = md.reactions(candles, asset, evs)
        news = [r for r in rows if r["kind"] in ("nfp", "cpi")]
        fomc = [r for r in rows if r["kind"] == "fomc"]
        out["assets"][asset] = {"h1": {**judge(rows, H1_SPLIT), "nfp": md.summary([r["r_day"] for r in rows if r["kind"] == "nfp"]),
                                       "cpi": md.summary([r["r_day"] for r in rows if r["kind"] == "cpi"]),
                                       "nfp_cpi_only": md.summary([r["r_day"] for r in news])},
                                "h3_fomc": judge(fomc, FOMC_SPLIT),
                                "first_event": rows[0]["at"] if rows else None, "events": rows}
    return out
