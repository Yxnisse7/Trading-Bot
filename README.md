# Trading-Bot — signaux de scalping (Nasdaq, S&P 500, Bitcoin, Ethereum, Or) à coût zéro

Générateur de **signaux courts (~1 h)** sur cinq actifs, à partir de **données gratuites**,
avec **suivi automatique** des issues, **apprentissage** sur l'historique, **backtest**,
**interface locale** et **résumé quotidien**. Le bot **n'exécute aucun ordre** : il propose,
vous décidez.

| Actif | Source principale | Replis (dans l'ordre) |
|---|---|---|
| Nasdaq 100 (futures `NQ=F`) | Yahoo Finance (API chart publique) | — |
| S&P 500 (futures `ES=F`) | Yahoo Finance | — |
| Bitcoin (`BTC/USD`) | Binance (`api.binance.com`, puis miroirs `data-api.binance.vision` et `api.binance.us`) | Coinbase Exchange, Kraken, Yahoo, CoinGecko (prix) |
| Ethereum (`ETH/USD`) | Binance (idem) | Coinbase Exchange, Kraken, Yahoo |
| Or (`XAU/USD` via `GC=F`) | Yahoo Finance | — |

Marchés meneurs (corrélations, Yahoo) : VIX (`^VIX`), dollar (`DX-Y.NYB`), rendement 10 ans (`^TNX`).
Binance refuse les adresses américaines (GitHub Actions) ; Coinbase et Kraken fournissent alors des
bougies avec de vrais volumes, ce qui réactive les critères volume et VWAP sur les cryptos.

Actualité : flux RSS gratuits (MarketWatch, CNBC, Yahoo Finance, CoinDesk, Cointelegraph, FXStreet),
**calendrier économique ForexFactory** (flux JSON gratuit, sans clé, une requête par heure, cache
disque en cas de panne : toutes les annonces USD à fort impact déclenchent un blackout, l'agenda des
30 prochaines heures figure dans le résumé quotidien) et calendrier manuel (`data/macro_calendar.json`).

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
| Range d'ouverture | Cassure du range des 30 premières minutes de la séance US, dans les 2 h qui suivent (indices, or) |
| Extrêmes de la veille | Cassure du plus haut / plus bas de la veille, sans extension excessive |
| Marché meneur | VIX (indices), dollar et taux (or), Bitcoin (Ethereum) : confirmation légère (poids 0,5) |

**Moments de marché.** Un profil d'activité par heure est calculé automatiquement à partir des
données (range moyen de chaque heure rapporté à la moyenne) : les heures creuses (< 60 % de
l'activité moyenne) ne produisent pas de signal court. Les setups « cassure du range d'ouverture »
et « cassure des extrêmes de la veille » ciblent les moments structurés de la séance.

**Corrélations, sans suivre bêtement.** Un marché meneur n'émet jamais de signal : il ne peut
qu'ajouter une confirmation légère ou opposer un **veto** (VIX +4 % en 15 min → pas de long
indices ; dollar +0,25 % en 1 h ou taux 10 ans +2 % → pas de long or ; Bitcoin en tendance contraire
→ pas de signal Ethereum dans l'autre sens). La direction vient toujours de l'actif lui-même.

**Deux horizons.** Chaque actif est analysé en base 5 min (scalp, ~1 h) **et** en base 15 min
(intraday, ~3 h : unités ×3 et ×12, range de référence sur 3 h, cibles plus larges). Les signaux
intraday sont annoncés avec leur durée estimée (« INTRADAY ~3 h »), limités à 2 par actif et par
jour, et comptés à part dans les statistiques (« par horizon »). Sur 60 jours de backtest, cet
horizon est légèrement positif sur Nasdaq et or, négatif sur S&P 500 et nettement perdant sur les
cryptos : il est donc désactivé par défaut sur Bitcoin et Ethereum (`assets.<actif>.long_horizon`). Le résumé indique aussi si les trades
expirés finissent en moyenne dans le bon sens, ce qui dirait qu'une sortie au temps serait préférable.

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

### Commandes Telegram
Écrivez au bot depuis votre téléphone ; les commandes sont traitées au passage suivant (toutes les
5 min) et seuls les messages du chat configuré sont acceptés :

| Commande | Effet |
|---|---|
| `/propose btc` | analyse immédiate de l'actif, lecture des indicateurs, proposition calibrée ou abstention expliquée |
| `/long nq cassure` / `/short or` | signal manuel (le commentaire est facultatif), calibré par le bot, notifié et suivi |
| `/status` | signaux ouverts |
| `/resume` | résumé du jour |
| `/balance` / `/balance 1000 1` | état de la simulation de compte / nouvelle balance (et risque %) |
| `/help` | aide |

Actifs : `nasdaq` (`nq`), `sp500` (`es`), `bitcoin` (`btc`), `ethereum` (`eth`), `gold` (`or`).

**Plusieurs personnes** : `TELEGRAM_CHAT_ID` accepte plusieurs identifiants séparés par des virgules.
Tous reçoivent les signaux et le résumé ; chacun peut envoyer des commandes, dont les réponses ne
vont qu'à lui. Un inconnu qui écrit au bot reçoit une seule fois son identifiant de chat, à
transmettre au propriétaire pour être ajouté au secret. Un groupe Telegram fonctionne aussi
(ajoutez le bot au groupe, son identifiant est négatif).

**Réactivité** : le workflow `commands.yml` ne fait que lire et traiter les commandes (quelques
secondes) ; déclenché par un cron externe toutes les 1 à 2 minutes, il rend les commandes quasi
immédiates sans alourdir le passage complet de 5 min.

### Simulation de compte (lots et balance)
Page `docs/portfolio.html` (lien « Simulation de compte » sur le tableau de bord), commande
`/balance` sur Telegram et `python run.py portfolio --balance 1000 --risk 1`.

- Vous définissez une **balance fictive** et un **risque par trade** (1 % par défaut). Définir une
  balance démarre une nouvelle simulation : seuls les trades ouverts **après** ce moment comptent,
  sans rétroactivité ; la simulation précédente est archivée. Sans définition, le bot simule sur la
  balance par défaut (`portfolio_default_balance`, 1 000 $).
- Pour chaque signal (bot, manuel, proposition ; jamais les fantômes), les **lots** sont calculés pour
  que la perte au stop soit égale au risque choisi, arrondis au pas du contrat et plafonnés par le
  levier de l'actif : MNQ (2 $/pt), MES (5 $/pt), MGC (10 $/pt) ×20 ; BTC et ETH (pas 0,001 / 0,01) ×3.
  Le dimensionnement figure dans le message Telegram du signal.
- À la clôture (TP, SL ou expiration), le résultat net des coûts estimés est appliqué à la balance et
  annoncé dans la notification d'issue ; la page montre la courbe de la balance, les positions
  simulées, chaque trade avec lots, brut, coûts, net et balance après.
- **Aucun trade n'est refusé** : si la balance ne permet pas le lot minimal au risque choisi, le lot
  minimal est pris quand même et le trade est marqué ⚠️ *risqué* (risque effectif et levier réels dans
  le message Telegram et sur la page) ; la page liste ces trades à part.
- Prix en dollars, aucune conversion de devise ; ni marge, ni glissement, ni financement overnight.

### Interface
`python run.py ui` sert une page simple et visuelle (`docs/index.html`) : indicateurs clés,
**graphiques** (SVG sans dépendance, infobulles au survol, thème clair / sombre, palette bleu / orange
lisible en cas de daltonisme) : courbe du P&L net cumulé trade après trade, résultats TP / SL / expirés
par actif, par sens, par horizon, par confiance et par source, trades par heure d'émission, et réussite
par indicateur contre le hasard attendu (barre contre repère) ; chaque graphique porte une phrase
« comment lire »,
signaux ouverts, **résumé des derniers trades par indicateur** (taux de réussite contre hasard
attendu, poids appris, derniers trades), statistiques par actif, derniers trades, backtests et
notes d'apprentissage. Le bouton **« Demander un trade »** crée un signal manuel : le bot calibre
l'entrée, le TP et le SL sur la volatilité du moment, envoie la notification Telegram / Discord et
suit le trade comme les siens ; le résultat est comptabilisé à part (source « manuel »), ce qui
permet de comparer votre jugement à celui du bot.

**En ligne, via GitHub Pages** (dépôt public, *Settings → Pages*, branche `main`, dossier `/docs`) :
la page est servie à `https://<propriétaire>.github.io/<dépôt>/`, lit `dashboard.json` publié à côté
d'elle par le bot à chaque passage, et les boutons déclenchent le workflow via l'API GitHub avec un
jeton fine-grained (*Actions : Read and write*) saisi une fois dans « Mode GitHub Actions » et
conservé uniquement dans votre navigateur. La notification arrive en 1 à 2 minutes.

**En local** : créez un fichier `.env` à partir de `.env.example` avec vos clés Telegram pour que
les demandes manuelles faites depuis l'interface locale envoient aussi la notification.

### Suivi automatique
- À chaque passage (5 min), le bot récupère les bougies 1 min depuis l'émission du signal et le
  prix courant.
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

- `bot.yml` : `tick` toutes les 5 min (commandes Telegram, suivi des signaux ouverts, scan toutes
  les 15 min) ; l'état (`data/*.json`, `data/REPORT.md`, `docs/dashboard.json`) est commité dans
  le dépôt pour persister entre deux exécutions.
  Lancement manuel possible avec une autre commande (`scan`, `track`, `test-notify`, `backtest`,
  `fetch-data`, `manual` avec les champs actif / sens / commentaire).
- `daily-summary.yml` : résumé quotidien à 22:05 UTC.
- `tests.yml` : tests à chaque push.

Ajoutez les secrets Telegram / Discord dans *Settings → Secrets and variables → Actions*, et vérifiez
que `main` est la branche par défaut (les crons ne s'exécutent que sur celle-ci).

**Coût.** Le dépôt est public : les minutes GitHub Actions sont illimitées, d'où un passage toutes
les 5 min. Sur un dépôt privé, chaque passage compte une minute entière sur un quota de 2 000 par
mois : passez alors le cron à 30 min. Le planificateur GitHub peut ne jamais démarrer sur un dépôt
récent ; un cron externe gratuit (cron-job.org) appelant l'API `workflow_dispatch` est une solution
fiable, décrite dans la section suivante.

**Cron externe (cron-job.org).** Créez un jeton fine-grained limité au dépôt avec la permission
*Actions : Read and write*, puis un cronjob toutes les 5 min en POST sur
`https://api.github.com/repos/<propriétaire>/<dépôt>/actions/workflows/bot.yml/dispatches` avec les
en-têtes `Authorization: Bearer <jeton>`, `Accept: application/vnd.github+json`,
`Content-Type: application/json` et le corps `{"ref":"main","inputs":{"command":"tick"}}`. Un second
cronjob quotidien à 22:05 UTC sur `daily-summary.yml` avec le corps `{"ref":"main"}`.

**Binance depuis GitHub Actions** : les serveurs GitHub sont situés aux États-Unis, Binance y
répond « 451 ». Le bot bascule immédiatement sur Yahoo Finance pour le Bitcoin. Yahoo ne fournit
pas de volume fiable sur `BTC-USD` : les critères volume et VWAP sont alors neutralisés
automatiquement.

## Configuration

Le dépôt contient un `config.json` (réglages « moins de trades, mieux ciblés » du 18/09/2026 : seuls
les signaux « fort », horizon 3 h suspendu, Nasdaq et S&P 500 limités à la session américaine
13h-20h UTC) ; supprimez une ligne pour revenir à la valeur par défaut.
Valeurs par défaut dans `trading_bot/config.py`, surcharge via `config.json` (voir
`config.example.json`). Principaux réglages :

| Clé | Défaut | Rôle |
|---|---:|---|
| `max_signals_per_asset_per_day` | 5 | plafond quotidien par actif |
| `max_losses_per_asset_per_day` | 3 | stops avant arrêt pour la journée |
| `max_open_signals` | 4 | positions ouvertes simultanées |
| `cooldown_minutes` / `cooldown_after_loss_minutes` | 30 / 60 | délai entre signaux ; après un stop, compté depuis la clôture, tous horizons confondus |
| `same_direction_after_loss_minutes` | 120 | après un stop, pas de nouveau signal dans le même sens sur l'actif (le sens inverse reste possible) |
| `post_event_caution_hours` | 24 | après FOMC / CPI / emploi : un critère et un point de score de plus exigés, horizon 3 h suspendu |
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
| `activity_filter` / `min_activity_ratio` | true / 0,6 | heures creuses ignorées (profil automatique) |
| `us_open_utc` / `orb_minutes` / `orb_window_minutes` | 13:30 / 30 / 120 | range d'ouverture US (13:30 UTC en heure d'été, 14:30 en hiver) |
| `correlation_enabled`, `vix_veto_pct`, `dxy_veto_pct`, `tnx_veto_pct` | true, 4, 0,25, 2 | vetos de corrélation |
| `long_horizon_enabled` / `long_horizon_base_minutes` / `max_long_signals_per_asset_per_day` | true / 15 / 2 | second horizon (~3 h) |
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
