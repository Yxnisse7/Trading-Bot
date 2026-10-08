# Passation — Trading-Bot (état au 8 octobre 2026)

Résumé complet de tout le travail fait sur le bot, pour reprendre dans une nouvelle conversation.
À lire avec `README.md` (fonctionnement détaillé) et `HYPOTHESES.md` (tous les essais, règles écrites
avant les résultats, et leur journal). L'agent IA « second avis » est un **projet séparé**, dans le
dépôt privé `Yxnisse7/trading-agent` : il n'est pas traité ici.

---

## 1. Qui, quoi, comment travailler

- **Yanisse** (GitHub `Yxnisse7`), trader débutant. Écrit en français, veut des explications simples,
  pas de jargon sans explication. Pratique, veut aller vite, mais accepte la rigueur quand on explique
  pourquoi.
- **Dépôt public** `Yxnisse7/Trading-Bot`, branche **`main`**, on pousse directement sur `main`.
- **Site** : https://yxnisse7.github.io/Trading-Bot/ (GitHub Pages, dossier `docs/`).
- **But** : un bot qui **envoie des signaux** sur Telegram (jamais d'ordre réel), mesure honnêtement
  s'il a un avantage, et aide à réussir un compte de prop firm (Topstep 50K), idéalement vite.
- Abonnement Claude **Pro** : économiser le quota (ne pas relire inutilement, travailler par lots).

## 2. Règles permanentes (à respecter dans toute session)

- **Ne jamais réécrire l'historique git** (pas de rebase, amend, force-push, filter-repo). Citation :
  « tu enlèves mon identifiant mais sans le truc avec l'historique git, je veux pas casser le truc,
  enlève juste ce qu'il y a en surface, fais pas de bêtise, le bot marche bien et c'est pas grave s'il
  reste dans l'historique ».
- **Aucun vrai identifiant de chat Telegram** dans les fichiers publics (les tests utilisent des
  identifiants fictifs ; l'état stocke des empreintes).
- **Personne d'autre ne doit pouvoir modifier la balance** (commandes réservées au propriétaire).
- **Aucun ordre réel.** Données **gratuites** de préférence.
- **Pré-enregistrement** : toute nouvelle stratégie ou modification est écrite dans `HYPOTHESES.md`
  **avant** de regarder le moindre résultat, avec ses critères d'abandon ; toute correction après un
  premier résultat est datée et comptée comme un nouvel essai. Les résultats vont dans le journal en
  bas de `HYPOTHESES.md`, et une section dans `README.md`.
  Exception choisie par Yanisse : `donchian_day` or mis en signaux réels sans promotion statistique.
- **Ne jamais envoyer l'adresse e-mail de Yanisse** nulle part.
- **Aucun nom de modèle d'IA** dans les commits, PR, code ou fichiers.
- Pied de commit : `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` puis la ligne
  `Claude-Session: <lien de la session>`.
- **Copie locale de sauvegarde** (Windows, interface en lecture seule) : ne jamais y configurer le
  jeton Telegram, ne jamais y lancer scan / tick / loop.
- Garder le workflow des **commandes Telegram toutes les minutes**.
- **Pas de runner auto-hébergé / pas de repli sur le PC** de Yanisse.
- **Halal** : entreprises et firmes israéliennes exclues (The5ers et Trade The Pool retirés de la
  comparaison des prop firms ; sociétés israéliennes exclues de la poche actions).
- Ne jamais désactiver la vérification TLS ni toucher au proxy réseau.
- Une clé API Anthropic, si un jour fournie, va **uniquement dans les secrets GitHub**.
- Ne pas créer de pull request sans demande explicite.

## 3. Architecture technique

**Exécution** : GitHub Actions (dépôt public → minutes illimitées), déclenchées par cron GitHub et par
un **cron externe cron-job.org** (API `workflow_dispatch`, plus fiable).

| Workflow | Rôle | Fréquence |
|---|---|---|
| `bot.yml` | `tick` : suivi des signaux ouverts + recherche de signaux + laboratoire en ombre + signaux réels Donchian + contrôle de décrochage ; commite l'état (`bot: état …`) | toutes les 5 min |
| `commands.yml` | lit et traite les commandes Telegram | toutes les minutes |
| `daily-summary.yml` | résumé quotidien | 22:05 UTC |
| `weekly-backtest.yml` | backtest + apprentissage + chances Topstep + comparaison prop firms (Node 20, `npm ci` dans `tools/propfirm`) | dimanche 20:00 UTC |
| `backup.yml` | archive zip du dépôt + bougies envoyée au seul propriétaire sur Telegram | dimanche 21:30 UTC |
| `invest.yml` | page Investir (halal) | chaque jour 06:30 UTC |
| `invest-review.yml`, `history.yml`, `halal.yml` | manuels (revue halal, historique long, ancien mode halal arrêté) | à la main |
| `tests.yml` | tests | à chaque push |

**Secrets GitHub** (noms seulement) : `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `DISCORD_WEBHOOK_URL`.
Variable `HALAL_TRADING` (ancien mode halal de trading, éteint sauf si `on`).

**Code** (`trading_bot/`, point d'entrée `run.py`) :
- Cœur du bot : `config.py`, `models.py`, `indicators.py`, `analysis.py`, `signals.py`, `tracker.py`,
  `backtest.py`, `learning.py`, `engine.py` (orchestration), `storage.py`, `notify.py`, `summary.py`,
  `report.py`, `ui.py`, `providers/` (Yahoo, Binance, CoinGecko, news RSS + calendrier ForexFactory,
  `history.py` pour l'historique long Binance/Dukascopy).
- Laboratoire et essais : `strategies.py` (stratégies, `SHADOW`, `LIVE`), `macro_history.py` (essai 4),
  `multi_trend.py` (essai 10), `trend_daily.py` (essai 11), `macro_drift.py` (essai 12),
  `macro_long.py` (essai 13), `drift.py` (essai 7), `fill_audit.py` (audit des prix),
  `topstep_odds.py` (chances Topstep et comparaison des prop firms).
- Investissement halal : `invest.py`, `halal_stocks.py`, `invest_review.py` ; ancien `halal.py`.
- `tools/propfirm/` : simulateur LuxAlgo `@luxalgo/prop-firm-sim-core` 1.3.0 (MIT, Node), spec
  Topstep `topstep_spec.mjs`, `odds.mjs`, `firms.mjs` (`node_modules` ignoré par git).
- `tests/` : **219 tests passent** (`python -m pytest -q`), données synthétiques, sans réseau.

**Site** (`docs/`) : tableau de bord (`index.html`), Simulation (`portfolio.html`), Apprentissage
(`apprentissage.html` : laboratoire, ombre, décrochage, audit des prix), Topstep (`topstep.html` :
compte simulé, chances du Combine, comparaison des prop firms), Investir (`investissement.html`).
Graphique live TradingView Lightweight Charts, données publiées dans `docs/dashboard.json`,
`docs/live/<actif>.json`, `docs/topstep/*.json`, `docs/invest/data.json`.

**Données** (`data/`) : état JSON du bot ; `data/topstep/` (compte simulé, odds.json, firms.json, séries
R de référence) ; `data/drift_reference.json` ; `data/essai8.json` … `data/essai13.json` ;
`data/macro_events_2010_2024.json` ; historique long dans des releases GitHub (`history`, `candles`),
jamais commité.

**Commandes utiles** : `python run.py tick | scan | track | backtest | summary | status | report |
learn | topstep-odds | drift-reference | donchian-day | intraday-gold | multi-trend | trend-daily |
macro-drift | macro-long | backtest-setups | fetch-data | backup | ui`.

## 4. Le bot de base (scalping ~1 h)

- **Actifs** : Nasdaq (NQ), S&P 500 (ES), Bitcoin, Or (GC → XAU), et à l'essai (suivis en silence)
  Ethereum, pétrole WTI, euro/dollar.
- **Méthode** : 9-12 critères (tendances 5 min / 15 min / 1 h, ADX, VWAP, RSI, MACD, niveaux clés,
  volume, range d'ouverture US, extrêmes de la veille, marchés meneurs VIX / dollar / taux avec veto).
  Signal si ≥ 3 critères et score suffisant. TP = 60 % du range horaire, SL = 40 %, faisabilité par
  Monte-Carlo, garde-fous (5 signaux/actif/jour, 4 ouverts max, pauses après stop, pause autour des
  annonces macro, sessions).
- **Réglages actuels** (`config.json`, 18/09) : seulement les signaux « fort », horizon 3 h suspendu,
  Nasdaq et S&P 500 limités à 13h-20h UTC ; Ethereum à l'essai depuis le 22/09.
- **Signaux fantômes** (setups faibles suivis en silence) et **variantes** testées en fantôme avec
  **promotion automatique** seulement avec une marge statistique corrigée du nombre d'essais.
- **Résultats réels** (au 08/10) : 122 signaux annoncés, 43 TP / 55 SL / 24 expirés, P&L cumulé
  −3,4 % ; fantômes 278, −11,2 %. Environ 6 signaux par jour (de 3 à 13).
- **Verdict des backtests** : **pas d'avantage**. 649 trades à −0,09 R au départ ; rejoué sur 24 mois
  ≈ −0,1 R par trade ; les critères mesurent tous la même chose (on entre quand le mouvement est fait).
  Chances Topstep du bot : 22 % par tentative contre 29 % pour un témoin sans avantage.
- Outils autour : tests de résistance (frais, stop, objectif, entrée retardée), analyse des sauts de
  changement de contrat, **audit de faisabilité des prix** (aucun stop franchi par un saut, contrôle
  automatique après chaque backtest), apprentissage par tranches horaires.

## 5. Comptes simulés

- **Simulation** (onglet Simulation) : balance fictive, lots calculés pour risquer un % au stop,
  `/balance`. Actuellement départ 500 $ le 18/09, **risque 10 %**, balance **682 $** (plus haut 1 274 $).
- **Compte Topstep 50K simulé** (onglet Topstep) : rejoue tous les trades de la simulation à 0,5 %
  (250 $) de risque, en micro-contrats (1 à 50), règles Topstep (objectif +3 000 $, perte max 2 000 $
  sous le plus haut de fin de journée bloquée à 50 000 $, limite journalière 1 000 $, cohérence 50 %,
  fermé avant 15:10 Chicago, objectif du jour 1 200 $). Commandes `/topstep`, `/pris`, `/journal`,
  `/sortie`, `/retirer`, `/topstep reset`, `/topstep risque`, `/topstep objectif`.
  **État au 08/10 : 49 411 $, seulement 116 $ au-dessus de la perte maximale (49 295 $)** — le compte
  simulé est tout près de l'échec.
- Autres commandes Telegram : `/propose`, `/long`, `/short` (avec TP/SL possibles), `/status`,
  `/resume`, `/stop`, `/help`.

## 6. Les essais (détail dans `HYPOTHESES.md`) — 108 essais comptés

| Essai | Idée | Résultat |
|---|---|---|
| A / B | Repli dans la tendance ; retour à la VWAP sans tendance | Abandonnés (−0,23 R et −0,33 R sur 12 mois) |
| 2 | Setup A seulement sur Nasdaq et S&P 500 | Abandonné (+0,03 R, PF 1,06, moitiés de signe différent) |
| 3 | Laboratoire : 8 stratégies publiées × 7 actifs (ORB, momentum intraday, noise area, gap fade, London breakout, Donchian 1 h, RSI2…) | **`donchian_1h` or validé** (+0,19 R puis +0,12 R sur l'année jamais vue) ; tout le reste écarté. Mis en ombre. Donchian 1 h Bitcoin en ombre pour accumuler des preuves |
| 4 | Annonces macro : la pause sert-elle ? cassure après annonce ? veille de Fed ? | Pause gardée par prudence (pas de preuve) ; cassure après annonce écartée |
| 5 | `noise_area` avec stop réaliste | Écarté partout |
| 6 | Investissement halal : poche actions et pépites contre des témoins | Biais du survivant mesuré ; apport de la poche non démontré → poche ramenée à 10 % par défaut |
| 7 | Alerte de décrochage des stratégies en ombre (bootstrap 5 000 tirages, percentiles) | En place : alerte Telegram si un suivi réel sort de la norme ; bloque la promotion |
| 8 | **`donchian_day`** : Donchian 1 h fermé chaque soir (sortie 15:00 Chicago, pas d'entrée 15:00-17:00, compatible Topstep) | **Or VALIDÉ** (+0,11 R puis +0,07 R, 482 trades sur 24 mois, +0,09 R ± 0,05), pas « prouvé ». Nasdaq, S&P 500, Bitcoin écartés |
| 9 | Stratégies intraday sur l'or (Donchian 15 min / 30 min fermés le soir, ORB COMEX) | Toutes écartées : plus de trades = gain trop faible face aux frais |
| 10 | `donchian_day` sur 17 autres contrats CME | Les 17 écartés (seul le yen passe la découverte, pas la confirmation) |
| 11 | Tendance journalière sur 16 marchés depuis 2007 (Donchian 55/20, momentum 12 mois) | Donchian 55/20 écarté ; momentum 12 mois retenu (Sharpe ~0,5) puis **arrêté à la demande de Yanisse** (« c'est de l'investissement, pas du trading ») |
| 12 | La réaction aux annonces (NFP, CPI, FOMC) gardée jusqu'au soir, 2 ans | Rien retenu (pistes or et Fed non significatives) |
| 13 | Essai 12 rejoué sur 2010-2024 (HistData 1 min, jamais vu, ~430 annonces + ~87 Fed par actif) | **Rien retenu, pistes de l'essai 12 non confirmées** : le sens d'une annonce ne prédit pas la suite de la journée |

**Conclusions générales retenues**
- Le seul avantage trouvé et confirmé : **suivi de tendance Donchian sur l'or** (1 h, et version fermée
  chaque soir). Il vit de ses gros gagnants (36 % de trades gagnants), une partie peut venir de la forte
  hausse de l'or sur la période.
- Plus on trade court et souvent, plus les frais mangent tout (scalping, intraday 15/30 min).
- Les annonces macro ne donnent pas de direction exploitable.
- **Réussir un Combine en 1-2 semaines** : aucune stratégie testée ne fait mieux que le hasard sur
  10 jours de bourse ; réussir aussi vite relève de la chance.

## 7. Chances Topstep et prop firms

- Simulateur Monte-Carlo LuxAlgo (10 000 parcours, bootstrap par blocs des R nets Topstep), comparé à
  un **témoin** (mêmes trades recentrés à 0 R = hasard).
- **Combine 50K avec `donchian_day` or** : 58 % par tentative à 250 $ de risque (financé en ~59 jours de
  bourse pour la moitié des parcours), 42 % à 500 $ (~28 jours) ; témoin 29 % / 25 %. Premier retrait
  ~17 jours après le financement, au moins un retrait en 90 jours pour 61 % des comptes financés
  (témoin 24 %). Règle de retrait : 5 jours gagnants d'au moins 150 $.
- **En 2 semaines maximum** : rien ne bat le hasard (Donchian or 0-9 %, témoin 13-22 %).
- **Comparaison de 23 firmes / 55 comptes** (annuaire LuxAlgo, règles non vérifiées une à une, firmes
  israéliennes exclues) : les comptes CFD à perte max fixe 8-10 % donnent 70-80 % avec Donchian or mais
  en 140-230 jours ; Apex ~60 %, Tradeify ~52 %, Topstep ~47 % (version qui garde la nuit, interdite
  chez Topstep). Changer de firme = décision de Yanisse après vérification des règles sur leur site.

## 8. Ce qui tourne aujourd'hui

- **En signaux réels** : **`donchian_day` or** depuis le **08/10/2026 07:30 UTC** (choix de Yanisse).
  Message « SIGNAL RÉEL » à l'entrée (prix, stop, heure de sortie au plus tard en heure de Paris, micros
  MGC pour 250 $ de risque, avertissement) et « SORTIE » (résultat en R et en $), inscrit au journal du
  compte Topstep simulé. Rien d'envoyé de plus de 6 h. **Aucun signal réel encore observé** au moment
  de cette passation : à surveiller (≈ 0,9 trade par jour attendu).
- **En ombre** (sans notification, page Apprentissage) : `donchian_1h` or (depuis le 05/10),
  `donchian_1h` Bitcoin (05/10), `donchian_day` or (07/10), variante `horizon_3h_gold` (06/10).
  Premiers trades : Donchian 1 h or 2 trades −0,31 R en moyenne, Bitcoin 1 trade −1,04 R → « trop tôt ».
- **Contrôle de décrochage** (essai 7) sur ces suivis, référence figée dans `data/drift_reference.json`.
- **Bot de scalping** : continue normalement (signaux « fort »).

## 9. Investir halal (onglet « Investir », séparé du trading)

ETF islamiques (MSCI World / ACWI / USA / EM Islamic, Dow Jones Islamic, Wahed, sukuk HSBC, or Royal
Mint), portefeuilles types, simulateur, poche actions halal (momentum 12-1, révision trimestrielle,
**10 % par défaut** depuis l'essai 6), pépites (≤ 5 %), Bitcoin optionnel, SCPI NCap Éducation Santé,
plan du mois, contrôle charia AAOIFI, **calculateur de zakat**, entreprises israéliennes exclues.
L'ancien mode halal de trading (second bot) est arrêté. **Décision en attente de Yanisse** : confirmer
la poche à 10 % et les pépites ≤ 5 % (recommandation de l'essai 6).

## 10. Skills installées dans `.claude/skills/`

Backtest et validation : `backtest-expert`, `backtesting-frameworks`, `ml4t-*` (sur-ajustement, Sharpe
dégonflé, contrats continus, coupe-circuit, walk-forward, triple barrière, méta-labels, régimes,
sensibilité), `monte-carlo-*`, `edge-strategy-reviewer`, `strategy-pivot-designer`,
`trade-hypothesis-ideator`, `fill-feasibility-and-impossible-fill-detection`,
`live-vs-backtest-drift-monitoring`, `paper-trading-and-forward-test-protocol`,
`transaction-cost-and-market-impact-modeling`, `futures-roll-and-contract-mechanics`,
`futures-position-sizer`, `momentum-and-trend-following-pitfalls`, `regime-detection-for-strategy-switching`,
`residual-edge-analyzer`, `risk-limit-calibration-against-historical-drawdowns`,
`capital-allocation-and-strategy-lifecycle`, `demo-account-realism-gap-assessment`.
Investissement : `sharia-screening`, `zakat-calculator`, `rebalancing`, `historical-risk`,
`factor-investing`, `thesis-tracker`. Outil : `find-skills`.

## 11. Sources de données (toutes gratuites)

- Yahoo Finance : bougies 5 min (~60 jours), 1 h (~730 jours) pour les contrats `=F` ; journalier via
  `period1/period2` (`range=max` dégrade en mensuel) ; ETF ajustés pour le journalier long.
- Binance / Coinbase / Kraken pour les cryptos (Binance refuse les serveurs américains de GitHub).
- Dukascopy (CFD 1 min, mois numérotés à partir de 0, très limité en débit maintenant).
- **HistData.com** : fichiers annuels M1 (jeton sur la page annuelle, POST `/get.php`, heure EST fixe
  UTC−5) — utilisé pour l'essai 13.
- Dates officielles : BLS (archives via la Wayback Machine, contenu gzip), FOMC (liens
  `monetaryYYYYMMDDa.htm` de federalreserve.gov), calendrier ForexFactory.

## 12. Leçons techniques (erreurs à ne pas refaire)

- Un `str.replace` sans compte a modifié 3 lignes identiques dans `engine.py` → toujours une ancre
  unique et vérifier le nombre de remplacements.
- Ne pas tuer un processus avec `pkill -f` sur un motif qui correspond à son propre shell.
- Données de test synthétiques trop larges → aucun trade : resserrer les bougies.
- Les jours fériés (séances écourtées) cassent les règles « fermer à 15:00 » : gérer la dernière bougie
  de la séance.
- Semaines ISO ≠ week-ends de marché : détecter le samedi.
- Ne compter dans une courbe que les trades clos (pas le gain latent).
- Quand l'état du bot est commité toutes les 5 min, faire `git pull` avant de pousser.

## 13. Ce qui reste à faire / pistes

1. **Surveiller les premiers signaux réels `donchian_day` or** (message d'entrée, de sortie, journal
   Topstep) et l'alerte de décrochage.
2. **Compte Topstep simulé à 116 $ de l'échec** : en parler avec Yanisse (reset ? continuer ?).
3. Décision halal en attente (poche 10 %, pépites ≤ 5 %).
4. **Agent IA « trader confirmé »** : projet séparé dans le dépôt privé `trading-agent` (formation de
   12 Go à transcrire en local, mémo de la méthode, avis sur chaque signal via l'abonnement Claude, puis
   peut-être l'API). Ce qui concerne le bot : les **règles codables de la formation** reviendront ici
   comme **nouveaux essais pré-enregistrés** ; l'agent lit les signaux publics
   (`docs/dashboard.json`, `docs/live/<actif>.json`) — ne pas casser ces formats.
5. Idées non lancées : vérifier les règles réelles d'Apex / Tradeify si Yanisse veut changer de firme ;
   accumuler les trades en ombre avant toute promotion.
