"""L'agent IA décide de chaque trade du démo MT5, AVANT l'ordre (demandé par Yanisse le 09/11/2026).

Avant, le pont copiait les signaux tout seul et l'agent donnait son avis après coup. Maintenant, pour chaque signal
de la copie (bot et stratégies, magic 200001) et des canaux Telegram (magic 300001), le pont lance l'agent du dépôt
privé, copié sur le PC, et attend sa décision sans bloquer le reste :

    python agent/avis_direct.py --decider chemin/signal.json

Le signal est celui de l'avis habituel (voir pc_relay._agent), avec en plus le prix du moment (bid, ask) ; ses prix
sont ceux de MetaTrader 5. La DERNIÈRE ligne affichée est la décision en JSON :
    {"action": "prendre"|"refuser"|"attendre", "entree": prix|null, "stop": prix|null, "objectif": prix|null,
     "confiance": 1-5, "raison": "...", "conseil": "..."}
- prendre : ordre tout de suite, avec le SL et le TP de l'agent s'il en donne (sinon ceux de la règle) ;
- refuser : pas de trade ;
- attendre : ordre limite à « entree », annulé au bout de WAIT_MAX (ou à la fin du signal) s'il n'est pas touché ;
- pas de réponse lisible dans TIMEOUT secondes : pas de trade (prudence).
Les niveaux de l'agent sont contrôlés ici (bon côté du prix, distance raisonnable) ; la taille reste celle de la
copie (pourcentage du solde au stop) ; les sorties prévues par la règle restent actives en plus du SL/TP.
Si l'agent installé sur le PC ne connaît pas encore --decider, la copie reste automatique comme avant.
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("decideur")

ACTIONS = ("prendre", "refuser", "attendre")
TIMEOUT = 150            # s : au-delà, pas de trade
WAIT_MAX = 2 * 3600      # s : durée de vie d'un ordre limite « attendre »
STOP_MIN_X, STOP_MAX_X = 0.3, 3.0     # SL de l'agent entre 0,3 et 3 fois la distance de la règle
WAIT_MAX_X = 1.5         # prix d'attente au plus à 1,5 fois la distance du stop du prix actuel
WORDS = {"prendre": "✅ pris", "refuser": "❌ refusé", "attendre": "⏳ en attente d'un meilleur prix",
         "aucune": "⚠️ pas de réponse, pas de trade"}


def _num(x: Any) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def normalize(rep: Any) -> dict[str, Any]:
    """Réponse brute de l'agent → décision propre ; tout ce qui n'est pas lisible devient « aucune »."""
    if not isinstance(rep, dict) or rep.get("action") not in ACTIONS:
        raison = str(rep.get("raison") or "") if isinstance(rep, dict) else ""
        return {"action": "aucune", "entree": None, "stop": None, "objectif": None, "confiance": 0,
                "raison": raison or "Pas de décision lisible de l'agent.", "conseil": ""}
    try:
        conf = max(1, min(5, int(rep.get("confiance") or 3)))
    except (TypeError, ValueError):
        conf = 3
    return {"action": rep["action"], "entree": _num(rep.get("entree")), "stop": _num(rep.get("stop")),
            "objectif": _num(rep.get("objectif")), "confiance": conf,
            "raison": str(rep.get("raison") or "").strip(), "conseil": str(rep.get("conseil") or "").strip()}


def plan(dec: dict[str, Any], long: bool, px: float, stop: float, target: float | None,
         min_dist: float) -> dict[str, Any]:
    """Applique la décision au trade : distances du stop et de l'objectif (comptées depuis le prix d'entrée), prix
    limite pour « attendre ». `px` = prix d'exécution du moment, `stop`/`target` = distances de la règle."""
    sg = 1 if long else -1
    out: dict[str, Any] = {"action": dec["action"], "stop": stop, "target": target, "entry": None, "notes": []}
    if dec["action"] not in ("prendre", "attendre"):
        return out
    ref = px
    if dec["action"] == "attendre":
        e = dec.get("entree")
        gain = sg * (px - e) if e else 0.0
        if not e or gain <= min_dist or gain > WAIT_MAX_X * stop:
            out["action"] = "refuser"
            out["notes"].append("prix d'attente incohérent ou trop loin, pas de trade")
            return out
        out["entry"] = ref = e
    if dec.get("stop") is not None:
        d = sg * (ref - dec["stop"])
        if STOP_MIN_X * stop <= d <= STOP_MAX_X * stop and d > min_dist:
            out["stop"] = d
        else:
            out["notes"].append("SL de l'agent écarté (trop loin, trop près ou du mauvais côté), SL de la règle gardé")
    if dec.get("objectif") is not None:
        t = sg * (dec["objectif"] - ref)
        if t > min_dist:
            out["target"] = t
        else:
            out["notes"].append("TP de l'agent du mauvais côté, TP de la règle gardé")
    return out


