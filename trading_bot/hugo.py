"""L'agent IA applique la méthode « BPR » d'un trader Nasdaq vu sur TikTok (demandé par Yanisse le 20/10/2026).

L'essai 40 a codé cette méthode à la lettre : sur 12 ans, elle ne tient pas, et elle trouve très peu de trades, parce
que le trader choisit ses zones « à l'œil ». Ici, c'est Claude (abonnement de Yanisse, jeton CLAUDE_CODE_OAUTH_TOKEN)
qui regarde les graphiques avec ses règles, comme lui. Le pont MT5 du PC le lance (mt5_hugo.py) :

    python -m trading_bot.hugo --marche chemin/marche.json

La DERNIÈRE ligne affichée est la décision en JSON :
    {"action": "achat"|"vente"|"rien", "stop": prix|null, "objectif": prix|null, "confiance": 1-5,
     "raison": "...", "a_surveiller": "..."}
Aucun ordre ici : c'est le pont qui passe l'ordre sur le démo, avec ses garde-fous. L'appel à Claude réutilise
agent/ia.py du dépôt privé de l'agent, copié sur le PC (dossier réglable par AGENT_DIR).
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
MIN_CONF = 3
MIN_RR = 1.5
TIMEOUT = 75

SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["achat", "vente", "rien"]},
        "stop": {"type": ["number", "null"]},
        "objectif": {"type": ["number", "null"]},
        "confiance": {"type": "integer", "minimum": 1, "maximum": 5},
        "raison": {"type": "string"},
        "a_surveiller": {"type": "string"},
    },
    "required": ["action", "stop", "objectif", "confiance", "raison", "a_surveiller"],
}

CONSIGNE = """Tu es un trader de Nasdaq qui applique UNE méthode précise, celle décrite ci-dessous, sur un compte démo.
Tu ne passes pas d'ordre : tu réponds achat, vente ou rien, et un programme applique ensuite le risque
(1 % du solde, une seule position, sortie au stop, à l'objectif ou au plus tard après 4 h).

=== LA MÉTHODE ===
1. Grand cadre d'abord (jour, puis 4 h, puis 1 h) : repère les zones où le prix va chercher de la liquidité :
   anciens plus hauts et plus bas (liquidité acheteuse et vendeuse), FVG non comblés (trou entre la mèche de la
   bougie 1 et celle de la bougie 3 d'un mouvement fort), order blocks (dernière bougie opposée avant un fort
   mouvement, on garde le corps), breaker blocks. Le plus grand cadre l'emporte toujours sur le plus petit.
   Déduis la tendance de fond : on cherche un achat OU une vente, pas les deux.
2. Fibonacci sur le dernier mouvement du grand cadre : un achat sous les 50 % (ou une vente au-dessus) est un
   plus, pas une obligation.
3. Le prix est dans une zone du grand cadre (ou l'a touchée dans la dernière heure) ET y réagit.
4. Déclencheur en petit cadre (15 min, 5 min) : un FVG opposé clôturé à travers (IFVG), ou mieux un BPR
   (un FVG haussier et un FVG baissier qui se chevauchent). La bougie doit être CLÔTURÉE ; un déclencheur clôturé
   dans les 30 dernières minutes compte encore si le prix n'est pas déjà parti vers l'objectif.
5. Stop derrière le BPR ou l'IFVG, ou derrière le creux (achat) ou le sommet (vente) de la réaction.
   Objectif : 2 fois la distance du stop (1:2), placé AVANT la prochaine zone opposée du grand cadre.
6. Heures : 9h-17h (Paris). Pas d'entrée dans les 15 minutes autour de l'ouverture de Wall Street
   (15h30) ni juste avant une annonce forte.
7. Si le marché ne respecte rien (pas de réaction propre sur les zones), on ne trade pas.

=== TES RÉPONSES ===
- Propose un trade dès que les points 1, 3 et 4 sont réunis (le point 2 aide à choisir). Réponds « rien »
  seulement s'il manque une zone, une réaction ou un déclencheur.
- Achat : stop sous le prix d'achat (ask), objectif au-dessus. Vente : stop au-dessus du prix de vente (bid), objectif
  en dessous. L'objectif vaut au moins 1,5 fois le stop (vise 2).
- confiance : 1 (très faible) à 5 (très forte).
- raison : 2 ou 3 phrases en français simple pour un débutant : la zone du grand cadre, le Fibo, le déclencheur
  (ou ce qui manque).
- a_surveiller : si tu réponds « rien », dis en une phrase si un trade peut venir bientôt (quelle zone, à quel prix,
  quel déclencheur attendre, avant quelle heure), ou « rien à surveiller pour l'instant ». Avec un trade, mets "".
Avec « rien », mets stop et objectif à null."""

RIEN = {"action": "rien", "stop": None, "objectif": None, "confiance": 1, "a_surveiller": ""}


def fmt(bougies: list[list[float]], n: int) -> str:
    return "\n".join(f"{datetime.fromtimestamp(x[0], PARIS):%d/%m %H:%M} O {x[1]:g} H {x[2]:g} L {x[3]:g} C {x[4]:g}"
                     for x in bougies[-n:]) or "indisponibles"


def message(m: dict[str, Any]) -> str:
    now = datetime.fromisoformat(m["now"].replace("Z", "+00:00")).astimezone(PARIS)
    annonces = "\n".join(f"- {a.get('heure')} : {a.get('titre')} (impact {a.get('impact')})"
                         for a in m.get("annonces") or []) or "- aucune"
    return f"""Marché : {m.get('asset_label', m.get('asset', '?'))}
Moment : {m.get('moment', '?')} · {now:%A %d/%m/%Y %H:%M} (heure de Paris)
Prix : achat (ask) {m['ask']:g} · vente (bid) {m['bid']:g} · écart {m.get('spread', m['ask'] - m['bid']):g}
Journée : {m.get('journee', 'aucun trade de la méthode aujourd’hui')}

Annonces (de −2 h à +6 h) :
{annonces}

Bougies jour :
{fmt(m.get('candles_1d', []), 20)}

Bougies 4 h :
{fmt(m.get('candles_4h', []), 30)}

Bougies 1 h :
{fmt(m.get('candles_1h', []), 48)}

Bougies 15 min :
{fmt(m.get('candles_15m', []), 48)}

Bougies 5 min :
{fmt(m.get('candles_5m', []), 60)}

Avec la méthode : achat, vente ou rien ?"""


def check(m: dict[str, Any], rep: dict[str, Any]) -> dict[str, Any]:
    """Un trade incohérent ou trop faible devient « rien » (le pont refait ses propres contrôles)."""
    watch = str(rep.get("a_surveiller") or "").strip()
    conf = int(rep.get("confiance") or 1)
    raison = str(rep.get("raison") or "").strip()
    action = rep.get("action")
    if action not in ("achat", "vente"):
        return dict(RIEN, raison=raison, confiance=conf, a_surveiller=watch)
    stop, obj = rep.get("stop"), rep.get("objectif")
    px = m["ask"] if action == "achat" else m["bid"]
    s = 1 if action == "achat" else -1
    if stop is None or obj is None or (px - stop) * s <= 0 or (obj - px) * s < MIN_RR * (px - stop) * s:
        return dict(RIEN, raison=f"Trade proposé incohérent (stop ou objectif), écarté. {raison}", confiance=conf,
                    a_surveiller=watch)
    if conf < MIN_CONF:
        return dict(RIEN, raison=f"Confiance trop faible pour entrer. {raison}", confiance=conf, a_surveiller=watch)
    return {"action": action, "stop": float(stop), "objectif": float(obj), "confiance": conf, "raison": raison,
            "a_surveiller": ""}


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
    ap.add_argument("--marche", required=True, help="fichier JSON du marché (pont MT5)")
    m = json.loads(Path(ap.parse_args().marche).read_text(encoding="utf-8"))
    try:
        d = decide(m)
    except Exception as e:  # noqa: BLE001 — le pont attend toujours une décision sur la dernière ligne
        d = dict(RIEN, raison=f"Erreur de l'agent ({type(e).__name__}).")
    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
