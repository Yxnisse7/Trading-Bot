"""Historique long en bougies 5 min, gratuit, pour tester les setups sur bien plus que les 60 jours de Yahoo.

- Cryptos : archives mensuelles publiques de Binance (data.binance.vision), vraies bougies et vrai volume.
- Nasdaq, S&P 500, or, pétrole, euro : bougies 1 min de Dukascopy (datafeed public), regroupées en 5 min.
  Ce sont des CFD (prix au comptant), pas les contrats CME : niveaux décalés et volume en nombre de
  ticks, mais même forme de mouvement. Les setups étant jugés en R, ça suffit pour tester une idée.

Rien n'est inventé : un jour ou un mois introuvable est simplement absent. Ces bougies vont dans
data/history/ (jamais mélangées aux bougies Yahoo de data/candles/, ni commitées : release « history »).
"""
from __future__ import annotations

import csv
import io
import logging
import lzma
import statistics
import struct
import time
import zipfile
from datetime import date, datetime, timedelta, timezone

import requests

from ..models import Candle

log = logging.getLogger(__name__)

BINANCE = {"bitcoin": "BTCUSDT", "ethereum": "ETHUSDT"}
DUKASCOPY = {"nasdaq": "USATECHIDXUSD", "sp500": "USA500IDXUSD", "gold": "XAUUSD",
             "oil": "LIGHTCMDUSD", "euro": "EURUSD"}
SOURCE_LABEL = {**{k: "Binance (vraies bougies)" for k in BINANCE},
                **{k: "Dukascopy (CFD au comptant)" for k in DUKASCOPY}}
SCALES = (1, 10, 100, 1000, 10000, 100000)


HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}
STATS: dict[str, int] = {"ok": 0, "absent": 0, "failed": 0, "throttled": 0}


def _get(url: str, timeout: int = 30, retries: int = 6) -> bytes | None:
    """Contenu brut, None si absent (404 ou fichier vide : week-end, jour férié, mois pas encore publié).
    Trop de requêtes (429) : on attend de plus en plus longtemps (Retry-After si fourni) puis on réessaie."""
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout, headers=HEADERS)
            if r.status_code == 404:
                STATS["absent"] += 1
                return None
            if r.status_code == 429:
                STATS["throttled"] += 1
                wait = r.headers.get("Retry-After", "")
                time.sleep(min(int(wait), 120) if wait.isdigit() else 10 * (attempt + 1))
                continue
            r.raise_for_status()
            STATS["ok" if r.content else "absent"] += 1
            return r.content or None
        except requests.RequestException as exc:
            if attempt == retries - 1:
                break
            log.debug("historique : %s (%s), nouvel essai", url, exc)
            time.sleep(3 * (attempt + 1))
    STATS["failed"] += 1
    log.warning("historique : %s indisponible après %d essais", url, retries)
    return None


def resample_5m(candles: list[Candle]) -> list[Candle]:
    """Regroupe des bougies 1 min en bougies 5 min alignées (00, 05, 10…)."""
    out: list[Candle] = []
    for c in sorted(candles, key=lambda c: c.ts):
        start = c.ts - c.ts % 300
        if out and out[-1].ts == start:
            b = out[-1]
            out[-1] = Candle(start, b.open, max(b.high, c.high), min(b.low, c.low), c.close, b.volume + c.volume)
        else:
            out.append(Candle(start, c.open, c.high, c.low, c.close, c.volume))
    return out


# ---------------------------------------------------------------- Binance
def parse_binance_csv(raw: bytes) -> list[Candle]:
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8")
    out = []
    for row in csv.reader(io.StringIO(text)):
        if not row or not row[0].isdigit():
            continue                                   # en-tête éventuel
        ts = int(row[0])
        ts = ts // 1_000_000 if ts > 10**14 else ts // 1000   # microsecondes depuis 2025, millisecondes avant
        out.append(Candle(ts, float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])))
    return out


def _binance_days(sym: str, start: date, end: date) -> list[Candle]:
    out: list[Candle] = []
    d = start
    while d < end:
        raw = _get(f"https://data.binance.vision/data/spot/daily/klines/{sym}/5m/{sym}-5m-{d:%Y-%m-%d}.zip")
        if raw:
            out += parse_binance_csv(raw)
        d += timedelta(days=1)
    return out


