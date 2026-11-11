"""Copie sur le démo MetaTrader 5 des signaux envoyés sur Telegram (demandé par Yanisse le 13/10/2026).

Le pont lit, toutes les 30 s, les signaux ouverts publiés par le bot sur le site (docs/live/<actif>.json) et les
signaux réels du laboratoire (data/lab_shadow.json : creux repris sur le Nasdaq). Les prix du bot sont ceux des
contrats à terme (Yahoo), un peu différents de ceux du CFD : on garde donc les **distances** du stop et de l'objectif,
appliquées au prix du CFD au moment de la copie. Taille : 5 % du solde démo au stop (choix de Yanisse le 15/10/2026, 1 % avant). Un signal publié il y a plus de
15 min n'est plus copié. Sortie : stop et objectif chez le courtier, ou fermeture à l'expiration du signal, ou quand
le bot le ferme. Compte démo seulement, magic 200001, règles d'arrêt de demo_rules.
"""
from __future__ import annotations

import json
import logging
import math
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import decideur as dc
from . import demo_rules
from . import gardien
from .mt5_local import LocalEngine, same_signal, server_offset

log = logging.getLogger("mt5_copy")

MAGIC = 200001
# 26/10/2026 (choix de Yanisse) : la copie démo répète le futur compte réel de 300 € → 2 % visé par trade ; si le lot
# minimum du courtier risque plus, il est pris quand même jusqu'à MIN_LOT_CAP du solde (simulation 2016-2025 : 25 trades
# ratés par an au lieu de 258, pire année 411 $ au lieu de 212 $). Plus de taille minimale par stratégie ni de plancher
# en $ par point (avant : 5 % de risque, nuit asiatique à 0,05 lot, 0,5-1 $ par point).
RISK_PCT = 0.02
MIN_LOT_CAP = 0.15
SOLO_MIN_LOT = {"XAUUSD+": 0.02}   # 28/10 (choix de Yanisse) : sur l'or, un trade du bot pris seul fait 0,02 lot au moins
#                      (0,01 reste pour les trades Telegram, 3 ordres à la fois) ; les autres marchés comme avant.
#                      Si 0,02 risque plus que MIN_LOT_CAP, le lot calculé est gardé.
MIN_LOT_MAX_RISK: dict[str, float] = {"nuit_asie": 0.30}   # 5/11 (choix de Yanisse) : la nuit asiatique est copiée
#                      au lot minimum même sur un petit solde (0,01 lot d'or ≈ 40 $ au stop), jusqu'à 30 % du solde
MIN_LOT: dict[str, float] = {}
MIN_POINT_VALUE: dict[str, float] = {}
FLOOR_MAX_RISK = 0.10
MAX_AGE = 15 * 60
CHASE_MAX = 0.5      # part de la distance du stop déjà parcourue depuis l'annonce au-delà de laquelle on ne copie plus
# Vantage refuse un commentaire d'ordre de 30 caractères ou plus (order_send renvoie None, « Invalid comment ») :
# « lab:cassure_williams:<horodatage> » (31) a fait rater la copie du 19/10. 26 passe.
COMMENT_MAX = 26
EVERY = 30
SYMBOLS = {"gold": "XAUUSD+", "nasdaq": "NAS100", "sp500": "SP500", "bitcoin": "BTCUSD", "ethereum": "ETHUSD",
           "oil": "CL-OIL", "euro": "EURUSD"}
# Lu directement dans le dépôt (pas le site) : disponible dès la sauvegarde du bot, sans attendre la mise en ligne
SITE = "https://raw.githubusercontent.com/Yxnisse7/Trading-Bot/main/docs/live/{asset}.json"
LAB = "https://raw.githubusercontent.com/Yxnisse7/Trading-Bot/main/data/lab_shadow.json"
LAB_TARGET_R = {"creux_repris_15m": 3.0}


CRYPTO = {"bitcoin", "ethereum"}


