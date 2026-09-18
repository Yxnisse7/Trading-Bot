from trading_bot import notify as n


def test_multi_chat_and_targeted(monkeypatch):
    calls = []
    monkeypatch.setattr(n, "_telegram", lambda token, cid, body: calls.append((cid, body)))
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
    monkeypatch.setattr(n, "_telegram", lambda token, cid, body: calls.append((cid, body)))
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
