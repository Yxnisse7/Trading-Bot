"""Les singes traders (demande de Yanisse, 27/10/2026) : chaque compte (Simulation, Topstep, démo MT5 de l'agent IA)
est présenté comme un trader singe, avec une humeur calculée par des règles simples. Clin d'œil aux 1 000 singes de
l'essai 21. Aucun effet sur les trades : l'essai 63 a montré que couper ou réduire selon la forme récente fait perdre.

Humeurs, dans l'ordre de priorité :
  pause       compte arrêté (limite atteinte, compte échoué) ou rien de fermé depuis 4 jours
  tilt        grosse journée rouge (60 % de la perte du jour permise, ou 3 pertes et plus de 2 mises perdues)
  peur        « peur de son ombre » : les stratégies suivies en ombre font nettement mieux que celles en réel (14 jours)
  frustre     au moins 4 pertes sur les 5 derniers trades, ou grosse baisse depuis le plus haut
  euphorique  5 gains d'affilée, ou 8 sur les 10 derniers
  confiant    au moins 3 gains sur les 5 derniers, proche du plus haut
  serein      le reste

Écrit docs/live/traders.json (page « Les traders » et petit singe des autres pages). Le résumé du compte MT5 vient du
PC (variable de dépôt PC_ACCOUNT écrite par le pont) ; PC éteint, le dernier résumé connu est gardé.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

VAR = "PC_ACCOUNT"
PARIS = ZoneInfo("Europe/Paris")
DAY = 86400
QUIET_DAYS = 4
SHADOW_DAYS = 14
CURVE_POINTS = 200
ORIGINS = {"200001": "Copie du bot", "777001": "Claude", "777002": "Agent IA", "777003": "Méthode Hugo",
           "300001": "Copie Telegram", "0": "Manuel"}

PENSEES = {
    "serein": ["Je suis mon plan, trade après trade.", "Rien d'extraordinaire, et c'est très bien comme ça.",
               "Les règles travaillent, moi je regarde."],
    "confiant": ["Ça tourne bien. Je garde la même taille, pas plus.", "Bonne série, mais le marché ne me doit rien.",
                 "Je reste concentré, la prochaine perte viendra aussi."],
    "euphorique": ["Tout me réussit… c'est justement là qu'il faut se méfier.",
                   "Série de gains : je n'augmente pas la mise, promis.", "Je me sens invincible. Mauvais signe."],
    "frustre": ["Les pertes s'enchaînent. Je respecte mes stops et je ne force pas.",
                "Dure période. Une série de pertes fait partie du jeu.", "Je serre les dents, le plan ne change pas."],
    "tilt": ["Grosse journée rouge. Surtout ne pas chercher à me refaire.", "Stop. On souffle, on revient demain.",
             "Je sens l'envie de tout rattraper : c'est le moment de lâcher l'écran."],
    "pause": ["Je suis en pause.", "Rien à faire pour l'instant, j'attends un vrai signal.", "Repos du guerrier."],
    "peur": ["Mon ombre fait mieux que moi… Je garde mes règles, l'ombre n'est qu'un test.",
             "Les stratégies en ombre gagnent, les miennes non. Ça peut être le hasard.",
             "J'ai peur de mon ombre, mais je ne change rien sans preuve."],
}


def _ts(s: str | None) -> int | None:
    if not s:
        return None
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def _paris_day(ts: float) -> str:
    return datetime.fromtimestamp(ts, PARIS).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- l'ombre (commune aux trois comptes)
def ombre(lab_shadow: dict[str, Any] | None, now: float) -> dict[str, Any]:
    """R net moyen sur 14 jours : stratégies en réel (trades annoncés) contre stratégies suivies en ombre."""
    since = now - SHADOW_DAYS * DAY
    real: list[float] = []
    shadow: list[float] = []
    for cell in (lab_shadow or {}).values():
        for t in cell.get("trades") or []:
            r, x = t.get("r_bot"), t.get("exit_ts")
            if r is None or not x or x < since:
                continue
            if cell.get("live") and t.get("notified_entry"):
                real.append(float(r))
            elif not cell.get("live"):
                shadow.append(float(r))
    mr = sum(real) / len(real) if real else None
    ms = sum(shadow) / len(shadow) if shadow else None
    scared = bool(len(real) >= 5 and len(shadow) >= 8 and ms is not None and mr is not None and ms > 0 and ms - mr >= 0.3)
    return {"jours": SHADOW_DAYS, "reel_n": len(real), "reel_r": None if mr is None else round(mr, 3),
            "ombre_n": len(shadow), "ombre_r": None if ms is None else round(ms, 3), "peur": scared}


# ---------------------------------------------------------------- humeur d'un compte
def humeur(trades: list[dict[str, Any]], *, now: float, balance: float, peak: float, start: float, unit: float,
           day_limit: float | None = None, stopped: str | None = None, open_n: int = 0, scared: bool = False,
           drawdown_bad: float = 0.25) -> dict[str, Any]:
    """trades : [{"closed": ts, "pnl": $}] triés du plus ancien au plus récent. unit : une mise typique en $."""
    pnls = [t["pnl"] for t in trades]
    last5, last10 = pnls[-5:], pnls[-10:]
    streak_w = 0
    for p in reversed(pnls):
        if p <= 0:
            break
        streak_w += 1
    streak_l = 0
    for p in reversed(pnls):
        if p > 0:
            break
        streak_l += 1
    today = _paris_day(now)
    tday = [t["pnl"] for t in trades if _paris_day(t["closed"]) == today]
    day_pnl = sum(tday)
    day_losses = sum(1 for p in tday if p <= 0)
    dd = (peak - balance) / peak if peak > 0 else 0.0
    last_close = trades[-1]["closed"] if trades else None
    quiet = (last_close is None or now - last_close > QUIET_DAYS * DAY) and open_n == 0
    reasons: list[str] = []

    if stopped:
        mood = "pause"
        reasons.append(stopped)
    elif quiet:
        mood = "pause"
        reasons.append(f"aucun trade fermé depuis {QUIET_DAYS} jours")
    elif (day_limit and day_pnl <= -0.6 * day_limit) or (day_losses >= 3 and day_pnl <= -2 * unit):
        mood = "tilt"
        reasons.append(f"{day_losses} perte{'s' if day_losses > 1 else ''} aujourd'hui ({day_pnl:+.0f} $)")
    elif scared:
        mood = "peur"
        reasons.append("les stratégies en ombre font mieux que celles en réel")
    elif sum(1 for p in last5 if p <= 0) >= 4 or dd >= drawdown_bad:
        mood = "frustre"
        if sum(1 for p in last5 if p <= 0) >= 4:
            reasons.append(f"{sum(1 for p in last5 if p <= 0)} pertes sur les 5 derniers trades")
        if dd >= drawdown_bad:
            reasons.append(f"{dd:.0%} sous son plus haut".replace("%", " %"))
    elif streak_w >= 5 or (len(last10) >= 10 and sum(1 for p in last10 if p > 0) >= 8):
        mood = "euphorique"
        reasons.append(f"{streak_w} gains d'affilée" if streak_w >= 5 else "8 gains sur les 10 derniers trades")
    elif len(last5) >= 3 and sum(1 for p in last5 if p > 0) >= 3 and dd < 0.10:
        mood = "confiant"
        reasons.append(f"{sum(1 for p in last5 if p > 0)} gains sur les 5 derniers trades")
    else:
        mood = "serein"
        reasons.append("rien d'inhabituel")
    if scared and mood != "peur":
        reasons.append("son ombre fait mieux que lui")

    w10 = sum(1 for p in last10 if p > 0)
    moral = 50 + 5 * (w10 - (len(last10) - w10)) - 100 * dd / 2 + (10 if day_pnl > 0 else -10 if day_pnl < 0 else 0)
    if mood == "pause" and stopped:
        moral = min(moral, 20)
    day_n = int(now // DAY)
    return {"humeur": mood, "moral": int(max(0, min(100, round(moral)))), "raisons": reasons,
            "pensee": PENSEES[mood][day_n % len(PENSEES[mood])],
            "stats": {"solde": round(balance, 2), "depart": round(start, 2), "plus_haut": round(peak, 2),
                      "resultat": round(balance - start, 2), "baisse_pct": round(100 * dd, 1),
                      "jour": round(day_pnl, 2), "trades": len(pnls),
                      "gagnants_pct": round(100 * sum(1 for p in pnls if p > 0) / len(pnls), 1) if pnls else None,
                      "serie": streak_w if streak_w else -streak_l, "ouverts": open_n}}


def _curve(points: list[tuple[int, float]]) -> list[list[float]]:
    if len(points) > CURVE_POINTS:
        step = len(points) / CURVE_POINTS
        points = [points[int(i * step)] for i in range(CURVE_POINTS - 1)] + [points[-1]]
    return [[int(t), round(b, 2)] for t, b in points]


# ---------------------------------------------------------------- les trois comptes
def simulation(pf: dict[str, Any], now: float, scared: bool) -> dict[str, Any] | None:
    hist = [h for h in pf.get("history") or [] if h.get("closed_at") and h.get("pnl") is not None]
    if not pf:
        return None
    hist.sort(key=lambda h: h["closed_at"])
    trades = [{"closed": _ts(h["closed_at"]), "pnl": float(h["pnl"])} for h in hist]
    bal, start = float(pf.get("balance") or 0), float(pf.get("balance_initial") or 0)
    peak = max([start, bal] + [float(h.get("balance_after") or 0) for h in hist])
    unit = bal * float(pf.get("risk_pct") or 1) / 100
    out = humeur(trades, now=now, balance=bal, peak=peak, start=start, unit=unit, open_n=len(pf.get("open") or []),
                 scared=scared, drawdown_bad=0.35)
    start_ts = _ts(pf.get("started_at")) or (trades[0]["closed"] if trades else now)
    out["courbe"] = _curve([(start_ts, start)] + [(t["closed"], float(h.get("balance_after") or 0))
                                                  for t, h in zip(trades, hist)])
    out["derniers"] = [{"t": t["closed"], "pnl": round(t["pnl"], 2), "actif": h.get("asset_label") or h.get("asset"),
                        "sens": h.get("direction"), "source": h.get("source")} for t, h in list(zip(trades, hist))[-8:]][::-1]
    out["note"] = f"compte simulé · départ {start:,.0f} $ · {float(pf.get('risk_pct') or 0):g} % de risque par trade".replace(",", " ")
    return out


def topstep(acct: dict[str, Any], now: float, scared: bool) -> dict[str, Any] | None:
    if not acct:
        return None
    rules = acct.get("rules") or {}
    trades_raw = sorted((t for t in acct.get("trades") or [] if t.get("closed_at") and t.get("pnl") is not None),
                        key=lambda t: t["closed_at"])
    trades = [{"closed": _ts(t["closed_at"]), "pnl": float(t["pnl"])} for t in trades_raw]
    start = float(rules.get("start_balance") or 50000)
    bal = float(acct.get("balance") or start)
    peak = max([start, bal] + [float(t.get("balance_after") or 0) for t in trades_raw])
    stopped = None
    if acct.get("failed"):
        stopped = "compte échoué (perte maximale atteinte)"
    elif acct.get("day_closed"):
        stopped = "journée arrêtée (limite du jour)"
    max_loss = float(rules.get("max_loss") or 2000)
    out = humeur(trades, now=now, balance=bal, peak=peak, start=start, unit=float(acct.get("risk_pct") or 0) / 100 * start or 250,
                 day_limit=float(rules.get("daily_loss") or 1000), stopped=stopped, open_n=len(acct.get("open") or []),
                 scared=scared, drawdown_bad=0.5 * max_loss / peak if peak else 0.02)
    start_ts = _ts(acct.get("started_at")) or (trades[0]["closed"] if trades else now)
    out["courbe"] = _curve([(start_ts, start)] + [(t["closed"], float(r.get("balance_after") or 0))
                                                  for t, r in zip(trades, trades_raw)])
    out["derniers"] = [{"t": t["closed"], "pnl": round(t["pnl"], 2), "actif": r.get("asset_label") or r.get("asset"),
                        "sens": r.get("direction"), "source": r.get("origin")} for t, r in list(zip(trades, trades_raw))[-8:]][::-1]
    out["stats"]["perte_max_reste"] = acct.get("room_to_mll")
    out["stats"]["objectif"] = acct.get("target_balance")
    out["note"] = f"Combine {rules.get('account', '50K')} simulé · statut : {acct.get('status', '?')}"
    return out


def encode_pc(snap: dict[str, Any]) -> str:
    """Résumé compact du compte MT5 pour la variable PC_ACCOUNT (côté PC, depuis Bridge.account_summary)."""
    return json.dumps(snap, separators=(",", ":"), ensure_ascii=False)


def mt5(raw: dict[str, Any] | None, now: float, scared: bool) -> dict[str, Any] | None:
    """raw : {"ts", "bal", "eq", "open", "stop", "d": [[fermé, résultat $, magic], …]} (30 derniers jours)."""
    if not raw:
        return None
    deals = sorted(raw.get("d") or [], key=lambda d: d[0])
    trades = [{"closed": int(d[0]), "pnl": float(d[1])} for d in deals]
    bal = float(raw.get("bal") or 0)
    # solde avant chaque trade, reconstruit à rebours depuis le solde actuel
    run = bal - sum(t["pnl"] for t in trades)
    pts: list[tuple[int, float]] = [((trades[0]["closed"] - 3600) if trades else int(now), run)]
    for t in trades:
        run += t["pnl"]
        pts.append((t["closed"], run))
    start = pts[0][1]
    peak = max(b for _, b in pts)
    day0 = [b for t, b in pts if _paris_day(t) < _paris_day(now)]
    out = humeur(trades, now=now, balance=bal, peak=peak, start=start, unit=0.02 * bal,
                 day_limit=0.06 * (day0[-1] if day0 else bal), stopped=raw.get("stop"), open_n=int(raw.get("open") or 0),
                 scared=scared, drawdown_bad=0.30)
    out["courbe"] = _curve(pts)
    out["derniers"] = [{"t": int(d[0]), "pnl": round(float(d[1]), 2), "actif": d[3] if len(d) > 3 else None, "sens": None,
                        "source": ORIGINS.get(str(d[2]), str(d[2]))} for d in deals[-8:]][::-1]
    out["stats"]["equite"] = raw.get("eq")
    out["note"] = "démo Vantage MT5 · 30 derniers jours · relevé par le pont du PC"
    out["releve"] = datetime.fromtimestamp(int(raw.get("ts") or now), timezone.utc).isoformat().replace("+00:00", "Z")
    return out


def build(*, portfolio: dict[str, Any], topstep_acct: dict[str, Any], lab_shadow: dict[str, Any] | None,
          pc_raw: str | None, previous: dict[str, Any] | None, now: float) -> dict[str, Any]:
    sh = ombre(lab_shadow, now)
    raw = None
    if pc_raw:
        try:
            raw = json.loads(pc_raw)
        except ValueError:
            raw = None
    comptes: dict[str, Any] = {}
    for key, val in (("simulation", simulation(portfolio, now, sh["peur"])),
                     ("topstep", topstep(topstep_acct, now, sh["peur"])),
                     ("mt5", mt5(raw, now, sh["peur"]))):
        if val is None and previous:
            val = (previous.get("comptes") or {}).get(key)
        if val is not None:
            comptes[key] = val
    return {"updated_at": datetime.fromtimestamp(now, timezone.utc).isoformat().replace("+00:00", "Z"),
            "ombre": sh, "comptes": comptes}

