"""Interface en ligne de commande.

  python run.py scan        # analyse et propose des signaux (si convergence)
  python run.py track       # met à jour les signaux ouverts (TP / SL / expiration)
  python run.py tick        # track + scan (mode planifié, ex. GitHub Actions toutes les 5 min)
  python run.py summary     # résumé quotidien
  python run.py stats       # statistiques de l'historique
  python run.py loop        # boucle locale : tick toutes les 5 minutes
  python run.py status      # signaux ouverts
  python run.py test-notify # envoie un message de test (Telegram / Discord / console)
  python run.py backtest    # rejoue la stratégie sur l'historique 5 min (--days 30, --asset bitcoin)
  python run.py report      # régénère data/REPORT.md
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import date

from .config import DISCLAIMER, load_config
from .models import utcnow
from .notify import notify
from .engine import Engine
from .learning import analyze
from .signals import format_signal


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Générateur de signaux de scalping (NQ, BTC, XAU) — données gratuites")
    p.add_argument("command", choices=["scan", "track", "tick", "summary", "stats", "loop", "status", "test-notify", "backtest", "report"])
    p.add_argument("--dry-run", action="store_true", help="scan sans enregistrer les signaux")
    p.add_argument("--day", help="jour du résumé (AAAA-MM-JJ)")
    p.add_argument("--interval", type=int, default=5, help="minutes entre deux ticks (mode loop)")
    p.add_argument("--days", type=int, default=30, help="profondeur du backtest en jours (max 60 sur Yahoo)")
    p.add_argument("--asset", action="append", help="limiter le backtest à un actif (répétable)")
    p.add_argument("--send", action="store_true", help="envoyer aussi le résultat du backtest en notification")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    cfg = load_config()
    logging.basicConfig(level=logging.DEBUG if args.verbose else getattr(logging, cfg.log_level, logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    eng = Engine(cfg)

    if args.command == "scan":
        sigs = eng.scan(dry_run=args.dry_run)
        if not sigs:
            print("Aucun signal : pas de convergence suffisante ou contexte défavorable.")
            print(DISCLAIMER)
    elif args.command == "track":
        closed = eng.track()
        print(f"{len(closed)} signal(aux) clôturé(s).")
    elif args.command == "tick":
        print(json.dumps(eng.tick(), ensure_ascii=False))
    elif args.command == "summary":
        day = date.fromisoformat(args.day) if args.day else None
        eng.summary(day)
    elif args.command == "stats":
        print(json.dumps(analyze(eng.store.history()), indent=2, ensure_ascii=False))
    elif args.command == "status":
        sigs = eng.store.open_signals()
        if not sigs:
            print("Aucun signal ouvert.")
        for s in sigs:
            print(format_signal(s, cfg.timezone))
            print()
    elif args.command == "backtest":
        res = eng.backtest(days=min(60, max(2, args.days)), asset_keys=args.asset, send=args.send)
        if not res:
            print("Backtest impossible : aucune donnée récupérée.")
            return 1
        print(DISCLAIMER)
    elif args.command == "report":
        print(eng.write_report())
    elif args.command == "test-notify":
        notify(f"🔔 Test de notification du Trading-Bot — {utcnow():%d/%m/%Y %H:%M} UTC.\n"
               "Si vous lisez ceci sur Telegram/Discord, les notifications sont opérationnelles.\n\n" + DISCLAIMER)
    elif args.command == "loop":
        print(f"Boucle locale : un tick toutes les {args.interval} min (Ctrl+C pour arrêter)")
        while True:
            try:
                print(json.dumps(eng.tick(), ensure_ascii=False), flush=True)
            except Exception as exc:  # noqa: BLE001 — la boucle ne doit jamais mourir
                logging.exception("tick en erreur : %s", exc)
            time.sleep(args.interval * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