def _ts(s: str | None) -> int | None:
    if not s:
        return None
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def _get(url: str) -> Any:
    url += f"?t={int(time.time())}"              # contourne le cache (jusqu'à 5 min) du serveur de fichiers
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def read_signals(get: Callable[[str], Any] = _get, closed: set[str] | None = None) -> tuple[list[dict[str, Any]], set[str]]:
    """Signaux ouverts à copier, et les actifs (ou « lab ») lus sans erreur. `closed` reçoit les clés des trades
    des stratégies annoncés puis fermés sur GitHub."""
    out, ok = [], set()
    for asset in SYMBOLS:
        try:
            d = get(SITE.format(asset=asset))
        except Exception as exc:                     # site injoignable : on ne ferme rien sur cet actif
            log.info("signaux %s illisibles (%s)", asset, exc)
            continue
        ok.add(asset)
        for s in d.get("open_signals") or []:
            if s.get("source") == "shadow" or s.get("stop_loss") is None:
                continue
            out.append({"key": f"bot:{s['id']}", "asset": asset, "direction": s["direction"], "entry": s["entry"],
                        "stop": abs(s["entry"] - s["stop_loss"]),
                        "target": abs(s["take_profit"] - s["entry"]) if s.get("take_profit") else None,
                        "created": _ts(s.get("created_at")), "expires": _ts(s.get("expires_at"))})
    try:
        lab = get(LAB)
        ok.add("lab")
        for name, rec in lab.items():
            if rec.get("asset") not in SYMBOLS:         # seuls les signaux réels sont annoncés (notified_entry)
                continue
            for t in rec.get("trades") or []:
                if closed is not None and t.get("status") == "closed":
                    closed.add(f"lab:{rec.get('strategy')}:{t.get('entry_ts')}")
                if t.get("status") != "open" or not t.get("notified_entry") or t.get("pc_absent"):
                    continue                                 # pc_absent : pas de signal sur les prix MT5
                k = LAB_TARGET_R.get(rec.get("strategy"))
                # âge compté depuis l'annonce Telegram (≈ 10 min après la bougie d'entrée, plus le délai de
                # GitHub) : compté depuis la bougie, les signaux arrivaient déjà « trop anciens » (16/10/2026)
                out.append({"key": f"lab:{rec['strategy']}:{t['entry_ts']}", "asset": rec["asset"],
                            "direction": t["direction"], "entry": t["entry"], "stop": t["risk"],
                            "target": k * t["risk"] if k else None,
                            "created": _ts(t["notified_entry"]) if isinstance(t["notified_entry"], str) else t["entry_ts"],
                            "expires": t.get("close_at")})
    except Exception as exc:
        log.info("laboratoire illisible (%s)", exc)
    return out, ok


def lot_for(balance: float, dist: float, info, min_lot_risk: float | None = None) -> float:
    """Lot qui risque RISK_PCT du solde au stop, arrondi au pas du courtier ; 0 si même le minimum risque trop."""
    contract, step = float(info.trade_contract_size), float(info.volume_step)
    if dist <= 0 or contract <= 0 or step <= 0:
        return 0.0
    raw = balance * RISK_PCT / (dist * contract)
    lot = int(raw / step + 1e-9) * step
    if lot < info.volume_min:
        # le minimum du courtier risque plus que prévu : toléré jusqu'à MIN_LOT_CAP du solde (ou l'exception)
        cap = max(MIN_LOT_CAP, min_lot_risk or 0.0)
        return float(info.volume_min) if info.volume_min * dist * contract <= cap * balance else 0.0
    return round(min(lot, float(info.volume_max)), 2)


def solo_floor(lot: float, balance: float, dist: float, info, min_lot_risk: float | None = None,
               sym: str = "XAUUSD+") -> float:
    """Remonte le lot au minimum de SOLO_MIN_LOT pour ce symbole quand le risque au stop reste sous le plafond."""
    contract, step = float(info.trade_contract_size), float(info.volume_step)
    floor = SOLO_MIN_LOT.get(sym)
    if not floor or lot <= 0 or lot >= floor or contract <= 0 or step <= 0:
        return lot
    cap = max(MIN_LOT_CAP, min_lot_risk or 0.0)
    want = math.ceil(floor / step - 1e-9) * step
    if want > float(info.volume_max) or want * dist * contract > cap * balance:
        return lot
    return round(want, 2)


