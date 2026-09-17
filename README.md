# Trading-Bot — signaux de scalping (Nasdaq, S&P 500, Bitcoin, Ethereum, Or) à coût zéro

Générateur de **signaux courts (~1 h)** sur cinq actifs, à partir de **données gratuites**,
avec **suivi automatique** des issues, **apprentissage** sur l'historique, **backtest**,
**interface locale** et **résumé quotidien**. Le bot **n'exécute aucun ordre** : il propose,
vous décidez.

| Actif | Source principale | Repli |
|---|---|---|
| Nasdaq 100 (futures `NQ=F`) | Yahoo Finance (API chart publique) | — |
| S&P 500 (futures `ES=F`) | Yahoo Finance | — |
| Bitcoin (`BTC/USD`) | Binance API publique (`BTCUSDT`) | Yahoo `BTC-USD`, CoinGecko (prix) |
| Ethereum (`ETH/USD`) | Binance API publique (`ETHUSDT`) | Yahoo `ETH-USD` |
| Or (`XAU/USD` via `GC=F`) | Yahoo Finance | — |

Actualité : flux RSS gratuits (MarketWatch, CNBC, Yahoo Finance, CoinDesk, Cointelegraph, Kitco,
FXStreet) et calendrier macro (`data/macro_calendar.json` : FOMC et CPI 2026 pré-remplis, rapport
emploi US détecté automatiquement).

> ⚠️ **Avertissement.** Les signaux sont générés automatiquement à partir de données publiques et
> d'une analyse algorithmique. Ils ne constituent **pas un conseil financier** et aucune stratégie ne
> garantit un gain. **Validez d'abord en paper trading** (compte simulé) avant tout passage en argent
> réel. Vous seul décidez et exécutez vos trades.

## Philosophie

**Qualité avant quantité.** Un signal n'est émis que si **au moins 3 critères convergent** sur
9 évalués, avec un score pondéré suffisant (confiance *moyen* ou *fort*) :

| Critère | Ce qu'il vérifie |
|---|---|
| Tendance 5 min | EMA20 > EMA50 et prix au-dessus de l'EMA20 (inverse pour un short) |
| Tendance 15 min | EMA20 vs EMA50 |
| Tendance 1 h | Prix vs EMA20 sur 1 h |
| Force de tendance | ADX 15 min ≥ 18 et +DI / −DI dans le sens du trade |
| VWAP | Prix du bon côté du VWAP de la journée |
| RSI | RSI 5 min en zone de momentum sain (52–70 long, 30–48 short) |
| MACD | Histogramme du bon côté et en expansion sur 3 barres |
| Niveau clé | Proche d'un support (long) / d'une résistance (short), avec de la place vers la cible |
| Volume | Volume anormal (z-score ≥ 1,5) confirmant la dernière bougie |

**Abstention par défaut.** Aucun signal si : marché sans tendance (ADX < 18), critères
contradictoires, tendance 15 min ou directionnel ADX opposés, RSI extrême, volatilité trop faible
ou anormale (ATR instantané > 2,5 × la moyenne 24 h), actualité à risque, fenêtre de blackout
macro, ou faible probabilité statistique d'atteindre TP ou SL sous 1 h.

**TP / SL réalistes, calibrés sur la volatilité.**
- Base : range horaire moyen des 24 dernières heures (bougies 5 min).
- TP = 60 % du range, ramené devant le niveau clé le plus proche s'il est plus près.
- SL = 40 % du range, ou juste au-delà du niveau clé opposé s'il est proche, jamais sous 25 %.
- Ratio risque / rendement ≥ 1,2, TP borné entre 25 % et 90 % du range.
- **Test de faisabilité** : simulation Monte-Carlo (3 000 trajectoires sur la volatilité réalisée des
  4 dernières heures, sans dérive). Si la probabilité que TP ou SL soit touché en 1 h est inférieure
  à 35 %, le signal est refusé.

**Garde-fous de risque.**
- Maximum 5 signaux par actif et par jour, un seul signal ouvert par actif, 4 positions
  ouvertes au plus tous actifs confondus.
- Refroidissement de 30 min entre deux signaux, 60 min après un stop.
- Protection quotidienne : après 3 stops sur un actif, plus de signal ce jour-là.
- Sessions : Nasdaq et S&P 500 12 h–21 h UTC, Or 7 h–20 h UTC, Bitcoin et Ethereum en continu.
- Seules les bougies **clôturées** sont analysées (jamais la bougie en formation).

