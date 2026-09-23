"""Mode halal (avis malikite) : un second bot, entièrement séparé du bot principal.

Règles appliquées (voir README, section « Mode halal ») :
  - achat seulement : aucune vente à découvert (vendre ce qu'on ne possède pas est interdit) ;
  - au comptant, sans levier : la simulation n'engage jamais plus que les liquidités disponibles ;
  - actifs au comptant uniquement : ETF islamiques (sociétés filtrées charia), or physique certifié,
    Bitcoin et Ethereum au comptant (avis divergents : à voir avec un savant). Aucun contrat à terme,
    aucun CFD, aucune option ;
  - trades plus longs (bougie de base 1 h, horizon ~12 h) : sans levier, un scalp ne couvre pas les frais ;
  - frais réels : écart acheteur-vendeur et frais de courtage (1 € l'ordre pour les ETF).

Séparation avec le bot principal : dossier de données propre (data/halal : signaux, historique,
apprentissage, simulation, état, numéros de messages), copie publiée propre (docs/halal), page du
site propre (halal.html), messages Telegram marqués 🌙. Il ne lit jamais les commandes Telegram (le bot
principal s'en charge) et n'écrit rien dans data/ ni dans docs/ en dehors de ses dossiers.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from . import messages as msg
from .config import DATA_DIR, ROOT_DIR, AssetConfig, Config, _apply_overrides
from .engine import Engine
from .models import Signal, iso, parse_iso, utcnow
from .notify import notify
from .storage import Store
from .summary import daily_summary

log = logging.getLogger(__name__)

HALAL_CONFIG_FILE = ROOT_DIR / "config.halal.json"
PAGE = "halal.html"
TAG = "🌙"

KEYWORDS_US = ("wall street", "stocks", "s&p", "nasdaq", "fed", "fomc", "inflation", "cpi", "payrolls",
               "treasury", "yields", "earnings", "recession")


def halal_assets() -> dict[str, AssetConfig]:
    """Actifs au comptant. Les seuils de volatilité portent sur le range moyen d'une fenêtre de 12 h."""
    common_etf = dict(price_decimals=2, tick_size=0.01, session_utc=(7, 15),  # Bourse de Londres, 8 h-16 h 30 heure de Londres
                      lot_label="parts", lot_multiplier=1.0, lot_step=1, lot_min=1, max_leverage=1.0,
                      fee_per_order=1.0)                                      # courtier à 1 € l'ordre
    return {
        "bitcoin": AssetConfig(
            key="bitcoin", label="Bitcoin (BTC)", yahoo_symbol="BTC-USD", binance_symbol="BTCUSDT",
            price_decimals=1, tick_size=1.0, min_hourly_range_pct=0.8, max_hourly_range_pct=12.0,
            cost_pct=0.25,     # frais de plateforme au comptant (~0,1 % par ordre) + écart acheteur-vendeur
            lot_label="BTC", lot_multiplier=1.0, lot_step=0.0001, lot_min=0.0001, max_leverage=1.0,
            news_keywords=("bitcoin", "btc", "crypto", "etf", "sec", "binance", "coinbase",
                           "hack", "exploit", "stablecoin", "tether", "liquidation"),
        ),
        "ethereum": AssetConfig(
            key="ethereum", label="Ethereum (ETH)", yahoo_symbol="ETH-USD", binance_symbol="ETHUSDT",
            price_decimals=2, tick_size=0.1, min_hourly_range_pct=1.0, max_hourly_range_pct=15.0,
            cost_pct=0.25, lot_label="ETH", lot_multiplier=1.0, lot_step=0.001, lot_min=0.001, max_leverage=1.0,
            news_keywords=("ethereum", "eth", "crypto", "etf", "sec", "binance", "coinbase",
                           "hack", "exploit", "stablecoin", "liquidation", "vitalik"),
        ),
        "usa_islamique": AssetConfig(
            key="usa_islamique", label="ETF USA islamique (ISDU)", yahoo_symbol="ISDU.L",
            min_hourly_range_pct=0.3, max_hourly_range_pct=4.0, cost_pct=0.10,
            news_keywords=KEYWORDS_US, **common_etf,
        ),
        "monde_islamique": AssetConfig(
            key="monde_islamique", label="ETF Monde islamique (ISDW)", yahoo_symbol="ISDW.L",
            min_hourly_range_pct=0.3, max_hourly_range_pct=4.0, cost_pct=0.12,
            news_keywords=KEYWORDS_US + ("europe", "ecb", "china", "japan"), **common_etf,
        ),
        "or_physique": AssetConfig(
            key="or_physique", label="Or physique Royal Mint (RMAU)", yahoo_symbol="RMAU.L",
            min_hourly_range_pct=0.3, max_hourly_range_pct=4.0, cost_pct=0.15,
            news_keywords=("gold", "xau", "dollar", "dxy", "fed", "fomc", "treasury", "yields",
                           "inflation", "cpi", "geopolit", "central bank"), **common_etf,
        ),
    }