def floor_lot(lot: float, balance: float, dist: float, info, point_value: float | None) -> float:
    """Remonte le lot jusqu'à `point_value` $ par point, si le risque au stop reste sous FLOOR_MAX_RISK du solde."""
    contract, step = float(info.trade_contract_size), float(info.volume_step)
    if not point_value or contract <= 0 or step <= 0:
        return lot
    need = max(float(info.volume_min), math.ceil(point_value / contract / step - 1e-9) * step)
    if lot >= need:
        return lot
    return round(min(need, float(info.volume_max)), 2) if need * dist * contract <= FLOOR_MAX_RISK * balance else 0.0


class Copier:
    def __init__(self, mt5, root: Path, journal: Callable[..., None], clock: Callable[[], float],
                 get: Callable[[str], Any] = _get, local: bool = False, relay=None, bot=None, decider=None):
        self.mt5, self.root, self.journal, self.clock, self.get = mt5, root, journal, clock, get
        # 09/11/2026 : l'agent IA décide de chaque copie avant l'ordre (decideur.py) ; None = copie automatique
        self.decider = decider
        self.waiting: dict[str, dict[str, Any]] = {}
        self.known: tuple[set[str], set[str], set[str]] = (set(), set(), set())
        # annonces Telegram et avis de l'agent depuis le PC (pc_relay, 19/10/2026)
        self.relay = relay
        # stratégies recalculées sur le PC avec les prix MT5 (16/10/2026) ; GitHub reste la source de secours
        self.local = LocalEngine(mt5, SYMBOLS, clock) if local else None
        # bot classique du Nasdaq recalculé sur le PC (mt5_bot, 20/10/2026) ; GitHub reste la source de secours
        self.bot = bot
        self.state_file = root / "journal" / "copies.json"
        self.last = 0.0
        try:
            self.state: dict[str, Any] = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.state = {}
        for rec in self.state.values():               # pont relancé pendant que l'agent réfléchissait
            if rec.get("status") == "agent : en réflexion":
                rec["status"] = "agent : interrompu (pont relancé)"

    def _save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=1), encoding="utf-8")

    def _filling(self, sym: str) -> int:
        mode = getattr(self.mt5.symbol_info(sym), "filling_mode", 0)
        return self.mt5.ORDER_FILLING_FOK if mode & 1 else self.mt5.ORDER_FILLING_IOC if mode & 2 else self.mt5.ORDER_FILLING_RETURN

    def _positions(self) -> dict[int, Any]:
        return {p.ticket: p for p in (self.mt5.positions_get() or []) if p.magic == MAGIC}

    def _close(self, p, why: str) -> None:
        tick = self.mt5.symbol_info_tick(p.symbol)
        long = p.type == self.mt5.POSITION_TYPE_BUY
        res = self.mt5.order_send({
            "action": self.mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume, "position": p.ticket,
            "type": self.mt5.ORDER_TYPE_SELL if long else self.mt5.ORDER_TYPE_BUY,
            "price": tick.bid if long else tick.ask, "deviation": 50, "magic": MAGIC, "comment": f"copie {why}"[:COMMENT_MAX],
            "type_time": self.mt5.ORDER_TIME_GTC, "type_filling": self._filling(p.symbol)})
        self.journal("copie sortie", sens="achat" if long else "vente", prix=tick.bid if long else tick.ask,
                     lot=p.volume, note=f"{p.symbol} {why} (code {getattr(res, 'retcode', None)})")

    def step(self) -> str:
        now = self.clock()
        if self.waiting:
            self._decisions()                         # à chaque tour du pont, pas toutes les 30 s
        if now - self.last < EVERY:
            return ""
        self.last = now
        acc = self.mt5.account_info()
        if acc is None or acc.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
            return "copie : compte réel refusé"
        if self.relay is not None:
            self.relay.beat()
        self.github_closed: set[str] = set()
        signals, ok = read_signals(self.get, self.github_closed)
        local, local_keys = [], set()
        if self.local is not None:
            local, lok = self.local.signals()
            for s in local:
                k = LAB_TARGET_R.get(s["key"].split(":")[1])
                s["target"] = k * s["stop"] if k else None
            pc_trades = self.local.recent()           # stratégies sur prix MT5 : Simulation sur GitHub (30/10/2026)
            if self.bot is not None:
                found, bok = self.bot.signals()       # objectif du bot gardé tel quel
                local, lok = local + found, lok | bok
                pc_trades = self.bot.recent() + pc_trades
            if self.relay is not None:
                self.relay.pc_trades = pc_trades
            ok |= lok
            local_keys = {s["key"] for s in local}
            if self.relay is not None:
                self.relay.local_ok = {k.split(":", 1)[1] for k in lok}
        github_keys = {s["key"] for s in signals}
        self.known = (ok, local_keys, github_keys)
        live: dict[str, dict[str, Any]] = {}
        for s in local + signals:                    # le calcul local passe en premier
            live.setdefault(s["key"], s)
        pos = self._positions()
        # sorties : signal expiré, ou fermé par le bot (seulement si sa source a bien été lue)
        for key, rec in list(self.state.items()):
            p = pos.get(rec.get("ticket"))
            if rec.get("status") == "limite":
                if p is None:
                    self._limit(key, rec, now)
                    continue
                rec["status"] = "ouvert"              # ordre limite de l'agent touché
                if self.relay is not None:
                    self.relay.reply_to(key, "⏳→✅ Ordre limite de l'agent exécuté sur MT5.")
            if p is None:
                if rec.get("ticket") and rec.get("status") == "ouvert":
                    rec["status"] = "fermé"
                continue
            if rec.get("expires") and now >= rec["expires"]:
                self._close(p, "expiration")
            elif self._ended(key, rec):
                self._close(p, "fermé par la règle" if rec.get("source") == "local" else "fermé par le bot")
        # entrées
        why = demo_rules.check(self.mt5, MAGIC)
        for key, s in live.items():
            if key in self.state:
                continue
            twin = next((k for k, r in self.state.items()
                         if r.get("source", "github") != s.get("source", "github")
                         and same_signal(key, s["direction"], k, r.get("direction"))), None)
            self.state[key] = {"asset": s["asset"], "status": "vu", "expires": s["expires"], "symbol": SYMBOLS.get(s["asset"], ""),
                               "direction": s["direction"], "source": s.get("source", "github"), "seen": int(now)}
            if twin:
                self.state[key]["status"] = f"même signal que {twin}"
                continue
            pc_strat = key.split(":")[1] if key.startswith("lab:") else "bot" if s["asset"] == "nasdaq" else ""
            if s.get("source", "github") == "github" and f"local:{pc_strat}" in ok:
                # 20/10 : le PC calcule cette stratégie sur les prix MT5 et n'y voit pas ce signal : on ne le copie pas
                self.state[key]["status"] = "pas de signal sur les prix MT5"
                continue
            if why:
                self.state[key]["status"] = f"refusé : {why}"
                self.journal("copie refusée", note=f"{key} règle d'arrêt : {why}")
                if self.relay is not None and s.get("source") == "local" and s["created"] \
                        and now - s["created"] <= MAX_AGE:
                    self.relay.entry(key, s, self.state[key])     # pas copié, mais c'est un signal réel
                continue
            if not s["created"] or now - s["created"] > MAX_AGE:
                self.state[key]["status"] = "trop ancien"
                continue
            if self.decider is not None and self.decider.available():
                self._ask(key, s)
                continue
            self.state[key].update(self._open(s, acc.balance))
            if self.state[key]["status"] == "pas de prix":
                del self.state[key]                 # pas encore de cotation : on réessaie au passage suivant
            elif self.relay is not None and s.get("source") == "local":
                self.relay.entry(key, s, self.state[key])
        self._save()
        if self.relay is not None and self.mt5.positions_get() is not None:   # terminal muet : on ne conclut rien
            self.relay.step(self._positions(), local_keys, ok)
        return f"copie : {sum(1 for r in self.state.values() if r.get('status') == 'ouvert')} position(s)"

    # ------------------------------------------------------------------ décision de l'agent IA (09/11/2026)
    def _ended(self, key: str, rec: dict[str, Any]) -> bool:
        """Signal fermé par sa source (seulement si cette source a bien été lue au dernier passage)."""
        ok, local_keys, github_keys = self.known
        if rec.get("source") == "local":
            # 10/11/2026 : Donchian 1 h Bitcoin des 29/10 et 05/11 restés ouverts sur MT5 alors que GitHub les avait
            # sortis un week-end (prix Vantage du week-end différents de ceux de GitHub, qui cote 24 h/24) :
            # pour les cryptos, une sortie vue sur GitHub ferme aussi la copie
            if rec.get("asset") in CRYPTO and key in getattr(self, "github_closed", set()):
                return True
            source, known = f"local:{key.split(':')[1]}", local_keys
        else:
            # 16/10 : comparé à tous les signaux moins ceux du PC, un trade GitHub que le PC voyait aussi
            # était fermé au redémarrage du pont ; seuls comptent les signaux de GitHub
            source, known = ("lab" if key.startswith("lab:") else rec["asset"]), github_keys
        return source in ok and key not in known

    @staticmethod
    def _strategy(key: str) -> str:
        return key.split(":")[1] if key.startswith("lab:") else "bot"

    def _ask(self, key: str, s: dict[str, Any]) -> None:
        """Envoie le signal à l'agent ; la décision est lue par _decisions aux tours suivants."""
        from .pc_relay import ASSETS, EXITS
        sym = SYMBOLS[s["asset"]]
        long = s["direction"] == "long"
        sg = 1 if long else -1
        tick = self.mt5.symbol_info_tick(sym) if self.mt5.symbol_select(sym, True) else None
        px = (tick.ask if long else tick.bid) if tick is not None else 0.0
        if px <= 0:
            del self.state[key]                     # pas encore de cotation : on réessaie au passage suivant
            return
        late = self._already_gone(s, sym, px, sg)
        if late:
            self.state[key]["status"] = late
            return
        strat = self._strategy(key)
        get = getattr(self.relay, "_candles", None)
        candles = (lambda tf, n: get(sym, tf, n, None) or []) if get else (lambda tf, n: [])  # noqa: E731
        now = self.clock()
        iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
        data = {"id": key.replace(":", "-"), "strategie": strat, "asset": s["asset"],
                "asset_label": ASSETS.get(s["asset"], s["asset"]), "direction": s["direction"],
                "entry": px, "stop_loss": px - sg * s["stop"],
                "take_profit": px + sg * s["target"] if s.get("target") else None,
                "sortie": EXITS.get(strat, "selon la règle de la stratégie"),
                "created_at": iso(s.get("created") or now), "maintenant": iso(now),
                "bid": tick.bid, "ask": tick.ask, "attente_max_min": dc.WAIT_MAX // 60,
                "telegram_message_ids": {}, "ticket_mt5": None,
                "candles_5m": candles("TIMEFRAME_M5", 288), "candles_1h": candles("TIMEFRAME_H1", 48),
                "candles_1d": candles("TIMEFRAME_D1", 20)}
        if not self.decider.ask(key, data):
            self.state[key]["status"] = "agent : pas de réponse"
            self.state[key]["agent"] = dc.normalize({"raison": "L'agent n'a pas pu être lancé."})
            self._announce(key, s, self.state[key])
            return
        self.state[key]["status"] = "agent : en réflexion"
        self.waiting[key] = s

    def _decisions(self) -> None:
        acc = self.mt5.account_info()
        if acc is None or acc.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
            return
        now = self.clock()
        for key in list(self.waiting):
            dec = self.decider.poll(key)
            if dec is None:
                continue
            s = self.waiting.pop(key)
            rec = self.state.get(key)
            if rec is None or rec.get("status") != "agent : en réflexion":
                continue
            rec["agent"] = dict(dec, notes=[])
            shown = s
            self.journal("décision de l'agent", sens="achat" if s["direction"] == "long" else "vente",
                         note=f"{key} {dec['action']} ({dec['confiance']}/5) : {dec['raison']}"[:300])
            if (s.get("expires") and now >= s["expires"]) or self._ended(key, rec):
                rec["status"] = "agent : signal fini avant la décision"
            elif dec["action"] not in ("prendre", "attendre"):
                rec["status"] = "agent : refusé" if dec["action"] == "refuser" else "agent : pas de réponse"
            else:
                sym = SYMBOLS[s["asset"]]
                long = s["direction"] == "long"
                info, tick = self.mt5.symbol_info(sym), self.mt5.symbol_info_tick(sym)
                px = (tick.ask if long else tick.bid) if tick is not None else 0.0
                if info is None or px <= 0:
                    rec["status"] = "agent : pas de prix après la décision"
                else:
                    gap = (info.trade_stops_level + 5) * info.point + abs(tick.ask - tick.bid)
                    p = dc.plan(dec, long, px, s["stop"], s.get("target"), gap)
                    rec["agent"]["notes"] = p["notes"]
                    if p["action"] == "refuser":
                        rec["status"] = "agent : refusé"
                    else:
                        shown = dict(s, stop=p["stop"], target=p["target"])
                        rec.update(self._open(shown, acc.balance, limit=p["entry"]))
                        if rec["status"] == "pas de prix":
                            rec["status"] = "agent : pas de prix après la décision"
                        shown["entry"] = rec.get("price") or p["entry"] or px
            self._announce(key, shown, rec)
        self._save()

    def _announce(self, key: str, s: dict[str, Any], rec: dict[str, Any]) -> None:
        if self.relay is None:
            return
        if s.get("source") == "local":
            self.relay.entry(key, s, rec)
        else:
            self.relay.note(key, s, rec)            # signal du site : déjà annoncé par GitHub

    def _limit(self, key: str, rec: dict[str, Any], now: float) -> None:
        """Ordre limite « attendre » pas encore touché : annulé à l'heure prévue ou si le signal est fini."""
        t = rec.get("ticket")
        if not any(o.ticket == t for o in (self.mt5.orders_get() or [])):
            deals = (self.mt5.history_deals_get(position=t) or []) if t else []
            rec["status"] = "fermé" if deals else "limite annulée"
            return
        why = ("pas touché à temps" if now >= float(rec.get("limit_until") or 0)
               else "fin du signal" if rec.get("expires") and now >= rec["expires"]
               else "signal fermé par la règle" if self._ended(key, rec) else "")
        if not why:
            return
        res = self.mt5.order_send({"action": self.mt5.TRADE_ACTION_REMOVE, "order": t})
        if getattr(res, "retcode", None) != self.mt5.TRADE_RETCODE_DONE:
            return                                  # on réessaie au passage suivant
        rec["status"] = f"limite annulée ({why})"
        self.journal("copie limite annulée", note=f"{key} {why}")
        if self.relay is not None:
            self.relay.cancelled(key, f"Ordre limite de l'agent annulé : {why}. Pas de trade.")

    def _already_gone(self, s: dict[str, Any], sym: str, px: float, sg: int) -> str:
        """Signal de GitHub copié en retard : si le prix du CFD a déjà fait plus de CHASE_MAX fois la distance du
        stop dans le sens du trade depuis l'annonce, on passe notre tour, comme la « zone d'entrée » de Telegram
        (16/10 : vente Nasdaq copiée 8 min après, 195 points plus bas, stop touché alors que le signal a gagné)."""
        created = s.get("created")
        now = self.clock()
        if s.get("source") == "local" or not created or now - created < 60:
            return ""
        try:
            off = server_offset(self.mt5, sym, now)
            rates = self.mt5.copy_rates_from(sym, self.mt5.TIMEFRAME_M1, int(created) + (off or 0), 1)
            ref = float(rates[-1]["close"]) if rates is not None and len(rates) else 0.0
        except Exception:                          # pas d'historique : on copie comme avant
            return ""
        moved = sg * (px - ref) if ref > 0 else 0.0
        if moved > CHASE_MAX * s["stop"]:
            return f"prix déjà parti ({moved:.2f} depuis l'annonce)"
        return ""

    def _open(self, s: dict[str, Any], balance: float, limit: float | None = None) -> dict[str, Any]:
        sym = SYMBOLS[s["asset"]]
        if not self.mt5.symbol_select(sym, True):
            return {"status": f"symbole {sym} indisponible"}
        long = s["direction"] == "long"
        info, px = self.mt5.symbol_info(sym), 0.0
        for attempt in range(5):           # juste après symbol_select, le premier prix vaut souvent 0
            tick = self.mt5.symbol_info_tick(sym)
            px = (tick.ask if long else tick.bid) if tick is not None else 0.0
            if px > 0:
                break
            time.sleep(0.5)
        if info is None or px <= 0:
            return {"status": "pas de prix"}
        sg = 1 if long else -1
        # le SL se mesure depuis le prix de sortie (l'autre côté de l'écart) : trop court, il est élargi au minimum
        # du courtier plutôt que refusé (code 10016), et la taille suit la distance élargie
        spread = abs(tick.ask - tick.bid) if tick is not None else 0.0
        s = dict(s, stop=max(s["stop"], (info.trade_stops_level + 5) * info.point + spread))
        if limit:                                   # ordre limite de l'agent (« attendre ») : niveaux autour du prix visé
            px = round(limit, info.digits)
        sl = round(px - sg * s["stop"], info.digits)
        tp = round(px + sg * s["target"], info.digits) if s.get("target") else 0.0
        late = "" if limit else self._already_gone(s, sym, px, sg)
        if late:
            return {"status": late}
        strat = s["key"].split(":")[1] if s["key"].startswith("lab:") else None
        lot = lot_for(balance, s["stop"], info, MIN_LOT_MAX_RISK.get(strat))
        lot = solo_floor(lot, balance, s["stop"], info, None, sym)   # l'exception ne vaut que pour le lot minimum
        lot = floor_lot(lot, balance, s["stop"], info, MIN_POINT_VALUE.get(sym))
        if strat in MIN_LOT:
            lot = round(min(max(lot, MIN_LOT[strat]), float(info.volume_max)), 2)
        if lot <= 0:
            return {"status": "taille minimale trop risquée"}
        blocked = gardien.check(self.mt5, sym, tick, info, s["stop"], lot, balance, self.clock())
        if blocked:                                  # 11/11/2026 : raison concrète et vérifiable, voir gardien.py
            self.journal("copie bloquée par le gardien", sens="achat" if long else "vente", prix=px, lot=lot,
                         note=f"{sym} {s['key']} : {blocked}")
            return {"status": f"gardien : {blocked}"}
        warn = gardien.news(gardien.events(self.root), s["asset"], self.clock())
        req = {"action": self.mt5.TRADE_ACTION_DEAL, "symbol": sym, "volume": lot,
               "type": self.mt5.ORDER_TYPE_BUY if long else self.mt5.ORDER_TYPE_SELL, "price": px, "sl": sl, "tp": tp,
               "deviation": 50, "magic": MAGIC, "comment": s["key"][:COMMENT_MAX], "type_time": self.mt5.ORDER_TIME_GTC,
               "type_filling": self._filling(sym)}
        if limit:
            req.update(action=self.mt5.TRADE_ACTION_PENDING, type_filling=self.mt5.ORDER_FILLING_RETURN,
                       type=self.mt5.ORDER_TYPE_BUY_LIMIT if long else self.mt5.ORDER_TYPE_SELL_LIMIT)
            req.pop("deviation")
        res = self.mt5.order_send(req)
        code = getattr(res, "retcode", None)
        ok = code == self.mt5.TRADE_RETCODE_DONE
        self.journal(("copie limite" if limit else "copie entrée") if ok else "copie rejetée",
                     sens="achat" if long else "vente",
                     prix=getattr(res, "price", px) or px, stop=sl, objectif=tp or "", lot=lot,
                     note=f"{sym} {s['key']} (code {code})")
        if not ok:
            return {"status": f"rejeté (code {code})"}
        ticket = getattr(res, "order", None) or getattr(res, "deal", None)
        if limit:
            until = self.clock() + dc.WAIT_MAX
            return {"status": "limite", "ticket": ticket, "symbol": sym, "lot": lot, "price": px,
                    "limit_until": min(until, s["expires"]) if s.get("expires") else until}
        return {"status": "ouvert", "ticket": ticket, "symbol": sym, "lot": lot,
                "price": float(getattr(res, "price", px) or px), **({"alerte": warn} if warn else {})}
