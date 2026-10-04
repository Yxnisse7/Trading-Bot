"""Historique long : décodage Binance et Dukascopy, regroupement en 5 min, contrôle de cohérence."""
import io
import lzma
import struct
import zipfile

from trading_bot.models import Candle
from trading_bot.providers import history as hist


def _zip(text):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("k.csv", text)
    return buf.getvalue()


def test_binance_csv_handles_milli_and_microseconds():
    raw = _zip("1704067200000,100,101,99,100.5,12,x\n1735689600000000,200,202,199,201,3,x\n")
    c = hist.parse_binance_csv(raw)
    assert [x.ts for x in c] == [1704067200, 1735689600]
    assert c[0].close == 100.5 and c[1].volume == 3.0


def _bi5(rows):
    return lzma.compress(b"".join(struct.pack(">5if", *r) for r in rows))


def test_dukascopy_candles_decode_scale_and_resample():
    # 3 minutes de Nasdaq vers 30 000 points, prix entiers x1000
    rows = [(0, 30_000_000, 30_010_000, 29_990_000, 30_020_000, 5.0),
            (60, 30_010_000, 30_030_000, 30_000_000, 30_040_000, 4.0),
            (300, 30_030_000, 30_020_000, 30_015_000, 30_035_000, 2.0)]
    raw = _bi5(rows)
    scale = hist.detect_scale(raw, reference=31_000.0)
    assert scale == 1000
    one = hist.parse_dukascopy_candles(raw, 1_700_000_000 - 1_700_000_000 % 86400, scale)
    assert one[0].open == 30_000 and one[0].close == 30_010 and one[0].high == 30_020 and one[0].low == 29_990
    five = hist.resample_5m(one)
    assert len(five) == 2 and five[0].high == 30_040 and five[0].close == 30_030 and five[0].volume == 9.0
    assert hist.check_candles(five)["incoherent"] == 0


def test_check_candles_flags_incoherent_bars():
    bad = [Candle(0, 10, 9, 11, 10)]                    # plus haut sous le plus bas
    assert hist.check_candles(bad)["incoherent"] == 1


def test_long_history_saved_apart_from_signal_history(tmp_path):
    from trading_bot.storage import Store

    store = Store(tmp_path / "data", tmp_path / "docs")
    store.save_history("nasdaq", [Candle(1_700_000_100, 1, 2, 0.5, 1.5, 10)])
    assert store.load_history("nasdaq")[0].close == 1.5
    assert store.history() == []                      # l'historique des signaux reste intact


def test_throttled_request_waits_then_succeeds(monkeypatch):
    calls = []

    class R:
        def __init__(self, code, content=b""):
            self.status_code, self.content, self.headers = code, content, {"Retry-After": "0"}

        def raise_for_status(self):
            pass

    replies = [R(429), R(429), R(200, b"ok")]
    monkeypatch.setattr(hist.requests, "get", lambda url, **kw: calls.append(kw) or replies.pop(0))
    monkeypatch.setattr(hist.time, "sleep", lambda s: None)
    hist.STATS.update(ok=0, absent=0, failed=0, throttled=0)
    assert hist._get("https://x") == b"ok"
    assert hist.STATS["throttled"] == 2 and hist.STATS["ok"] == 1
    assert "User-Agent" in calls[0]["headers"]