def last_json(text: str) -> Any:
    lines = [x for x in text.splitlines() if x.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except ValueError:
        return None


class Decideur:
    """Lance l'agent pour un signal et rend sa décision quand elle est prête (jamais bloquant)."""

    def __init__(self, root: Path, clock: Callable[[], float], cfg: dict[str, Any] | None = None,
                 spawn: Callable[..., Any] = subprocess.Popen):
        self.root, self.clock, self.spawn = Path(root), clock, spawn
        self.cfg = cfg or {}
        self.folder = self.root / "journal" / "decisions"
        self.running: dict[str, tuple[Any, float, Path]] = {}

    def _args(self) -> list[str]:
        cmd = self.cfg.get("command") or ""
        return list(cmd) if isinstance(cmd, list) else cmd.split()

    def available(self) -> bool:
        """Branché, dossier présent, et agent qui connaît --decider (sinon la copie reste automatique)."""
        if not self.cfg.get("decide", True):
            return False
        args, cwd = self._args(), self.cfg.get("dir")
        if not args or not cwd or not Path(cwd).exists():
            return False
        script = next((Path(a) for a in args if a.endswith(".py")), None)
        if script is None:
            return True
        try:
            return "--decider" in script.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return False

    def ask(self, key: str, data: dict[str, Any]) -> bool:
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            path = self.folder / f"{data['id']}.json"
            path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
            logf = self.folder / f"{data['id']}.log"
            out = open(logf, "w", encoding="utf-8")  # noqa: SIM115 — gardé par le processus
            proc = self.spawn(self._args() + ["--decider", str(path)], cwd=self.cfg.get("dir"), stdout=out,
                              stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:                          # l'agent ne doit jamais faire tomber le pont
            log.exception("décision de l'agent (%s)", key)
            return False
        self.running[key] = (proc, self.clock(), logf)
        return True

    def poll(self, key: str) -> dict[str, Any] | None:
        """None tant que l'agent réfléchit ; sinon la décision (« aucune » si panne ou délai dépassé)."""
        item = self.running.get(key)
        if item is None:
            return normalize({"raison": "L'agent n'a pas été lancé."})
        proc, start, logf = item
        if proc.poll() is None:
            if self.clock() - start <= float(self.cfg.get("decide_timeout", TIMEOUT)):
                return None
            proc.kill()
            del self.running[key]
            return normalize({"raison": "L'agent n'a pas répondu à temps."})
        del self.running[key]
        try:
            rep = last_json(logf.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            rep = None
        return normalize(rep)


def line(dec: dict[str, Any], notes: list[str] | None = None) -> str:
    """Ligne Telegram (texte brut, à échapper) de la décision."""
    txt = f"Agent IA : {WORDS.get(dec['action'], dec['action'])}"
    if dec.get("confiance"):
        txt += f" (confiance {dec['confiance']}/5)"
    if dec.get("raison"):
        txt += f". {dec['raison']}"
    if notes:
        txt += f" ({'; '.join(notes)})"
    return txt
