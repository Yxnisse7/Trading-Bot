"""Claude lit un message d'un canal Telegram de signaux et dit ce qu'il demande (demandé par Yanisse le 23/10/2026).

Chaque signaleur écrit à sa façon (« GOLD BUY NOW 4020 SL 4010 TP 4030 », « on sécurise au BE », « clôturez »…) :
plutôt qu'une règle par canal, Claude (abonnement de Yanisse, agent/ia.py du dépôt privé copié sur le PC) traduit le
message en une action simple. Le pont MT5 (mt5_tgcopy.py) le lance :

    python -m trading_bot.tg_parse --message chemin/message.json

La DERNIÈRE ligne affichée est la décision en JSON :
    {"type": "ouverture"|"stop"|"fermer"|"rien", "marche": "gold"|…|null, "sens": "achat"|"vente"|null,
     "entree": prix|null, "stop": prix|null, "objectifs": [prix…], "signal": "id"|null, "raison": "..."}
Aucun ordre ici : c'est le pont qui décide et passe l'ordre sur le démo.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

AGENT_DIR = r"E:\TradingBot\agent\agent"
TIMEOUT = 60
MARKETS = ["gold", "nasdaq", "sp500", "bitcoin", "ethereum", "oil", "euro"]

SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "enum": ["ouverture", "stop", "fermer", "rien"]},
        "marche": {"type": ["string", "null"], "enum": [*MARKETS, None]},
        "sens": {"type": ["string", "null"], "enum": ["achat", "vente", None]},
        "entree": {"type": ["number", "null"]},
        "stop": {"type": ["number", "null"]},
        "objectifs": {"type": "array", "items": {"type": "number"}},
        "signal": {"type": ["string", "null"]},
        "raison": {"type": "string"},
    },
    "required": ["type", "marche", "sens", "entree", "stop", "objectifs", "signal", "raison"],
}

CONSIGNE = """Tu lis un message posté dans un canal Telegram de signaux de trading, et tu dis ce qu'il demande, sans
rien inventer. Un programme copie ensuite sur un compte DÉMO.

Marchés connus : gold (or, XAUUSD, GOLD), nasdaq (NAS100, US100, NQ, USTEC), sp500 (US500, SPX, ES), bitcoin (BTC),
ethereum (ETH), oil (pétrole, WTI, USOIL, CL), euro (EURUSD). Un autre marché → « rien ».

type :
- « ouverture » : le message donne un NOUVEAU trade (achat/buy/long ou vente/sell/short). Mets marche, sens, stop
  (SL) et les objectifs (TP1, TP2… dans l'ordre, liste vide s'il n'y en a pas). entree : le prix d'entrée donné ;
  si c'est une zone (ex. 4020-4015), le prix de la zone le plus proche du prix actuel ; null si « au marché / now »
  sans prix. Sans stop clair, réponds « rien » (le programme ne copie jamais un trade sans stop).
- « stop » : le message demande de déplacer le stop d'un trade déjà ouvert (ex. « SL au BE », « break even »,
  « sécurisez », « SL à 4025 »). stop = le nouveau prix ; pour le BE, le prix d'entrée de ce trade.
- « fermer » : le message demande de sortir d'un trade ouvert (« close », « clôturez », « on coupe », « sortez »).
- « rien » : tout le reste (résultat déjà fait comme « TP1 touché ✅ », analyse, pub, bonjour, question…).
signal : pour « stop » et « fermer », l'id du trade ouvert concerné dans la liste fournie (celui auquel le message
répond, sinon le plus récent du même marché) ; null pour les autres types.
raison : une phrase courte en français simple.
Si tu n'es pas sûr, réponds « rien »."""

RIEN: dict[str, Any] = {"type": "rien", "marche": None, "sens": None, "entree": None, "stop": None, "objectifs": [],
                        "signal": None}


def message(m: dict[str, Any]) -> str:
    opened = "\n".join(f"- id {o['id']} : {o['sens']} {o['marche']} entrée {o['entree']}, stop {o['stop']}, "
                       f"objectifs {o.get('objectifs') or 'aucun'} (message n°{o.get('msg_id')})"
                       for o in m.get("ouverts") or []) or "- aucun"
    prices = "\n".join(f"- {k} : vente {v['bid']:g} · achat {v['ask']:g}" for k, v in (m.get("prix") or {}).items()) \
        or "- inconnus"
    reply = m.get("reponse_a")
    return f"""Canal : {m.get('chat', '?')}
Message n°{m.get('msg_id')}{' (MODIFIÉ, il remplace l’ancienne version)' if m.get('edited') else ''} :
<<<
{m.get('text', '')}
>>>
{f'Il répond au message : <<< {reply} >>>' if reply else 'Il ne répond à aucun message.'}

Trades de ce canal déjà ouverts sur le démo :
{opened}

Prix actuels :
{prices}

Que demande ce message ?"""


def check(m: dict[str, Any], rep: dict[str, Any]) -> dict[str, Any]:
    """Une réponse incomplète devient « rien » (le pont refait ses propres contrôles)."""
    why = str(rep.get("raison") or "").strip()
    kind = rep.get("type")
    ids = {str(o["id"]) for o in m.get("ouverts") or []}
    if kind == "ouverture":
        if rep.get("marche") not in MARKETS or rep.get("sens") not in ("achat", "vente") or rep.get("stop") is None:
            return dict(RIEN, raison=f"Trade incomplet (marché, sens ou stop), pas copié. {why}")
        objs = [float(x) for x in rep.get("objectifs") or []]
        return {**RIEN, "type": kind, "marche": rep["marche"], "sens": rep["sens"], "stop": float(rep["stop"]),
                "entree": None if rep.get("entree") is None else float(rep["entree"]), "objectifs": objs, "raison": why}
    if kind in ("stop", "fermer"):
        if str(rep.get("signal")) not in ids or (kind == "stop" and rep.get("stop") is None):
            return dict(RIEN, raison=f"Trade concerné introuvable. {why}")
        return {**RIEN, "type": kind, "signal": str(rep["signal"]),
                "stop": None if rep.get("stop") is None else float(rep["stop"]), "raison": why}
    return dict(RIEN, raison=why)


def decide(m: dict[str, Any], call: Callable[..., Any] | None = None) -> dict[str, Any]:
    if call is None:
        if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
            return dict(RIEN, raison="Claude n'est pas connecté.")
        sys.path.insert(0, os.environ.get("AGENT_DIR", AGENT_DIR))
        from ia import appeler_claude, installer_claude  # dépôt privé de l'agent, copié sur le PC
        if not installer_claude():
            return dict(RIEN, raison="Claude n'est pas installé sur le PC.")
        call = appeler_claude
    out = call(message(m), CONSIGNE, SCHEMA, TIMEOUT)
    rep = (out or {}).get("structured_output")
    if not rep and out:
        text = out.get("result", "")
        try:
            rep = json.loads(text[text.index("{"):text.rindex("}") + 1])
        except ValueError:
            rep = None
    if not rep or (out or {}).get("is_error"):
        return dict(RIEN, raison="Pas de réponse lisible de Claude.")
    return check(m, rep)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", required=True, help="fichier JSON du message (pont MT5)")
    m = json.loads(Path(ap.parse_args().message).read_text(encoding="utf-8"))
    try:
        d = decide(m)
    except Exception as e:  # noqa: BLE001 — le pont attend toujours une décision sur la dernière ligne
        d = dict(RIEN, raison=f"Erreur de lecture ({type(e).__name__}).")
    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