def fetch_binance(asset: str, months: int, today: date) -> list[Candle]:
    sym = BINANCE[asset]
    out: list[Candle] = []
    y, m = today.year, today.month
    for _ in range(months):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        url = f"https://data.binance.vision/data/spot/monthly/klines/{sym}/5m/{sym}-5m-{y}-{m:02d}.zip"
        raw = _get(url)
        if raw:
            out += parse_binance_csv(raw)
        else:
            # archive du mois pas encore publiée (premiers jours du mois suivant) : archives quotidiennes
            out += _binance_days(sym, date(y, m, 1), date(y + m // 12, m % 12 + 1, 1))
    out += _binance_days(sym, date(today.year, today.month, 1), today)     # mois en cours
    return sorted({c.ts: c for c in out}.values(), key=lambda c: c.ts)


# ---------------------------------------------------------------- Dukascopy
def parse_dukascopy_candles(raw: bytes, day_start: int, scale: float) -> list[Candle]:
    """Fichier BID_candles_min_1.bi5 : LZMA, enregistrements de 24 octets (big-endian) :
    secondes depuis minuit UTC, ouverture, clôture, plus bas, plus haut (entiers ÷ échelle), volume."""
    data = lzma.decompress(raw)
    out = []
    for off in range(0, len(data) - 23, 24):
        t, o, c, lo, hi, v = struct.unpack(">5if", data[off:off + 24])
        if v <= 0 and o == c == lo == hi:
            continue                                   # minute sans cotation
        out.append(Candle(day_start + t, o / scale, hi / scale, lo / scale, c / scale, float(v)))
    return out


def detect_scale(raw: bytes, reference: float | None) -> float:
    """Échelle des prix entiers : celle qui ramène la médiane près du prix de référence (bougies Yahoo)."""
    data = lzma.decompress(raw)
    closes = [struct.unpack(">5if", data[o:o + 24])[2] for o in range(0, len(data) - 23, 24)]
    med = statistics.median(closes) if closes else 0
    if not med or not reference:
        return 1000.0
    return float(min(SCALES, key=lambda s: abs((med / s) / reference - 1)))


def fetch_dukascopy(asset: str, days: int, today: date, reference: float | None, pause: float = 0.5,
                    deadline: float | None = None) -> list[Candle]:
    """`deadline` (horodatage) : on s'arrête là et on garde ce qui est déjà téléchargé (du plus ancien au plus récent)."""
    sym = DUKASCOPY[asset]
    out: list[Candle] = []
    scale = None
    d = today - timedelta(days=days)
    while d < today:
        if deadline is not None and time.time() > deadline:
            log.warning("Dukascopy %s : temps écoulé, arrêt au %s", sym, d)
            break
        if d.weekday() != 5:                           # samedi : marché fermé
            # mois numérotés à partir de 0 dans les adresses Dukascopy
            url = f"https://datafeed.dukascopy.com/datafeed/{sym}/{d.year}/{d.month - 1:02d}/{d.day:02d}/BID_candles_min_1.bi5"
            raw = _get(url)
            if raw:
                if scale is None:
                    scale = detect_scale(raw, reference)
                start = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
                try:
                    out += parse_dukascopy_candles(raw, start, scale)
                except (lzma.LZMAError, struct.error) as exc:
                    log.warning("Dukascopy %s %s illisible (%s)", sym, d, exc)
            time.sleep(pause)
        d += timedelta(days=1)
    return resample_5m(out)


def check_candles(candles: list[Candle]) -> dict:
    """Contrôle de cohérence (fiche ml4t-validate-data) : bas ≤ ouverture/clôture ≤ haut, doublons, trous."""
    bad = sum(1 for c in candles if not (c.low <= min(c.open, c.close) and max(c.open, c.close) <= c.high))
    gaps = sum(1 for a, b in zip(candles, candles[1:]) if b.ts - a.ts > 4 * 86400)
    return {"n": len(candles), "incoherent": bad, "gaps_over_4_days": gaps,
            "first": datetime.fromtimestamp(candles[0].ts, tz=timezone.utc).date().isoformat() if candles else None,
            "last": datetime.fromtimestamp(candles[-1].ts, tz=timezone.utc).date().isoformat() if candles else None}
