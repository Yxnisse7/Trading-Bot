"""Interface locale : petit serveur HTTP (bibliothèque standard) qui sert docs/index.html,
expose les données du tableau de bord et accepte les demandes de trade manuel.

  python run.py ui            # http://127.0.0.1:8787
"""
from __future__ import annotations

import json
import logging
import mimetypes
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .config import ROOT_DIR
from .engine import Engine

log = logging.getLogger(__name__)

RAW = "https://raw.githubusercontent.com/Yxnisse7/Trading-Bot/main/docs/"
_raw_cache: dict[str, tuple[float, bytes]] = {}


def fresh_json(rel: str, fallback: Path, ttl: float = 60.0, get=None) -> bytes | None:
    """Copie miroir du dépôt sur le PC : les fichiers du site sont relus sur GitHub (1 à 2 min après le bot,
    plus vite que GitHub Pages), gardés `ttl` secondes ; le fichier local sert si GitHub ne répond pas."""
    now = time.time()
    hit = _raw_cache.get(rel)
    if hit and now - hit[0] < ttl:
        return hit[1]
    try:
        body = (get or _fetch)(RAW + rel + f"?t={int(now)}")
        json.loads(body)
        _raw_cache[rel] = (now, body)
        return body
    except Exception as e:                         # réseau coupé, fichier absent : copie locale
        log.debug("lecture GitHub impossible (%s) : %s", rel, e)
        if hit:
            return hit[1]
        return fallback.read_bytes() if fallback.is_file() else None


def _fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=8) as r:
        return r.read()


def demo_file() -> Path:
    """État du démo MT5 écrit par le pont (journal/demo_live.json, dossier du PC, à côté du clone du bot)."""
    return Path(os.environ.get("TRADING_BOT_PC_ROOT", ROOT_DIR.parent)) / "journal" / "demo_live.json"


def make_handler(engine: Engine):
    lock = threading.Lock()
    docs_dir = ROOT_DIR / "docs"
    data_dir = engine.store.dir
    mirror = is_mirror(engine)

    class Handler(BaseHTTPRequestHandler):
        server_version = "TradingBotUI/1.0"

        def log_message(self, fmt: str, *args: Any) -> None:  # journal plus discret
            log.debug("%s " + fmt, self.address_string(), *args)

        # ---- utilitaires
        def _json(self, code: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _file(self, path: Path) -> None:
            if not path.is_file():
                self._json(404, {"error": "introuvable"})
                return
            ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype == "application/json":
                ctype += "; charset=utf-8"
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _bytes(self, body: bytes, ctype: str = "application/json; charset=utf-8") -> None:
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                return {}
            try:
                return json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return {}

        # ---- routes
        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                self.send_response(302)
                self.send_header("Location", "/docs/index.html")
                self.end_headers()
                return
            if path == "/api/demo":
                self._file(demo_file())
                return
            if path == "/api/state" and mirror:
                body = fresh_json("dashboard.json", engine.store.dashboard_file)
                if body is not None:
                    self._bytes(body)
                    return
            if path == "/api/portfolio" and mirror:
                body = fresh_json("portfolio.json", docs_dir / "portfolio.json")
                if body is not None:
                    self._bytes(body)
                    return
            if mirror and path.startswith("/docs/") and path.endswith(".json") and ".." not in path:
                body = fresh_json(path[len("/docs/"):], docs_dir / path[len("/docs/"):])
                if body is not None:
                    self._bytes(body)
                    return
            if path == "/api/state":
                if not engine.store.dashboard_file.exists():
                    with lock:
                        engine.write_report()
                self._file(engine.store.dashboard_file)
                return
            if path == "/api/portfolio":
                self._json(200, engine.portfolio.data)
                return
            if path == "/api/ping":
                # mirror : l'interface lit les données du dépôt (copie de secours mise à jour par git pull),
                # pas celles d'un bot qui tourne sur ce PC (TRADING_BOT_DATA_DIR vers un autre dossier)
                self._json(200, {"ok": True, "mode": "local", "mirror": mirror, "demo": demo_file().is_file()})
                return
            if path.startswith("/docs/"):
                target = (docs_dir / path[len("/docs/"):]).resolve()
                if docs_dir.resolve() in target.parents or target == docs_dir.resolve():
                    self._file(target)
                    return
            if path.startswith("/data/"):
                target = (data_dir / path[len("/data/"):]).resolve()
                if data_dir.resolve() in target.parents and target.suffix in (".json", ".md", ".log"):
                    self._file(target)
                    return
            self._json(404, {"error": "introuvable"})

        def do_POST(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            body = self._body()
            if is_mirror(engine):
                # copie miroir du dépôt : aucune action, le vrai bot tourne sur GitHub Actions
                self._json(403, {"ok": False, "error": "Copie locale du dépôt : actions désactivées (le bot tourne sur "
                                 "GitHub). Pour tester sur ce PC, lancez-le avec TRADING_BOT_DATA_DIR vers un autre dossier."})
                return
            try:
                if path == "/api/manual":
                    with lock:
                        num = lambda k: float(body[k]) if body.get(k) not in (None, "") else None  # noqa: E731
                        sig = engine.manual(str(body.get("asset", "")), str(body.get("direction", "")),
                                            note=str(body.get("note", ""))[:200],
                                            take_profit=num("tp"), stop_loss=num("sl"))
                    self._json(200, {"ok": True, "signal": sig.to_dict()})
                elif path == "/api/portfolio":
                    with lock:
                        data = engine.set_balance(float(body.get("balance", 0)),
                                                  float(body["risk_pct"]) if body.get("risk_pct") not in (None, "") else None)
                    self._json(200, {"ok": True, "portfolio": data})
                elif path == "/api/propose":
                    with lock:
                        res = engine.propose(str(body.get("asset", "")))
                    self._json(200, {"ok": True, **res})
                elif path == "/api/stop":
                    with lock:
                        res = engine.stop_trade(str(body.get("id") or "") or None)
                    self._json(200, {"ok": True, **res})
                elif path == "/api/scan":
                    with lock:
                        sigs = engine.scan()
                    self._json(200, {"ok": True, "new": [s.id for s in sigs]})
                elif path == "/api/track":
                    with lock:
                        closed = engine.track()
                    self._json(200, {"ok": True, "closed": [s.id for s in closed]})
                elif path == "/api/refresh":
                    with lock:
                        engine.write_report()
                    self._json(200, {"ok": True})
                else:
                    self._json(404, {"error": "introuvable"})
            except (ValueError, RuntimeError) as exc:
                self._json(400, {"ok": False, "error": str(exc)})
            except Exception as exc:  # noqa: BLE001 — l'interface ne doit pas tomber
                log.exception("erreur API")
                self._json(500, {"ok": False, "error": f"erreur interne : {exc}"})

    return Handler


def is_mirror(engine: Engine) -> bool:
    """L'interface lit les données du dépôt lui-même (copie de secours tenue à jour par git pull)."""
    return engine.store.dir.resolve() == (ROOT_DIR / "data").resolve()


def serve(engine: Engine, host: str = "127.0.0.1", port: int = 8787) -> None:
    # Copie miroir : rien n'est réécrit au démarrage, sinon le prochain « git pull » bute sur
    # des fichiers modifiés localement. Bot qui tourne sur ce PC : rapport recalculé.
    if not is_mirror(engine) or not engine.store.dashboard_file.exists():
        engine.write_report()
    server = ThreadingHTTPServer((host, port), make_handler(engine))
    print(f"Interface : http://{host}:{port}  (Ctrl+C pour arrêter)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
