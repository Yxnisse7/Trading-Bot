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
  python run.py fetch-data  # enregistre 60 jours de bougies 5 min dans data/candles/ (backtest --offline)
  python run.py manual --asset bitcoin --direction long [--tp 45000 --sl 43000]  # signal demandé, notifié et suivi
  python run.py propose --asset bitcoin                   # analyse à la demande + proposition
  python run.py commands    # traite les commandes Telegram reçues (/propose, /long, /short, /status)
  python run.py guide       # envoie le guide des commandes à tous les chats configurés
  python run.py learn       # recalcule l'apprentissage sur tous les trades clôturés
  python run.py portfolio [--balance 1000 --risk 1]   # simulation de compte : état, ou nouvelle balance
  python run.py ui          # interface locale : http://127.0.0.1:8787
  python run.py check-data  # vérifie que chaque actif répond (bougies, dernier prix)
  python run.py stop [--signal ID]  # arrête un trade au prix du moment (suivi ensuite en silence pour l'apprentissage)

Mode halal (second bot séparé, données dans data/halal) : ajoutez --halal, par ex.
  python run.py --halal tick | summary | status | portfolio --balance 1000 | backtest --days 60 | check-data
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import date, datetime

from .config import DISCLAIMER, load_config
from .models import utcnow
from .notify import notify
from .engine import Engine
from .learning import analyze
from .signals import format_signal


