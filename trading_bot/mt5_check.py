"""Contrôle du soir : les signaux annoncés dans la journée contre les trades vraiment pris sur MT5 (demandé par
Yanisse le 28/10/2026, après des signaux ratés par des bugs du pont).

Chaque soir de semaine à 23 h 30 (Paris), un message Telegram dit combien de signaux la copie a vus aujourd'hui, combien
sont partis sur MT5, et pour chaque signal raté la raison, pour qu'un bug se voie le soir même. Les doublons (même signal
vu par le PC et par GitHub) ne comptent qu'une fois. Lit journal/copies.json, tenu par la copie (mt5_copy.py).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from . import messages as msg
from .mt5_hunt import PARIS

log = logging.getLogger("mt5_check")

AT = (23, 30)
NAMES = {"bot": "bot classique", "noise_area": "zone de bruit", "noise_area_v2": "zone de bruit v2",
         "donchian_1h": "Donchian 1 h", "swing_w3": "W3", "cassure_williams": "cassure Williams",
         "nuit_asie": "nuit asiatique", "double7": "Double 7"}
ASSETS = {"nasdaq": "Nasdaq", "gold": "Or", "bitcoin": "Bitcoin", "ethereum": "Ethereum", "sp500": "S&P 500",
          "oil": "Pétrole", "euro": "Euro"}


TWIN_WINDOW = 30 * 60


def reason(status: str) -> str:
    """Raison d'un signal raté, en français simple."""
    if status.startswith("agent : "):
        return "l'agent IA : " + status.split(":", 1)[-1].strip()
    if status.startswith("limite annulée"):
        return "ordre limite de l'agent jamais touché"
    if status.startswith("taille minimale"):
        return "le lot minimum risquait trop pour ton solde"
    if status.startswith("rejeté"):
        return f"MT5 a refusé l'ordre ({status.split('(', 1)[-1].rstrip(')')})"
    if status.startswith("refusé"):
        return "règle d'arrêt : " + status.split(":", 1)[-1].strip()
    if status == "trop ancien":
        return "vu trop tard (plus de 15 min après l'annonce)"
    if status.startswith("prix déjà parti"):
        return "le prix était déjà parti quand la copie l'a vu"
    if status.startswith("pas de signal sur les prix MT5"):
        return "le signal de GitHub n'existe pas sur les prix MT5"
    if status.startswith("symbole"):
        return status
    if status == "vu":
        return "vu mais jamais traité (à vérifier)"
    return status


def label(key: str, rec: dict[str, Any]) -> str:
    parts = key.split(":")
    strat = NAMES.get(parts[1], parts[1]) if key.startswith("lab:") and len(parts) > 1 else "bot classique"
    sens = "achat" if rec.get("direction") == "long" else "vente"
    return f"{strat} · {ASSETS.get(rec.get('asset'), rec.get('asset'))} · {sens}"


def _pc_twin(rec: dict[str, Any], todays: dict[str, Any]) -> bool:
    """Signal de GitHub écarté parce que le PC calcule cette stratégie lui-même : c'est un doublon (pas un raté) si
    le PC a eu un signal du même marché et du même sens à 30 min près (09/11 : 4 achats du bot Nasdaq pris par le
    PC, leurs 4 jumeaux de GitHub comptés à tort comme ratés)."""
    if not str(rec.get("status", "")).startswith("pas de signal sur les prix MT5"):
        return False
    seen = float(rec.get("seen") or 0)
    return any(r.get("source") == "local" and r.get("asset") == rec.get("asset")
               and r.get("direction") == rec.get("direction") and abs(float(r.get("seen") or 0) - seen) <= TWIN_WINDOW
               for r in todays.values())


def report(state: dict[str, Any], now: float) -> str:
    """Texte HTML du contrôle pour la journée de Paris qui contient `now`."""
    day = datetime.fromtimestamp(now, PARIS).date()
    start = datetime(day.year, day.month, day.day, tzinfo=PARIS).timestamp()
    todays = {k: r for k, r in state.items() if start <= float(r.get("seen") or 0) <= now}
    twins = [k for k, r in todays.items() if str(r.get("status", "")).startswith("même signal") or _pc_twin(r, todays)]
    real = {k: r for k, r in todays.items() if k not in twins}
    taken = [k for k, r in real.items() if r.get("status") in ("ouvert", "fermé")]
    agent = {k: r for k, r in real.items() if k not in taken and (r.get("agent") or str(r.get("status", "")).startswith(
        ("agent : ", "limite")))}                    # décidé par l'agent IA (09/11/2026) : pas un raté
    missed = {k: r for k, r in real.items() if k not in taken and k not in agent}
    head = f"<b>🔍 Contrôle du soir · {day:%d/%m}</b>"
    if not real:
        return head + "\nAucun signal vu par la copie aujourd'hui."
    lines = [head, f"{len(real)} signal(aux) annoncé(s) · <b>{len(taken)} pris sur MT5</b> · {len(missed)} raté(s)"
             + (f" · {len(agent)} laissé(s) de côté par l'agent" if agent else "")]
    for k, r in sorted(agent.items(), key=lambda kv: kv[1].get("seen") or 0):
        at = datetime.fromtimestamp(float(r.get("seen") or 0), PARIS)
        lines.append(f"🤖 {at:%H:%M} {msg.esc(label(k, r))} : {msg.esc(reason(str(r.get('status', ''))))}")
    if twins:
        lines.append(f"<i>({len(twins)} doublon(s) PC/GitHub non comptés)</i>")
    for k, r in sorted(missed.items(), key=lambda kv: kv[1].get("seen") or 0):
        at = datetime.fromtimestamp(float(r.get("seen") or 0), PARIS)
        lines.append(f"❌ {at:%H:%M} {msg.esc(label(k, r))} : {msg.esc(reason(str(r.get('status', ''))))}")
    if not missed:
        lines.append("✅ Tout ce qui a été annoncé est parti sur MT5.")
    return "\n".join(lines)


class DailyCheck:
    def __init__(self, copier, relay, root: Path, clock: Callable[[], float]):
        self.copier, self.relay, self.clock = copier, relay, clock
        self.file = Path(root) / "journal" / "controle.json"
        try:
            self.state: dict[str, Any] = json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.state = {}

    def step(self) -> str:
        now = self.clock()
        t = datetime.fromtimestamp(now, PARIS)
        if t.weekday() >= 5 or (t.hour, t.minute) < AT or self.state.get("last") == t.date().isoformat():
            return ""
        if self.relay is None or not self.relay.enabled():
            return ""
        self.relay._post(report(self.copier.state, now))
        self.state["last"] = t.date().isoformat()
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.state), encoding="utf-8")
        return "contrôle du soir envoyé"
