"""Taille conseillée selon l'agitation du marché (essai 56, en ombre depuis le 26/10/2026, choix de Yanisse).

Agitation = amplitude moyenne (plus haut − plus bas, en % de la clôture) des 14 jours d'avant ; repère = médiane de
cette moyenne sur les 250 jours d'avant. Taille = agitation / repère, bornée entre 0,5 et 2 (plus grand quand ça
bouge). Information seulement : la mise réelle de la copie démo ne change pas.
"""
from __future__ import annotations

from statistics import median
from typing import Iterable, Sequence

STRATS = {"noise_area_v2"}
BASE_PCT = 5.0                       # mise actuelle de la copie démo (mt5_copy.RISK_PCT)


def factor(days: Iterable[Sequence[float]]) -> float | None:
    """`days` : (plus haut, plus bas, clôture) des jours **avant** celui du trade, du plus ancien au plus récent."""
    rg = [(h - lo) / c for h, lo, c in days if c]
    if len(rg) < 264:
        return None
    means = [sum(rg[m - 14:m]) / 14 for m in range(len(rg) - 250, len(rg) + 1)]
    ref = median(means[:-1])
    if ref <= 0:
        return None
    return max(0.5, min(2.0, means[-1] / ref))


def line(k: float | None) -> str | None:
    if k is None:
        return None
    mood = "marché agité" if k > 1.1 else "marché calme" if k < 0.9 else "agitation normale"
    pct = f"{BASE_PCT * k:.1f}".replace(".", ",").replace(",0", "")
    return (f"Taille conseillée (essai 56, en ombre) : ×{k:.2f}".replace(".", ",")
            + f" · {mood} → {pct} % au lieu de {BASE_PCT:.0f} %")