HALAL_REFUSED = {"manual", "propose", "commands", "guide", "ui", "loop", "fetch-data", "topstep"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Générateur de signaux de scalping (NQ, BTC, XAU) — données gratuites")
    p.add_argument("command", choices=["scan", "track", "tick", "summary", "stats", "loop", "status", "test-notify", "backtest", "report", "fetch-data", "manual", "propose", "ui", "commands", "portfolio", "guide", "learn", "flush-outbox", "check-data", "stop", "topstep"])
    p.add_argument("--signal", help="stop : identifiant (ou début) du trade à arrêter, ou son actif ; sans valeur, le seul trade ouvert")
    p.add_argument("--halal", action="store_true", help="mode halal : second bot séparé (achat seulement, sans levier, data/halal)")
    p.add_argument("--dry-run", action="store_true", help="scan sans enregistrer les signaux")
    p.add_argument("--force", action="store_true", help="summary : renvoyer le résumé même s'il a déjà été envoyé pour ce jour")
    p.add_argument("--day", help="jour du résumé : AAAA-MM-JJ, « hier » ou « aujourd'hui » (défaut : dernière journée de trading, la veille avant midi)")
    p.add_argument("--interval", type=int, default=5, help="minutes entre deux ticks (mode loop)")
    p.add_argument("--days", type=int, default=30, help="profondeur du backtest en jours (max 60 sur Yahoo)")
    p.add_argument("--asset", action="append", help="limiter le backtest à un actif (répétable)")
    p.add_argument("--send", action="store_true", help="envoyer aussi le résultat du backtest en notification")
    p.add_argument("--offline", action="store_true", help="backtest sur les bougies de data/candles/ (sans réseau)")
    p.add_argument("--direction", choices=["long", "short"], help="sens du signal manuel")
    p.add_argument("--note", default="", help="commentaire du signal manuel")
    p.add_argument("--tp", type=float, help="objectif imposé pour le signal manuel (sinon calibré par le bot)")
    p.add_argument("--sl", type=float, help="stop imposé pour le signal manuel (sinon calibré par le bot)")
    p.add_argument("--port", type=int, default=8787, help="port de l'interface locale")
    p.add_argument("--balance", type=float, help="nouvelle balance de simulation")
    p.add_argument("--risk", type=float, help="risque par trade en % de la balance")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    if args.halal:
        from .halal import HalalEngine, halal_config, use_halal_notify_dir

        if args.command in HALAL_REFUSED:
            print(f"« {args.command} » n'existe pas en mode halal : il ne traite ni commandes Telegram ni trades manuels.")
            return 2
        use_halal_notify_dir()
        cfg = halal_config()
    else:
        cfg = load_config()
    logging.basicConfig(level=logging.DEBUG if args.verbose else getattr(logging, cfg.log_level, logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if args.command == "flush-outbox":
        from .notify import flush_outbox

        print(f"{flush_outbox()} notification(s) envoyée(s).")
        return 0
    eng = HalalEngine(cfg) if args.halal else Engine(cfg)

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
        if args.day in ("hier", "yesterday"):
            day = eng.summary_day(utcnow().replace(hour=0))
        elif args.day in ("aujourd'hui", "today"):
            day = datetime.now(eng.tz).date()
        else:
            day = date.fromisoformat(args.day) if args.day else None
        if not eng.summary(day, force=args.force):
            print("Résumé déjà envoyé pour ce jour : rien à renvoyer (--force pour le renvoyer).")
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
        res = eng.backtest(days=min(60, max(2, args.days)), asset_keys=args.asset, send=args.send, offline=args.offline)
        if not res:
            print("Backtest impossible : aucune donnée récupérée.")
            return 1
        print(DISCLAIMER)
    elif args.command == "fetch-data":
        out = eng.fetch_data(days=min(60, max(2, args.days)), asset_keys=args.asset)
        print(json.dumps(out, ensure_ascii=False))
        if not out:
            return 1
    elif args.command == "manual":
        if not args.asset or not args.direction:
            print("Usage : python run.py manual --asset <actif> --direction long|short [--tp X] [--sl Y] [--note ...]")
            return 2
        sig = eng.manual(args.asset[0], args.direction, note=args.note, take_profit=args.tp, stop_loss=args.sl)
        print(json.dumps(sig.to_dict(), ensure_ascii=False, indent=2))
    elif args.command == "stop":
        try:
            res = eng.stop_trade(args.signal)
        except (ValueError, RuntimeError) as exc:
            print(f"Arrêt impossible : {exc}")
            return 1
        row = res["row"]
        print(f"Trade {res['signal']['id']} arrêté à {res['signal']['meta']['manual_exit']['price']}"
              + (f" : {row['pnl']:+.2f} {eng.portfolio.data.get('currency', '$')}" if row else ""))
    elif args.command == "topstep":
        # --note : « pris <id|actif> [micros] », « sortie <id|actif> [prix] », « retirer <id> », « journal … », « risque 0.5 » (% de la balance) ; vide = état du compte
        from .messages import strip_html
        words = (args.note or "").split()
        action = words[0].lower() if words else "topstep"
        cmd = {"add": "pris", "remove": "retirer"}.get(action, action)
        if cmd not in ("pris", "sortie", "retirer", "journal", "risque", "reset", "nouveau"):
            cmd, words = "topstep", [""] + words
        if cmd in ("reset", "nouveau"):
            cmd, words = "topstep", ["", "reset"]
        if cmd == "risque":
            cmd, words = "topstep", ["", "risque"] + words[1:]
        try:
            text = eng.topstep_command(cmd, words[1:])
        except (ValueError, KeyError, RuntimeError) as exc:
            print(f"Topstep : {exc}")
            return 1
        notify(text, html=True)
        print(strip_html(text))
    elif args.command == "check-data":
        out = eng.check_data()
        print(json.dumps(out, ensure_ascii=False, indent=2))
        if any("error" in v for v in out.values()):
            return 1
    elif args.command == "portfolio":
        if args.balance:
            eng.set_balance(args.balance, args.risk)
        print(eng.portfolio.format_summary())
    elif args.command == "commands":
        print(f"{eng.process_commands()} commande(s) traitée(s).")
    elif args.command == "propose":
        if not args.asset:
            print("Usage : python run.py propose --asset <actif>")
            return 2
        res = eng.propose(args.asset[0])
        print(res["text"])
    elif args.command == "ui":
        from .ui import serve

        serve(eng, port=args.port)
    elif args.command == "report":
        print(eng.write_report())
    elif args.command == "learn":
        adj = eng._relearn()
        eng.write_report()
        print("\n".join(adj.get("notes", [])))
    elif args.command == "guide":
        eng.send_help()
    elif args.command == "test-notify":
        notify(f"🔔 Test de notification du Trading-Bot — {utcnow():%d/%m/%Y %H:%M} UTC.\n"
               "Si vous lisez ceci sur Telegram/Discord, les notifications sont opérationnelles.")
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
