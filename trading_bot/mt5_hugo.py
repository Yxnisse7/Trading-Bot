"""Chasse « méthode Hugo » de l'agent IA sur le Nasdaq démo (choix de Yanisse le 20/10/2026, après l'essai 40).

Même mécanique que la chasse de l'agent (mt5_hunt.py) avec un numéro magique à part, mais le jugement suit la
méthode BPR d'un trader TikTok (trading_bot/hugo.py) :
- réveils à heures fixes (9h, 10h, 14h30, 15h45, 16h30 Paris, en semaine), et veille toutes les 20 min de 9h à 17h
  (demandé par Yanisse le 23/10/2026), pas après les annonces ;
- commande Telegram /hugo, quand le PC est allumé : analyse tout de suite, réponse même sans trade (avec la zone à
  surveiller) ;
- règles de journée de la vidéo : arrêt après un gain ou deux pertes ;
- un compte Topstep 50K virtuel suit ses trades (300 $ de risque par trade, comme dans la vidéo), affiché à chaque
  sortie : il dit si la méthode passerait l'examen.

Les messages Telegram sont lus sans être acquittés (getUpdates sans offset) : le bot de GitHub continue de recevoir
les autres commandes, et ignore /hugo.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from . import messages as msg
from .mt5_hunt import PARIS, Hunter
from .notify import chat_key, telegram_chat_ids
from .topstep import RULES

log = logging.getLogger("mt5_hugo")

POLL = 10                    # s entre deux lectures des messages Telegram
FRESH = 300                  # une commande plus vieille que 5 min est ignorée
RISK_USD = 300.0             # risque par trade du compte Topstep virtuel (vidéo)


def _updates(token: str) -> list[dict[str, Any]]:
    import requests
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates",
                         params={"timeout": 0, "allowed_updates": '["message"]'}, timeout=10)
        r.raise_for_status()
        return r.json().get("result", [])
    except (requests.RequestException, ValueError) as exc:
        log.warning("hugo : lecture Telegram impossible (%s)", exc)
        return []


class HugoHunter(Hunter):
    MAGIC = 777003
    NAME = "hugo"
    ASSETS = {"nasdaq": ("Nasdaq 100", (("09:00", "matin"), ("10:00", "matin"), ("14:30", "stats américaines"),
                                        ("15:45", "après l'ouverture de Wall Street"), ("16:30", "après-midi")), 2.0)}
    NEWS = False
    WATCH = {"nasdaq": (("09:00", "17:00"),)}  # + veille toutes les `every_minutes` (23/10)
    TAG = "Méthode Hugo (agent IA)"
    COMMENT = "hugo IA"
    FRAMES = (("candles_5m", "TIMEFRAME_M5", 288), ("candles_15m", "TIMEFRAME_M15", 96),
              ("candles_1h", "TIMEFRAME_H1", 72), ("candles_4h", "TIMEFRAME_H4", 60), ("candles_1d", "TIMEFRAME_D1", 30))
    DEFAULTS = {"command": r"E:\TradingBot\venv\Scripts\python.exe -m trading_bot.hugo", "dir": r"E:\TradingBot\bot",
                "agent_dir": r"E:\TradingBot\agent\agent"}

    def __init__(self, mt5, root: Path, clock: Callable[[], float], relay=None, cfg: dict[str, Any] | None = None,
                 spawn=None, updates: Callable[[str], list[dict[str, Any]]] = _updates):
        kw = {"spawn": spawn} if spawn is not None else {}
        super().__init__(mt5, root, clock, relay=relay, cfg=cfg, **kw)
        self.updates = updates
        self.last_poll = 0.0
        self.state.setdefault("days", {})
        self.state.setdefault("topstep", self._new_account(1))

    # ------------------------------------------------------------------ règles de la vidéo
    def ready(self) -> bool:
        return (Path(self.cfg["dir"]) / "trading_bot" / "hugo.py").exists() and \
            (Path(self.cfg["agent_dir"]) / "ia.py").exists()

    def _today(self, now: float) -> str:
        return datetime.fromtimestamp(now, PARIS).date().isoformat()

    def may_trade(self, asset: str, now: float) -> bool:
        d = self.state["days"].get(self._today(now), {})
        return d.get("wins", 0) < 1 and d.get("losses", 0) < 2

    def _day_text(self, now: float) -> str:
        d = self.state["days"].get(self._today(now), {})
        w, lo = d.get("wins", 0), d.get("losses", 0)
        if not w and not lo:
            return "aucun trade de la méthode aujourd'hui"
        stop = " : journée terminée (1 gain ou 2 pertes)" if not self.may_trade("nasdaq", now) else ""
        return f"{w} gain(s), {lo} perte(s) aujourd'hui{stop}"

    def extra(self, asset: str, now: float) -> dict[str, Any]:
        return {"methode": "hugo", "journee": self._day_text(now)}

    def closed(self, asset: str, t: dict[str, Any], profit: float, r: float) -> list[str]:
        now = self.clock()
        day = self.state["days"].setdefault(self._today(now), {"wins": 0, "losses": 0})
        day["wins" if profit >= 0 else "losses"] += 1
        self.state["days"] = dict(sorted(self.state["days"].items())[-30:])
        acc = self._topstep(r * RISK_USD, self._today(now))
        lines = [f"Journée méthode Hugo : {self._day_text(now)}."]
        lines.append(f"Topstep 50K virtuel n°{acc['n']} : {msg.num(acc['balance'], 0)} $ · perte max "
                     f"{msg.num(acc['mll'], 0)} $ · objectif {msg.num(RULES['start_balance'] + RULES['profit_target'], 0)} $")
        if acc.get("done"):
            lines.append(acc["done"])
        return lines

    # ------------------------------------------------------------------ compte Topstep virtuel
    @staticmethod
    def _new_account(n: int) -> dict[str, Any]:
        start = RULES["start_balance"]
        return {"n": n, "balance": start, "peak": start, "mll": start - RULES["max_loss"], "day": None, "days": {}}

    def _topstep(self, pnl: float, day: str) -> dict[str, Any]:
        a = self.state["topstep"]
        start = RULES["start_balance"]
        if a["day"] is not None and a["day"] != day:          # perte max suiveuse en fin de journée
            a["peak"] = max(a["peak"], a["balance"])
            a["mll"] = min(start, max(a["mll"], a["peak"] - RULES["max_loss"]))
        a["day"] = day
        a["balance"] = round(a["balance"] + pnl, 2)
        a["days"][day] = round(a["days"].get(day, 0.0) + pnl, 2)
        profit = a["balance"] - start
        best = max(a["days"].values())
        out = dict(a)
        if a["balance"] <= a["mll"] or a["days"][day] <= -RULES["daily_loss"]:
            out["done"] = f"❌ Compte virtuel n°{a['n']} sauté. Un compte neuf repart au prochain trade."
        elif profit >= max(RULES["profit_target"], best / RULES["consistency"]):
            out["done"] = f"🏆 Compte virtuel n°{a['n']} : examen Topstep réussi. Un compte neuf repart au prochain trade."
        if out.get("done"):
            self.state.setdefault("topstep_history", []).append({**a, "result": "réussi" if "réussi" in out["done"] else "sauté"})
            self.state["topstep"] = self._new_account(a["n"] + 1)
        return out

    # ------------------------------------------------------------------ /hugo sur Telegram
    def step(self) -> str:
        said = self.poll()
        return super().step() or said

    def poll(self) -> str:
        now = self.clock()
        if self.relay is None or not self.relay.enabled() or now - self.last_poll < POLL:
            return ""
        self.last_poll = now
        allowed = {chat_key(c) for c in telegram_chat_ids()}
        seen = int(self.state.get("tg_seen") or 0)
        asked = False
        for u in self.updates(self.relay.token):
            uid = int(u.get("update_id") or 0)
            m = u.get("message") or {}
            if uid <= seen:
                continue
            seen = max(seen, uid)
            text = str(m.get("text") or "").strip().lower()
            if (text.split("@", 1)[0].split() or [""])[0] != "/hugo":
                continue
            if chat_key(str((m.get("chat") or {}).get("id"))) not in allowed or now - float(m.get("date") or 0) > FRESH:
                continue
            asked = True
        self.state["tg_seen"] = seen
        self._save()
        return self.ask(now) if asked else ""

    def ask(self, now: float) -> str:
        """Analyse demandée avec /hugo : réponse sur Telegram dans tous les cas."""
        if self.proc is not None:
            self.relay._post("🔎 Méthode Hugo : une analyse est déjà en cours, la réponse arrive.")
            return "hugo : déjà en cours"
        t = self.state["trades"].get("nasdaq")
        if t:
            self.relay._post(f"🔎 Méthode Hugo : un trade est déjà ouvert ({'achat' if t['buy'] else 'vente'} à "
                             f"{msg.num(t['entry'], 2)}, SL {msg.num(t['stop'], 2)}, TP {msg.num(t['target'], 2)}).")
            return "hugo : trade déjà ouvert"
        if not self.ready():
            self.relay._post("🔎 Méthode Hugo : l'agent n'est pas installé sur le PC.")
            return "hugo : agent absent"
        acc = self.mt5.account_info()
        if acc is None or acc.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
            self.relay._post("🔎 Méthode Hugo : MT5 n'est pas sur le compte démo, rien n'est lancé.")
            return "hugo : pas de démo"
        said = self._wake("nasdaq", now, "demande /hugo", self.events(), acc)
        if self.proc is None:
            self.relay._post(f"🔎 Méthode Hugo : impossible d'analyser maintenant ({said.split(': ', 1)[-1]}).")
            return said
        self.proc[4]["demande"] = True
        self.relay._post("🔎 Méthode Hugo : je regarde le Nasdaq, réponse dans une minute environ.")
        return said

    def _decide(self, a: dict[str, Any], data: dict[str, Any]) -> None:
        trade = a.get("action") in ("achat", "vente")
        allowed = self.may_trade(data["asset"], self.clock())
        if data.get("demande") and self.relay is not None and self.relay.enabled():
            lines = [f"<b>🔎 Méthode Hugo · {msg.esc(data['asset_label'])}</b> · analyse demandée",
                     f"Réponse : <b>{msg.esc(str(a.get('action', 'rien')))}</b> · confiance {int(a.get('confiance') or 0)}/5",
                     "", msg.esc(str(a.get("raison", "")))]
            if a.get("a_surveiller"):
                lines += ["", f"À surveiller : {msg.esc(str(a['a_surveiller']))}"]
            if trade and not allowed:
                lines += ["", "Pas d'ordre : la journée de la méthode est terminée (1 gain ou 2 pertes)."]
            self.relay._post("\n".join(lines))
        if trade and allowed:
            super()._decide(a, data)
        else:
            from . import claude_desk as desk
            desk._journal({"action": f"hugo {data['asset']} : {a.get('action')}", "prix": data.get("bid"),
                           "stop": a.get("stop"), "objectif": a.get("objectif"),
                           "resultat": "" if allowed else "journée terminée",
                           "raison": f"[{data['moment']}] {a.get('raison', '')} {a.get('a_surveiller', '')}".strip()})
