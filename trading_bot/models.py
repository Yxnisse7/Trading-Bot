"""Structures de données : bougies, signaux, issues."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Candle:
    ts: int          # timestamp epoch (secondes, UTC) d'ouverture de la bougie
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @property
    def range(self) -> float:
        return self.high - self.low


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass
class Signal:
    id: str
    asset: str
    asset_label: str
    direction: str            # "long" | "short"
    entry: float
    take_profit: float
    stop_loss: float
    risk_reward: float
    confidence: str           # "moyen" | "fort"
    score: float
    criteria: list[str]       # critères techniques alignés (pour l'apprentissage)
    rationale: str            # justification courte (technique + actualité)
    news_context: str
    created_at: str           # ISO UTC
    expires_at: str           # ISO UTC
    status: str = "open"      # open | tp | sl | expired
    closed_at: str | None = None
    close_price: float | None = None
    pnl_pct: float | None = None
    duration_minutes: int | None = None
    hourly_range: float | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Signal":
        return cls(**d)

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    def risk_distance(self) -> float:
        return abs(self.entry - self.stop_loss)

    def reward_distance(self) -> float:
        return abs(self.take_profit - self.entry)
