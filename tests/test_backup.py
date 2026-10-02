"""Sauvegarde hebdomadaire : archive des fichiers suivis (+ bougies), envoyée au seul propriétaire."""
import subprocess
import zipfile
from datetime import datetime, timezone

from trading_bot import backup

DAY = datetime(2026, 10, 4, 21, 30, tzinfo=timezone.utc)


def _repo(tmp_path):
    root = tmp_path / "repo"
    (root / "data").mkdir(parents=True)
    (root / "data" / "signals.json").write_text("[]")
    (root / "run.py").write_text("print('ok')")
    (root / "secret.env").write_text("TOKEN=x")                 # non suivi : jamais dans l'archive
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "data/signals.json", "run.py"], cwd=root, check=True)
    return root


def test_archive_contains_tracked_files_and_candles(tmp_path):
    root = _repo(tmp_path)
    candles = tmp_path / "candles.tar.gz"
    candles.write_bytes(b"bougies")
    path, summary = backup.build_archive(root, tmp_path / "out", DAY, candles)
    names = zipfile.ZipFile(path).namelist()
    assert path.name == "yasuke-sauvegarde-2026-10-04.zip"
    assert "Trading-Bot/data/signals.json" in names and "Trading-Bot/run.py" in names
    assert "Trading-Bot/sauvegarde/candles.tar.gz" in names and "Trading-Bot/sauvegarde/LISEZMOI.txt" in names
    assert not any("secret.env" in n for n in names)
    assert summary["files"] == 2 and summary["candles"] is True
    assert "bougies" in backup.caption(summary, DAY)


def test_archive_without_candles(tmp_path):
    path, summary = backup.build_archive(_repo(tmp_path), tmp_path / "out", DAY, tmp_path / "absent.tar.gz")
    assert summary["candles"] is False
    assert "Trading-Bot/sauvegarde/candles.tar.gz" not in zipfile.ZipFile(path).namelist()


def test_sent_only_to_owner(tmp_path, monkeypatch):
    path, _ = backup.build_archive(_repo(tmp_path), tmp_path / "out", DAY)
    sent = []

    class Resp:
        def raise_for_status(self):
            pass

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "111, 222")
    monkeypatch.setattr(backup.requests, "post", lambda url, data, files, timeout: sent.append(data["chat_id"]) or Resp())
    assert backup.send_document(path, "légende") is True
    assert sent == ["111"]                                           # le propriétaire seulement


def test_not_configured_returns_false(tmp_path, monkeypatch):
    path, _ = backup.build_archive(_repo(tmp_path), tmp_path / "out", DAY)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    assert backup.send_document(path, "x") is False
