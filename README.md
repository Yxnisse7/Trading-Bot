# Trading-Bot — signaux de scalping (Nasdaq, S&P 500, Bitcoin, Ethereum, Or, Pétrole, Euro) à coût zéro

Générateur de **signaux courts (~1 h)** sur sept actifs, dont deux à l'essai, à partir de **données gratuites**,
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
| Pétrole WTI (futures `CL=F`), **à l'essai** | Yahoo Finance | — |
| Euro / dollar (futures `6E=F`, pour avoir un vrai volume), **à l'essai** | Yahoo Finance | — |

**Actifs à l'essai.** Un nouvel actif (`trial: true`) est analysé comme les autres mais ses signaux
sont suivis **en silence**, comme une variante (`essai_<actif>`). Il ne devient un actif annoncé
qu'une fois promu : au moins 100 trades suivis, avec un gain net moyen égal ou supérieur à celui des
signaux réels. Le pétrole et l'euro ont été choisis pour leurs moteurs propres, peu liés aux indices
et aux cryptos, leur liquidité et leurs frais faibles. La sélection marche aussi dans l'autre sens :
l'Ethereum, pire actif en backtest comme en réel, a été remis à l'essai le 22/09/2026 dans
`config.json` (supprimez la ligne pour l'annuler).

Marchés meneurs (corrélations, Yahoo) : VIX (`^VIX`), dollar (`DX-Y.NYB`), rendement 10 ans (`^TNX`).
Binance refuse les adresses américaines (GitHub Actions) ; Coinbase et Kraken fournissent alors des
bougies avec de vrais volumes, ce qui réactive les critères volume et VWAP sur les cryptos.

Actualité : flux RSS gratuits (MarketWatch, CNBC, Yahoo Finance, CoinDesk, Cointelegraph, FXStreet),
**calendrier économique ForexFactory** (flux JSON gratuit, sans clé, une requête par heure, cache
disque en cas de panne : toutes les annonces USD à fort impact déclenchent un blackout ; les annonces
EUR à fort impact bloquent seulement l'euro, et les stocks de pétrole américains du mercredi seulement
le pétrole ; l'agenda des
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
alimentent aussi l'apprentissage (`learn_from_backtest`). Chaque fantôme porte une étiquette :
variante en test (voir « Variantes testées en fantôme ») ou simple setup faible.

## Fonctionnement

```
python run.py scan         # analyse + propose des signaux (si convergence)
python run.py track        # vérifie les signaux ouverts : TP / SL / expiration (1 h)
python run.py tick         # track puis scan — commande planifiée
python run.py backtest     # rejoue la stratégie sur l'historique (--days 30, --asset bitcoin)
python run.py summary      # résumé quotidien (jour + cumulé, enseignements, ajustements)
python run.py guide        # envoie le guide des commandes à tous les chats Telegram configurés
python run.py report       # régénère data/REPORT.md
python run.py stats        # statistiques détaillées de l'historique (JSON)
python run.py status       # signaux ouverts
python run.py test-notify  # message de test Telegram / Discord
python run.py manual --asset bitcoin --direction long [--tp 45000 --sl 43000]  # signal demandé
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
Page `docs/portfolio.html` (onglet « Simulation »), commande
`/balance` sur Telegram et `python run.py portfolio --balance 1000 --risk 1`.

- Vous définissez une **balance fictive** et un **risque par trade** (1 % par défaut). Définir une
  balance démarre une nouvelle simulation : seuls les trades ouverts **après** ce moment comptent,
  sans rétroactivité ; la simulation précédente est archivée. Sans définition, le bot simule sur la
  balance par défaut (`portfolio_default_balance`, 1 000 $).
- Pour chaque signal (bot, manuel, proposition ; jamais les fantômes), les **lots** sont calculés pour
  que la perte au stop soit égale au risque choisi, arrondis au pas du contrat et plafonnés par le
  levier de l'actif : MNQ (2 $/pt), MES (5 $/pt), MGC (10 $/pt), MCL (100 barils, 1 $ par cent),
  M6E (12 500 €) ×20 ; BTC et ETH (pas 0,001 / 0,01) ×3.
  Le dimensionnement figure dans le message Telegram du signal.
- À la clôture (TP, SL ou expiration), le résultat net des coûts estimés est appliqué à la balance et
  annoncé dans la notification d'issue ; la page montre la courbe de la balance, les positions
  simulées, chaque trade avec lots, brut, coûts, net et balance après.
- **Aucun trade n'est refusé** : si la balance ne permet pas le lot minimal au risque choisi, le lot
  minimal est pris quand même et le trade est marqué ⚠️ *risqué* (risque effectif et levier réels dans
  le message Telegram et sur la page) ; la page liste ces trades à part.
- Prix en dollars, aucune conversion de devise ; ni marge, ni glissement, ni financement overnight.

### Interface
Le site (`docs/`, servi par GitHub Pages ou par `python run.py ui`) a trois onglets, avec la même
charte : police Geist, bleu = gain / TP, orange = perte / SL, gris = neutre ou hasard, violet réservé
à la marque et aux boutons ; thème clair ou sombre ; sur téléphone, une barre de navigation en bas.

- **Tableau de bord** (`docs/index.html`) : un chiffre vedette, l'avantage du bot face au hasard, avec
  sa jauge de fiabilité (trades nécessaires pour qu'un avantage de 10 points soit détectable) ; tuiles
  balance, résultat cumulé, trades clôturés, suivi en ombre ; graphique live ; courbe du résultat et
  résultat par actif ; signaux en cours (un nouveau signal déclenche une notification et reste
  surligné quelques secondes) ; derniers trades avec filtres (actif, source, résultat), 10 par 10, et
  critères en clair (« Tendance 5 min · 15 min · 1 h ») ; liens vers les analyses détaillées.
- **Simulation** (`docs/portfolio.html`) : balance, courbe de la balance, positions, trades appliqués,
  trades risqués ; la définition de la balance est repliée et signale qu'elle vaut pour tout le monde.
- **Apprentissage** (`docs/apprentissage.html`) : notes d'apprentissage et variantes en test,
  réussite par indicateur contre le hasard, résultats par heure, sens, horizon, confiance et source
  (une seule légende), statistiques par actif et backtests.

Le bouton **« Nouveau trade »** ouvre une fenêtre : Acheter ou Vendre, actif (avec le dernier prix
connu et son âge), TP et SL facultatifs (vides : le bot les calibre sur la volatilité du moment),
raccourcis « Serré » et « Large », aperçu avant envoi (gain/risque, gain ou perte en dollars sur la
simulation, taille, risque sur la balance, zone d'entrée, avertissement si le trade est risqué),
erreurs expliquées sur le champ (SL du mauvais côté du prix…) et la commande Telegram équivalente.
« Proposer un trade » demande au bot sa lecture de l'actif. Les trades envoyés sont suivis comme ceux
du bot, sous la source « manuel ».

Nombres au format français (virgule, espace des milliers, vrai signe moins), blocs gris pendant le
chargement, transitions courtes désactivées si le système demande moins d'animations. Fichiers
communs : `docs/yasuke.css` (charte), `docs/yasuke.js` (en-tête, formats, chargement des données),
`docs/charts.js` (petits graphiques SVG), `docs/live-chart.js`, `docs/sections.js`.

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
arrive après la clôture de la bougie analysée : environ 6 à 12 min pour les contrats à terme, dont
les données Yahoo ont une bougie de retard, et 1 à 7 min pour les cryptos. Les résultats de backtest
sont donc **optimistes** par rapport au réel.

**Aide à l'entrée dans chaque signal.** Le message indique l'heure du prix de référence et son âge,
puis une **zone d'entrée** : au-delà du milieu entre stop et objectif, le gain possible devient plus
petit que le risque, donc mieux vaut passer son tour ; de l'autre côté, un retour à mi-chemin du stop
signale un scénario qui s'affaiblit.

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
`trading_bot/learning.py` recalcule les poids des critères **entièrement, à chaque passage, à
partir de tous les trades clôturés** : réels, fantômes et backtest. Il n'a aucune mémoire des poids
précédents : les mêmes trades donnent toujours les mêmes poids, et aucun trade n'est compté deux fois.

- **Résultat en R** : chaque trade est mesuré en multiples du risque pris, trades expirés compris.
  Sous le hasard, l'espérance brute d'un trade est nulle quelle que soit la place du TP et du SL :
  c'est la référence. Comparer le brut à zéro revient à comparer le net au coût du hasard.
- **Marge de sécurité** : un poids ne bouge que de la part de l'écart qui dépasse ce que le bruit
  peut expliquer, à 95 % (`learning_z`), et seulement au-delà de 30 trades équivalents
  (`learning_min_trades`). Avec peu de données, le poids reste à sa valeur par défaut.
- **Sources pondérées** (`learning_source_weights`) : trade réel 1, fantôme 0,6, backtest 0,25.
- **Familles** : les trois tendances et l'ADX mesurent la même information et sont jugés ensemble.
- **Socle global + correction par actif** : chaque actif part des poids globaux et ne s'en écarte
  que si sa propre différence dépasse, elle aussi, la marge de sécurité (`weights_by_asset`).
- **Tranches horaires** évitées seulement si elles sont nettement pires que le hasard.
- Le backtest est **relancé chaque dimanche** (`weekly-backtest.yml`) et remplace le précédent :
  l'apprentissage ne s'appuie jamais sur un backtest figé. Yahoo ne donne que 60 jours de bougies
  5 min : elles sont donc **accumulées** de semaine en semaine hors du dépôt (release GitHub
  « candles », fichier `candles.tar.gz`, 400 jours gardés au plus), et la stratégie est rejouée sur
  **180 jours** (`BACKTEST_DAYS`). Ne supprimez pas cette release : c'est la mémoire longue du backtest.

### Contexte, sorties et filtres (apprentissage v3)
Les critères cochés sont présents sur presque tous les trades : ils ne disent pas **quand** un
trade marche. Le bot apprend donc aussi sur des mesures chiffrées, sans rien changer de lui-même :

- **Contexte** (`meta.ctx`, module `context.py`) : à chaque signal (réel, en ombre, backtest) sont
  notés la force de tendance (ADX), le RSI et les écarts au VWAP et à l'EMA20 dans le sens du trade,
  la volatilité du moment, l'activité de l'heure, la taille du range, les frais rapportés au risque,
  les minutes depuis l'ouverture américaine et le jour. Chaque mesure est coupée en tranches ; une
  tranche est « à éviter » si même sa borne haute reste sous zéro (marge des tranches horaires).
- **Sorties** (`meta.exc`) : pendant le suivi (et en backtest), gain et perte maximaux en R, et
  retour éventuel au prix d'entrée après +0,5 / +0,8 / +1 R. On mesure ce qu'aurait donné un stop
  remonté à l'entrée ; une règle meilleure est signalée « à décider » mais **jamais activée seule** :
  elle toucherait les sorties des vrais trades.
- **Filtres testés hors échantillon** : « pas d'entrée sur les indices et l'or de 15:00 à 17:00 »
  (30 min avant à 1 h 30 après l'ouverture US) et « contextes appris comme perdants ». Un signal réel
  concerné est **quand même envoyé**, mais marqué (`meta.filters`). Le filtre ne s'applique que si,
  sur les trades marqués depuis sa mise en place (au moins 100 gardés, 20 écartés), les trades
  écartés font nettement pire que les autres (écart prouvé à 95 %, gain net). Il écarte alors ces
  signaux, suivis en silence.

Tout est affiché sur la page Apprentissage (sections « Filtres testés », « Contexte des trades »,
« Sorties »).

Les poids, statistiques et notes sont dans `data/adjustments.json`, affichés dans le résumé
quotidien, le rapport et le tableau de bord.

### Variantes testées en fantôme
Pour gagner des trades sans baisser l'exigence, trois variantes tournent en silence, avec la même
barre de qualité qu'un signal réel, et alimentent l'apprentissage dès maintenant :

| Variante | Ce qui est testé |
|---|---|
| `hors_session` | Nasdaq et S&P 500 le matin européen, 7h-13h UTC (`variant_extended_sessions`) |
| `horizon_3h` | l'horizon ~3 h sur le Nasdaq, le S&P 500 et l'or |
| `confiance_moyenne` | les setups « moyen » quand « fort » est exigé |
| `avant_ouverture` | les entrées dans l'heure qui précède l'ouverture de Wall Street (jusqu'à 5 min après), sur les actifs à séance : un trade ouvert à ce moment subit le pic de l'ouverture. Elles sont suivies en silence et redeviennent réelles si elles font leurs preuves |
| `reprise_apres_stop` | une nouvelle entrée juste après un stop, que le refroidissement (60 min, et 2 h dans le même sens) bloque d'habitude |

Une variante passe **automatiquement en signaux réels** quand, sur au moins 100 trades
(`variant_min_trades`), son gain net moyen égale ou dépasse celui des signaux réels du bot **et**
reste positif « au pire », c'est-à-dire après une marge de sécurité corrigée du nombre d'essais
(Bonferroni sur toutes les variantes et filtres en compétition, `promotion_alpha` = 5 % : ≈ 2,58
écarts-types pour 10 essais, 1,96 au minimum ; les filtres utilisent la même marge). Sans cette
correction, l'une des variantes finirait par battre le bot par pur hasard. Elle repasse en test si
ses résultats retombent. Chaque promotion ou retrait est annoncé sur Telegram.
Une seule variante est testée à la fois sur un même trade, pour ne pas mélanger deux changements.

### Tests de résistance du backtest
À chaque backtest hebdomadaire, les mêmes trades sont rejoués sur les mêmes bougies dans des
conditions dégradées (`trading_bot/stress.py`, méthode de la skill `backtest-expert`) : frais × 1,5 et
× 2, stop et objectif déplacés de ±25 à 50 %, entrée retardée de 5 et 10 min (niveaux notifiés
inchangés, comme sur Topstep où l'entrée arrive après le signal ; « manqué » si le prix les a déjà
dépassés), et le pire cas cumulé. Une grille stop × objectif montre si le gain tient sur une zone de
réglages (« plateau ») ou sur une seule case. Le scénario de référence retrouve exactement le
résultat du backtest. Verdict sur la page Apprentissage (`data/stress.json`) : robuste, fragile,
très fragile, ou pas d'avantage (la stratégie perd déjà en référence).

### Changements de contrat (analyse d'octobre 2026)
Yahoo colle les contrats successifs (`NQ=F`, `CL=F`…) sans corriger l'écart de prix au changement
d'échéance (skill `ml4t-continuous-futures`). Sur l'historique gardé (juillet → septembre 2026) :
- **Nasdaq, S&P 500, or, euro : aucun saut artificiel visible.** Les plus grands écarts tombent à la
  réouverture du dimanche, en même temps sur des marchés sans lien et dans le sens du marché, pas dans
  celui qu'aurait le report d'échéance ; l'euro n'a aucun écart pendant sa semaine d'échéance.
- **Pétrole : deux sauts probables**, au lendemain de l'expiration du contrat du mois (+1,43 % le
  22 juillet, −1,99 % le 23 septembre, plus de 20 fois la variation habituelle d'une bougie). Effet
  mesuré : 1 trade de backtest sur 181 et 1 trade en ombre sur 32, tous deux stoppés par ce saut.

Conclusion : effet trop rare pour justifier une correction automatique, qui risquerait d'effacer de
vrais mouvements (annonces OPEP, stocks). À revérifier quand l'historique couvrira plus de mois.

**SL adaptés à l'heure** (`session_range`, actifs à séance : Nasdaq, S&P 500, or, pétrole) : le range
de référence du TP et du SL est le plus grand du range moyen sur 24 h et du range de la même heure les
jours précédents. À l'ouverture américaine, le marché bouge 3 à 4 fois plus que la nuit : un stop
calculé sur la moyenne de la journée y était pris par le bruit. Sur 60 jours de backtest, avant → après :
Nasdaq −2,97 % → −1,17 %, or −2,66 % → −1,41 %, pétrole −2,26 % → +3,00 %, S&P 500 inchangé ; les
cryptos (24 h/24) y perdaient, elles gardent le calcul d'origine. L'heure d'ouverture suit New York
(13:30 UTC l'été, 14:30 UTC l'hiver).

### Nouveaux setups et historique long
Deux idées d'entrée, écrites dans `HYPOTHESES.md` **avant** tout test, avec leurs critères d'abandon :
A « repli dans une tendance forte » (ADX 15 min ≥ 30, entrée à la reprise après un retour sur l'EMA 20,
stop sous le creux, objectif 1,5 R) et B « retour à la VWAP sans tendance » (ADX < 20, prix à plus de
2 ATR de la VWAP du jour). Un setup n'est gardé que s'il fait au moins 100 trades, un gain net moyen
positif, un facteur de profit ≥ 1,1, le même résultat dans les deux moitiés de la période et s'il
résiste aux tests de résistance. Il serait alors suivi en ombre, jamais notifié directement.

- `python run.py backtest-setups` : sur les bougies récentes (Yahoo / Binance) ;
  `--history` : sur l'historique long. Résultats dans `data/setups.json` et sur la page Apprentissage.
- **Historique long gratuit** (workflow manuel « Historique long », `python run.py fetch-history --months 12`) :
  archives mensuelles Binance pour les cryptos (vraies bougies), bougies 1 min Dukascopy regroupées en
  5 min pour le reste. Dukascopy donne des **CFD au comptant**, pas les contrats CME : niveaux un peu
  décalés, volume en ticks, mais même forme de mouvement, ce qui suffit pour juger une idée en R.
  Dukascopy limite le nombre de requêtes : le téléchargement patiente et réessaie (compter plusieurs
  dizaines de minutes pour 12 mois). Les bougies vont dans la release « history », jamais dans le dépôt.
- Autres sources si besoin : Yahoo en bougies 1 h sur 730 jours (gratuit, vrais contrats, mais trop
  grossier pour des trades de 2 h) ; Databento (vraies données CME en 1 min, 125 $ de crédit offert à
  l'inscription, payant ensuite).

**Bilan sur 12 mois (octobre 2025 → octobre 2026, analyse du 5 octobre 2026).** Le bot actuel, rejoué
sur l'historique long avec ses propres frais (gain moyen par trade, avant frais → après frais) :

| Actif | Trades | Avant frais | Après frais |
|---|---|---|---|
| Nasdaq 100 | 478 | +0,09 R | +0,02 R |
| Pétrole | 640 | +0,04 R | −0,06 R |
| Or | 588 | +0,04 R | −0,07 R |
| S&P 500 | 415 | +0,02 R | −0,08 R |
| Bitcoin | 597 | +0,05 R | −0,14 R |
| Ethereum | 643 | 0,00 R | −0,18 R |
| Euro / dollar | 233 | +0,01 R | −0,20 R |

Avant frais, l'avantage est faible partout ; après frais, seul le Nasdaq reste au-dessus de zéro, sans
que ce soit prouvé (il faudrait de l'ordre de 1 500 trades pour un écart pareil). Les frais comptés par
le bot sont prudents : chez Topstep (frais réels + 1 tick de glissement), ils sont environ 3 fois plus
bas sur le Nasdaq et l'or, ce qui ne suffit pas à rendre les autres actifs gagnants.

Setups : A −0,22 R sur 4 074 trades, B −0,31 R sur 3 051 trades, tous deux abandonnés. L'essai 2
(A sur Nasdaq et S&P 500, mois jamais regardés) donne +0,03 R sur 388 trades avec un facteur de profit
de 1,06 et une seconde moitié négative : abandonné aussi. Détail dans `HYPOTHESES.md`.

### Sections repliables
Sur les trois pages, chaque section se replie ou se déplie d'un clic sur son titre (en glissant), et
un bouton « Tout replier / Tout déplier » s'ajoute à l'en-tête. L'état est mémorisé dans le
navigateur, page par page (`docs/sections.js`).

### Graphique live
À chaque passage (~5 min), le bot publie pour chaque actif un instantané compact des 24 dernières
heures de bougies 5 min (288), les niveaux des signaux ouverts et les trades clôturés de la période,
dans `data/live/<actif>.json`, copié dans `docs/live/` pour GitHub Pages. Le graphique est dessiné
avec **TradingView Lightweight Charts** (copie locale dans `docs/vendor/`, licence Apache 2.0) :
zoom à la molette ou au pincement, déplacement, réticule avec prix et heure, ligne du prix actuel,
vues 5 min, 15 min et 1 h (reconstruites à partir des bougies 5 min), flèches d'entrée et ronds de
sortie des trades passés, lignes TP / SL / entrée et zone d'entrée des signaux en cours. Les actifs se
choisissent par pastilles, avec leur variation sur 24 h. Le même graphique figure sur la page de
simulation ; l'actif et l'unité de temps choisis sont mémorisés. Si la bibliothèque ne se charge pas,
un graphique SVG simple prend le relais. Ce n'est pas un flux temps réel : la granularité est celle
des passages du bot.

**Délai d'affichage** : Telegram reçoit les messages dès que le passage est enregistré. Le site,
lui, passe par GitHub Pages, qui met environ 3 minutes à publier, et se rafraîchit toutes les
2 minutes : il affiche les nouveautés 3 à 5 minutes après Telegram. Dans un navigateur où un jeton
GitHub est enregistré (« Mode GitHub Actions »), les pages lisent les fichiers directement dans le
dépôt, sans attendre GitHub Pages, et se rafraîchissent chaque minute : environ 1 minute après
Telegram (la pastille d'état affiche « direct »). Sans jeton, ou si GitHub le refuse, GitHub Pages
prend le relais automatiquement.

Les pages chargent les fichiers communs (`yasuke.js`, `yasuke.css`, `live-chart.js`…) avec une empreinte
de leur contenu (`yasuke.js?v=…`) : un navigateur ne peut pas garder un ancien script en cache avec une
page neuve. Après toute modification de ces fichiers : `python scripts/version_assets.py` (un test le
vérifie).

### Avertissement et vie privée
L'avertissement complet (« pas un conseil financier, validez en paper trading ») n'est plus répété à
chaque notification : il figure dans le guide `/help` que reçoit automatiquement chaque nouveau chat
autorisé, dans `REPORT.md` et sur les deux pages du site.
Le dépôt et le site étant publics, aucun identifiant de chat Telegram n'est écrit dans les fichiers
versionnés : `data/state.json` ne garde qu'une empreinte courte (SHA-256 tronqué), le tableau de bord
publié ne contient aucun champ `telegram_*`, et le journal des notifications masque les identifiants.

### Messages Telegram
Mêmes règles que le site (`trading_bot/messages.py`) : nombres à la française, Achat / Vente avec
↗️ / ↘️, prix en « code » (un appui les copie, sans séparateur de milliers), boutons « Graphique »
(ouvre le site sur le bon actif) et « Simulation » sous chaque signal (`site_url` dans la config).

- **Signal** : sens, actif, horizon ; entrée avec l'heure et l'âge du prix, TP et SL avec leur écart
  en %, gain/risque, heure d'expiration, zone d'entrée ; « Pourquoi » (critères en clair),
  historique réel de l'actif face au hasard, actualité en une ligne, et la ligne de simulation
  (lots, risque, ⚠️ levier ou lot minimal si le trade est risqué). Aucune formulation ne peut passer
  pour une probabilité de gain.
- **Issue** : envoyée **en réponse au message du signal** (le numéro du message est gardé dans
  `data/telegram_messages.json`, indexé par une empreinte du chat, jamais le numéro de chat), avec le
  résultat en dollars d'abord, le trajet du prix, la durée, la balance et une série éventuelle
  (« 3e gain d'affilée »).
- Si Telegram refuse la mise en forme, le message repart aussitôt en texte brut.

### Investir halal (onglet « Investir »)
Pas du trading : de l'investissement halal à long terme. Page `investissement.html` (l'ancienne page
`halal.html` y redirige), données mises à jour chaque jour à 06:30 UTC par le workflow
« Investissement halal — mise à jour » (`python run.py invest`, module `invest.py`), publiées dans
`docs/invest/data.json`. Aucun ordre, aucun message Telegram.

- **Produits** (tous au comptant, cherchables par ISIN chez Trade Republic, Degiro ou Interactive
  Brokers, en compte-titres : non éligibles au PEA) : iShares MSCI World Islamic (IE00B27YCN58),
  Invesco MSCI ACWI Islamic (IE000LFC57H7), iShares MSCI USA Islamic (IE00B296QM64), iShares MSCI EM
  Islamic (IE00B27YCP72), Invesco Dow Jones Islamic Global Developed (IE000UOXRAM8), Wahed S&P 500
  Shariah (IE000QF8TEK7), HSBC Global Sukuk (IE000E8WZD37), Royal Mint Physical Gold (XS2115336336,
  certifié charia par Amanie Advisors).
- **Chiffres en euros** (historique mensuel Yahoo, dividendes réinvestis quand disponibles, dollars et
  pence convertis) : rendements sur 1, 5 et 10 ans, volatilité, pire baisse, et pour chaque durée de
  détention la part des périodes gagnantes. **Durée conseillée** = plus courte durée gagnante au moins
  95 % du temps. Produit trop récent : historique de référence du même marché (MSCI World Islamic,
  USA Islamic, prix de l'or), affiché comme tel.
- **Portefeuilles types** (prudent, équilibré, dynamique) simulés avec rééquilibrage mensuel ; un
  les sukuk (ETF lancé en 2023) sont estimés avec des obligations d'État américaines 3-7 ans (même
  devise, durée proche ; référence de calcul, non halal, affichée comme telle), l'or avec le prix de l'or.
- **Simulateur** : mise de départ, versement mensuel et durée ; cas défavorable, médian et favorable
  tirés des périodes réelles de l'historique (10 %, 50 %, 90 %).
- **Avis par règles affichées** : tendance longue (prix contre moyenne sur 10 mois), distance au plus
  haut et ce qu'ont donné dans le passé les achats pendant une baisse de 10 % ou plus. Pas un conseil
  personnalisé.
- **Actualités** : finance islamique, ETF islamiques, sukuk, or, marchés (Google Actualités, 10 jours).
- Fiscalité 2026 rappelée (flat tax 31,4 %), purification des dividendes, compte au comptant.

- **Poche offensive : actions halal** (module `halal_stocks.py`, recalculée chaque semaine) : univers =
  les 150 plus grosses entreprises de l'ETF iShares MSCI World Islamic (filtre charia MSCI ; fichier
  de composition public d'iShares, dernière composition gardée si indisponible), historique mensuel en
  euros. Règle « momentum 12-1 » : les 10 actions qui ont le plus monté sur 12 mois (sans le dernier
  mois) et dont le prix est au-dessus de sa moyenne sur 10 mois ; une action détenue n'est remplacée
  que si elle sort du top 20 ou perd sa tendance. **Backtest** mois par mois contre l'ETF Monde
  islamique, frais de rotation compris (0,3 % par achat ou vente) ; biais affiché : l'univers est la
  composition actuelle de l'indice. La page conseille la poche (20 % par défaut, 30 % au plus)
  seulement si la règle a battu l'ETF sur l'historique ; sinon 0 %.
- **Révision tous les 3 mois par défaut** (janvier, avril, juillet, octobre) : c'est le mode qui a donné le
  meilleur résultat net avec de petits montants. Entre deux révisions, les versements vont aux actions
  déjà détenues ; le mois de révision, la page signale celles à vendre et un **rappel Telegram** (une
  fois par trimestre) liste les actions du trimestre. Le mode « chaque mois » reste disponible.
- **Pépites** (part « pari », 5 % par défaut, 10 % au plus) : les entreprises plus petites de l'indice
  islamique (rangs 151 à 400 par taille), classées par hausse sur 6 mois sans le dernier ; 5 actions,
  2 au plus par secteur, révision tous les 3 mois, backtest affiché contre l'ETF.
- **Modes de révision**, rejoués avec de vrais montants (200 € puis 20 €/mois dans la poche, achats en
  plan gratuits, 1 € par vente, 31,4 % d'impôt sur chaque vente en gain) : chaque mois, tous les 3 mois,
  ou sans jamais vendre (les versements vont aux meilleures actions du moment). Comparés à l'ETF Monde
  islamique avec les mêmes versements, sur la valeur nette si tout était vendu à la fin.
- **Entreprises israéliennes exclues** de la poche actions et des pépites (pays indiqué par iShares, plus
  une liste de sociétés israéliennes cotées ailleurs) ; leur part dans l'ETF Monde islamique est affichée
  (un ETF ne permet pas de les retirer).
- **Bitcoin** (au comptant, avis divergents) : fiche avec historique en euros et part réglable dans le plan
  (0, 3 ou 5 %). **SCPI NCap Éducation Santé** (Norma Capital, certifiée charia, 0 % de dette) : fiche tenue à
  jour à la main (prix de part, loyers versés, 12 % de frais d'entrée, minimum 1 010 €, 8 ans et plus),
  détenable dans le portefeuille mais hors du plan mensuel.
- **Mon portefeuille et plan du mois** : on saisit ses lignes (ETF ou actions, quantité, prix d'achat
  facultatif) ; la page donne la valeur, la plus-value, et **combien verser sur chaque ligne ce mois-ci**
  pour se rapprocher des parts visées (portefeuille type + poche actions), sans rien vendre. Les
  actions sorties de la règle sont signalées « à remplacer ». Enregistré dans le navigateur ; un lien
  permet de retrouver son portefeuille sur un autre appareil.
- **Zakat** : calculateur sur la page (rien ne sort du navigateur). Placements du portefeuille repris
  automatiquement, plus comptes et livrets, PEE (compté ou non tant qu'il est bloqué), or et argent
  physiques, dettes de l'année. Nisab en argent (595 g, par défaut) ou en or (85 g) au prix publié chaque
  jour (contrats GC=F et SI=F en euros), actions à 100 % ou à 25 % (norme AAOIFI 35), année lunaire
  (2,5 %) ou solaire (2,577 %). Skill `zakat-calculator`.
- **Revue de la stratégie** (`invest_review.py`, workflow manuel « revue de la stratégie », essai 6 de
  HYPOTHESES.md) : la poche et les pépites comparées à des **témoins dans le même univers** (toutes les
  actions à poids égal, 500 tirages au hasard avec la même rotation) pour neutraliser le biais du
  survivant ; variantes anti-krach et corrélation ; risque du portefeuille « Dynamique » réglé comme sur
  le site (chute maximale, pire année, perte en euros) ; **contrôle charia AAOIFI** des actions retenues
  (dette et liquidités < 30 % de la capitalisation, intérêts < 5 % du chiffre d'affaires) avec leur taux
  de purification. Skills `sharia-screening`, `historical-risk`, `factor-investing`, `rebalancing`.

L'ancien **mode halal de trading** (second bot, `data/halal`) est arrêté : ses étapes ne tournent
plus que si la variable de dépôt `HALAL_TRADING` vaut `on`. Le code et les données sont gardés.

### Positions ouvertes : estimation et arrêt manuel
Sur le tableau de bord, la simulation et la page halal, chaque position ouverte affiche une
**estimation en euros** : le résultat de la position simulée au dernier prix connu (graphique live),
frais déduits, converti au cours euro/dollar suivi par le bot.

Le bouton **« Arrêter »** (ou `/stop [actif]` sur Telegram, `python run.py stop --signal <id>`) solde la
position simulée au prix du moment ; la confirmation arrive sur Telegram, en réponse au signal, avec le
résultat en dollars et en euros. Le bot **continue de suivre le trade en silence** jusqu'au TP, au SL ou
à l'expiration (message sans son à la fin), et l'apprentissage retient :
- son vrai résultat s'il touche le TP (un TP reste un TP, même si vous étiez sorti avant) ;
- votre sortie si vous êtes sorti **en gain** et qu'il finit plus bas (le signal offrait une vraie fenêtre de gain) ;
- son vrai résultat si vous êtes sorti en perte.

Un trade arrêté ne bloque plus de nouveau signal sur l'actif. Sur le site, le bouton passe par le
workflow GitHub (jeton du « Mode GitHub Actions ») : l'arrêt a lieu 1 à 2 minutes plus tard.

### Compte Topstep 50K (la simulation rejouée chez Topstep)
Un **compte séparé** qui rejoue **tous les trades de l'onglet Simulation** (passés et à venir, ceux du bot
comme vos trades manuels) sur un compte d'évaluation Topstep 50K. Page du site : `topstep.html`
(onglet « Topstep »). Il a ses propres fichiers : il ne change ni la simulation ni l'apprentissage du bot.

Chaque trade est dimensionné **comme dans la simulation** : un pourcentage de la balance du moment risqué
au stop, converti en micro-contrats (1 à 50). Par défaut **0,5 %** (250 $ sur 50 000 $), réglable sur la
page ou avec `/topstep risque 1` ; tout le compte est alors recalculé. Les 10 % de la simulation à 500 $
ne sont pas repris : la perte maximale Topstep (2 000 $) ne vaut que 4 % de la balance. Rejoués sur les 53
premiers trades de la simulation, 10 % font échouer le compte le 22/09, 1 % dépasse la limite journalière,
0,5 % finit à +1 548 $.

Micro-contrats : MNQ (2 $ le point), MES (5 $), MGC (10 $), MCL (100 $), M6E (12 500 $), MBT (0,10 $),
MET (0,10 $). En plus des trades de la simulation :
- `/pris [actif|id] [micros]` (bouton « Pris ») ajoute un signal que la simulation n'a pas pris, ou impose
  vos micros sur un trade déjà présent ;
- `/journal <actif> <long|short> <entrée> <sortie> <micros> [AAAA-MM-JJTHH:MM]` (heure de Paris) ajoute
  un trade fait hors du bot ;
- `/sortie [actif|id] [prix]` (bouton « Sortie ») enregistre votre sortie **pour ce compte seulement** ;
- `/retirer <id>` retire un trade, `/topstep` affiche l'état.

Les trades déjà repris restent dans le compte même si la simulation est remise à zéro.
**Objectif du jour** : dès que le résultat réalisé de la journée de trading atteint 1 200 $ (40 % de
l'objectif, sous les 50 % de la règle de cohérence), le compte ne prend plus de nouveau trade jusqu'à la
journée suivante (17:00 heure de Chicago, minuit à Paris). `/topstep objectif 1500` pour le changer,
`/topstep objectif 0` pour le désactiver. De même, après −1 000 $ dans la journée, plus aucun trade :
Topstep bloque le compte jusqu'au lendemain. Les trades laissés de côté sont listés sur la page (« Trades
non pris ») et le message Telegram de l'issue l'indique. Le bot, lui, continue de trader normalement.

`/topstep reset` (bouton « Nouveau compte à 50 000 $ ») repart d'un compte neuf : seuls les trades
ouverts à partir de ce moment comptent, l'ancien compte est gardé en résumé.

Règles appliquées (septembre 2026, à vérifier sur topstep.com) : objectif +3 000 $ ; perte maximale de
2 000 $ sous le plus haut solde de fin de journée, bloquée à 50 000 $ ; limite journalière de 1 000 $ ;
cohérence (meilleure journée ≤ 50 % du gain, sinon l'objectif monte) ; 50 micros au plus en même temps ;
positions fermées avant 15:10 heure de Chicago ; journée de trading de 17:00 à 17:00 heure de Chicago.
Les manquements sont signalés sur la page et dans `/topstep`.

Données : `data/topstep/account.json` (vos choix) et `data/topstep/dashboard.json` (compte calculé),
copié dans `docs/topstep/` à chaque passage. Sur GitHub : workflow « tick », commande `topstep`, note
`pris <id> 3`, `sortie <id>`, `retirer <id>`, `journal …` ou `risque 0.5`.

Connexion automatique : l'API TopstepX (ProjectX) permet de passer des ordres par programme sur le
Combine et l'Express Funded (pas sur le Live Funded), mais seulement **depuis votre propre appareil**
(serveurs distants, VPS et VPN interdits). Le bot, qui tourne sur GitHub Actions, ne passe donc aucun
ordre.

### Rapport et résumé quotidien
`data/REPORT.md` est régénéré à chaque événement (signal, clôture, résumé, backtest) : vue
d'ensemble, signaux ouverts, statistiques par actif / sens / confiance / critère / heure, derniers
trades, poids appris, backtests. Le résumé quotidien (Telegram, **sans son** à minuit) donne le bilan
du jour, chaque trade de la journée, la réussite cumulée face au hasard, ce qui est **significatif**
(écart au hasard au-delà de 1,96 écart-type) et, à part, les pistes encore trop peu fournies pour
conclure, l'apprentissage, la simulation de compte et les annonces à venir. Il n'est **envoyé qu'une
fois par jour** : le planificateur de GitHub (souvent en retard d'une à deux heures) et le cron externe
le déclenchent tous deux, le second passage ne renvoie rien (`python run.py summary --force` pour le
renvoyer). La commande `/resume` répond toujours.

## Installation locale

```bash
pip install -r requirements.txt        # uniquement `requests`
cp config.example.json config.json     # optionnel : ajustez les seuils
python run.py backtest --days 30       # validez la stratégie sur l'historique
python run.py scan -v
python run.py loop                     # laisse tourner en tâche de fond
```

Tests : `pip install -r requirements-dev.txt && python -m pytest -q`

Sous Windows : `tzdata` (fuseaux horaires) s'installe tout seul avec `requirements.txt`, et
`.gitattributes` garde les fins de ligne LF (sinon les empreintes des fichiers du site diffèrent).
Une copie locale de secours ne doit **pas** recevoir le jeton Telegram tant que le bot tourne sur
GitHub Actions : elle lirait les commandes à sa place et doublerait les messages.

## Notifications gratuites (optionnel)

| Variable d'environnement | Service |
|---|---|
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Bot Telegram (créé via @BotFather ; le chat ID est le `chat.id` de `getUpdates`) |
| `DISCORD_WEBHOOK_URL` | Webhook Discord |

Sans configuration, les messages sont affichés en console et journalisés dans `data/notifications.log`.

## Planification sans infrastructure : GitHub Actions

Les workflows sont dans `.github/workflows/`, dont `weekly-backtest.yml` qui relance le backtest
chaque dimanche à 20:00 UTC :

- `bot.yml` : `tick` toutes les 5 min (commandes Telegram, suivi des signaux ouverts, recherche de
  signaux à chaque passage, `scan_interval_minutes`) ; l'état (`data/*.json`, `data/REPORT.md`, `docs/dashboard.json`) est commité dans
  le dépôt pour persister entre deux exécutions.
  Lancement manuel possible avec une autre commande (`scan`, `track`, `test-notify`, `backtest`,
  `fetch-data`, `manual` avec les champs actif / sens / commentaire).
- `bot.yml` accepte aussi `tp` et `sl` en entrée pour `manual` (objectif et stop imposés).
- `daily-summary.yml` : résumé quotidien à 22:05 UTC (00:05 Paris en été) ; lancé avant midi heure locale, il porte sur la veille, sinon sur le jour même (`--day hier|aujourd'hui|AAAA-MM-JJ` pour forcer).
- `tests.yml` : tests à chaque push.
- `backup.yml` : **sauvegarde hebdomadaire** le dimanche à 21:30 UTC, après le backtest. Une
  archive zip de tous les fichiers suivis du dépôt (code, données, site), plus l'historique des
  bougies (release `candles`), est envoyée en silence au **seul propriétaire** (premier chat de
  `TELEGRAM_CHAT_ID`) : environ 5 Mo, sous la limite de 50 Mo des bots Telegram. Rien n'est écrit
  dans le dépôt, et les secrets n'y sont jamais. Si GitHub bloquait un jour le dépôt, le mode
  d'emploi pour tout reconstruire est dans `sauvegarde/LISEZMOI.txt` de l'archive (nouveau dépôt,
  secrets à remettre, Pages, workflows, cron-job.org). Commande : `python run.py backup --candles <archive>`.

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
  halal.py                  mode halal : second bot séparé (achat seulement, comptant, sans levier)
  ui.py                     serveur local de l'interface (bibliothèque standard)
  notify.py                 Telegram / Discord / console
  storage.py                persistance JSON
  providers/                yahoo, binance, coingecko, news (RSS + calendrier)
docs/                       site : index.html (tableau de bord), portfolio.html (simulation), apprentissage.html, halal.html,
                            yasuke.css / yasuke.js (charte et outils communs), charts.js, live-chart.js, sections.js,
                            vendor/ (TradingView Lightweight Charts), live/ et *.json publiés par le bot
data/                       état persistant (signaux, fantômes, historique, ajustements, backtests, rapport, dashboard) ;
                            data/halal/ : état du mode halal, jamais mélangé
tests/                      tests unitaires (données synthétiques, sans réseau)
```