def halal_config(path: Path | None = None) -> Config:
    cfg = Config(assets=halal_assets())
    cfg.long_only = True
    cfg.cash_only = True
    cfg.scan_bases = [60]                   # bougie 1 h → horizon ~12 h
    cfg.scan_days = 30                      # 1 h × 30 jours : assez d'historique pour les tendances
    cfg.scan_interval_minutes = 15          # sur une bougie 1 h, analyser toutes les 15 min suffit
    cfg.min_confidence = "moyen"
    cfg.min_tp_to_cost_ratio = 4.0
    cfg.max_open_signals = 4
    cfg.max_long_signals_per_asset_per_day = 2
    cfg.max_losses_per_asset_per_day = 2
    cfg.cooldown_minutes = 120
    cfg.cooldown_after_loss_minutes = 360
    cfg.same_direction_after_loss_minutes = 720
    cfg.correlation_enabled = False         # contexte des marchés meneurs calibré pour le scalping
    cfg.shadow_enabled = False              # pas de fantômes ni de variantes : il apprend de ses seuls trades
    cfg.variants_enabled = False
    cfg.learn_from_backtest = True
    cfg.long_horizon_enabled = False
    cfg.portfolio_default_balance = 1000.0
    cfg.portfolio_risk_pct = 1.0
    path = path or HALAL_CONFIG_FILE
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            _apply_overrides(cfg, json.load(fh))
    return cfg


def halal_data_dir() -> Path:
    """data/halal, jamais le dossier du bot principal (TRADING_BOT_DATA_DIR peut déjà le désigner)."""
    base = Path(DATA_DIR)
    return base if base.name == "halal" else base / "halal"


def halal_store(data_dir: Path | None = None) -> Store:
    d = Path(data_dir or halal_data_dir())
    docs = ROOT_DIR / "docs" / "halal" if d.resolve() == (ROOT_DIR / "data" / "halal").resolve() else None
    return Store(d, docs_dir=docs)


def page_buttons(site_url: str | None, asset_key: str | None = None) -> list[list[tuple[str, str]]]:
    if not site_url:
        return []
    base = site_url.rstrip("/") + "/" + PAGE
    return [[("📈 Graphique", base + (f"?actif={asset_key}" if asset_key else "") + "#live"),
             ("🌙 Mode halal", base)]]


