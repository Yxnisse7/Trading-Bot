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
