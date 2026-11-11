"""Le gardien : dernier contrôle avant chaque ordre de la copie démo MT5 (demandé par Yanisse le 11/11/2026).

Le test à l'aveugle (200 trades, 11/11) a montré que l'agent IA ne sait pas trier les bons et les mauvais trades de
nos stratégies avec les prix seuls. Le gardien ne juge donc pas le trade : il bloque seulement pour une raison
concrète, que l'on peut vérifier après coup dans le journal.

Bloque (pas d'ordre) :
- MetaTrader 5 déconnecté du courtier ;
- prix figé : dernière cotation vieille de plus de STALE secondes ;
- écart du courtier anormal : écart achat/vente supérieur à SPREAD_MAX fois la distance du stop ;
- risque total ouvert sur le compte (toutes les positions, tous les robots) + ce trade au-dessus de RISK_MAX du solde.
Prévient sans bloquer (ligne dans l'annonce Telegram) :
- annonce économique forte pour ce marché dans les NEWS_BEFORE minutes qui viennent ou tombée depuis moins de
  NEWS_AFTER minutes. Essai 33 : éviter les annonces n'améliore pas les stratégies, mais l'ordre peut glisser ;
  si l'écart s'ouvre vraiment, c'est la règle de l'écart qui bloque.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import demo_rules

STALE = 180          # s
SPREAD_MAX = 0.25    # part de la distance du stop
RISK_MAX = 0.10      # part du solde
NEWS_BEFORE, NEWS_AFTER = 5 * 60, 2 * 60


def server_offset(now: float) -> int:
    day = datetime.fromtimestamp(now, timezone.utc).date()
    return 3600 * (3 if demo_rules._us_dst(day) else 2)


def position_risk(p: Any, info: Any) -> float:
    """Perte en dollars si la position touche son SL (0 sans SL connu ou si le SL protège déjà un gain)."""
    sl, op = float(getattr(p, "sl", 0) or 0), float(getattr(p, "price_open", 0) or 0)
    contract = float(getattr(info, "trade_contract_size", 0) or 0)
    if sl <= 0 or op <= 0 or contract <= 0:
        return 0.0
    long = getattr(p, "type", 0) == 0
    dist = (op - sl) if long else (sl - op)
    return max(0.0, dist * contract * float(getattr(p, "volume", 0) or 0))


def open_risk(mt5) -> float:
    total = 0.0
    for p in mt5.positions_get() or []:
        total += position_risk(p, mt5.symbol_info(p.symbol))
    return total


def events(root: Path) -> list[dict[str, Any]]:
    """Calendrier économique relu sur GitHub par le pont (mt5_bot.SHARED), sinon celui du dernier git pull."""
    for f in (root / "journal" / "bot_pc" / "calendar_cache.json", root / "bot" / "data" / "calendar_cache.json"):
        try:
            return json.loads(f.read_text(encoding="utf-8")).get("events", [])
        except (OSError, ValueError, AttributeError):
            continue
    return []


def news(events: list[dict[str, Any]], asset: str, now: float) -> str:
    """Annonce forte toute proche pour ce marché : texte d'avertissement, ou ""."""
    for e in events or []:
        if e.get("impact") != "high" or asset not in (e.get("assets") or []):
            continue
        try:
            at = datetime.fromisoformat(str(e["at"])).timestamp()
        except (KeyError, ValueError):
            continue
        if -NEWS_AFTER <= at - now <= NEWS_BEFORE:
            mins = int(round((at - now) / 60))
            when = f"dans {mins} min" if mins > 0 else "à l'instant" if mins == 0 else f"il y a {-mins} min"
            return f"annonce forte {when} ({e.get('name', '?')}) : l'ordre peut glisser"
    return ""


def check(mt5, sym: str, tick: Any, info: Any, stop: float, lot: float, balance: float, now: float) -> str:
    """Raison du blocage, ou "" si l'ordre peut partir. `stop` : distance du stop en prix, `lot` : taille prévue."""
    term = getattr(mt5, "terminal_info", lambda: None)()
    if term is not None and getattr(term, "connected", True) is False:
        return "MetaTrader 5 déconnecté du courtier"
    t = float(getattr(tick, "time", 0) or 0)
    if t > 0:
        age = now + server_offset(now) - t
        if age > STALE:
            return f"prix figé depuis {int(age // 60)} min"
    spread = abs(float(tick.ask) - float(tick.bid))
    if stop > 0 and spread > SPREAD_MAX * stop:
        return f"écart du courtier anormal ({spread:.2f}, soit {spread / stop:.0%} du stop)"
    contract = float(getattr(info, "trade_contract_size", 0) or 0)
    if balance > 0 and contract > 0:
        mine = stop * contract * lot
        total = open_risk(mt5) + mine
        if total > RISK_MAX * balance:
            return (f"risque total ouvert trop élevé ({total:.0f} $ avec ce trade, soit {total / balance:.0%} du solde, "
                    f"limite {RISK_MAX:.0%})")
    return ""
