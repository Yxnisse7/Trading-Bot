"""Orchestration : scan (génération de signaux), track (suivi), summary (bilan), tick, backtest."""
from __future__ import annotations

import copy
import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from . import indicators as ind
from .analysis import assess
from .backtest import format_backtest, run_backtest
from .config import DISCLAIMER, Config, load_config
from .learning import learn
from .models import Signal, iso, parse_iso, utcnow
from .notify import notify, telegram_chat_ids, telegram_updates
from .providers import market
from .providers import news as newsmod
from .providers.http import ProviderError
from .report import build_dashboard, build_report
from .signals import build_signal, format_signal
from .storage import Store
from .summary import daily_summary
from .tracker import format_outcome, update_signal

log = logging.getLogger(__name__)

NEWS_CATEGORIES = {"nasdaq": ["macro"], "sp500": ["macro"], "bitcoin": ["crypto", "macro"],
                   "ethereum": ["crypto", "macro"], "gold": ["gold", "macro"]}


class Engine:
    def __init__(self, cfg: Config | None = None, store: Store | None = None):
        self.cfg = cfg or load_config()
        self.store = store or Store()
        self.tz = ZoneInfo(self.cfg.timezone)

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
            log.info("Blackout macro : %s à %s UTC — aucun signal", blackout.name, blackout.at.strftime("%H:%M"))
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
                raw = market.fetch_candles_5m(asset, days=5)
            except ProviderError as exc:
                log.warning("%s : données indisponibles (%s)", asset.label, exc)
                continue
            candles = ind.closed_candles(raw, int(now.timestamp()), 300)
            if not candles or now.timestamp() - candles[-1].ts > 30 * 60:
                log.info("%s : dernière bougie clôturée trop ancienne (marché fermé ?)", asset.label)
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
                if self.cfg.shadow_enabled and not dry_run:
                    self._maybe_shadow(asset, a, news_ctx, now, all_sigs)
                continue
            produced.append(sig)
            all_sigs.append(sig)
            if not dry_run:
                self.store.add_signal(sig)
            notify(format_signal(sig, self.cfg.timezone) + "\n\n" + DISCLAIMER)
            log.info("%s : signal %s %s émis (id %s)", asset.label, sig.direction, sig.entry, sig.id)
        self._touch_state(now, note=f"{len(produced)} signal(aux)")
        if not dry_run:
            self.write_report()
        return produced

    def _maybe_shadow(self, asset, a, news_ctx: str, now: datetime, all_sigs: list[Signal]) -> Signal | None:
        """Signal fantôme : même construction TP / SL, seuils de confiance relâchés, jamais notifié."""
        if a.direction is None or a.n_criteria < self.cfg.shadow_min_criteria:
            return None
        today = now.astimezone(self.tz).date()
        mine = [s for s in all_sigs if s.asset == asset.key and s.source == "shadow"]
        if sum(1 for s in mine if parse_iso(s.created_at).astimezone(self.tz).date() == today) >= self.cfg.shadow_max_per_asset_per_day:
            return None
        if sum(1 for s in mine if s.status == "open") >= self.cfg.shadow_max_open_per_asset:
            return None
        relaxed = copy.copy(self.cfg)
        relaxed.min_criteria = self.cfg.shadow_min_criteria
        relaxed.min_score = 0.0
        relaxed.min_confidence = "moyen"
        sig, why = build_signal(asset, a, relaxed, news_ctx, now)
        if sig is None:
            return None
        sig.source = "shadow"
        self.store.add_shadow(sig)
        all_sigs.append(sig)
        log.info("%s : signal fantôme %s %s (id %s, %d critères)", asset.label, sig.direction, sig.entry, sig.id, sig.score and a.n_criteria)
        return sig

    def _policy_block(self, asset_key: str, all_sigs: list[Signal], now: datetime) -> list[str]:
        reasons = []
        today = now.astimezone(self.tz).date()
        mine = sorted((s for s in all_sigs if s.asset == asset_key and s.source != "shadow"), key=lambda s: s.created_at)
        todays = [s for s in mine if parse_iso(s.created_at).astimezone(self.tz).date() == today]
        if len(todays) >= self.cfg.max_signals_per_asset_per_day:
            reasons.append(f"maximum quotidien atteint ({self.cfg.max_signals_per_asset_per_day})")
        if sum(1 for s in todays if s.status == "sl") >= self.cfg.max_losses_per_asset_per_day:
            reasons.append(f"protection quotidienne : {self.cfg.max_losses_per_asset_per_day} stops déjà touchés")
        if any(s.status == "open" for s in mine):
            reasons.append("un signal est déjà ouvert sur cet actif")
        if sum(1 for s in all_sigs if s.status == "open" and s.source != "shadow") >= self.cfg.max_open_signals:
            reasons.append(f"plafond de signaux ouverts atteint ({self.cfg.max_open_signals})")
        if mine:
            last = mine[-1]
            cooldown = self.cfg.cooldown_after_loss_minutes if last.status == "sl" else self.cfg.cooldown_minutes
            if now - parse_iso(last.created_at) < timedelta(minutes=cooldown):
                reasons.append("délai de refroidissement en cours")
        return reasons

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
                notify(format_outcome(done, self.cfg.timezone))
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
        sample = self.store.history()
        if self.cfg.learn_from_backtest:
            sample = sample + self.store.backtest_trades()
        adj = learn(sample, self.cfg, self.store.adjustments())
        self.store.save_adjustments(adj)
        return adj

    # ---------------------------------------------------------------- manuel
    def manual(self, asset_key: str, direction: str, now: datetime | None = None, note: str = "") -> Signal:
        """Signal demandé par l'utilisateur : niveaux calibrés par le bot, notifié et suivi comme les autres."""
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
        try:
            a.price = market.fetch_price(asset)
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
        crit = ", ".join(sig.criteria) if sig.criteria else "aucun"
        sig.rationale = (f"Demande manuelle {direction}. Critères du bot alignés dans ce sens : {crit}. " + sig.rationale.split(". ", 1)[-1])
        tp_pct = abs(sig.take_profit - sig.entry) / sig.entry * 100.0
        if asset.cost_pct > 0 and tp_pct < self.cfg.min_tp_to_cost_ratio * asset.cost_pct:
            sig.rationale += f" ⚠️ Cible petite face aux coûts estimés ({tp_pct:.2f} % pour {asset.cost_pct:.2f} % de frais)." 
        self.store.add_signal(sig)
        notify("🖐️ SIGNAL MANUEL\n" + format_signal(sig, self.cfg.timezone) + "\n\n" + DISCLAIMER)
        self.write_report()
        return sig

    # --------------------------------------------------------------- summary
    def summary(self, day=None, send: bool = True) -> str:
        adj = self._relearn()
        text = daily_summary(self.store.all_signals(), self.cfg, day, adj)
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
        a = assess(asset, candles, self.cfg, self.store.adjustments().get("weights") or None)
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
            text = (header + f"\n\n❌ Je m'abstiens : {why}.\nActualité : {news_ctx}\n\nLecture des indicateurs :\n" + lecture
                    + "\n\n" + DISCLAIMER)
            notify(text)
            return {"proposed": False, "reason": why, "text": text}

        relaxed = copy.copy(self.cfg)
        relaxed.min_criteria = 1
        relaxed.min_score = 0.0
        relaxed.min_confidence = "moyen"
        sig, why = build_signal(asset, a, relaxed, news_ctx, now)
        if sig is None:
            text = (header + f"\n\n❌ Direction {a.direction} ({a.n_criteria} critère(s)) mais pas de niveaux réalistes : "
                    + "; ".join(why) + f"\nActualité : {news_ctx}\n\nLecture des indicateurs :\n" + lecture + "\n\n" + DISCLAIMER)
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
        self.store.add_signal(sig)
        text = (header + "\n\n" + verdict + "\n\n" + format_signal(sig, self.cfg.timezone)
                + "\n\nLecture des indicateurs :\n" + lecture + "\n\n" + DISCLAIMER)
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
        self.store.save_dashboard(build_dashboard(all_sigs, self.cfg, adjustments, backtests, self.store.state()))
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
            res = run_backtest(asset, candles, self.cfg)
            results[key] = res
            text = format_backtest(res)
            print(text, flush=True)
            if send:
                notify(text)
        if results:
            self.store.save_backtests(results)
            self.write_report()
        return results

    # -------------------------------------------------------------- commandes
    ASSET_ALIASES = {
        "nasdaq": "nasdaq", "nq": "nasdaq", "ndx": "nasdaq",
        "sp500": "sp500", "sp": "sp500", "spx": "sp500", "es": "sp500", "s&p": "sp500", "s&p500": "sp500",
        "bitcoin": "bitcoin", "btc": "bitcoin",
        "ethereum": "ethereum", "eth": "ethereum",
        "gold": "gold", "or": "gold", "xau": "gold", "xauusd": "gold",
    }
    HELP = ("Commandes disponibles :\n"
            "/propose <actif> — analyse immédiate et proposition de trade\n"
            "/long <actif> [commentaire] — signal manuel à l'achat\n"
            "/short <actif> [commentaire] — signal manuel à la vente\n"
            "/status — signaux ouverts\n"
            "/resume — résumé du jour\n"
            "Actifs : nasdaq (nq), sp500 (es), bitcoin (btc), ethereum (eth), gold (or)")

    def handle_command(self, text: str, now: datetime | None = None) -> str | None:
        """Exécute une commande texte (Telegram). Renvoie la réponse à envoyer, ou None si ignorée."""
        now = now or utcnow()
        parts = text.strip().split()
        if not parts or not parts[0].startswith("/"):
            return None
        cmd = parts[0].lower().split("@", 1)[0]
        args = parts[1:]
        if cmd in ("/help", "/start", "/aide"):
            return self.HELP
        if cmd == "/status":
            sigs = self.store.open_signals()
            if not sigs:
                return "Aucun signal ouvert."
            return "\n\n".join(format_signal(s, self.cfg.timezone) for s in sigs)
        if cmd in ("/resume", "/résumé", "/summary"):
            return self.summary(send=False)
        if cmd in ("/propose", "/long", "/short"):
            if not args:
                return f"Précisez l'actif : {cmd} bitcoin"
            asset_key = self.ASSET_ALIASES.get(args[0].lower())
            if asset_key is None:
                return f"Actif inconnu « {args[0]} ». " + self.HELP
            try:
                if cmd == "/propose":
                    self.propose(asset_key, now)   # envoie lui-même la notification
                    return None
                note = " ".join(args[1:])[:200]
                self.manual(asset_key, "long" if cmd == "/long" else "short", now, note=note)  # notifie lui-même
                return None
            except (ProviderError, RuntimeError, ValueError) as exc:
                return f"Impossible de traiter {cmd} {args[0]} : {exc}"
        return None

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
        informed: list[str] = list(st.get("telegram_informed", []))
        for upd in updates:
            last_id = max(last_id or 0, (upd.get("update_id") or 0) + 1)
            if upd["chat_id"] not in allowed:
                log.warning("message Telegram ignoré (chat %s non autorisé)", upd["chat_id"])
                if upd["chat_id"] not in informed:
                    informed.append(upd["chat_id"])
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
        self.store.save_state(st)
        return handled

    # ------------------------------------------------------------------ tick
    def tick(self, now: datetime | None = None) -> dict[str, Any]:
        """Un passage complet : commandes reçues, suivi des signaux ouverts, puis scan si l'intervalle est écoulé."""
        now = now or utcnow()
        try:
            self.process_commands(now)
        except Exception:  # noqa: BLE001
            log.exception("traitement des commandes Telegram")
        closed = self.track(now)
        st = self.store.state()
        last_scan = parse_iso(st["last_scan"]) if st.get("last_scan") else None
        new: list[Signal] = []
        if last_scan is None or now - last_scan >= timedelta(minutes=self.cfg.scan_interval_minutes - 1):
            new = self.scan(now)
        return {"closed": [s.id for s in closed], "new": [s.id for s in new]}