class HalalEngine(Engine):
    LIVE_CANDLES = 864          # 3 jours de bougies 5 min : vues 15 min et 1 h exploitables sur un swing
    LIVE_DAYS = 5

    def __init__(self, cfg: Config | None = None, store: Store | None = None):
        store = store or halal_store()
        # garde-fou, avant toute écriture : jamais dans le dossier de données du bot principal
        if store.dir.resolve() == (ROOT_DIR / "data").resolve():
            raise RuntimeError("le mode halal ne doit pas écrire dans data/ : utilisez data/halal")
        super().__init__(cfg or halal_config(), store)

    # ------------------------------------------------------------ messages
    def _notify_signal(self, sig: Signal, sizing: dict[str, Any] | None, header: str | None = None,
                       footer: str | None = None, now: datetime | None = None) -> str:
        head = f"{TAG} <b>HALAL</b> · au comptant, sans levier" + (f"\n{header}" if header else "")
        text = self._signal_text(sig, sizing, header=head, now=now)
        text += "\n<i>Achat réel uniquement, payé comptant ; sortie au TP, au SL ou à l'expiration.</i>"
        if footer:
            text += "\n\n" + footer
        notify(text, html=True, key=sig.id, buttons=page_buttons(self.cfg.site_url, sig.asset))
        return text

    def _notify_outcome(self, sig: Signal, row: dict[str, Any] | None) -> None:
        cur = self.portfolio.data.get("currency", self.cfg.portfolio_currency)
        visible = sorted((s for s in self.store.history() if s.source != "shadow" and s.closed_at),
                         key=lambda s: s.closed_at)
        text = msg.outcome_text(sig, row, cur, streak=msg.streak_text(visible), digits=self._digits(sig.asset),
                                initial=float(self.portfolio.data.get("balance_initial") or 0) or None)
        notify(f"{TAG} <b>HALAL</b>\n" + text, html=True, reply_to=sig.id)

    # ------------------------------------------------------------ passage
    def tick(self, now: datetime | None = None) -> dict[str, Any]:
        """Suivi, instantané du graphique puis analyse. Aucune lecture des commandes Telegram :
        le bot principal les traite, et un second lecteur lui volerait des messages."""
        now = now or utcnow()
        closed = self.track(now)
        st = self.store.state()
        st["last_tick"] = iso(now)          # l'analyse n'a lieu que toutes les 15 min : état du bot pour le site
        self.store.save_state(st)
        try:
            self.write_live_snapshot(now)
        except Exception:  # noqa: BLE001 — le graphique ne doit jamais casser un passage
            log.exception("instantané live (halal)")
        st = self.store.state()
        last_scan = parse_iso(st["last_scan"]) if st.get("last_scan") else None
        new: list[Signal] = []
        if last_scan is None or now - last_scan >= timedelta(minutes=self.cfg.scan_interval_minutes - 1):
            new = self.scan(now)
        else:
            self.write_report()             # état publié (dernier passage) à jour sur la page du site
        return {"closed": [s.id for s in closed], "new": [s.id for s in new]}

    def process_commands(self, now: datetime | None = None) -> int:
        return 0

    def welcome_new_chats(self) -> list[str]:
        return []

    def manual(self, *args, **kwargs):
        raise RuntimeError("le mode halal n'accepte pas de trade manuel")

    def propose(self, *args, **kwargs):
        raise RuntimeError("le mode halal n'accepte pas de proposition à la demande")

    # ------------------------------------------------------------ résumé
    def summary(self, day=None, send: bool = True, force: bool = False) -> str:
        day = day or self.summary_day()
        st = self.store.state()
        if send and not force and st.get("last_summary_day") == day.isoformat():
            log.info("résumé halal du %s déjà envoyé : rien à renvoyer", day)
            return ""
        adj = self._relearn()
        text = daily_summary(self.store.all_signals(), self.cfg, day, adj)
        text = text.replace("📊 RÉSUMÉ QUOTIDIEN", f"{TAG} RÉSUMÉ HALAL", 1)
        text = "\n".join(line for line in text.splitlines() if "en ombre" not in line)
        port = self.portfolio.format_summary(html=True).replace("SIMULATION DE COMPTE", "SIMULATION HALAL (comptant, sans levier)", 1)
        text += "\n\n" + port
        text += ("\n\n<b>Rappel</b> : achat seulement, sans levier, actifs au comptant. Purifiez les intérêts "
                 "éventuels versés par le courtier sur les espèces, et la part non conforme des dividendes.")
        if send:
            notify(text, html=True, silent=True, buttons=page_buttons(self.cfg.site_url))
        self.write_report()
        st = self.store.state()
        st["last_summary"] = iso(utcnow())
        if send:
            st["last_summary_day"] = day.isoformat()
        self.store.save_state(st)
        return text


def use_halal_notify_dir() -> None:
    """Journal et numéros des messages du mode halal dans data/halal (lancement local sans variable d'environnement)."""
    os.environ.setdefault("TRADING_BOT_NOTIFY_DIR", str(halal_data_dir()))
