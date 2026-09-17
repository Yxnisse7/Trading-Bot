"""Persistance JSON simple (fichiers versionnés dans data/ pour GitHub Actions)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import DATA_DIR
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
        return self.history() + self.open_signals()

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
