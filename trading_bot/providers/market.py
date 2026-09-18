"""Routage par actif avec repli automatique entre fournisseurs gratuits.

Crypto : Binance (hôte principal puis miroirs) → Coinbase → Kraken → Yahoo (sans volume fiable).
Indices / or : Yahoo Finance.
"""
from __future__ import annotations

import logging

from ..config import AssetConfig
from ..models import Candle
from . import binance, coinbase, coingecko, kraken, yahoo
from .http import ProviderError

log = logging.getLogger(__name__)

# Symboles Coinbase / Kraken par actif crypto
COINBASE_PRODUCTS = {"bitcoin": "BTC-USD", "ethereum": "ETH-USD"}
KRAKEN_PAIRS = {"bitcoin": "XBTUSD", "ethereum": "ETHUSD"}


def _crypto_sources(asset: AssetConfig) -> bool:
    return asset.key in COINBASE_PRODUCTS


def fetch_candles_5m(asset: AssetConfig, days: int = 5) -> list[Candle]:
    """Bougies 5 minutes sur plusieurs jours (pour ATR, range horaire, MTF)."""
    errors = []
    if _crypto_sources(asset):
        if asset.binance_symbol and days * 288 <= 1000:  # Binance : 1 000 bougies max par requête
            try:
                return binance.fetch_candles(asset.binance_symbol, "5m", limit=days * 288)
            except ProviderError as exc:
                errors.append(f"binance: {exc}")
        if days <= 7:
            try:
                return coinbase.fetch_candles(COINBASE_PRODUCTS[asset.key], 300, limit=days * 288)
            except ProviderError as exc:
                errors.append(f"coinbase: {exc}")
            try:
                return kraken.fetch_candles(KRAKEN_PAIRS[asset.key], 5)
            except ProviderError as exc:
                errors.append(f"kraken: {exc}")
    try:
        return yahoo.fetch_candles(asset.yahoo_symbol, "5m", f"{min(days, 60)}d")
    except ProviderError as exc:
        errors.append(f"yahoo: {exc}")
    raise ProviderError(f"{asset.key}: " + " | ".join(errors))


def fetch_candles_1m(asset: AssetConfig) -> list[Candle]:
    """Bougies 1 minute récentes (pour vérifier finement les touches TP/SL)."""
    errors = []
    if _crypto_sources(asset):
        if asset.binance_symbol:
            try:
                return binance.fetch_candles(asset.binance_symbol, "1m", limit=300)
            except ProviderError as exc:
                errors.append(f"binance: {exc}")
        try:
            return coinbase.fetch_candles(COINBASE_PRODUCTS[asset.key], 60, limit=300)
        except ProviderError as exc:
            errors.append(f"coinbase: {exc}")
        try:
            return kraken.fetch_candles(KRAKEN_PAIRS[asset.key], 1)
        except ProviderError as exc:
            errors.append(f"kraken: {exc}")
    try:
        return yahoo.fetch_candles(asset.yahoo_symbol, "1m", "1d")
    except ProviderError as exc:
        errors.append(f"yahoo: {exc}")
    raise ProviderError(f"{asset.key}: " + " | ".join(errors))


def fetch_price(asset: AssetConfig) -> float:
    errors = []
    if _crypto_sources(asset):
        if asset.binance_symbol:
            try:
                return binance.fetch_price(asset.binance_symbol)
            except ProviderError as exc:
                errors.append(f"binance: {exc}")
        try:
            return coinbase.fetch_price(COINBASE_PRODUCTS[asset.key])
        except ProviderError as exc:
            errors.append(f"coinbase: {exc}")
        try:
            return kraken.fetch_price(KRAKEN_PAIRS[asset.key])
        except ProviderError as exc:
            errors.append(f"kraken: {exc}")
    try:
        return yahoo.fetch_price(asset.yahoo_symbol)
    except ProviderError as exc:
        errors.append(f"yahoo: {exc}")
    if asset.key == "bitcoin":
        try:
            return coingecko.fetch_price()
        except ProviderError as exc:
            errors.append(f"coingecko: {exc}")
    raise ProviderError(f"{asset.key}: " + " | ".join(errors))


# ---- séries de référence pour les corrélations (Yahoo) ------------------------------------
LEADERS = {
    "vix": "^VIX",          # volatilité implicite : hausse brutale = risque pour indices
    "dxy": "DX-Y.NYB",      # dollar : hausse = vent contraire pour l'or (et souvent le Nasdaq)
    "tnx": "^TNX",          # rendement 10 ans US : hausse = vent contraire Nasdaq / or
}


def fetch_leader_candles(key: str) -> list[Candle]:
    symbol = LEADERS[key]
    return yahoo.fetch_candles(symbol, "5m", "2d")
