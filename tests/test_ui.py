import json
import threading
from datetime import datetime, timezone
from http.client import HTTPConnection

from trading_bot.config import Config, default_assets
from trading_bot.engine import Engine
from trading_bot.storage import Store
from trading_bot.ui import make_handler
from http.server import ThreadingHTTPServer

from conftest import make_candles


def test_ui_serves_dashboard_and_manual(tmp_path, monkeypatch):
    now = datetime(2026, 9, 17, 14, 0, tzinfo=timezone.utc)
    candles = make_candles(n=500, drift=0.0, noise=0.0008, seed=9, start_ts=int(now.timestamp()) - 500 * 300)
    cfg = Config(assets=default_assets())
    eng = Engine(cfg, Store(tmp_path))
    from trading_bot import engine as engmod
    monkeypatch.setattr(engmod.market, "fetch_candles_5m", lambda asset, days=5: candles)
    monkeypatch.setattr(engmod.market, "fetch_price", lambda asset: candles[-1].close)
    monkeypatch.setattr(engmod, "notify", lambda text, title=None: None)
    monkeypatch.setattr(engmod, "utcnow", lambda: now)

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(eng))
    port = server.server_address[1]
    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    try:
        c = HTTPConnection("127.0.0.1", port, timeout=5)
        c.request("GET", "/api/ping"); r = c.getresponse(); assert r.status == 200 and json.loads(r.read())["mode"] == "local"
        c.request("GET", "/api/state"); r = c.getresponse(); assert r.status == 200
        state = json.loads(r.read()); assert "criteria" in state and len(state["assets"]) == 5
        c.request("GET", "/docs/index.html"); r = c.getresponse(); body = r.read().decode("utf-8")
        assert r.status == 200 and "Demander un trade" in body
        c.request("GET", "/docs/../trading_bot/config.py"); r = c.getresponse(); r.read(); assert r.status == 404
        payload = json.dumps({"asset": "gold", "direction": "long", "note": "ui"})
        c.request("POST", "/api/manual", body=payload, headers={"Content-Type": "application/json"})
        r = c.getresponse(); j = json.loads(r.read())
        assert r.status == 200 and j["ok"] and j["signal"]["source"] == "manual" and j["signal"]["asset"] == "gold"
        c.request("POST", "/api/manual", body=json.dumps({"asset": "x", "direction": "long"}), headers={"Content-Type": "application/json"})
        r = c.getresponse(); assert r.status == 400 and not json.loads(r.read())["ok"]
        c.request("GET", "/api/state"); r = c.getresponse(); state = json.loads(r.read())
        assert state["overview"]["open"] == 1
    finally:
        server.shutdown()
        server.server_close()


def test_dotenv_loading(tmp_path, monkeypatch):
    from trading_bot.config import load_dotenv
    env = tmp_path / ".env"
    env.write_text('TELEGRAM_BOT_TOKEN="abc:123"\n# commentaire\nTELEGRAM_CHAT_ID=42\nDEJA=nouveau\n', encoding="utf-8")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setenv("DEJA", "existant")
    load_dotenv(env)
    import os
    assert os.environ["TELEGRAM_BOT_TOKEN"] == "abc:123" and os.environ["TELEGRAM_CHAT_ID"] == "42"
    assert os.environ["DEJA"] == "existant"
