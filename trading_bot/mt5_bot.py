"""Bot classique (Nasdaq) calculé sur le PC avec les prix live de MetaTrader 5 (demandé par Yanisse le 19/10/2026 :
« PC allumé, tout vient du PC »).

À chaque nouvelle bougie 5 min close sur le CFD du Nasdaq, le pont rejoue le scan du bot de GitHub (Engine.scan,
mêmes critères, même filtre du bot appris, mêmes sorties : stop ×1,5, objectif 3 fois le stop, 24 h au plus) sur les
bougies du courtier. Les réglages appris (adjustments.json, drift.json) et le calendrier manuel sont relus sur
GitHub ; les signaux du PC sont gardés à part (journal/bot_pc/), avec leurs règles de prudence (un signal ouvert à
la fois, refroidissement, plafond du jour), et suivis jusqu'au TP, au SL ou à l'expiration sur les mêmes bougies.

Les signaux sortent au format de mt5_local (clé « lab:bot:<horodatage> ») : la copie, le message Telegram du PC,
l'agent IA et la variable PC_ALIVE les traitent comme ceux des stratégies. Si le calcul échoue (marché fermé, pas
de bougies, erreur), « bot » n'est pas marqué lu et GitHub reprend la main, comme avant.
Écart connu : le bot appris a été entraîné sur les contrats à terme (NQ), pas sur le CFD.
"""
from __future__ import annotations

import json
import logging
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import engine as engmod
from .config import load_config
from .models import Candle, Signal, iso, parse_iso
from .mt5_local import BAR, server_offset
from .providers import market
from .storage import Store
from .tracker import update_signal

log = logging.getLogger("mt5_bot")

ASSET = "nasdaq"
STRAT = "bot"
RAW = "https://raw.githubusercontent.com/Yxnisse7/Trading-Bot/main/data/{name}"
SHARED = ("adjustments.json", "drift.json", "macro_calendar.json")    # réglages appris sur GitHub
REFRESH = 3600                                                         # s entre deux relectures de ces réglages


def _download(name: str) -> bytes:
    with urllib.request.urlopen(RAW.format(name=name), timeout=20) as r:
        return r.read()


class LocalBot:
    def __init__(self, mt5, symbols: dict[str, str], clock: Callable[[], float], root: Path,
                 download: Callable[[str], bytes] = _download, notify_off: bool = True):
        self.mt5, self.symbols, self.clock = mt5, symbols, clock
        self.download = download
        self.store = Store(Path(root) / "journal" / "bot_pc")
        cfg = load_config()
        cfg.assets = {ASSET: cfg.assets[ASSET]}
        self.cfg = cfg
        self.last_bar = 0
        self.last_refresh = 0.0
        self.found: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ données
    def _candles(self, now: float) -> list[Candle]:
        sym = self.symbols.get(ASSET)
        if not sym:
            return []
        off = server_offset(self.mt5, sym, now)
        if off is None:
            return []
        n = self.cfg.scan_days * 288 + 1
        rates = self.mt5.copy_rates_from_pos(sym, self.mt5.TIMEFRAME_M5, 0, n)
        if rates is None or len(rates) < 100:
            return []
        bars = [Candle(int(r["time"]) - off, float(r["open"]), float(r["high"]), float(r["low"]),
                       float(r["close"]), float(r["tick_volume"])) for r in rates]
        return [b for b in bars if b.ts + BAR <= now]

    def _refresh(self, now: float) -> None:
        if now - self.last_refresh < REFRESH:
            return
        self.last_refresh = now
        for name in SHARED:
            try:
                (self.store.dir / name).write_bytes(self.download(name))
            except Exception as exc:                  # GitHub injoignable : on garde la dernière copie
                log.info("réglages %s non relus (%s)", name, exc)

    # ------------------------------------------------------------------ suivi
    def _track(self, bars: list[Candle], now: float) -> None:
        """Clôt les signaux du PC au TP, au SL ou à l'expiration, sur les bougies du courtier."""
        still, done = [], []
        for sig in self.store.open_signals():
            since = int(parse_iso(sig.created_at).timestamp())
            closed = update_signal(sig, [b for b in bars if b.ts >= since], bars[-1].close if bars else None,
                                   datetime.fromtimestamp(now, timezone.utc))
            (done if closed else still).append(closed or sig)
        if done:
            for sig in done:
                self.store.append_history(sig)
            self.store.save_open(still)

    def _scan(self, bars: list[Candle], now: float) -> list[Signal]:
        eng = engmod.Engine(self.cfg, store=self.store)
        real_fetch, real_notify = market.fetch_candles_5m, engmod.notify

        def fetch(asset, days=5):
            return bars if asset.key == ASSET else real_fetch(asset, days)
        market.fetch_candles_5m, engmod.notify = fetch, lambda *a, **k: None   # jamais de message d'ici
        try:
            return eng.scan(datetime.fromtimestamp(now, timezone.utc), dry_run=True)
        finally:
            market.fetch_candles_5m, engmod.notify = real_fetch, real_notify

    @staticmethod
    def _out(sig: Signal) -> dict[str, Any]:
        ts = int(parse_iso(sig.created_at).timestamp())
        return {"key": f"lab:{STRAT}:{ts}", "asset": ASSET, "direction": sig.direction, "entry": sig.entry,
                "stop": abs(sig.entry - sig.stop_loss), "target": abs(sig.take_profit - sig.entry),
                "created": ts, "expires": int(parse_iso(sig.expires_at).timestamp()), "source": "local"}

    # ------------------------------------------------------------------ passage
    def signals(self) -> tuple[list[dict[str, Any]], set[str]]:
        """Signaux du bot ouverts sur le PC (format mt5_local) et {« local:bot »} si le calcul a marché."""
        now = self.clock()
        try:
            bars = self._candles(now)
            if not bars or now - (bars[-1].ts + BAR) > 600:
                return [], set()                       # flux arrêté : GitHub prend le relais
            if bars[-1].ts != self.last_bar:
                self._refresh(now)
                self._track(bars, now)
                for sig in self._scan(bars, now):
                    sig.meta["source_prix"] = "MT5"
                    self.store.add_signal(sig)
                    log.info("bot classique PC : %s %s à %s", sig.direction, ASSET, sig.entry)
                self.last_bar = bars[-1].ts
                self.found = [self._out(s) for s in self.store.open_signals()]
        except Exception:                              # jamais bloquant : GitHub prend le relais
            log.exception("bot classique sur le PC")
            return [], set()
        return list(self.found), {f"local:{STRAT}"}
