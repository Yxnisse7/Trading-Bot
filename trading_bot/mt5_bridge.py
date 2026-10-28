"""Pont MetaTrader 5 (PC Windows) : les règles de l'essai 18 en direct sur l'or, un seul trade à la fois.

Modes (fichier config.json à côté du dossier du bot) :
- « observe » : le pont lit le marché et note dans le journal les trades qu'il aurait pris, sans aucun ordre ;
- « demo » : il passe les ordres, **seulement sur un compte démo** ; un compte réel est toujours refusé.
Le terminal MetaTrader 5 doit être ouvert et connecté. Aucun identifiant n'est lu ni écrit ici.
Lancement : `python -m trading_bot.mt5_bridge E:\\TradingBot` (ou lancer.bat).
"""
from __future__ import annotations

import csv
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import demo_rules
from . import essai18 as e18
from .models import Candle

log = logging.getLogger("mt5_bridge")

DEFAULTS: dict[str, Any] = {
    "mode": "observe",            # observe | demo
    "symbol": "XAUUSD",
    "entry": "R1-R4",             # R1, R2, R3, R4 ou R1-R4 (essai 18)
    "exit": "X1",                 # X1 : objectif à 1 fois le stop
    "lot": 0.01,
    "virtual_capital": 100.0,     # le pont trade comme si le compte ne valait que ça
    "daily_loss_limit": 10.0,     # en $ : plus aucun trade ce jour-là une fois atteint
    "magic": 180018,
    "bars": 3000,
    "poll_seconds": 2,
    "record_ticks": True,
    "copy_bot": True,             # copie aussi les signaux Telegram du bot sur le démo (mt5_copy.py)         # enregistre chaque prix (achat/vente) du courtier dans ticks/AAAA-MM-JJ.csv
    "agent": {"enabled": False, "model": "", "library": ""},
    # avis de l'agent IA après chaque entrée annoncée par le PC (pc_relay.py), lancé en arrière-plan ;
    # rien ne se passe tant que le dossier de l'agent n'existe pas
    "avis": {"command": r"E:\TradingBot\venv\Scripts\python.exe E:\TradingBot\agent\agent\avis_direct.py",
             "dir": r"E:\TradingBot\agent", "timeout": 90},
}


def load_config(root: Path) -> dict[str, Any]:
    f = root / "config.json"
    cfg = json.loads(json.dumps(DEFAULTS))
    if f.exists():
        user = json.loads(f.read_text(encoding="utf-8-sig"))     # Bloc-notes ajoute parfois une marque BOM
        cfg.update({k: v for k, v in user.items() if k not in ("agent", "avis")})
        cfg["agent"].update(user.get("agent", {}))
        cfg["avis"].update(user.get("avis", {}))
    else:
        f.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return cfg


