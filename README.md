# Trading-Bot — signaux de scalping (Nasdaq, Bitcoin, Or) à coût zéro

Générateur de **signaux courts (~1 h)** sur trois actifs :

| Actif | Source principale | Repli |
|---|---|---|
| Nasdaq 100 (futures `NQ=F`) | Yahoo Finance (API chart publique) | — |
| Bitcoin (`BTC/USD`) | Binance API publique (`BTCUSDT`) | Yahoo `BTC-USD`, CoinGecko (prix) |
| Or (`XAU/USD` via `GC=F`) | Yahoo Finance | — |

Actualité : flux RSS gratuits (MarketWatch, CNBC, Yahoo Finance, CoinDesk, Cointelegraph, Kitco, FXStreet)
+ calendrier macro (`data/macro_calendar.json`, NFP détecté automatiquement).

> ⚠️ **Avertissement.** Les signaux sont générés automatiquement à partir de données publiques et
> d'une analyse algorithmique. Ils ne constituent **pas un conseil financier** et aucune stratégie ne
> garantit un gain. Le bot **n'exécute aucun ordre** : vous décidez et exécutez vous-même.
> **Validez d'abord en paper trading** (compte simulé) avant tout passage en argent réel.

## Philosophie

- **Qualité avant quantité** : un signal n'est émis que si **au moins 3 critères convergent**
  (tendance 5 m / 15 m / 1 h, RSI en momentum, MACD en expansion, proximité d'un niveau clé,
  volume anormal) et que le score pondéré atteint la confiance *moyen* ou *fort*.
- **Abstention par défaut** : marché indécis, tendance 15 m contraire, niveau clé bloquant, volatilité
  trop faible ou anormale, actualité à risque, fenêtre de blackout macro → **aucun signal**.
- **Maximum 3 signaux / actif / jour**, 1 seul signal ouvert par actif, 60 min de refroidissement.
- **TP / SL calibrés sur la volatilité réelle** : range horaire moyen des 24 dernières heures
  (bougies 5 m). TP = 60 % du range, SL = 40 % (ratio ≥ 1,2), TP borné entre 25 % et 90 % du
  range pour rester atteignable en ~1 h sans être noyé dans le bruit. Si aucune cible réaliste
  n'existe, pas de signal.

## Fonctionnement

```
python run.py scan      # analyse + propose des signaux (si convergence)
python run.py track     # vérifie les signaux ouverts : TP / SL / expiration (1 h)
python run.py tick      # track puis scan (toutes les ~15 min) — commande planifiée
python run.py summary   # résumé quotidien (jour + cumulé, enseignements, ajustements)
python run.py stats     # statistiques détaillées de l'historique
python run.py status    # signaux ouverts
python run.py loop      # boucle locale : un tick toutes les 5 min
```

### Suivi automatique
- À chaque passage (5 min en local, 15 min sur GitHub Actions), le bot récupère les bougies 1 m
  depuis l'émission du signal et le prix courant.
- TP touché / SL touché (si les deux dans la même bougie : SL, par prudence) / **expiré** après 1 h
  (clôturé au prix courant pour les statistiques).
- Notification immédiate avec l'heure exacte, le prix de clôture, le P&L et la durée réelle.
- Chaque issue est enregistrée dans `data/history.json` (horodatages, résultat, durée, critères).

### Apprentissage
`trading_bot/learning.py` analyse l'historique par critère, actif, direction, confiance, tranche horaire
et contexte d'actualité. Un critère dont le taux de réussite est < 40 % sur ≥ 10 trades voit son poids
réduit ; > 60 % → augmenté. Les tranches horaires < 30 % sont évitées. Les poids sont stockés dans
`data/adjustments.json` et appliqués aux scans suivants.

### Résumé quotidien
Nombre de signaux, gagnants / perdants / expirés, taux de réussite du jour et cumulé, ce qui a
fonctionné ou non, ajustements prévus, rappel des limites.

## Installation locale

```bash
pip install -r requirements.txt        # uniquement `requests`
cp config.example.json config.json     # optionnel : ajustez les seuils
python run.py scan -v
python run.py loop                     # laisse tourner en tâche de fond
```

Tests : `pip install -r requirements-dev.txt && python -m pytest -q`

## Notifications gratuites (optionnel)

| Variable d'environnement | Service |
|---|---|
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Bot Telegram (créez-le via @BotFather) |
| `DISCORD_WEBHOOK_URL` | Webhook Discord |

Sans configuration, les messages sont affichés en console et journalisés dans `data/notifications.log`.

## Planification sans infrastructure : GitHub Actions

Trois workflows sont fournis dans `.github/workflows/` :

- `bot.yml` : `tick` toutes les 15 min (suivi des signaux ouverts puis scan) ; l'état
  (`data/*.json`) est commité dans le dépôt pour persister entre deux exécutions.
- `daily-summary.yml` : résumé quotidien à 22:05 UTC.
- `tests.yml` : tests à chaque push.

Ajoutez les secrets Telegram / Discord dans *Settings → Secrets and variables → Actions*.

**Coût.** Le cron est réglé sur 15 min car le dépôt est privé : le quota gratuit (2 000 min/mois)
ne couvre pas un tick toutes les 5 min. Le suivi TP/SL reste exact (il s'appuie sur les bougies 1 min
depuis l'émission du signal) mais la notification d'issue peut arriver avec jusqu'à 15 min de retard.
Pour un suivi toutes les 5 min, exécutez `python run.py loop` sur une machine locale, ou passez le
dépôt en public (minutes illimitées) et remettez `*/5`. Les crons GitHub sont exécutés « au mieux » :
un retard de quelques minutes est normal.

## Configuration

Valeurs par défaut dans `trading_bot/config.py`, surcharge via `config.json` (voir
`config.example.json`) : limites par jour, seuils de score, fractions TP/SL, sessions horaires
par actif (UTC), tolérance à l'actualité, fuseau d'affichage.

Calendrier macro : `data/macro_calendar.json` (heures UTC). Blackout 45 min avant / 30 min après
chaque événement `high`. Les 8 réunions FOMC et les 12 publications CPI de 2026 sont pré-remplies
(sources : federalreserve.gov, bls.gov) ; complétez avec BCE, PCE, etc. si besoin.

## Structure

```
run.py                      point d'entrée CLI
trading_bot/
  config.py                 paramètres + actifs
  models.py                 Candle, Signal
  indicators.py             SMA/EMA/RSI/MACD/ATR/pivots/range horaire (Python pur)
  analysis.py               évaluation multi-timeframe, score, confiance
  signals.py                construction TP/SL/RR et formatage
  tracker.py                résolution TP/SL/expiration
  learning.py               statistiques + ajustement des poids
  summary.py                résumé quotidien
  engine.py                 orchestration scan/track/summary/tick
  notify.py                 Telegram / Discord / console
  storage.py                persistance JSON
  providers/                yahoo, binance, coingecko, news (RSS + calendrier)
data/                       état persistant (signaux ouverts, historique, ajustements)
tests/                      tests unitaires (données synthétiques, sans réseau)
```
