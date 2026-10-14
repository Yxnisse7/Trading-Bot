"""Bot appris (essai 25) : un modèle d'arbres prévoit le R net d'un signal du bot à partir de ce que le bot voyait à
l'entrée (critères alignés, contexte, score, sens, heure, actif). Sur l'or et le Nasdaq, un signal dont le R prévu
n'est pas > 0 est écarté (suivi en silence) : choix de Yanisse le 14/10/2026, après l'essai 25.

Depuis l'essai 26 (choix de Yanisse le 14/10/2026), le Nasdaq a son propre modèle, appris sur les seuls indices
(Nasdaq, S&P 500, DAX : `python -m trading_bot.essai26 --train` → data/models/bot_indices.pkl) ; l'or garde celui de
l'essai 25.

Le modèle est entraîné sur tous les signaux rejoués de 2014-2026 (`python -m trading_bot.essai25 --train`) et
enregistré dans data/models/bot_arbres.pkl ; à réentraîner chaque année.
"""
from __future__ import annotations

import logging
import math
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

ASSETS = ("gold", "nasdaq", "sp500", "bitcoin")
CRITERIA = ("trend_5m", "trend_15m", "trend_1h", "adx", "vwap", "rsi", "macd", "level", "volume", "orb", "pdhl", "corr")
CTX = ("adx", "rsi_dir", "ema_ext", "atr_ratio", "activity", "range_pct", "cost_r", "us_open_min", "weekday")
APPLIED = {"gold", "nasdaq"}                 # actifs où le modèle a passé tous les contrôles
PATH = Path(__file__).resolve().parent.parent / "data" / "models" / "bot_arbres.pkl"
ASSETS_26 = ("gold", "nasdaq", "sp500", "dax", "bitcoin")       # codage de l'actif des modèles de l'essai 26
INDICES_PATH = PATH.parent / "bot_indices.pkl"
MODELS = {"gold": (PATH, ASSETS), "nasdaq": (INDICES_PATH, ASSETS_26)}   # actif → (fichier, codage de l'actif)
_cache: dict[str, Any] = {}


def features(criteria, meta: dict[str, Any] | None, created_at: str, score: float, direction: str, key: str,
             assets: tuple[str, ...] = ASSETS) -> list[float]:
    crit = set(criteria or [])
    ctx = (meta or {}).get("ctx") or {}
    hour = datetime.fromisoformat(created_at.replace("Z", "+00:00")).hour
    x = [1.0 if c in crit else 0.0 for c in CRITERIA]
    x += [float(ctx.get(k) or 0.0) for k in CTX] + [1.0 if ctx else 0.0]
    x += [float(score or 0.0), 1.0 if direction == "long" else -1.0,
          math.sin(2 * math.pi * hour / 24), math.cos(2 * math.pi * hour / 24)]
    x += [1.0 if key == a else 0.0 for a in assets]
    return x


def load(path: Path = PATH) -> Any | None:
    key = str(path)
    if key not in _cache:
        try:
            with open(path, "rb") as f:
                _cache[key] = pickle.load(f)["model"]
        except Exception as exc:  # noqa: BLE001 — modèle absent ou bibliothèque manquante
            log.warning("bot appris indisponible (%s) : signaux concernés écartés", exc)
            _cache[key] = None
    return _cache[key]


def predicted_r(sig) -> float | None:
    """R net prévu pour ce signal, None si le modèle est indisponible."""
    path, assets = MODELS.get(sig.asset, (PATH, ASSETS))
    model = load(path)
    if model is None:
        return None
    x = features(sig.criteria, sig.meta, sig.created_at, sig.score, sig.direction, sig.asset, assets)
    return float(model.predict([x])[0])


def rejects(sig) -> bool:
    """Vrai si le bot appris écarte ce signal (actif concerné et R prévu ≤ 0, ou modèle indisponible)."""
    if sig.asset not in APPLIED:
        return False
    r = predicted_r(sig)
    sig.meta["model_r"] = None if r is None else round(r, 4)
    return r is None or r <= 0