**Signaux fantômes (apprentissage accéléré).** Chaque setup qui a une direction et au moins
2 critères alignés mais qui ne passe pas le filtre de confiance est suivi **en silence** : mêmes
niveaux TP / SL, même suivi, mais aucune notification. Ces trades fantômes n'entrent pas dans vos
statistiques de signaux, ils alimentent uniquement les statistiques par critère et l'apprentissage,
ce qui multiplie les données disponibles sans vous inonder de messages. Les trades de backtest
alimentent aussi l'apprentissage (`learn_from_backtest`).

## Fonctionnement

```
python run.py scan         # analyse + propose des signaux (si convergence)
python run.py track        # vérifie les signaux ouverts : TP / SL / expiration (1 h)
python run.py tick         # track puis scan — commande planifiée
python run.py backtest     # rejoue la stratégie sur l'historique (--days 30, --asset bitcoin)
python run.py summary      # résumé quotidien (jour + cumulé, enseignements, ajustements)
python run.py report       # régénère data/REPORT.md
python run.py stats        # statistiques détaillées de l'historique (JSON)
python run.py status       # signaux ouverts
python run.py test-notify  # message de test Telegram / Discord
python run.py manual --asset bitcoin --direction long   # signal demandé, notifié et suivi
python run.py ui           # interface locale : http://127.0.0.1:8787
python run.py loop         # boucle locale : un tick toutes les 5 min
```

### Interface
`python run.py ui` sert une page simple et visuelle (`docs/index.html`) : indicateurs clés,
signaux ouverts, **résumé des derniers trades par indicateur** (taux de réussite contre hasard
attendu, poids appris, derniers trades), statistiques par actif, derniers trades, backtests et
notes d'apprentissage. Le bouton **« Demander un trade »** crée un signal manuel : le bot calibre
l'entrée, le TP et le SL sur la volatilité du moment, envoie la notification Telegram / Discord et
suit le trade comme les siens ; le résultat est comptabilisé à part (source « manuel »), ce qui
permet de comparer votre jugement à celui du bot.

Sans serveur local (page ouverte depuis GitHub Pages ou depuis le fichier), la page lit
`data/dashboard.json` en lecture seule et le bouton passe par GitHub Actions : renseignez une fois
propriétaire, dépôt et un jeton fine-grained limité à ce dépôt avec la permission *Actions :
lecture et écriture* (stocké uniquement dans votre navigateur). La demande déclenche le workflow
avec la commande `manual` ; la notification arrive en 1 à 2 minutes.

### Suivi automatique
- À chaque passage (5 min en local, 15 min sur GitHub Actions), le bot récupère les bougies 1 min
  depuis l'émission du signal et le prix courant.
- TP touché / SL touché (si les deux dans la même bougie : SL, par prudence) / **expiré** après 1 h
  (clôturé au prix courant pour les statistiques).
- Notification immédiate avec l'heure exacte, le prix de clôture, le P&L brut et net des coûts
  estimés, et la durée réelle.
- Chaque issue est enregistrée dans `data/history.json` (horodatages, résultat, durée, critères).

### Backtest
`python run.py backtest --days 30` rejoue la même logique (analyse, niveaux, politique de risque)
sur jusqu'à 60 jours de bougies 5 min, sans biais de futur : chaque signal est évalué sur les
bougies clôturées, son issue sur l'heure suivante. `python run.py fetch-data` enregistre
l'historique dans `data/candles/` pour des backtests reproductibles hors ligne (`--offline`).

Résultats : taux de réussite, **taux de réussite attendu par pur hasard** (SL / (TP + SL) : sans
aucun avantage, un TP à 60 % du range et un SL à 40 % donnent mécaniquement ~40 % de réussite),
**avantage** (écart entre les deux), P&L brut et **net des coûts estimés** (spread + commissions,
`cost_pct` par actif), espérance par trade, profit factor, pire série de stops, motifs de refus.
Les résultats sont enregistrés dans `data/backtests.json` et repris dans le rapport.

Limites : l'actualité n'est pas rejouée (non disponible historiquement), et en réel le signal
arrive jusqu'à 15 min après la clôture de la bougie analysée. Les résultats de backtest sont donc
**optimistes** par rapport au réel.

