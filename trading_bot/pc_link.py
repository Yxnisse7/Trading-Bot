"""Lien entre le PC et le bot de GitHub : qui annonce un signal réel sur Telegram (demandé par Yanisse le 19/10/2026).

PC allumé, le pont MT5 calcule les stratégies en direct et annonce lui-même entrées et sorties (pas de retard).
Toutes les minutes, il écrit dans la variable de dépôt PC_ALIVE l'heure et la liste des signaux qu'il a annoncés.
Le bot de GitHub la lit au début de chaque passage (variable `vars.PC_ALIVE` du workflow) :
- signal déjà annoncé par le PC : GitHub se tait (il tient quand même Topstep et la Simulation) ;
- PC vivant mais signal pas encore annoncé : GitHub attend jusqu'à WAIT après la bougie, puis l'annonce lui-même ;
- PC éteint (variable plus vieille que FRESH, 10 min) : GitHub annonce tout, comme avant.
Ce module ne dépend de rien du PC : il sert aux deux côtés.
"""
from __future__ import annotations

import json
from typing import Any

from .mt5_local import same_signal

VAR = "PC_ALIVE"
FRESH = 600          # s : au-delà, le PC est considéré éteint (la variable est lue au début du passage GitHub,
                     # qui peut durer quelques minutes : 3 min de marge feraient des doublons)
WAIT = 15 * 60       # s après la bougie d'entrée : délai laissé au PC avant que GitHub annonce lui-même
KEEP = 2 * 86400     # s : durée de vie des clés annoncées dans la variable

LABELS = {"creux_repris_15m": "Creux repris", "noise_area": "Zone de bruit", "noise_area_v2": "Zone de bruit v2",
          "swing_w3": "Swing W3", "nuit_asie": "Nuit asiatique", "donchian_1h": "Donchian 1 h",
          "cassure_williams": "Cassure Williams", "donchian_day": "Donchian or"}


def encode(ts: float, sent: list[dict[str, Any]]) -> str:
    return json.dumps({"ts": int(ts), "sent": [{"k": s["k"], "d": s.get("d")} for s in sent]},
                      separators=(",", ":"))


def decode(raw: str | None) -> tuple[int, list[dict[str, Any]]]:
    try:
        d = json.loads(raw or "")
        return int(d.get("ts") or 0), [s for s in d.get("sent") or [] if isinstance(s, dict) and s.get("k")]
    except (ValueError, TypeError, AttributeError):
        return 0, []


def alive(raw: str | None, now: float) -> bool:
    ts, _ = decode(raw)
    return 0 <= now - ts <= FRESH


def entry_owner(raw: str | None, strat: str, entry_ts: int, direction: str, now: float) -> str:
    """« pc » (déjà annoncé par le PC), « wait » (PC vivant, on lui laisse le temps) ou « github »."""
    ts, sent = decode(raw)
    key = f"lab:{strat}:{int(entry_ts)}"
    if any(same_signal(key, direction, s["k"], s.get("d")) for s in sent):
        return "pc"
    if 0 <= now - ts <= FRESH and now - entry_ts < WAIT:
        return "wait"
    return "github"
