"""Routage par actif avec repli automatique entre fournisseurs gratuits."""
from __future__ import annotations

import logging

from ..config import AssetConfig
from ..models import Candle
from . import binance, coingecko, yahoo
from .http import ProviderError

log = logging.getLogger(__name__)


def fetch_candles_5m(asset: AssetConfig, days: int = 5) -> list[Candle]:
    """Bougies 5 minutes sur plusieurs jours (pour ATR, range horaire, MTF)."""
    errors = []
    if asset.binance_symbol:
        try:
            return binance.fetch_candles(asset.binance_symbol, "5m", limit=min(1000, days * 288))
        except ProviderError as exc:
            errors.append(f"binance: {exc}")
    try:
        return yahoo.fetch_candles(asset.yahoo_symbol, "5m", f"{days}d")
    except ProviderError as exc:
        errors.append(f"yahoo: {exc}")
    raise ProviderError(f"{asset.key}: " + " | ".join(errors))


def fetch_candles_1m(asset: AssetConfig) -> list[Candle]:
    """Bougies 1 minute récentes (pour vérifier finement les touches TP/SL)."""
    errors = []
    if asset.binance_symbol:
        try:
            return binance.fetch_candles(asset.binance_symbol, "1m", limit=180)
        except ProviderError as exc:
            errors.append(f"binance: {exc}")
    try:
        return yahoo.fetch_candles(asset.yahoo_symbol, "1m", "1d")
    except ProviderError as exc:
        errors.append(f"yahoo: {exc}")
    raise ProviderError(f"{asset.key}: " + " | ".join(errors))


def fetch_price(asset: AssetConfig) -> float:
    errors = []
    if asset.binance_symbol:
        try:
            return binance.fetch_price(asset.binance_symbol)
        except ProviderError as exc:
            errors.append(f"binance: {exc}")
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
