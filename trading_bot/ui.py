"""Interface locale : petit serveur HTTP (bibliothèque standard) qui sert docs/index.html,
expose les données du tableau de bord et accepte les demandes de trade manuel.

  python run.py ui            # http://127.0.0.1:8787
"""
from __future__ import annotations

import json
import logging
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .config import ROOT_DIR
from .engine import Engine

log = logging.getLogger(__name__)


def make_handler(engine: Engine):
    lock = threading.Lock()
    docs_dir = ROOT_DIR / "docs"
    data_dir = engine.store.dir

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
                self._json(200, {"ok": True, "mode": "local"})
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


def serve(engine: Engine, host: str = "127.0.0.1", port: int = 8787) -> None:
    engine.write_report()
    server = ThreadingHTTPServer((host, port), make_handler(engine))
    print(f"Interface : http://{host}:{port}  (Ctrl+C pour arrêter)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
