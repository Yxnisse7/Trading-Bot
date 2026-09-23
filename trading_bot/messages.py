"""Mise en forme des messages Telegram (HTML) : signaux, issues, lignes de simulation.

Règles communes, les mêmes que sur le site :
  - nombres à la française : virgule décimale, espace des milliers, vrai signe moins ;
  - les prix sont écrits sans séparateur de milliers et en « code » : un appui les copie ;
  - Achat / Vente plutôt que LONG / SHORT, ↗️ / ↘️ plutôt que 🟢 / 🔴 (pas de jugement bon / mauvais) ;
  - aucune formulation qui puisse passer pour une probabilité de gain.
Tout texte venant de l'extérieur (libellés, actualités, notes) est échappé : le message part en HTML.
"""
from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .models import Signal, parse_iso, utcnow

MINUS = "−"
NBSP = " "

CRIT_TEXT = {
    "adx": "tendance forte", "vwap": "VWAP", "rsi": "RSI", "macd": "MACD", "level": "niveau clé",
    "volume": "volume anormal", "orb": "cassure d'ouverture", "pdhl": "niveaux de la veille",
    "corr": "marché meneur favorable",
}
TREND_MULT = {"trend_5m": 1, "trend_15m": 3, "trend_1h": 12}


def esc(text: Any) -> str:
    return html.escape(str(text if text is not None else ""), quote=False)


def strip_html(text: str) -> str:
    """Version texte brut d'un message HTML (journal, console, Discord, secours)."""
    return html.unescape(re.sub(r"</?(b|i|u|s|code|pre|a)(\s[^>]*)?>", "", text))


def num(v: float | None, d: int = 2, group: bool = True) -> str:
    if v is None:
        return "n/a"
    s = f"{abs(v):,.{d}f}" if group else f"{abs(v):.{d}f}"
    s = s.replace(",", NBSP).replace(".", ",")
    neg = v < 0 and round(abs(v), d) > 0
    return (MINUS if neg else "") + s


def signed(v: float | None, d: int = 2, suffix: str = "") -> str:
    if v is None:
        return "n/a"
    plus = "+" if v > 0 and round(v, d) > 0 else ""
    return plus + num(v, d) + suffix


def pct(v: float | None, d: int = 2) -> str:
    """Variation déjà exprimée en %, signée : +0,13 %."""
    return signed(v, d, NBSP + "%")


def rate(ratio: float | None, d: int = 0) -> str:
    """Taux (0-1) : 45 %."""
    return "n/a" if ratio is None else num(ratio * 100, d) + NBSP + "%"


def money(v: float | None, cur: str = "$", d: int = 2, sign: bool = False) -> str:
    if v is None:
        return "n/a"
    return (signed(v, d) if sign else num(v, d)) + NBSP + cur


def decimals_of(tick: float | None, sample: float | None = None) -> int:
    if tick and tick < 1:
        return max(2, len(f"{tick:.10f}".rstrip("0").split(".")[1]))
    if sample is not None:
        s = f"{sample:.6f}".rstrip("0").rstrip(".")
        return max(2, len(s.split(".")[1]) if "." in s else 0)
    return 2


def price(v: float | None, digits: int = 2) -> str:
    """Prix à copier : sans séparateur de milliers, virgule décimale."""
    return num(v, digits, group=False)


def code_price(v: float | None, digits: int = 2) -> str:
    return f"<code>{price(v, digits)}</code>"


def horizon_text(minutes: int | None) -> str:
    m = minutes or 60
    return f"{m // 60} h" if m % 60 == 0 else f"{m} min"


def crit_text(criteria: list[str], base_minutes: int = 5) -> str:
    """« tendance 5 min · 15 min · 1 h, tendance forte, MACD, RSI, VWAP »"""
    crit = list(criteria or [])
    trends = [horizon_text(base_minutes * TREND_MULT[c]) for c in ("trend_5m", "trend_15m", "trend_1h") if c in crit]
    parts = ["tendance " + " · ".join(trends)] if trends else []
    parts += [CRIT_TEXT.get(c, c) for c in crit if c not in TREND_MULT]
    return ", ".join(parts) if parts else "aucun critère aligné"


def news_text(news_context: str | None) -> str:
    """Une ligne courte : « calme », ou l'alerte principale avec son premier titre."""
    ctx = (news_context or "").strip()
    if not ctx:
        return "rien à signaler"
    low = ctx.lower()
    if "calme" in low and "surveiller" not in low and "prudence" not in low:
        return "calme"
    first = ctx.split(" · ")[0]
    first = re.sub(r"\(score \d+\)\s*", "", first)
    first = re.sub(r"^actualité\s+", "", first, flags=re.I)
    first = first.split(" | ")[0].strip()
    if len(first) > 110:
        first = first[:107].rstrip() + "…"
    return "⚠️ " + first[0].lower() + first[1:] if first else "rien à signaler"


