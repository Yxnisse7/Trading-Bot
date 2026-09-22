#!/usr/bin/env bash
# Backtest hebdomadaire : 60 jours de bougies 5 min fraîches, stratégie rejouée avec les réglages
# actuels. Les trades obtenus remplacent ceux du backtest précédent dans l'apprentissage.
# Les bougies brutes (~7 Mo) ne sont pas réenregistrées chaque semaine dans le dépôt.
set -euo pipefail
python run.py fetch-data --days 60
python run.py backtest --days 60 --offline
python run.py learn          # les poids tiennent compte du nouveau backtest sans attendre
git checkout -- data/candles 2>/dev/null || true
