"""Persistance JSON simple (fichiers versionnés dans data/ pour GitHub Actions)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import DATA_DIR, ROOT_DIR
from .models import Signal


class Store:
    def __init__(self, data_dir: Path | None = None):
        self.dir = Path(data_dir or DATA_DIR)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.signals_file = self.dir / "signals.json"        # signaux ouverts
        self.history_file = self.dir / "history.json"        # signaux clôturés
        self.state_file = self.dir / "state.json"            # méta (dernier scan, etc.)
        self.adjust_file = self.dir / "adjustments.json"     # poids appris
        self.calendar_file = self.dir / "macro_calendar.json"
        self.backtest_file = self.dir / "backtests.json"      # derniers résultats de backtest
        self.backtest_trades_file = self.dir / "backtest_trades.json"  # trades de backtest (apprentissage)
        self.report_file = self.dir / "REPORT.md"             # rapport lisible sur GitHub
        self.shadow_file = self.dir / "shadow.json"           # signaux fantômes ouverts
        self.calendar_cache_file = self.dir / "calendar_cache.json"  # calendrier économique (ForexFactory)
        self.portfolio_file = self.dir / "portfolio.json"     # simulation de compte
        self.dashboard_file = self.dir / "dashboard.json"     # données de l'interface

    # ---- helpers
    def _read(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default

    def _write(self, path: Path, data: Any) -> None:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)

    # ---- signaux ouverts
    def open_signals(self) -> list[Signal]:
        return [Signal.from_dict(d) for d in self._read(self.signals_file, [])]

    def save_open(self, signals: list[Signal]) -> None:
        self._write(self.signals_file, [s.to_dict() for s in signals])

    def add_signal(self, sig: Signal) -> None:
        sigs = self.open_signals()
        sigs.append(sig)
        self.save_open(sigs)

    # ---- historique
    def history(self) -> list[Signal]:
        return [Signal.from_dict(d) for d in self._read(self.history_file, [])]

    def append_history(self, sig: Signal) -> None:
        hist = self._read(self.history_file, [])
        hist.append(sig.to_dict())
        self._write(self.history_file, hist)

    def all_signals(self) -> list[Signal]:
        """Historique + signaux ouverts (fantômes inclus, distingués par `source`)."""
        return self.history() + self.open_signals() + self.open_shadow()

    # ---- signaux fantômes ouverts
    def open_shadow(self) -> list[Signal]:
        return [Signal.from_dict(d) for d in self._read(self.shadow_file, [])]

    def save_shadow(self, signals: list[Signal]) -> None:
        self._write(self.shadow_file, [s.to_dict() for s in signals])

    def add_shadow(self, sig: Signal) -> None:
        sigs = self.open_shadow()
        sigs.append(sig)
        self.save_shadow(sigs)

    # ---- état
    def state(self) -> dict[str, Any]:
        return self._read(self.state_file, {})

    def save_state(self, state: dict[str, Any]) -> None:
        self._write(self.state_file, state)

    # ---- ajustements
    def adjustments(self) -> dict[str, Any]:
        return self._read(self.adjust_file, {"weights": {}, "notes": []})

    def save_adjustments(self, adj: dict[str, Any]) -> None:
        self._write(self.adjust_file, adj)

    # ---- calendrier macro
    def calendar(self) -> list[dict]:
        return self._read(self.calendar_file, {"events": []}).get("events", [])

    # ---- backtests (sans la liste détaillée des trades, trop volumineuse)
    def backtests(self) -> dict[str, Any]:
        return self._read(self.backtest_file, {})

    def save_backtests(self, results: dict[str, Any]) -> None:
        slim = {k: {kk: vv for kk, vv in v.items() if kk != "trades"} for k, v in results.items()}
        self._write(self.backtest_file, slim)
        trades = self._read(self.backtest_trades_file, {})
        for k, v in results.items():
            trades[k] = [{f: t.get(f) for f in ("id", "asset", "direction", "entry", "take_profit", "stop_loss",
                                                  "confidence", "criteria", "created_at", "status", "pnl_pct",
                                                  "pnl_gross_pct", "duration_minutes", "news_context")}
                         | {"source": "backtest", "asset_label": v.get("asset_label", k), "expires_at": t.get("expires_at"),
                            "risk_reward": t.get("risk_reward"), "score": t.get("score"), "rationale": ""}
                         for t in v.get("trades", [])]
        self._write(self.backtest_trades_file, trades)

    def backtest_trades(self) -> list[Signal]:
        out = []
        for rows in self._read(self.backtest_trades_file, {}).values():
            for d in rows:
                try:
                    out.append(Signal.from_dict(d))
                except TypeError:
                    continue
        return out

    # ---- simulation de compte
    def portfolio(self) -> dict[str, Any]:
        return self._read(self.portfolio_file, {})

    def _docs_dir(self) -> Path | None:
        """Dossier docs/ à alimenter (GitHub Pages) — uniquement pour le dossier de données du projet."""
        docs = ROOT_DIR / "docs"
        if docs.is_dir() and self.dir.resolve() == (ROOT_DIR / "data").resolve():
            return docs
        return None

    def save_portfolio(self, data: dict[str, Any]) -> None:
        self._write(self.portfolio_file, data)
        docs = self._docs_dir()
        if docs is not None:
            try:
                self._write(docs / "portfolio.json", data)
            except OSError:
                pass

    # ---- interface
    def save_dashboard(self, data: dict[str, Any]) -> None:
        self._write(self.dashboard_file, data)
        # copie à côté de docs/index.html pour GitHub Pages (dossier /docs)
        docs = self._docs_dir()
        if docs is not None:
            try:
                self._write(docs / "dashboard.json", data)
            except OSError:
                pass

    # ---- instantané « live » d'un actif (bougies récentes pour le graphique du site)
    def save_live(self, asset_key: str, data: dict[str, Any]) -> None:
        live = self.dir / "live"
        live.mkdir(parents=True, exist_ok=True)
        self._write(live / f"{asset_key}.json", data)
        docs = self._docs_dir()
        if docs is not None:
            try:
                (docs / "live").mkdir(parents=True, exist_ok=True)
                self._write(docs / "live" / f"{asset_key}.json", data)
            except OSError:
                pass

    # ---- rapport
    def save_report(self, text: str) -> None:
        self.report_file.write_text(text, encoding="utf-8")

    # ---- bougies hors ligne (data/candles/<actif>_5m.json, format compact [ts,o,h,l,c,v])
    def candles_file(self, asset_key: str) -> Path:
        return self.dir / "candles" / f"{asset_key}_5m.json"

    def save_candles(self, asset_key: str, candles: list) -> None:
        path = self.candles_file(asset_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [[c.ts, c.open, c.high, c.low, c.close, c.volume] for c in candles]
        path.write_text(json.dumps(rows, separators=(",", ":")), encoding="utf-8")

    def load_candles(self, asset_key: str) -> list:
        from .models import Candle

        rows = self._read(self.candles_file(asset_key), [])
        return [Candle(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])) for r in rows]
