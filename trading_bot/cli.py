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
from datetime import date, datetime, timezone

from .config import DISCLAIMER, load_config
from .models import iso, utcnow
from .notify import notify
from .engine import Engine
from .learning import analyze
from .signals import format_signal


HALAL_REFUSED = {"manual", "propose", "commands", "guide", "ui", "loop", "fetch-data", "topstep", "invest", "backup", "fetch-history", "backtest-setups"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Générateur de signaux de scalping (NQ, BTC, XAU) — données gratuites")
    p.add_argument("command", choices=["scan", "track", "tick", "summary", "stats", "loop", "status", "test-notify", "backtest", "report", "fetch-data", "manual", "propose", "ui", "commands", "portfolio", "guide", "learn", "flush-outbox", "check-data", "stop", "topstep", "trim-candles", "invest", "backup", "fetch-history", "backtest-setups"])
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
    p.add_argument("--risk", type=float, help="risque par trade en %% de la balance")
    p.add_argument("--candles", help="backup : archive des bougies (release « candles ») à inclure")
    p.add_argument("--months", type=int, default=12, help="fetch-history : profondeur de l'historique long en mois")
    p.add_argument("--older", action="store_true", help="fetch-history : remonter avant l'historique déjà gardé et fusionner")
    p.add_argument("--max-minutes", type=int, default=0, help="fetch-history : temps maximal par actif (0 = sans limite)")
    p.add_argument("--history", action="store_true", help="backtest-setups : sur l'historique long (data/history) plutôt que les bougies Yahoo")
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
    if args.command == "backup":
        # sauvegarde hebdomadaire : archive du dépôt (+ bougies) envoyée au propriétaire sur Telegram
        import tempfile
        from pathlib import Path

        from . import backup

        day = utcnow()
        path, summary = backup.build_archive(Path.cwd(), Path(tempfile.mkdtemp()), day,
                                             Path(args.candles) if args.candles else None)
        sent = backup.send_document(path, backup.caption(summary, day))
        print(f"Sauvegarde {path.name} : {summary['size'] / 1e6:.1f} Mo, {summary['files']} fichiers, "
              f"bougies {'incluses' if summary['candles'] else 'absentes'} — {'envoyée' if sent else 'NON envoyée'}.")
        return 0 if sent else 1
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
        # hors ligne, l'historique gardé peut dépasser les 60 jours de Yahoo
        res = eng.backtest(days=min(400 if args.offline else 60, max(2, args.days)), asset_keys=args.asset,
                           send=args.send, offline=args.offline)
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
        if cmd not in ("pris", "sortie", "retirer", "journal", "risque", "objectif", "reset", "nouveau"):
            cmd, words = "topstep", [""] + words
        if cmd in ("reset", "nouveau"):
            cmd, words = "topstep", ["", "reset"]
        if cmd == "objectif":
            cmd, words = "topstep", ["", "objectif"] + words[1:]
        if cmd == "risque":
            cmd, words = "topstep", ["", "risque"] + words[1:]
        try:
            text = eng.topstep_command(cmd, words[1:])
        except (ValueError, KeyError, RuntimeError) as exc:
            print(f"Topstep : {exc}")
            return 1
        notify(text, html=True)
        print(strip_html(text))
    elif args.command == "invest":
        # investissement halal à long terme : historique mensuel, statistiques, avis, actualités
        from . import invest
        data = invest.build()
        invest.publish(data)
        reminder = invest.revision_reminder(data, utcnow())
        if reminder:
            notify(reminder, html=True, buttons=[[("📅 Mon plan du mois", eng.cfg.site_url.rstrip("/") + "/investissement.html#plan-mois")]])
        ok = [p["key"] for p in data["products"] if p["stats"]]
        print(f"Investissement : {len(ok)} produits sur {len(data['products'])}, {len(data['news'])} actualités"
              + (f" ; indisponibles : {', '.join(data['errors'])}" if data["errors"] else ""))
    elif args.command == "fetch-history":
        # historique long (Binance pour les cryptos, Dukascopy pour le reste) dans data/history/
        from datetime import date

        from .providers import history as hist

        today = date.today()
        keys = args.asset or list(eng.cfg.assets)
        keys = sorted(keys, key=lambda k: k not in hist.BINANCE)        # Binance d'abord : rapide, sans limite
        for key in keys:
            hist.STATS.update(ok=0, absent=0, failed=0, throttled=0)
            ref = eng.store.load_candles(key)
            existing = eng.store.load_history(key) if args.older else []
            # --older : on remonte `--months` mois avant la plus ancienne bougie déjà gardée, puis on fusionne
            end = datetime.fromtimestamp(existing[0].ts, tz=timezone.utc).date() if existing else today
            if key in hist.BINANCE:
                candles = hist.fetch_binance(key, args.months, end)
            elif key in hist.DUKASCOPY:
                candles = hist.fetch_dukascopy(key, args.months * 31, end, ref[-1].close if ref else None,
                                               deadline=time.time() + args.max_minutes * 60 if args.max_minutes else None)
            else:
                continue
            if existing:
                candles = sorted({c.ts: c for c in candles + existing}.values(), key=lambda c: c.ts)
            if candles:
                eng.store.save_history(key, candles)
            print(key, hist.SOURCE_LABEL.get(key, ""), json.dumps(hist.check_candles(candles) | {"fichiers": dict(hist.STATS)},
                                                                ensure_ascii=False), flush=True)
    elif args.command == "backtest-setups":
        # setups pré-enregistrés (HYPOTHESES.md) jugés sur leurs critères d'abandon
        from . import setups

        load = eng.store.load_history if args.history else eng.store.load_candles
        candles = {k: load(k) for k in eng.cfg.assets}
        candles = {k: v for k, v in candles.items() if v}
        if not candles:
            print("Aucune bougie : lancez d'abord fetch-history (ou fetch-data).")
            return 1
        source = "historique long (Binance, Dukascopy CFD)" if args.history else "bougies Yahoo / Binance récentes"
        out = setups.evaluate(eng.cfg.assets, candles, source)
        out["updated_at"] = iso(utcnow())
        eng.store.save_setups(out, history=args.history)
        for key, v in out["setups"].items():
            t = v["total"]
            print(f"{v['label']} [{source}] : {t['n']} trades, {t['mean_r']} R net, facteur de profit "
                  f"{t['profit_factor']} → {v['verdict']}")
            for check, ok in v["checks"].items():
                print(f"   {'✓' if ok else '✗'} {check}")
        eng.write_report()
    elif args.command == "trim-candles":
        # garde les `--days` derniers jours de bougies enregistrées (historique du backtest)
        for key in eng.cfg.assets:
            candles = eng.store.load_candles(key)
            if candles:
                cutoff = candles[-1].ts - args.days * 86400
                eng.store.save_candles(key, [c for c in candles if c.ts >= cutoff])
                print(f"{key} : {sum(1 for c in candles if c.ts >= cutoff)} bougies gardées")
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
