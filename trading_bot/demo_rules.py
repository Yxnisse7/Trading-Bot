"""Règles d'arrêt du démo MetaTrader 5, écrites à froid le 13/10/2026 (HYPOTHESES.md, après l'essai 22).

Quand une règle est franchie, le pont et le poste de l'assistant refusent toute nouvelle entrée ; seul Yanisse peut
relancer (en changeant `since` ici, après en avoir parlé). Comptées sur les trades fermés, frais compris.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

SINCE = datetime(2026, 10, 14, tzinfo=timezone.utc)
R1_ONE_R_PER_LOT = 371.0          # 1 R ≈ 3,71 $ à 0,01 lot (stop moyen de R1 à l'essai 18)

RULES: dict[int, dict[str, Any]] = {
    180018: {"name": "pont R1", "max_loss": 25.0, "max_streak": 8, "check_after": 40, "min_mean_r": -0.30},
    777001: {"name": "poste de l'assistant", "max_loss": 100.0, "max_streak": 6},
    200001: {"name": "copie des signaux du bot", "max_loss": 300.0, "max_streak": None},   # 300 $ : choix de Yanisse le 14/10 ; plus de limite de pertes d'affilée (choix du 20/10)
}


def closed_trades(deals, magic: int, entry_out: int) -> list[tuple[int, float]]:
    """(heure de fermeture, résultat en $ frais compris) par position fermée, dans l'ordre."""
    pos: dict[int, dict[str, Any]] = {}
    for d in deals or []:
        if d.magic != magic:
            continue
        p = pos.setdefault(getattr(d, "position_id", id(d)), {"pnl": 0.0, "closed": None})
        p["pnl"] += d.profit + d.commission + d.swap
        if getattr(d, "entry", entry_out) == entry_out:
            p["closed"] = max(p["closed"] or 0, int(d.time))
    return sorted((p["closed"], p["pnl"]) for p in pos.values() if p["closed"] is not None)


def breach(trades: list[tuple[int, float]], magic: int, lot: float = 0.01) -> str | None:
    """Règle franchie (texte à noter au journal), ou None."""
    rule = RULES.get(magic)
    if rule is None or not trades:
        return None
    pnl = [x for _, x in trades]
    total = sum(pnl)
    if total <= -rule["max_loss"]:
        return f"perte cumulée {total:.2f} $ (limite {rule['max_loss']:.0f} $)"
    streak = 0
    for x in reversed(pnl):
        if x >= 0:
            break
        streak += 1
    if rule.get("max_streak") and streak >= rule["max_streak"]:
        return f"{streak} pertes d'affilée (limite {rule['max_streak']})"
    if rule.get("check_after") and len(pnl) >= rule["check_after"]:
        mean_r = total / len(pnl) / (R1_ONE_R_PER_LOT * lot)
        if mean_r < rule["min_mean_r"]:
            return f"moyenne {mean_r:+.2f} R sur {len(pnl)} trades (limite {rule['min_mean_r']:+.2f} R)"
    return None


def check(mt5, magic: int, lot: float = 0.01, now: datetime | None = None) -> str | None:
    """Lit l'historique du terminal depuis SINCE et renvoie la règle franchie, ou None."""
    now = now or datetime.now(timezone.utc) + timedelta(days=1)    # l'heure du serveur est en avance sur UTC
    deals = mt5.history_deals_get(SINCE, now) or []
    return breach(closed_trades(deals, magic, getattr(mt5, "DEAL_ENTRY_OUT", 1)), magic, lot)
