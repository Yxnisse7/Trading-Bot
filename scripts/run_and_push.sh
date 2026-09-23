#!/usr/bin/env bash
# Exécute une commande du bot puis enregistre l'état dans le dépôt, de façon sûre face aux
# exécutions concurrentes : on part toujours de l'état distant le plus récent, et si le push est
# refusé (quelqu'un a poussé entre-temps), on rejoue la commande depuis l'état frais.
# Les notifications sont mises en attente et envoyées seulement après un push réussi
# (exactement une fois, même après un rejeu).
set -euo pipefail

# Après l'envoi, les numéros des messages Telegram (pour que l'issue d'un trade réponde à son signal)
# sont enregistrés par un petit commit à part ; s'il échoue, seul le fil de réponse est perdu.
# (mode halal : TRADING_BOT_DATA_DIR=data/halal, ses messages ont leur propre fichier)
IDS_FILE="${TRADING_BOT_DATA_DIR:-data}/telegram_messages.json"
save_message_ids() {
  if [ -n "$(git status --porcelain "$IDS_FILE" 2>/dev/null)" ]; then
    git add "$IDS_FILE"
    git commit -q -m "bot: numéros des messages Telegram" || return 0
    git push -q origin "HEAD:$BRANCH" || echo "Numéros des messages non enregistrés (dépôt modifié entre-temps)."
  fi
}
BRANCH="${GITHUB_REF_NAME:-main}"
export TRADING_BOT_OUTBOX="${TRADING_BOT_OUTBOX:-${RUNNER_TEMP:-/tmp}/outbox.jsonl}"
git config user.name "trading-bot[actions]"
git config user.email "actions@users.noreply.github.com"

for attempt in 1 2 3 4; do
  rm -f "$TRADING_BOT_OUTBOX"
  git fetch -q origin "$BRANCH"
  git reset -q --hard "origin/$BRANCH"
  echo "== tentative $attempt : $*"
  "$@"
  git add data/
  # copies publiées sur le site (docs/halal n'existe qu'après le premier passage du mode halal)
  for p in docs/dashboard.json docs/portfolio.json docs/live docs/halal; do
    if [ -e "$p" ]; then git add "$p"; fi
  done
  if git diff --cached --quiet; then
    echo "Aucun changement d'état."
    python run.py flush-outbox
    save_message_ids
    exit 0
  fi
  git commit -q -m "bot: état $(date -u +'%Y-%m-%d %H:%M UTC')"
  if git push -q origin "HEAD:$BRANCH"; then
    python run.py flush-outbox
    save_message_ids
    exit 0
  fi
  echo "Push refusé (état distant modifié entre-temps) : rejeu depuis l'état frais."
  sleep $((attempt * 2))
done
echo "Impossible d'enregistrer l'état après 4 tentatives." >&2
exit 1
