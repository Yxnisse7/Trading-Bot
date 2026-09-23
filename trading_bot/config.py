"""Configuration centrale du bot (valeurs par défaut + surcharge via config.json)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path | None = None) -> None:
    """Charge un fichier .env (clé=valeur) sans écraser les variables déjà définies."""
    path = path or ROOT_DIR / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()

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
    long_horizon: bool = True     # analyser aussi l'horizon ~3 h sur cet actif
    # ---- simulation de compte : 1 lot = `lot_multiplier` unités de compte par point de prix
    lot_label: str = "lot"
    lot_multiplier: float = 1.0   # MNQ 2 $/pt, MES 5 $/pt, MGC 10 $/pt, BTC 1 $/$, ETH 1 $/$
    lot_step: float = 1.0         # granularité des lots (0,001 BTC, 0,01 ETH, 1 contrat micro)
    lot_min: float = 1.0
    max_leverage: float = 10.0    # notionnel maximal = balance × levier
    # Nouvel actif à l'essai : ses signaux sont suivis en silence (fantômes) et ne deviennent réels
    # qu'une fois la variante « essai_<actif> » promue, comme les autres variantes.
    trial: bool = False


@dataclass
class Config:
    assets: dict[str, AssetConfig] = field(default_factory=dict)

    # ---- Politique de signaux ----
    max_signals_per_asset_per_day: int = 5
    max_losses_per_asset_per_day: int = 3   # après N stops sur un actif, plus de signal ce jour-là
    max_open_signals: int = 4               # positions simultanées maximum, tous actifs confondus
    cooldown_minutes: int = 30              # délai minimal entre deux signaux sur un même actif
    cooldown_after_loss_minutes: int = 60   # délai après un stop touché (compté depuis la clôture, tous horizons)
    same_direction_after_loss_minutes: int = 120  # après un stop, pas de nouveau signal dans le MÊME sens sur l'actif

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
    # ---- Moments de marché
    activity_filter: bool = True            # ignore les heures creuses (profil d'activité automatique)
    min_activity_ratio: float = 0.6         # heure < 60 % de l'activité moyenne → pas de signal court
    us_open_utc: tuple[int, int] = (13, 30) # ouverture cash US (13:30 UTC en heure d'été, 14:30 en hiver)
    orb_minutes: int = 30                   # durée du range d'ouverture
    orb_window_minutes: int = 120           # fenêtre après le range d'ouverture où la cassure compte

    # ---- Corrélations (veto + confirmation légère, jamais un signal en soi)
    correlation_enabled: bool = True
    vix_veto_pct: float = 4.0               # VIX +4 % en 15 min → pas de long indices
    dxy_veto_pct: float = 0.25              # DXY +0,25 % en 1 h → pas de long or
    tnx_veto_pct: float = 2.0               # rendement 10 ans +2 % en 1 h → pas de long Nasdaq / or

    # ---- Second horizon (intraday plus long, base 15 min → ~3 h)
    long_horizon_enabled: bool = True
    long_horizon_base_minutes: int = 15
    max_long_signals_per_asset_per_day: int = 2

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
    post_event_caution_hours: int = 24       # après FOMC / CPI / emploi : +1 critère exigé, horizon 3 h suspendu

    # ---- Suivi ----
    track_interval_minutes: int = 5
    scan_interval_minutes: int = 5          # recherche de signaux à chaque passage (jusqu'à 10 min gagnées)

    # ---- Apprentissage ----
    # Recalcul complet à chaque passage, à partir de TOUS les trades clôturés, sans mémoire des
    # poids précédents : les mêmes trades donnent toujours les mêmes poids.
    learning_min_trades: int = 30           # trades équivalents minimum avant de bouger un poids
    learning_z: float = 1.96                # marge de sécurité : écart prouvé à 95 %
    learning_gain: float = 2.5              # +0,2 R d'avantage prouvé → poids ×1,5 (plafonné)
    learning_source_weights: dict[str, float] = field(default_factory=lambda: {
        "bot": 1.0, "manual": 1.0, "request": 1.0,   # trades réels : la référence
        "shadow": 0.6,                                # temps réel, mais setups non envoyés
        "backtest": 0.25,                             # passé rejoué : utile, mais figé
    })
    learning_asset_min_trades: int = 30     # correction par actif seulement au-delà
    learning_hours_z: float = 2.5           # 24 tranches testées : marge plus large

    # ---- Variantes testées en fantôme (jamais notifiées tant qu'elles ne sont pas promues)
    # Promotion automatique si, sur au moins `variant_min_trades` trades, la variante fait au moins
    # aussi bien (gain net moyen) que les signaux réels du bot.
    variants_enabled: bool = True
    variant_extended_sessions: dict[str, tuple[int, int]] = field(default_factory=lambda: {
        "nasdaq": (7, 13), "sp500": (7, 13),          # indices : matinée européenne (UTC)
    })
    variant_min_trades: int = 100
    variant_baseline_min_trades: int = 30

    # ---- Simulation de compte (paper trading chiffré)
    portfolio_default_balance: float = 1000.0
    portfolio_risk_pct: float = 1.0         # risque par trade, en % de la balance courante
    portfolio_currency: str = "$"           # simple libellé : les prix sont en dollars, aucune conversion

    timezone: str = "Europe/Paris"
    # adresse du site (boutons « Graphique » et « Simulation » sous les messages Telegram ; vide = pas de boutons)
    site_url: str = "https://yxnisse7.github.io/Trading-Bot/"
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
            lot_label="MNQ", lot_multiplier=2.0, lot_step=1, lot_min=1, max_leverage=20,
            news_keywords=("nasdaq", "wall street", "fed", "fomc", "inflation", "cpi",
                           "payrolls", "treasury", "yields", "tech stocks", "s&p"),
        ),
        "sp500": AssetConfig(
            key="sp500", label="S&P 500 (ES)", yahoo_symbol="ES=F",
            price_decimals=2, tick_size=0.25,
            min_hourly_range_pct=0.06, max_hourly_range_pct=2.0,
            session_utc=(12, 21),
            cost_pct=0.01,
            lot_label="MES", lot_multiplier=5.0, lot_step=1, lot_min=1, max_leverage=20,
            news_keywords=("s&p", "wall street", "stocks", "fed", "fomc", "inflation", "cpi",
                           "payrolls", "treasury", "yields", "earnings"),
        ),
        "bitcoin": AssetConfig(
            key="bitcoin", label="Bitcoin (BTC/USD)", yahoo_symbol="BTC-USD",
            binance_symbol="BTCUSDT", price_decimals=1, tick_size=1.0,
            min_hourly_range_pct=0.15, max_hourly_range_pct=4.0,
            session_utc=None,  # 24/7
            cost_pct=0.06,   # spread + frais taker typiques (0,03 % × 2)
            long_horizon=False,  # backtest 60 j : horizon 3 h nettement perdant sur les cryptos
            lot_label="BTC", lot_multiplier=1.0, lot_step=0.001, lot_min=0.001, max_leverage=3,
            news_keywords=("bitcoin", "btc", "crypto", "etf", "sec", "binance", "coinbase",
                           "hack", "exploit", "stablecoin", "tether", "liquidation"),
        ),
        "ethereum": AssetConfig(
            key="ethereum", label="Ethereum (ETH/USD)", yahoo_symbol="ETH-USD",
            binance_symbol="ETHUSDT", price_decimals=2, tick_size=0.1,
            min_hourly_range_pct=0.2, max_hourly_range_pct=5.0,
            session_utc=None,
            cost_pct=0.08,
            long_horizon=False,  # idem
            lot_label="ETH", lot_multiplier=1.0, lot_step=0.01, lot_min=0.01, max_leverage=3,
            news_keywords=("ethereum", "eth", "crypto", "etf", "sec", "binance", "coinbase",
                           "hack", "exploit", "stablecoin", "liquidation", "vitalik"),
        ),
        "gold": AssetConfig(
            key="gold", label="Or (XAU/USD)", yahoo_symbol="GC=F",
            price_decimals=2, tick_size=0.1,
            min_hourly_range_pct=0.05, max_hourly_range_pct=2.0,
            session_utc=(7, 20),  # Londres + New York
            cost_pct=0.02,   # spread CFD / futures typique
            lot_label="MGC", lot_multiplier=10.0, lot_step=1, lot_min=1, max_leverage=20,
            news_keywords=("gold", "xau", "dollar", "dxy", "fed", "fomc", "treasury",
                           "yields", "inflation", "cpi", "geopolit", "central bank"),
        ),
        # ---- Nouveaux actifs, à l'essai : moteurs propres, peu liés aux indices et aux cryptos
        "oil": AssetConfig(
            key="oil", label="Pétrole WTI (CL)", yahoo_symbol="CL=F",
            price_decimals=2, tick_size=0.01,
            min_hourly_range_pct=0.10, max_hourly_range_pct=2.5,
            session_utc=(7, 20),  # Londres + New York (NYMEX)
            cost_pct=0.03,        # micro-contrat MCL : ≈ 1 tick de spread + commissions
            lot_label="MCL", lot_multiplier=100.0, lot_step=1, lot_min=1, max_leverage=20,  # 100 barils
            trial=True,
            news_keywords=("oil", "crude", "wti", "brent", "opec", "barrel", "eia", "inventor",
                           "saudi", "pipeline", "refinery", "hormuz"),
        ),
        "euro": AssetConfig(
            key="euro", label="Euro / dollar (6E)", yahoo_symbol="6E=F",  # contrat à terme : volume réel
            price_decimals=5, tick_size=0.00005,
            min_hourly_range_pct=0.03, max_hourly_range_pct=0.6,
            session_utc=(6, 17),  # Londres + chevauchement New York
            cost_pct=0.01,        # micro-contrat M6E : ≈ 1 tick de spread + commissions
            lot_label="M6E", lot_multiplier=12500.0, lot_step=1, lot_min=1, max_leverage=20,  # 12 500 €
            trial=True,
            news_keywords=("euro", "eur/usd", "eurusd", "ecb", "lagarde", "eurozone", "euro area",
                           "germany", "bund", "dollar", "fed", "fomc"),
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
