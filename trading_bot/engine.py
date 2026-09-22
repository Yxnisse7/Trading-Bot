"""Orchestration : scan (génération de signaux), track (suivi), summary (bilan), tick, backtest."""
from __future__ import annotations

import copy
import hashlib
import re
from dataclasses import replace
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from . import indicators as ind
from .analysis import assess
from .backtest import format_backtest, run_backtest
from .config import DISCLAIMER, Config, load_config
from .learning import learn
from .models import Signal, iso, parse_iso, utcnow
from .notify import notify, telegram_chat_ids, telegram_updates
from .portfolio import Portfolio
from .providers import calendar as calmod
from .providers import market
from .providers import news as newsmod
from .providers.http import ProviderError
from .report import build_dashboard, build_report
from .signals import build_signal, format_signal, round_to_tick
from .storage import Store
from .summary import daily_summary
from .tracker import format_outcome, update_signal

log = logging.getLogger(__name__)


def chat_key(chat_id: str) -> str:
    """Empreinte courte d'un identifiant de chat : l'état du bot est public (dépôt + site),
    on n'y écrit donc jamais le numéro lui-même, seulement de quoi le reconnaître."""
    return hashlib.sha256(str(chat_id).encode("utf-8")).hexdigest()[:12]


def chat_keys(values) -> list[str]:
    """Normalise une liste stockée : les anciens identifiants bruts sont convertis en empreintes."""
    return [chat_key(v) if str(v).isdigit() else str(v) for v in (values or [])]


MAJOR_EVENT_RE = re.compile(r"FOMC|Fed\b|taux directeur|CPI|inflation|Non-?farm|NFP|emploi|payrolls", re.I)

# « gold » = flux FXStreet (devises, matières premières, dollar) : pertinent aussi pour le pétrole et l'euro
NEWS_CATEGORIES = {"nasdaq": ["macro"], "sp500": ["macro"], "bitcoin": ["crypto", "macro"],
                   "ethereum": ["crypto", "macro"], "gold": ["gold", "macro"],
                   "oil": ["gold", "macro"], "euro": ["gold", "macro"]}


