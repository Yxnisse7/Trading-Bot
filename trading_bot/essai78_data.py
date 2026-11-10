"""Données des essais 78 à 80 (hors dépôt, dans data/history/long/).

    python -m trading_bot.essai78_data          → <marché>_1m.npz (HistData), <crypto>_5m.npz (Binance), yahoo78.json

HistData : fichiers annuels 1 min (mois par mois pour l'année en cours), heure fixe UTC−5 → UTC.
Binance : bougies 5 min mensuelles de data.binance.vision (avec le volume).
Yahoo : cours journaliers (Russell 2000, VIX) pour les règles journalières.
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import numpy as np
import requests

from .essai33 import LONG

UTC = timezone.utc
HISTDATA = {"silver": "XAGUSD", "nikkei": "JPXJPY", "ftse": "UKXGBP", "cac": "FRXEUR", "hangseng": "HKXHKD",
            "asx": "AUXAUD", "brent": "BCOUSD", "gbpusd": "GBPUSD", "usdjpy": "USDJPY",
            # déjà connus, utiles aux essais 79-80
            "gold": "XAUUSD", "euro": "EURUSD", "nasdaq": "NSXUSD", "sp500": "SPXUSD", "dax": "GRXEUR"}
BINANCE = {"eth": "ETHUSDT", "sol": "SOLUSDT", "btc": "BTCUSDT"}
YAHOO = {"russell": "^RUT", "vix": "^VIX", "nasdaq_d": "^NDX", "sp500_d": "^GSPC"}
FIRST_YEAR, LAST_YEAR, LAST_MONTH = 2014, 2026, 10
PAGE = "https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair}/{per}"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"


def _hd_one(pair: str, year: int, month: int | None) -> bytes | None:
    raw = LONG / "raw78" / f"{pair}_{year}{'' if month is None else f'{month:02d}'}.csv"
    if raw.exists():
        return raw.read_bytes()
    s = requests.Session()
    s.headers["User-Agent"] = UA
    per = f"{year}" if month is None else f"{year}/{month}"
    for attempt in range(4):
        try:
            page = PAGE.format(pair=pair.lower(), per=per)
            html = s.get(page, timeout=60).text
            tk = re.search(r'id="tk" value="([0-9a-f]+)"', html)
            if not tk:
                return None
            r = s.post("https://www.histdata.com/get.php", timeout=300, headers={"Referer": page},
                       data={"tk": tk.group(1), "date": str(year),
                             "datemonth": str(year) if month is None else f"{year}{month:02d}",
                             "platform": "ASCII", "timeframe": "M1", "fxpair": pair})
            z = zipfile.ZipFile(io.BytesIO(r.content))
            data = z.read(next(n for n in z.namelist() if n.lower().endswith(".csv")))
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(data)
            return data
        except Exception:                                    # noqa: BLE001 — réseau capricieux : on réessaie
            time.sleep(2 ** (attempt + 1))
    return None


def histdata(asset: str) -> str:
    npz = LONG / f"{asset}_1m.npz"
    if npz.exists():
        return f"{asset} déjà là"
    pair = HISTDATA[asset]
    jobs = [(pair, y, None) for y in range(FIRST_YEAR, LAST_YEAR)] + \
           [(pair, LAST_YEAR, m) for m in range(1, LAST_MONTH + 1)]
    rows = []
    for pr, y, m in jobs:
        data = _hd_one(pr, y, m)
        if data is None and m is None:                        # année en cours : peut-être seulement des mois
            for mm in range(1, 13):
                d2 = _hd_one(pr, y, mm)
                if d2:
                    data = (data or b"") + d2
        if not data:
            continue
        for line in data.decode("ascii", "ignore").splitlines():
            p = line.strip().split(";")
            if len(p) < 5 or len(p[0]) != 15:
                continue
            t = datetime.strptime(p[0], "%Y%m%d %H%M%S").replace(tzinfo=UTC) + timedelta(hours=5)
            rows.append((int(t.timestamp()), float(p[1]), float(p[2]), float(p[3]), float(p[4])))
    if not rows:
        return f"{asset} : aucune donnée"
    a = np.array(sorted(set(rows)), dtype=float)
    np.savez_compressed(npz, ts=a[:, 0].astype(np.int64), o=a[:, 1], h=a[:, 2], l=a[:, 3], c=a[:, 4])
    return f"{asset} {len(a)} bougies {datetime.fromtimestamp(a[0, 0], UTC):%Y-%m} → {datetime.fromtimestamp(a[-1, 0], UTC):%Y-%m}"


def binance(asset: str) -> str:
    npz = LONG / f"{asset}_5m.npz"
    if npz.exists():
        return f"{asset} déjà là"
    sym = BINANCE[asset]
    months = [(y, m) for y in range(2017, LAST_YEAR + 1) for m in range(1, 13) if (y, m) <= (LAST_YEAR, LAST_MONTH)]

    def one(ym):
        y, m = ym
        url = f"https://data.binance.vision/data/spot/monthly/klines/{sym}/5m/{sym}-5m-{y}-{m:02d}.zip"
        for attempt in range(4):
            try:
                r = requests.get(url, timeout=120)
                if r.status_code == 404:
                    return []
                z = zipfile.ZipFile(io.BytesIO(r.content))
                out = []
                for line in z.read(z.namelist()[0]).decode().splitlines():
                    p = line.split(",")
                    if not p[0].isdigit():
                        continue
                    t = int(p[0])
                    t = t // 1000000 if t > 10 ** 14 else t // 1000          # microsecondes depuis 2025
                    out.append((t, float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5])))
                return out
            except Exception:                                # noqa: BLE001
                time.sleep(2 ** (attempt + 1))
        return []

    with ThreadPoolExecutor(6) as ex:
        rows = [r for part in ex.map(one, months) for r in part]
    a = np.array(sorted(set(rows)), dtype=float)
    np.savez_compressed(npz, ts=a[:, 0].astype(np.int64), o=a[:, 1], h=a[:, 2], l=a[:, 3], c=a[:, 4], v=a[:, 5])
    return f"{asset} {len(a)} bougies 5 min"


def yahoo() -> str:
    f = LONG / "yahoo78.json"
    out = json.loads(f.read_text()) if f.exists() else {}
    p1 = int(datetime(2005, 1, 1, tzinfo=UTC).timestamp())
    p2 = int(datetime(LAST_YEAR, LAST_MONTH, 31, tzinfo=UTC).timestamp())
    for key, sym in YAHOO.items():
        if key in out:
            continue
        r = requests.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}",
                         params={"period1": p1, "period2": p2, "interval": "1d"}, headers={"User-Agent": UA}, timeout=60)
        res = r.json()["chart"]["result"][0]
        q = res["indicators"]["quote"][0]
        out[key] = [[t, o, h, lo, c] for t, o, h, lo, c in zip(res["timestamp"], q["open"], q["high"], q["low"], q["close"])
                    if None not in (o, h, lo, c)]
    f.write_text(json.dumps(out))
    return "yahoo " + ", ".join(f"{k} {len(v)}" for k, v in out.items())


def main() -> None:
    LONG.mkdir(parents=True, exist_ok=True)
    want = sys.argv[1:] or [*HISTDATA, *BINANCE, "yahoo"]
    for a in want:
        if a in BINANCE:
            print(binance(a), flush=True)
    hd = [a for a in want if a in HISTDATA]
    with ThreadPoolExecutor(4) as ex:
        for msg in ex.map(histdata, hd):
            print(msg, flush=True)
    if "yahoo" in want:
        try:
            print(yahoo(), flush=True)
        except Exception as e:                              # noqa: BLE001
            print("yahoo en échec :", e, flush=True)


if __name__ == "__main__":
    main()