### Ce que disent les backtests (juillet → septembre 2026)

Douze variantes ont été testées sur 70 jours de données réelles (calibrage sur juillet–août,
validation sur septembre) : configuration de base, ratios TP / SL différents, confiance « fort »
seulement, 4 critères minimum, ADX ≥ 25, filtre d'extension par rapport à l'EMA20, et version
contrarienne. **Aucune ne montre d'avantage robuste** : le taux de réussite reste à peu près
égal au hasard attendu et l'espérance par trade oscille entre −0,02 % et +0,01 % avant coûts,
donc négative après coûts.

Autrement dit : à l'horizon d'une heure, avec des cibles à quelques dixièmes de pour cent, les
indicateurs classiques alignés ne prédisent pas mieux que pile ou face la direction de l'heure
suivante sur cette période. Sur les cryptomonnaies, le brut est parfois positif mais les frais
(0,06 à 0,08 % par aller-retour) absorbent tout : d'où le filtre `min_tp_to_cost_ratio`, qui
refuse une cible valant moins de 6 fois le coût. Le S&P 500 et l'Ethereum ont montré un léger
avantage sur certaines configurations, non confirmé quand on change les filtres : à considérer
comme du bruit tant que le paper trading ne le confirme pas. Le bot le mesure lui-même et l'affiche (« hasard attendu » et
« avantage ») dans le rapport, le résumé quotidien et les backtests. Tant que l'avantage mesuré
en paper trading n'est pas nettement positif sur plusieurs dizaines de trades, **ne passez pas
en argent réel**. Les deux réglages expérimentaux (`max_extension`, `contrarian`) sont livrés
désactivés, pour vos propres tests.

### Apprentissage
`trading_bot/learning.py` analyse l'historique par critère, actif, sens, confiance, tranche horaire
et contexte d'actualité. Un critère dont le taux de réussite est < 40 % sur ≥ 10 trades voit son
poids réduit ; > 60 % → augmenté. Les tranches horaires < 30 % sont évitées. Les poids sont stockés
dans `data/adjustments.json` et appliqués aux scans suivants.

### Rapport et résumé quotidien
`data/REPORT.md` est régénéré à chaque événement (signal, clôture, résumé, backtest) : vue
d'ensemble, signaux ouverts, statistiques par actif / sens / confiance / critère / heure, derniers
trades, poids appris, backtests. Le résumé quotidien (Telegram) reprend le nombre de signaux,
gagnants / perdants / expirés, taux du jour et cumulé, ce qui a fonctionné ou non, ajustements
prévus et rappel des limites.

## Installation locale

```bash
pip install -r requirements.txt        # uniquement `requests`
cp config.example.json config.json     # optionnel : ajustez les seuils
python run.py backtest --days 30       # validez la stratégie sur l'historique
python run.py scan -v
python run.py loop                     # laisse tourner en tâche de fond
```

Tests : `pip install -r requirements-dev.txt && python -m pytest -q`

## Notifications gratuites (optionnel)

| Variable d'environnement | Service |
|---|---|
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Bot Telegram (créé via @BotFather ; le chat ID est le `chat.id` de `getUpdates`) |
| `DISCORD_WEBHOOK_URL` | Webhook Discord |

Sans configuration, les messages sont affichés en console et journalisés dans `data/notifications.log`.

## Planification sans infrastructure : GitHub Actions

Trois workflows sont fournis dans `.github/workflows/` :

- `bot.yml` : `tick` toutes les 15 min (suivi des signaux ouverts puis scan) ; l'état
  (`data/*.json`, `data/REPORT.md`) est commité dans le dépôt pour persister entre deux exécutions.
  Lancement manuel possible avec une autre commande (`scan`, `track`, `test-notify`, `backtest`,
  `fetch-data`, `manual` avec les champs actif / sens / commentaire).
- `daily-summary.yml` : résumé quotidien à 22:05 UTC.
- `tests.yml` : tests à chaque push.

