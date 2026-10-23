"""Annonces Telegram depuis le PC et avis de l'agent IA (demandé par Yanisse le 19/10/2026).

PC allumé, les stratégies en réel sont calculées par le pont sur les bougies MT5 (mt5_local) : ce module annonce
leur entrée sur Telegram dès la copie démo, puis la sortie en réponse au message d'entrée, avec le résultat MT5.
Toutes les minutes, il écrit la variable de dépôt PC_ALIVE (pc_link) pour que le bot de GitHub se taise sur ces
signaux. Après chaque entrée, l'agent IA (dépôt privé, copié sur le PC) est lancé en arrière-plan avec le signal et
les bougies : il répond lui-même sous le message, sans jamais retarder les ordres.

Rien n'est lu dans un fichier : les jetons viennent des variables d'environnement Windows, tapées par Yanisse.
- TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID : sans eux, le PC n'annonce rien et ne signale pas qu'il est allumé
  (GitHub annonce tout, comme avant) ;
- PONT_GITHUB_TOKEN : jeton GitHub limité au dépôt du bot (droit « Variables » en écriture) ;
- CLAUDE_CODE_OAUTH_TOKEN : lu par l'agent lui-même.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from . import messages as msg
from . import pc_link
from .mt5_local import server_offset
from .notify import _telegram, chat_key, telegram_chat_ids

log = logging.getLogger("pc_relay")

REPO = "Yxnisse7/Trading-Bot"
BEAT = 60
AGENT_TIMEOUT = 90
ASSETS = {"gold": "Or (XAU/USD)", "nasdaq": "Nasdaq 100", "sp500": "S&P 500", "bitcoin": "Bitcoin (BTC/USD)",
          "ethereum": "Ethereum", "oil": "Pétrole", "euro": "Euro (EUR/USD)"}
EXITS = {"noise_area": "quand le prix revient dans la zone (contrôlé chaque demi-heure), au SL, ou en fin de séance",
         "noise_area_v2": "quand le prix revient dans la zone (contrôlé chaque demi-heure), au SL, ou en fin de séance",
         "donchian_1h": "cassure du canal dans l'autre sens, ou au SL",
         "swing_w3": "SL suiveur remonté sous les creux 1 h, au plus tard au bout de 5 jours",
         "nuit_asie": "vente à 03:00 New York, ou au SL de sécurité (1 % sous l'entrée)",
         "cassure_williams": "vente à 02:00 Paris (00:00 UTC), ou au SL (ouverture du jour)",
         "creux_repris_15m": "objectif, SL, ou au bout de 4 h",
         "bot": "au TP, au SL, ou au bout de 24 h"}


def _github(method: str, url: str, token: str, body: dict | None = None) -> int:
    import requests
    r = requests.request(method, url, json=body, timeout=10,
                         headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                  "X-GitHub-Api-Version": "2022-11-28"})
    return r.status_code


class Relay:
    def __init__(self, mt5, root: Path, clock: Callable[[], float], agent: dict[str, Any] | None = None,
                 env: dict[str, str] | None = None, send: Callable[..., int | None] = _telegram,
                 github: Callable[..., int] = _github, spawn: Callable[..., Any] = subprocess.Popen):
        self.mt5, self.root, self.clock = mt5, root, clock
        self.env = os.environ if env is None else env
        self.send, self.github, self.spawn = send, github, spawn
        self.agent = agent or {}
        self.file = root / "journal" / "telegram_pc.json"
        self.last_beat = 0.0
        self.local_ok: set[str] = set()               # stratégies calculées sur le PC au dernier passage
        self.pc_trades: list[dict[str, Any]] | None = None   # trades du bot classique sur le PC (mt5_bot)
        self.sent_trades = ""
        self.running: list[tuple[Any, float, str]] = []
        try:
            self.state: dict[str, Any] = json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.state = {}

    # ------------------------------------------------------------------ état
    @property
    def token(self) -> str:
        return self.env.get("TELEGRAM_BOT_TOKEN") or ""

    def enabled(self) -> bool:
        return bool(self.token and self.env.get("TELEGRAM_CHAT_ID"))

    def _save(self) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.state, indent=1, ensure_ascii=False), encoding="utf-8")

    def _post(self, body: str, reply: dict[str, int] | None = None) -> dict[str, int]:
        ids = {}
        for cid in telegram_chat_ids():
            mid = self.send(self.token, cid, body, html=True, reply_to=(reply or {}).get(chat_key(cid)))
            if mid:
                ids[chat_key(cid)] = mid
        return ids

    # ------------------------------------------------------------------ PC allumé
    def beat(self) -> None:
        """Écrit PC_ALIVE (heure + signaux annoncés) au plus une fois par minute."""
        now = self.clock()
        tok = self.env.get("PONT_GITHUB_TOKEN")
        if not tok or not self.enabled() or now - self.last_beat < BEAT:
            return
        self.last_beat = now
        sent = [{"k": k, "d": r.get("direction")} for k, r in self.state.items()
                if now - r.get("ts", 0) <= pc_link.KEEP]
        self._put(tok, pc_link.VAR, pc_link.encode(now, sent, self.local_ok))
        if self.pc_trades is not None:
            trades = json.dumps(self.pc_trades, separators=(",", ":"), ensure_ascii=False)
            if trades != self.sent_trades and self._put(tok, pc_link.TRADES, trades):
                self.sent_trades = trades

    def _put(self, tok: str, name: str, value: str) -> bool:
        base = f"https://api.github.com/repos/{REPO}/actions/variables"
        try:
            code = self.github("PATCH", f"{base}/{name}", tok, {"name": name, "value": value})
            if code == 404:
                code = self.github("POST", base, tok, {"name": name, "value": value})
            if code not in (200, 201, 204):
                log.warning("variable %s : réponse %s (jeton GitHub ?)", name, code)
            return code in (200, 201, 204)
        except Exception as exc:                      # GitHub injoignable : il reprendra la main tout seul
            log.warning("variable %s : %s", name, exc)
            return False

    # ------------------------------------------------------------------ entrée
    def entry(self, key: str, s: dict[str, Any], rec: dict[str, Any]) -> None:
        """Annonce un signal calculé sur le PC (une seule fois), puis lance l'agent IA."""
        if not self.enabled() or key in self.state:
            return
        strat = key.split(":")[1]
        long = s["direction"] == "long"
        sym = rec.get("symbol") or ""
        info = self.mt5.symbol_info(sym) if sym else None
        digits = int(getattr(info, "digits", 2) or 2)
        sg = 1 if long else -1
        stop = s["entry"] - sg * s["stop"]
        target = s["entry"] + sg * s["target"] if s.get("target") else None
        chg = lambda v: msg.pct((v / s["entry"] - 1) * 100.0)  # noqa: E731
        copy = (f"copié, {msg.num(rec.get('lot'), 2)} lot" if rec.get("status") == "ouvert"
                else f"pas copié ({rec.get('status')})")
        lines = [f"<b>{'↗️ ACHAT' if long else '↘️ VENTE'} · {msg.esc(ASSETS.get(s['asset'], s['asset']))}</b>"
                 f" · {msg.esc(pc_link.LABELS.get(strat, strat))}",
                 f"Entrée {msg.code_price(s['entry'], digits)}",
                 f"SL     {msg.code_price(stop, digits)}  {chg(stop)}",
                 f"TP     {msg.code_price(target, digits)}  {chg(target)}" if target else "TP     aucun",
                 f"Sortie : {EXITS.get(strat, 'selon la règle de la stratégie')}.",
                 "",
                 f"MT5 démo : {msg.esc(copy)}",
                 "Topstep et Simulation : calculés par le bot en ligne (voir le site).",
                 "<i>Annoncé par ton PC, prix MetaTrader 5. Le bot ne passe aucun ordre réel.</i>"]
        ids = self._post("\n".join(lines))
        if not ids:
            return                                    # Telegram injoignable : GitHub annoncera après pc_link.WAIT
        self.state[key] = {"asset": s["asset"], "direction": s["direction"], "entry": s["entry"],
                           "created": s.get("created"), "expires": s.get("expires"), "ticket": rec.get("ticket"),
                           "symbol": sym, "lot": rec.get("lot"), "msg": ids, "ts": self.clock()}
        self._save()
        self.last_beat = 0.0                          # GitHub doit l'apprendre tout de suite
        self.beat()
        self._agent(key, s, sym, stop, target, ids)

    # ------------------------------------------------------------------ sortie
    def step(self, positions: dict[int, Any], local_keys: set[str], local_ok: set[str]) -> None:
        """Annonce la sortie des signaux annoncés par le PC, en réponse à l'entrée ; surveille l'agent."""
        self._reap()
        if not self.enabled():
            return
        now = self.clock()
        changed = False
        for key, r in self.state.items():
            if r.get("exit_sent"):
                continue
            strat = key.split(":")[1]
            ticket = r.get("ticket")
            if ticket:
                # fermée seulement si l'historique du courtier montre bien la sortie (entrée + sortie)
                closed = ticket not in positions and len(self.mt5.history_deals_get(position=ticket) or []) >= 2
            else:
                closed = (f"local:{strat}" in local_ok and key not in local_keys) or bool(
                    r.get("expires") and now >= r["expires"])
            if not closed:
                continue
            self._exit(key, r, now)
            r["exit_sent"] = True
            changed = True
        if changed:
            self._save()

    def _exit(self, key: str, r: dict[str, Any], now: float) -> None:
        strat = key.split(":")[1]
        long = r["direction"] == "long"
        sg = 1 if long else -1
        sym = r.get("symbol") or ""
        info = self.mt5.symbol_info(sym) if sym else None
        digits = int(getattr(info, "digits", 2) or 2)
        profit, exit_px, why = None, None, "fin du signal (règle de la stratégie)"
        if r.get("ticket"):
            deals = self.mt5.history_deals_get(position=r["ticket"]) or []
            if deals:
                profit = sum(float(d.profit) + float(getattr(d, "commission", 0) or 0) + float(getattr(d, "swap", 0) or 0)
                             for d in deals)
                last = deals[-1]
                exit_px = float(last.price)
                reason = getattr(last, "reason", None)
                if reason == getattr(self.mt5, "DEAL_REASON_SL", -1):
                    why = "SL touché"
                elif reason == getattr(self.mt5, "DEAL_REASON_TP", -1):
                    why = "TP touché"
                elif "expiration" in (getattr(last, "comment", "") or ""):
                    why = "fin prévue (heure de sortie)"
        if exit_px is None and sym:
            tick = self.mt5.symbol_info_tick(sym)
            exit_px = float((tick.bid if long else tick.ask) if tick is not None else r["entry"])
        exit_px = exit_px or r["entry"]
        move = (exit_px / r["entry"] - 1) * 100.0 * sg
        gain = profit > 0 if profit is not None else move > 0
        minutes = int((now - (r.get("created") or r["ts"])) // 60)
        lines = [f"<b>{'✅ GAIN' if gain else '❌ PERTE'} · {msg.esc(ASSETS.get(r['asset'], r['asset']))} "
                 f"{'Achat' if long else 'Vente'}</b> · {msg.esc(pc_link.LABELS.get(strat, strat))}",
                 f"{msg.price(r['entry'], digits)} → {msg.price(exit_px, digits)} · {msg.pct(move)} · "
                 f"{msg.duration_text(minutes)}",
                 f"Raison : {why}",
                 "",
                 (f"MT5 démo : <b>{msg.money(profit, sign=True)}</b> ({msg.num(r.get('lot'), 2)} lot, frais compris)"
                  if profit is not None else "MT5 démo : pas de copie"),
                 "Topstep et Simulation : sur le site (calculés par le bot en ligne)."]
        self._post("\n".join(lines), reply=r.get("msg"))

    # ------------------------------------------------------------------ agent IA
    def _agent(self, key: str, s: dict[str, Any], sym: str, stop: float, target: float | None,
               ids: dict[str, int], sortie: str | None = None, ticket: int | None = None) -> None:
        cmd, cwd = self.agent.get("command"), self.agent.get("dir")
        if not cmd or not cwd or not Path(cwd).exists():
            return
        try:
            data = {"id": key.replace(":", "-"), "strategie": key.split(":")[1], "asset": s["asset"],
                    "asset_label": ASSETS.get(s["asset"], s["asset"]), "direction": s["direction"],
                    "entry": s["entry"], "stop_loss": stop, "take_profit": target,
                    "sortie": sortie if sortie is not None else EXITS.get(key.split(":")[1], ""),
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(s.get("created") or self.clock())),
                    "telegram_message_ids": self._chat_ids(ids), "ticket_mt5": ticket or self.state.get(key, {}).get("ticket"),
                    "candles_5m": self._candles(sym, "TIMEFRAME_M5", 288, s.get("created")),
                    "candles_1h": self._candles(sym, "TIMEFRAME_H1", 48, s.get("created")),
                    "candles_1d": self._candles(sym, "TIMEFRAME_D1", 20, s.get("created"))}
            folder = self.root / "journal" / "avis"
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"{data['id']}.json"
            path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
            args = (cmd if isinstance(cmd, list) else cmd.split()) + ["--signal", str(path)]
            out = open(folder / f"{data['id']}.log", "w", encoding="utf-8")
            proc = self.spawn(args, cwd=cwd, stdout=out, stderr=subprocess.STDOUT,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.running.append((proc, self.clock(), key))
        except Exception:                             # l'avis ne doit jamais gêner le pont
            log.exception("agent IA (%s)", key)

    def _chat_ids(self, ids: dict[str, int]) -> dict[str, int]:
        """Numéros des messages par chat, pour l'agent (ce fichier reste sur le PC)."""
        return {cid: ids[chat_key(cid)] for cid in telegram_chat_ids() if chat_key(cid) in ids}

    def _candles(self, sym: str, tf: str, n: int, until: int | None) -> list[list[float]]:
        if not sym:
            return []
        off = server_offset(self.mt5, sym, self.clock()) or 0
        rates = self.mt5.copy_rates_from_pos(sym, getattr(self.mt5, tf), 0, n + 30)
        if rates is None:
            return []
        rows = [[int(x["time"]) - off, float(x["open"]), float(x["high"]), float(x["low"]), float(x["close"])]
                for x in rates]
        if until:
            rows = [x for x in rows if x[0] < until]
        return rows[-n:]

    def _reap(self) -> None:
        now, keep = self.clock(), []
        for proc, start, key in self.running:
            if proc.poll() is not None:
                continue
            if now - start > float(self.agent.get("timeout", AGENT_TIMEOUT)):
                proc.kill()
                log.warning("agent IA arrêté après %s s (%s)", AGENT_TIMEOUT, key)
                continue
            keep.append((proc, start, key))
        self.running = keep
