"""Configuration centrale du bot (valeurs par défaut + surcharge via config.json)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("TRADING_BOT_DATA_DIR", ROOT_DIR / "data"))
CONFIG_FILE = Path(os.environ.get("TRADING_BOT_CONFIG", ROOT_DIR / "config.json"))

DISCLAIMER = (
    "⚠️ Signaux générés automatiquement à partir de données publiques gratuites et "
    "d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie "
    "ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout "
    "passage en argent réel. Vous seul décidez et exécutez vos trades."
)


@dataclass
class AssetConfig:
    key: str                      # identifiant interne : nasdaq / bitcoin / gold
    label: str                    # libellé affiché
    yahoo_symbol: str             # symbole Yahoo Finance (NQ=F, BTC-USD, GC=F)
    binance_symbol: str | None = None
    price_decimals: int = 2
    tick_size: float = 0.01       # arrondi des niveaux
    min_hourly_range_pct: float = 0.05   # volatilité horaire minimale (%) pour trader
    max_hourly_range_pct: float = 3.0    # au-delà : volatilité anormale → pas de signal
    session_utc: tuple[int, int] | None = None  # plage horaire (heures UTC) où l'on scanne
    news_keywords: tuple[str, ...] = ()
    cost_pct: float = 0.0         # coût aller-retour estimé (spread + commissions), en % du prix


@dataclass
class Config:
    assets: dict[str, AssetConfig] = field(default_factory=dict)

    # ---- Politique de signaux ----
    max_signals_per_asset_per_day: int = 5
    max_losses_per_asset_per_day: int = 3   # après N stops sur un actif, plus de signal ce jour-là
    max_open_signals: int = 4               # positions simultanées maximum, tous actifs confondus
    cooldown_minutes: int = 30              # délai minimal entre deux signaux sur un même actif
    cooldown_after_loss_minutes: int = 60   # délai après un stop touché

    # ---- Signaux fantômes : setups rejetés pour confiance insuffisante, suivis en silence
    #      (jamais notifiés) pour nourrir l'apprentissage et les statistiques par critère
    shadow_enabled: bool = True
    shadow_min_criteria: int = 2
    shadow_max_per_asset_per_day: int = 12
    shadow_max_open_per_asset: int = 3
    learn_from_backtest: bool = True        # les trades de backtest alimentent aussi l'apprentissage
    signal_lifetime_minutes: int = 60       # durée de vie d'un signal (TP / SL sinon expiré)
    min_confidence: str = "moyen"           # moyen | fort
    min_score: float = 3.0                  # score pondéré minimal pour "moyen"
    strong_score: float = 5.0               # score pondéré à partir duquel "fort"
    min_criteria: int = 3                   # nombre minimal de critères alignés
    min_risk_reward: float = 1.2
    min_adx: float = 18.0                   # force de tendance minimale (ADX 15 min)
    # ---- Expérimental (désactivé par défaut ; aucun avantage démontré en backtest)
    max_extension: float | None = None      # distance max prix / EMA20 5 min, en ranges horaires
    contrarian: bool = False                # prendre le contre-pied de la direction détectée
    min_resolution_probability: float = 0.35  # P(TP ou SL touché sous 1 h) minimale (simulation sans dérive)

    # ---- Calibrage TP / SL sur la volatilité ----
    atr_period: int = 14
    tp_range_fraction: float = 0.60     # TP = fraction du range horaire moyen
    sl_range_fraction: float = 0.40     # SL = fraction du range horaire moyen
    min_sl_range_fraction: float = 0.25 # SL jamais plus serré que cette fraction (bruit)
    min_tp_range_fraction: float = 0.25 # en dessous : cible trop proche (bruit/spread)
    max_tp_range_fraction: float = 0.90 # au-dessus : cible irréaliste sous 1 h
    max_atr_ratio: float = 2.5          # ATR actuel / ATR moyen 24 h au-delà duquel on s'abstient
    min_tp_to_cost_ratio: float = 6.0   # la cible doit valoir au moins N fois le coût aller-retour

    # ---- Actualité ----
    news_lookback_minutes: int = 120
    news_blackout_before_minutes: int = 45   # avant une annonce macro majeure
    news_blackout_after_minutes: int = 30    # après
    max_news_risk_score: int = 3             # au-delà : marché jugé incertain

    # ---- Suivi ----
    track_interval_minutes: int = 5
    scan_interval_minutes: int = 15

    # ---- Apprentissage ----
    learning_min_trades: int = 10
    learning_weak_win_rate: float = 0.40
    learning_strong_win_rate: float = 0.60

    timezone: str = "Europe/Paris"
    log_level: str = "INFO"

    def asset(self, key: str) -> AssetConfig:
        return self.assets[key]


def default_assets() -> dict[str, AssetConfig]:
    return {
        "nasdaq": AssetConfig(
            key="nasdaq", label="Nasdaq 100 (NQ)", yahoo_symbol="NQ=F",
            price_decimals=2, tick_size=0.25,
            min_hourly_range_pct=0.08, max_hourly_range_pct=2.5,
            # Futures NQ : on évite la nuit/ouverture chaotique ; 13h-21h UTC = séance US + pré-ouverture
            session_utc=(12, 21),
            cost_pct=0.01,   # ≈ 1 tick de spread + commissions sur un micro-contrat
            news_keywords=("nasdaq", "wall street", "fed", "fomc", "inflation", "cpi",
                           "payrolls", "treasury", "yields", "tech stocks", "s&p"),
        ),
        "sp500": AssetConfig(
            key="sp500", label="S&P 500 (ES)", yahoo_symbol="ES=F",
            price_decimals=2, tick_size=0.25,
            min_hourly_range_pct=0.06, max_hourly_range_pct=2.0,
            session_utc=(12, 21),
            cost_pct=0.01,
            news_keywords=("s&p", "wall street", "stocks", "fed", "fomc", "inflation", "cpi",
                           "payrolls", "treasury", "yields", "earnings"),
        ),
        "bitcoin": AssetConfig(
            key="bitcoin", label="Bitcoin (BTC/USD)", yahoo_symbol="BTC-USD",
            binance_symbol="BTCUSDT", price_decimals=1, tick_size=1.0,
            min_hourly_range_pct=0.15, max_hourly_range_pct=4.0,
            session_utc=None,  # 24/7
            cost_pct=0.06,   # spread + frais taker typiques (0,03 % × 2)
            news_keywords=("bitcoin", "btc", "crypto", "etf", "sec", "binance", "coinbase",
                           "hack", "exploit", "stablecoin", "tether", "liquidation"),
        ),
        "ethereum": AssetConfig(
            key="ethereum", label="Ethereum (ETH/USD)", yahoo_symbol="ETH-USD",
            binance_symbol="ETHUSDT", price_decimals=2, tick_size=0.1,
            min_hourly_range_pct=0.2, max_hourly_range_pct=5.0,
            session_utc=None,
            cost_pct=0.08,
            news_keywords=("ethereum", "eth", "crypto", "etf", "sec", "binance", "coinbase",
                           "hack", "exploit", "stablecoin", "liquidation", "vitalik"),
        ),
        "gold": AssetConfig(
            key="gold", label="Or (XAU/USD)", yahoo_symbol="GC=F",
            price_decimals=2, tick_size=0.1,
            min_hourly_range_pct=0.05, max_hourly_range_pct=2.0,
            session_utc=(7, 20),  # Londres + New York
            cost_pct=0.02,   # spread CFD / futures typique
            news_keywords=("gold", "xau", "dollar", "dxy", "fed", "fomc", "treasury",
                           "yields", "inflation", "cpi", "geopolit", "central bank"),
        ),
    }


def _apply_overrides(cfg: Config, data: dict[str, Any]) -> Config:
    for key, value in data.items():
        if key == "assets" and isinstance(value, dict):
            for akey, aval in value.items():
                if akey in cfg.assets and isinstance(aval, dict):
                    for f, v in aval.items():
                        if hasattr(cfg.assets[akey], f):
                            if f == "session_utc" and v is not None:
                                v = tuple(v)
                            if f == "news_keywords":
                                v = tuple(v)
                            setattr(cfg.assets[akey], f, v)
        elif hasattr(cfg, key):
            setattr(cfg, key, value)
    return cfg


def load_config(path: Path | None = None) -> Config:
    cfg = Config(assets=default_assets())
    path = path or CONFIG_FILE
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            _apply_overrides(cfg, json.load(fh))
    return cfg
