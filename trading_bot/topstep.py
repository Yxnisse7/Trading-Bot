"""Compte Topstep 50K simulé : uniquement les trades que vous avez réellement pris, avec les règles Topstep.

Séparé de tout le reste, comme le mode halal : la simulation du bot principal n'est pas touchée et le
bot n'ajoute aucun trade de lui-même. Le compte contient :
  - vos trades manuels (/long, /short, « Nouveau trade » du site), automatiquement ;
  - les signaux du bot que vous marquez « pris » (/pris, bouton du site), avec vos contrats ;
  - les trades faits hors du bot, saisis au journal (/journal).
Le résultat d'un signal suit sa vraie issue (TP, SL, expiration), ou votre arrêt manuel s'il y en a un.

Règles appliquées (compte d'évaluation 50K, septembre 2026 — à vérifier sur topstep.com avant de trader) :
  - objectif de gain : +3 000 $ ;
  - perte maximale (MLL) : 2 000 $ sous le plus haut solde de fin de journée, jamais au-dessus de 50 000 $ ;
  - limite de perte journalière (DLL, facultative) : 1 000 $ ;
  - cohérence : la meilleure journée ne dépasse pas 50 % du gain total ;
  - taille maximale : 5 contrats standards ou 50 micros en même temps ;
  - positions fermées avant 15:10 heure de Chicago (Topstep ferme lui-même à partir de 15:08) ;
  - la journée de trading commence à 17:00 heure de Chicago.

Données : data/topstep/account.json (vos choix : trades pris, contrats, journal) et
data/topstep/dashboard.json (compte calculé), copié dans docs/topstep/ pour le site.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .config import DATA_DIR, ROOT_DIR, Config
from .models import Signal, iso, parse_iso, utcnow

CHICAGO = ZoneInfo("America/Chicago")

RULES = {
    "account": "50K",
    "start_balance": 50_000.0,
    "profit_target": 3_000.0,
    "max_loss": 2_000.0,
    "daily_loss": 1_000.0,
    "consistency": 0.50,
    "max_micros": 50,            # 5 contrats standards = 50 micros
    "flat_by_ct": (15, 10),      # heure de Chicago
    "day_start_ct": 17,          # nouvelle journée de trading à 17:00 heure de Chicago
}

# Contrat micro Topstep correspondant à chaque actif du bot : (symbole, $ par point et par micro)
PRODUCTS = {
    "nasdaq": ("MNQ", 2.0), "sp500": ("MES", 5.0), "gold": ("MGC", 10.0), "oil": ("MCL", 100.0),
    "euro": ("M6E", 12_500.0), "bitcoin": ("MBT", 0.1), "ethereum": ("MET", 0.1),
}
DEFAULT_RISK = 200.0             # risque par trade par défaut : 10 % de la perte maximale autorisée


def _data_dir() -> Path:
    base = Path(DATA_DIR)
    return base.parent / "topstep" if base.name == "halal" else base / "topstep"


class TopstepAccount:
    def __init__(self, data_dir: Path | None = None, docs_dir: Path | None = None):
        self.dir = Path(data_dir or _data_dir())
        if docs_dir is None and self.dir.resolve() == (ROOT_DIR / "data" / "topstep").resolve():
            docs_dir = ROOT_DIR / "docs" / "topstep"
        self.docs = docs_dir
        self.file = self.dir / "account.json"
        self.state = self._load()

    # ------------------------------------------------------------ vos choix
    def _load(self) -> dict[str, Any]:
        try:
            return json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"risk_per_trade": DEFAULT_RISK, "taken": {}, "removed": [], "journal": [], "exits": {},
                    "created_at": iso(utcnow())}

    def save(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding="utf-8")

    def take(self, sig: Signal, contracts: int | None = None) -> dict[str, Any]:
        if sig.asset not in PRODUCTS:
            raise ValueError(f"{sig.asset_label} n'a pas de contrat équivalent chez Topstep")
        if sig.source == "shadow":
            raise ValueError("un signal suivi en silence n'a pas été envoyé : il ne peut pas avoir été pris")
        n = int(contracts) if contracts else self.default_contracts(sig)
        if not 1 <= n <= RULES["max_micros"]:
            raise ValueError(f"nombre de micros entre 1 et {RULES['max_micros']}")
        self.state.setdefault("taken", {})[sig.id] = {"contracts": n, "at": iso(utcnow())}
        self.state["removed"] = [i for i in self.state.get("removed", []) if i != sig.id]
        self.save()
        return {"id": sig.id, "contracts": n}

    def remove(self, ref: str) -> str:
        ref = ref.strip()
        taken = self.state.setdefault("taken", {})
        journal = self.state.setdefault("journal", [])
        for key in list(taken):
            if key.startswith(ref):
                del taken[key]
                self.state.setdefault("removed", []).append(key)
                self.save()
                return key
        for j in journal:
            if j["id"].startswith(ref):
                journal.remove(j)
                self.save()
                return j["id"]
        # un trade manuel (inclus d'office) peut aussi être retiré
        self.state.setdefault("removed", []).append(ref)
        self.save()
        return ref

    def exit(self, sig: Signal, price: float, when: datetime | None = None) -> dict[str, Any]:
        """Votre sortie sur Topstep, pour ce compte seulement : le signal du bot et sa simulation ne changent pas."""
        if sig.id not in {s.id for s, _, _ in self.included([sig])}:
            raise ValueError(f"{sig.asset_label} n'est pas dans le compte Topstep (/pris d'abord)")
        if not price or price <= 0:
            raise ValueError("prix de sortie invalide")
        row = {"price": float(price), "at": iso(when or utcnow())}
        self.state.setdefault("exits", {})[sig.id] = row
        self.save()
        return row

    def add_journal(self, asset: str, direction: str, entry: float, exit_: float, contracts: int,
                    opened_at: datetime, closed_at: datetime | None = None, note: str = "") -> dict[str, Any]:
        if asset not in PRODUCTS:
            raise ValueError(f"actif inconnu pour Topstep : {asset} ({', '.join(PRODUCTS)})")
        if direction not in ("long", "short"):
            raise ValueError("sens attendu : long ou short")
        if not 1 <= contracts <= RULES["max_micros"]:
            raise ValueError(f"nombre de micros entre 1 et {RULES['max_micros']}")
        row = {"id": "j" + opened_at.strftime("%m%d%H%M") + asset[:3], "asset": asset, "direction": direction,
               "entry": float(entry), "exit": float(exit_), "contracts": int(contracts),
               "opened_at": iso(opened_at), "closed_at": iso(closed_at or opened_at), "note": note[:120]}
        self.state.setdefault("journal", []).append(row)
        self.save()
        return row

    def set_risk(self, amount: float) -> None:
        if not 10 <= amount <= RULES["max_loss"]:
            raise ValueError("risque par trade entre 10 et 2 000 $")
        self.state["risk_per_trade"] = float(amount)
        self.save()

    def default_contracts(self, sig: Signal) -> int:
        """Micros pour risquer `risk_per_trade` au stop, entre 1 et 50."""
        _, mult = PRODUCTS[sig.asset]
        per_micro = abs(sig.entry - sig.stop_loss) * mult
        risk = float(self.state.get("risk_per_trade", DEFAULT_RISK))
        n = math.floor(risk / per_micro) if per_micro > 0 else 1
        return max(1, min(RULES["max_micros"], n))

    # ------------------------------------------------------------ compte calculé
    def included(self, signals: list[Signal]) -> list[tuple[Signal, int, str]]:
        """(signal, micros, origine) : vos trades manuels d'office, plus les signaux marqués « pris »."""
        taken = self.state.get("taken", {})
        removed = set(self.state.get("removed", []))
        out = []
        for s in signals:
            if s.id in removed or s.asset not in PRODUCTS or s.source == "shadow":
                continue
            if s.id in taken:
                out.append((s, int(taken[s.id]["contracts"]), "pris"))
            elif s.source in ("manual", "request"):
                out.append((s, self.default_contracts(s), "manuel"))
        return out

    def compute(self, signals: list[Signal], cfg: Config, now: datetime | None = None) -> dict[str, Any]:
        now = now or utcnow()
        rows, open_rows = [], []
        for s, n, origin in self.included(signals):
            symbol, mult = PRODUCTS[s.asset]
            asset = cfg.assets.get(s.asset)
            me = self.state.get("exits", {}).get(s.id) or (s.meta or {}).get("manual_exit")
            if me:
                exit_price, closed_at, status = me["price"], me["at"], "manual"
            elif s.status != "open" and s.close_price is not None:
                exit_price, closed_at, status = s.close_price, s.closed_at, s.status
            else:
                open_rows.append({"id": s.id, "asset": s.asset, "asset_label": s.asset_label, "symbol": symbol,
                                  "direction": s.direction, "entry": s.entry, "take_profit": s.take_profit,
                                  "stop_loss": s.stop_loss, "contracts": n, "multiplier": mult, "origin": origin,
                                  "opened_at": s.created_at, "expires_at": s.expires_at,
                                  "risk": round(abs(s.entry - s.stop_loss) * mult * n, 2),
                                  "notional": round(s.entry * mult * n, 2),
                                  "cost_pct": asset.cost_pct if asset else 0.0})
                continue
            rows.append(self._row(s.id, s.asset, s.asset_label, symbol, mult, s.direction, s.entry, exit_price, n,
                                  s.created_at, closed_at, status, origin, asset.cost_pct if asset else 0.0))
        for j in self.state.get("journal", []):
            symbol, mult = PRODUCTS[j["asset"]]
            asset = cfg.assets.get(j["asset"])
            label = asset.label if asset else j["asset"]
            rows.append(self._row(j["id"], j["asset"], label, symbol, mult, j["direction"], j["entry"], j["exit"],
                                  j["contracts"], j["opened_at"], j["closed_at"], "journal", "journal",
                                  asset.cost_pct if asset else 0.0))
        rows.sort(key=lambda r: r["closed_at"])
        data = self._apply_rules(rows, open_rows, now)
        data["candidates"] = self.candidates(signals, now)
        return data

    def candidates(self, signals: list[Signal], now: datetime, days: int = 3, limit: int = 15) -> list[dict[str, Any]]:
        """Signaux envoyés ces derniers jours, pas encore dans le compte : à marquer « pris » depuis le site."""
        inside = {s.id for s, _, _ in self.included(signals)}
        since = now - timedelta(days=days)
        out = []
        for s in sorted(signals, key=lambda x: x.created_at, reverse=True):
            if s.source == "shadow" or s.asset not in PRODUCTS or s.id in inside or parse_iso(s.created_at) < since:
                continue
            out.append({"id": s.id, "asset": s.asset, "asset_label": s.asset_label, "symbol": PRODUCTS[s.asset][0],
                        "direction": s.direction, "entry": s.entry, "take_profit": s.take_profit,
                        "stop_loss": s.stop_loss, "created_at": s.created_at, "status": s.status,
                        "pnl_pct": s.pnl_pct, "contracts": self.default_contracts(s)})
            if len(out) >= limit:
                break
        return out

    @staticmethod
    def _row(id_, asset, label, symbol, mult, direction, entry, exit_price, n, opened_at, closed_at, status, origin,
             cost_pct) -> dict[str, Any]:
        sign = 1.0 if direction == "long" else -1.0
        gross = sign * (exit_price - entry) * mult * n
        cost = cost_pct / 100.0 * entry * mult * n
        opened, closed = parse_iso(opened_at), parse_iso(closed_at)
        flat = _flat_limit(closed)
        late = opened < flat <= closed        # encore ouvert à 15:10 heure de Chicago
        return {"id": id_, "asset": asset, "asset_label": label, "symbol": symbol, "direction": direction,
                "entry": entry, "exit": exit_price, "contracts": n, "status": status, "origin": origin,
                "opened_at": opened_at, "closed_at": closed_at, "day": trading_day(closed).isoformat(),
                "pnl_gross": round(gross, 2), "cost": round(cost, 2), "pnl": round(gross - cost, 2),
                "past_flat_time": late}

    def _apply_rules(self, rows: list[dict[str, Any]], open_rows: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
        start = RULES["start_balance"]
        balance, mll, peak_eod = start, start - RULES["max_loss"], start
        failed = None
        days: dict[str, float] = {}
        violations: list[str] = []
        current_day = None
        for r in rows:
            if current_day is not None and r["day"] != current_day:
                # fin de journée : la perte maximale remonte avec le plus haut solde de clôture
                peak_eod = max(peak_eod, balance)
                mll = min(start, max(mll, peak_eod - RULES["max_loss"]))
            current_day = r["day"]
            balance = round(balance + r["pnl"], 2)
            days[r["day"]] = round(days.get(r["day"], 0.0) + r["pnl"], 2)
            r["balance_after"] = balance
            if failed is None and balance <= mll:
                failed = {"at": r["closed_at"], "balance": balance, "mll": mll}
            if r["past_flat_time"]:
                violations.append(f"{r['symbol']} du {_fmt_day(r['day'])} encore ouvert à 15:10 heure de Chicago : "
                                  "Topstep l'aurait fermé lui-même à 15:08")
        if current_day is not None and current_day != trading_day(now).isoformat():
            peak_eod = max(peak_eod, balance)
            mll = min(start, max(mll, peak_eod - RULES["max_loss"]))
        for d, pnl in days.items():
            if pnl <= -RULES["daily_loss"]:
                violations.append(f"journée du {_fmt_day(d)} : {pnl:+.0f} $, limite journalière de "
                                  f"{RULES['daily_loss']:.0f} $ atteinte")
        over = _max_concurrent(rows, open_rows)
        if over > RULES["max_micros"]:
            violations.append(f"jusqu'à {over} micros ouverts en même temps, pour {RULES['max_micros']} autorisés")

        profit = round(balance - start, 2)
        best_day = max(days.values()) if days else 0.0
        need = max(RULES["profit_target"], best_day / RULES["consistency"]) if best_day > 0 else RULES["profit_target"]
        today = trading_day(now).isoformat()
        today_pnl = days.get(today, 0.0)
        if failed:
            status = "échoué"
        elif profit >= need:
            status = "objectif atteint"
        else:
            status = "en cours"
        return {
            "updated_at": iso(now), "rules": RULES, "products": {k: v[0] for k, v in PRODUCTS.items()},
            "risk_per_trade": self.state.get("risk_per_trade", DEFAULT_RISK),
            "balance": balance, "profit": profit, "mll": round(mll, 2), "room_to_mll": round(balance - mll, 2),
            "peak_eod": round(peak_eod, 2), "target_balance": round(start + need, 2), "needed_profit": round(need, 2),
            "best_day": round(best_day, 2), "consistency_ok": profit <= 0 or best_day <= RULES["consistency"] * profit,
            "today": today, "today_pnl": round(today_pnl, 2), "room_today": round(RULES["daily_loss"] + today_pnl, 2),
            "status": status, "failed": failed, "violations": violations,
            "days": [{"day": d, "pnl": p} for d, p in sorted(days.items())],
            "trades": rows, "open": open_rows, "journal_count": len(self.state.get("journal", [])),
        }

    def publish(self, data: dict[str, Any]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2, ensure_ascii=False)
        (self.dir / "dashboard.json").write_text(text, encoding="utf-8")
        if self.docs is not None:
            self.docs.mkdir(parents=True, exist_ok=True)
            (self.docs / "account.json").write_text(text, encoding="utf-8")


def trading_day(t: datetime):
    """Journée de trading Topstep : de 17:00 à 17:00 heure de Chicago (le soir compte pour le lendemain)."""
    ct = t.astimezone(CHICAGO)
    return (ct + timedelta(days=1)).date() if ct.hour >= RULES["day_start_ct"] else ct.date()


def _flat_limit(t: datetime) -> datetime:
    """15:10 heure de Chicago de la journée de trading de `t`."""
    d = trading_day(t)
    h, m = RULES["flat_by_ct"]
    return datetime.combine(d, time(h, m), tzinfo=CHICAGO).astimezone(timezone.utc)


def _max_concurrent(rows: list[dict[str, Any]], open_rows: list[dict[str, Any]]) -> int:
    events = []
    for r in rows:
        events += [(parse_iso(r["opened_at"]), r["contracts"]), (parse_iso(r["closed_at"]), -r["contracts"])]
    for r in open_rows:
        events.append((parse_iso(r["opened_at"]), r["contracts"]))
    level = peak = 0
    for _, delta in sorted(events, key=lambda e: (e[0], e[1])):
        level += delta
        peak = max(peak, level)
    return peak


def _fmt_day(day: str) -> str:
    return f"{day[8:10]}/{day[5:7]}"


# ------------------------------------------------------------------ commandes texte
def parse_command(text: str) -> tuple[str, list[str]]:
    parts = text.strip().split()
    return (parts[0].lower() if parts else "", parts[1:])


def summary_text(d: dict[str, Any]) -> str:
    """Résumé Telegram (HTML) du compte simulé."""
    from .messages import money
    lines = [f"<b>🏁 TOPSTEP 50K (simulation)</b> · {d['status']}",
             f"Balance {money(d['balance'], '$')} · résultat {money(d['profit'], '$', sign=True)}",
             f"Objectif : {money(d['target_balance'], '$')} (encore {money(max(0.0, d['target_balance'] - d['balance']), '$')})",
             f"Perte maximale : {money(d['mll'], '$')}, marge {money(d['room_to_mll'], '$')}",
             f"Aujourd'hui {money(d['today_pnl'], '$', sign=True)} · limite journalière restante {money(d['room_today'], '$')}",
             f"Trades : {len(d['trades'])} clôturés, {len(d['open'])} ouverts · risque par trade {money(d['risk_per_trade'], '$', 0)}"]
    if d["violations"]:
        lines.append("⚠️ " + " · ".join(d["violations"][-3:]))
    lines.append("<i>/pris [actif] [micros] · /sortie [actif] [prix] · /retirer id · /journal · /topstep</i>")
    return "\n".join(lines)


JOURNAL_HELP = ("Journal d'un trade fait hors du bot : /journal <actif> <long|short> <entrée> <sortie> <micros> "
                "[AAAA-MM-JJTHH:MM ouverture, heure de Paris] — ex. /journal nasdaq short 30950 30910 3 2026-09-23T15:01")


def parse_journal(args: list[str], tz: str = "Europe/Paris") -> dict[str, Any]:
    if len(args) < 5:
        raise ValueError(JOURNAL_HELP)
    asset, direction = args[0].lower(), args[1].lower()
    direction = {"achat": "long", "vente": "short"}.get(direction, direction)
    num = lambda v: float(v.replace(",", "."))  # noqa: E731
    entry, exit_, contracts = num(args[2]), num(args[3]), int(args[4])
    when = utcnow()
    if len(args) > 5 and re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", args[5]):
        when = datetime.fromisoformat(args[5][:16]).replace(tzinfo=ZoneInfo(tz)).astimezone(timezone.utc)
    return {"asset": asset, "direction": direction, "entry": entry, "exit_": exit_, "contracts": contracts,
            "opened_at": when, "note": " ".join(args[6:])}
