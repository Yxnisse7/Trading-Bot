#!/usr/bin/env bash
# Backtest hebdomadaire. Les bougies 5 min s'accumulent de semaine en semaine : Yahoo n'en donne
# que 60 jours, l'historique complet est gardé hors du dépôt (release GitHub « candles », fichier
# candles.tar.gz), repris ici, complété des 60 derniers jours, puis resauvegardé. La stratégie est
# ensuite rejouée sur jusqu'à BACKTEST_DAYS jours (180 par défaut) : bien plus de trades pour apprendre.
# Les bougies brutes ne sont jamais enregistrées dans le dépôt.
set -euo pipefail
TAG=candles
DAYS="${BACKTEST_DAYS:-180}"
KEEP="${CANDLES_KEEP_DAYS:-400}"
TMP="$(mktemp -d)"

if command -v gh >/dev/null && gh release download "$TAG" --pattern candles.tar.gz --dir "$TMP" 2>/dev/null; then
  tar xzf "$TMP/candles.tar.gz" -C data/candles
  echo "Historique des bougies repris ($(du -h "$TMP/candles.tar.gz" | cut -f1))"
else
  echo "Pas encore d'historique gardé : départ sur les bougies du dépôt"
fi

python run.py fetch-data --days 60
python run.py trim-candles --days "$KEEP"

if command -v gh >/dev/null; then
  rm -f "$TMP/candles.tar.gz"
  tar czf "$TMP/candles.tar.gz" -C data/candles .
  gh release view "$TAG" >/dev/null 2>&1 || gh release create "$TAG" --prerelease \
    --title "Historique des bougies 5 min" \
    --notes "Bougies 5 min accumulées chaque dimanche par le backtest hebdomadaire (données de marché publiques). Ne pas supprimer : c'est la mémoire longue du backtest."
  gh release upload "$TAG" "$TMP/candles.tar.gz" --clobber || echo "Sauvegarde de l'historique impossible cette semaine"
fi

python run.py backtest --days "$DAYS" --offline
python run.py learn          # les poids tiennent compte du nouveau backtest sans attendre
git checkout -- data/candles 2>/dev/null || true
git clean -fdq data/candles 2>/dev/null || true
# chances de réussir le Combine Topstep sur les nouveaux trades (moteur node, installé par le workflow)
python run.py topstep-odds || echo "Chances Topstep non recalculées cette semaine"
# tendance mensuelle (essai 11) : cours journaliers des 16 ETF, positions du mois suivies en ombre
python run.py trend-daily --refresh || echo "Tendance mensuelle non recalculée cette semaine"