def entry_zone(sig: Signal, tick: float | None = None) -> tuple[float, float] | None:
    """Zone d'entrée (même règle que signals.entry_guidance) ; None si gain/risque déjà < 1."""
    from .signals import round_to_tick
    if (sig.risk_reward or 0) < 1.0:
        return None
    tick = float((sig.meta or {}).get("tick") or tick or 0)
    rnd = (lambda v: round_to_tick(v, tick)) if tick > 0 else (lambda v: v)
    limit = rnd((sig.take_profit + sig.stop_loss) / 2.0)
    against = rnd(sig.entry - 0.5 * (sig.entry - sig.stop_loss))
    return (min(limit, against), max(limit, against))


def site_buttons(site_url: str | None, asset_key: str | None = None) -> list[list[tuple[str, str]]]:
    if not site_url:
        return []
    base = site_url.rstrip("/") + "/"
    chart = base + "index.html" + (f"?actif={asset_key}" if asset_key else "") + "#ch-live"
    return [[("📈 Graphique", chart), ("💼 Simulation", base + "portfolio.html")]]


# ----------------------------------------------------------------- signal
def signal_text(sig: Signal, tz: str = "Europe/Paris", *, header: str | None = None, history: str | None = None,
                sim: str | None = None, now: datetime | None = None, digits: int | None = None,
                tick: float | None = None) -> str:
    zone = ZoneInfo(tz)
    dg = digits if digits is not None else decimals_of((sig.meta or {}).get("tick"), sig.entry)
    long = sig.direction == "long"
    word = "↗️ ACHAT" if long else "↘️ VENTE"
    base = int((sig.meta or {}).get("base_minutes") or 5)
    hm = sig.horizon_minutes or 60
    kind = "scalp ~1 h" if hm <= 60 else (f"intraday ~{horizon_text(hm)}" if hm < 360 else f"swing ~{horizon_text(hm)}")
    tp_chg = (sig.take_profit / sig.entry - 1) * 100.0
    sl_chg = (sig.stop_loss / sig.entry - 1) * 100.0
    expires = parse_iso(sig.expires_at).astimezone(zone)
    rr = abs(sig.take_profit - sig.entry) / abs(sig.entry - sig.stop_loss) if sig.entry != sig.stop_loss else 0.0

    lines = []
    if header:
        lines.append(header)
    lines.append(f"<b>{word} · {esc(sig.asset_label)}</b> · {kind}")
    price_time = (sig.meta or {}).get("price_time")
    when = ""
    if price_time:
        t = parse_iso(price_time)
        age = max(0, int(((now or utcnow()) - t).total_seconds() // 60))
        when = f"  <i>clôture {t.astimezone(zone):%H:%M}, il y a {age} min</i>"
    lines.append(f"Entrée {code_price(sig.entry, dg)}{when}")
    lines.append(f"TP     {code_price(sig.take_profit, dg)}  {pct(tp_chg)}")
    lines.append(f"SL     {code_price(sig.stop_loss, dg)}  {pct(sl_chg)}")
    until = f"le {expires:%d/%m} à {expires:%H:%M}" if hm >= 360 else f"à {expires:%H:%M}"
    lines.append(f"Gain/risque <b>{num(rr, 2)}</b> · expire {until}")
    z = entry_zone(sig, tick)
    if z is None:
        lines.append("⚠️ Au prix visé, le gain possible est déjà plus petit que le risque.")
    else:
        lo, hi = z
        beyond = f"au-dessus de {price(hi, dg)}" if long else f"sous {price(lo, dg)}"
        lines.append(f"Zone d'entrée : {price(lo, dg)} à {price(hi, dg)} <i>({beyond}, passez votre tour)</i>")
    lines.append("")
    if sig.source == "manual":
        crit = crit_text(sig.criteria, base) if sig.criteria else "aucun"
        lines.append(f"Critères du bot dans ce sens : {esc(crit)}")
        note = (sig.news_context or "").split("demande manuelle", 1)[-1].lstrip(" :")
        if note:
            lines.append(f"Votre note : {esc(note)}")
        if "Cible petite face aux coûts" in (sig.rationale or ""):
            lines.append("⚠️ Cible petite face aux coûts estimés")
        if history:
            lines.append(history)
    else:
        lines.append(f"Pourquoi : {esc(crit_text(sig.criteria, base))}")
        if history:
            lines.append(history)
        lines.append(f"Actualité : {esc(news_text(sig.news_context))}")
    if sim:
        lines.append(sim)
    return "\n".join(lines)


def history_line(asset_label: str, stats: dict[str, Any] | None) -> str:
    """Historique réel de l'actif face au hasard (trades notifiés uniquement)."""
    name = esc(re.sub(r" \(.*\)$", "", asset_label))
    if not stats or not stats.get("n"):
        return f"Historique {name} : premier trade, pas encore de recul"
    decided = (stats.get("tp") or 0) + (stats.get("sl") or 0)
    if decided < 5:
        return f"Historique {name} : {stats['n']} trade{'s' if stats['n'] > 1 else ''} seulement, pas encore de recul"
    return (f"Historique {name} : {rate(stats.get('win_rate'))} gagnants sur {decided}, "
            f"hasard {rate(stats.get('neutral_win_rate'))}")


def sizing_line(sizing: dict[str, Any] | None, currency: str = "$") -> str:
    if not sizing:
        return ""
    if sizing.get("lots", 0) <= 0:
        return f"Simulation : trade non pris, {esc(sizing.get('reason', ''))}"
    lots = sizing["lots"]
    lots_txt = num(lots, 0 if float(lots).is_integer() else 3, group=False)
    text = (f"Simulation : {lots_txt} {esc(sizing['lot_label'])} · risque {money(sizing['risk_amount'], currency)} "
            f"({num(sizing['risk_pct_effective'], 1)}{NBSP}%)")
    if sizing.get("risky"):
        flags = []
        for w in sizing.get("warnings", []):
            if w.startswith("lot minimal"):
                m = re.search(r"risque au stop ([\d.]+) au lieu de ([\d.]+)", w)
                if m and float(m.group(1)) > float(m.group(2)):
                    flags.append("lot minimal au-dessus du risque visé")
            elif w.startswith("levier"):
                flags.append(f"levier ×{num(sizing.get('leverage'), 0)}")
        text += " · ⚠️ " + (", ".join(flags) if flags else "trade risqué")
    return text


# ----------------------------------------------------------------- issue
def duration_text(minutes: int | None) -> str:
    if minutes is None:
        return ""
    if minutes < 1:
        return "moins d'une minute"
    if minutes < 60:
        return f"{minutes} min"
    return f"{minutes // 60} h {minutes % 60:02d}"


def outcome_text(sig: Signal, row: dict[str, Any] | None = None, currency: str = "$", streak: str = "",
                 digits: int | None = None, initial: float | None = None) -> str:
    dg = digits if digits is not None else decimals_of((sig.meta or {}).get("tick"), sig.entry)
    head = {"tp": "✅ TP", "sl": "❌ SL", "expired": "⏱️ Expiré"}.get(sig.status, sig.status)
    word = "Achat" if sig.direction == "long" else "Vente"
    money_part = f" · <b>{money(row['pnl'], currency, sign=True)}</b>" if row else ""
    lines = [f"<b>{head} · {esc(sig.asset_label)} {word}</b>{money_part}"]
    lines.append(f"{price(sig.entry, dg)} à {price(sig.close_price, dg)} · {pct(sig.pnl_pct)} net · {duration_text(sig.duration_minutes)}")
    if sig.status == "expired":
        lines.append("Ni TP ni SL dans le temps imparti : clôturé au prix du moment.")
    if row:
        bal = row["balance_after"]
        change = f", soit {pct((bal / initial - 1) * 100, 1)} depuis le départ" if initial else ""
        risky = " · ⚠️ trade risqué" if row.get("risky") else ""
        lines.append(f"Balance {money(bal, currency)}{change}{risky}")
        lines.append(f"<i>brut {money(row['pnl_gross'], currency, sign=True)}, coûts {money(row['cost'], currency)}</i>")
    if streak:
        lines.append(streak)
    return "\n".join(lines)


def streak_text(history: list[Signal]) -> str:
    """« 3e gain d'affilée » / « 2e perte d'affilée » à partir des derniers trades notifiés (le plus récent en dernier)."""
    closed = [s for s in history if s.status in ("tp", "sl")]
    if not closed:
        return ""
    last = closed[-1].status
    n = 0
    for s in reversed(closed):
        if s.status != last:
            break
        n += 1
    if n < 2:
        return ""
    return f"{n}e gain d'affilée" if last == "tp" else f"{n}e perte d'affilée"
