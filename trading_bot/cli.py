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


HALAL_REFUSED = {"manual", "propose", "commands", "guide", "ui", "loop", "fetch-data", "topstep", "invest", "backup", "fetch-history", "backtest-setups", "strategy-lab", "invest-review", "topstep-odds", "drift-reference", "donchian-day", "intraday-gold", "multi-trend", "trend-daily", "macro-drift"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Générateur de signaux de scalping (NQ, BTC, XAU) — données gratuites")
    p.add_argument("command", choices=["scan", "track", "tick", "summary", "stats", "loop", "status", "test-notify", "backtest", "report", "fetch-data", "manual", "propose", "ui", "commands", "portfolio", "guide", "learn", "flush-outbox", "check-data", "stop", "topstep", "trim-candles", "invest", "backup", "fetch-history", "backtest-setups", "strategy-lab", "invest-review", "topstep-odds", "drift-reference", "donchian-day", "intraday-gold", "multi-trend", "trend-daily", "macro-drift"])
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
    p.add_argument("--refresh", action="store_true", help="multi-trend : retélécharger les bougies de 1 h Yahoo")
    p.add_argument("--rebuild-donchian", action="store_true", help="topstep-odds : recalculer les R de donchian or sur l'historique long")
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
    elif args.command == "donchian-day":
        # essai 8 (HYPOTHESES.md) : donchian_1h fermé chaque jour à 15:00 heure de Chicago, règle fixée d'avance
        from . import strategies as sl
        from .providers import history as hist
        from .topstep import FEES, PRODUCTS

        split = int(datetime(2025, 9, 28, tzinfo=timezone.utc).timestamp())
        out = {"essai": 8, "strategy": "donchian_day", "split": "2025-09-28", "n_trials": 74, "cells": {}}
        for key in ("gold", "nasdaq", "sp500", "bitcoin"):
            asset = eng.cfg.assets[key]
            candles = eng.store.load_history(key)
            if key in hist.BINANCE:
                candles = sorted({c.ts: c for c in candles + eng.store.load_candles(key)}.values(), key=lambda c: c.ts)
            if not candles:
                continue
            tr = [t for t in sl.donchian_day(candles, key) if t.reason != "fin des données"]
            fee = FEES.get(key)
            tcost = (sum(fee), PRODUCTS[key][1]) if fee and key in PRODUCTS else None
            disc = sl.evaluate(tr, asset.cost_pct, tcost, start_ts=split)
            conf = sl.evaluate(tr, asset.cost_pct, tcost, end_ts=split)
            both = sl.evaluate(tr, asset.cost_pct, tcost)
            ok_d, ok_c = sl.discovery_pass(disc), sl.confirmation_pass(conf)
            status = ("prouvé" if sl.proven(both, out["n_trials"]) else "validé") if ok_d and ok_c else (
                "écarté (découverte)" if not ok_d else "écarté (confirmation)")
            reasons = {}
            for t in tr:
                reasons[t.reason] = reasons.get(t.reason, 0) + 1
            out["cells"][key] = {"asset": key, "asset_label": asset.label, "discovery": disc, "confirmation": conf,
                                 "all": both, "status": status, "robust": sl.robust_check(tr, asset.cost_pct, tcost, split),
                                 "exits": reasons}
            d, c, a = disc["net"], conf["net"], both["net"]
            print(f"{key:8s} découverte n={disc['n']:4d} {d['mean_r']} PF {d['profit_factor']} moitiés "
                  f"{disc['first_half']['mean_r']}/{disc['second_half']['mean_r']} | confirmation n={conf['n']:4d} "
                  f"{c['mean_r']} PF {c['profit_factor']} | 24 mois n={both['n']} {a['mean_r']} ± {a['se']} → {status} "
                  f"| sorties {reasons}", flush=True)
        out["updated_at"] = iso(utcnow())
        eng.store._write(eng.store.dir / "essai8.json", out)
    elif args.command == "macro-drift":
        # essai 12 (HYPOTHESES.md) : la réaction du marché aux annonces continue-t-elle jusqu'à la fin de séance ?
        from . import macro_drift
        res = macro_drift.run(eng.store)
        for k, a in res["assets"].items():
            if "all" not in a:
                print(k, a)
                continue
            s1, s2, al = a["year1"], a["year2"], a["all"]
            print(f"{k:7s} {al['n']} annonces : {al['mean']} ATR (t {al['t']}, gagnants {al.get('win_rate')}) | "
                  f"an 1 {s1['mean']} · an 2 {s2['mean']} | fortes {a['strong']['mean']} (n {a['strong']['n']}) | "
                  f"lendemain {a['next_day']['mean']} | NFP {a['by_kind']['nfp']['mean']} CPI {a['by_kind']['cpi']['mean']} "
                  f"FOMC {a['by_kind']['fomc']['mean']} → retenu {a['kept']}")
        f = res.get("donchian_filter")
        if f:
            print(f"Donchian or les jours d'annonce : dans le sens {f['aligned']} | contre {f['opposed']} | "
                  f"autres jours {f['other_days']} → filtre proposé {f['propose_filter']}")
        eng.store._write(eng.store.dir / "essai12.json", res)
    elif args.command == "trend-daily":
        # essai 11 (HYPOTHESES.md) : tendance journalière sur 16 marchés depuis 2007 ; le momentum 12 mois retenu
        # est suivi en ombre (poids annoncés chaque mois, résultat réel du mois écoulé)
        from . import trend_daily
        shadow = eng.store.trend_shadow()
        res = trend_daily.run(refresh=args.refresh, shadow=shadow)
        a, b = res["donchian_55_20"], res["momentum_12m"]
        print(f"A Donchian 55/20 : {a['first_half']['mean_r']} R puis {a['second_half']['mean_r']} R → retenu {a['kept']}")
        print(f"B momentum 12 mois : Sharpe {b['first_half'].get('sharpe')} puis {b['second_half'].get('sharpe')} → retenu {b['kept']}")
        eng.store._write(eng.store.dir / "essai11.json", res)
        if shadow:
            eng.store.save_trend_shadow(shadow)
            cur = shadow["months"][-1]
            print(f"mois {cur['month']} : " + ", ".join(f"{m} {w:+.0%}" for m, w in sorted(cur["weights"].items(), key=lambda x: -abs(x[1]))))
        eng.write_report()
    elif args.command == "multi-trend":
        # essai 10 (HYPOTHESES.md) : donchian_day sur 17 autres contrats CME (+ l'or en contrôle)
        from . import multi_trend
        res = multi_trend.run(refresh=args.refresh)
        for k, c in res["markets"].items():
            if "discovery" not in c:
                print(f"{c['label']:28s} {c['status']}")
                continue
            d, f = c["discovery"]["net"], c["confirmation"]["net"]
            print(f"{c['label']:28s} {c['trades_per_day']:4.2f}/j | découverte n={c['discovery']['n']:3d} {d['mean_r']} PF {d['profit_factor']} "
                  f"| confirmation n={c['confirmation']['n']:3d} {f['mean_r']} PF {f['profit_factor']} | stop médian {c['median_stop_usd']} $ "
                  f"jouable 500 $ {c['tradable']['500']} | sauts retirés {c['trades_removed_jumps']} → {c['status']}", flush=True)
        port = res.get("portfolio")
        if port:
            print(f"portefeuille {port['markets']} : {port['n']} trades, {port['trades_per_day']}/j, {port['mean_r']} R "
                  f"(confirmation {port['mean_r_confirmation']}, découverte {port['mean_r_discovery']}) → retenu {port['kept']}")
            for x in port.get("combine", []):
                print(f"   risque {x['risk']:.0f} $ : réussite {x['pass']:.0%} (témoin {x['witness_pass']:.0%}), en 2 semaines "
                      f"{x['pass10']:.0%} (témoin {x['witness_pass10']:.0%}), financé en {x['funded_days']}, retrait +{x['first_payout']} j")
        else:
            print("aucun marché validé et jouable : pas de portefeuille")
        eng.store._write(eng.store.dir / "essai10.json", res)
    elif args.command == "intraday-gold":
        # essai 9 (HYPOTHESES.md) : 3 stratégies intraday sur l'or, règles fixées d'avance ; réussite du Combine
        # en 10 jours de bourse comparée à leur témoin sans avantage
        from . import strategies as sl
        from . import topstep_odds
        from .topstep import FEES, PRODUCTS

        split = int(datetime(2025, 9, 28, tzinfo=timezone.utc).timestamp())
        asset = eng.cfg.assets["gold"]
        candles = eng.store.load_history("gold")
        tcost = (sum(FEES["gold"]), PRODUCTS["gold"][1])
        out = {"essai": 9, "split": "2025-09-28", "n_trials": 77, "cells": {}}
        series = sl._Series(candles)
        runners = {"donchian_15m_day": lambda: sl.donchian_15m_day(candles, "gold"),
                   "donchian_30m_day": lambda: sl.donchian_30m_day(candles, "gold"),
                   "comex_orb": lambda: sl.comex_orb(series, "gold")}
        start = datetime.fromtimestamp(candles[0].ts, timezone.utc)
        end = datetime.fromtimestamp(candles[-1].ts, timezone.utc)
        for name, run in runners.items():
            tr = sorted((t for t in run() if t.reason != "fin des données"), key=lambda t: t.entry_ts)
            disc = sl.evaluate(tr, asset.cost_pct, tcost, start_ts=split)
            conf = sl.evaluate(tr, asset.cost_pct, tcost, end_ts=split)
            both = sl.evaluate(tr, asset.cost_pct, tcost)
            ok_d, ok_c = sl.discovery_pass(disc), sl.confirmation_pass(conf)
            status = ("prouvé" if sl.proven(both, out["n_trials"]) else "validé") if ok_d and ok_c else (
                "écarté (découverte)" if not ok_d else "écarté (confirmation)")
            rs = [round(sl.trade_rs(t, 0.0, tcost)["net_topstep"], 4) for t in tr]
            cell = {"strategy": name, "discovery": disc, "confirmation": conf, "all": both, "status": status,
                    "robust": sl.robust_check(tr, asset.cost_pct, tcost, split),
                    "holding": topstep_odds.holding_stats(tr),
                    "trades_per_day": round(len(rs) / topstep_odds.weekdays_between(start, end), 3)}
            if rs and len(rs) >= 30:
                m = sum(rs) / len(rs)
                prof = {"key": name, "label": name, "rSeries": rs, "tradesPerDay": cell["trades_per_day"]}
                wit = {"key": "witness", "label": "témoin", "rSeries": [round(r - m, 4) for r in rs],
                       "tradesPerDay": cell["trades_per_day"]}
                try:
                    sim = topstep_odds.run_engine([prof, wit], risks=(250.0, 500.0, 750.0), paths=4000)
                    by = {p["key"]: p for p in sim["profiles"]}
                    cell["combine"] = [{"risk": a["risk"], "pass": a["pass"], "pass10": a["pass10"],
                                        "witness_pass": b["pass"], "witness_pass10": b["pass10"],
                                        "funded_days": a.get("fundedDays")}
                                       for a, b in zip(by[name]["risks"], by["witness"]["risks"])]
                    best = max(cell["combine"], key=lambda x: x["pass10"] - x["witness_pass10"])
                    cell["fast"] = status in ("validé", "prouvé") and best["pass10"] >= best["witness_pass10"] + 0.10
                except Exception as exc:  # noqa: BLE001 — le verdict de l'essai 3 reste valable sans le moteur
                    cell["combine_error"] = str(exc)
            out["cells"][name] = cell
            d, c, a = disc["net"], conf["net"], both["net"]
            print(f"{name:17s} {cell['trades_per_day']} trades/jour | découverte n={disc['n']} {d['mean_r']} PF {d['profit_factor']} "
                  f"moitiés {disc['first_half']['mean_r']}/{disc['second_half']['mean_r']} | confirmation n={conf['n']} "
                  f"{c['mean_r']} PF {c['profit_factor']} | 24 mois {a['mean_r']} ± {a['se']} → {status}", flush=True)
            for x in cell.get("combine", []):
                print(f"   risque {x['risk']:.0f} $ : réussite {x['pass']:.0%} (témoin {x['witness_pass']:.0%}), "
                      f"en 2 semaines {x['pass10']:.0%} (témoin {x['witness_pass10']:.0%}), financé en {x['funded_days']}", flush=True)
        out["updated_at"] = iso(utcnow())
        eng.store._write(eng.store.dir / "essai9.json", out)
    elif args.command == "drift-reference":
        # essai 7 : R du backtest de 24 mois des stratégies en ombre, figés comme référence (historique long requis)
        from . import drift
        ref = drift.build_reference(eng.store, eng.cfg)
        if not ref:
            print("pas d'historique long (python run.py fetch-history)")
        else:
            eng.store.save_drift_reference(ref)
            for k, v in ref.items():
                if isinstance(v, dict):
                    rs = v["rSeries"]
                    print(f"{k} : {len(rs)} trades, {sum(rs) / max(1, len(rs)):+.3f} R moyen, {v['period']}")
            eng.check_drift()
    elif args.command == "topstep-odds":
        # chances de réussir le Combine Topstep 50K (Monte Carlo LuxAlgo, outil d'information, aucun ordre)
        from . import topstep_odds
        if args.rebuild_donchian:
            candles = eng.store.load_history("gold")
            if candles:
                topstep_odds.rebuild_strategies(candles)
            else:
                print("pas d'historique long de l'or (python run.py fetch-history --asset gold)")
        res = topstep_odds.build()
        topstep_odds.publish(res)
        for prof in res["profiles"]:
            st = prof["stats"]
            print(f"{prof['label']} : {st['n']} trades, {st['mean_r']} R moyen")
            for r in prof["risks"]:
                print(f"  risque {r['risk']:.0f} $ : réussite {r['pass']:.1%} par tentative "
                      f"[{r['ci'][0]:.1%}-{r['ci'][1]:.1%}], {r['attempts']:.1f} tentatives, coût {r['cost']:.0f} $")
        # même calcul sur les comptes 50K des autres prop firms (annuaire public de LuxAlgo)
        try:
            firms = topstep_odds.build_firms()
            topstep_odds.publish(firms, name="firms.json")
            print(f"prop firms : {len(firms['challenges'])} comptes comparés ({len(firms['errors'])} erreurs), "
                  f"écartées : {', '.join(firms['excluded']) or 'aucune'}")
        except Exception as exc:  # noqa: BLE001 — l'annuaire est un service externe : Topstep reste publié
            print(f"comparaison des prop firms impossible : {exc}")
    elif args.command == "invest-review":
        # revue de la stratégie d'investissement halal (essai 6 de HYPOTHESES.md) : témoins, variantes,
        # risque du portefeuille complet, contrôle charia AAOIFI ; publié pour la page Investir
        from . import invest_review
        res = invest_review.run()
        invest_review.publish(res)
        for key in ("pocket", "pepites"):
            r = res.get(key)
            if not r:
                print(f"{key} : pas assez d'historique")
                continue
            ew = r["equal_weight"] or {}
            print(f"{key} : règle {r['rule']['cagr']:+.1%}/an (chute max {r['rule']['max_dd']:.0%}), poids égal "
                  f"{ew.get('cagr', float('nan')):+.1%}/an, mieux que {r['random']['rule_beats_share']:.0%} des tirages, "
                  f"apport démontré : {'oui' if r['edge_proven'] else 'non'}"
                  + "".join(f" ; {n} {v['cagr']:+.1%}/an chute {v['max_dd']:.0%} → {'adoptée' if v['adopt'] else 'non'}"
                            for n, v in r["variants"].items()))
        verdicts = [v.get("verdict") for v in res["current"]["aaoifi"].values()]
        print(f"Contrôle AAOIFI : {verdicts.count('conforme')} conformes sur {len(verdicts)}")
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
    elif args.command == "strategy-lab":
        # essai 3 (HYPOTHESES.md) : 8 stratégies publiées × chaque actif, découverte puis confirmation
        from . import strategies as sl
        from .providers import history as hist
        from .topstep import FEES, PRODUCTS

        split = int(datetime(2025, 9, 28, tzinfo=timezone.utc).timestamp())
        n_trials = (len(sl.STRATEGIES) - len(sl.INFO_ONLY)) * len(eng.cfg.assets)
        out = {"split": "2025-09-28", "n_trials": n_trials, "strategies": sl.STRATEGIES, "cells": {}}
        for key, asset in eng.cfg.assets.items():
            if args.asset and key not in args.asset:
                continue
            candles = eng.store.load_history(key)
            if key in hist.BINANCE:                                    # même source : comble le dernier mois
                candles = sorted({c.ts: c for c in candles + eng.store.load_candles(key)}.values(), key=lambda c: c.ts)
            if not candles:
                continue
            trades = sl.run_all(key, candles)
            fee = FEES.get(key)
            tcost = (sum(fee), PRODUCTS[key][1]) if fee and key in PRODUCTS else None
            for strat in sl.STRATEGIES:
                tr = [t for t in trades if t.strategy == strat]
                disc = sl.evaluate(tr, asset.cost_pct, tcost, start_ts=split)
                conf = sl.evaluate(tr, asset.cost_pct, tcost, end_ts=split)
                both = sl.evaluate(tr, asset.cost_pct, tcost)
                need = sl.MIN_TRADES.get(strat, 30)
                cand = sl.discovery_pass(disc, need)
                robust = None
                if strat in sl.ROBUST_ONLY:
                    robust = sl.robust_check(tr, asset.cost_pct, tcost, split)
                if strat in sl.INFO_ONLY:
                    status = "pour information"
                elif robust is not None:
                    status = "validé (à suivre en ombre)" if robust["passed"] else "écarté (essai 5)"
                elif not cand:
                    status = "écarté (découverte)"
                elif conf["n"] == 0:
                    status = "candidat : confirmation à venir"
                elif not sl.confirmation_pass(conf, need):
                    status = "écarté (confirmation)"
                else:
                    status = "prouvé" if sl.proven(both, n_trials) else "validé"
                out["cells"][f"{strat}:{key}"] = {"strategy": strat, "asset": key, "asset_label": asset.label,
                                                  "discovery": disc, "confirmation": conf, "all": both, "status": status,
                                                  **({"robust": robust} if robust is not None else {})}
                d, c = disc["net"], conf["net"]
                print(f"{strat:16s} {key:9s} découverte n={disc['n']:4d} {d['mean_r']} PF {d['profit_factor']} | "
                      f"confirmation n={conf['n']:4d} {c['mean_r']} PF {c['profit_factor']} → {status}", flush=True)
        out["updated_at"] = iso(utcnow())
        eng.store.save_strategies(out, merge=bool(args.asset))
        eng.write_report()
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
