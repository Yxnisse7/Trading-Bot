"""Règles d'arrêt des stratégies en réel, écrites d'avance (HYPOTHESES.md, 10/11/2026).

Une stratégie passe en « ombre » (proposition à Yanisse, jamais automatique) si la somme de ses 20 derniers trades
réels est pire que le pire 1 % des séries de 20 trades de son histoire 2014-2026 ; entre le pire 5 % et le pire 1 % :
« surveiller ». Seuils calculés une fois (frais compris, un trade à la fois).
"""
from __future__ import annotations

from typing import Any

WINDOW = 20
# stratégie → (surveiller, ombre), en R sur 20 trades
LIMITS = {"noise_area_v2": (-10.8, -14.3), "donchian_1h": (-9.0, -14.0), "cassure_williams": (-6.0, -9.9),
          "swing_w3": (-18.3, -20.9), "nuit_asie": (-2.2, -5.0), "bot": (-10.2, -15.6)}
NAMES = {"noise_area_v2": "Zone de bruit v2", "donchian_1h": "Donchian 1 h", "cassure_williams": "Cassure Williams",
         "swing_w3": "W3", "nuit_asie": "Nuit asiatique", "bot": "Bot Nasdaq"}


def level(strategy: str, rs: list[float]) -> dict[str, Any] | None:
    """État d'une stratégie d'après ses derniers trades réels clos (R nets, du plus ancien au plus récent)."""
    if strategy not in LIMITS:
        return None
    last = [float(r) for r in rs[-WINDOW:]]
    total = round(sum(last), 2)
    watch, shadow = LIMITS[strategy]
    state = "ombre" if total <= shadow else "surveiller" if total <= watch else "ok"
    return {"strategy": strategy, "name": NAMES[strategy], "n": len(last), "total_r": total, "watch": watch,
            "shadow": shadow, "state": state}


def from_lab(lab: dict[str, Any]) -> list[dict[str, Any]]:
    """États des stratégies annoncées en réel, lus dans data/lab_shadow.json (trades clos et annoncés)."""
    out = []
    for rec in (lab or {}).values():
        strat = rec.get("strategy")
        rs = [t.get("r_bot") for t in sorted(rec.get("trades") or [], key=lambda t: t.get("entry_ts") or 0)
              if t.get("status") == "closed" and t.get("notified_entry") and t.get("r_bot") is not None]
        row = level(strat, rs) if rs else None
        if row:
            out.append(row)
    return out


def lines(rows: list[dict[str, Any]]) -> list[str]:
    """Lignes pour le contrôle du soir : seulement les stratégies à surveiller ou à mettre en ombre."""
    out = []
    for r in rows:
        if r["state"] == "ok":
            continue
        icon, word = ("🛑", f"limite franchie ({r['shadow']:g} R) : à mettre en ombre ?") if r["state"] == "ombre" \
            else ("⚠️", f"à surveiller (limite {r['shadow']:g} R)")
        out.append(f"{icon} {r['name']} : {r['total_r']:+.1f} R sur ses {r['n']} derniers trades, {word}")
    return out
