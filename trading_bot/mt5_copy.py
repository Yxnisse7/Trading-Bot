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

from . import demo_rules
from .mt5_local import LocalEngine, same_signal, server_offset

log = logging.getLogger("mt5_copy")

MAGIC = 200001
RISK_PCT = 0.05
# Risque toléré au lot minimum du courtier (part du solde), par stratégie, quand il dépasse 2 fois RISK_PCT :
# « heures asiatiques » or a un stop de sécurité à 1 % du prix (≈ 41 $ à 0,01 lot), choix de Yanisse le 14/10/2026.
MIN_LOT_MAX_RISK = {"nuit_asie": 0.05}
# Lot minimum imposé par stratégie, quel que soit le risque au stop (choix de Yanisse le 16/10/2026 : nuit asiatique
# au moins 0,05 lot, soit ≈ 5 $ par point et ≈ 210 $ si le stop de sécurité à 1 % est touché).
MIN_LOT = {"nuit_asie": 0.05}
# Taille minimale en $ par point de prix (choix de Yanisse le 14/10/2026 : « au moins 0,50 à 1 $ par point ») ;
# accepté tant que le risque au stop reste sous FLOOR_MAX_RISK du solde, sinon le trade n'est pas copié. Rien pour
# les cryptos : 1 $ par point y voudrait dire 1 bitcoin entier.
MIN_POINT_VALUE = {"NAS100": 0.5, "SP500": 1.0, "XAUUSD+": 1.0}
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


def _ts(s: str | None) -> int | None:
    if not s:
        return None
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def _get(url: str) -> Any:
    url += f"?t={int(time.time())}"              # contourne le cache (jusqu'à 5 min) du serveur de fichiers
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def read_signals(get: Callable[[str], Any] = _get) -> tuple[list[dict[str, Any]], set[str]]:
    """Signaux ouverts à copier, et les actifs (ou « lab ») lus sans erreur."""
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
        # le minimum du courtier risque plus que prévu : toléré jusqu'à 2 fois le risque voulu (ou l'exception)
        cap = max(2 * RISK_PCT, min_lot_risk or 0.0)
        return float(info.volume_min) if info.volume_min * dist * contract <= cap * balance else 0.0
    return round(min(lot, float(info.volume_max)), 2)


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
                 get: Callable[[str], Any] = _get, local: bool = False, relay=None, bot=None):
        self.mt5, self.root, self.journal, self.clock, self.get = mt5, root, journal, clock, get
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
        if now - self.last < EVERY:
            return ""
        self.last = now
        acc = self.mt5.account_info()
        if acc is None or acc.trade_mode != self.mt5.ACCOUNT_TRADE_MODE_DEMO:
            return "copie : compte réel refusé"
        if self.relay is not None:
            self.relay.beat()
        signals, ok = read_signals(self.get)
        local, local_keys = [], set()
        if self.local is not None:
            local, lok = self.local.signals()
            for s in local:
                k = LAB_TARGET_R.get(s["key"].split(":")[1])
                s["target"] = k * s["stop"] if k else None
            if self.bot is not None:
                found, bok = self.bot.signals()       # objectif du bot gardé tel quel
                local, lok = local + found, lok | bok
            ok |= lok
            local_keys = {s["key"] for s in local}
            if self.relay is not None:
                self.relay.local_ok = {k.split(":", 1)[1] for k in lok}
        github_keys = {s["key"] for s in signals}
        live: dict[str, dict[str, Any]] = {}
        for s in local + signals:                    # le calcul local passe en premier
            live.setdefault(s["key"], s)
        pos = self._positions()
        # sorties : signal expiré, ou fermé par le bot (seulement si sa source a bien été lue)
        for key, rec in list(self.state.items()):
            p = pos.get(rec.get("ticket"))
            if p is None:
                if rec.get("ticket") and rec.get("status") == "ouvert":
                    rec["status"] = "fermé"
                continue
            if rec.get("source") == "local":
                source, known = f"local:{key.split(':')[1]}", local_keys
            else:
                # 16/10 : comparé à tous les signaux moins ceux du PC, un trade GitHub que le PC voyait aussi
                # était fermé au redémarrage du pont ; seuls comptent les signaux de GitHub
                source, known = ("lab" if key.startswith("lab:") else rec["asset"]), github_keys
            if rec.get("expires") and now >= rec["expires"]:
                self._close(p, "expiration")
            elif source in ok and key not in known:
                self._close(p, "fermé par la règle" if rec.get("source") == "local" else "fermé par le bot")
        # entrées
        why = demo_rules.check(self.mt5, MAGIC)
        for key, s in live.items():
            if key in self.state:
                continue
            twin = next((k for k, r in self.state.items()
                         if r.get("source", "github") != s.get("source", "github")
                         and same_signal(key, s["direction"], k, r.get("direction"))), None)
            self.state[key] = {"asset": s["asset"], "status": "vu", "expires": s["expires"],
                               "direction": s["direction"], "source": s.get("source", "github")}
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
            self.state[key].update(self._open(s, acc.balance))
            if self.state[key]["status"] == "pas de prix":
                del self.state[key]                 # pas encore de cotation : on réessaie au passage suivant
            elif self.relay is not None and s.get("source") == "local":
                self.relay.entry(key, s, self.state[key])
        self._save()
        if self.relay is not None and self.mt5.positions_get() is not None:   # terminal muet : on ne conclut rien
            self.relay.step(self._positions(), local_keys, ok)
        return f"copie : {sum(1 for r in self.state.values() if r.get('status') == 'ouvert')} position(s)"

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

    def _open(self, s: dict[str, Any], balance: float) -> dict[str, Any]:
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
        sl = round(px - sg * s["stop"], info.digits)
        tp = round(px + sg * s["target"], info.digits) if s["target"] else 0.0
        late = self._already_gone(s, sym, px, sg)
        if late:
            return {"status": late}
        strat = s["key"].split(":")[1] if s["key"].startswith("lab:") else None
        lot = lot_for(balance, s["stop"], info, MIN_LOT_MAX_RISK.get(strat))
        lot = floor_lot(lot, balance, s["stop"], info, MIN_POINT_VALUE.get(sym))
        if strat in MIN_LOT:
            lot = round(min(max(lot, MIN_LOT[strat]), float(info.volume_max)), 2)
        if lot <= 0:
            return {"status": "taille minimale trop risquée"}
        res = self.mt5.order_send({
            "action": self.mt5.TRADE_ACTION_DEAL, "symbol": sym, "volume": lot,
            "type": self.mt5.ORDER_TYPE_BUY if long else self.mt5.ORDER_TYPE_SELL, "price": px, "sl": sl, "tp": tp,
            "deviation": 50, "magic": MAGIC, "comment": s["key"][:COMMENT_MAX], "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self._filling(sym)})
        code = getattr(res, "retcode", None)
        ok = code == self.mt5.TRADE_RETCODE_DONE
        self.journal("copie entrée" if ok else "copie rejetée", sens="achat" if long else "vente",
                     prix=getattr(res, "price", px) or px, stop=sl, objectif=tp or "", lot=lot,
                     note=f"{sym} {s['key']} (code {code})")
        if not ok:
            return {"status": f"rejeté (code {code})"}
        return {"status": "ouvert", "ticket": getattr(res, "order", None) or getattr(res, "deal", None), "symbol": sym,
                "lot": lot}
