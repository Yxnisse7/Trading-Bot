"""Essai 51 (HYPOTHESES.md) : zone de bruit v2 Nasdaq, stop fixe au départ puis, dès +X R atteint, stop au bord de
la zone (moins une marge en ATR 15 min) déplacé à chaque bougie. Idée de Yanisse (26/10/2026) pour gagner plus souvent.

    python -m trading_bot.essai51          → data/essai51.json
"""
from __future__ import annotations

from .essai50 import main

CELLS = {"B": ("30", "30", "v2", None, 0.0),
         "M1": ("30", "30", "v2", 1.0, 0.5),
         "M2": ("30", "30", "v2", 0.5, 0.25),
         "M3": ("30", "30", "v2", 1.0, 1.0),
         "M4": ("30", "30", "v2", 0.5, 0.5)}

if __name__ == "__main__":
    main(CELLS, 51)
