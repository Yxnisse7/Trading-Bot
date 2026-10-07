"""Chances de réussir le Combine Topstep 50K avec les trades du bot (outil d'information, aucun ordre).

Trois séries de trades, exprimées en R (gain ou perte divisé par le risque pris au stop), frais Topstep
réels compris :
  - « compte simulé » : les trades du compte Topstep simulé du bot, au fil de l'eau ;
  - « backtest du bot » : le dernier backtest des quatre actifs annoncés (Nasdaq, S&P 500, Bitcoin, or) ;
  - « donchian or » : la seule stratégie validée par le laboratoire, rejouée sur 24 mois (fichier figé
    `data/topstep/r_donchian_gold.json`, recalculé par `python run.py topstep-odds --rebuild-donchian`).

Le Monte Carlo est fait par le moteur open source de LuxAlgo (`tools/propfirm/odds.mjs`, MIT) : bootstrap en
blocs des R réels (les séries de pertes restent groupées), règles Topstep exactes (perte maximale qui suit le
plus haut de fin de journée et se fige au solde de départ, cohérence 50 %), 10 000 parcours. La perte
journalière n'élimine pas chez Topstep (elle coupe la journée) : elle n'est pas comptée comme un échec.
Skills : monte-carlo-trade-resampling-and-drawdown-distribution, monte-carlo-strategy-robustness-testing.
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .config import ROOT_DIR
from .models import iso, parse_iso, utcnow
from .topstep import FEES, PRODUCTS, RULES

log = logging.getLogger(__name__)

TOOL = ROOT_DIR / "tools" / "propfirm" / "odds.mjs"
REAL_ASSETS = ("nasdaq", "sp500", "bitcoin", "gold")
RISKS = (250.0, 500.0)          # $ risqués au stop : 0,5 % (réglage du compte simulé) et 1 % de 50 000 $
DONCHIAN_FILE = "r_donchian_gold.json"


def topstep_dir() -> Path:
    return ROOT_DIR / "data" / "topstep"


def weekdays_between(a: datetime, b: datetime) -> int:
    d, n = a.date(), 0
    while d <= b.date():
        n += d.weekday() < 5
        d += timedelta(days=1)
    return max(1, n)


def r_from_account(rows: list[dict[str, Any]], risk_pct: float) -> list[float]:
    """R net de chaque trade clos du compte simulé : résultat net ÷ risque pris au stop (risk_pct de la balance
    d'avant le trade)."""
    out = []
    for t in sorted(rows, key=lambda r: r.get("closed_at") or ""):
        if t.get("pnl") is None or t.get("balance_after") is None:
            continue
        before = t["balance_after"] - t["pnl"]
        risk = before * risk_pct / 100
        if risk > 0:
            out.append(round(t["pnl"] / risk, 4))
    return out


def r_from_signal(s: dict[str, Any]) -> float | None:
    """R net Topstep d'un signal de backtest : mouvement brut ÷ distance du stop, moins les frais Topstep
    (commission et un tick de glissement par micro, convertis en points)."""
    asset = s.get("asset")
    if asset not in FEES or asset not in PRODUCTS or s.get("pnl_gross_pct") is None:
        return None
    risk_pts = abs(s["entry"] - s["stop_loss"])
    if risk_pts <= 0:
        return None
    gross_pts = s["pnl_gross_pct"] / 100 * s["entry"]
    fee, tick = FEES[asset]
    cost_pts = (fee + tick) / PRODUCTS[asset][1]
    return round((gross_pts - cost_pts) / risk_pts, 4)


def backtest_profile(data: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    sigs = [s for a in REAL_ASSETS for s in data.get(a, [])]
    sigs.sort(key=lambda s: s.get("created_at") or "")
    rs = [r for r in (r_from_signal(s) for s in sigs) if r is not None]
    if len(rs) < 10:
        return None
    start, end = parse_iso(sigs[0]["created_at"]), parse_iso(sigs[-1]["created_at"])
    return {"key": "backtest", "label": "Backtest du bot (Nasdaq, S&P 500, Bitcoin, or)", "rSeries": rs,
            "tradesPerDay": round(len(rs) / weekdays_between(start, end), 3),
            "period": [iso(start)[:10], iso(end)[:10]]}


def account_profile(dash: dict[str, Any]) -> dict[str, Any] | None:
    rows = [t for t in dash.get("trades") or [] if t.get("closed_at")]
    rs = r_from_account(rows, dash.get("risk_pct") or 0.5)
    if not rs:
        return None
    start = parse_iso(dash.get("started_at") or rows[0]["closed_at"])
    end = parse_iso(max(t["closed_at"] for t in rows))
    return {"key": "account", "label": "Compte Topstep simulé du bot (trades réels)", "rSeries": rs,
            "tradesPerDay": round(len(rs) / weekdays_between(start, end), 3),
            "period": [iso(start)[:10], iso(end)[:10]]}


def build_donchian(candles: list) -> dict[str, Any]:
    """Rejoue donchian_1h sur l'or (historique long gardé hors du dépôt, `store.load_history("gold")`) et garde
    ses R nets Topstep, calculés exactement comme dans le laboratoire."""
    from . import strategies as sl
    trades = sorted(sl.donchian_1h(candles, "gold"), key=lambda t: t.entry_ts)
    trades = [t for t in trades if t.reason != "fin des données"]
    if not trades:
        raise ValueError("aucun trade donchian sur l'historique de l'or")
    tcost = (sum(FEES["gold"]), PRODUCTS["gold"][1])
    rs = [round(sl.trade_rs(t, 0.0, tcost)["net_topstep"], 4) for t in trades]
    start = datetime.fromtimestamp(candles[0].ts, timezone.utc)
    end = datetime.fromtimestamp(candles[-1].ts, timezone.utc)
    return {"strategy": "donchian_1h", "asset": "gold", "rSeries": rs,
            "tradesPerDay": round(len(rs) / weekdays_between(start, end), 3),
            "period": [iso(start)[:10], iso(end)[:10]], "built_at": iso(utcnow())}


def save_donchian(d: dict[str, Any], data_dir: Path | None = None) -> None:
    ddir = data_dir or topstep_dir()
    ddir.mkdir(parents=True, exist_ok=True)
    (ddir / DONCHIAN_FILE).write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8")


def donchian_profile(d: dict[str, Any] | None) -> dict[str, Any] | None:
    if not d or len(d.get("rSeries") or []) < 10:
        return None
    return {"key": "donchian_gold", "label": "Donchian 1 h sur l'or (stratégie validée, 24 mois)",
            "rSeries": d["rSeries"], "tradesPerDay": d["tradesPerDay"], "period": d["period"]}


def witness_profile(base: dict[str, Any] | None) -> dict[str, Any] | None:
    """Témoin sans avantage : les mêmes trades que le backtest, recentrés sur 0 R de moyenne. Il montre ce que
    le hasard seul donne au Combine (un compte qui ne gagne rien réussit quand même parfois)."""
    if not base:
        return None
    m = sum(base["rSeries"]) / len(base["rSeries"])
    return {"key": "witness", "label": "Témoin sans avantage (mêmes trades, moyenne ramenée à 0 R)",
            "rSeries": [round(r - m, 4) for r in base["rSeries"]], "tradesPerDay": base["tradesPerDay"],
            "period": base["period"]}


def summarize_r(rs: list[float]) -> dict[str, Any]:
    n = len(rs)
    return {"n": n, "mean_r": round(sum(rs) / n, 4) if n else None,
            "win_rate": round(sum(1 for r in rs if r > 0) / n, 4) if n else None}


def run_engine(profiles: list[dict[str, Any]], risks=RISKS, paths: int = 10_000, node: str | None = None) -> dict[str, Any]:
    node = node or shutil.which("node")
    if not node or not TOOL.exists() or not (TOOL.parent / "node_modules").exists():
        raise RuntimeError("moteur de simulation absent (node et tools/propfirm/node_modules requis)")
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "in.json", Path(tmp) / "out.json"
        src.write_text(json.dumps({"profiles": [{k: p[k] for k in ("key", "label", "rSeries", "tradesPerDay")} for p in profiles],
                                   "risks": list(risks)}), encoding="utf-8")
        subprocess.run([node, str(TOOL), str(src), str(dst), str(paths)], check=True, timeout=900,
                       cwd=str(TOOL.parent), capture_output=True)
        return json.loads(dst.read_text(encoding="utf-8"))


def build(now: datetime | None = None, data_dir: Path | None = None, engine=run_engine) -> dict[str, Any]:
    now = now or utcnow()
    ddir = data_dir or topstep_dir()
    root = ddir.parent
    profiles = []
    try:
        p = account_profile(json.loads((ddir / "dashboard.json").read_text(encoding="utf-8")))
        if p:
            profiles.append(p)
    except (OSError, ValueError):
        pass
    try:
        p = backtest_profile(json.loads((root / "backtest_trades.json").read_text(encoding="utf-8")))
        if p:
            profiles += [p, witness_profile(p)]
    except (OSError, ValueError):
        pass
    try:
        p = donchian_profile(json.loads((ddir / DONCHIAN_FILE).read_text(encoding="utf-8")))
        if p:
            profiles.append(p)
    except (OSError, ValueError):
        pass
    sim = engine(profiles) if profiles else {"profiles": []}
    by = {p["key"]: p for p in profiles}
    for row in sim.get("profiles", []):
        src = by.get(row["key"], {})
        row["stats"] = summarize_r(src.get("rSeries") or [])
        row["period"] = src.get("period")
        for r in row.get("risks", []):
            fail = r.get("fail") or {}
            total = sum(fail.values())             # le moteur compte toutes les tentatives : on garde des parts
            r["fail"] = {k: round(v / total, 4) for k, v in fail.items() if v} if total else {}
    return {"updated_at": iso(now), "rules": {"account": RULES["account"], "profit_target": RULES["profit_target"],
                                             "max_loss": RULES["max_loss"], "daily_loss": RULES["daily_loss"],
                                             "consistency": RULES["consistency"]},
            "engine": "LuxAlgo prop-firm-sim-core 1.3.0 (MIT)", "paths": sim.get("paths"), "seed": sim.get("seed"),
            "fees": (sim.get("spec") or {}).get("fees"), "flags": sim.get("flags", []), "profiles": sim.get("profiles", [])}


def publish(res: dict[str, Any], data_dir: Path | None = None, docs_dir: Path | None = None) -> None:
    text = json.dumps(res, ensure_ascii=False, separators=(",", ":"))
    for d in (data_dir or topstep_dir(), docs_dir or ROOT_DIR / "docs" / "topstep"):
        d.mkdir(parents=True, exist_ok=True)
        (d / "odds.json").write_text(text, encoding="utf-8")
