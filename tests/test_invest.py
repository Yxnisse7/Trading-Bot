"""Investissement halal à long terme : conversion en euros, statistiques, durées, portefeuilles, avis."""
import math
from datetime import datetime, timezone

import pytest

from trading_bot import invest
from trading_bot.providers.http import ProviderError

NOW = datetime(2026, 9, 30, tzinfo=timezone.utc)
START = datetime(2008, 1, 1, tzinfo=timezone.utc)


def _months(n, start=START):
    out, y, m = [], start.year, start.month
    for _ in range(n):
        out.append(int(datetime(y, m, 1, tzinfo=timezone.utc).timestamp()))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def _series(n, growth=0.007, amp=0.04, start=START, crash_at=None):
    ts = _months(n, start)
    v, rows = 100.0, []
    for i, t in enumerate(ts):
        v *= 1 + growth + amp * math.sin(i / 3.0)
        if crash_at is not None and i == crash_at:
            v *= 0.8
        rows.append((t, v))
    return rows


def fake_fetch(symbol):
    n = 225                                               # janvier 2008 → septembre 2026
    if symbol == "EURUSD=X":
        return [(t, 1.10) for t in _months(n)], "USD"
    if symbol == "EURGBP=X":
        return [(t, 0.85) for t in _months(n)], "GBP"
    if symbol == "MWIM.L":                               # lancé en 2026, coté en pence
        return [(t, v * 100) for t, v in _series(8, start=datetime(2026, 2, 1, tzinfo=timezone.utc))], "GBp"
    if symbol == "HBKU.L":
        return _series(14, growth=0.004, amp=0.002, start=datetime(2025, 8, 1, tzinfo=timezone.utc)), "USD"
    if symbol == "SPWI.L":
        raise ProviderError("symbole inconnu")
    if symbol == "ISDE.L":
        return _series(n, crash_at=n - 3), "USD"          # baisse récente de 20 %
    return _series(n), "USD"


def test_to_eur_handles_pence_and_dollars():
    fx = {"USD": {"2026-01": 1.25}, "GBP": {"2026-01": 0.8}}
    t = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp())
    assert invest.to_eur([(t, 125.0)], "USD", fx) == [("2026-01", 100.0)]
    assert invest.to_eur([(t, 8000.0)], "GBp", fx) == [("2026-01", 100.0)]      # 80 £ → 100 €


def test_holding_periods_and_advised_horizon():
    s = [(f"m{i}", v) for i, (_, v) in enumerate(_series(200))]
    periods = invest.holding_periods(s)
    assert periods["1"]["n"] == 188 and 0 <= periods["1"]["positive"] <= 1
    assert periods["10"]["positive"] == 1.0
    h = invest.advised_horizon(periods)
    assert h is not None and h <= 10


def test_build_products_models_and_advice():
    data = invest.build(NOW, fetch=fake_fetch, news=None, stocks=None)
    by = {p["key"]: p for p in data["products"]}
    monde = by["monde"]["stats"]
    assert monde["months"] > 200 and monde["r10"] is not None
    assert by["monde"]["advised"]["years"] >= 5 and by["sukuk"]["advised"]["years"] >= 2   # planchers de bon sens
    assert data["models"]["dynamique"]["advised"]["years"] >= 8
    # produit récent coté en pence : converti, jugé « trop récent », avec l'historique de référence du monde
    acwi = by["acwi"]
    assert acwi["stats"]["months"] == 8 and acwi["advice"]["label"] == "Trop récent"
    assert acwi["reference"]["months"] > 200
    assert by["sp500_wahed"]["stats"] is None and by["sp500_wahed"]["error"]
    # baisse récente de 20 % sur les émergents : renforcer progressivement
    assert by["emergents"]["advice"]["label"] == "Renforcer progressivement"
    # portefeuille prudent : sukuk trop récents, retirés de la simulation et signalés
    prudent = data["models"]["prudent"]["sim"]
    assert prudent["dropped"] == ["sukuk"] and abs(sum(prudent["weights_used"].values()) - 1) < 1e-9
    assert data["models"]["dynamique"]["sim"]["periods"]


def test_publish_writes_site_copy(tmp_path):
    invest.publish({"ok": 1}, tmp_path / "data", tmp_path / "docs")
    assert (tmp_path / "docs" / "data.json").read_text() == '{"ok":1}'


def test_news_titles_are_cleaned(monkeypatch):
    rss = """<rss><channel>
      <item><title>Les sukuk en hausse - Les Echos</title><link>https://a</link><pubDate>Mon, 28 Sep 2026 08:00:00 GMT</pubDate></item>
      <item><title>Cours de l'or : le SJC atteint 140 millions de VND - Vietnam.vn</title><link>https://c</link><pubDate>Mon, 28 Sep 2026 09:00:00 GMT</pubDate></item>
      <item><title>Vieux titre - Source</title><link>https://b</link><pubDate>Mon, 01 Jun 2026 08:00:00 GMT</pubDate></item>
    </channel></rss>"""
    monkeypatch.setattr(invest, "get_text", lambda url, timeout=12: rss)
    items = invest.fetch_invest_news(NOW)
    assert items[0]["title"] == "Les sukuk en hausse" and items[0]["source"] == "Les Echos"
    assert len(items) == 1                        # doublons, titres anciens et sites bloqués écartés