class Bridge:
    def __init__(self, mt5, cfg: dict[str, Any], root: Path, agent=None, clock=time.time):
        self.mt5, self.cfg, self.root, self.agent, self.clock = mt5, cfg, root, agent, clock
        self.sym, self.magic = cfg["symbol"], int(cfg["magic"])
        self.last_bar: int | None = None
        self.limit_day: str | None = None
        self.stop_rule: str | None = None
        self.copier = None
        self.hunter = None
        self.hugo = None
        self.asker = None
        self.check = None
        self.tgcopy = None
        self.relay = None
        self._closed: tuple[float, list[list]] | None = None
        if cfg.get("copy_bot") and cfg["mode"] == "demo":
            from .mt5_copy import Copier
            from .pc_relay import Relay
            bot = None
            if cfg.get("local_bot", True):
                from .mt5_bot import LocalBot
                from .mt5_copy import SYMBOLS
                bot = LocalBot(mt5, SYMBOLS, clock, root)
            relay = Relay(mt5, root, clock, agent=cfg["avis"])
            self.relay = relay
            if relay.enabled():                  # menu des commandes quand on tape « / » dans Telegram
                from .notify import telegram_set_menu
                telegram_set_menu()
            self.copier = Copier(mt5, root, self.journal, clock, local=bool(cfg.get("local_strategies", True)),
                                 relay=relay, bot=bot)
            if cfg.get("hunt", True):            # l'agent IA cherche des trades sur l'or à heures fixes (mt5_hunt.py)
                from .mt5_hunt import Hunter
                self.hunter = Hunter(mt5, root, clock, relay=relay, cfg=cfg.get("chasse"))
            if cfg.get("hugo", True):            # méthode Hugo sur le Nasdaq + commande /hugo (mt5_hugo.py)
                from .mt5_hugo import HugoHunter
                self.hugo = HugoHunter(mt5, root, clock, relay=relay, cfg=cfg.get("hugo_cfg"))
            if cfg.get("ask", True):             # questions à l'agent depuis Telegram : /avis (mt5_ask.py)
                from .mt5_ask import Asker
                self.asker = Asker(mt5, root, clock, relay=relay, cfg=cfg.get("ask_cfg"))
            if cfg.get("controle", True):        # contrôle du soir : signaux annoncés contre trades pris (mt5_check.py)
                from .mt5_check import DailyCheck
                self.check = DailyCheck(self.copier, relay, root, clock)
            if (cfg.get("tg_copy") or {}).get("channels"):   # copie des canaux Telegram de signaleurs (mt5_tgcopy.py)
                from .mt5_tgcopy import TgCopier
                self.tgcopy = TgCopier(mt5, root, clock, relay=relay, cfg=cfg["tg_copy"])
        self.tick_from: int | None = None
        if cfg["exit"] != "X1":
            raise ValueError("seule la sortie X1 est branchée en direct pour l'instant")

    # ------------------------------------------------------------ lecture du terminal
    def offset(self) -> int | None:
        """Décalage de l'heure du serveur (les bougies MT5 sont datées à l'heure du serveur), arrondi à la
        demi-heure ; None sans cotation récente (marché fermé, terminal pas encore à jour)."""
        tick = self.mt5.symbol_info_tick(self.sym)
        if tick is None or not tick.time:
            return None
        off = round((tick.time - self.clock()) / 1800) * 1800
        return off if abs(tick.time - off - self.clock()) <= 180 else None

    def candles(self, offset: int) -> list[Candle]:
        rates = self.mt5.copy_rates_from_pos(self.sym, self.mt5.TIMEFRAME_M1, 0, int(self.cfg["bars"]) + 1)
        if rates is None or len(rates) < 2:
            return []
        return [Candle(int(r["time"]) - offset, float(r["open"]), float(r["high"]), float(r["low"]),
                       float(r["close"]), float(r["tick_volume"])) for r in rates[:-1]]     # la dernière est en cours

    def is_demo(self) -> bool:
        a = self.mt5.account_info()
        return a is not None and a.trade_mode == self.mt5.ACCOUNT_TRADE_MODE_DEMO

    def positions(self) -> list:
        return [p for p in (self.mt5.positions_get(symbol=self.sym) or []) if p.magic == self.magic]

    def today_pnl(self, offset: int) -> float:
        """Résultat des trades du pont fermés aujourd'hui (UTC), frais compris."""
        now = self.clock()
        day0 = int(now // 86400 * 86400)
        lo = datetime.fromtimestamp(day0 + offset - 86400, timezone.utc)
        hi = datetime.fromtimestamp(now + offset + 86400, timezone.utc)
        deals = self.mt5.history_deals_get(lo, hi) or []
        return sum(d.profit + d.commission + d.swap for d in deals
                   if d.magic == self.magic and d.time - offset >= day0)

    # ------------------------------------------------------------ état en direct pour l'interface locale
    ORIGINS = {200001: "Copie du bot", 777001: "Claude", 777002: "Agent IA", 777003: "Méthode Hugo", 300001: "Copie Telegram",
               0: "Manuel"}

    CLOSED_COLS = ["closed", "opened", "symbol", "side", "volume", "open", "close", "pnl", "origin", "why"]
    WHY = {4: "SL", 5: "TP", 6: "marge", 3: "pont", 0: "main", 1: "main", 2: "main"}

    def closed_positions(self, off: int, days: int = 30) -> list[list]:
        """Positions fermées des `days` derniers jours, une ligne par position (colonnes CLOSED_COLS, plus récente
        d'abord) : heures en UTC, résultat net frais compris, sens de la position, cause de la sortie. Relu au plus
        toutes les 30 s : la page MT5 du site en tire sa courbe et ses tableaux."""
        now = self.clock()
        if self._closed is not None and now - self._closed[0] < 30:
            return self._closed[1]
        lo = datetime.fromtimestamp(now + off - days * 86400, timezone.utc)
        hi = datetime.fromtimestamp(now + off + 86400, timezone.utc)
        pos: dict[int, dict[str, Any]] = {}
        for d in self.mt5.history_deals_get(lo, hi) or []:
            if not d.symbol:
                continue
            p = pos.setdefault(d.position_id, {"pnl": 0.0, "magic": d.magic, "symbol": d.symbol})
            p["pnl"] += d.profit + d.commission + d.swap
            if d.entry == 0:                                  # entrée
                p.update(side="vente" if d.type == 1 else "achat", opened=int(d.time) - off, open=d.price)
            elif d.entry in (1, 3):                           # sortie (ou sortie par une position inverse)
                p.update(closed=int(d.time) - off, close=d.price, volume=d.volume, why=self.WHY.get(getattr(d, "reason", -1), ""),
                         exit_side="vente" if d.type == 1 else "achat")
        rows = []
        for p in pos.values():
            if "closed" not in p:
                continue
            side = p.get("side") or ("achat" if p["exit_side"] == "vente" else "vente")
            origin = "Pont (or)" if p["magic"] == self.magic else self.ORIGINS.get(p["magic"], f"Autre ({p['magic']})")
            rows.append([p["closed"], p.get("opened"), p["symbol"], side, p["volume"], round(p.get("open") or 0, 5),
                         round(p["close"], 5), round(p["pnl"], 2), origin, p["why"]])
        rows.sort(key=lambda r: -r[0])
        self._closed = (now, rows)
        return rows

    def snapshot(self) -> dict[str, Any] | None:
        """Compte, positions ouvertes et trades fermés des dernières 36 h (heures en UTC), pour l'onglet « Démo MT5 »
        de l'interface locale. Aucun identifiant (numéro de compte, serveur) n'est écrit."""
        a = self.mt5.account_info()
        if a is None:
            return None
        off = self.offset() or 0
        origin = lambda m: "Pont (or)" if m == self.magic else self.ORIGINS.get(m, f"Autre ({m})")  # noqa: E731
        pos = [{"ticket": p.ticket, "symbol": p.symbol, "side": "achat" if p.type == 0 else "vente", "volume": p.volume,
                "open": p.price_open, "price": p.price_current, "sl": p.sl or None, "tp": p.tp or None,
                "profit": round(p.profit + p.swap, 2), "opened": int(p.time) - off, "origin": origin(p.magic),
                "comment": p.comment} for p in (self.mt5.positions_get() or [])]
        now = self.clock()
        lo = datetime.fromtimestamp(now + off - 36 * 3600, timezone.utc)
        hi = datetime.fromtimestamp(now + off + 86400, timezone.utc)
        deals = [{"ticket": d.position_id, "symbol": d.symbol, "side": "vente" if d.type == 1 else "achat", "volume": d.volume,
                  "price": d.price, "profit": round(d.profit + d.commission + d.swap, 2), "closed": int(d.time) - off,
                  "origin": origin(d.magic), "comment": d.comment}
                 for d in (self.mt5.history_deals_get(lo, hi) or []) if d.entry == 1 and d.symbol]   # 1 = sortie de position
        return {"updated_at": datetime.fromtimestamp(now, timezone.utc).isoformat().replace("+00:00", "Z"),
                "demo": a.trade_mode == self.mt5.ACCOUNT_TRADE_MODE_DEMO, "currency": a.currency,
                "balance": a.balance, "equity": a.equity, "profit": a.profit, "margin_free": a.margin_free,
                "stopped": self.stop_rule, "positions": pos, "deals": sorted(deals, key=lambda d: -d["closed"]),
                "cols": self.CLOSED_COLS, "closed": self.closed_positions(off)}

    def account_summary(self, days: int = 30) -> dict[str, Any] | None:
        """Résumé du compte pour la page « Les traders » du site (variable PC_ACCOUNT, humeur.py) : solde, et pour
        chaque position fermée des `days` derniers jours [fermeture UTC, résultat $ frais compris, magic, symbole].
        Aucun identifiant (numéro de compte, serveur)."""
        a = self.mt5.account_info()
        if a is None or a.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
            return None
        off = self.offset() or 0
        now = self.clock()
        lo = datetime.fromtimestamp(now + off - days * 86400, timezone.utc)
        hi = datetime.fromtimestamp(now + off + 86400, timezone.utc)
        pos: dict[int, list] = {}
        for d in self.mt5.history_deals_get(lo, hi) or []:
            if not d.symbol:
                continue
            row = pos.setdefault(d.position_id, [0, 0.0, d.magic, d.symbol])
            row[1] += d.profit + d.commission + d.swap
            if d.entry == 1:                       # sortie : heure de fermeture
                row[0] = max(row[0], int(d.time) - off)
        closed = sorted(([r[0], round(r[1], 2), r[2], r[3]] for r in pos.values() if r[0]), key=lambda r: r[0])
        return {"ts": int(now), "bal": round(a.balance, 2), "eq": round(a.equity, 2),
                "open": len(self.mt5.positions_get() or []), "stop": self.stop_rule, "d": closed[-400:]}

    def write_snapshot(self) -> None:
        if self.relay is not None:
            self.relay.account(self.account_summary)
        snap = self.snapshot()
        if snap is None:
            return
        if self.relay is not None:
            self.relay.demo(snap)                      # copie pour la page « Démo MT5 » du site (toutes les minutes)
        f = self.root / "journal" / "demo_live.json"
        f.parent.mkdir(exist_ok=True)
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
        tmp.replace(f)

    # ------------------------------------------------------------ journal
    def record_ticks(self) -> int:
        """Ajoute les nouveaux ticks du courtier (heure du serveur en ms, achat, vente) au fichier du jour."""
        if not self.cfg.get("record_ticks"):
            return 0
        if self.tick_from is None:
            tick = self.mt5.symbol_info_tick(self.sym)
            if tick is None or not tick.time:
                return 0
            self.tick_from = (tick.time - 60) * 1000
        start = datetime.fromtimestamp(self.tick_from / 1000, timezone.utc)
        ticks = self.mt5.copy_ticks_from(self.sym, start, 100000, self.mt5.COPY_TICKS_ALL)
        rows = [t for t in (ticks if ticks is not None else []) if int(t["time_msc"]) > self.tick_from]
        if not rows:
            return 0
        day = datetime.fromtimestamp(self.clock(), timezone.utc).strftime("%Y-%m-%d")
        f = self.root / "ticks" / f"{day}.csv"
        f.parent.mkdir(parents=True, exist_ok=True)
        with f.open("a", encoding="utf-8") as fh:
            fh.writelines(f"{int(t['time_msc'])},{float(t['bid'])},{float(t['ask'])}\n" for t in rows)
        self.tick_from = int(rows[-1]["time_msc"])
        return len(rows)

    def journal(self, event: str, **kw) -> None:
        now = datetime.fromtimestamp(self.clock(), timezone.utc)
        f = self.root / "journal" / f"{now:%Y-%m}.csv"
        f.parent.mkdir(parents=True, exist_ok=True)
        new = not f.exists()
        cols = ["heure_utc", "evenement", "sens", "prix", "stop", "objectif", "lot", "note"]
        with f.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            if new:
                w.writeheader()
            w.writerow({"heure_utc": now.strftime("%Y-%m-%d %H:%M:%S"), "evenement": event,
                        **{k: kw.get(k, "") for k in cols[2:]}})
        log.info("%s %s", event, kw)

    # ------------------------------------------------------------ ordres
    def _filling(self) -> int:
        info = self.mt5.symbol_info(self.sym)
        mode = getattr(info, "filling_mode", 0)
        if mode & 1:
            return self.mt5.ORDER_FILLING_FOK
        if mode & 2:
            return self.mt5.ORDER_FILLING_IOC
        return self.mt5.ORDER_FILLING_RETURN

    def close(self, p, why: str) -> None:
        if self.cfg["mode"] != "demo" or not self.is_demo():
            return
        tick = self.mt5.symbol_info_tick(self.sym)
        long = p.type == self.mt5.POSITION_TYPE_BUY
        res = self.mt5.order_send({
            "action": self.mt5.TRADE_ACTION_DEAL, "symbol": self.sym, "volume": p.volume, "position": p.ticket,
            "type": self.mt5.ORDER_TYPE_SELL if long else self.mt5.ORDER_TYPE_BUY,
            "price": tick.bid if long else tick.ask, "deviation": 30, "magic": self.magic,
            "comment": f"essai18 {why}", "type_time": self.mt5.ORDER_TIME_GTC, "type_filling": self._filling()})
        self.journal("sortie", sens="achat" if long else "vente", prix=tick.bid if long else tick.ask,
                     lot=p.volume, note=f"{why} (code {getattr(res, 'retcode', None)})")

    def manage(self, offset: int) -> bool:
        """Sorties au temps (60 min, 20:30 UTC). Renvoie True si une position du pont reste ouverte."""
        now = self.clock()
        open_ = self.positions()
        for p in open_:
            opened = p.time - offset
            if now >= opened + e18.MAX_HOLD or now >= e18._close_ts(opened):
                self.close(p, "durée")
        return bool(open_)

    # ------------------------------------------------------------ une itération
    def step(self) -> str:
        try:
            self.record_ticks()
        except Exception:                          # l'enregistrement ne doit jamais bloquer le trading
            log.exception("enregistrement des ticks")
        if self.copier is not None:
            try:
                state = self.copier.step()
                if state and state != getattr(self, "_copy_state", ""):
                    log.info("%s", state)
                    self._copy_state = state
            except Exception:                      # la copie ne doit jamais bloquer le scalping
                log.exception("copie des signaux du bot")
        if self.hunter is not None:
            try:
                state = self.hunter.step()
                if state:
                    log.info("%s", state)
            except Exception:                      # la chasse de l'agent ne doit jamais bloquer le reste
                log.exception("chasse de l'agent IA")
        if self.hugo is not None:
            try:
                state = self.hugo.step()
                if state:
                    log.info("%s", state)
            except Exception:                      # idem pour la méthode Hugo
                log.exception("méthode Hugo de l'agent IA")
        if self.asker is not None:
            try:
                state = self.asker.step()
                if state:
                    log.info("%s", state)
            except Exception:                      # idem pour les questions à l'agent
                log.exception("questions à l'agent IA")
        if self.check is not None:
            try:
                state = self.check.step()
                if state:
                    log.info("%s", state)
            except Exception:                      # idem pour le contrôle du soir
                log.exception("contrôle du soir")
        if self.tgcopy is not None:
            try:
                state = self.tgcopy.step()
                if state:
                    log.info("%s", state)
            except Exception:                      # idem pour la copie des canaux Telegram
                log.exception("copie des canaux Telegram")
        off = self.offset()
        if off is None:
            return "flux arrêté"
        bars = self.candles(off)
        now = self.clock()
        if not bars or now - (bars[-1].ts + 60) > 180:
            return "flux arrêté"
        if self.manage(off):
            return "position ouverte"
        if bars[-1].ts == self.last_bar:
            return "rien de neuf"
        self.last_bar = bars[-1].ts
        day = datetime.fromtimestamp(now, timezone.utc).date().isoformat()
        if self.today_pnl(off) <= -float(self.cfg["daily_loss_limit"]):
            if self.limit_day != day:
                self.limit_day = day
                self.journal("limite du jour", note=f"perte du jour ≥ {self.cfg['daily_loss_limit']} $ : arrêt jusqu'à demain")
            return "limite du jour"
        if self.cfg["mode"] == "demo":
            why = demo_rules.check(self.mt5, self.magic, float(self.cfg["lot"]),
                                   datetime.fromtimestamp(now + off, timezone.utc))
            if why:
                if self.stop_rule != why:
                    self.stop_rule = why
                    self.journal("arrêt du démo", note=f"règle d'arrêt franchie : {why} (HYPOTHESES.md)")
                return "règle d'arrêt"
        i = len(bars) - 1
        if not e18.hours_ok(bars[i].ts + 60):
            return "hors horaires"
        x = e18.Ctx(bars)
        d = e18.signal(self.cfg["entry"], x, i)
        if not d:
            return "pas de signal"
        tick = self.mt5.symbol_info_tick(self.sym)
        px = tick.ask if d > 0 else tick.bid
        sens = "achat" if d > 0 else "vente"
        p = e18.plan(x, i, d, px)
        if p is None:
            self.journal("signal refusé", sens=sens, prix=px, note="stop trop large ou obstacle trop proche")
            return "refusé"
        stop, dist = p
        target = px + d * dist
        info = self.mt5.symbol_info(self.sym)
        digits = getattr(info, "digits", 2)
        stop, target = round(stop, digits), round(target, digits)
        min_dist = getattr(info, "trade_stops_level", 0) * getattr(info, "point", 0.01)
        if dist <= min_dist:
            self.journal("signal refusé", sens=sens, prix=px, stop=stop, note="stop plus court que le minimum du courtier")
            return "refusé"
        if self.agent is not None:
            ok, why = self.agent.ask({"sens": sens, "prix": px, "stop": stop, "objectif": target,
                                      "bougies_1m": [c.__dict__ for c in bars[-60:]]})
            if not ok:
                self.journal("refusé par l'agent", sens=sens, prix=px, stop=stop, objectif=target, note=why)
                return "refusé par l'agent"
        if self.cfg["mode"] != "demo":
            self.journal("observé", sens=sens, prix=px, stop=stop, objectif=target, lot=self.cfg["lot"],
                         note="mode observation : aucun ordre")
            return "observé"
        if not self.is_demo():
            self.journal("REFUSÉ", sens=sens, prix=px, note="compte réel : le pont ne trade que sur un compte démo")
            return "compte réel refusé"
        res = self.mt5.order_send({
            "action": self.mt5.TRADE_ACTION_DEAL, "symbol": self.sym, "volume": float(self.cfg["lot"]),
            "type": self.mt5.ORDER_TYPE_BUY if d > 0 else self.mt5.ORDER_TYPE_SELL, "price": px,
            "sl": stop, "tp": target, "deviation": 30, "magic": self.magic, "comment": "essai18",
            "type_time": self.mt5.ORDER_TIME_GTC, "type_filling": self._filling()})
        code = getattr(res, "retcode", None)
        ok = code == self.mt5.TRADE_RETCODE_DONE
        self.journal("entrée" if ok else "ordre rejeté", sens=sens, prix=getattr(res, "price", px) or px,
                     stop=stop, objectif=target, lot=self.cfg["lot"], note=f"code {code}")
        return "entrée" if ok else "ordre rejeté"


def main(argv: list[str]) -> int:
    import MetaTrader5 as mt5                     # module officiel, Windows seulement

    from .agent_hook import Agent
    root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(root / "pont.log", encoding="utf-8")])
    cfg = load_config(root)
    if not mt5.initialize():
        log.error("MetaTrader 5 injoignable (%s) : ouvre le terminal et connecte-toi", mt5.last_error())
        return 1
    if not mt5.symbol_select(cfg["symbol"], True):
        log.error("symbole %s introuvable chez ce courtier", cfg["symbol"])
        return 1
    bridge = Bridge(mt5, cfg, root, agent=Agent(cfg["agent"], root))
    log.info("pont lancé : mode %s, %s, entrée %s, compte démo : %s", cfg["mode"], cfg["symbol"], cfg["entry"], bridge.is_demo())
    last = ""
    while True:
        try:
            state = bridge.step()
            bridge.write_snapshot()
            if state != last:
                log.info("état : %s", state)
                last = state
        except Exception:                          # le pont ne doit pas s'arrêter sur une erreur passagère
            log.exception("erreur, nouvel essai")
            time.sleep(10)
            mt5.initialize()
        time.sleep(float(cfg["poll_seconds"]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
