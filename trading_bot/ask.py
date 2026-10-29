"""Question posée à l'agent IA depuis Telegram (demandé par Yanisse le 27/10/2026) : « /avis ton avis sur le Nasdaq ? ».

Le pont MT5 du PC (mt5_ask.py) lance ce script avec le marché du moment, les positions ouvertes du démo et la question :

    python -m trading_bot.ask --marche chemin/marche.json

La DERNIÈRE ligne affichée est la réponse en JSON : {"conseil": "garder"|"securiser"|"fermer"|"aucune_position"|
"autre", "reponse": "..."}. Un avis seulement : aucun ordre, aucun stop déplacé.

« /propose btc » (29/10/2026, mode "propose" dans le fichier) : Claude propose un trade sur ce marché, ou rien. Réponse :
{"decision": "achat"|"vente"|"rien", "entree", "stop", "objectif", "confiance": 1-5, "reponse"}. Aucun ordre non plus. L'appel à Claude réutilise agent/ia.py
du dépôt privé de l'agent, copié sur le PC (dossier réglable par AGENT_DIR).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
AGENT_DIR = r"E:\TradingBot\agent\agent"
TIMEOUT = 70
CONSEILS = ("garder", "securiser", "fermer", "aucune_position", "autre")

SCHEMA = {
    "type": "object",
    "properties": {
        "conseil": {"type": "string", "enum": list(CONSEILS)},
        "reponse": {"type": "string"},
    },
    "required": ["conseil", "reponse"],
}

CONSIGNE = """Tu es le conseiller d'un trader débutant qui te pose une question depuis Telegram, sur son compte démo MT5.
Tu vois les bougies du marché concerné (jour, 1 h, 15 min, 5 min), le prix du moment, les annonces à venir et ses
positions ouvertes (sens, entrée, stop, objectif, gain ou perte du moment, qui l'a ouverte).

Réponds à sa question, en français simple, en 6 phrases au plus :
- Commence par ton avis net : la tendance du moment et ce qui peut arriver ensuite (plutôt hausse, plutôt baisse, ou pas
  clair), avec les niveaux de prix qui comptent (support, résistance, creux ou sommet récent).
- S'il a des positions et que sa question les concerne : pour chacune, dis s'il vaut mieux la garder, sécuriser
  (remonter le stop à l'entrée ou sous un creux récent, en donnant le niveau) ou la fermer, et pourquoi.
- Si le marché est fermé, dis-le en une phrase, et donne ton avis pour la réouverture (écart possible à l'ouverture).
- Dis ce qui changerait ton avis (un niveau cassé, une annonce).
- Pas de promesse, pas de certitude : le marché peut faire l'inverse. Tu ne passes aucun ordre et tu ne déplaces
  aucun stop : tu donnes un avis, c'est lui qui décide.
- Si la question n'a rien à voir avec les marchés, réponds brièvement et honnêtement, conseil « autre ».
- conseil : « garder », « securiser » ou « fermer » (pour l'ensemble de ses positions concernées, la plus importante
  si elles diffèrent), « aucune_position » s'il n'a rien d'ouvert sur ce marché, « autre » sinon.
Ne conseille jamais de trader un compte réel ni de grossir une position pour se refaire."""

FAIL = {"conseil": "autre"}

DECISIONS = ("achat", "vente", "rien")
SCHEMA_PROPOSE = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": list(DECISIONS)},
        "entree": {"type": ["number", "null"]},
        "stop": {"type": ["number", "null"]},
        "objectif": {"type": ["number", "null"]},
        "confiance": {"type": "integer", "minimum": 1, "maximum": 5},
        "reponse": {"type": "string"},
    },
    "required": ["decision", "confiance", "reponse"],
}

CONSIGNE_PROPOSE = """Tu es le conseiller d'un trader débutant qui te demande depuis Telegram (/propose) un trade sur un
marché, maintenant, pour son compte démo MT5. Tu vois les bougies (jour, 1 h, 15 min, 5 min), le prix du moment, les
annonces à venir et ses positions ouvertes.

Dis s'il y a un trade à prendre maintenant, ou s'il vaut mieux attendre :
- decision « achat » ou « vente » seulement si tu vois une vraie raison (tendance claire sur 1 h et 15 min, repli
  terminé sur un support ou une résistance, cassure nette) ; sinon « rien ». « Rien » est une bonne réponse.
- entree : le prix d'entrée (le prix du moment, ou un prix d'attente proche si mieux vaut attendre un repli).
- stop : derrière le dernier creux (achat) ou le dernier sommet (vente) qui invaliderait l'idée, pas plus serré que le
  bruit des bougies 5 min.
- objectif : un niveau réaliste (sommet ou creux récent, chiffre rond), au moins 1,5 fois la distance du stop.
- confiance : de 1 (très incertain) à 5 (très net). Un trade correct mais ordinaire vaut 3.
- reponse : en français simple, 5 phrases au plus : la tendance, pourquoi ce trade (ou pourquoi attendre), les
  niveaux, ce qui l'annulerait (un niveau cassé, une annonce dans l'heure). Si le marché est fermé, decision « rien »
  et dis ce que tu surveilles à la réouverture.
- S'il a déjà une position ouverte sur ce marché, tiens-en compte (ne propose pas le sens inverse sans le dire).
Pas de promesse, pas de certitude. Tu ne passes aucun ordre : c'est lui qui décide. Ne conseille jamais de trader un
compte réel ni de grossir une position pour se refaire."""


def fmt(bougies: list[list[float]], n: int) -> str:
    return "\n".join(
        f"{datetime.fromtimestamp(x[0], PARIS):%d/%m %H:%M} O {x[1]:g} H {x[2]:g} L {x[3]:g} C {x[4]:g}"
        for x in bougies[-n:]) or "indisponibles"


def message(m: dict[str, Any]) -> str:
    now = datetime.fromisoformat(m["now"].replace("Z", "+00:00")).astimezone(PARIS)
    annonces = "\n".join(f"- {a.get('heure')} : {a.get('titre')} (impact {a.get('impact')})"
                         for a in m.get("annonces") or []) or "- aucune"
    pos = "\n".join(
        f"- {p.get('marche')} {p.get('sens')} {p.get('lot')} lot, entrée {p.get('entree')}, stop {p.get('stop')}, "
        f"objectif {p.get('objectif')}, gain/perte du moment {p.get('profit')} $, ouverte par {p.get('origine')}"
        for p in m.get("positions") or []) or "- aucune position ouverte"
    demande = ("Demande du trader : propose-moi un trade sur ce marché maintenant, ou dis-moi d'attendre."
               if m.get("mode") == "propose" else f"Question du trader : {m.get('question', '')}")
    return f"""{demande}

Marché concerné : {m.get('asset_label', m.get('asset', '?'))} · {now:%A %d/%m/%Y %H:%M} (heure de Paris)
Prix : achat (ask) {m['ask']:g} · vente (bid) {m['bid']:g}
{("ATTENTION : " + m["ferme"] + ". Le prix ci-dessus est le dernier connu, les bougies s'arrêtent à la clôture : donne ton avis pour la réouverture.") if m.get("ferme") else ""}

Positions ouvertes sur son démo (tous marchés) :
{pos}

Annonces (de −2 h à +6 h, heure de Paris) :
{annonces}

Bougies jour :
{fmt(m.get('candles_1d', []), 10)}

Bougies 1 h :
{fmt(m.get('candles_1h', []), 24)}

Bougies 15 min :
{fmt(m.get('candles_15m', []), 32)}

Bougies 5 min :
{fmt(m.get('candles_5m', []), 36)}

Ta réponse :"""


def check(rep: dict[str, Any]) -> dict[str, Any]:
    text = str(rep.get("reponse") or "").strip()
    if not text:
        return dict(FAIL, reponse="Pas de réponse lisible de Claude.")
    conseil = rep.get("conseil") if rep.get("conseil") in CONSEILS else "autre"
    return {"conseil": conseil, "reponse": text}


def check_propose(rep: dict[str, Any], m: dict[str, Any]) -> dict[str, Any]:
    """Un achat ou une vente sans stop et objectif du bon côté de l'entrée devient « rien »."""
    text = str(rep.get("reponse") or "").strip() or "Pas d'explication de Claude."
    try:
        conf = min(5, max(1, int(rep.get("confiance") or 1)))
    except (TypeError, ValueError):
        conf = 1
    out = {"decision": "rien", "entree": None, "stop": None, "objectif": None, "confiance": conf, "reponse": text}
    d = rep.get("decision")
    if d not in ("achat", "vente"):
        return out
    try:
        stop, target = float(rep["stop"]), float(rep["objectif"])
        entry = float(rep.get("entree") or (m["ask"] if d == "achat" else m["bid"]))
    except (KeyError, TypeError, ValueError):
        return dict(out, reponse=text + " (Niveaux incomplets : pas de trade proposé.)")
    if not (stop < entry < target if d == "achat" else target < entry < stop):
        return dict(out, reponse=text + " (Stop ou objectif du mauvais côté : pas de trade proposé.)")
    return dict(out, decision=d, entree=entry, stop=stop, objectif=target)


def decide(m: dict[str, Any], call: Callable[..., Any] | None = None) -> dict[str, Any]:
    propose = m.get("mode") == "propose"
    fail = {"decision": "rien", "entree": None, "stop": None, "objectif": None, "confiance": 1} if propose else FAIL
    if call is None:
        if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
            return dict(fail, reponse="Claude n'est pas connecté sur le PC.")
        sys.path.insert(0, os.environ.get("AGENT_DIR", AGENT_DIR))
        from ia import appeler_claude, installer_claude  # dépôt privé de l'agent, copié sur le PC
        if not installer_claude():
            return dict(fail, reponse="Claude n'est pas installé sur le PC.")
        call = appeler_claude
    out = call(message(m), CONSIGNE_PROPOSE if propose else CONSIGNE, SCHEMA_PROPOSE if propose else SCHEMA, TIMEOUT)
    rep = (out or {}).get("structured_output")
    if not rep and out:
        text = out.get("result", "")
        try:
            rep = json.loads(text[text.index("{"):text.rindex("}") + 1])
        except ValueError:
            rep = None
    if not rep or (out or {}).get("is_error"):
        return dict(fail, reponse="Pas de réponse lisible de Claude.")
    return check_propose(rep, m) if propose else check(rep)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--marche", required=True, help="fichier JSON du marché (pont MT5)")
    m = json.loads(Path(ap.parse_args().marche).read_text(encoding="utf-8"))
    try:
        d = decide(m)
    except Exception as e:  # noqa: BLE001 — le pont attend toujours une réponse sur la dernière ligne
        d = dict({"decision": "rien", "confiance": 1} if m.get("mode") == "propose" else FAIL,
                 reponse=f"Erreur de l'agent ({type(e).__name__}).")
    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
