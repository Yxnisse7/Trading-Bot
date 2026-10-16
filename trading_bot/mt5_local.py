"""Stratégies en signaux réels calculées sur le PC, avec les prix live de MetaTrader 5 (demandé par Yanisse le
16/10/2026).

Le bot de GitHub annonce ses signaux environ 10 min après la bougie (prix Yahoo en retard, passage toutes les
5 min, puis lecture du dépôt par le pont). Ici, le pont rejoue les mêmes règles (strategies.RUNNERS_*) sur les
bougies 5 min du courtier dès qu'une bougie se ferme : la copie démo part tout de suite.

Bascule : si le calcul local échoue (marché fermé, pas assez de bougies, erreur), la stratégie n'est pas marquée
« lue » et la copie retombe sur les signaux de GitHub, comme avant. Telegram, Topstep et la Simulation viennent
toujours du bot de GitHub, que le PC soit allumé ou non.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable

from . import strategies as sl
from .models import Candle

log = logging.getLogger("mt5_local")

BAR = 300
DEFAULT_DAYS = 8
# même stratégie, même sens, entrées à moins de 3 h d'écart : c'est le même signal (prix CFD et contrats à terme
# ne cassent pas toujours à la même bougie)
SAME_SIGNAL = 3 * 3600


def active(now: float) -> list[tuple[str, str]]:
    """Stratégies en signaux réels à cette heure (même liste que le bot : strategies.LIVE moins LIVE_END)."""
    out = []
    for (strat, asset), since in sl.LIVE.items():
        start = datetime.fromisoformat(since.replace("Z", "+00:00")).timestamp()
        end = sl.LIVE_END.get((strat, asset))
        if now < start or (end and now >= datetime.fromisoformat(end.replace("Z", "+00:00")).timestamp()):
            continue
        out.append((strat, asset))
    return out


def server_offset(mt5, sym: str, now: float) -> int | None:
    """Décalage de l'heure du serveur (arrondi à la demi-heure) ; None sans cotation récente."""
    tick = mt5.symbol_info_tick(sym)
    if tick is None or not tick.time:
        return None
    off = round((tick.time - now) / 1800) * 1800
    return off if abs(tick.time - off - now) <= 180 else None


def close_at(strat: str, entry_ts: int) -> int | None:
    if strat in sl.OVERNIGHT:
        hold = sl.OVERNIGHT[strat]
        return entry_ts + hold if hold else None
    return sl.session_close_ts(entry_ts)


class LocalEngine:
    def __init__(self, mt5, symbols: dict[str, str], clock: Callable[[], float]):
        self.mt5, self.symbols, self.clock = mt5, symbols, clock
        self.cache: dict[str, tuple[int, list[dict[str, Any]]]] = {}

    def _candles(self, sym: str, days: int, now: float) -> list[Candle]:
        off = server_offset(self.mt5, sym, now)
        if off is None:
            return []
        rates = self.mt5.copy_rates_from_pos(sym, self.mt5.TIMEFRAME_M5, 0, days * 288 + 1)
        if rates is None or len(rates) < 100:
            return []
        bars = [Candle(int(r["time"]) - off, float(r["open"]), float(r["high"]), float(r["low"]),
                       float(r["close"]), float(r["tick_volume"])) for r in rates]
        return [b for b in bars if b.ts + BAR <= now]            # bougies closes seulement

    def signals(self) -> tuple[list[dict[str, Any]], set[str]]:
        """Positions ouvertes selon les règles, au format de mt5_copy.read_signals, et les stratégies lues."""
        now = self.clock()
        out, ok = [], set()
        for strat, asset in active(now):
            sym = self.symbols.get(asset)
            runner = sl.RUNNERS_1H.get(strat) or sl.RUNNERS_5M.get(strat)
            if sym is None or runner is None:
                continue
            name = f"{strat}:{asset}"
            try:
                bars = self._candles(sym, sl.LAB_DAYS.get(strat, DEFAULT_DAYS), now)
                if not bars or now - (bars[-1].ts + BAR) > 600:
                    continue                                       # flux arrêté : GitHub prend le relais
                cached = self.cache.get(name)
                if cached and cached[0] == bars[-1].ts:
                    out += cached[1]
                    ok.add(f"local:{strat}")
                    continue
                trades = runner(bars, asset) if strat in sl.RUNNERS_1H else runner(sl._Series(bars), asset)
            except Exception:                                      # jamais bloquant : GitHub prend le relais
                log.exception("calcul local %s", name)
                continue
            found = []
            for t in trades:
                still_open = t.reason == "fin des données" or t.exit_ts > now
                if not still_open:
                    continue
                found.append({"key": f"lab:{strat}:{t.entry_ts}", "asset": asset, "direction": t.direction,
                              "entry": t.entry, "stop": t.risk, "target": None, "created": t.entry_ts,
                              "expires": close_at(strat, t.entry_ts), "source": "local"})
            self.cache[name] = (bars[-1].ts, found)
            out += found
            ok.add(f"local:{strat}")
        return out, ok


def same_signal(a_key: str, a_dir: str | None, b_key: str, b_dir: str | None) -> bool:
    """Deux clés « lab:stratégie:horodatage » désignent-elles le même signal (local et GitHub) ?"""
    pa, pb = a_key.split(":"), b_key.split(":")
    if len(pa) != 3 or len(pb) != 3 or pa[0] != "lab" or pb[0] != "lab" or pa[1] != pb[1]:
        return False
    if a_dir and b_dir and a_dir != b_dir:
        return False
    return abs(int(pa[2]) - int(pb[2])) <= SAME_SIGNAL

