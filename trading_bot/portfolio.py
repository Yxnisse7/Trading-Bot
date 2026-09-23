"""Simulation de compte : balance fictive, lots dimensionnés par le risque, résultat par trade.

Règles :
- la balance ne prend en compte que les trades ouverts APRÈS sa définition (aucune rétroactivité) ;
- taille de position par risque fixe : perte au stop = `risk_pct` % de la balance courante,
  plafonnée par le levier maximal de l'actif ; lots arrondis au pas de l'actif ;
- aucun trade n'est refusé : si la balance ne permet pas le lot minimal au risque demandé, le lot
  minimal est pris quand même et le trade est marqué « risqué » (risque effectif et levier affichés) ;
- au dénouement : P&L = sens × (sortie − entrée) × multiplicateur × lots − coûts estimés (cost_pct × notionnel) ;
- signaux fantômes exclus ; signaux du bot, manuels et propositions inclus.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from .config import AssetConfig, Config
from .models import Signal, iso, parse_iso, utcnow
from .storage import Store


def _floor_step(value: float, step: float) -> float:
    if step <= 0:
        return value
    n = math.floor(value / step + 1e-9)
    return round(n * step, 6)


def size_position(balance: float, risk_pct: float, asset: AssetConfig, entry: float, stop: float) -> dict[str, Any]:
    """Lots « optimaux » pour la balance : risque fixe au stop, plafond de levier, pas de lot."""
    stop_dist = abs(entry - stop)
    if balance <= 0 or stop_dist <= 0 or asset.lot_multiplier <= 0:
        return {"lots": 0.0, "reason": "paramètres invalides"}
    risk_amount = balance * risk_pct / 100.0
    loss_per_lot = stop_dist * asset.lot_multiplier
    lots = _floor_step(risk_amount / loss_per_lot, asset.lot_step)
    notional_per_lot = entry * asset.lot_multiplier
    max_lots = _floor_step(balance * asset.max_leverage / notional_per_lot, asset.lot_step)
    capped = False
    if lots > max_lots:
        lots = max_lots
        capped = True
    warnings: list[str] = []
    if lots < asset.lot_min:
        # Simulation : on prend toujours le trade, au lot minimal, en signalant le dépassement de risque.
        lots = asset.lot_min
        warnings.append(f"lot minimal {asset.lot_min:g} {asset.lot_label} imposé : risque au stop "
                        f"{lots * loss_per_lot:.2f} au lieu de {risk_amount:.2f} visé")
        if lots > max_lots:
            warnings.append(f"levier ×{lots * notional_per_lot / balance:.1f} au-delà du plafond ×{asset.max_leverage:g}")
    risk_eff = lots * loss_per_lot / balance * 100.0
    risky = bool(warnings)
    notional = lots * notional_per_lot
    return {
        "lots": lots, "lot_label": asset.lot_label, "risk_amount": round(lots * loss_per_lot, 2),
        "risk_pct_effective": round(risk_eff, 3),
        "notional": round(notional, 2), "leverage": round(notional / balance, 2), "capped_by_leverage": capped,
        "balance_at_open": round(balance, 2), "risky": risky, "warnings": warnings,
    }


class Portfolio:
    def __init__(self, store: Store, cfg: Config):
        self.store = store
        self.cfg = cfg
        self.data = store.portfolio()
        if not self.data:
            self.data = self._fresh(cfg.portfolio_default_balance, cfg.portfolio_risk_pct, utcnow(), default=True)
            self.save()

    # ---- état
    def _fresh(self, balance: float, risk_pct: float, when: datetime, default: bool = False) -> dict[str, Any]:
        return {
            "currency": self.cfg.portfolio_currency,
            "balance_initial": round(balance, 2), "balance": round(balance, 2), "peak": round(balance, 2),
            "risk_pct": risk_pct, "started_at": iso(when), "is_default": default,
            "open": {},        # id du signal → dimensionnement
            "history": [],     # trades clôturés appliqués à la balance
            "skipped": [],     # trades impossibles à dimensionner (paramètres invalides uniquement)
            "archives": [],    # simulations précédentes
            "updated_at": iso(when),
        }

    def save(self) -> None:
        self.data["updated_at"] = iso(utcnow())
        self.store.save_portfolio(self.data)

    def set_balance(self, balance: float, risk_pct: float | None = None, when: datetime | None = None) -> dict[str, Any]:
        """Nouvelle simulation : la balance ne prendra en compte que les trades ouverts à partir de maintenant."""
        if balance <= 0:
            raise ValueError("la balance doit être positive")
        when = when or utcnow()
        risk = risk_pct if risk_pct is not None else float(self.data.get("risk_pct", self.cfg.portfolio_risk_pct))
        if not 0.05 <= risk <= 10:
            raise ValueError("le risque par trade doit être entre 0,05 % et 10 %")
        old = self.data
        archives = list(old.get("archives", []))
        if old.get("history") or old.get("open"):
            archives.append({k: old[k] for k in ("balance_initial", "balance", "risk_pct", "started_at", "updated_at") if k in old}
                            | {"trades": len(old.get("history", []))})
        self.data = self._fresh(balance, risk, when)
        self.data["archives"] = archives[-10:]
        self.save()
        return self.data

    # ---- cycle de vie d'un trade
    def on_open(self, sig: Signal, asset: AssetConfig) -> dict[str, Any] | None:
        """Dimensionne un signal qui vient d'être émis (après `started_at`). Renvoie le dimensionnement."""
        if sig.source == "shadow":
            return None
        if parse_iso(sig.created_at) < parse_iso(self.data["started_at"]):
            return None
        sizing = size_position(float(self.data["balance"]), float(self.data["risk_pct"]), asset, sig.entry, sig.stop_loss)
        if sizing.get("lots", 0) <= 0:
            self.data.setdefault("skipped", []).append({"id": sig.id, "asset": sig.asset, "reason": sizing.get("reason"),
                                                        "at": sig.created_at})
            self.data["skipped"] = self.data["skipped"][-50:]
            self.save()
            return sizing
        self.data.setdefault("open", {})[sig.id] = {**sizing, "asset": sig.asset, "direction": sig.direction,
                                                    "entry": sig.entry, "stop_loss": sig.stop_loss,
                                                    "take_profit": sig.take_profit, "opened_at": sig.created_at}
        self.save()
        return sizing

    def on_close(self, sig: Signal, asset: AssetConfig) -> dict[str, Any] | None:
        """Applique le résultat d'un trade clôturé à la balance. Renvoie la ligne d'historique."""
        pos = self.data.get("open", {}).pop(sig.id, None)
        if pos is None or sig.close_price is None:
            return None
        sign = 1.0 if sig.direction == "long" else -1.0
        gross = sign * (sig.close_price - sig.entry) * asset.lot_multiplier * pos["lots"]
        cost = asset.cost_pct / 100.0 * pos["notional"]
        pnl = round(gross - cost, 2)
        balance = round(float(self.data["balance"]) + pnl, 2)
        self.data["balance"] = balance
        self.data["peak"] = max(float(self.data.get("peak", balance)), balance)
        row = {
            "id": sig.id, "asset": sig.asset, "asset_label": sig.asset_label, "direction": sig.direction,
            "horizon": sig.horizon or "1h", "source": sig.source, "status": sig.status,
            "entry": sig.entry, "exit": sig.close_price, "lots": pos["lots"], "lot_label": pos.get("lot_label", asset.lot_label),
            "risky": bool(pos.get("risky")), "risk_pct_effective": pos.get("risk_pct_effective"),
            "notional": pos["notional"], "risk_amount": pos["risk_amount"],
            "pnl_gross": round(gross, 2), "cost": round(cost, 2), "pnl": pnl,
            "pnl_pct_balance": round(pnl / pos["balance_at_open"] * 100.0, 3) if pos.get("balance_at_open") else None,
            "balance_after": balance, "opened_at": pos.get("opened_at", sig.created_at), "closed_at": sig.closed_at,
        }
        self.data.setdefault("history", []).append(row)
        self.save()
        return row

    # ---- synthèse
    def summary(self) -> dict[str, Any]:
        d = self.data
        hist = d.get("history", [])
        balance = float(d["balance"])
        initial = float(d["balance_initial"])
        peak = float(d.get("peak", initial))
        wins = [h for h in hist if h["pnl"] > 0]
        losses = [h for h in hist if h["pnl"] < 0]
        return {
            "currency": d.get("currency", self.cfg.portfolio_currency),
            "balance": balance, "balance_initial": initial, "risk_pct": d.get("risk_pct"),
            "started_at": d.get("started_at"), "is_default": d.get("is_default", False),
            "pnl": round(balance - initial, 2), "pnl_pct": round((balance - initial) / initial * 100.0, 2) if initial else 0.0,
            "peak": peak, "drawdown_pct": round((peak - balance) / peak * 100.0, 2) if peak else 0.0,
            "trades": len(hist), "wins": len(wins), "losses": len(losses),
            "avg_win": round(sum(h["pnl"] for h in wins) / len(wins), 2) if wins else 0.0,
            "avg_loss": round(sum(h["pnl"] for h in losses) / len(losses), 2) if losses else 0.0,
            "open_positions": len(d.get("open", {})),
            "skipped": len(d.get("skipped", [])),
            "risky": sum(1 for h in hist if h.get("risky")) + sum(1 for p in d.get("open", {}).values() if p.get("risky")),
        }

    def format_sizing(self, sizing: dict[str, Any] | None, asset: AssetConfig) -> str:
        from .messages import sizing_line, strip_html
        return strip_html(sizing_line(sizing, self.data.get("currency", self.cfg.portfolio_currency)))

    def format_outcome(self, row: dict[str, Any] | None) -> str:
        from .messages import money
        if not row:
            return ""
        cur = self.data.get("currency", self.cfg.portfolio_currency)
        flag = " ⚠️ trade risqué" if row.get("risky") else ""
        return (f"Simulation : {row['lots']:g} {row['lot_label']}{flag} · {money(row['pnl'], cur, sign=True)} "
                f"(brut {money(row['pnl_gross'], cur, sign=True)}, coûts {money(row['cost'], cur)}) · balance {money(row['balance_after'], cur)}")

    def format_summary(self, html: bool = False) -> str:
        from .messages import money, num, pct
        s = self.summary()
        cur = s["currency"]
        started = parse_iso(s["started_at"]).strftime("%d/%m/%Y") if s.get("started_at") else "-"
        title = "💼 SIMULATION DE COMPTE" + (" (balance par défaut, non définie)" if s["is_default"] else "")
        lines = [
            f"<b>{title}</b>" if html else title,
            f"Balance : {money(s['balance'], cur)} (départ {money(s['balance_initial'], cur)} le {started})",
            f"Résultat : {money(s['pnl'], cur, sign=True)}, soit {pct(s['pnl_pct'])} · plus haut {money(s['peak'], cur)} · "
            f"repli depuis le plus haut {num(s['drawdown_pct'], 1)} %",
            f"Trades : {s['trades']} ({s['wins']} gagnants, {s['losses']} perdants) · gain moyen {money(s['avg_win'], cur, sign=True)} · "
            f"perte moyenne {money(s['avg_loss'], cur, sign=True)}",
            f"Risque par trade : {num(s['risk_pct'], 1)} % · positions ouvertes : {s['open_positions']} · trades risqués : {s['risky']}",
        ]
        if s["risky"]:
            lines.append("⚠️ Trades risqués : avec cette balance, un seul micro-contrat dépasse souvent le levier maximal "
                         "ou le risque visé. Le trade est pris quand même et signalé ; seule une balance plus grande "
                         "les ferait disparaître.")
        return "\n".join(lines)
