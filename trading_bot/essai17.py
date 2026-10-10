"""Essai 17 (HYPOTHESES.md) : toutes nos stratégies existantes sur le DAX et l'Euro Stoxx 50.

Aucune règle nouvelle : on réutilise le bot rejoué, le laboratoire (essais 3, 5, 8, 9) et les essais 14 à 16.
Les stratégies de séance, écrites à l'heure de New York, tournent sur une « horloge européenne » : chaque
bougie est replacée à l'heure de Paris moins 30 min, lue comme une heure de New York (9:30 du code = 9:00 à
Paris). Frais du bot en % du prix (courtier CFD), pas de Topstep. « Prouvé » avec la marge pour 374 essais.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from . import essai14 as e14
from . import essai15 as e15
from . import essai16 as e16
from . import strategies as sl
from .models import Candle

N_TRIALS = 374
ASSETS = {"dax": ("DEUIDXEUR", "DAX 40 (CFD)", 0.01), "estoxx": ("EUSIDXEUR", "Euro Stoxx 50 (CFD)", 0.03)}
PARIS = ZoneInfo("Europe/Paris")
LAB_REMAPPED = ("orb5", "orb30", "intraday_mom", "noise_area", "noise_area_v2", "gap_fade")
LAB_REAL_5M = ("london_breakout",)
LAB_REAL_1H = ("donchian_1h", "rsi2_1h")
LAB_REMAPPED_1H = ("donchian_day", "donchian_15m_day", "donchian_30m_day")


def remap(candles: list[Candle]) -> list[Candle]:
    """Horloge européenne : heure de Paris moins 30 min, réécrite comme une heure de New York."""
    out: dict[int, Candle] = {}
    for c in candles:
        wall = datetime.fromtimestamp(c.ts, PARIS).replace(tzinfo=None) + timedelta(minutes=30)
        ts = int(wall.replace(tzinfo=sl.NY).timestamp())
        out[ts] = Candle(ts, c.open, c.high, c.low, c.close, c.volume)
    return [out[k] for k in sorted(out)]


def asset_config(cfg, key: str):
    """Réglages du bot de l'indice S&P 500, avec le nom et les frais de l'indice européen."""
    _, label, cost = ASSETS[key]
    return replace(cfg.assets["sp500"], key=key, label=label, yahoo_symbol="", cost_pct=cost,
                   news_keywords=(), lot_label="CFD", lot_multiplier=1.0)


def enable_european_sessions() -> None:
    """Les règles de séance des essais 14 et 15 s'appliquent aux deux indices (heure transposée)."""
    for key in ASSETS:
        e14.OPEN_NY[key] = (9, 30)
        e14.FUTURES.add(key)
    e15.INDICES = tuple(dict.fromkeys(e15.INDICES + tuple(ASSETS)))


def verdict(trades: list[sl.Trade], cost_pct: float) -> dict[str, Any]:
    trades = [t for t in trades if t.reason != "fin des données"]
    disc = sl.evaluate(trades, cost_pct, None, start_ts=e14.SPLIT)
    conf = sl.evaluate(trades, cost_pct, None, end_ts=e14.SPLIT)
    both = sl.evaluate(trades, cost_pct, None)
    ok_d, ok_c = sl.discovery_pass(disc), sl.confirmation_pass(conf)
    status = ("prouvé" if sl.proven(both, N_TRIALS) else "validé") if ok_d and ok_c else (
        "écarté (découverte)" if not ok_d else "écarté (confirmation)")
    return {"discovery": disc, "confirmation": conf, "all": both, "status": status}


def cells(key: str, real: list[Candle], rem: list[Candle], ctx: e15.Ctx, other: e15.Ctx | None,
          base: list[sl.Trade], cost_pct: float) -> list[tuple[str, list[sl.Trade]]]:
    out: list[tuple[str, list[sl.Trade]]] = [("bot", base)]
    s_rem, s_real = sl._Series(rem), sl._Series(real)
    out += [(n, sl.RUNNERS_5M[n](s_rem, key)) for n in LAB_REMAPPED]
    out += [(n, sl.RUNNERS_5M[n](s_real, key)) for n in LAB_REAL_5M]
    out += [(n, sl.RUNNERS_1H[n](real, key)) for n in LAB_REAL_1H]
    out += [(n, sl.RUNNERS_1H[n](rem, key)) for n in LAB_REMAPPED_1H]
    out += [(f, [t for t in base if not e14.removed_by(f, t, ctx, other)]) for f in e14.FILTERS]
    out += [(c, [x for x in (e14.exit_variant(c, t, ctx) for t in base) if x is not None]) for c in e14.EXITS]
    out += [(b, e14.setup_trades(b, key, ctx)) for b in e14.SETUPS]
    out += [(f, [t for t in base if not e15.removed_by(f, t, ctx, cost_pct / 100 * t.entry)]) for f in e15.FILTERS]
    for g in e15.GESTION:
        if g == "G39":
            out.append((g, e15.half_size(base, ctx)))
        elif g == "G40":
            out.append((g, e15.day_limits(base)))
        else:
            out.append((g, [x for x in (e15.manage(g, t, ctx) for t in base) if x is not None]))
    out += [(s, e15.setup_trades(s, key, ctx)) for s in e15.SETUPS]
    ctx16 = e16.Ctx(real)
    out += [(w, e16.trades(w, key, ctx16)) for w in e16.VARIANTS]
    return out
