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
    777002: {"name": "agent IA (chasse)", "max_loss": 100.0, "max_streak": None},   # 20/10, démo seulement
    777003: {"name": "agent IA (méthode Hugo)", "max_loss": 100.0, "max_streak": None},   # 20/10, démo seulement
    # plus de limite : la copie démo tourne comme le futur compte réel (choix de Yanisse le 22/10, après −389 $ ;
    # 300 $ choisis le 14/10, plus de pertes d'affilée depuis le 20/10)
    # 26/10 (choix de Yanisse) : répétition du futur compte réel de 300 € → arrêt du jour à −6 % du solde du matin,
    # arrêt total sous 90 $ de solde ; pas de limite de trades
    200001: {"name": "copie des signaux du bot", "max_loss": None, "max_streak": None,
             "day_loss_pct": 6.0, "min_balance": 90.0},
    300001: {"name": "copie des canaux Telegram", "max_loss": None, "max_streak": None},   # 23/10, démo seulement
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
    if rule.get("max_loss") is not None and total <= -rule["max_loss"]:
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
    trades = closed_trades(deals, magic, getattr(mt5, "DEAL_ENTRY_OUT", 1))
    return breach(trades, magic, lot) or balance_breach(mt5, magic, trades, now)


def balance_breach(mt5, magic: int, trades: list[tuple[int, float]], now: datetime) -> str | None:
    """Règles en % du solde : arrêt du jour (jour du serveur Vantage, solde du matin) et solde minimum du compte."""
    rule = RULES.get(magic) or {}
    if not rule.get("day_loss_pct") and not rule.get("min_balance"):
        return None
    acc = mt5.account_info()
    if acc is None:
        return None
    if rule.get("min_balance") and acc.balance <= rule["min_balance"]:
        return f"solde {acc.balance:.2f} $ (arrêt sous {rule['min_balance']:.0f} $)"
    if rule.get("day_loss_pct"):
        # les heures des deals sont celles du serveur (UTC+3 l'été, +2 l'hiver) ; `now` est déjà décalé d'un jour
        today = (now - timedelta(days=1) + timedelta(hours=3)).date()
        pnl = sum(x for t, x in trades if datetime.fromtimestamp(t, timezone.utc).date() == today)
        start = acc.balance - pnl
        if start > 0 and pnl <= -rule["day_loss_pct"] / 100 * start:
            return f"perte du jour {pnl:.2f} $ ({-100 * pnl / start:.1f} % du solde du matin, limite {rule['day_loss_pct']:.0f} %)"
    return None