class Engine:
    def __init__(self, cfg: Config | None = None, store: Store | None = None):
        self.cfg = cfg or load_config()
        self.store = store or Store()
        self.tz = ZoneInfo(self.cfg.timezone)
        self.portfolio = Portfolio(self.store, self.cfg)

    # ------------------------------------------------------------------ scan
    def scan(self, now: datetime | None = None, dry_run: bool = False) -> list[Signal]:
        now = now or utcnow()
        produced: list[Signal] = []
        # fantômes ouverts inclus : les plafonds des fantômes doivent les voir d'un passage à l'autre
        all_sigs = self.store.all_signals()
        adj = self.store.adjustments()
        avoid_hours = set(adj.get("avoid_hours_utc") or [])
        promoted = set(adj.get("promoted_variants") or []) if self.cfg.variants_enabled else set()
        variants_on = self.cfg.variants_enabled and self.cfg.shadow_enabled and not dry_run

        calendar = self.macro_events(now)
        blackout = newsmod.in_blackout(now, calendar, self.cfg.news_blackout_before_minutes,
                                       self.cfg.news_blackout_after_minutes)
        if blackout:
            log.info("Blackout macro : %s à %s UTC — aucun signal", blackout.name, blackout.at.strftime("%H:%M"))
            self._touch_state(now, note=f"blackout {blackout.name}")
            return []
        if now.hour in avoid_hours:
            log.info("Tranche horaire %02dh UTC évitée (apprentissage)", now.hour)
            self._touch_state(now, note="tranche évitée")
            return []

        news_cache: dict[str, list[newsmod.NewsItem]] = {}
        context = self.correlation_context(now) if self.cfg.correlation_enabled else {}
        caution = self.post_event_caution(now, calendar)
        scan_cfg = self.cfg
        if caution:
            # Lendemain de FOMC / CPI / emploi : les tendances lentes sont peu fiables (repositionnement),
            # on exige un critère de plus et on suspend l'horizon 3 h.
            scan_cfg = replace(self.cfg, min_criteria=self.cfg.min_criteria + 1, min_score=self.cfg.min_score + 1.0)
            log.info("Prudence post-événement (%s, %s UTC) : %d critères exigés, horizon 3 h suspendu",
                     caution.name, caution.at.strftime("%d/%m %H:%M"), scan_cfg.min_criteria)
        if "confiance_moyenne" in promoted and scan_cfg.min_confidence == "fort":
            scan_cfg = replace(scan_cfg, min_confidence="moyen")
        # (horizon, base en minutes, variante testée en fantôme ou None pour un signal réel)
        horizons: list[tuple[str, int, str | None]] = [("1h", 5, None)]
        long_key = f"{self.cfg.long_horizon_base_minutes * 12 // 60}h"
        if not caution:
            if self.cfg.long_horizon_enabled or "horizon_3h" in promoted:
                horizons.append((long_key, self.cfg.long_horizon_base_minutes, None))
            elif variants_on:
                horizons.append((long_key, self.cfg.long_horizon_base_minutes, "horizon_3h"))
        # Bitcoin d'abord : sa direction sert de contexte à l'Ethereum
        ordered = sorted(self.cfg.assets.values(), key=lambda a: 0 if a.key == "bitcoin" else 1)
        for asset in ordered:
            trial_key = f"essai_{asset.key}" if asset.trial and f"essai_{asset.key}" not in promoted else None
            if trial_key and not variants_on:
                log.info("%s : actif à l'essai, suivi en silence uniquement", asset.label)
                continue
            session_variant = None
            if asset.session_utc and not (asset.session_utc[0] <= now.hour < asset.session_utc[1]):
                ext = (self.cfg.variant_extended_sessions or {}).get(asset.key)
                in_ext = bool(ext) and ext[0] <= now.hour < ext[1]
                if in_ext and "hors_session" in promoted:
                    pass                                   # variante promue : traitée comme la session normale
                elif in_ext and variants_on:
                    session_variant = "hors_session"       # testée en fantôme, jamais notifiée
                else:
                    log.info("%s : hors session de trading configurée", asset.label)
                    continue
            own_event = newsmod.in_blackout(now, calendar, self.cfg.news_blackout_before_minutes,
                                            self.cfg.news_blackout_after_minutes, asset_key=asset.key)
            if own_event:
                log.info("%s : annonce propre à l'actif (%s) → pas de signal", asset.label, own_event.name)
                continue
            weights = self._weights_for(adj, asset.key)
            # Une seule variante à la fois : un actif à l'essai n'est testé que dans ses réglages normaux,
            # et hors session seul l'horizon standard est testé, pour que les statistiques de chaque
            # variante ne mélangent pas deux changements.
            if trial_key:
                plan = [(h, base, trial_key) for h, base, v in horizons if v is None and not session_variant]
            elif session_variant:
                plan = [(h, base, session_variant) for h, base, v in horizons if base == 5 and v is None]
            else:
                plan = list(horizons)
            if not plan:
                continue
            blocked = {h: self._scan_block(asset, h, base, variant, all_sigs, now) for h, base, variant in plan}
            if all(blocked.values()):
                log.info("%s : pas de scan (%s)", asset.label, "; ".join(blocked["1h"]))
                continue
            try:
                raw = market.fetch_candles_5m(asset, days=5)
            except ProviderError as exc:
                log.warning("%s : données indisponibles (%s)", asset.label, exc)
                continue
            candles = ind.closed_candles(raw, int(now.timestamp()), 300)
            if not candles or now.timestamp() - candles[-1].ts > 30 * 60:
                log.info("%s : dernière bougie clôturée trop ancienne (marché fermé ?)", asset.label)
                continue

            news_ctx = risk = None
            for hkey, base, variant in plan:
                if blocked[hkey]:
                    log.info("%s [%s] : %s", asset.label, hkey, "; ".join(blocked[hkey]))
                    continue
                a = assess(asset, candles, scan_cfg, weights, base_minutes=base, context=context)
                if asset.key == "bitcoin" and base == 5:
                    context["btc_dir"] = a.direction if a.direction else self._quick_direction(candles)
                if a.direction is None:
                    log.info("%s [%s] : %s", asset.label, hkey, "; ".join(a.reasons_rejected) or "aucune direction")
                    continue
                stubborn = self._direction_block(asset.key, a.direction, all_sigs, now)
                if stubborn:
                    log.info("%s [%s] : %s", asset.label, hkey, stubborn)
                    continue
                if news_ctx is None:
                    items: list[newsmod.NewsItem] = []
                    for c in NEWS_CATEGORIES.get(asset.key, ["macro"]):
                        if c not in news_cache:
                            news_cache[c] = newsmod.fetch_news([c], self.cfg.news_lookback_minutes, now)
                        items += news_cache[c]
                    risk, hits = newsmod.risk_score(items, asset.news_keywords)
                    news_ctx = ("actualité calme sur les 2 dernières heures" if risk == 0
                                else f"actualité à surveiller (score {risk}) : " + " | ".join(hits[:2]))
                if risk is not None and risk > self.cfg.max_news_risk_score:
                    log.info("%s [%s] : actualité incertaine (score %d) → pas de signal", asset.label, hkey, risk)
                    continue
                if caution:
                    news_ctx = f"prudence post-{caution.name} : critères renforcés · " + (news_ctx or "")
                sig, why = build_signal(asset, a, scan_cfg, news_ctx, now)
                if sig is not None:
                    sig.meta["price_time"] = self._candle_close_iso(candles)
                if sig is None:
                    log.info("%s [%s] : pas de signal (%s)", asset.label, hkey, "; ".join(why))
                    if self.cfg.shadow_enabled and not dry_run and base == 5 and not variant:
                        self._maybe_shadow(asset, a, news_ctx, now, all_sigs, scan_cfg)
                    continue
                if variant:
                    # même exigence qu'un signal réel, mais suivi en silence pour mesurer la variante
                    self._record_shadow(sig, variant, all_sigs)
                    log.info("%s [%s] : variante « %s » testée en fantôme (id %s)", asset.label, hkey, variant, sig.id)
                    continue
                produced.append(sig)
                all_sigs.append(sig)
                sim_line = ""
                if not dry_run:
                    sizing = self.portfolio.on_open(sig, asset)
                    sig.meta["sim"] = sizing
                    sim_line = self.portfolio.format_sizing(sizing, asset)
                    self.store.add_signal(sig)
                notify(format_signal(sig, self.cfg.timezone) + ("\n" + sim_line if sim_line else ""))
                log.info("%s [%s] : signal %s %s émis (id %s)", asset.label, hkey, sig.direction, sig.entry, sig.id)
        self._touch_state(now, note=f"{len(produced)} signal(aux)")
        if not dry_run:
            self.write_report()
        return produced

    @staticmethod
    def _candle_close_iso(candles: list) -> str:
        """Heure de clôture de la dernière bougie 5 min : l'heure du prix de référence du signal."""
        return iso(datetime.fromtimestamp(candles[-1].ts + 300, tz=timezone.utc))

    @staticmethod
    def _weights_for(adj: dict[str, Any], asset_key: str) -> dict[str, float] | None:
        """Poids appris pour cet actif : socle global, corrigé pour l'actif s'il a assez de preuves."""
        return (adj.get("weights_by_asset") or {}).get(asset_key) or adj.get("weights") or None

    def _scan_block(self, asset, horizon: str, base: int, variant: str | None, all_sigs: list[Signal],
                    now: datetime) -> list[str]:
        if base != 5 and not asset.long_horizon:
            return ["horizon 3 h désactivé pour cet actif"]
        if variant:
            return self._variant_block(asset.key, variant, horizon, all_sigs, now)
        return self._policy_block(asset.key, all_sigs, now, horizon=horizon)

    def _variant_block(self, asset_key: str, variant: str, horizon: str, all_sigs: list[Signal],
                       now: datetime) -> list[str]:
        """Contraintes d'une variante en test : les mêmes que pour un signal réel, sur ses propres fantômes."""
        today = now.astimezone(self.tz).date()
        # compteurs propres à la variante : les fantômes « faibles » ne doivent pas l'évincer
        mine = sorted((s for s in all_sigs if s.asset == asset_key and s.source == "shadow"
                       and (s.meta or {}).get("variant") == variant and (s.horizon or "1h") == horizon),
                      key=lambda s: s.created_at)
        reasons = []
        if sum(1 for s in mine if parse_iso(s.created_at).astimezone(self.tz).date() == today) >= self.cfg.shadow_max_per_asset_per_day:
            reasons.append("plafond quotidien de la variante atteint")
        if any(s.status == "open" for s in mine):
            reasons.append(f"variante « {variant} » déjà ouverte sur cet actif")
        if mine and now - parse_iso(mine[-1].created_at) < timedelta(minutes=self.cfg.cooldown_minutes):
            reasons.append("délai de refroidissement de la variante")
        return reasons

    def _record_shadow(self, sig: Signal, variant: str, all_sigs: list[Signal]) -> Signal:
        sig.source = "shadow"
        sig.meta["variant"] = variant
        self.store.add_shadow(sig)
        all_sigs.append(sig)
        return sig

    def _maybe_shadow(self, asset, a, news_ctx: str, now: datetime, all_sigs: list[Signal],
                      cfg: Config | None = None) -> Signal | None:
        """Signal fantôme : même construction TP / SL, seuils de confiance relâchés, jamais notifié.

        Étiquette « confiance_moyenne » s'il aurait passé la barre « moyen » (variante testée pour
        une éventuelle promotion), « faible » sinon (sert seulement à l'apprentissage)."""
        cfg = cfg or self.cfg
        if a.direction is None or a.n_criteria < self.cfg.shadow_min_criteria:
            return None
        today = now.astimezone(self.tz).date()
        mine = [s for s in all_sigs if s.asset == asset.key and s.source == "shadow"]
        if sum(1 for s in mine if parse_iso(s.created_at).astimezone(self.tz).date() == today) >= self.cfg.shadow_max_per_asset_per_day:
            return None
        if sum(1 for s in mine if s.status == "open") >= self.cfg.shadow_max_open_per_asset:
            return None
        sig, variant = None, "faible"
        if cfg.min_confidence == "fort":
            sig, _ = build_signal(asset, a, replace(cfg, min_confidence="moyen"), news_ctx, now)
            variant = "confiance_moyenne" if sig is not None else "faible"
        if sig is None:
            relaxed = copy.copy(cfg)
            relaxed.min_criteria = self.cfg.shadow_min_criteria
            relaxed.min_score = 0.0
            relaxed.min_confidence = "moyen"
            sig, why = build_signal(asset, a, relaxed, news_ctx, now)
            variant = "faible"
        if sig is None:
            return None
        self._record_shadow(sig, variant, all_sigs)
        log.info("%s : signal fantôme %s %s (id %s, %d critères)", asset.label, sig.direction, sig.entry, sig.id, sig.score and a.n_criteria)
        return sig

    def _policy_block(self, asset_key: str, all_sigs: list[Signal], now: datetime, horizon: str = "1h") -> list[str]:
        """Raisons de ne pas chercher de signal sur cet actif pour cet horizon (liste vide = autorisé)."""
        reasons = []
        today = now.astimezone(self.tz).date()
        visible = [s for s in all_sigs if s.asset == asset_key and s.source != "shadow"]
        mine = sorted((s for s in visible if (s.horizon or "1h") == horizon), key=lambda s: s.created_at)
        todays = [s for s in mine if parse_iso(s.created_at).astimezone(self.tz).date() == today]
        cap = self.cfg.max_signals_per_asset_per_day if horizon == "1h" else self.cfg.max_long_signals_per_asset_per_day
        if len(todays) >= cap:
            reasons.append(f"maximum quotidien atteint ({cap}, horizon {horizon})")
        losses_today = sum(1 for s in visible if s.status == "sl" and parse_iso(s.created_at).astimezone(self.tz).date() == today)
        if losses_today >= self.cfg.max_losses_per_asset_per_day:
            reasons.append(f"protection quotidienne : {self.cfg.max_losses_per_asset_per_day} stops déjà touchés")
        if any(s.status == "open" for s in mine):
            reasons.append(f"un signal {horizon} est déjà ouvert sur cet actif")
        if sum(1 for s in all_sigs if s.status == "open" and s.source != "shadow") >= self.cfg.max_open_signals:
            reasons.append(f"plafond de signaux ouverts atteint ({self.cfg.max_open_signals})")
        if mine:
            last = mine[-1]
            if now - parse_iso(last.created_at) < timedelta(minutes=self.cfg.cooldown_minutes):
                reasons.append("délai de refroidissement en cours")
        # Après un stop (quel que soit l'horizon), délai compté depuis la clôture, pas depuis l'émission.
        last_sl = max((parse_iso(s.closed_at) for s in visible if s.status == "sl" and s.closed_at), default=None)
        if last_sl and now - last_sl < timedelta(minutes=self.cfg.cooldown_after_loss_minutes):
            reasons.append("stop touché récemment sur cet actif : délai de refroidissement")
        return reasons

    def _direction_block(self, asset_key: str, direction: str, all_sigs: list[Signal], now: datetime) -> str | None:
        """Ne pas s'obstiner : après un stop dans un sens, pas de nouveau signal dans ce sens pendant N minutes."""
        minutes = self.cfg.same_direction_after_loss_minutes
        if minutes <= 0:
            return None
        recent = [s for s in all_sigs if s.asset == asset_key and s.source != "shadow" and s.status == "sl"
                  and s.direction == direction and s.closed_at
                  and now - parse_iso(s.closed_at) < timedelta(minutes=minutes)]
        if not recent:
            return None
        since = int((now - parse_iso(max(s.closed_at for s in recent))).total_seconds() // 60)
        return (f"stop {direction} touché il y a {since} min sur cet actif : pas de nouvelle tentative "
                f"dans le même sens avant {minutes} min")

    def post_event_caution(self, now: datetime, events: list[newsmod.MacroEvent]) -> newsmod.MacroEvent | None:
        """Événement majeur (FOMC, CPI, emploi) passé depuis moins de N heures : marché en repositionnement."""
        hours = self.cfg.post_event_caution_hours
        if hours <= 0:
            return None
        major = [ev for ev in events if ev.impact == "high" and not ev.assets and MAJOR_EVENT_RE.search(ev.name)
                 and timedelta(0) <= now - ev.at <= timedelta(hours=hours)]
        return max(major, key=lambda ev: ev.at) if major else None

    @staticmethod
    def _quick_direction(candles_5m: list) -> str | None:
        closes = [c.close for c in candles_5m]
        e20 = ind.ema(closes, 20)
        e50 = ind.ema(closes, 50)
        if e20[-1] is None or e50[-1] is None:
            return None
        if e20[-1] > e50[-1] * 1.0005:
            return "long"
        if e20[-1] < e50[-1] * 0.9995:
            return "short"
        return None

    # ------------------------------------------------------- simulation
    def set_balance(self, balance: float, risk_pct: float | None = None, now: datetime | None = None) -> dict[str, Any]:
        data = self.portfolio.set_balance(balance, risk_pct, now)
        self.write_report()
        return data

    # ------------------------------------------------------- contexte marché
    def correlation_context(self, now: datetime) -> dict[str, Any]:
        """Variations récentes des marchés meneurs (VIX 15 min, DXY et taux 10 ans sur 1 h)."""
        ctx: dict[str, Any] = {}
        for key, minutes, field in (("vix", 15, "vix_ret15"), ("dxy", 60, "dxy_ret60"), ("tnx", 60, "tnx_ret60")):
            try:
                candles = ind.closed_candles(market.fetch_leader_candles(key), int(now.timestamp()), 300)
                if candles and now.timestamp() - candles[-1].ts <= 30 * 60:
                    ctx[field] = ind.pct_change(candles, minutes)
            except ProviderError as exc:
                log.info("marché meneur %s indisponible (%s)", key, exc)
        return ctx

    def macro_events(self, now: datetime) -> list[newsmod.MacroEvent]:
        """Calendrier : événements manuels + rapport emploi + calendrier économique en ligne (cache)."""
        events = newsmod.load_calendar(self.store.calendar()) + newsmod.recurring_macro_events(now)
        try:
            events += calmod.fetch_events(self.store.calendar_cache_file)
        except Exception as exc:  # noqa: BLE001 — le calendrier ne doit jamais bloquer un passage
            log.warning("calendrier économique : %s", exc)
        return events

    def _touch_state(self, now: datetime, note: str = "") -> None:
        st = self.store.state()
        st["last_scan"] = iso(now)
        st["last_scan_note"] = note
        self.store.save_state(st)

    # ----------------------------------------------------------------- track
    def track(self, now: datetime | None = None) -> list[Signal]:
        """Met à jour les signaux ouverts (notifiés, manuels et fantômes). Renvoie ceux clôturés."""
        now = now or utcnow()
        open_sigs = self.store.open_signals()
        shadow = self.store.open_shadow()
        if not open_sigs and not shadow:
            return []
        cache: dict[str, tuple[list | None, float | None]] = {}

        def market_data(asset):
            if asset.key not in cache:
                candles = price = None
                try:
                    candles = market.fetch_candles_1m(asset)
                except ProviderError as exc:
                    log.warning("%s : bougies 1 min indisponibles (%s)", asset.label, exc)
                try:
                    price = market.fetch_price(asset)
                except ProviderError as exc:
                    log.warning("%s : prix indisponible (%s)", asset.label, exc)
                cache[asset.key] = (candles, price)
            return cache[asset.key]

        closed: list[Signal] = []
        remaining: list[Signal] = []
        for sig in open_sigs:
            asset = self.cfg.assets[sig.asset]
            candles, price = market_data(asset)
            done = update_signal(sig, candles, price, now, asset.cost_pct)
            if done is None:
                remaining.append(sig)
            else:
                closed.append(done)
                self.store.append_history(done)
                row = self.portfolio.on_close(done, asset)
                notify(format_outcome(done, self.cfg.timezone) + ("\n" + self.portfolio.format_outcome(row) if row else ""))
        self.store.save_open(remaining)

        remaining_shadow: list[Signal] = []
        closed_shadow = 0
        for sig in shadow:
            asset = self.cfg.assets[sig.asset]
            candles, price = market_data(asset)
            done = update_signal(sig, candles, price, now, asset.cost_pct)
            if done is None:
                remaining_shadow.append(sig)
            else:
                closed_shadow += 1
                self.store.append_history(done)
        self.store.save_shadow(remaining_shadow)
        if closed_shadow:
            log.info("%d signal(aux) fantôme(s) clôturé(s)", closed_shadow)

        if closed or closed_shadow:
            self._relearn()
            self.write_report()
        st = self.store.state()
        st["last_track"] = iso(now)
        self.store.save_state(st)
        return closed

    def _relearn(self) -> dict[str, Any]:
        """Recalcule entièrement les poids à partir de tous les trades clôturés (réels, fantômes,
        backtest) et annonce les variantes promues ou retirées."""
        before = set(self.store.adjustments().get("promoted_variants") or [])
        sample = self.store.history()
        if self.cfg.learn_from_backtest:
            sample = sample + self.store.backtest_trades()
        adj = learn(sample, self.cfg)
        self.store.save_adjustments(adj)
        if self.cfg.variants_enabled:
            after = set(adj.get("promoted_variants") or [])
            for key in sorted(after - before):
                v = adj["variants"][key]
                notify(f"🧪 VARIANTE PROMUE : {v['label']}\nSur {v['n']} trades suivis en silence, elle fait au moins "
                       f"aussi bien que les signaux réels ({v['mean_net_r']:+.2f} R net par trade). "
                       f"Elle passe désormais en signaux réels.")
            for key in sorted(before - after):
                v = (adj.get("variants") or {}).get(key, {"label": key})
                notify(f"🧪 VARIANTE RETIRÉE : {v['label']}\nSes résultats sont repassés sous ceux des signaux "
                       f"réels : elle retourne en test silencieux.")
        return adj

    # ---------------------------------------------------------------- manuel
    @staticmethod
    def _apply_custom_levels(sig: Signal, asset, take_profit: float | None, stop_loss: float | None) -> list[str]:
        """Remplace l'objectif et/ou le stop calculés par ceux demandés. Renvoie les mentions à afficher."""
        entry = sig.entry
        tp = round_to_tick(float(take_profit), asset.tick_size) if take_profit is not None else sig.take_profit
        sl = round_to_tick(float(stop_loss), asset.tick_size) if stop_loss is not None else sig.stop_loss
        side = "au-dessus" if sig.direction == "long" else "en dessous"
        other = "en dessous" if sig.direction == "long" else "au-dessus"
        ok_tp = tp > entry if sig.direction == "long" else tp < entry
        ok_sl = sl < entry if sig.direction == "long" else sl > entry
        if not ok_tp:
            raise ValueError(f"pour un {sig.direction}, l'objectif ({tp:g}) doit être {side} de l'entrée ({entry:g})")
        if not ok_sl:
            raise ValueError(f"pour un {sig.direction}, le stop ({sl:g}) doit être {other} de l'entrée ({entry:g})")
        sig.take_profit, sig.stop_loss = tp, sl
        risk = abs(entry - sl)
        sig.risk_reward = round(abs(tp - entry) / risk, 2) if risk else 0.0
        mentions = []
        if take_profit is not None:
            mentions.append(f"objectif imposé {tp:g}")
        if stop_loss is not None:
            mentions.append(f"stop imposé {sl:g}")
        return mentions

    def manual(self, asset_key: str, direction: str, now: datetime | None = None, note: str = "",
               take_profit: float | None = None, stop_loss: float | None = None) -> Signal:
        """Signal demandé par l'utilisateur. Objectif et stop calibrés par le bot, ou imposés si fournis."""
        from dataclasses import replace

        now = now or utcnow()
        if asset_key not in self.cfg.assets:
            raise ValueError(f"actif inconnu : {asset_key}")
        if direction not in ("long", "short"):
            raise ValueError("direction attendue : long ou short")
        asset = self.cfg.assets[asset_key]
        raw = market.fetch_candles_5m(asset, days=5)
        candles = ind.closed_candles(raw, int(now.timestamp()), 300) or raw
        a = assess(asset, candles, self.cfg)
        price_time = self._candle_close_iso(candles)
        try:
            a.price = market.fetch_price(asset)
            price_time = None                    # cotation instantanée : son âge exact n'est pas connu
        except ProviderError:
            pass
        a = replace(a, direction=direction, reasons_rejected=[])
        relaxed = copy.copy(self.cfg)
        relaxed.min_criteria = 0
        relaxed.min_score = 0.0
        relaxed.min_confidence = "moyen"
        relaxed.min_resolution_probability = 0.0
        relaxed.min_tp_to_cost_ratio = 0.0  # décision explicite de l'utilisateur : on avertit, on ne bloque pas
        # les niveaux clés ne doivent pas empêcher une demande explicite : on garde le calibrage sur le range
        a = replace(a, support=None, resistance=None)
        sig, why = build_signal(asset, a, relaxed, f"demande manuelle{(' : ' + note) if note else ''}", now)
        if sig is None:
            raise RuntimeError("impossible de construire des niveaux réalistes : " + "; ".join(why))
        sig.source = "manual"
        sig.confidence = "manuel"
        if price_time:
            sig.meta["price_time"] = price_time
        custom = self._apply_custom_levels(sig, asset, take_profit, stop_loss) if (take_profit is not None or stop_loss is not None) else []
        crit = ", ".join(sig.criteria) if sig.criteria else "aucun"
        sig.rationale = (f"Demande manuelle {direction}. Critères du bot alignés dans ce sens : {crit}. " + sig.rationale.split(". ", 1)[-1])
        if custom:
            # le calibrage automatique (fractions du range, probabilité de résolution) ne décrit plus
            # les niveaux réellement suivis : on le retire pour ne pas induire en erreur
            sig.rationale = re.sub(r",\s*TP = .*?probabilité de résolution[^.]*\.", ".", sig.rationale)
            sig.rationale += f" Niveaux fournis par vous : {', '.join(custom)} (rapport gain/risque {sig.risk_reward})."
            sig.meta["custom_levels"] = True
        tp_pct = abs(sig.take_profit - sig.entry) / sig.entry * 100.0
        if asset.cost_pct > 0 and tp_pct < self.cfg.min_tp_to_cost_ratio * asset.cost_pct:
            sig.rationale += f" ⚠️ Cible petite face aux coûts estimés ({tp_pct:.2f} % pour {asset.cost_pct:.2f} % de frais)."
        sizing = self.portfolio.on_open(sig, asset)
        sig.meta["sim"] = sizing
        self.store.add_signal(sig)
        notify("🖐️ SIGNAL MANUEL\n" + format_signal(sig, self.cfg.timezone) + "\n" + self.portfolio.format_sizing(sizing, asset))
        self.write_report()
        return sig

    # --------------------------------------------------------------- summary
    def summary_day(self, now: datetime | None = None):
        """Jour résumé par défaut : la journée de trading la plus récente. Lancé après minuit (jusqu'à
        midi heure locale), le résumé porte sur la veille ; lancé l'après-midi ou le soir, sur le jour même."""
        local = (now or utcnow()).astimezone(self.tz)
        return (local - timedelta(days=1)).date() if local.hour < 12 else local.date()

    def summary(self, day=None, send: bool = True) -> str:
        day = day or self.summary_day()
        adj = self._relearn()
        text = daily_summary(self.store.all_signals(), self.cfg, day, adj)
        text += "\n\n" + self.portfolio.format_summary()
        try:
            now = utcnow()
            agenda = calmod.upcoming(self.macro_events(now), now, hours=30, min_impact="high")
            text += ("\n\nAnnonces à fort impact dans les 30 prochaines heures :\n"
                     + calmod.format_agenda(agenda, self.cfg.timezone))
        except Exception as exc:  # noqa: BLE001
            log.warning("agenda indisponible : %s", exc)
        if send:
            notify(text)
        self.write_report()
        st = self.store.state()
        st["last_summary"] = iso(utcnow())
        self.store.save_state(st)
        return text

    # ------------------------------------------------------------ proposition
    def propose(self, asset_key: str, now: datetime | None = None) -> dict[str, Any]:
        """Analyse immédiate d'un actif à la demande : le bot dit ce qu'il voit et, s'il y a une
        direction, propose un trade calibré (suivi comme les autres, source « request »).
        S'il n'y a pas de direction, il s'abstient et l'explique."""
        from .analysis import confidence_label
        from .signals import criterion_label

        now = now or utcnow()
        if asset_key not in self.cfg.assets:
            raise ValueError(f"actif inconnu : {asset_key}")
        asset = self.cfg.assets[asset_key]
        raw = market.fetch_candles_5m(asset, days=5)
        candles = ind.closed_candles(raw, int(now.timestamp()), 300) or raw
        stale = now.timestamp() - candles[-1].ts > 30 * 60
        a = assess(asset, candles, self.cfg, self._weights_for(self.store.adjustments(), asset.key))
        try:
            a.price = market.fetch_price(asset)
        except ProviderError:
            pass
        items: list[newsmod.NewsItem] = []
        for c in NEWS_CATEGORIES.get(asset.key, ["macro"]):
            items += newsmod.fetch_news([c], self.cfg.news_lookback_minutes, now)
        risk, hits = newsmod.risk_score(items, asset.news_keywords)
        news_ctx = ("actualité calme sur les 2 dernières heures" if risk == 0
                    else f"actualité à surveiller (score {risk}) : " + " | ".join(hits[:2]))

        lecture = "\n".join(f"  • {criterion_label(k)} : {v}" for k, v in a.details.items())
        header = f"🔎 ANALYSE À LA DEMANDE — {asset.label} — prix {a.price:.{asset.price_decimals}f}"
        already = next((s for s in self.store.open_signals() if s.asset == asset_key), None)

        if stale:
            text = header + "\n\nMarché fermé ou données trop anciennes : pas de proposition.\n\nLecture des indicateurs :\n" + lecture
            notify(text)
            return {"proposed": False, "reason": "marché fermé", "text": text}
        if already is not None:
            text = (header + f"\n\nUn signal est déjà ouvert sur cet actif (id {already.id}, {already.direction} @ {already.entry}, "
                    f"TP {already.take_profit}, SL {already.stop_loss}). Attendez son issue.\n\nLecture des indicateurs :\n" + lecture)
            notify(text)
            return {"proposed": False, "reason": "signal déjà ouvert", "text": text, "signal": already.to_dict()}
        if a.direction is None:
            why = "; ".join(a.reasons_rejected) or "aucune direction dominante"
            text = (header + f"\n\n❌ Je m'abstiens : {why}.\nActualité : {news_ctx}\n\nLecture des indicateurs :\n" + lecture)
            notify(text)
            return {"proposed": False, "reason": why, "text": text}

        relaxed = copy.copy(self.cfg)
        relaxed.min_criteria = 1
        relaxed.min_score = 0.0
        relaxed.min_confidence = "moyen"
        sig, why = build_signal(asset, a, relaxed, news_ctx, now)
        if sig is None:
            text = (header + f"\n\n❌ Direction {a.direction} ({a.n_criteria} critère(s)) mais pas de niveaux réalistes : "
                    + "; ".join(why) + f"\nActualité : {news_ctx}\n\nLecture des indicateurs :\n" + lecture)
            notify(text)
            return {"proposed": False, "reason": "; ".join(why), "text": text}

        conf = confidence_label(a.score, a.n_criteria, self.cfg)
        sig.source = "request"
        sig.confidence = conf or "faible"
        verdict = {"fort": "✅ Ce setup passe mes critères (confiance forte).",
                   "moyen": "✅ Ce setup passe mes critères (confiance moyenne)."}.get(
            conf, f"⚠️ Ce setup ne passe PAS mes critères ({a.n_criteria} critère(s) aligné(s), score {a.score}) : je ne l'aurais pas envoyé seul.")
        if risk > self.cfg.max_news_risk_score:
            verdict += f" ⚠️ Actualité à risque (score {risk})."
        sizing = self.portfolio.on_open(sig, asset)
        sig.meta["sim"] = sizing
        self.store.add_signal(sig)
        text = (header + "\n\n" + verdict + "\n\n" + format_signal(sig, self.cfg.timezone)
                + "\n" + self.portfolio.format_sizing(sizing, asset)
                + "\n\nLecture des indicateurs :\n" + lecture)
        notify(text)
        self.write_report()
        return {"proposed": True, "verdict": verdict, "text": text, "signal": sig.to_dict()}

    # ---------------------------------------------------------------- report
    def write_report(self) -> str:
        backtests = self.store.backtests()
        all_sigs = self.store.all_signals()
        adjustments = self.store.adjustments()
        text = build_report(all_sigs, self.cfg, adjustments, backtests)
        self.store.save_report(text)
        dash = build_dashboard(all_sigs, self.cfg, adjustments, backtests, self.store.state())
        dash["portfolio"] = self.portfolio.summary()
        self.store.save_dashboard(dash)
        return text

    # ------------------------------------------------------------ données
    def fetch_data(self, days: int = 60, asset_keys: list[str] | None = None) -> dict[str, int]:
        """Enregistre l'historique 5 min dans data/candles/ (backtests hors ligne, reproductibles)."""
        out: dict[str, int] = {}
        for key, asset in self.cfg.assets.items():
            if asset_keys and key not in asset_keys:
                continue
            try:
                fresh = market.fetch_candles_5m(asset, days=days)
            except ProviderError as exc:
                log.warning("%s : données indisponibles (%s)", asset.label, exc)
                continue
            known = {c.ts: c for c in self.store.load_candles(key)}
            known.update({c.ts: c for c in fresh})
            merged = [known[ts] for ts in sorted(known)]
            self.store.save_candles(key, merged)
            out[key] = len(merged)
            log.info("%s : %d bougies 5 min enregistrées", asset.label, len(merged))
        return out

    # -------------------------------------------------------------- backtest
    def backtest(self, days: int = 30, asset_keys: list[str] | None = None, send: bool = False,
                 offline: bool = False) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for key, asset in self.cfg.assets.items():
            if asset_keys and key not in asset_keys:
                continue
            if offline:
                candles = self.store.load_candles(key)
                if candles:
                    cutoff = candles[-1].ts - days * 86400
                    candles = [c for c in candles if c.ts >= cutoff]
                if not candles:
                    log.warning("%s : aucune bougie hors ligne (lancez d'abord `fetch-data`)", asset.label)
                    continue
            else:
                try:
                    candles = market.fetch_candles_5m(asset, days=days)
                except ProviderError as exc:
                    log.warning("%s : données indisponibles pour le backtest (%s)", asset.label, exc)
                    continue
            bases = [5] + ([self.cfg.long_horizon_base_minutes] if (self.cfg.long_horizon_enabled and asset.long_horizon) else [])
            for base in bases:
                res = run_backtest(asset, candles, self.cfg, base_minutes=base)
                results[key if base == 5 else f"{key}_{res['horizon']}"] = res
                text = format_backtest(res)
                print(text, flush=True)
                if send:
                    notify(text)
        if results:
            # backtest complet (tous les actifs) : il remplace l'ancien, rien de figé ne subsiste
            self.store.save_backtests(results, replace=not asset_keys)
            self.write_report()
        return results

    # -------------------------------------------------------------- commandes
    ASSET_ALIASES = {
        "nasdaq": "nasdaq", "nq": "nasdaq", "ndx": "nasdaq",
        "sp500": "sp500", "sp": "sp500", "spx": "sp500", "es": "sp500", "s&p": "sp500", "s&p500": "sp500",
        "bitcoin": "bitcoin", "btc": "bitcoin",
        "ethereum": "ethereum", "eth": "ethereum",
        "gold": "gold", "or": "gold", "xau": "gold", "xauusd": "gold",
        "oil": "oil", "petrole": "oil", "pétrole": "oil", "wti": "oil", "cl": "oil", "mcl": "oil", "crude": "oil",
        "euro": "euro", "eur": "euro", "eurusd": "euro", "eur/usd": "euro", "6e": "euro", "m6e": "euro",
    }
    HELP = (
        "📖 GUIDE DU BOT — toutes les commandes\n"
        "\n"
        "Ce bot repère des opportunités de scalping sur 5 marchés et vous les envoie ici. "
        "Il n'exécute AUCUN ordre réel : il propose, vous décidez.\n"
        "\n"
        "▶️ CONSULTER\n"
        "/status — les signaux actuellement ouverts (entrée, objectif, stop)\n"
        "/resume — le bilan de la dernière journée : trades, réussite, enseignements\n"
        "/balance — l'état de la simulation de compte, sans rien modifier\n"
        "/help — ce message\n"
        "\n"
        "▶️ DEMANDER UNE ANALYSE\n"
        "/propose <actif> — le bot analyse l'actif maintenant et propose un trade s'il en voit un\n"
        "/long <actif> [objectif] [stop] [commentaire] — signal manuel à l'achat\n"
        "/short <actif> [objectif] [stop] [commentaire] — signal manuel à la vente\n"
        "Sans chiffres, le bot calibre l'objectif et le stop sur la volatilité du moment. "
        "Avec, ce sont vos niveaux qui sont suivis : l'objectif d'abord, le stop ensuite.\n"
        "\n"
        "Actifs : nasdaq (nq) · sp500 (es) · bitcoin (btc) · ethereum (eth) · gold (or) · "
        "petrole (wti) · euro (eurusd).{trial}\n"
        "Exemples : /propose btc — /long nasdaq cassure du plus haut — /short eth 2450 2530 rejet\n"
        "\n"
        "⛔ À NE PAS UTILISER\n"
        "/balance <montant> — ne changez PAS la balance. Suivie d'un montant, cette commande "
        "remet la simulation de compte à zéro pour tout le monde et archive les trades en cours. "
        "Elle est réservée au propriétaire du bot. Un mode invité viendra l'empêcher ; "
        "en attendant, tapez /balance seul pour consulter, jamais avec un montant.\n"
        "\n"
        "📊 Tableau de bord : https://yxnisse7.github.io/Trading-Bot/\n"
        "💼 Simulation de compte : https://yxnisse7.github.io/Trading-Bot/portfolio.html"
    )

    def help_text(self) -> str:
        """Guide des commandes, avec la liste à jour des actifs à l'essai."""
        promoted = set(self.store.adjustments().get("promoted_variants") or [])
        trial = [a.label for k, a in self.cfg.assets.items() if a.trial and f"essai_{k}" not in promoted]
        line = (f" À l'essai : {', '.join(trial)}. Le bot les suit en silence et ne les annoncera qu'une fois "
                f"qu'ils auront fait leurs preuves." if trial else "")
        return self.HELP.replace("{trial}", line)

    def welcome_new_chats(self) -> list[str]:
        """Envoie le guide aux chats autorisés qui ne l'ont jamais reçu (une fois par chat)."""
        st = self.store.state()
        stored = list(st.get("telegram_welcomed", []))
        welcomed = chat_keys(stored)
        new = [c for c in telegram_chat_ids() if chat_key(c) not in welcomed]
        for chat in new:
            notify(self.help_text() + "\n\n" + DISCLAIMER, chat_id=chat)
            welcomed.append(chat_key(chat))
            log.info("guide envoyé à un nouveau chat (%s)", chat_key(chat))
        if not new and welcomed == stored:
            return []
        st = self.store.state()
        st["telegram_welcomed"] = welcomed[-50:]
        st["telegram_informed"] = chat_keys(st.get("telegram_informed", []))
        self.store.save_state(st)
        return new

    def send_help(self) -> str:
        """Envoie le guide à tous les chats configurés (et les marque comme informés)."""
        notify(self.help_text() + "\n\n" + DISCLAIMER)
        st = self.store.state()
        known = chat_keys(st.get("telegram_welcomed", [])) + [chat_key(c) for c in telegram_chat_ids()]
        st["telegram_welcomed"] = list(dict.fromkeys(known))[-50:]
        self.store.save_state(st)
        return self.help_text()

    def handle_command(self, text: str, now: datetime | None = None) -> str | None:
        """Exécute une commande texte (Telegram). Renvoie la réponse à envoyer, ou None si ignorée."""
        now = now or utcnow()
        parts = text.strip().split()
        if not parts or not parts[0].startswith("/"):
            return None
        cmd = parts[0].lower().split("@", 1)[0]
        args = parts[1:]
        if cmd in ("/help", "/start", "/aide"):
            return self.help_text()
        if cmd == "/status":
            sigs = self.store.open_signals()
            if not sigs:
                return "Aucun signal ouvert."
            return "\n\n".join(format_signal(s, self.cfg.timezone) for s in sigs)
        if cmd in ("/resume", "/résumé", "/summary"):
            return self.summary(send=False)
        if cmd == "/balance":
            if not args:
                return self.portfolio.format_summary()
            try:
                amount = float(args[0].replace(",", ".").replace("€", "").replace("$", ""))
                risk = float(args[1].replace(",", ".").replace("%", "")) if len(args) > 1 else None
                self.set_balance(amount, risk, now)
                return "Simulation réinitialisée.\n" + self.portfolio.format_summary()
            except ValueError as exc:
                return f"Balance invalide : {exc}. Exemple : /balance 1000 1"
        if cmd in ("/propose", "/long", "/short"):
            if not args:
                return f"Précisez l'actif : {cmd} bitcoin"
            asset_key = self.ASSET_ALIASES.get(args[0].lower())
            if asset_key is None:
                return f"Actif inconnu « {args[0]} ». " + self.help_text()
            try:
                if cmd == "/propose":
                    self.propose(asset_key, now)   # envoie lui-même la notification
                    return None
                levels, rest = self._parse_levels(args[1:])
                note = " ".join(rest)[:200]
                self.manual(asset_key, "long" if cmd == "/long" else "short", now, note=note,
                            take_profit=levels[0], stop_loss=levels[1])  # notifie lui-même
                return None
            except (ProviderError, RuntimeError, ValueError) as exc:
                return f"Impossible de traiter {cmd} {args[0]} : {exc}"
        return None

    @staticmethod
    def _parse_levels(args: list[str]) -> tuple[tuple[float | None, float | None], list[str]]:
        """Lit « <TP> <SL> » en tête des arguments : les nombres sont des niveaux, le reste un commentaire."""
        levels: list[float] = []
        rest = list(args)
        while rest and len(levels) < 2:
            token = rest[0].replace(",", ".").replace("$", "").replace("€", "")
            try:
                levels.append(float(token))
            except ValueError:
                break
            rest.pop(0)
        tp = levels[0] if levels else None
        sl = levels[1] if len(levels) > 1 else None
        return (tp, sl), rest

    def process_commands(self, now: datetime | None = None) -> int:
        """Lit les messages Telegram reçus depuis le dernier passage et exécute les commandes.

        Seuls les messages du chat configuré (TELEGRAM_CHAT_ID) sont pris en compte.
        """
        allowed = set(telegram_chat_ids())
        if not allowed:
            return 0
        st = self.store.state()
        offset = st.get("telegram_offset")
        updates = telegram_updates(offset)
        if not updates:
            return 0
        handled = 0
        last_id = offset
        informed: list[str] = chat_keys(st.get("telegram_informed", []))
        for upd in updates:
            last_id = max(last_id or 0, (upd.get("update_id") or 0) + 1)
            if upd["chat_id"] not in allowed:
                log.warning("message Telegram ignoré (chat %s non autorisé)", upd["chat_id"])
                if chat_key(upd["chat_id"]) not in informed:
                    informed.append(chat_key(upd["chat_id"]))
                    notify("Ce bot est privé. Votre identifiant de chat est " + upd["chat_id"]
                           + " : transmettez-le au propriétaire pour qu'il vous ajoute.", chat_id=upd["chat_id"])
                continue
            # messages trop anciens (avant la mise en service) : ignorés pour ne pas rejouer d'anciens /start
            if upd.get("date") and (now or utcnow()).timestamp() - upd["date"] > 6 * 3600:
                continue
            try:
                reply = self.handle_command(upd["text"], now)
            except Exception as exc:  # noqa: BLE001 — une commande ne doit pas casser le passage
                log.exception("commande en erreur : %s", upd["text"])
                reply = f"Erreur en traitant « {upd['text']} » : {exc}"
            if reply:
                notify(reply, chat_id=upd["chat_id"])
            handled += 1
        st = self.store.state()
        st["telegram_offset"] = last_id
        st["telegram_informed"] = informed[-50:]
        st["telegram_welcomed"] = chat_keys(st.get("telegram_welcomed", []))
        self.store.save_state(st)
        return handled

    # ------------------------------------------------------------- live
    LIVE_CANDLES = 80          # ~6 h 40 d'historique en 5 min

    def write_live_snapshot(self, now: datetime | None = None) -> list[str]:
        """Publie, pour chaque actif, les dernières bougies 5 min et les niveaux des signaux ouverts.

        Sert le graphique « live » du site : rafraîchi à chaque passage du bot (≈ 5 min).
        """
        now = now or utcnow()
        open_sigs = [s for s in self.store.open_signals() if s.source != "shadow"]
        written = []
        for key, asset in self.cfg.assets.items():
            try:
                raw = market.fetch_candles_5m(asset, days=2)
            except ProviderError as exc:
                log.info("%s : instantané live indisponible (%s)", asset.label, exc)
                continue
            # closed_candles attend la DURÉE d'une bougie (5 min), pas un nombre : on tronque ensuite
            candles = ind.closed_candles(raw, int(now.timestamp()), 300)[-self.LIVE_CANDLES:]
            if not candles:
                continue
            digits = max(0, len(str(asset.tick_size).split(".")[-1])) if asset.tick_size < 1 else 2
            r = lambda v: round(float(v), digits)  # noqa: E731
            levels = [{"id": s.id, "direction": s.direction, "entry": s.entry, "take_profit": s.take_profit,
                       "stop_loss": s.stop_loss, "source": s.source, "horizon": s.horizon or "1h",
                       "created_at": s.created_at, "expires_at": s.expires_at}
                      for s in open_sigs if s.asset == key]
            self.store.save_live(key, {
                "asset": key, "label": asset.label, "updated_at": iso(now), "interval": "5m",
                "candles": [[c.ts, r(c.open), r(c.high), r(c.low), r(c.close)] for c in candles],
                "last": r(candles[-1].close), "open_signals": levels,
            })
            written.append(key)
        return written

    # ------------------------------------------------------------------ tick
    def tick(self, now: datetime | None = None) -> dict[str, Any]:
        """Un passage complet : commandes reçues, suivi des signaux ouverts, puis scan si l'intervalle est écoulé."""
        now = now or utcnow()
        try:
            self.welcome_new_chats()
        except Exception:  # noqa: BLE001 — un guide non envoyé ne doit pas casser le passage
            log.exception("envoi du guide aux nouveaux chats")
        try:
            self.process_commands(now)
        except Exception:  # noqa: BLE001
            log.exception("traitement des commandes Telegram")
        closed = self.track(now)
        try:
            self.write_live_snapshot(now)
        except Exception:  # noqa: BLE001 — le graphique ne doit jamais casser un passage
            log.exception("instantané live")
        st = self.store.state()
        last_scan = parse_iso(st["last_scan"]) if st.get("last_scan") else None
        new: list[Signal] = []
        if last_scan is None or now - last_scan >= timedelta(minutes=self.cfg.scan_interval_minutes - 1):
            new = self.scan(now)
        return {"closed": [s.id for s in closed], "new": [s.id for s in new]}