Ajoutez les secrets Telegram / Discord dans *Settings → Secrets and variables → Actions*, et vérifiez
que `main` est la branche par défaut (les crons ne s'exécutent que sur celle-ci).

**Coût.** Le cron est réglé sur 15 min car le dépôt est privé : le quota gratuit (2 000 min/mois)
ne couvre pas un tick toutes les 5 min. Le suivi TP/SL reste exact (il s'appuie sur les bougies 1 min
depuis l'émission du signal) mais la notification d'issue peut arriver avec jusqu'à 15 min de retard.
Pour un suivi toutes les 5 min, exécutez `python run.py loop` sur une machine locale, ou passez le
dépôt en public (minutes illimitées) et remettez `*/5`. Les crons GitHub sont exécutés « au mieux » :
un retard de quelques minutes est normal.

**Binance depuis GitHub Actions** : les serveurs GitHub sont situés aux États-Unis, Binance y
répond « 451 ». Le bot bascule immédiatement sur Yahoo Finance pour le Bitcoin. Yahoo ne fournit
pas de volume fiable sur `BTC-USD` : les critères volume et VWAP sont alors neutralisés
automatiquement.

## Configuration

Valeurs par défaut dans `trading_bot/config.py`, surcharge via `config.json` (voir
`config.example.json`). Principaux réglages :

| Clé | Défaut | Rôle |
|---|---:|---|
| `max_signals_per_asset_per_day` | 5 | plafond quotidien par actif |
| `max_losses_per_asset_per_day` | 3 | stops avant arrêt pour la journée |
| `max_open_signals` | 4 | positions ouvertes simultanées |
| `cooldown_minutes` / `cooldown_after_loss_minutes` | 30 / 60 | délais entre signaux |
| `shadow_enabled` / `shadow_min_criteria` | true / 2 | signaux fantômes (suivi silencieux) |
| `learn_from_backtest` | true | les trades de backtest alimentent l'apprentissage |
| `min_criteria` / `min_score` / `strong_score` | 3 / 3,0 / 5,0 | seuils de confiance |
| `min_confidence` | `moyen` | `fort` pour ne garder que les meilleurs signaux |
| `min_adx` | 18 | force de tendance minimale |
| `tp_range_fraction` / `sl_range_fraction` | 0,60 / 0,40 | calibrage TP / SL sur le range horaire |
| `min_risk_reward` | 1,2 | ratio minimal |
| `min_resolution_probability` | 0,35 | faisabilité sous 1 h (simulation) |
| `max_atr_ratio` | 2,5 | volatilité instantanée anormale |
| `min_tp_to_cost_ratio` | 6 | la cible doit valoir au moins 6 × le coût aller-retour |
| `max_news_risk_score` | 2 | tolérance à l'actualité |
| `assets.<actif>.cost_pct` | 0,01 / 0,01 / 0,06 / 0,08 / 0,02 | coût aller-retour estimé (NQ / ES / BTC / ETH / or), déduit du P&L |
| `assets.<actif>.session_utc` | voir ci-dessus | plage horaire de scan |

Calendrier macro : `data/macro_calendar.json` (heures UTC). Blackout 45 min avant / 30 min après
chaque événement `high`. Les 8 réunions FOMC et les 12 publications CPI de 2026 sont pré-remplies
(sources : federalreserve.gov, bls.gov) ; complétez avec BCE, PCE, etc. si besoin.

## Structure

```
run.py                      point d'entrée CLI
trading_bot/
  config.py                 paramètres + actifs
  models.py                 Candle, Signal
  indicators.py             EMA / RSI / MACD / ATR / ADX / VWAP / pivots / range horaire / Monte-Carlo
  analysis.py               évaluation multi-timeframe, score, confiance
  signals.py                construction TP / SL / ratio, faisabilité, formatage
  tracker.py                résolution TP / SL / expiration
  backtest.py               rejeu historique sans biais de futur
  learning.py               statistiques + ajustement des poids
  summary.py                résumé quotidien
  report.py                 rapport Markdown
  engine.py                 orchestration scan / track / summary / tick / backtest / manuel
  ui.py                     serveur local de l'interface (bibliothèque standard)
  notify.py                 Telegram / Discord / console
  storage.py                persistance JSON
  providers/                yahoo, binance, coingecko, news (RSS + calendrier)
docs/index.html             interface (tableau de bord + demande de trade)
data/                       état persistant (signaux, fantômes, historique, ajustements, backtests, rapport, dashboard)
tests/                      tests unitaires (données synthétiques, sans réseau)
```
