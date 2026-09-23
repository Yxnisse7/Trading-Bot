from trading_bot import notify as n


def test_multi_chat_and_targeted(monkeypatch):
    calls = []
    monkeypatch.setattr(n, "_telegram", lambda token, cid, body, **kw: calls.append((cid, body)))
    monkeypatch.setattr(n, "_discord", lambda webhook, body: calls.append(("discord", body)))
    monkeypatch.setattr(n, "_append_log", lambda body: None)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1, 2;3")
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://x")
    assert n.telegram_chat_ids() == ["1", "2", "3"] and n.telegram_chat_id() == "1"
    n.notify("hello")
    assert calls == [("1", "hello"), ("2", "hello"), ("3", "hello"), ("discord", "hello")]
    calls.clear()
    n.notify("réponse", chat_id="2")
    assert calls == [("2", "réponse")]


def test_outbox_defers_and_flushes(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(n, "_telegram", lambda token, cid, body, **kw: calls.append((cid, body)))
    monkeypatch.setattr(n, "_append_log", lambda body: None)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    outbox = tmp_path / "outbox.jsonl"
    monkeypatch.setenv("TRADING_BOT_OUTBOX", str(outbox))
    n.notify("a")
    n.notify("b", chat_id="9")
    assert calls == [] and outbox.exists()
    assert n.flush_outbox() == 2
    assert calls == [("1", "a"), ("9", "b")] and not outbox.exists()
    assert n.flush_outbox() == 0


def test_html_buttons_reply_threading(monkeypatch, tmp_path):
    """Un signal garde le numéro de son message ; l'issue lui répond. Aucun numéro de chat n'est écrit."""
    calls = []

    def fake(token, cid, body, **kw):
        calls.append((cid, body, kw))
        return 100 + len(calls)
    monkeypatch.setattr(n, "_telegram", fake)
    monkeypatch.setattr(n, "_append_log", lambda body: None)
    monkeypatch.setattr(n, "DATA_DIR", tmp_path)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111,222")
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("TRADING_BOT_OUTBOX", raising=False)
    n.notify("<b>signal</b>", html=True, key="sig1", buttons=[[("Graphique", "https://x")]])
    assert calls[0][2]["html"] and calls[0][2]["buttons"] == [[("Graphique", "https://x")]] and calls[0][2]["reply_to"] is None
    saved = (tmp_path / n.MESSAGES_FILE).read_text(encoding="utf-8")
    assert "111" not in saved and "222" not in saved and n.chat_key("111") in saved
    n.notify("issue", reply_to="sig1", silent=True)
    assert [c[2]["reply_to"] for c in calls[2:]] == [101, 102] and all(c[2]["silent"] for c in calls[2:])


def test_html_refused_falls_back_to_plain(monkeypatch):
    class R:
        def __init__(self, code):
            self.status_code, self.text = code, "bad"
        def raise_for_status(self):
            pass
        def json(self):
            return {"result": {"message_id": 7}}
    posted = []

    def post(url, json=None, timeout=None):
        posted.append(json)
        return R(400 if json.get("parse_mode") else 200)
    monkeypatch.setattr(n.requests, "post", post)
    assert n._telegram("t", "1", "<b>Prix</b> <code>1,5</code> &amp; co", html=True) == 7
    assert posted[1]["text"] == "Prix 1,5 & co" and "parse_mode" not in posted[1]
