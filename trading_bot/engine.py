"""Orchestration : scan (génération de signaux), track (suivi), summary (bilan)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from .analysis import assess
from .config import DISCLAIMER, Config, load_config
from .learning import learn
from .models import Signal, iso, parse_iso, utcnow
from .notify import notify
from .providers import market
from .providers import news as newsmod
from .providers.http import ProviderError
from .signals import build_signal, format_signal
from .storage import Store
from .summary import daily_summary
from .tracker import format_outcome, update_signal

log = logging.getLogger(__name__)

NEWS_CATEGORIES = {"nasdaq": ["macro"], "bitcoin": ["crypto", "macro"], "gold": ["gold", "macro"]}


class Engine:
    def __init__(self, cfg: Config | None = None, store: Store | None = None):
        self.cfg = cfg or load_config()
        self.store = store or Store()

    # ------------------------------------------------------------------ scan
    def scan(self, now: datetime | None = None, dry_run: bool = False) -> list[Signal]:
        now = now or utcnow()
        produced: list[Signal] = []
        all_sigs = self.store.history() + self.store.open_signals()
        adj = self.store.adjustments()
        weights = adj.get("weights") or None
        avoid_hours = set(adj.get("avoid_hours_utc") or [])

        calendar = newsmod.load_calendar(self.store.calendar()) + newsmod.recurring_macro_events(now)
        blackout = newsmod.in_blackout(now, calendar, self.cfg.news_blackout_before_minutes,
                                       self.cfg.news_blackout_after_minutes)
        if blackout:
            log.info("Blackout macro : %s à %s — aucun signal", blackout.name, blackout.at)
            self._touch_state(now, note=f"blackout {blackout.name}")
            return []
        if now.hour in avoid_hours:
            log.info("Tranche horaire %02dh UTC évitée (apprentissage)", now.hour)
            self._touch_state(now, note="tranche évitée")
            return []

        news_cache: dict[str, list[newsmod.NewsItem]] = {}
        for asset in self.cfg.assets.values():
            reasons = self._policy_block(asset.key, all_sigs, now)
            if asset.session_utc and not (asset.session_utc[0] <= now.hour < asset.session_utc[1]):
                reasons.append("hors session de trading configurée")
            if reasons:
                log.info("%s : pas de scan (%s)", asset.label, "; ".join(reasons))
                continue
            try:
                candles = market.fetch_candles_5m(asset, days=5)
            except ProviderError as exc:
                log.warning("%s : données indisponibles (%s)", asset.label, exc)
                continue
            if now.timestamp() - candles[-1].ts > 30 * 60:
                log.info("%s : dernière bougie trop ancienne (marché fermé ?)", asset.label)
                continue

            a = assess(asset, candles, self.cfg, weights)
            if a.direction is None:
                log.info("%s : %s", asset.label, "; ".join(a.reasons_rejected) or "aucune direction")
                continue

            items: list[newsmod.NewsItem] = []
            for c in NEWS_CATEGORIES.get(asset.key, ["macro"]):
                if c not in news_cache:
                    news_cache[c] = newsmod.fetch_news([c], self.cfg.news_lookback_minutes, now)
                items += news_cache[c]
            risk, hits = newsmod.risk_score(items, asset.news_keywords)
            if risk > self.cfg.max_news_risk_score:
                log.info("%s : actualité incertaine (score %d) → pas de signal. %s", asset.label, risk, hits)
                continue
            news_ctx = ("actualité calme sur les 2 dernières heures" if risk == 0
                        else f"actualité à surveiller (score {risk}) : " + " | ".join(hits[:2]))

            sig, why = build_signal(asset, a, self.cfg, news_ctx, now)
            if sig is None:
                log.info("%s : pas de signal (%s)", asset.label, "; ".join(why))
                continue
            produced.append(sig)
            if not dry_run:
                self.store.add_signal(sig)
                all_sigs.append(sig)
            notify(format_signal(sig, self.cfg.timezone) + "\n\n" + DISCLAIMER)
        self._touch_state(now, note=f"{len(produced)} signal(aux)")
        return produced

    def _policy_block(self, asset_key: str, all_sigs: list[Signal], now: datetime) -> list[str]:
        reasons = []
        mine = [s for s in all_sigs if s.asset == asset_key]
        todays = [s for s in mine if parse_iso(s.created_at).date() == now.date()]
        if len(todays) >= self.cfg.max_signals_per_asset_per_day:
            reasons.append(f"maximum quotidien atteint ({self.cfg.max_signals_per_asset_per_day})")
        if any(s.status == "open" for s in mine):
            reasons.append("un signal est déjà ouvert sur cet actif")
        last = max((parse_iso(s.created_at) for s in mine), default=None)
        if last and now - last < timedelta(minutes=self.cfg.cooldown_minutes):
            reasons.append("délai de refroidissement en cours")
        return reasons

    def _touch_state(self, now: datetime, note: str = "") -> None:
        st = self.store.state()
        st["last_scan"] = iso(now)
        st["last_scan_note"] = note
        self.store.save_state(st)

    # ----------------------------------------------------------------- track
    def track(self, now: datetime | None = None) -> list[Signal]:
        now = now or utcnow()
        open_sigs = self.store.open_signals()
        if not open_sigs:
            return []
        closed: list[Signal] = []
        remaining: list[Signal] = []
        for sig in open_sigs:
            asset = self.cfg.assets[sig.asset]
            candles = None
            price = None
            try:
                candles = market.fetch_candles_1m(asset)
            except ProviderError as exc:
                log.warning("%s : bougies 1m indisponibles (%s)", asset.label, exc)
            try:
                price = market.fetch_price(asset)
            except ProviderError as exc:
                log.warning("%s : prix indisponible (%s)", asset.label, exc)
            done = update_signal(sig, candles, price, now)
            if done is None:
                remaining.append(sig)
            else:
                closed.append(done)
                self.store.append_history(done)
                notify(format_outcome(done, self.cfg.timezone))
        self.store.save_open(remaining)
        if closed:
            self._relearn()
        st = self.store.state()
        st["last_track"] = iso(now)
        self.store.save_state(st)
        return closed

    def _relearn(self) -> dict[str, Any]:
        adj = learn(self.store.history(), self.cfg, self.store.adjustments())
        self.store.save_adjustments(adj)
        return adj

    # --------------------------------------------------------------- summary
    def summary(self, day=None, send: bool = True) -> str:
        adj = self._relearn()
        text = daily_summary(self.store.all_signals(), self.cfg, day, adj)
        if send:
            notify(text)
        st = self.store.state()
        st["last_summary"] = iso(utcnow())
        self.store.save_state(st)
        return text

    # ------------------------------------------------------------------ tick
    def tick(self, now: datetime | None = None) -> dict[str, Any]:
        """Un passage complet : suivi des signaux ouverts, puis scan si l'intervalle est écoulé."""
        now = now or utcnow()
        closed = self.track(now)
        st = self.store.state()
        last_scan = parse_iso(st["last_scan"]) if st.get("last_scan") else None
        new: list[Signal] = []
        if last_scan is None or now - last_scan >= timedelta(minutes=self.cfg.scan_interval_minutes - 1):
            new = self.scan(now)
        return {"closed": [s.id for s in closed], "new": [s.id for s in new]}
