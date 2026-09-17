"""Client HTTP minimal avec ré-essais et cache court (pour rester sous les quotas gratuits)."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

from ..config import DATA_DIR

log = logging.getLogger(__name__)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CACHE_DIR = DATA_DIR / "cache"


class ProviderError(RuntimeError):
    pass


def get_json(url: str, params: dict[str, Any] | None = None, *, timeout: int = 15,
             retries: int = 3, cache_seconds: int = 0, headers: dict[str, str] | None = None) -> Any:
    hdrs = {"User-Agent": UA, "Accept": "application/json,text/plain,*/*"}
    if headers:
        hdrs.update(headers)
    cache_file = None
    if cache_seconds > 0:
        key = url + "?" + json.dumps(params or {}, sort_keys=True)
        cache_file = CACHE_DIR / (str(abs(hash(key))) + ".json")
        if cache_file.exists() and time.time() - cache_file.stat().st_mtime < cache_seconds:
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=hdrs, timeout=timeout)
            if r.status_code == 429:
                raise ProviderError(f"rate limited: {url}")
            r.raise_for_status()
            data = r.json()
            if cache_file is not None:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps(data), encoding="utf-8")
            return data
        except (requests.RequestException, ValueError, ProviderError) as exc:  # noqa: PERF203
            last_err = exc
            log.warning("HTTP %s échec (%d/%d): %s", url, attempt + 1, retries, exc)
            time.sleep(1.5 * (attempt + 1))
    raise ProviderError(f"{url}: {last_err}")


def get_text(url: str, *, timeout: int = 15, retries: int = 2) -> str:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
            r.raise_for_status()
            return r.text
        except requests.RequestException as exc:  # noqa: PERF203
            last_err = exc
            time.sleep(1.0 * (attempt + 1))
    raise ProviderError(f"{url}: {last_err}")
