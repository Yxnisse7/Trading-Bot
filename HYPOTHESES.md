# Hypothèses de setups — pré-enregistrement

Écrit **avant** tout backtest des setups (4 octobre 2026), pour ne pas ajuster l'idée aux résultats
(skills `ml4t-backtest-overfitting`, `trade-hypothesis-ideator`, `backtest-expert`). Toute
modification après le premier résultat doit être notée ici avec sa date et compte comme un nouvel
essai.

## Constat de départ (logique actuelle)

649 trades de backtest à −0,09 R net, aucun scénario de résistance gagnant. Le bot additionne des
critères de tendance qui mesurent presque tous la même chose : il entre quand le mouvement est déjà
fait. Gain maximal médian pendant un trade : 0,72 à 0,86 R, sous l'objectif ; entrer 10 min plus tard
est moins mauvais ; stop serré −0,25 R, stop large −0,05 R ; ADX ≥ 35 +0,07 R, ADX < 26 −0,10 R.

## Setup A — repli dans une tendance forte (`setup_repli`)

**Idée.** Dans une tendance forte, acheter le repli plutôt que l'extension : meilleur prix d'entrée,
stop placé sous une structure réelle (le creux du repli) et non dans le bruit.

**Règles (bougies 5 min clôturées, aucune donnée future) :**
1. Tendance : ADX 14 sur bougies 15 min clôturées ≥ 30, +DI > −DI (achat) ou −DI > +DI (vente), et
   clôture du dessus (achat) ou du dessous (vente) de l'EMA 50 sur 15 min.
2. Repli : sur les 6 dernières bougies 5 min, un plus bas (achat) a touché l'EMA 20 du 5 min.
3. Déclencheur : la bougie clôture au-dessus de l'EMA 20 et au-dessus du plus haut de la précédente
   (vente : symétrique).
4. Stop : sous le plus bas des 6 dernières bougies, moins 0,1 ATR 14 ; trade ignoré si le risque
   sort de 0,5 à 2,5 ATR.
5. Objectif : 1,5 R. Durée maximale : 24 bougies (2 h).

**Réglages :** ADX 30, EMA 20 / 50, fenêtre 6, objectif 1,5 R, 2 h — chiffres ronds, aucun optimisé.

## Setup B — retour à la VWAP sans tendance (`setup_vwap`)

**Idée.** Là où le suivi de tendance perd (ADX bas), un prix étiré loin de la moyenne du jour
pondérée par le volume (VWAP) tend à y revenir.

**Règles :**
1. Pas de tendance : ADX 14 sur bougies 15 min clôturées < 20.
2. Étirement : clôture à plus de 2 ATR 14 (5 min) de la VWAP du jour (UTC).
3. Déclencheur : bougie qui clôture sous le plus bas de la précédente (prix au-dessus de la VWAP →
   vente) ou au-dessus du plus haut de la précédente (prix sous la VWAP → achat).
4. Stop : au-delà de l'extrême des 6 dernières bougies, plus 0,1 ATR.
5. Objectif : la VWAP au moment de l'entrée ; trade ignoré si l'objectif vaut moins de 1 R.
   Durée maximale : 24 bougies (2 h).

**Réglages :** ADX 20, 2 ATR, fenêtre 6 — chiffres ronds.

## Critères de décision (identiques pour A et B)

Mesurés sur l'historique long (release « history », 12 mois si disponible) et sur les bougies Yahoo
récentes, frais réels inclus :

| Critère | Abandon si |
|---|---|
| Échantillon | moins de 100 trades |
| Gain net moyen | ≤ 0 R |
| Facteur de profit | < 1,1 |
| Stabilité dans le temps | signe différent entre la 1re et la 2de moitié, ou 2de moitié < 50 % de la 1re |
| Tests de résistance | moins de 60 % des scénarios dégradés gagnants |
| Plateau stop × objectif | moins de 50 % des réglages gagnants |

Un setup qui passe tout reste **en ombre sur le marché réel** (variante silencieuse) et ne devient un
signal réel que par la promotion automatique, avec la marge corrigée du nombre d'essais.

## Essai 2 — setup A limité au Nasdaq et au S&P 500 (`setup_repli` indices)

Écrit le 4 octobre 2026, **après** avoir vu le premier essai (A positif seulement sur ces deux
actifs, 39 et 51 trades) : c'est une idée tirée des résultats, donc suspecte tant qu'elle n'est pas
confirmée ailleurs. Règles de A inchangées, actifs limités à `nasdaq` et `sp500`.

**Données de confirmation :** historique long Dukascopy, **uniquement les bougies antérieures au
9 juillet 2026** (début des bougies déjà vues), soit environ octobre 2025 → juin 2026. Mêmes critères
d'abandon que plus haut (100 trades minimum, gain net moyen > 0, facteur de profit ≥ 1,1, deux
moitiés de même signe, tests de résistance). Frais : ceux du bot (0,01 % aller-retour).

## Essai 3 — laboratoire de stratégies (`trading_bot/strategies.py`)

Écrit le 5 octobre 2026, **avant** de lancer ces stratégies sur les données. Constat de départ : les
critères du bot sont presque tous présents sur chaque trade (6,6 en moyenne, ADX, tendances, VWAP et
RSI sur quasiment tous) ; ils ne trient rien, les repondérer par actif n'apporterait rien. On teste à la
place 8 idées différentes, tirées d'études ou de méthodes connues, réglages fixés d'avance :

| Stratégie | Règle (heures de New York sauf mention) |
|---|---|
| `orb5` | 1re bougie 9:30–9:35 : sens de sa couleur, stop à l'autre extrémité, objectif 10 R, sortie 16:00 (Zarattini & Aziz 2023) |
| `orb30` | Range 9:30–10:00 ; 1re clôture au-delà avant 12:00, stop à l'autre côté du range, sortie 16:00 |
| `intraday_mom` | Signe du rendement clôture de la veille (16:00) → 10:00 ; entrée 15:30 dans ce sens, sortie 16:00, stop 2 ATR (Gao, Han, Li & Zhou 2018) |
| `noise_area` | Bornes = ouverture (corrigée de l'écart) ± mouvement moyen depuis l'ouverture sur 14 jours à la même heure ; entrée aux demi-heures 10:00–15:30 hors bornes, sortie sous max(borne, VWAP) ou 16:00 (Zarattini, Aziz & Barbon 2024) |
| `gap_fade` | Écart d'ouverture de 0,25 % à 1 % : entrée contre l'écart à 9:35, objectif clôture de la veille, stop à même distance, sortie 12:00 |
| `london_breakout` | Range 00:00–07:00 UTC ; 1re clôture au-delà avant 11:00 UTC, stop autre côté, objectif 1 R, sortie 16:00 UTC |
| `donchian_1h` | Bougies 1 h : clôture au-delà du plus haut/bas des 20 heures, stop 2 ATR, sortie sur cassure des 10 heures ou 120 h |
| `rsi2_1h` | Bougies 1 h : RSI(2) < 10 au-dessus de la MM200 (achat) ou > 90 en dessous (vente), sortie RSI > 70 / < 30 ou 10 h, stop 2,5 ATR (Connors) |

Les 8 stratégies sont testées sur les 7 actifs (56 essais). Frais de référence : **frais réels Topstep**
(commission par micro + 1 tick) ; les frais du bot sont affichés à côté.

**Périodes.** Découverte : historique long du 28/09/2025 au 04/10/2026 (déjà utilisé pour le bot, pas
pour ces stratégies ; seul l'avantage du critère ORB du bot sur les indices y a été vu). Confirmation :
01/10/2024 → 27/09/2025, **jamais regardé** (téléchargement en cours au moment d'écrire).

**Critères.**
1. Découverte — candidat si : au moins 30 trades, gain net moyen > 0, facteur de profit ≥ 1,1, les deux
   moitiés positives.
2. Confirmation — un candidat est **validé** s'il refait au moins 30 trades, gain net moyen > 0 et
   facteur de profit ≥ 1,1 sur la période jamais vue.
3. **Prouvé** si, sur les deux périodes réunies, la borne basse du gain net moyen reste > 0 avec la marge
   corrigée pour 56 essais (z ≈ 3,1).

Un couple stratégie × actif validé part **en ombre** sur le marché réel (aucune notification) ; il ne
devient un signal réel que par la promotion automatique habituelle.

## Essai 4 — les annonces macro (`trading_bot/macro_history.py`)

Écrit le 5 octobre 2026, **avant** tout test. Annonces : emploi (NFP) et inflation (CPI) à 8:30 heure de
New York, décision de la Fed (FOMC) à 14:00, dates officielles d'octobre 2024 à octobre 2026 (fermeture
de l'État fédéral de l'automne 2025 comprise). Frais Topstep, mêmes données que l'essai 3.

1. **La protection actuelle sert-elle ?** Trades du backtest du bot ouverts de 45 min avant à 30 min après
   une annonce, comparés aux autres. Jugée utile si ces trades font pire d'au moins 0,1 R en moyenne ;
   sinon on proposera de la desserrer. Mesure indicative (peu de trades dans les fenêtres).
2. **`news_breakout`** (tous les actifs) : range des 15 min qui suivent l'annonce (8:30–8:45, ou
   14:00–14:15 pour la Fed) ; première clôture de 5 min au-delà avant 10:00 (Fed : 15:00), dans le sens
   de la cassure, stop de l'autre côté du range, sortie à 12:00 (Fed : 16:00). Le quart d'heure d'attente
   tient compte des 10 min de retard des données CME gratuites.
   Critères de l'essai 3, mais **20 trades minimum** au lieu de 30 (environ 30 annonces par an).
3. **`pre_fomc`** (Nasdaq, S&P 500) : achat la veille de la décision à 14:00, sortie à 13:55 le jour J,
   stop 2 ATR horaire (Lucca & Moench 2015, effet affaibli depuis 2016). Seulement 8 décisions par an :
   **résultat affiché pour information, sans verdict.**

## Essai 5 — `noise_area` avec un stop réaliste (`noise_area_v2`)

Écrit le 5 octobre 2026, **avant** de lancer cette version. Constat : `noise_area` sur le Bitcoin ne
gagnait que grâce à 5 % de trades à +17 à +37 R, issus de stops placés à quelques dollars du prix
(irréalisables : plus de 50 micros chez Topstep, un tick de glissement mange le gain) ; en % du prix,
pas d'avantage régulier.

**Règle :** entrées et sorties de `noise_area` inchangées, mais stop dur dès l'entrée à la plus grande des
deux distances : borne (max(borne, VWAP) à l'achat, min(borne, VWAP) à la vente) ou **1 ATR(14) des bougies
de 15 min closes**. Ce stop est aussi le dénominateur du R (plus de plancher à 0,5 ATR 5 min).

**Données :** les deux années ont déjà été regardées pour la version d'origine ; il n'existe donc plus de
données vierges pour cette idée. Jugement sur les 24 mois, actif par actif (7 essais), frais Topstep :
au moins 100 trades, gain net moyen > 0 **chacune des deux années**, facteur de profit ≥ 1,1, gain moyen
encore ≥ 0 **sans les 5 % meilleurs trades**, et gain moyen en % du prix > 0. Un actif qui passe tout part
en ombre sur le marché réel : c'est là que se fera la vraie confirmation.

## Essai 6 — investissement halal : poche actions et pépites (`trading_bot/invest_review.py`)

Écrit le 7 octobre 2026, **avant** tout calcul. Constat : le backtest de la poche (+40 %/an contre +12 %
pour l'ETF Monde islamique, 2021 → 2026) part de la composition **actuelle** de l'indice (les 150 plus
grosses aujourd'hui = celles qui ont le plus monté) : biais du survivant (skill `ml4t-survivorship-bias`).
Les compositions passées d'iShares ne sont plus téléchargeables gratuitement. Les pépites (rangs 151 à
400, momentum 6 mois) font +9,7 %/an contre +10,7 % pour l'ETF, deux fois plus volatiles.

**1. Témoins dans le même univers** (mêmes actions, même biais, mêmes frais de 0,3 % par achat ou vente,
révision tous les 3 mois) : (a) toutes les actions de l'univers à poids égal ; (b) 500 tirages de N actions
au hasard (N = 10 pour la poche, 5 pour les pépites), mêmes règles de maintien. L'**apport du momentum**
est l'écart avec ces témoins, pas avec l'ETF. Verdict « apport démontré » si la règle bat le poids égal
**et** fait mieux que 90 % des tirages, **sur chacune des deux moitiés** de la période. Sinon : apport non
démontré → je recommande de ramener la part (poche ≤ 10 %, pépites ≤ 5 %) ; rien n'est retiré sans
l'accord de Yanisse.

**2. Deux variantes de la règle** (2 variantes × 2 poches = 4 essais), appliquées au choix des actions :
- *anti-krach* : une action ayant perdu 25 % ou plus le mois précédent n'est ni achetée ni gardée ;
- *corrélation* : une candidate dont les rendements mensuels des 24 derniers mois sont corrélés à plus de
  0,75 avec une action déjà retenue est sautée (contre les paris cachés sur un seul thème).
Adoptée seulement si, par rapport à la règle actuelle : chute maximale réduite d'au moins 3 points, CAGR
pas plus bas de plus de 1 point, et chute maximale pas pire sur chaque moitié. Sinon la règle reste telle
quelle.

**3. Risque du portefeuille complet**, pour information (skill `historical-risk`) : portefeuille
« Dynamique » réglé comme sur le site (poche 20 %, pépites 5 %, Bitcoin 3 %, reste en ETF et or),
rééquilibré chaque mois : chute maximale, pire année glissante, perte mensuelle à 95 %, et ce que cela
donne en euros pour 1 000 € puis 200 €/mois.

**4. Contrôle charia AAOIFI** (skill `sharia-screening`, norme 21), sur les actions et pépites
sélectionnées, déjà filtrées par MSCI (dette et liquidités < 33,33 % du **total de l'actif**). AAOIFI
rapporte à la **capitalisation** : dette portant intérêt (hors loyers) < 30 %, liquidités et placements à
intérêt < 30 %, revenus d'intérêts < 5 % du chiffre d'affaires, sur les derniers comptes annuels. Résultat
affiché par action (conforme / non conforme AAOIFI / données manquantes) avec son taux de purification
(intérêts ÷ chiffre d'affaires). Aucune exclusion automatique : appliquer la norme plus stricte reste un
choix de Yanisse.

## Essai 7 — alerte de décrochage des stratégies en ombre (`trading_bot/drift.py`)

Écrit le 7 octobre 2026, **avant** de comparer quoi que ce soit (skill `live-vs-backtest-drift-monitoring`).
Suivies en ombre : `donchian_1h` or et Bitcoin (laboratoire, essai 3) et la variante `horizon_3h_gold`.
Question : leurs trades réels restent-ils dans ce que leur backtest de 24 mois laissait attendre ?

**Référence figée** : les R nets Topstep du backtest de 24 mois de chaque stratégie (même règle, même
calcul du R que les trades en ombre), enregistrés une fois dans `data/drift_reference.json`. Elle ne change
plus, sauf si la règle de la stratégie change (ce qui serait un nouvel essai).

**Mesure**, à chaque nouveau trade clos en ombre (n trades depuis le début du suivi) : 5 000 tirages de n
trades consécutifs dans la référence (bootstrap en blocs de 5 trades en moyenne, pour garder les séries de
pertes). Deux chiffres : le **rang du gain cumulé** réel parmi les tirages (percentile) et le **rang de la
pire baisse** réelle (perte maximale depuis un sommet, en R).

**Seuils fixés d'avance** :
- « dans la norme » : gain cumulé au-dessus du 5e percentile et pire baisse sous le 95e ;
- « à surveiller » (dès 5 trades) : gain cumulé sous le 5e percentile **ou** pire baisse au-dessus du 95e ;
- « décroché » (dès 10 trades) : gain cumulé sous le 1er percentile **ou** pire baisse au-dessus du 99e.

**Action** : message Telegram quand l'état s'aggrave (une fois par changement), état affiché sur la page
Apprentissage. « Décroché » bloque la promotion de `horizon_3h_gold` tant qu'il dure ; pour Donchian (aucun
signal réel), le suivi continue, mais la stratégie ne pourra pas passer en signal réel avant d'être
revenue dans la norme. Aucune autre décision automatique. Un « décroché » peut venir d'un avantage qui
s'efface, d'une différence de données (Yahoo en direct, Dukascopy et Binance dans le backtest) ou d'un bug :
la cause est cherchée à la main.

## Essai 8 — Donchian fermé chaque soir (`donchian_day`), compatible avec Topstep

Écrit le 7 octobre 2026, **avant** de lancer cette version. Constat : `donchian_1h` sur l'or (validé à
l'essai 3) garde ses positions d'un jour à l'autre (215 trades sur 313) et le week-end (67). Topstep et la
plupart des firmes futures imposent de tout fermer avant 15:10 heure de Chicago : la stratégie n'y est pas
permise telle quelle.

**Règle** (aucun réglage nouveau, rien d'ajusté après coup) : exactement `donchian_1h` (cassure du canal des
20 dernières bougies de 1 h à la clôture, stop à 2 ATR(14), sortie à la clôture d'une bougie qui casse le
canal des 10 dernières, 120 bougies au plus), avec deux ajouts :
- **sortie forcée à 15:00 heure de Chicago**, à la clôture de la bougie 1 h qui finit à 15:00, si la position
  est encore ouverte (10 minutes de marge avant la fermeture imposée de 15:10) ;
- **aucune entrée** sur une bougie qui clôture entre 15:00 et 17:00 heure de Chicago (fin de séance et
  pause du marché) ; la séance suivante démarre à 17:00 comme chez Topstep.
Le vendredi, la sortie de 15:00 évite le week-end.

**Actifs** (4 essais) : or (principal), Nasdaq, S&P 500, Bitcoin, les quatre actifs annoncés par le bot.
Frais Topstep réels.

**Verdict** avec les critères de l'essai 3 : découverte du 28/09/2025 au 04/10/2026 (≥ 30 trades, gain
moyen > 0, facteur de profit ≥ 1,1, les deux moitiés positives), puis confirmation sur 10/2024 → 09/2025
(≥ 30 trades, gain > 0, facteur de profit ≥ 1,1). « Validé » si les deux passent ; « prouvé » si la borne
basse sur 24 mois reste > 0 avec la marge corrigée pour 74 essais (70 + 4). Les critères de l'essai 5 (deux
années positives, résultat sans les 5 % meilleurs trades, gain en % du prix) sont donnés pour information.
Limite connue : ces données ont déjà servi à valider `donchian_1h` ; la règle n'est pas réglée dessus, mais
ce n'est pas une donnée vierge.

**Suite** : validé sur l'or → suivi en ombre sur le marché réel (comme `donchian_1h`) et chances Topstep
recalculées avec ses trades ; écarté → la conclusion reste « Donchian n'est jouable que sur un compte qui
permet de garder la nuit ».

## Essai 9 — stratégies intraday sur l'or, pour aller plus vite au Combine

Écrit le 7 octobre 2026, **avant** de lancer ces stratégies. Constat : `donchian_day` (essai 8) gagne sur l'or
mais ne fait qu'environ un trade par jour : il réussit le Combine en ~1,5 à 3 mois, et en 2 semaines il fait
moins bien que le hasard (5 % contre 22 % pour le témoin à 500 $). Pour réussir vite sans compter sur la chance,
il faut plusieurs trades par jour qui gagnent chacun en moyenne. L'or est le seul marché où une tendance a tenu ;
les stratégies intraday de l'essai 3 (ORB de 9:30, momentum intraday, comblement d'écart, RSI 2, Londres) n'y ont
pas tenu. Trois idées nouvelles seulement (3 essais, 77 au total), réglages fixés ici :

- **A. `donchian_15m_day`** : la règle de `donchian_day` sur des bougies de **15 min** (cassure du canal des 20
  dernières bougies à la clôture, stop à 2 ATR(14) de 15 min, sortie à la clôture d'une bougie qui casse le canal
  des 10 dernières, 120 bougies au plus, sortie forcée à 15:00 heure de Chicago ou à la dernière clôture d'une
  séance écourtée, aucune entrée de 15:00 à 17:00) ;
- **B. `donchian_30m_day`** : la même sur des bougies de **30 min** ;
- **C. `comex_orb`** : cassure de l'ouverture du COMEX (marché de l'or, 8:20 heure de New York). Range = les 30
  premières minutes (bougies 5 min de 8:20 à 8:45) ; entrée à la clôture de la première bougie 5 min qui clôture
  au-dessus ou au-dessous du range, avant 12:00 heure de New York ; stop de l'autre côté du range ; sortie au stop
  ou à 15:00 heure de Chicago. Un trade par jour au plus.

**Verdict** (frais Topstep réels, données de l'or) : critères de l'essai 3, découverte du 28/09/2025 au
04/10/2026 puis confirmation 10/2024 → 09/2025 ; « prouvé » avec la marge corrigée pour 77 essais.
**Utile pour aller vite** si, en plus, la stratégie validée réussit le Combine 50K en 10 jours de bourse au plus
au moins 10 points plus souvent que son témoin sans avantage (mêmes trades, gain moyen ramené à 0), au risque où
elle fait le mieux parmi 250, 500 et 750 $. Rien d'autre n'est essayé après coup sur ces données (ni autre
durée de bougie, ni autre heure) : ce serait un nouvel essai.

**Suite** : validée → suivi en ombre sur le marché réel avec le contrôle de décrochage ; écartée → on le dit.
Ajout aux règles Topstep simulées : pour retirer, 5 jours gagnants d'au moins 150 $ (pas forcément d'affilée,
aide Topstep), pour mesurer le délai jusqu'au premier retrait.

## Essai 10 — la tendance fermée chaque soir sur 17 autres contrats CME

Écrit le 7 octobre 2026, **avant** de télécharger ces données. Constat : la seule règle validée
(`donchian_day`, essai 8) est un suivi de tendance, l'effet le mieux documenté sur les contrats à terme
(Moskowitz, Ooi & Pedersen, 2012 ; Hurst, Ooi & Pedersen, 2017), surtout sur les matières premières, les taux
et les devises. Il a échoué sur les indices actions (Nasdaq, S&P 500), qui ont tendance à revenir en arrière
dans la journée. Sur l'or seul, il ne fait qu'un trade par jour : trop lent. Si la même règle tient sur
d'autres marchés de tendance, on aurait plus de trades gagnants en moyenne, donc un Combine plus rapide, pour
une raison connue et non par réglage.

**Règle** : exactement `donchian_day` (essai 8), sans rien changer, sur des bougies de 1 h.
**Données** : Yahoo Finance, bougies de 1 h des contrats « =F » (contrat le plus proche), de mai 2024 à
octobre 2026, gardées hors du dépôt (`data/history/*_1h.json`).
**Marchés** (17 essais nouveaux, 94 au total) et contrat Topstep le plus petit, frais aller-retour TopstepX
(help.topstep.com, octobre 2026) + 1 tick de glissement :
- métaux : argent (SIL, 2,72 $), cuivre (MHG, 1,92 $), platine (PL, 4,32 $) ;
- énergie : pétrole (MCL, 1,92 $), gaz naturel (MNG, 2,12 $), fioul (HO, 4,02 $), essence (RB, 4,02 $) ;
- taux : 10 ans US (ZN, 2,62 $), 30 ans US (ZB, 2,76 $) ;
- céréales : maïs (ZC), soja (ZS), blé (ZW), 5,28 $ chacun ;
- devises : euro (M6E), livre (M6B), dollar australien (M6A), 1,00 $ chacun ; yen (6J) et dollar canadien
  (6C), 4,22 $ (pas de micro chez Topstep).
L'or (MGC) sur ces mêmes données Yahoo sert de contrôle (pas un essai nouveau).

**Verdict par marché** : critères de l'essai 3, découverte du 28/09/2025 au 07/10/2026 puis confirmation de
mai 2024 au 27/09/2025 ; « prouvé » avec la marge corrigée pour 94 essais.
**Changements de contrat** : la position est fermée chaque soir, donc jamais tenue pendant un changement ; seule
une fausse cassure à la reprise est possible. Contrôle fixé d'avance : une séance « avec saut » est une séance
dont l'écart d'ouverture dépasse 5 fois l'écart d'ouverture médian du marché ; un marché n'est validé que s'il
passe aussi les critères sans les trades entrés dans les 3 premières bougies de ces séances.
**Jouable** à un risque donné si, pour au moins 80 % des trades, le stop d'un seul contrat coûte au plus ce
risque (sinon il faudrait moins d'un contrat).
**Portefeuille** : les marchés validés et jouables à 500 $ (plus l'or) sont rejoués ensemble dans l'ordre du
temps : gain moyen sur chacune des deux périodes, puis chances Topstep (réussite, en 2 semaines, délai) contre
leur témoin sans avantage. Utile pour aller vite si la réussite en 10 jours dépasse le témoin d'au moins
10 points.
Avec 17 essais, un ou deux marchés peuvent passer par chance : un marché validé seul part en ombre, rien de
plus ; le portefeuille n'est retenu que si son gain est positif sur les deux périodes.

## Essai 11 — suivi de tendance sur bougies journalières, 16 marchés, depuis 2007

Écrit le 7 octobre 2026, **avant** de télécharger ces données. Constat (essai 10) : fermée chaque soir, la
tendance ne rapporte presque rien ; l'effet documenté (Moskowitz, Ooi & Pedersen, 2012 ; Hurst, Ooi & Pedersen,
2017, plus d'un siècle de données) se joue sur des semaines et des mois. Autre façon de trader : un signal le
soir après la clôture, des positions gardées des jours ou des semaines, sur beaucoup de marchés.

**Données** : Yahoo Finance, cours journaliers ajustés (dividendes) de 16 ETF qui détiennent les contrats et les
roulent eux-mêmes : leur prix suit ce que gagne celui qui garde le contrat, sans les sauts artificiels des séries
« =F ». Or GLD, argent SLV, pétrole USO, gaz UNG, agriculture DBA, métaux industriels DBB, taux US 7-10 ans IEF,
taux US 20 ans+ TLT, euro FXE, yen FXY, livre FXB, dollar australien FXA, dollar canadien FXC, actions US SPY,
Nasdaq 100 QQQ, actions émergentes EEM. Période commune : mars 2007 → octobre 2026. Gardées hors du dépôt.
**Frais** : 0,05 % du prix par aller-retour (écart et commission), en plus des frais déjà dans le prix de l'ETF.

**A. Cassure de Donchian 55/20 (« Turtle », système 2)**, réglages publiés, rien d'ajusté : signal à la clôture
au-dessus du plus haut (au-dessous du plus bas) des 55 dernières séances, entrée à l'ouverture suivante, stop à
2 ATR(20) de l'entrée (exécuté à l'ouverture si elle est au-delà), sortie à l'ouverture qui suit une clôture
sous le plus bas (au-dessus du plus haut) des 20 dernières séances. Une position par marché, achat et vente.
Résultat en R (gain ÷ risque au stop).
**B. Momentum sur 12 mois (Moskowitz, Ooi & Pedersen, 2012)** : chaque fin de mois, position dans le sens du
rendement des 12 derniers mois sur chaque marché, taille inverse à sa volatilité (60 séances), poids égal entre
marchés, frais sur chaque changement de taille.

**Verdict** (2 essais, 96 au total), jugé sur le **portefeuille** des 16 marchés, pas marché par marché (un
suivi de tendance n'est rentable qu'en diversifiant ; les résultats par marché sont donnés pour information) :
deux moitiés, mars 2007 → décembre 2016 et janvier 2017 → octobre 2026. A est retenu si son gain moyen par trade
est > 0 avec un facteur de profit ≥ 1,1 sur **chaque** moitié et si au moins 60 % des années civiles sont
positives. B est retenu si son rendement annuel est > 0 et son ratio de Sharpe ≥ 0,3 sur **chaque** moitié.
Pour information : chute maximale, résultat sans les 5 % meilleurs trades (un suivi de tendance vit de ses
gros gagnants : ce critère n'est pas éliminatoire ici), corrélation avec les actions.

**Mise en pratique**, pour information : positions gardées la nuit et le week-end, donc **pas chez Topstep** ;
possible sur un compte CFD qui le permet ou un compte personnel. Simulation d'un défi CFD 50 000 $ type (objectif
+10 % puis +5 %, perte maximale fixe de 10 %, perte journalière de 5 %) sur la courbe de gain journalière de A,
à 0,5 % et 1 % du compte risqué par trade : chances de réussir et délai. Remarque halal : sur un compte CFD,
garder une position la nuit coûte des intérêts (« swap ») ; il faudrait un compte sans swap.
**Suite** : retenu → suivi en ombre sur le marché réel (signal du soir) ; écarté → on le dit.

## Essai 12 — la réaction aux annonces macro, gardée plus longtemps

Écrit le 8 octobre 2026, **avant** de mesurer quoi que ce soit. Idée de Yanisse : ajouter ce que les calculs
de prix ne voient pas, les annonces, sur un horizon plus long que le direct. Aucune source gratuite accessible
ne donne l'historique des prévisions (consensus) : ForexFactory, Myfxbook, Investing.com bloquent, Trading
Economics est payant, le jeu de données ouvert fxmacrodata n'est pas encore publié. La surprise est donc
mesurée par **la réaction du marché** : sens du mouvement entre la clôture de la bougie 5 min juste avant
l'annonce et 30 min après. C'est la lecture du chiffre par le marché, quelle qu'ait été la prévision.
Différence avec l'essai 4 (`news_breakout`, cassure du range de 15 min, déjà écartée) : on ne joue pas la
cassure en direct, on se demande si le sens donné par l'annonce **continue pendant des heures**.

**Annonces** : emploi (NFP) et inflation (CPI) à 8:30 heure de New York, décisions de la Fed (FOMC) à 14:00,
octobre 2024 → octobre 2026 (`macro_history.py`, environ 60 avec données). **Actifs** : or, Nasdaq, S&P 500,
euro (bougies 5 min de l'historique long, frais Topstep).

**H1, dérive après l'annonce** (4 essais, 100 au total) : entrée 30 min après l'annonce dans le sens de la
réaction, sortie à 15:00 heure de Chicago le même jour (compatible Topstep). Résultat en unités d'ATR 1 h
(14) au moment de l'entrée, frais compris. Retenue pour un actif si le gain moyen est > 0 avec une statistique
t ≥ 2, **et** positif sur chacune des deux années (10/2024 → 09/2025, 10/2025 → 10/2026). Pour information :
même trade gardé jusqu'au lendemain 15:00 ; réactions fortes seulement (au-dessus de la médiane de l'actif).
**H2, filtre pour Donchian or** (information, pas d'essai) : les jours d'annonce, trades de `donchian_day` sur
l'or ouverts après la réaction, séparés en « dans le sens de la réaction » et « contre ». Si les trades contre
font au moins 0,3 R de moins avec au moins 15 trades de chaque côté, un filtre est proposé, suivi d'abord en
ombre ; sinon rien ne change.
Limite connue : environ 60 annonces, donc un échantillon petit ; seul un effet net peut passer.

## Essai 13 — l'essai 12 rejoué sur 2010-2024, données jamais regardées

Écrit le 8 octobre 2026, **avant** de télécharger ces données. L'essai 12 (deux ans, ~60 annonces) n'a rien
retenu, mais deux pistes restaient ouvertes : l'or (+0,32 ATR, positif les deux années, t 1,03) et, observé
après coup, les décisions de la Fed (réaction qui continue sur les 4 actifs, 15-16 décisions). Les rejouer sur
une période **jamais regardée** est le seul moyen honnête de trancher.

**Annonces** : emploi (NFP) et inflation (CPI), 8:30 heure de New York, janvier 2010 → septembre 2024 (dates
exactes tirées des archives du BLS, via la copie de la Wayback Machine, bls.gov bloquant les robots) ; décisions
prévues de la Fed, 14:00 heure de New York, janvier 2013 → septembre 2024 (dates des communiqués sur
federalreserve.gov ; avant 2013 l'heure variait, donc exclu ; communiqués extraordinaires exclus).
**Prix** : bougies 1 min Dukascopy regroupées en 5 min, seulement la veille, le jour et le lendemain de chaque
annonce, pour l'or, le S&P 500, le Nasdaq et l'euro (un indice absent de Dukascopy les premières années est
simplement absent). Gardés hors du dépôt.

**Règles** : exactement celles de l'essai 12 (réaction entre la bougie 5 min d'avant l'annonce et 30 min
après, entrée dans ce sens, sortie à 15:00 heure de Chicago, résultat en ATR 1 h, frais Topstep).
**H1** (4 essais) : par actif, toutes annonces confondues : gain moyen > 0, t ≥ 2, et positif sur chacune des
deux moitiés (2010 → 2017-03, 2017-04 → 2024-09). **H3, la Fed** (4 essais, 108 au total) : par actif, sur les
décisions de la Fed seulement, mêmes critères (moitiés : 2013 → 2018, 2019 → 2024). Pour information : sortie le
lendemain, réactions fortes, emploi et inflation séparés.
Une piste retenue ici serait suivie en ombre sur les annonces à venir avant tout signal réel.
**Modification avant tout résultat (8 octobre 2026)** : Dukascopy limite le débit (10 à 25 s par fichier puis
refus, plus de 20 h pour 15 ans) ; la source devient **HistData.com** (bougies 1 min gratuites, une année par
fichier ; or XAUUSD, euro EURUSD, S&P 500 SPXUSD, Nasdaq 100 NSXUSD ; heure de l'Est sans changement d'heure,
convertie en UTC). Règles et critères inchangés. Contrôle prévu : la plus forte agitation des jours d'emploi doit
tomber dans la bougie de 8:30 heure de New York (sinon décalage d'heure, corrigé avant tout verdict).

## Essai 14 — entrer sur repli plutôt qu'après l'accélération : 13 idées, 49 cellules

Écrit le 9 octobre 2026, **avant** de lancer le moindre calcul. Constat de départ : du 6 au 8 octobre, le bot
a perdu 12 trades sur 13, presque tous des entrées prises après un mouvement déjà fait, stoppées au premier
rebond (c'est le défaut connu depuis le premier essai). Idée commune : n'entrer que sur un repli près de la
moyenne, dans le sens de la tendance de l'unité supérieure, avec de la place devant soi et un objectif plus
lointain que le risque. Yanisse a demandé de tester toutes les idées codables en une fois.

**Données** : historique long 5 min (release « history »), or, Nasdaq, S&P 500, Bitcoin (les 4 actifs
annoncés). Découverte du 28/09/2025 au 04/10/2026, confirmation du 10/2024 au 27/09/2025. Frais Topstep réels
(Bitcoin : frais du bot). Indicateurs calculés sur des bougies **clôturées** uniquement. Moyenne 20 = moyenne
simple des 20 dernières clôtures ; ATR 14 ; RSI 21. « Veille » = la journée UTC de cotation précédente.

**Famille A — filtres sur les trades du bot actuel** (le bot est rejoué sur les 24 mois avec ses réglages du
jour ; un filtre retire des trades, il n'en ajoute pas) :
- **A1 étirement** : trade retiré si, à l'entrée, la clôture est à plus de 1,5 ATR 14 (5 min) de la moyenne 20
  (5 min), du côté du trade.
- **A2 journée sans direction** : trade retiré si le prix d'entrée est dans le range (plus haut / plus bas) de
  la veille **et** si la moyenne 20 en 15 min a bougé de moins de 0,25 ATR 14 (15 min) sur les 4 dernières
  bougies de 15 min.
- **A3 obstacle** : trade retiré si le plus haut de la veille (achat) ou le plus bas de la veille (vente) se
  trouve entre l'entrée et l'objectif.
- **A4 marge de l'unité supérieure** : trade retiré si le RSI 21 en 1 h est au-dessus de 65 (achat) ou en
  dessous de 35 (vente).
- **A5 indices qui ne suivent pas** (Nasdaq et S&P 500 seulement) : trade retiré si l'autre indice clôture
  du mauvais côté de sa moyenne 20 en 15 min (sous la moyenne pour un achat, au-dessus pour une vente).

**Famille C — autres sorties sur les mêmes entrées du bot** (même entrée, même stop initial) :
- **C11 deux moitiés** : la moitié sort à +1 R ; le stop du reste passe alors au prix d'entrée, puis suit le
  plus bas (achat) ou le plus haut (vente) des 3 dernières bougies 5 min clôturées ; pas d'objectif ; sortie au
  plus tard après 36 bougies (3 h). Résultat = moyenne des deux moitiés.
- **C12 stop temps** : sortie à la clôture de la 6e bougie (30 min) si le trade n'a jamais atteint +0,5 R ;
  sinon sortie normale du bot (objectif, stop ou 1 h).
- **C13 retour sous la moyenne** : sortie à la clôture d'une bougie 5 min qui finit du mauvais côté de la
  moyenne 20 (5 min) ; sinon sortie normale du bot.

**Famille B — nouveaux setups** (bougies 15 min regroupées depuis le 5 min ; aucune entrée de 15:00 à 17:00
heure de Chicago, sortie forcée à 15:00 heure de Chicago, au plus 16 bougies de 15 min ; Bitcoin : sortie
après 16 bougies seulement ; trade ignoré si le risque sort de 0,3 à 3 ATR 14 (15 min) ; objectif 3 R sauf
mention) :
- **B6 repli** : tendance 1 h (clôture au-dessus de la moyenne 20 en 1 h, et moyenne plus haute qu'il y a
  3 bougies ; vente symétrique) ; au moins 3 plus bas descendants d'affilée en 15 min (au plus 6) ; plus bas de
  la dernière bougie à moins de 0,5 ATR de la moyenne 20 (15 min). Entrée si la bougie suivante dépasse le plus
  haut de la dernière bougie (à ce prix) ; stop sous le plus bas des 2 dernières bougies.
- **B7 cassure avec volume** : clôture au-dessus du plus haut des 20 bougies précédentes avec un volume au
  moins 2 fois la moyenne de ces 20 bougies (vente symétrique) ; entrée à la clôture ; stop sous le plus bas de
  ces 20 bougies.
- **B8 bougie étroite** : bougie au range le plus petit des 7 dernières, clôture à moins de 0,5 ATR de la
  moyenne 20 (15 min), tendance 1 h comme B6 ; entrée si la bougie suivante dépasse son extrême dans le sens de
  la tendance ; stop à l'autre extrême.
- **B9 cassure ratée** : une bougie dépasse le plus haut des 20 précédentes avec un volume sous leur moyenne,
  puis clôture en dessous de ce plus haut → vente à la clôture, stop 0,1 ATR au-dessus de son plus haut,
  objectif le plus bas des 20 bougies (achat symétrique) ; ignoré si l'objectif vaut moins de 1 R.
- **B10 ouverture hors du range de la veille** (Nasdaq, S&P 500 : 9:30 heure de New York ; or : 8:20) :
  range des 15 premières minutes ; si la clôture de 15 min est au-dessus du plus haut de la veille, achat à la
  première clôture 5 min au-dessus du range avant 12:00 heure de New York (vente symétrique sous le plus bas
  de la veille) ; stop de l'autre côté du range ; objectif 3 R ; sortie à 15:00 heure de Chicago.

**Verdict par cellule** (idée × actif) : critères de l'essai 3, sur le résultat **avec** la règle (bot filtré,
bot avec la nouvelle sortie, ou setup seul) : découverte (≥ 30 trades, gain moyen net > 0, facteur de profit
≥ 1,1, deux moitiés positives) puis confirmation (≥ 30 trades, gain > 0, facteur de profit ≥ 1,1).
« Validé » si les deux passent ; « prouvé » si la borne basse sur 24 mois reste > 0 avec la marge corrigée pour
**157 essais** (108 + 49). Pour les familles A et C, on donne aussi l'écart avec le bot sans la règle, pour
information. Une cellule validée irait **en ombre** sur le marché réel, jamais directement en signal réel.
Les idées « risque » (1 % par trade, perte maximale par jour) ne sont pas testées : ce sont des réglages
de prudence, pas des sources d'avantage.

## Essai 15 — les autres règles codables : 25 idées, 97 cellules

Écrit le 9 octobre 2026, **avant** tout calcul. Après l'essai 14, Yanisse a demandé de tester toutes les règles
codables restantes de notre liste. Déjà testées ailleurs (pas refaites) : pause autour des annonces (essai 4),
ouverture américaine et ORB (essais 3, 9, 14), étirement, obstacle, marge du RSI, repli, bougie étroite,
cassure avec volume, cassure ratée, deux moitiés, stop temps (essai 14), clôture avant la fin de séance
(essai 8). Non testables ici : liste fermée de marchés (le bot n'en suit déjà que 4), filtres sur actions
(pas de données d'actions dans le bot), ne jamais reculer son stop ni renforcer une perte (le bot ne le fait
jamais).

**Données, découpage, frais, indicateurs** : identiques à l'essai 14 (4 actifs, découverte 28/09/2025 →
10/2026, confirmation 10/2024 → 27/09/2025, frais Topstep, Bitcoin frais du bot, bougies clôturées
seulement). En plus : stochastique lent 21,3,3 (%K brut sur 21 bougies lissé sur 3, %D = moyenne 3 du %K
lissé) ; VWAP de séance pondéré par le volume.

**Famille F — filtres sur les trades du bot** (mêmes trades rejoués qu'à l'essai 14) :
- **F1 biais moyenne 1 h** : retiré si la clôture 1 h est du mauvais côté de la moyenne 20 (1 h) ou si
  cette moyenne va dans l'autre sens sur 3 bougies.
- **F2 biais oscillateur 1 h** : retiré si le RSI 21 et le %K du stochastique (1 h) sont tous les deux du
  mauvais côté de 50.
- **F3 tendance journalière** : retiré si la clôture de la veille (jour UTC) est du mauvais côté de la
  moyenne 20 des clôtures journalières.
- **F4 bougie de contrôle** : retiré si, parmi les 8 dernières bougies 15 min, une bougie a un range d'au
  moins 2 ATR 14 (15 min) et que le prix d'entrée est encore entre son plus haut et son plus bas.
- **F5 marché plat** : retiré si la moyenne 20 (15 min) a bougé de moins de 0,25 ATR sur 4 bougies **et** si
  le RSI 21 (15 min) est entre 45 et 55.
- **F6 range trop étroit** : retiré si le range des 12 dernières bougies 5 min est inférieur à 2 × (distance au
  stop + coût aller-retour en points).
- **F8 heures actives** : gardé seulement entre 8:00 et 12:00 (sauf 9:30-9:45) et entre 14:00 et 16:00 heure de
  New York, pour les 4 actifs.

**Famille G — gestion des trades du bot** (mêmes entrées) :
- **G30 objectif 3 R** (même stop), sortie au plus tard après 3 h.
- **G31 stop sous les 2 dernières bougies 5 min** moins 0,1 ATR (au-dessus pour une vente), objectif recalé à
  1,5 fois ce nouveau risque ; résultat en R du nouveau risque.
- **G34 stop suiveur** : pas d'objectif ; après chaque bougie, stop remonté au plus bas des 3 dernières
  bougies (plus haut pour une vente) s'il est meilleur ; 3 h au plus.
- **G35 objectif posé un peu avant** : distance de l'objectif réduite de 7 % (1,4 R au lieu de 1,5 R).
- **G36 oscillateur qui repasse 50** : sortie à la clôture quand le RSI 21 (5 min) repasse sous 50 (au-dessus
  pour une vente) ; stop et objectif inchangés.
- **G37 bougie exceptionnelle** : sortie à la clôture d'une bougie 5 min dans le sens du trade dont le range
  vaut au moins 2,5 ATR 14 ; le reste inchangé.
- **G38 renfort** : moitié de la taille à l'entrée, objectif 3 R ; à +1 R, l'autre moitié est ajoutée et le
  stop des deux passe au prix d'entrée ; 3 h au plus ; résultat en R de la taille complète.
- **G39 demi-taille en marché indécis** : taille divisée par deux quand le trade aurait été retiré par F5 ou
  par A2 (essai 14).
- **G40 limites du jour** : par actif, au plus 3 trades par jour de New York, et plus aucun après 2 pertes
  dans la journée.

**Famille S — nouveaux setups en 15 min** (règles communes de la famille B de l'essai 14 : pas d'entrée de
15:00 à 17:00 heure de Chicago sur les futures, sortie forcée à 15:00 Chicago, 16 bougies au plus, risque
entre 0,3 et 3 ATR 14 (15 min), objectif 3 R sauf mention, une position à la fois ; ventes symétriques) :
- **S15 repli du RSI** : tendance 1 h (comme B6) ; le RSI 21 est monté au-dessus de 55 dans les 12 dernières
  bougies, n'est pas passé sous 40 depuis 6 bougies, était entre 40 et 50 à la bougie précédente et repasse
  au-dessus de 50 → achat à la clôture, stop sous le plus bas des 5 dernières bougies.
- **S16 divergence validée** : un plus bas des 20 bougies avec RSI sous 30, puis dans les 30 bougies un
  nouveau plus bas plus bas avec RSI au-dessus de 30, puis le RSI repasse au-dessus de 50 → achat à la clôture,
  stop sous le second creux.
- **S17 divergence avortée** : tendance 1 h haussière ; nouveau plus haut des 20 bougies avec un RSI plus bas
  qu'au plus haut précédent (dans les 30 bougies) ; puis une clôture au-dessus de ce nouveau plus haut dans
  les 10 bougies → achat, stop sous le plus bas des 5 dernières bougies.
- **S25 creux cassé puis repris** : tendance 1 h haussière ; une bougie casse le plus bas des 10 précédentes
  et une des 2 bougies suivantes clôture au-dessus de ce plus bas → achat à cette clôture, stop sous le
  nouveau plus bas moins 0,1 ATR.
- **S26 retournement en 4 temps** : baisse préalable (moyenne 20 en baisse sur 10 bougies, prix dessous) ;
  clôture au-dessus de la moyenne 20 ; creux plus haut que le plus bas de la baisse (pivot 2 bougies de chaque
  côté) ; dans les 30 bougies après la clôture au-dessus de la moyenne, clôture au-dessus du sommet entre les
  deux creux → achat, stop sous le creux plus haut.
- **S27 double creux** : deux pivots bas (2 bougies de chaque côté) à moins de 0,3 ATR l'un de l'autre, à 5 à
  30 bougies d'écart ; achat à la première clôture au-dessus du plus haut entre eux, dans les 10 bougies après
  le second ; stop sous le plus bas des deux ; objectif = ce plus haut + la hauteur de la figure (ignoré si
  moins de 1 R ; condition retirée avant tout calcul, voir le journal).
- **S28 VWAP** : VWAP de séance (indices 9:30, or 8:20 heure de New York, Bitcoin 0:00 UTC), pas avant 30 min ;
  VWAP plus haut que 4 bougies avant, bougie dont le plus bas touche le VWAP et qui clôture au-dessus → achat
  à la clôture, stop sous la bougie moins 0,1 ATR, objectif 2 R, sortie au plus tard à 16:00 heure de New
  York (Bitcoin 24:00 UTC).
- **S21 milieu de la première bougie** (Nasdaq, S&P 500, or ; ouverture comme B10) : à la clôture de la
  première heure, achat si la clôture est au-dessus du milieu de la première bougie 5 min, vente sinon ; stop
  de l'autre côté du range de la première heure ; pas d'objectif, sortie à 15:00 heure de Chicago.
- **S22 écarts d'ouverture** (Nasdaq, S&P 500) : ouverture de 9:30 à au moins 0,3 % de la clôture de 16:00 de
  la veille ; si le volume de la première bougie 5 min vaut au moins 1,5 fois la moyenne des 20 dernières
  premières bougies, entrée dans le sens de l'écart, sinon contre l'écart ; entrée à la clôture de cette
  bougie, stop à son autre extrême, objectif 2 R, sortie à 15:00 heure de Chicago.

**Pour information, sans verdict** : la règle du risque à 1 % par trade est comparée au 10 % actuel du compte
simulé (pire baisse et capital final sur les trades du bot rejoués, 4 actifs ensemble).

**Verdict par cellule** : mêmes critères qu'à l'essai 14. « Prouvé » avec la marge corrigée pour **254 essais**
(157 + 97). Une cellule validée irait en ombre, jamais directement en signal réel.

## Essai 16 — le swing : tendance journalière et 1 h, repli en 15 min, 2 à 5 jours (3 variantes, 12 cellules)

Écrit le 9 octobre 2026, **avant** tout calcul. Quinze essais montrent que le scalping en 5 min n'a pas
d'avantage solide, alors que les stratégies plus longues (Donchian sur l'or) en ont un peu, les frais pesant
moins. Yanisse a demandé de tester un vrai style swing : positions de 2 à 5 jours, prises dans une tendance
nette, sur un repli. Topstep interdit de garder une position la nuit : ce style viserait un compte CFD
(compte islamique sans swap pour le halal).

**Données** : historique long 5 min des 4 actifs (or, Nasdaq, S&P 500, Bitcoin), rééchantillonné en 15 min,
1 h et jour (UTC). Découverte du 28/09/2025 au 04/10/2026, confirmation du 10/2024 au 27/09/2025, comme les
essais 14 et 15. **Frais du bot** (estimation prudente en % du prix, valable pour tout courtier : or 0,02 %,
indices 0,01 %, Bitcoin 0,06 %) ; l'estimation IC Markets (plus basse) est donnée pour information. Le swap
(frais de nuit) n'est pas compté : il est nul sur un compte islamique, qui peut facturer à la place des frais
de dossier non modélisés ici.

**Entrée (commune aux 3 variantes)**, à la clôture d'une bougie 15 min, une position à la fois par actif :
1. **Tendance journalière** : la clôture de la veille est au-dessus de la moyenne 20 des clôtures
   journalières, et cette moyenne est plus haute qu'il y a 5 jours (vente : l'inverse).
2. **Tendance 1 h** dans le même sens : clôture 1 h au-dessus de la moyenne 20 (1 h), moyenne plus haute
   qu'il y a 3 bougies.
3. **Pas après un mouvement étiré** : clôture 1 h à moins de 2 ATR 14 (1 h) de la moyenne 20 (1 h).
4. **Repli sur la zone neutre en 15 min** : le RSI 21 est monté au-dessus de 55 dans les 12 dernières bougies,
   n'est pas passé sous 40 depuis 6 bougies, était entre 40 et 50 à la bougie précédente et repasse au-dessus
   de 50 (vente : symétrique autour de 50-60).
5. **Heures** : entrée seulement entre 8:00 et 22:00 heure de Paris ; pas d'entrée le vendredi après 12:00
   heure de New York (sauf Bitcoin).
6. **Stop sous le 2e creux** : sous le plus bas des 2 derniers creux 15 min (pivot, 2 bougies de chaque côté)
   des 40 dernières bougies, moins 0,1 ATR 14 (15 min) ; s'il n'y a pas 2 creux, sous le plus bas des 10
   dernières bougies. Trade ignoré si ce risque sort de 0,3 à 3 ATR 14 (1 h).

**Sortie** (stop toujours prioritaire ; durée maximale 5 jours ; or et indices fermés le vendredi à 16:00
heure de New York, pas de week-end) :
- **W1 une sortie** : objectif 3 R, stop fixe.
- **W2 deux unités** : moitié à +1 R, stop de l'autre moitié au prix d'entrée, puis remonté sous chaque
  nouveau creux 1 h (pivot, 2 bougies de chaque côté) apparu depuis l'entrée, moins 0,1 ATR 14 (1 h).
- **W3 suiveur seul** : pas d'objectif, stop remonté sous chaque nouveau creux 1 h comme W2, sans sortie
  partielle.

**Verdict par cellule** (variante × actif) : critères de l'essai 3 (découverte ≥ 30 trades, gain net > 0,
facteur de profit ≥ 1,1, deux moitiés positives ; confirmation ≥ 30 trades, gain > 0, facteur ≥ 1,1).
« Prouvé » avec la marge corrigée pour **266 essais** (254 + 12). Une cellule validée irait en ombre.

## Essai 17 — toutes nos stratégies sur le DAX et l'Euro Stoxx 50 (54 idées, 108 cellules)

Écrit le 10 octobre 2026, **avant** d'avoir regardé les données (téléchargement lancé en parallèle). Ce sont les deux indices européens que notre
liste de règles cite parmi les meilleurs marchés à trader, et nous ne les avons jamais testés. Topstep ne les
propose pas : ils se traderaient chez un courtier CFD. Yanisse a demandé de leur appliquer toutes nos
stratégies existantes, sans en inventer de nouvelles.

**Données** : bougies 1 min Dukascopy (CFD au comptant, DEUIDXEUR et EUSIDXEUR), regroupées en 5 min, 25 mois.
Découverte du 28/09/2025 à octobre 2026, confirmation de octobre 2024 au 27/09/2025, comme les essais 14 à 16.
**Frais du bot** en % du prix (pas de Topstep) : DAX 0,01 % (spread CFD d'environ 1 à 1,5 point plus un peu de
glissement), Euro Stoxx 50 0,03 % (spread d'environ 1,5 point sur un indice 4 à 5 fois plus bas).

**Horloge européenne** : nos stratégies de séance sont écrites à l'heure de New York (ouverture 9:30, fin
16:00, sortie forcée 15:00 heure de Chicago). Pour les indices européens, chaque bougie est replacée à l'heure
de Paris moins 30 minutes, lue comme une heure de New York : l'ouverture de 9:30 du code devient 9:00 à Paris
(ouverture de Francfort), la sortie forcée de 16:00 devient 15:30 à Paris, la pause sans entrée de 15:00-17:00
heure de Chicago devient 15:30-17:30 à Paris. Les R ne changent pas, seuls les horaires sont transposés.
Restent à l'heure réelle : `london_breakout` (déjà écrite en heure UTC autour de l'ouverture de Londres),
`donchian_1h` et `rsi2_1h` (sans horaires de séance), et le swing de l'essai 16 (entrées 8:00-22:00 à Paris,
sortie le vendredi à 16:00 heure de New York, soit 22:00 à Paris).

**Stratégies testées (mêmes règles et mêmes réglages que dans leur essai d'origine), sur chacun des 2 indices** :
- le **bot actuel** rejoué (réglages de l'indice S&P 500, horizon 1 h) ;
- laboratoire de l'essai 3 et 5 : `orb5`, `orb30`, `intraday_mom`, `noise_area`, `noise_area_v2`, `gap_fade`,
  `london_breakout`, `donchian_1h`, `rsi2_1h` (`news_breakout` et `pre_fomc` sont propres aux annonces
  américaines, `comex_orb` à l'or : non testés) ;
- `donchian_day`, `donchian_15m_day`, `donchian_30m_day` (essais 8 et 9) ;
- essai 14 : filtres A1 à A5 sur le bot (A5 : l'autre indice européen), sorties C11 à C13, setups B6 à B10 ;
- essai 15 : filtres F1 à F8, gestion G30 à G40, setups S15 à S28, S21 et S22 ;
- essai 16 : swing W1 à W3.

**Verdict par cellule** : critères de l'essai 3 (découverte puis confirmation), frais ci-dessus. « Prouvé »
avec la marge corrigée pour **374 essais** (266 + 108). DAX et Euro Stoxx 50 bougent presque ensemble : une
stratégie validée sur les deux compte comme un seul indice, pas comme deux confirmations. Une cellule validée
irait en ombre, jamais directement en signal réel.

## Essai 18 — scalping de quelques minutes sur l'or, règles reformulées (10 idées, 10 cellules)

Écrit le 12 octobre 2026, **avant** d'avoir regardé les données (téléchargement lancé en parallèle). Yanisse veut
essayer le vrai scalping (trades de quelques minutes, un seul à la fois) sur un compte démo MetaTrader 5, puis
peut-être en réel. Avant tout démo, on teste les règles de scalping de notre liste de règles, reformulées ici,
sur l'or (notre meilleur marché), avec les frais d'un courtier ECN.

**Données** : bougies 1 min Dukascopy (or au comptant XAUUSD, prix acheteur BID, volume en ticks), 10/2024 →
10/2026. Les bougies 5 min, 15 min et 1 h sont reconstruites à partir des bougies 1 min, et une décision ne lit
que des bougies closes. Découverte du 28/09/2025 à octobre 2026, confirmation de octobre 2024 au 27/09/2025,
comme les essais 14 à 17. Les ticks (seconde par seconde) sont trop lents à télécharger sur 2 ans : la vérification
sur ticks ne se fera que pour une cellule validée (dernier mois), avant tout démo.

**Frais** : 0,30 $ par once et par aller-retour (compte ECN type Vantage RAW : écart achat-vente d'environ 0,12 à
0,25 $ aux heures actives, commission 6 $ par lot de 100 onces, plus un peu de glissement), retirés de chaque trade
et exprimés en R (frais ÷ distance du stop).

**Indicateurs** : moyennes mobiles simples 20 et 50 (MM20, MM50), RSI 21, stochastique 21-3-3, ATR 14.

**Contexte obligatoire (achat ; vente symétrique)** :
- 15 min et 5 min : clôture au-dessus de la MM20, MM20 plus haute que 3 bougies plus tôt, RSI 21 au-dessus de 50 ;
- 1 h : clôture au-dessus de la MM20 (on ne trade pas contre l'heure) ;
- pas étiré : clôture 5 min moins MM20 5 min inférieure à 2 ATR 5 min ;
- de la place : le plus haut des 24 dernières bougies 1 h est soit sous le prix (cassure), soit à au moins
  1,5 fois la distance du stop au-dessus de l'entrée (on n'achète pas juste sous une résistance) ;
- horaires : entrées de 7:00 à 20:00 UTC du lundi au vendredi (19:00 le vendredi), aucune entrée de 8:25 à 8:45
  ni de 9:55 à 10:05 heure de New York (annonces américaines), toute position fermée à 20:30 UTC.

**Entrées (signal sur une bougie 1 min close, entrée à l'ouverture de la suivante)** :
- **R1 repli sur la moyenne** : dans les 5 dernières bougies 1 min, un plus bas a touché la MM20 1 min, la clôture
  est restée au-dessus de la MM50 1 min, puis la stochastique 1 min repart vers le haut (%K croise %D, %K sous 50 au
  croisement) et la bougie du signal clôture au-dessus de la MM20 ;
- **R2 cassure d'une pause** : les 4 dernières bougies 5 min tiennent dans une hauteur d'au plus 1 ATR 5 min, une
  bougie 1 min clôture au-dessus de leur plus haut avec un volume supérieur à 1,5 fois la moyenne des 20 dernières ;
- **R3 retour au RSI 50** : le RSI 21 en 5 min est passé entre 45 et 52 sur l'une des 3 dernières bougies 5 min,
  puis une bougie 1 min clôture au-dessus du plus haut de la précédente ;
- **R4 chiffre rond** : niveaux tous les 10 $ ; une bougie 1 min a clôturé au-dessus d'un niveau dans les 30 dernières
  minutes, le prix est revenu à moins de 0,3 ATR 5 min du niveau sans clôturer en dessous, puis une bougie 1 min
  haussière clôture au-dessus du plus haut de la précédente ;
- **R1-R4 ensemble** : le premier signal venu des quatre.

**Stop** : sous le plus bas des 10 dernières bougies 1 min, moins 0,25 $ de marge. Distance au moins 0,5 ATR 5 min
(jamais un stop minuscule) ; au-delà de 1,5 ATR 5 min, pas de trade.

**Sorties (2 variantes par entrée)** :
- **X1 1 pour 1** : objectif à 1 fois la distance du stop, durée maximale 60 min ;
- **X2 moitié puis suiveur** : moitié fermée à 1 fois la distance du stop, stop de l'autre moitié remonté à l'entrée,
  puis suivi sous le plus bas des 5 dernières bougies 1 min closes, durée maximale 60 min.
Stop et objectif touchés dans la même bougie 1 min : compté en stop (prudent). Un seul trade à la fois par cellule.

**Verdict par cellule** : critères de l'essai 3 (découverte puis confirmation), frais ci-dessus, 5 entrées × 2
sorties = 10 cellules. « Prouvé » avec la marge corrigée pour **384 essais** (374 + 10). On rapporte aussi le
résultat avant frais et le nombre de trades par jour. Une cellule validée ne va ni en signal réel ni en ombre
directement : vérification sur ticks du dernier mois, puis démo MetaTrader 5 de quelques semaines. Aucun ordre
réel.

## Essai 19 — scalping de quelques secondes sur l'or (6 cellules)

Écrit le 13 octobre 2026, **avant** d'avoir regardé les ticks (téléchargement lancé en parallèle). Après l'essai 18
(trades de plusieurs minutes, tous écartés), Yanisse veut tester le scalping qu'il pratique à la main : beaucoup de
trades de quelques secondes, sortie dès qu'on est gagnant, au bon moment.

**Données** : ticks Dukascopy de l'or au comptant (prix acheteur et vendeur réels), de 7:00 à 21:00 UTC, du
01/09/2026 au 12/10/2026. Découverte du 21/09 au 12/10, confirmation du 01/09 au 20/09 (la plus ancienne, comme
les essais précédents). Les ticks du courtier Vantage enregistrés par le pont MetaTrader 5 serviront ensuite à
vérifier l'écart réel, sans changer les règles.

**Exécution** : prix milieu des ticks Dukascopy, plus les frais de Vantage RAW : écart de 0,15 $ (mesuré sur le
compte démo le 12/10) payé à moitié à l'entrée et à moitié à la sortie, plus 0,06 $ de commission, soit **0,21 $
par once et par aller-retour**. Correction écrite avant tout résultat : la première version faisait payer l'écart
Dukascopy, mais en ouvrant un fichier on voit qu'il est d'environ 0,55 $, presque 4 fois celui de Vantage ; il
aurait condamné l'essai pour une raison qui n'est pas celle de Yanisse. Le résultat avec l'écart Dukascopy réel
sera donné pour information.

**Contexte (achat ; vente symétrique)** : bougies 5 min et 15 min reconstruites à partir des ticks (prix milieu),
clôture au-dessus de la MM20, MM20 plus haute que 3 bougies plus tôt, RSI 21 au-dessus de 50 (mêmes règles que le
contexte de l'essai 18, sans l'heure). Entrées de 7:00 à 20:00 UTC, aucune de 8:25 à 8:45 ni de 9:55 à 10:05 heure
de New York.

**Entrée, départ brusque** : le prix milieu dépasse le plus haut des 60 dernières secondes **et** a monté d'au moins
0,30 $ en 10 secondes. Entrée au tick suivant.

**Sortie** : objectif quand le prix de sortie (bid pour un achat) dépasse l'entrée de **X** ; stop quand il recule de
**S** ; sinon sortie au marché au bout de **60 secondes**. X ∈ {0,10 ; 0,30 ; 0,60} $, S ∈ {0,50 ; 1,00} $ : 6
cellules. R = résultat ÷ S. Un seul trade à la fois, 10 secondes de pause après chaque sortie.

**Verdict par cellule** : critères de l'essai 3 (au moins 30 trades, moyenne nette positive, facteur de profit
≥ 1,1, les deux moitiés de la découverte positives, puis confirmation). « Prouvé » avec la marge corrigée pour
**390 essais** (384 + 6). On rapporte le taux de réussite, les trades par jour et la part des frais. Une cellule
validée irait en démo sur MetaTrader 5, jamais en réel sans la demande de Yanisse.

## Essai 20 — rebond après une bougie d'épuisement sur l'or (4 cellules)

Écrit le 13 octobre 2026, **avant** tout résultat. Idée de Yanisse, vue en direct le matin même : une bougie 5 min
de baisse beaucoup plus grande que les autres arrive sur un niveau sans le casser, puis le prix repart.

**Données** : bougies 1 min Dukascopy de l'or (celles de l'essai 18, 10/2024 → 10/2026), bougies 5 min reconstruites.
Découverte du 28/09/2025 à octobre 2026, confirmation de octobre 2024 au 27/09/2025. Frais de Vantage RAW : 0,21 $
par once et par aller-retour (écart 0,15 $ + commission 0,06 $).

**Bougie d'épuisement (achat ; vente symétrique)** : bougie 5 min close, baissière, dont la hauteur fait au moins
2 fois la moyenne des 20 bougies 5 min précédentes, clôturée entre 7:00 et 20:00 UTC (hors 8:25-8:45 et
9:55-10:05 heure de New York).

**Niveau** (cellules « niveau ») : son plus bas passe à moins de 1 $ d'un chiffre rond (multiple de 10 $) ou du plus
bas des 3 heures précédentes, et sa clôture reste au-dessus de ce niveau (il n'est pas cassé). Cellules « sans
niveau » : toute bougie d'épuisement.

**Entrée** : dans les 5 minutes qui suivent, une bougie 1 min clôture au moins 0,20 $ au-dessus de la clôture de la
bougie d'épuisement ; entrée à l'ouverture de la minute suivante. Sinon, pas de trade.

**Stop** sous le plus bas de la bougie d'épuisement, moins 0,25 $. **Objectif** à 1 fois ou 2 fois la distance du
stop ; sortie au marché au bout de 30 minutes. Stop et objectif dans la même minute : compté en stop. Un trade à
la fois.

**Cellules** : {niveau, sans niveau} × {objectif 1R, 2R} = 4. Verdict selon les critères de l'essai 3, « prouvé »
avec la marge corrigée pour **394 essais** (390 + 4). Une cellule validée irait en démo sur MetaTrader 5.

## Essai 21 — le test des 1000 singes : nos stratégies battent-elles des entrées au hasard ? (≈ 230 cellules)

Écrit le 13 octobre 2026, **avant** tout résultat. Idée tirée d'une vidéo envoyée par Yanisse : garder les stops,
les objectifs, la durée et le sens des trades d'une stratégie, mais remplacer ses entrées par des entrées tirées
au hasard, 1 000 fois. Si la stratégie ne se détache pas des singes, ce n'est pas son signal qui gagnait, mais le
marché ou la gestion du trade.

**Stratégies** (à la demande de Yanisse : toutes, pas seulement celles en ombre) : les 54 de l'essai 17 (bot rejoué,
laboratoire des essais 3, 5, 8 et 9, essais 14, 15 et 16) sur l'or, le Nasdaq, le S&P 500 et le Bitcoin (bougies
5 min Dukascopy et Binance, 10/2024 → 10/2026), plus les 10 cellules de l'essai 18 et les 4 de l'essai 20 (or,
bougies 1 min). Le DAX et l'Euro Stoxx 50 (essai 17, rien de validé, marchés non tradés) et l'essai 19 (ticks) ne
sont pas repris. Frais : Topstep pour l'or, le Nasdaq et le S&P 500, ceux du bot pour le Bitcoin, 0,30 $ et 0,21 $
par once pour les essais 18 et 20 (les mêmes que dans chaque essai d'origine).

**Un singe** : pour chaque trade réel de la cellule, une entrée à l'ouverture d'une bougie tirée au hasard (bougies
5 min, ou 1 min pour les essais 18 et 20) **à la même heure de la journée** (heure de New York) n'importe où dans
les 24 mois, **même sens**, **même distance de stop**, objectif à la même distance que le gain réel quand le trade
réel est sorti à l'objectif (sinon pas d'objectif), et sortie à la clôture au bout du **même nombre de bougies** que
le trade réel si ni le stop ni l'objectif n'ont été touchés. Stop et objectif dans la même bougie : compté en stop.
On calcule le R net moyen de ces faux trades. 1 000 singes par cellule (graine fixée, résultats reproductibles).

**Singe filtre** (en plus, pour les cellules qui ne font que retirer des trades du bot : filtres A1-A5, F1-F8 et
limites G40) : 1 000 tirages au hasard du même nombre de trades parmi ceux du bot. Le filtre doit faire mieux qu'un
filtre au hasard.

**Verdict par cellule**, sur les 24 mois : la cellule **bat les singes** si son R net moyen dépasse au moins 950 des
1 000 singes (moins de 5 % de chances par hasard). « **Nettement** » si l'écart, compté en écarts types des singes,
reste au-dessus du seuil corrigé pour le nombre de cellules testées (même correction que nos « prouvé »). Pour
information : la moyenne des singes (ce que la gestion et le marché donnent sans signal), et la position de la
cellule sur la découverte et la confirmation séparément. Moins de 30 trades : pas de verdict.

**Ce qu'on en fera, décidé d'avance** : une stratégie suivie aujourd'hui (Donchian or en signaux réels, Donchian
Bitcoin et or en ombre, A1 sans étirement sur l'or, G40 sur l'or, S25 sur le Nasdaq, R1 sur le démo MetaTrader 5)
qui **ne bat pas** les singes est signalée à Yanisse avec la proposition de l'arrêter ; rien n'est arrêté sans son
accord. Une cellule écartée par nos essais qui bat les singes n'est **pas** repêchée : le test des singes est un
filtre en plus, jamais une porte d'entrée. L'horizon 3 h de l'or (`horizon_3h_gold`) n'est pas dans la liste (il
demanderait de rejouer le bot) et reste jugé par l'essai 7.

## Essai 22 — les autres contrôles de la vidéo : plateau, centaines de trades, régimes, walk-forward, frais doublés

Écrit le 13 octobre 2026, **avant** tout résultat, à la demande de Yanisse (même vidéo que l'essai 21). Le test
des singes (essai 21), la partie cachée jamais regardée (découverte et confirmation), la correction du nombre
d'essais et l'entrée à l'ouverture de la bougie suivante sont déjà en place ; on ajoute le reste.

**Stratégies contrôlées** : celles qu'on suit encore. Donchian fermé chaque soir sur l'or (`donchian_day`, en ombre
depuis l'essai 21), Donchian 1 h sur l'or et le Bitcoin, A1 sans étirement et G40 limites du jour sur l'or (filtres
du bot), S25 creux repris sur le Nasdaq. Mêmes données (24 mois, 10/2024 → 10/2026) et mêmes frais que l'essai 21.

**Grilles de réglages** (le réglage actuel est au milieu ou presque) :
- Donchian : canal d'entrée 10, 15, **20**, 25, 30 heures × canal de sortie 5, **10**, 15 heures (15 réglages) ;
- A1 : écart à la moyenne 1, 1,25, **1,5**, 1,75, 2 ATR (5) ;
- G40 : 2, **3**, 4, 5 trades par jour × arrêt après 1, **2**, 3 pertes (12) ;
- S25 : creux des 6, 8, **10**, 12, 15 bougies × reprise en 1, **2**, 3 bougies (15).

**Cinq contrôles**, tous sur les 24 mois, R net moyen par trade :
1. **Plateau** : au moins 2 réglages sur 3 de la grille gagnent (R net > 0, au moins 30 trades), **et** tous les
   voisins directs du réglage actuel gagnent.
2. **Centaines de trades** : au moins 200 trades.
3. **Régimes** : chaque trade est classé selon le marché des 20 jours précédents (rendement sur 20 jours divisé par
   son agitation normale : au-dessus de +0,5 « hausse », sous −0,5 « baisse », entre les deux « plat ») ; il faut un
   R net > 0 dans au moins 2 des régimes qui comptent au moins 30 trades.
4. **Walk-forward** : tous les 3 mois, on choisit le meilleur réglage de la grille sur les 6 mois précédents, puis
   on le joue sur les 3 mois suivants, jamais vus ; il faut que la suite de ces trimestres gagne (R net > 0).
5. **Frais doublés** : le réglage actuel garde un R net > 0 avec des frais multipliés par 2.

Une stratégie est **robuste** si elle passe les 5. **Décidé d'avance** : une stratégie qui échoue est signalée à
Yanisse avec la proposition de l'arrêter ; rien n'est changé sans son accord, et aucun réglage n'est changé pour le
« meilleur » de la grille (ce serait refaire le courtier de Baltimore).

## Règles d'arrêt du démo MetaTrader 5 (écrites à froid le 13 octobre 2026)

Comptées à partir du 14/10/2026 00:00 UTC, sur les trades fermés, frais compris. Quand une règle est franchie, le
programme refuse toute nouvelle entrée et le note au journal ; seul Yanisse peut relancer, après en avoir parlé.

- **Pont R1** (magic 180018, 0,01 lot, compte vu comme 100 $) : perte cumulée de 25 $ ; ou 8 pertes d'affilée ;
  ou, après 40 trades, une moyenne pire que −0,30 R (1 R ≈ 3,71 $ à 0,01 lot, stop moyen de l'essai 18). Le
  backtest promet −0,04 R ; on s'attend à moins bien (la vidéo dit de diviser par deux ce que promet le test), d'où
  la marge.
- **Poste de l'assistant** (magic 777001, 1 % du solde par trade) : perte cumulée de 100 $ (10 % des 1 000 $) ; ou
  6 pertes d'affilée. Pas de backtest à comparer : ses entrées sont jugées à la main.
- La limite de 10 $ par jour du pont reste en place.

## Essai 23 — toutes nos stratégies rejouées sur 2014-2024, années jamais regardées

Écrit le 13 octobre 2026, **avant** tout téléchargement et tout résultat, à la demande de Yanisse (« rejoue tout »).
Nos essais 14 à 22 ne regardent que 10/2024 → 10/2026, une seule époque (l'or monte fort). On rejoue les mêmes
règles, **sans rien changer**, sur les dix années d'avant.

**Données** : bougies 1 min Dukascopy (CFD) regroupées en 5 min pour l'or, le Nasdaq et le S&P 500, du 01/01/2014
au début de nos données actuelles (fin septembre 2024) ; Bitcoin : Binance 5 min d'août 2017 à septembre 2024.
Échelle des prix fixée sur une journée récente (les prix de 2014 sont très différents de ceux d'aujourd'hui).

**Changement de source, écrit avant tout résultat (13/10/2026 au soir)** : Dukascopy nous a freinés (1 an d'or en 2 h,
puis erreurs 429/503). On prend à la place les bougies 1 min HistData (or XAUUSD, S&P 500 SPXUSD, Nasdaq NSXUSD),
heure de New York avec heure d'été. Contrôle fait sur l'automne 2024, où les deux sources se recouvrent : mêmes prix
que nos bougies Dukascopy à la bougie près (décalage UTC−4 l'été, UTC−5 l'hiver). Rien d'autre ne change.

**Stratégies** : les 54 de l'essai 17 (bot rejoué, laboratoire, essais 14, 15 et 16) sur les 4 actifs, mêmes réglages,
mêmes frais que l'essai 21 (Topstep pour l'or, le Nasdaq et le S&P 500 ; ceux du bot pour le Bitcoin).

**Verdict par cellule** sur 2014-2024 : elle **tient** si elle a au moins 100 trades, un R net moyen > 0, un facteur
de profit ≥ 1,1, et un R net > 0 dans au moins la moitié des années complètes. Pour information : le résultat de
chaque année, et le test des singes de l'essai 21 sur cette période.

**Décidé d'avance** :
- G40 sur l'or et S25 sur le Nasdaq, passés en réel le 13/10 : s'ils ne tiennent pas, proposition à Yanisse de
  revenir en ombre. S'ils tiennent, ils restent.
- Donchian or (en ombre depuis le 13/10) : s'il tient, on peut en reparler, mais il ne bat toujours pas les singes
  de 2024-2026 ; rien ne change sans l'accord de Yanisse.
- Une stratégie écartée sur 2024-2026 qui tient sur 2014-2024 n'est **pas** repêchée : elle a échoué sur les
  années récentes, qui comptent le plus.

## Essai 24 — tout de A à Z sur 2014-2026, d'un seul bloc

Écrit le 14 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« faire les tests sur 2014-2026 en faisant
tous les tests, de A à Z, pour ne pas être biaisé »). Les essais 14 à 23 ont regardé les années par morceaux ; ici
chaque stratégie passe **tous** les contrôles d'un coup, sur les 12 ans réunis.

**Données** : bougies 5 min de l'essai 23 (2014 → 09/2024) suivies de nos données actuelles (09/2024 → 10/2026), sans
trou ni recouvrement ; Bitcoin dès 08/2017. Bot rejoué : trades de l'essai 23 suivis de ceux de l'essai 14 (mêmes règles).

**Stratégies** : les 54 de l'essai 17 sur les 4 actifs (216 cellules), réglages actuels, frais de l'essai 21.

**Contrôles** (une cellule est **robuste** si elle passe tous ceux qui s'appliquent à elle) :
1. au moins 200 trades ;
2. R net moyen > 0 et facteur de profit ≥ 1,1 sur 2014-2026 ;
3. R net > 0 dans au moins 60 % des années complètes ;
4. les deux moitiés positives : avant 2020 et depuis 2020 ;
5. les deux dernières années (10/2024 → 10/2026) positives : les années récentes comptent ;
6. toujours positive avec les frais doublés ;
7. positive dans au moins 2 des 3 régimes de marché (hausse, baisse, plat, comme à l'essai 22, 30 trades minimum) ;
8. bat les 1000 singes (≥ 950), et pour un filtre, bat aussi les filtres au hasard (≥ 950) ;
9. pour les stratégies qui ont des réglages (Donchian jour et 1 h, A1, G40, S25, sur chaque actif) : plateau des
   réglages et walk-forward > 0, comme à l'essai 22. Les autres n'ont pas de réglage à faire varier : contrôle sans objet.

**Prouvée** : robuste et écart aux singes au-delà du seuil corrigé du nombre de cellules (Bonferroni, comme l'essai 21).

**Décidé d'avance** :
- G40 or et S25 Nasdaq (en réel) : s'ils ne sont pas robustes, proposition de les remettre en ombre.
- Une cellule robuste qui n'est pas suivie aujourd'hui (y compris celles écartées avant) : proposition de la mettre
  **en ombre** d'abord, jamais directement en réel. Cette règle remplace, pour cet essai seulement, le « pas de
  repêchage » de l'essai 23, car le contrôle 5 exige déjà que les années récentes soient gagnantes.
- Rien ne change sans l'accord de Yanisse.

## Essai 25 — faire apprendre le bot principal sur 12 ans, jugé sur des années cachées

Écrit le 14 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« entraîner le bot avec les données
historiques, en cachant une partie du graphique »). Jusqu'ici le bot n'apprenait que de ses propres signaux réels
(quelques centaines), trop peu pour séparer les bons critères du hasard.

**Données** : tous les signaux du bot rejoué sur 2014 → 10/2026 (essais 23 et 14 ; or, Nasdaq, S&P 500, Bitcoin),
avec ce que le bot voyait à l'entrée : les critères alignés (tendances 5 min / 15 min / 1 h, ADX, VWAP, RSI, MACD,
niveau, volume, ouverture, veille, marché meneur), le score, le sens, l'heure, le jour, l'ADX, le RSI, l'étirement,
l'agitation (ATR), l'activité, le range de l'heure, le coût en R, la distance à l'ouverture américaine, l'actif.
Cible : le R net du trade (frais de l'essai 21).

**Apprentissage, années cachées (walk-forward)** : pour chaque année Y de 2017 à 2026, le modèle n'apprend que sur
les années avant Y, puis décide sur l'année Y qu'il n'a jamais vue ; il prend un signal seulement si le R prévu est
> 0. Deux modèles, fixés d'avance : (a) **poids des critères** (régression linéaire avec pénalité, lisible comme des
poids) ; (b) **arbres** (gradient boosting, 200 arbres de profondeur 3). Un seul modèle pour les 4 actifs (l'actif est
une des entrées).

**Verdict par actif et par modèle**, sur les signaux gardés de 2017-2026 (tous vus pour la première fois) : les
contrôles de l'essai 24 — au moins 200 trades ; R net > 0 et PF ≥ 1,1 ; R > 0 dans 60 % des années ; deux moitiés
positives (2017-2021 et 2022-2026) ; 2 dernières années positives ; frais doublés positifs ; 2 régimes sur 3 ; bat les
1000 singes **et** les 1000 « filtres au hasard » (même nombre de signaux tirés au hasard parmi ceux du bot, la même
année). Prouvé si l'écart aux filtres au hasard dépasse le seuil corrigé (8 cellules).

**Décidé d'avance** : si un modèle passe tout sur un actif, proposition à Yanisse de le brancher sur le bot pour cet
actif (réentraîné chaque année sur tout l'historique). Sinon, on le dit : apprendre sur ces critères ne crée pas
d'avantage, et la piste suivante serait de changer les critères eux-mêmes. Rien ne change sans son accord.

## Essai 26 — apprendre par groupe de marchés (et le DAX)

Écrit le 14 octobre 2026, **avant** tout calcul, à la demande de Yanisse : un bot qui apprend sur chaque marché (ou
groupe de marchés qui bougent ensemble) séparément marche-t-il mieux qu'un seul bot qui mélange tout ?

**Données** : celles de l'essai 25, plus le **DAX** (bougies 1 min HistData 2014 → 08/2024, mêmes prix que nos
bougies Dukascopy à la bougie près sur l'automne 2024, puis nos données jusqu'à 10/2026), bot rejoué sur l'horloge
européenne de l'essai 17, frais du bot (CFD, 0,01 %).

**Trois façons d'apprendre**, même modèle d'arbres que l'essai 25 (mêmes réglages), mêmes années cachées
(apprend sur les années avant Y, décide sur Y, de 2017 à 2026) :
- **seul** : un modèle par marché, qui n'apprend que sur ses propres signaux (or, Nasdaq, S&P 500, DAX, Bitcoin) ;
- **groupe indices** : un modèle pour Nasdaq + S&P 500 + DAX ensemble (l'or et le Bitcoin restent seuls) ;
- **tout ensemble** : un modèle pour les 5 marchés (comme l'essai 25, DAX en plus).

**Verdict** : 13 cellules (5 + 3 + 5), contrôles de l'essai 25 (dont les filtres au hasard la même année), « prouvé »
avec le seuil corrigé pour 13 cellules. Pour information : corrélation des rendements journaliers entre marchés.

**Décidé d'avance** : sur chaque marché, si une autre façon d'apprendre est prouvée et fait un meilleur R moyen que
celle branchée aujourd'hui (tout ensemble, essai 25), proposition de la brancher. Un marché prouvé qui n'est pas
branché (S&P 500, Bitcoin, DAX) : proposition de le brancher. Rien ne change sans l'accord de Yanisse.

## Essai 27 — l'or la nuit (idées trouvées sur le web)

Écrit le 14 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« cherche sur le web des stratégies sur
l'or »). Déjà testés et écartés ici : cassure du range asiatique (`london_breakout`), Donchian, momentum 12 mois,
tendance journalière, annonces, scalping, idées de la formation. Idées nouvelles retenues (sources : Blose,
Gondhalekar et Kort, *Journal of Economics and Finance* 2018 : l'or monte la nuit et baisse le jour ; mémoire CBS
Donati et Jung : l'or monte pendant les heures asiatiques) :
- **N1 nuit COMEX** : achat à 13:30 heure de New York (fin de séance COMEX), vente le lendemain à 08:20 ;
- **N2 heures asiatiques** : achat à 18:00 New York, vente à 03:00 (ouverture de Londres) ;
- **N3 vente le jour** : vente à 08:20 New York, rachat à 13:30.
Du lundi au vendredi, une position à la fois, bougies 5 min 2014-2026 (HistData puis les nôtres), frais Vantage
RAW 0,30 $ l'once aller-retour (swap ignoré : compte sans swap).

**Contrôles** (rendement net en % par trade) : > 0 ; 60 % des années ; deux moitiés (avant et depuis 2020) ; 2
dernières années ; frais doublés ; **singes** : 1000 séries de trades à des heures tirées au hasard le même jour,
même durée, même sens, à battre au moins 950 fois (pour ne pas confondre l'idée avec la hausse de l'or depuis
2014). « Prouvé » : tout passe et z > seuil corrigé pour 3 cellules (2,39).

**Décidé d'avance** : une cellule prouvée → proposition de la suivre en ombre, puis sur le démo MT5. Rien ne
change sans l'accord de Yanisse.

## Essai 28 — d'autres stratégies courtes sur l'or (recherche large)

Écrit le 14 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« cherche d'autres stratégies sur l'or,
des trades qui ne durent pas des jours »). Recherche web, forums, études ; les sources sans règle précise ni preuve
sont écartées (SMC/ICT, robots vendus). Bougies 5 min de l'or 2014-2026, frais 0,30 $ l'once aller-retour, heures
de New York sauf mention :
- **A vente du matin** (mémoire CBS 2019, l'or baisse pendant Londres) : vente à 03:00, rachat à 10:00, lundi-vendredi ;
- **B achat de l'après-midi** (même source) : achat à 11:00, vente à 16:55 ;
- **C1 faux cassage du plus bas de la veille** (Unger Academy, contrats GC) : séance = 18:00 → 17:00 ; dans la
  séance, avant 16:00, 1re bougie 5 min qui passe sous le plus bas de la séance d'avant et clôture au-dessus →
  achat à l'ouverture suivante, stop 0,9 %, objectif 0,8 % (18 $ et 16 $ rapportés au prix moyen 2016-2024), sortie
  au plus tard à 16:55, une fois par séance ;
- **C2** : la même chose, en vente, au plus haut de la séance d'avant ;
- **D suite de la Fed** (Awartani, Hussain et Virk 2024) : jours de décision FOMC, entrée à 14:05 dans le sens de la
  bougie 14:00-14:05, sortie à 16:00 ;
- **E avant les fixings de Londres** (mémoire CBS, Caminschi et Heaney 2014) : vente 10:00 → 10:30 et 14:30 →
  15:00, **heure de Londres** ;
- **F retournement après l'emploi (NFP)** (études FXStreet) : à 08:45, position contraire au mouvement 08:30-08:45,
  sortie à 11:00.

**Contrôles** de l'essai 27 (rendement net en % par trade, singes le même jour à une heure au hasard, même durée,
même sens) plus **au moins 100 trades** ; « prouvé » : tout passe et z > seuil corrigé pour 7 cellules (2,69).

**Décidé d'avance** : une cellule prouvée → proposition de la passer en signaux réels comme l'essai 27. Rien ne
change sans l'accord de Yanisse.

## Essai 29 — largeur du stop et ratio objectif/stop sur les signaux du bot

Écrit le 14 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« le SL coupe-t-il nos trades trop tôt ?
plus large, ça touche le TP après ? plusieurs réglages et ratios, jusqu'à 5-10 % »). On garde les **entrées** du
bot (heure, sens, prix, 2014-2026, or, Nasdaq, S&P 500, Bitcoin) et on change seulement la sortie :
- **Famille 1** (stop proportionnel à celui du bot) : stop × 0,5 / 1 / 1,5 / 2 / 3, objectif à 0,5 / 1 / 1,5 / 2 /
  3 / 5 fois le stop, sortie au plus tard 1 jour après l'entrée (30 réglages par actif) ;
- **Famille 2** (stop en % du prix) : stop 1 / 2 / 5 / 10 %, objectif à 1 / 2 / 3 fois le stop, sortie au plus
  tard 20 jours après l'entrée (12 réglages par actif ; position gardée la nuit, pas chez Topstep).
Si le stop et l'objectif sont touchés dans la même bougie de 5 min, on compte le stop (prudent). Frais du bot.

**Mesures** : part des trades qui touchent l'objectif, le stop, ou finissent à l'heure ; R net moyen. **Contrôles**
de l'essai 24 (200 trades, R > 0 et PF ≥ 1,1, 60 % des années, deux moitiés avant/depuis 2020, 2 dernières années,
frais doublés) puis, seulement pour les réglages qui les passent tous, **singes** : 200 séries d'entrées au hasard
le même jour, même sens, même sortie, à battre au moins 190 fois. « Prouvé » : tout passe et z > seuil corrigé pour
les 168 réglages (3,43).

**Décidé d'avance** : un réglage prouvé → proposition de l'appliquer aux signaux du bot sur cet actif. Rien ne
change sans l'accord de Yanisse.

## Essai 30 — stratégies Bitcoin courtes (recherche large)

Écrit le 14 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« des trades de 20 jours c'est long, y a
pas des stratégies Bitcoin en scalping ou plus courtes ? regarde internet »). Recherche web (études, Quantpedia,
blogs, forums) ; écartées faute de règle précise ou de preuve : comblement du gap CME, « chute de 10 h », expiration
Deribit, liquidations ; écartée faute de données assez fines : la bougie de :00/:15/:30/:45 (minutes). Bougies 5 min
Binance BTCUSDT août 2017 → octobre 2026, frais du bot 0,06 % aller-retour. σ toujours calculé sur le passé seul.
- **B1 heure du soir** (Padysak et Vojtko, Quantpedia) : achat 21:00 UTC, vente 23:00 UTC, tous les jours ;
- **B2** : la même chose, le vendredi seulement ;
- **B3** : la même chose, seulement les jours « agités » (volatilité horaire des 30 jours d'avant, mesurée à 00:00
  UTC, au-dessus de sa médiane des 365 jours d'avant) ;
- **B4 contre une grosse bougie 1 h** (De Nicola 2021) : bougie 1 h (heures UTC pleines) qui bouge de plus de 3 σ
  (σ des 720 bougies 1 h d'avant) → position contraire à l'ouverture suivante, sortie 1 h après ;
- **B5** : la même chose à 2 σ ;
- **B6** : la même chose avec des bougies 2 h (heures paires UTC), 3 σ (σ des 360 bougies d'avant), sortie 2 h après ;
- **B7 dernière demi-heure, à contre-sens** (Shen, Urquhart et Wang 2022) : position 16:30 → 17:00 New York,
  contraire au mouvement 16:00 → 16:30 ;
- **B8 dernière demi-heure, dans le sens de la journée** (même étude) : position 16:30 → 17:00 New York dans le sens
  du mouvement 17:00 la veille → 10:00 ;
- **B9 plus haut de 10 jours le soir** (Quantpedia 2024) : lundi, mardi et vendredi à 16:00 New York, si le prix
  dépasse ses prix de 16:00 des 10 jours d'avant → achat, vente le lendemain 10:00 New York ;
- **B10 cassure de volatilité (Larry Williams)** : jour UTC, achat dès que le prix dépasse l'ouverture du jour +
  0,5 × l'amplitude (plus haut − plus bas) de la veille, au niveau ou à l'ouverture si elle est déjà au-dessus,
  vente à 00:00 UTC ;
- **B11** : la même chose, seulement si l'ouverture du jour est au-dessus de la moyenne des 5 clôtures journalières
  d'avant ;
- **B12 ouverture de Tokyo le lundi** (Concretum 2026) : achat dimanche 19:00 New York, vente lundi 19:00.

**Contrôles** (rendement net en % par trade) : au moins 200 trades, net > 0, 60 % des années pleines positives,
deux moitiés (avant 2020 / depuis 2020) positives, 2 dernières années (depuis le 14/10/2024) positives, frais
doublés > 0, **singes** (1 000 séries, même sens, même durée, à battre 950 fois) : pour les règles d'horaire (B1-B3,
B7, B8, B12), le même jour à une heure au hasard ; pour les règles à signal (B4-B6, B9-B11), n'importe quel jour à
la même heure. « Prouvé » : tout passe et z > seuil corrigé pour 12 cellules (2,64).

**Décidé d'avance** : une cellule prouvée → proposition de la passer en signaux réels (copie démo comprise). Rien
ne change sans l'accord de Yanisse.

## Essai 31 — pétrole et euro sur 2014-2026

Écrit le 14 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« le pétrole et l'euro, on en a fait des
tests ? il existe des stratégies pour ces actifs ? »). Jusqu'ici, ils n'avaient que 24 mois de test (essais 3, 5,
10). Bougies 1 min HistData (EURUSD 2014 → 09/10/2026 ; WTIUSD 2014-2023 et juin-octobre 2026, complétées par
Dukascopy LIGHTCMDUSD de janvier 2024 à mai 2026, HistData n'ayant pas ces mois), regroupées en 5 min. Frais du
bot : pétrole 0,03 %, euro 0,01 % aller-retour. Ouverture de la séance de jour (pour les règles qui en ont besoin) :
pétrole 09:00, euro 08:20 (New York).

**Partie A** : les 54 stratégies de l'essai 24, bot classique compris (rejoué sur les 12 ans), mêmes contrôles
(200 trades, R > 0 et PF ≥ 1,1, 60 % des années, deux moitiés, 2 dernières années, frais doublés, 2 régimes sur 3,
singes de l'essai 21) ; « prouvée » : tout passe et z > seuil corrigé pour toutes les cellules jugées.

**Partie B** : idées d'une recherche large (études, Quantpedia, blogs, forums), contrôles de l'essai 30 (rendement
net en % par trade, 200 trades, années, moitiés, 2 dernières années, frais doublés, 1 000 singes à battre 950 fois ;
le même jour à une heure au hasard pour les règles d'horaire, n'importe quel jour à la même heure pour P4 et P5) ;
« prouvé » : z > seuil corrigé pour 11 cellules (2,61). Heures de New York sauf mention.
- **P1 suite du rapport EIA** (Wen et al. 2023) : mercredi, position 14:00 → 14:30 dans le sens de 10:30 → 11:00 ;
- **P2 la matinée prédit la clôture** (Wen et al. 2021) : autres jours de semaine, position 14:00 → 14:30 dans le
  sens de 14:30 la veille → 10:00 ;
- **P3 la journée prédit la clôture** (Baltussen et al. 2021) : chaque jour, position 14:00 → 14:30 dans le sens de
  14:30 la veille → 14:00 ;
- **P4 cassure de bande à l'ouverture** (Holmberg et al. 2013) : bande à l'ouverture de 09:00 ± (|moyenne| + 1,28 ×
  écart-type des 60 rendements 09:00 → 14:30 d'avant), achat ou vente au premier franchissement, sortie à 14:30 ;
- **P5 contre le rapport EIA** (Geman et Li) : mercredi, si 10:30 → 10:35 dépasse 2 σ (52 mercredis d'avant),
  position contraire 10:35 → 11:00 ;
- **P6 rapport API la veille** : mardi, sens de 16:30 → 17:00, position de 18:00 à 10:25 le lendemain ;
- **E1a vente avant le fixing BCE** (Krohn, Mueller et Whelan 2024) : vente 02:00 New York → 14:15 Francfort ;
- **E1b achat après le fixing de Londres** (même étude) : achat 16:00 Londres → 17:00 New York ;
- **E2a vente pendant Londres** (Breedon et Ranaldo 2013) : vente 03:00 → 11:00 ;
- **E2b achat l'après-midi new-yorkais** (même étude) : achat 11:00 → 16:00 ;
- **E6 la journée prédit la clôture** (Baltussen et al.) : position 14:30 → 15:00 dans le sens de 15:00 la veille →
  14:30.
Écartées : OPEC (trop peu d'événements, calendrier à reconstruire), fixing de fin de mois et FOMC (moins de 200
trades), rapports avec prévisions consensus, carnet d'ordres, options.

**Décidé d'avance** : une cellule prouvée → proposition de la passer en signaux réels (copie démo comprise) ; le
pétrole et l'euro restent « à l'essai » sinon. Rien ne change sans l'accord de Yanisse.

## Essai 32 — réajuster le stop pendant le trade

Écrit le 14 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« est-ce qu'on pourrait pas réajuster nos
SL ? »). Aujourd'hui le stop de départ ne bouge jamais (sauf les sorties propres à chaque stratégie). Stratégies
jugées, telles qu'elles tournent en réel, sur 2014-2026 (bougies longues de l'essai 23 + historique récent) :
zone de bruit et zone de bruit v2 (Nasdaq), Donchian 1 h, W3 et cassure Williams (Bitcoin), nuit asiatique (or),
bot classique or (sans le filtre du modèle) et bot classique Nasdaq (stop × 1,5, objectif 3, 24 h, essai 29).

Même entrée, même sortie d'origine ; seul le stop est déplacé, à la clôture de chaque bougie 5 min, et seulement
pour le resserrer (il n'agit qu'à partir de la bougie suivante) :
- **A** stop au prix d'entrée dès +1 R atteint ;
- **B** stop au prix d'entrée dès +0,5 R atteint ;
- **C** stop suiveur à 1 R derrière le meilleur prix atteint ;
- **D** stop verrouillé à +1 R dès +2 R atteint.
R = distance du stop de départ ; frais du bot inchangés.

Contrôles, sur l'écart trade par trade (variante − version actuelle, en R net) : écart moyen > 0 ; écart > 0 avant
2020 et depuis 2020 ; > 0 sur les 2 dernières années (depuis le 14/10/2024) ; > 0 sur 60 % des années ; et la
variante elle-même garde R > 0. « Prouvée » : tout passe et z de l'écart (test apparié) > seuil corrigé pour
32 cellules (2,95). Les singes ne servent pas ici : on compare deux gestions des mêmes trades.

**Décidé d'avance** : une variante prouvée → proposition de l'appliquer à cette stratégie (signaux Telegram, journal,
simulation et copie démo). Rien ne change sans l'accord de Yanisse.

## Essais 33 à 37 — idées des vidéos @kara_tools

Écrit le 15 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« fais tous les tests sur ce qu'on a
relevé de bon dans toutes les vidéos »). Analyse des 8 vidéos : `/mnt/project-files/videos/analyse-kara-tools.md`
(hors dépôt). Données : or 1 min HistData 2014 → 10/2026 (regroupées en 5 min et 1 h, heures UTC), Bitcoin 5 min
Binance 2017 → 10/2026 avec le volume. Frais : or 0,30 $ l'once aller-retour (Vantage RAW), Bitcoin 0,06 %.
R = distance du stop. Si le stop et l'objectif sont touchés dans la même bougie, on compte le stop.

**Contrôles communs** (cellules qui tradent) : au moins 200 trades ; R net > 0 et facteur de profit ≥ 1,1 ; 60 % des
années pleines positives ; avant 2020 et depuis 2020 positifs ; 2 dernières années (depuis le 14/10/2024) positives ;
frais doublés > 0 ; **1 000 singes** (n'importe quel jour, même heure UTC, même sens, même stop et objectif en % du
prix, même durée maximale) à battre 950 fois. « Prouvée » : tout passe et z > seuil corrigé (Bonferroni à 5 %
unilatéral) pour le nombre de cellules de l'essai.

### Essai 35 — structure de marché sur l'or (vidéo « lire le prix »)

Lecture de la structure sur bougies fermées. Tendance haussière : le sommet de structure H est le plus haut de la
jambe en cours ; un creux n'est **confirmé** que quand une bougie casse H ; il vaut le plus bas entre H et la
cassure. Tendance baissière : l'inverse. La tendance change quand le creux (ou sommet) confirmé est cassé en clôture.
Repli = (H − creux) / (H − creux confirmé précédent). Vitesse = bougies pour remonter du creux à la cassure,
comparées aux bougies de la descente de H au creux. Entrée à l'ouverture de la bougie qui suit la cassure, dans le
sens de la tendance ; stop sous le nouveau creux confirmé (au-dessus du sommet en baisse) ; objectif = taille de la
jambe précédente reportée depuis le creux (vidéo « 3 portes » : la nouvelle jambe vaut la précédente) ; sortie au
plus tard après 48 bougies ; une seule position à la fois. Stop de moins de 0,05 % du prix : signal ignoré.
- **S1** creux fort (repli ≥ 50 %), cassure en **clôture**, cassure rapide (montée en moins de bougies que la descente) ;
- **S2** creux fort, cassure en clôture, sans condition de vitesse ;
- **S3** creux faible (repli < 25 %), cassure en clôture (témoin : la vidéo le dit moins bon) ;
- **S4** creux fort, cassure rapide, mais entrée dès qu'une **mèche** dépasse H (au prix H).
Chacune en bougies 1 h et 5 min : **8 cellules**, seuil z > 2,50.

### Essai 34 — stop selon l'heure (vidéo « les ondes »)

Sur les entrées de S2 (1 h et 5 min), on remplace le stop de structure par un stop **proportionnel à l'agitation
habituelle de l'heure d'entrée** : k × amplitude médiane de la bougie 1 h de cette heure UTC sur les 250 jours
d'avant (k = 1, 2, 3), objectif à 2 fois le stop, même durée maximale. Témoin apparié : même entrée, stop constant
en % du prix égal à k × amplitude médiane **toutes heures confondues** des 250 jours d'avant, objectif 2 fois le stop.
Contrôle de l'essai 32 sur l'écart trade par trade (variante − témoin, en R net) : écart moyen > 0, > 0 avant et
depuis 2020, > 0 sur les 2 dernières années, > 0 sur 60 % des années, variante R > 0 ; « prouvée » : z apparié >
seuil pour **6 cellules** (2,64).

### Essai 33 — les annonces (vidéo « ton stop à 100 sort à 97 »)

Annonces : emploi, inflation, décisions de la Fed 2014-2024 (`data/macro_events_2010_2024.json`).
- **33a mesure** (sans verdict) : amplitude moyenne de la bougie 1 min de l'or à l'heure de l'annonce, contre la même
  minute les autres jours ; et, pour les stops de l'essai 35 touchés dans la minute d'une annonce, l'écart entre le
  stop et le plus bas (haut) de cette minute = glissement dans le pire cas.
- **33b filtre** : sur les 8 cellules de l'essai 35, aucune entrée de 30 min avant à 15 min après une annonce, et
  sortie à l'ouverture de la bougie 30 min avant une annonce si la position est ouverte. Contrôle apparié de l'essai
  34 (variante − version d'origine), **8 cellules** (2,50) ; les stops touchés dans la minute d'une annonce sont
  comptés au pire prix de cette minute dans les deux versions.
- **33c démo** : si le PC est joignable, comparer prix du stop et prix obtenu dans les journaux du démo MT5 (près
  d'une annonce ou non). Mesure seulement.

### Essai 36 — profil de volume du Bitcoin (vidéo « le volume »)

Profil de la veille (jour UTC) : 40 tranches de prix égales entre le plus bas et le plus haut de la veille, volume
de chaque bougie 5 min réparti sur sa tranche de clôture ; zone pleine = tranche ≥ 1,5 × la moyenne ; zone creuse =
tranche ≤ 0,5 × la moyenne ; point de contrôle = tranche la plus pleine.
- **36a mesure** : le jour même, temps moyen passé par tranche traversée en zone creuse contre zone pleine, comparé au
  même calcul avec le profil d'un autre jour tiré au hasard (200 tirages) ; « le prix traverse vite les zones creuses »
  est confirmé si le rapport réel est plus petit que 190 tirages sur 200.
- **36b** : une bougie 5 min clôture dans une zone creuse en venant d'une tranche pleine ou normale voisine → position
  dans le sens de la traversée, objectif = bord opposé de la zone creuse, stop = bord d'entrée moins la même distance
  (1 pour 1), au plus 4 h, une position à la fois.
- **36c** : la même chose, seulement entre le plus bas et le plus haut de la zone de valeur (70 % du volume autour du
  point de contrôle).
36b et 36c : contrôles communs, **2 cellules** (1,96).

### Essai 37 — les anciens extrêmes sur l'or (vidéo « 3 portes » : « l'or s'installe au-delà 64 fois sur 100 »)

- **37a mesure** : quand une bougie 5 min dépasse le plus haut (bas) de la séance d'avant (18:00 → 17:00 New York),
  part des cas où le prix est encore au-delà 15 min et 1 h plus tard ; témoin : le même calcul avec un niveau
  décalé de 0,25 % vers l'intérieur.
- **37b** : à la 1re clôture 5 min au-delà de l'extrême de la veille, position dans le sens de la cassure, sortie
  15 min après ; **37c** : sortie 1 h après. Stop de sécurité 0,5 %. Contrôles communs, **2 cellules** (1,96).

**Décidé d'avance** : une cellule prouvée → proposition de la passer en ombre puis sur le démo MT5 (ou d'appliquer
le filtre ou le stop à la stratégie concernée). Rien ne change sans l'accord de Yanisse.

## Essai 38 — memecoins pump.fun : entrer après la montée, sortir à la chute

Écrit le 18 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« un bot qui trade les memecoins : grosse
montée au début, puis la chute ; entrer tôt et ressortir avec la chute »). Étude seulement : aucun bot, aucun ordre.
Données : corpus public « PumpFun Launch-to-Graduation Corpus » (Hugging Face, Slinky21, licence CC BY 4.0),
**tous** les coins lancés sur pump.fun (Solana) du 5 juin au 14 juillet 2026, morts et arnaques compris, chaque
échange sur la courbe de lancement (« bonding curve »). Hors dépôt (≈ 6 Go), non vérifié par nous sur la chaîne.
Exclus : coins sans prix (toutes leurs lignes `price_sol` vides), coins lancés pendant la panne du 3 juillet
(2 juillet 23:00 → 4 juillet 00:00 UTC) ou moins de 70 min avant la fin du corpus.

**Exécution** : mise 0,5 SOL par trade. Le prix est celui de la courbe ; on achète et vend au **premier échange au
moins 2 s après** le déclencheur (délai d'un bot correct, les « snipers » sont plus rapides). Glissement de notre
propre ordre calculé sur la courbe (produit constant : achat × (1 + 0,5 / SOL virtuel), vente ÷ (1 + jetons vendus /
jetons virtuels)). Frais : 1,25 % par côté (plateforme 0,95 % + créateur 0,30 %) et 0,001 SOL de réseau par
transaction. La courbe rachète toujours : un coin mort se vend au dernier prix. Si le coin quitte la courbe
(« graduation ») pendant le trade, sortie au dernier prix de la courbe. Une seule entrée par coin et par cellule.
Résultat en % de la mise, net.

**Entrées** : **K1** dès le lancement (premier échange ≥ 2 s après le premier échange, le « sniping » d'un bot
lent) ; **K2 / K3 / K5** quand le prix atteint 2 / 3 / 5 fois le prix du premier échange dans les 10 premières
minutes (la « grosse montée du début »). **Sorties** : **T20** suiveur, vente dès que le prix tombe 20 % sous le plus
haut depuis l'entrée ; **T40** suiveur à 40 % ; **M5** vente 5 minutes après l'entrée. Toutes : vente au plus tard
60 min après l'entrée. **12 cellules** (seuil z 2,64).

**Contrôles** : au moins 200 trades ; moyenne nette > 0 et facteur de profit ≥ 1,1 ; positive sur chaque moitié
(lancements avant / depuis le 25 juin) et sur les 7 derniers jours ; frais doublés > 0 ; **1 000 singes** : pour
chaque trade, un coin pris au hasard parmi ceux lancés le même jour qui ont encore un échange au même âge (± 60 s),
même sortie ; à battre 950 fois. « Prouvée » : tout passe et z > 2,64. Pour information : la moyenne sans les 5 %
meilleurs trades, et la part de trades perdants.

**Décidé d'avance** : une cellule prouvée → proposition d'un suivi en direct sans argent (papier) pendant au moins
2 semaines, puis d'en discuter ; rien de plus sans l'accord de Yanisse. Réserve halal écrite d'avance : les
memecoins sont jugés par beaucoup de savants comme de la pure spéculation, à trancher par Yanisse.

## Essai 39 — memecoins pump.fun : ne garder que les « bons » coins

Écrit le 18 octobre 2026, **avant** tout calcul, à la demande de Yanisse (« ça dépend du coin, il faut choisir des
bons coins avec un minimum de market cap ; cherche ce qui différencie un bon coin d'un rug »). Mêmes données,
exécution, frais, contrôles et singes que l'essai 38. Critères trouvés sur le web (guides anti-arnaque Solana,
seuils de fournisseurs d'outils, non vérifiés) et présents dans le corpus, tous connus **au lancement** :
10 plus gros porteurs ≤ 25 % des jetons, plus gros porteur ≤ 10 %, achat du créateur ≤ 5 %, aucun ancien coin du
créateur marqué arnaque (`creator_past_rugs` = 0). Valeur absente = coin refusé. Coins marqués `top10_pct_suspect`
exclus. Market cap = prix × nombre de jetons (2 milliards en « mayhem », 1 milliard sinon), au moment de l'entrée.
(Les droits de création et de gel de jetons sont retirés d'office sur pump.fun : critère sans objet.)

**Filtres** : **F1** coin « propre » (les 4 critères) ; **F2** market cap à l'entrée ≥ 100 SOL ; **F3** F1 et F2.
**Entrées** K2, K3, K5 de l'essai 38 ; **sorties** T20 et T40. **18 cellules** (seuil z 2,77).
Pour information : la même cellule sans filtre (essai 38) à côté.

**Décidé d'avance** : comme l'essai 38 (une cellule prouvée → proposition d'un suivi papier, rien de plus).

## Essai 60 — memecoins pump.fun : copier les meilleurs portefeuilles, sortir en 3 lots

Écrit le 26 octobre 2026, **avant** tout calcul, à la demande de Yanisse (plateforme Axiom : suivre les plus gros
traders de memecoins, sniper les bons coins, ressortir petit à petit). Mêmes données, exécution et singes que
l'essai 38. Twitter et l'actualité ne sont pas testables (pas d'historique gratuit des tweets).

**Partie A — copier les portefeuilles.** Apprentissage : coins lancés du 5 au 30 juin ; test : coins lancés du
1er au 14 juillet (panne du 3 juillet exclue). Gain réalisé de chaque portefeuille en apprentissage = SOL des ventes
− SOL des achats (lignes `sol_amount` vides ou incohérentes exclues, adresse du System Program exclue), au moins
20 coins achetés. **W100** = les 100 meilleurs, **W1000** = les 1 000 meilleurs. Copie : au premier achat d'un de ces
portefeuilles dans un coin de test, dans les 10 premières minutes du coin, on achète au premier échange au moins
2 s après (une seule copie par coin). Sorties : **X1** on revend quand ce portefeuille fait sa première vente dans le
coin (+ 2 s) ; **T20** suiveur 20 % ; **L3** en 3 lots (définis en partie B). Toutes : au plus 60 min.
Frais Axiom : **1 % par côté en plus** de pump.fun (2,25 % par côté au total), non vérifié sur leur site.
Contrôles : ceux de l'essai 38, sauf les moitiés et 7 derniers jours remplacés par **chaque semaine de test
positive** (1-7 et 8-14 juillet). **6 cellules.**

**Partie B — sortir en 3 lots** sur les entrées K2, K3, K5 de l'essai 38 (tout le corpus, frais de l'essai 38 pour
comparer avec T20) : un tiers vendu quand le prix atteint 2 fois l'entrée, un tiers à 3 fois, le reste au suiveur
20 % ; le suiveur 20 % s'applique à tout ce qui reste à tout moment ; au plus 60 min. Chaque vente paie ses frais et
0,001 SOL de réseau. Contrôles de l'essai 38. **3 cellules.** Pour information : les mêmes avec les frais Axiom.

**9 cellules en tout** (seuil z 2,54). **Décidé d'avance** : comme l'essai 38.

## Journal des essais

| Date | Essai | Résultat |
|---|---|---|
| 2026-10-04 | Pré-enregistrement de A et B | — |
| 2026-10-04 | A et B sur les bougies Yahoo conservées (≈ 3 mois, 7 actifs), frais inclus | A : 858 trades, −0,27 R, PF 0,62 → **abandon** (Nasdaq +0,13 R sur 47 trades, S&P +0,06 R sur 60 : trop peu pour conclure). B : 665 trades, −0,46 R → **abandon**. Avant frais, l'avantage est proche de zéro ; les frais coûtent 0,36 à 0,57 R par trade sur les cryptos et 0,25 R sur l'euro. |
| 2026-10-05 | A et B sur 12 mois (historique long : Binance pour les cryptos, Dukascopy CFD pour S&P 500, or, pétrole, euro ; Nasdaq manquant, mauvais symbole corrigé), frais du bot | A : 3 696 trades, −0,23 R, PF 0,66, les deux moitiés négatives, 0 % des scénarios dégradés gagnants → **abandon confirmé**. Seul actif positif : S&P 500, +0,07 R sur 223 trades (PF 1,13). B : 2 827 trades, −0,33 R → **abandon confirmé**, négatif sur chaque actif. |
| 2026-10-05 | **Essai 2** : A sur Nasdaq et S&P 500, bougies Dukascopy du 28/09/2025 au 08/07/2026 (jamais regardées) | 388 trades, +0,03 R, PF 1,06 ; 1re moitié +0,10 R, 2de −0,03 R ; Nasdaq −0,03 R (218), S&P +0,11 R (170). Tests de résistance et plateau stop × objectif passés, mais facteur de profit < 1,1 et changement de signe entre les moitiés → **abandon**. La piste du premier essai ne se confirme pas. |
| 2026-10-05 | **Essai 3, découverte** (28/09/2025 → 04/10/2026, frais Topstep). Correction d'implémentation avant tout verdict : `gap_fade` et `noise_area` prenaient la bougie de 9:25 pour « clôture de la veille » (les CFD cotent la nuit) ; remplacée par la clôture de 16:00 de la séance précédente, comme écrit dans la règle | 4 candidats sur 56 : `noise_area` Bitcoin +0,24 R (216 trades, PF 1,22), `donchian_1h` or +0,18 R (153, PF 1,33), `rsi2_1h` or +0,05 R (244, PF 1,25), `gap_fade` or +0,05 R (85, PF 1,14). Le hasard seul en donnerait à peu près autant : la confirmation sur 10/2024 → 09/2025 tranchera. Tout le reste est écarté, souvent à cause des frais fixes (Ethereum, euro). |
| 2026-10-05 | **Essai 4, découverte** (28/09/2025 → 04/10/2026, frais Topstep) | Protection : trades du bot ouverts de −45 à +30 min autour d'une annonce −0,34 R (23 trades) contre −0,09 R ailleurs (3 520) ; de +30 min à +2 h : −0,29 R (51). Écart > 0,1 R → **protection gardée** (marge d'erreur large). `news_breakout` : négatif sur 6 actifs sur 7 (Nasdaq −0,28 R, S&P −0,20 R sur 24 trades ; Bitcoin +0,03 R, PF 1,08) → **écarté partout**. `pre_fomc` (pour information, 8 décisions) : Nasdaq +0,09 R, S&P −0,46 R. Corrigé au passage : le bot plaçait le rapport emploi au 1er vendredi à 12:30 UTC ; il suit désormais les dates officielles du BLS à 8:30 heure de New York (13:30 UTC l'hiver). |
| 2026-10-05 | **Essai 3, confirmation partielle** (10/2024 → 09/2025 jamais vue ; Bitcoin, Ethereum, S&P 500, pétrole) | `noise_area` Bitcoin : −0,14 R sur 226 trades → **écarté** ; `donchian_1h` Bitcoin (passé de justesse en découverte avec l'historique plus long) : +0,01 R sur 274 → **écarté**, mais +0,05 R ± 0,19 sur 24 mois : mis **en ombre** sur le marché réel (aucune notification) pour accumuler des preuves. Analyse de `noise_area` Bitcoin : tout le gain vient des 5 % meilleurs trades (stops à quelques dollars, irréalisables) ; en % du prix, pas d'avantage. |
| 2026-10-05 | **Essai 5** (`noise_area_v2`, stop ≥ 1 ATR 15 min), 24 mois | Bitcoin +0,04 R (495 trades) mais 2024-25 −0,04 R, −0,29 R sans les 5 % meilleurs, −0,003 % du prix → **écarté** ; S&P 500 −0,07 R, Ethereum −0,21 R, pétrole −0,20 R → **écartés**. L'or, le Nasdaq et l'euro suivent avec la confirmation de l'essai 3. |
| 2026-10-05 | **Essai 3, confirmation** (or, Nasdaq, euro) | **`donchian_1h` or VALIDÉ** : découverte +0,19 R (152 trades, PF 1,34), confirmation sur l'année jamais vue +0,12 R (162, PF 1,20) ; 24 mois +0,15 R ± 0,21 (314 trades), positif 7 trimestres sur 9, +0,10 % du prix par trade. Pas « prouvé » (marge corrigée pour 70 essais). Réserve : l'or a pris +58 % sur la période ; les achats font +0,56 R puis +0,22 R, les ventes −0,38 R puis +0,16 R : une partie du gain peut venir de la hausse de l'or. Comme tout suivi de tendance, le résultat dépend des gros gagnants (stops à 2 ATR, réalistes). → **en ombre sur le marché réel** depuis le 05/10/2026. `rsi2_1h` or (−0,01 R), `gap_fade` or (−0,02 R), `intraday_mom` or (−0,05 R) → **écartés à la confirmation**. Essai 5 : `noise_area_v2` Nasdaq (+0,03 / +0,12 R mais −0,23 R sans les 5 % meilleurs), or et euro → **écartés**. |
| 2026-10-05 | **Essai 4, protection sur 24 mois** (bot rejoué sur 10/2024 → 10/2026) | Fenêtre −45/+30 min : −0,18 R ± 0,32 (54 trades) contre −0,11 R ailleurs (7 262) ; +30 min à +2 h : +0,09 R (125). Écart −0,08 R, sous le seuil de 0,1 R fixé d'avance, et le signe change d'une année à l'autre (2024-25 −0,42 R, 2025-26 +0,14 R) : **pas de preuve que la pause aide ni qu'elle nuise**. Elle ne retire que 0,7 % des trades et le backtest ne voit pas l'élargissement réel des écarts de prix pendant les annonces : **gardée** par prudence. |
| 2026-10-06 | Mesures exploratoires, **non pré-enregistrées** (bot actuel rejoué sur 24 mois) | Trades expirés : 19 % des trades, +0,07 R en moyenne à l'expiration ; les prolonger jusqu'à 3 h n'améliore rien (TP et SL touchés à parts égales ensuite). Horizon 3 h contre 1 h, frais Topstep : or **+0,10 R ± 0,08 en 3 h** (+0,15 puis +0,06 R) contre +0,03 R en 1 h ; Nasdaq +0,02 R dans les deux cas ; S&P 500 −0,03/−0,05 R ; pétrole, euro, Bitcoin négatifs ; Ethereum −0,55 à −0,60 R (frais du micro-contrat MET, 3,6 fois l'estimation du bot) ; euro −0,19 R (frais M6E 1,6 fois l'estimation). Choisi parmi 14 combinaisons : à confirmer en ombre avant tout signal réel. |
| 2026-10-06 | Horizon 3 h sur l'or séparé des autres actifs | En ombre depuis le 06/10 sous la variante `horizon_3h_gold` (promue ou non pour l'or seul, avec la marge corrigée du nombre d'essais). Les 16 trades 3 h de l'or déjà suivis restent dans la variante commune `horizon_3h` (−0,06 R, frais du bot). Ethereum, euro et pétrole étaient déjà à l'essai (aucun signal réel). |
| 2026-10-07 | **Essai 6** : poche actions et pépites halal contre des témoins du même univers (06/2021 → 10/2026, 500 tirages, frais de rotation 0,3 %) | **Biais du survivant mesuré** : dans l'univers actuel, de simples tirages au hasard font +21 %/an et le poids égal +23,5 %/an, contre +12 %/an pour l'ETF Monde islamique : environ la moitié du +40 %/an de la poche venait du choix de l'univers, pas de la règle. **Poche** : +39,8 %/an contre +23,5 % au poids égal (mieux que 99,8 % des tirages), mais **seulement sur la 1re moitié** (+52 % contre +17 %) ; 2de moitié +28,8 % contre +29,8 % au poids égal (mieux que 60 % des tirages) → **apport non démontré** selon la règle fixée d'avance ; 2,6 fois plus volatile que le poids égal (chute max −29 % contre −12 %). **Pépites** : +11,8 %/an contre +11,9 % au poids égal, mieux que 65 % des tirages, chute max −19 % contre −9 % → **aucun apport**. **Variantes** anti-krach et corrélation : chute maximale inchangée ou pire → **aucune adoptée**. Corrélation moyenne entre les 15 actions retenues : 0,17, aucune paire au-dessus de 0,75 (pas de pari caché mesurable sur 24 mois). **AAOIFI** : les 15 conformes, purification de 0 à 1,3 % (Micron 1,3 %, Atlassian 1,1 %). **Portefeuille Dynamique du site** (poche 20 %, pépites 5 %, Bitcoin 3 %) : +18 %/an, chute max −17 %, pire année −5 %, perte mensuelle à 95 % : −7 % ; 1 000 € puis 200 €/mois → 10 200 € versés, 15 398 € ; pire recul −1 113 € (mars 2025). Ces chiffres incluent le biais de la poche. Recommandation prévue d'avance : poche ramenée à 10 %, pépites ≤ 5 % — **à décider par Yanisse**. Bug corrigé au passage : le mois de classement était la médiane des mois *distincts* (quelques historiques arrêtés tôt l'ont fait reculer à juillet 2026) ; c'est désormais la médiane de toutes les actions. |
| 2026-10-07 | Chances de réussir le Combine Topstep 50K (outil d'information, **non pré-enregistré**, aucune décision automatique) : Monte Carlo LuxAlgo, 10 000 parcours, bootstrap par blocs des R nets Topstep | Témoin sans avantage (mêmes trades, moyenne 0 R) : 29 % par tentative à 250 $. Bot : 22 % (backtest, 376 trades, −0,02 R) et 28 % (compte simulé, 55 trades, −0,01 R) → **pas mieux que le hasard**. `donchian_1h` or : **48 %** à 250 $ (2,1 essais, 580 $ de frais, 82 jours), 32 % à 500 $ (gain moyen 0,15 R mais 36 % de gagnants : à 500 $, les séries de pertes touchent la perte maximale). Un compte réussi ne prouve rien seul : sans aucun avantage, près de 3 tentatives sur 10 réussissent. |
| 2026-10-07 | **Essai 7**, référence figée (R nets Topstep, 24 mois) et premier contrôle | Référence : `donchian_1h` or 313 trades, +0,15 R ; `donchian_1h` Bitcoin 511 trades, +0,07 R ; `horizon_3h_gold` 694 trades, +0,10 R. Premier contrôle : Donchian or et Bitcoin 1 trade chacun (−0,5 et −1,0 R) → trop tôt ; `horizon_3h_gold` 5 trades, −3,0 R cumulés, 8,5 % des tirages font pire, pire baisse sous le 81e percentile → **dans la norme**. |
| 2026-10-07 | Audit de faisabilité des prix d'exécution (mesure, **non pré-enregistrée**, aucun réglage changé) : bot rejoué sur 24 mois (7 424 trades, 7 actifs) et 70 couples du laboratoire | Bot : **aucun stop franchi par un saut de prix** (coût 0 R), aucun stop de moins de 4 ticks, 22 bougies touchant objectif et stop (0,6 % des stops, comptées en stop par prudence), écart d'entrée moyen +0,001 R. 2 sorties hors bougie (Nasdaq, 24/04/2026 15:45) : saut au-dessus de l'objectif, compté à l'objectif alors qu'un ordre limite aurait obtenu mieux → prudent. Laboratoire : aucune sortie ni entrée hors de sa bougie ; `donchian_1h` or propre (écart d'entrée −0,0003 R). Stops irréalisables (< 4 ticks) seulement sur des couples déjà écartés : `orb5` euro 79, `noise_area` euro 42, `orb5` pétrole 13. Limite : données CFD (Dukascopy) et Binance, sans écart achat-vente ni volume du contrat Topstep. Contrôle désormais automatique après chaque backtest. |
| 2026-10-07 | Comparaison des prop firms (information, **non pré-enregistrée**) : mêmes R rejoués sur 55 comptes d'évaluation 50K de 23 firmes (annuaire LuxAlgo, règles non vérifiées une à une), 250 $ et 500 $ de risque | Donchian or à 250 $ : 70-80 % sur les comptes CFD à perte maximale fixe de 8-10 % (témoin sans avantage 25-42 %), en 140-230 jours de bourse ; à 500 $ : 60-69 % en 56-106 jours. Futures : Apex 60 %*, Tradeify 52 %*, Topstep 47 %. **Donchian garde ses positions la nuit (215/313 trades) et le week-end (67)** : interdit chez Topstep et la plupart des firmes futures → son chiffre Topstep est théorique ; une version fermée chaque soir serait un nouvel essai. Bot (backtest) : sous le témoin partout. Rien n'est décidé automatiquement ; changer de firme est un choix de Yanisse, après vérification des règles sur le site de la firme. |
| 2026-10-07 | **Essai 8** (`donchian_day`, frais Topstep). Correction d'implémentation avant verdict : les jours de séance écourtée (fériés), aucune bougie ne finissait à 15:00 et 10 positions restaient ouvertes la nuit ; la sortie se fait désormais à la dernière clôture de la séance, et la dernière bougie d'une séance ne permet plus d'entrer (même règle écrite). Comptage des week-ends corrigé (un dimanche soir et le lundi tombaient dans deux semaines ISO) | **Or VALIDÉ** : découverte +0,11 R (226 trades, PF 1,26, moitiés +0,12 / +0,10), confirmation +0,07 R (256, PF 1,16) ; 24 mois +0,09 R ± 0,05 (482 trades), pas « prouvé » (74 essais) ; essai 5 pour information : −0,07 R sans les 5 % meilleurs trades (dépend des gros gagnants, comme tout suivi de tendance), +0,05 % du prix par trade ; achats +0,12 R, ventes +0,03 R. 0 position gardée la nuit ou le week-end (contre 215 et 73 pour `donchian_1h`). Nasdaq −0,04 R, S&P 500 −0,06 R, Bitcoin +0,09 puis −0,01 R → **écartés**. → **en ombre sur le marché réel** depuis le 07/10/2026 (contrôle de décrochage de l'essai 7 compris). Chances Topstep 50K : 58 % par tentative à 250 $ (financé en 59 jours de bourse pour la moitié des parcours, 9 sur 10 en 144), 42 % à 500 $ (28 jours, 9 sur 10 en 76), témoin sans avantage 29 % et 25 %. |
| 2026-10-07 | Mesure exploratoire, **non pré-enregistrée** : réussir le Combine Topstep 50K **en 10 jours de bourse au plus**, et `donchian_day` sur les 4 actifs ensemble | En 2 semaines : témoin sans avantage 13 % (250 $) / 22 % (500 $) / 21 % (750 $), bot 10 / 19 / 19 %, `donchian_day` or 0 / 5 / 9 %, `donchian_day` 4 actifs 10 / 16 / 17 % → **aucune série ne fait mieux que le hasard en 2 semaines** ; réussir aussi vite, c'est de la chance. `donchian_day` sur or + Nasdaq + S&P 500 + Bitcoin : 2 274 trades, +0,008 R en moyenne (les trois actifs perdants annulent l'or), 27 % sans limite de temps contre 29 % pour le témoin → mélanger les actifs écartés n'aide pas. |
| 2026-10-07 | **Essai 9** : 3 stratégies intraday sur l'or (frais Topstep), puis réussite du Combine en 10 jours contre leur témoin | `donchian_15m_day` (2,8 trades/jour) : découverte +0,06 R (739, PF 1,11), confirmation +0,03 R (745, PF 1,05 < 1,1) → **écarté** ; `donchian_30m_day` (1,6/jour) : +0,08 R (404, PF 1,17) puis +0,05 R (426, PF 1,09 < 1,1) → **écarté** de justesse ; `comex_orb` (0,9/jour) : −0,10 R en découverte (moitiés +0,08 / −0,27) → **écarté**. En 2 semaines, aucune ne dépasse son témoin de plus de 3 points (12 % contre 9 % au mieux). Conclusion : sur ces données, plus de trades par jour sur l'or = gain par trade trop faible face aux frais ; **aucune stratégie n'est « utile pour aller vite »**. Ajout aux règles simulées : retrait après 5 jours gagnants d'au moins 150 $ ; `donchian_day` à 500 $ : 1er retrait 17 jours de bourse après le financement pour la moitié des parcours, au moins un retrait en 90 jours pour 61 % des comptes financés (témoin 24 %). |
| 2026-10-07 | **Essai 10** : `donchian_day` sur 17 contrats CME (Yahoo 1 h, mai 2024 → octobre 2026, frais TopstepX) | **Les 17 sont écartés**, presque tous dès la découverte (argent +0,03 R PF 1,07, cuivre +0,02, pétrole −0,03, gaz −0,12, fioul −0,06, essence −0,14, taux 10 ans −0,17, 30 ans −0,20, maïs −0,19, soja −0,10, blé −0,09, euro −0,17, livre −0,08, dollar australien −0,13, dollar canadien −0,14) ; seul le yen passe la découverte (+0,13 R, PF 1,30) mais pas la confirmation (+0,02 R, PF 1,04). Avant frais, la tendance fermée chaque soir est proche de zéro partout sauf le yen (+0,11 R) et l'or (+0,08 R). Contrôle or sur données Yahoo : confirmation +0,08 R (PF 1,18) mais découverte +0,05 R avec une moitié à 0,00 → échoue de justesse aux critères stricts, plus faible que sur les données Dukascopy (+0,11 / +0,07 R) : l'avantage de `donchian_day` sur l'or reste à confirmer en ombre. Pas de portefeuille. Leçon : l'effet de tendance documenté se mesure sur des semaines ou des mois ; fermer chaque soir en retire l'essentiel. |
| 2026-10-07 | **Essai 11** : tendance journalière sur 16 ETF (mars 2007 → octobre 2026, frais 0,05 %). Correction d'implémentation avant verdict : le gain latent du dernier trade encore ouvert était compté dans la courbe journalière ; seuls les trades clos le sont (verdicts inchangés) | **A. Donchian 55/20 : écarté** — 2007-2016 +0,37 R par trade (684 trades, PF 1,57), 2017-2026 −0,03 R (747, PF 0,96) ; 61 % d'années positives ; pire baisse 91 R ; sans les 5 % meilleurs trades −0,29 R (vit de ses gros gagnants). Gagnants : pétrole, or, Nasdaq 100, taux 7-10 ans, argent ; perdants : dollar canadien, australien, yen. **B. Momentum 12 mois : RETENU** — Sharpe 0,42 (2007-2016) et 0,54 (2017-2026), +3,9 % puis +4,8 % par an pour 10 % de volatilité, pire baisse −19 %, 2 années sur 3 positives (de −11 % à +19 %). → **suivi en ombre** depuis octobre 2026 (positions du mois sur la page Apprentissage, résultat réel chaque mois). Pour information : défi CFD 50 000 $ (+10 % puis +5 %, perte max 10 %, journalière 5 %) sur l'historique réel : A 26-28 % de réussite ; B (non pré-enregistré) ~40 % en 3 à 6 mois pour la moitié des départs. Ni l'un ni l'autre ne réussit un défi vite : c'est une stratégie de placement sur des mois, pas un défi en 2 semaines. |
| 2026-10-08 | Essai 11, suite | **Suivi en ombre du momentum 12 mois arrêté** à la demande de Yanisse : c'est une stratégie de placement sur des mois (levier, ventes à découvert), pas du trading. Résultats gardés au journal ; le code reste (`python run.py trend-daily`), mais plus de calcul chaque semaine ni de section sur le site. |
| 2026-10-08 | **`donchian_day` or passe en signaux réels** (choix de Yanisse, pas une promotion statistique : validé en backtest à l'essai 8, pas « prouvé », aucun trade réel encore) | Message Telegram à l'entrée (prix, stop, heure de sortie au plus tard, micros MGC pour le risque du compte Topstep simulé) et à la sortie (résultat en R et en $), sortie inscrite au journal du compte Topstep simulé. Le bot ne passe aucun ordre. Le contrôle de décrochage (essai 7) continue de le surveiller. |
| 2026-10-08 | **Essai 12** : réaction aux annonces (NFP, CPI, FOMC, 10/2024 → 10/2026) gardée jusqu'à 15:00 heure de Chicago | **Rien n'est retenu.** Or +0,32 ATR par annonce (58, t 1,03, positif les deux années mais trop incertain), Nasdaq +0,13 (t 0,26), S&P 500 −0,07, euro −0,62 (t −1,64 : la réaction a plutôt tendance à se retourner, surtout après l'inflation). Gardé jusqu'au lendemain : or +0,75, Nasdaq −0,33, S&P 0,00, euro −0,74. Observation après coup, non retenue : après les décisions de la Fed, la réaction continue sur les 4 actifs (+0,6 à +1,2 ATR) mais sur 15-16 décisions seulement, à peine plus de gagnants que de perdants (or 10 sur 16) ; sous-groupe repéré parmi 12, la chance suffit à l'expliquer. **H2** : seulement 5 trades Donchian or « contre la réaction » en 2 ans → pas de filtre. Les jours d'annonce, Donchian or fait −0,09 R (24 trades) contre +0,10 R les autres jours : trop peu pour conclure. |
| 2026-10-08 | **Essai 13** : essai 12 rejoué sur 2010-2024, jamais regardé (HistData, ~430 annonces emploi/inflation, ~87 décisions de la Fed par actif). Contrôle d'heure réussi : jours d'emploi, agitation maximale dans la bougie de 8:30 sur les 4 actifs (3 à 5 fois les autres) | **Rien n'est retenu, et les pistes de l'essai 12 ne se confirment pas.** H1 : or −0,10 ATR (t −0,58 ; +0,12 puis −0,31), S&P 500 −0,33 (t −1,77), Nasdaq −0,37 (t −1,87), euro +0,05 (t 0,29). H3, la Fed : or −0,13 (t −0,37), S&P 500 +0,02, Nasdaq +0,25 (t 0,76, −0,08 puis +0,62), euro +0,05. Sur les indices, la réaction tend même à se retourner un peu avant la clôture (non significatif, non pré-enregistré). Conclusion : sur 15 ans, le sens donné par une annonce ne prédit pas la suite de la journée ; ce qu'on avait vu sur 2 ans était du hasard. |
| 2026-10-09 | **Essai 14** : 13 idées, 49 cellules, 24 mois (découverte 28/09/2025 → 10/2026, confirmation 10/2024 → 09/2025), frais Topstep (Bitcoin : frais du bot). Bot rejoué : or 1 113 trades +0,02 R, Nasdaq 943 +0,02 R, S&P 500 867 −0,06 R, Bitcoin 1 102 −0,20 R | **Une seule cellule validée : A1 (pas d'entrée étirée) sur l'or** — découverte +0,06 R (348 trades, PF 1,13, moitiés +0,10 / +0,02), confirmation +0,07 R (279, PF 1,15) ; 24 mois +0,07 R ± 0,04 (627 trades) contre +0,02 R pour le bot seul ; pas « prouvé » (157 essais). **Tout le reste est écarté.** Nasdaq : A1, A2, A3, A5, C11, C12 passent la découverte (+0,05 à +0,09 R) mais tombent à zéro ou en négatif à la confirmation. S&P 500 et Bitcoin : aucune règle ne rend le bot positif (Bitcoin −0,18 à −0,21 R quel que soit le filtre ou la sortie). Sorties C11-C13 : rien de mieux que la sortie actuelle. Setups 15 min : B6 repli −0,07 à −0,51 R, B8 bougie étroite −0,22 à −0,57 R, B9 cassure ratée négatif partout sauf la découverte de l'or (+0,09 R puis −0,13 R) ; B7 (cassure avec volume) et B10 (ouverture hors du range de la veille) n'ont que 25 à 90 trades par période et changent de signe. Conclusion : sur ces données, entrer « sur repli » ne crée pas d'avantage ; seul le refus des entrées étirées aide un peu, et seulement sur l'or. Mise en ombre d'A1 sur l'or : à décider par Yanisse. |
| 2026-10-09 | Essai 14, suite | **A1 sur l'or mis en ombre** (accord de Yanisse) : chaque signal réel de l'or en 1 h est marqué `sans_etirement_or` s'il est étiré, sans rien changer aux notifications. Le filtre ne s'applique que s'il fait ses preuves sur les trades marqués (même règle que les autres filtres, page Apprentissage). |
| 2026-10-09 | Pré-enregistrement de l'essai 15 (25 idées, 97 cellules ; titre d'abord écrit « 22 idées », erreur de compte corrigée avant tout calcul) | — |
| 2026-10-09 | Essai 15, correction avant tout calcul sur données réelles | S27 : en entrant au-dessus de la ligne de cou avec le stop sous les creux, l'objectif « ligne de cou + hauteur » vaut **toujours** moins de 1 R (vu en testant le code sur des bougies synthétiques : 0 trade). La condition « ignoré si moins de 1 R » est retirée ; le reste de la règle est inchangé. |
| 2026-10-09 | **Essai 15** : 25 idées, 97 cellules, 24 mois, frais Topstep (Bitcoin : frais du bot), mêmes trades du bot rejoués qu'à l'essai 14 | **Deux cellules validées, aucune « prouvée » (254 essais).** **G40 limites du jour sur l'or** (3 trades par jour au plus, arrêt après 2 pertes) : découverte +0,09 R (412 trades, PF 1,18, moitiés +0,05 / +0,12), confirmation +0,06 R (374, PF 1,12) ; 24 mois +0,07 R ± 0,04 contre +0,02 R pour le bot seul. **S25 creux cassé puis repris sur le Nasdaq** : découverte +0,09 R (323, PF 1,15, moitiés +0,13 / +0,05), confirmation +0,10 R (338, PF 1,16) ; 24 mois +0,09 R ± 0,06. Avec 97 cellules, le hasard seul en ferait passer quelques-unes : ces deux-là restent à confirmer en ombre. Passés près : S25 or (+0,08 / +0,07 R, mais une moitié de découverte à −0,01 R), S26 retournement Nasdaq (+0,08 / +0,08 R, une moitié à −0,04 R). **Tout le reste est écarté** : aucun des 7 filtres F ne tient sur un actif ; sorties et stops G (objectif 3 R, stop sous 2 bougies −0,06 à −0,45 R, stop suiveur, renfort, sortie RSI, bougie exceptionnelle, demi-taille) ne font pas mieux que la sortie actuelle ; setups divergence (S16, 13 à 18 trades seulement), VWAP (S28, négatif partout), double creux (S27, négatif partout), milieu de la 1re bougie (S21) et écarts d'ouverture (S22) écartés. Bitcoin négatif dans les 25 idées. **Pour information**, bot complet rejoué (4 actifs ensemble, 4 025 trades) : à 10 % de risque par trade le compte est vidé ; à 1 %, il finit à 8 % du départ (pire baisse −94 %) : la règle du 1 % ralentit la chute, elle ne crée pas d'avantage. |
| 2026-10-09 | Essai 15, suite | **Mis en ombre** (accord de Yanisse), sans rien changer aux notifications : G40 sur l'or (signal réel de l'or marqué `limites_jour_or` s'il arrive après 3 signaux du jour ou après 2 pertes, jugé comme les autres filtres) ; S25 sur le Nasdaq (`creux_repris_15m`, suivi en ombre dans le laboratoire depuis le 09/10/2026 22:00 UTC, avec le contrôle de décrochage de l'essai 7). |
| 2026-10-09 | Pré-enregistrement de l'essai 16 (swing, 3 variantes, 12 cellules) | — |
| 2026-10-09 | **Essai 16** : swing (tendance jour + 1 h, repli du RSI en 15 min, stop sous le 2e creux 15 min), 24 mois, frais du bot | **Une cellule validée, pas « prouvée » (266 essais) : W2 deux unités sur le S&P 500** — découverte +0,05 R (71 trades, PF 1,12, moitiés +0,01 / +0,10), confirmation +0,10 R (79, PF 1,22) ; 24 mois +0,08 R ± 0,10 (150 trades ; estimation IC Markets +0,07 R). **Tout le reste est écarté** : or −0,06 à −0,08 R, Nasdaq −0,10 à −0,21 R ; Bitcoin très bon en découverte (W3 +0,62 R, W1 +0,36 R) mais nul ou négatif sur l'année d'avant (W1 −0,23 R, W3 +0,03 R). **Constat important** : avec un stop sous le 2e creux en 15 min, les positions ne durent que 7 à 11 h en moyenne (70 à 100 % des sorties au stop) : ce n'est pas encore un vrai swing de 2 à 5 jours ; le stop est trop proche pour l'horizon visé. Un stop sous les creux 1 h serait un nouvel essai. Environ 60 à 90 trades par an et par actif, donc des marges d'erreur larges (± 0,10 à 0,33 R). |
| 2026-10-10 | Pré-enregistrement de l'essai 17 (toutes nos stratégies sur le DAX et l'Euro Stoxx 50, 108 cellules) | — |
| 2026-10-10 | **Essai 17** : toutes nos stratégies (54) sur le DAX et l'Euro Stoxx 50, Dukascopy du 26/08/2024 au 09/10/2026, frais du bot (DAX 0,01 %, Euro Stoxx 0,03 %), horloge européenne | **Aucune cellule validée sur 108.** Bot rejoué : DAX −0,01 R (924 trades ; +0,08 R avant frais), Euro Stoxx −0,20 R (446). Seules 3 cellules sont positives sur les deux périodes, toutes sur le DAX et toutes sous le seuil de confirmation (facteur de profit < 1,1) : F3 tendance journalière +0,13 puis +0,05 R (PF 1,09), `donchian_1h` +0,09 puis +0,05 R (PF 1,09), G30 objectif 3 R +0,07 puis +0,03 R (une moitié de découverte négative). Nos 3 stratégies validées ailleurs ne passent pas : `donchian_day` DAX −0,02 R, Euro Stoxx −0,07 R ; limites du jour (G40) DAX −0,02 R ; creux repris (S25) DAX 0,00 R, Euro Stoxx −0,28 R. Euro Stoxx négatif presque partout (frais plus lourds, données de séance seulement). 15 cellules sur 108 sont positives sur 24 mois, à peu près ce que donnerait le hasard. Conclusion : rien à tirer de ces deux indices avec nos stratégies actuelles ; le DAX est légèrement positif avant frais, comme le Nasdaq. |
| 2026-10-13 | **Essai 18** : scalping de quelques minutes sur l'or (bougies 1 min Dukascopy 10/2024 → 10/2026, 4 entrées + leur réunion × 2 sorties, frais 0,30 $ par once, 384 essais) | **Les 10 cellules sont écartées.** Seule R1 (repli sur la MM20) passe la découverte en sortie 1 pour 1 : +0,06 R (263 trades, PF 1,12, moitiés +0,02 / +0,09), puis s'effondre en confirmation : −0,13 R (245, PF 0,76) ; 24 mois −0,04 R ± 0,04 (brut +0,09 R, frais 0,08 R par trade). R3 (RSI 50) −0,10 R, R4 (chiffre rond, 4,5 trades/jour) −0,10 R et **déjà −0,02 R avant frais**, R2 (cassure de pause) 14 trades seulement, réunion R1-R4 −0,11 R (5,6 trades/jour). La sortie moitié + suiveur ne change presque rien. Stop moyen 3,7 à 5,5 $ : les frais d'un compte ECN coûtent 0,06 à 0,08 R par trade. Conclusion : sur ces règles, le scalping de quelques minutes n'a pas d'avantage sur l'or, même avant frais pour la plupart des entrées ; rien ne va en démo. |
| 2026-10-13 | **Essai 20** : rebond après une bougie 5 min d'épuisement sur l'or (idée de Yanisse ; bougies 1 min 10/2024 → 10/2026, frais Vantage 0,21 $, 394 essais) | **Les 4 cellules sont écartées.** Avec niveau tenu, objectif 2R : découverte +0,08 R (258 trades, PF 1,14, moitiés +0,12 / +0,03) puis confirmation **−0,32 R** (181, PF 0,57) ; 24 mois −0,08 R, brut 0,00 R. Niveau 1R : +0,01 puis −0,25 R. Sans niveau (≈ 1 800 trades) : −0,05 à −0,17 R. Avant frais, le rebond après une bougie d'épuisement est à zéro (−0,01 à +0,01 R) : sur l'or, ce schéma ne donne pas d'avantage mesurable ; le bon exemple du 13/10 au matin était un cas favorable parmi d'autres. |
| 2026-10-13 | **Essai 19** : scalping de quelques secondes sur l'or (ticks Dukascopy du 31/08 au 12/10/2026, 6,1 millions de ticks, départ brusque de 0,30 $ en 10 s dans le sens du contexte 5 et 15 min, sortie à +X / −S / 60 s, frais Vantage 0,21 $, 390 essais) | **Les 6 cellules sont écartées dès la découverte.** Toutes perdent environ **0,21 $ par once et par trade**, c'est-à-dire exactement les frais : avant frais, le résultat est à zéro (−0,014 à −0,003 $). En R : −0,21 à −0,23 R (stop 1 $), −0,43 à −0,46 R (stop 0,50 $), les deux périodes pareilles. Taux de réussite 33 % à 71 % selon l'objectif, sans que cela compense. Le signal se déclenche très souvent (200 à 280 trades par jour actif) : un départ de 0,30 $ en 10 s sur l'or est du bruit ordinaire, pas une information. Avec l'écart réel Dukascopy (≈ 0,55 $), pour information : −0,65 $ par trade. 4 fichiers horaires sur 434 manquants (2 absents, 2 en échec), sans effet sur la conclusion. |
| 2026-10-13 | Pré-enregistrement de l'essai 21 (test des 1000 singes sur toutes nos stratégies) | — |
| 2026-10-13 | **Essai 21** : test des 1000 singes (mêmes sens, stops, objectifs et durées, entrées tirées au hasard à la même heure) sur 230 cellules : les 54 stratégies de l'essai 17 sur l'or, le Nasdaq, le S&P 500 et le Bitcoin, et les essais 18 et 20. Précision avant tout résultat : pour les trades du bot, le singe garde l'objectif du signal même quand il n'a pas été touché | **220 cellules jugées, 29 battent les singes, une seule nettement : G40 limites du jour sur l'or** (+0,07 R contre −0,07 R pour les singes, battus 1000/1000, z 4,7 ; elle bat aussi 994 filtres au hasard). Les singes perdent en moyenne −0,08 R : sans signal, frais et gestion coûtent. **Stratégies suivies qui ne battent pas les singes** : Donchian or en signaux réels (+0,09 R, singes +0,02 R, battus 911/1000), Donchian 1 h or (886) et Bitcoin (927), W2 S&P 500 (799) ; A1 sans étirement or bat les entrées au hasard (1000) mais pas les filtres au hasard (949, seuil 950). Le marché de l'or qui montait explique une partie du gain du Donchian. Battent les singes : bot or (1000) et Nasdaq (973), S25 Nasdaq (964), R1 du démo (952, mais −0,04 R après frais). Signalé à Yanisse avec la proposition d'arrêter les stratégies suivies qui ne passent pas ; rien n'est changé sans son accord. |
| 2026-10-13 | Essai 21, suite | **Donchian or : fin des signaux réels, suivi en ombre** (choix de Yanisse). Plus aucune nouvelle entrée envoyée après le 13/10 19:30 UTC ; la vente ouverte à 18:00 UTC reçoit encore son message de sortie. Les autres stratégies en ombre continuent. |
| 2026-10-13 | Pré-enregistrement de l'essai 22 (plateau, centaines de trades, régimes, walk-forward, frais doublés) et des règles d'arrêt du démo | — |
| 2026-10-13 | **Essai 22** : plateau, centaines de trades, régimes, walk-forward (6 mois choisis, 3 mois joués, 7 trimestres), frais doublés, sur les 6 stratégies suivies | **Robustes (5 contrôles sur 5)** : Donchian or fermé chaque soir (+0,09 R, 482 trades, grille 15/15 positive, hausse/baisse/plat +0,09/+0,12/+0,09, walk-forward +0,12, frais ×2 +0,08), Donchian 1 h or (+0,15 R, 313 trades, walk-forward +0,09), **G40 or** (+0,07 R, 786 trades, grille 12/12, walk-forward +0,08 sur 6 trimestres sur 7, frais ×2 +0,02 ; perd en marché plat −0,10 R), **S25 Nasdaq** (+0,09 R, 661 trades, grille 15/15, walk-forward +0,08, frais ×2 +0,06). **Échouent** : Donchian Bitcoin (voisin sortie 5 h à −0,01 R, frais ×2 −0,01 R, perd en hausse −0,15 R) ; A1 or (ne gagne qu'en hausse : baisse et plat ≈ 0). Avec l'essai 21 : seules **G40 or et S25 Nasdaq passent tout** (singes compris). Les deux Donchian or tiennent tous les contrôles de solidité mais ne battent pas les entrées au hasard dans le même sens : leur gain vient surtout de la tendance de l'or. Rien n'est changé sans l'accord de Yanisse. |
| 2026-10-13 | Essais 21 et 22, suite | **Passent en réel** (choix de Yanisse, les deux seules qui passent les singes et les 5 contrôles) : **G40 sur l'or** appliqué aux signaux du bot (au-delà de 3 signaux dans la journée ou après 2 pertes, le signal de l'or n'est plus envoyé et reste suivi en silence) et **S25 creux repris sur le Nasdaq** en signaux réels Telegram (entrée, stop, objectif 3 R, sortie au bout de 4 h ou à 15:00 à Chicago ; relu toutes les 15 min). Validés, pas « prouvés » ; aucun ordre n'est passé par le bot. Le Donchian or reste en ombre. |
| 2026-10-13 | Variante de G40 proposée par Yanisse (mesure, **non pré-enregistrée**, rien changé) : pas de plafond de 3 trades, arrêt seulement après 2 pertes d'affilée | Bot or rejoué sur 24 mois : 982 trades, +0,04 R par trade, +42 R au total, frais ×2 −0,02 R, contre G40 actuel 786 trades, +0,07 R, **+58 R**, frais ×2 +0,02 R. Les 196 trades en plus (4e trade et suivants, ou après perte-gain-perte) perdent −0,08 R chacun (−0,13 R en découverte, −0,03 R en confirmation). G40 reste tel quel. |
| 2026-10-13 | Copie des signaux Telegram du bot sur le démo MetaTrader 5 (demande de Yanisse) | `mt5_copy.py`, magic 200001, mêmes distances de stop et d'objectif que le signal, 1 % du solde démo au stop. Règle d'arrêt écrite avant le premier trade : perte cumulée de 100 $ ou 8 pertes d'affilée. |
| 2026-10-13 | Pré-enregistrement de l'essai 23 (toutes nos stratégies sur 2014-2024) | — |
| 2026-10-14 | **Essai 23** : les 54 stratégies sur 2014 → 09/2024 (HistData 1 min, Bitcoin Binance dès 08/2017), frais Topstep (Bitcoin : frais du bot), 216 cellules | **G40 or ne tient pas** : 3 662 trades, −0,16 R, PF 0,73, 0 année positive sur 10 (avant frais +0,01 R : l'avantage vu en 2024-2026 n'existe pas sur les 10 ans d'avant). **S25 Nasdaq ne tient pas** : 3 901 trades, −0,13 R, PF 0,82, 2/10 (avant frais +0,02 R). **Donchian or** : jour −0,01 R (6/10), 1 h +0,03 R PF 1,05 (7/10) → ne tiennent pas. Bot seul : or −0,15 R, Nasdaq −0,02, S&P 500 −0,11, Bitcoin −0,10 → négatif partout. A1, W2, R1 : négatifs. **Tiennent** (6 sur 216) : `noise_area` Nasdaq +0,21 R (9/10), `noise_area_v2` Nasdaq +0,12 R, `donchian_1h` Nasdaq +0,06 R, `donchian_1h` Bitcoin +0,18 R (6/7), `orb30` Bitcoin +0,11 R, W3 Bitcoin +0,40 R (720 trades) — toutes écartées sur 2024-2026, donc **pas repêchées** (règle écrite d'avance). Conséquence prévue : proposer à Yanisse de remettre G40 et S25 en ombre. |
| 2026-10-14 | Pré-enregistrement de l'essai 24 (tout de A à Z sur 2014-2026) | — |
| 2026-10-14 | **Essai 24** : 216 cellules sur 2014-2026 d'un seul bloc, 10 contrôles (seuil singes corrigé z > 3,5) | **4 cellules prouvées, tout le reste échoue.** `noise_area` Nasdaq : 2 620 trades, +0,21 R, PF 1,17, 11 années positives sur 12, avant 2020 +0,17 / depuis +0,24, 2 dernières années +0,21, frais ×2 +0,08, singes 1000 (z 4,6). `noise_area_v2` Nasdaq : 2 912, +0,11 R, 9/12, singes 1000 (z 3,9). `donchian_1h` Bitcoin : 2 094, +0,15 R, 6/8, récent +0,05, singes 998 (z 4,1). W3 Bitcoin : 886, +0,39 R, 5/8, récent +0,32, singes 996 (z 4,8). **Pour information, hors règle** : `noise_area` Nasdaq vit de ses gros gagnants (−0,48 R sans les 5 % meilleurs ; v2 −0,19 R), stop médian 11,8 points, 6 stops < 4 ticks. **G40 or** : −0,12 R, 1/12 → pas robuste ; **S25 Nasdaq** : −0,10 R, 4/12, singes 569 → pas robuste ; Donchian or jour +0,00 R, 1 h +0,05 R PF 1,08 → pas robustes. Conséquences prévues : proposer G40 et S25 en ombre, et `noise_area` / `noise_area_v2` Nasdaq et W3 Bitcoin en ombre (`donchian_1h` Bitcoin y est déjà). |
| 2026-10-14 | Choix de Yanisse après l'essai 24 | **En signaux réels** (Telegram et copie sur le démo MT5) depuis le 14/10 08:00 UTC : `noise_area` et `noise_area_v2` Nasdaq, `donchian_1h` Bitcoin, W3 Bitcoin (`swing_w3`). **Remis en ombre** : G40 or (retiré des filtres appliqués au bot) et S25 Nasdaq (`LIVE_END`). Pas de passage préalable en ombre pour les quatre nouvelles : choix de Yanisse, contraire à la proposition écrite d'avance. Le bot ne passe aucun ordre réel. |
| 2026-10-14 | Pré-enregistrement de l'essai 25 (apprentissage du bot sur 12 ans, années cachées) | — |
| 2026-10-14 | **Essai 25** : le bot apprend sur ses signaux de 2014-2026, jugé année par année sur des années cachées (2017-2026), 8 cellules (seuil z > 2,5) | Bot seul 2017-2026 : or −0,08 R, Nasdaq +0,01, S&P 500 −0,07, Bitcoin −0,12. **Poids des critères (linéaire) : rien ne passe** (au mieux Nasdaq +0,03 R, PF 1,06). **Arbres : prouvés sur l'or et le Nasdaq.** Or : garde 284 signaux sur 4 430 (6 %), +0,14 R, PF 1,32, frais ×2 +0,05, 3 régimes positifs, bat les singes 1000 et les filtres au hasard 1000 (z 3,4) ; année 2022 −0,70 R. Nasdaq : garde 1 468 sur 4 458 (33 %), +0,09 R, PF 1,18, 8 années positives sur 10, filtres au hasard 999 (z 3,1). S&P 500 (−0,05 R) et Bitcoin (−0,04 R) : pas robustes. Conséquence prévue : proposer de brancher le modèle d'arbres sur le bot pour l'or et le Nasdaq. |
| 2026-10-14 | Choix de Yanisse après l'essai 25 | **Bot appris branché en réel** sur l'or et le Nasdaq : modèle d'arbres de l'essai 25 entraîné sur les 24 389 signaux 2014-2026 (data/models/bot_arbres.pkl), un signal n'est annoncé que si son R prévu est > 0 (filtre `modele_arbres`, les autres suivis en silence). **S&P 500 et Bitcoin mis à l'essai** (le bot y perd, avec ou sans apprentissage). Les stratégies du laboratoire sur ces actifs ne changent pas. À réentraîner chaque année. |
| 2026-10-14 | Pré-enregistrement de l'essai 26 (apprentissage par groupe de marchés, DAX) | — |
| 2026-10-14 | **Essai 26** : bot appris par marché seul, groupe d'indices (Nasdaq + S&P 500 + DAX) ou tous ensemble (5 marchés, DAX compris), années cachées 2017-2026, 13 cellules (seuil z > 2,9) | Bot seul 2017-2026 : DAX −0,00 R. **Seul : rien ne passe** (meilleurs Nasdaq +0,05 R et DAX +0,04 R, PF < 1,1 ; or −0,07). **Groupe indices : prouvé sur le Nasdaq** : garde 1 538 sur 4 458 (35 %), +0,10 R, PF 1,23, 6 années sur 8, 2017-21 +0,14 / 2022+ +0,07, 2 dernières années +0,08, filtres au hasard 1000 (z 4,2) ; S&P 500 −0,03 et DAX +0,01 échouent. **Tout ensemble** : Nasdaq robuste (+0,06 R, z 1,7, sous le seuil) ; **l'or ne garde plus que 151 signaux et échoue** (+0,07 R, filtres au hasard 940) alors qu'il était prouvé dans l'essai 25 avec 4 marchés : le résultat de l'or dépend des marchés mis avec lui, il est fragile. S&P 500, DAX, Bitcoin : échouent partout. Corrélation des rendements journaliers Nasdaq/S&P 500 0,93 ; or et Bitcoin presque indépendants des indices. Conséquence écrite d'avance : proposer le modèle « groupe indices » pour le Nasdaq. |
| 2026-10-14 | Choix de Yanisse après l'essai 26 | **Nasdaq** : le bot appris passe au modèle « groupe indices » (arbres entraînés sur les 16 537 signaux Nasdaq + S&P 500 + DAX 2014-2026, data/models/bot_indices.pkl). **Or** : garde le modèle de l'essai 25 (choix de Yanisse, alors que l'essai 26 le montre fragile). Rien d'autre ne change. |
| 2026-10-14 | **Essai 27** : l'or la nuit (idées du web), 2014-2026, 3 cellules (seuil z > 2,39), frais 0,30 $ l'once | **N2 heures asiatiques (achat 18:00 New York, vente 03:00) PROUVÉE** : 2 543 trades, +0,034 % net par trade (brut +0,053 %), 9 années sur 12, avant 2020 +0,003 % / depuis +0,064 %, 2 dernières années +0,10 %, frais doublés +0,016 %, bat 1000 singes sur 1000 (z 4,1). Réserve : presque nul avant 2020, le gain vient surtout de 2020-2026 ; l'écart du courtier à 18:00 (réouverture) peut dépasser les frais comptés. N1 nuit COMEX +0,031 % mais 7 années sur 12 et singes 877 → pas robuste. N3 vente le jour −0,009 % → pas robuste. Conséquence écrite d'avance : proposer N2 en ombre puis sur le démo MT5. |
| 2026-10-14 | Choix de Yanisse après l'essai 27 | **En signaux réels** (Telegram et copie sur le démo MT5) depuis le 14/10 12:00 UTC : `nuit_asie` or (achat 18:00 New York du lundi au jeudi, vente 03:00). Ajout d'un **stop de sécurité à 1 %** sous l'entrée, absent du test : sur 2014-2026, 91 stops touchés sur 2 565 nuits, +0,030 % net au lieu de +0,034 %. Pas de passage préalable en ombre (choix de Yanisse, contraire à la proposition écrite d'avance). Le bot ne passe aucun ordre réel. |
| 2026-10-14 | **Essai 28** : 7 stratégies courtes sur l'or trouvées par une recherche large (web, forums, études), 2014-2026, frais 0,30 $ l'once | **Rien ne passe.** A vente du matin (03:00-10:00) −0,016 % net (brut +0,003) ; B achat de l'après-midi −0,019 % ; C1 faux cassage du plus bas de la veille −0,007 % (brut +0,012, bat les singes mais pas les frais) ; C2 au plus haut −0,044 % ; E vente avant les fixings de Londres −0,010 % (brut +0,008, 6 384 trades) ; F retournement après l'emploi −0,030 %. **D suite de la Fed** : +0,10 % net, frais doublés +0,08, singes 991, mais 92 décisions seulement (< 100) et 7 années sur 12, presque nul depuis 2020 (+0,008 %) → pas robuste. Les effets « de l'heure » existent avant frais mais sont plus petits que l'écart du courtier. |
| 2026-10-14 | Choix de Yanisse : copie démo de `nuit_asie` | Le copieur MT5 accepte, pour cette stratégie seulement, le lot minimum (0,01) jusqu'à 5 % de risque du solde au stop de sécurité (≈ 41 $ sur 1 000 $), au lieu de 2 % pour les autres. Démo seulement. |
| 2026-10-14 | **Essai 29** : signaux du bot 2014-2026 (or, Nasdaq, S&P 500, Bitcoin), 168 réglages de stop et d'objectif (seuil z > 3,43). Correction avant verdict : les singes « le même jour » trichaient (le sens du bot suit le mouvement du jour, une entrée plus tôt le même jour en profite : singes à +0,3 à +0,7 R) ; remplacés par ceux de l'essai 21 : n'importe quel jour, même heure UTC, même sens, même stop en % du prix | **Nasdaq : 12 réglages prouvés**, en plateau : stop du bot × 1 à 3 avec objectif 1,5 à 5 fois le stop, par exemple stop × 1,5 et objectif 3 : +0,15 R, 10 années sur 12, objectif touché 26 %, stop 65 % (réglage actuel stop × 1 objectif 1 : −0,01 R). **Bitcoin : stop 2 %, objectif 3 prouvé** (+0,09 R, 7 années sur 9, gardé jusqu'à 20 jours). **Or : stop 1 %, objectif 3 robuste mais pas prouvé** (+0,11 R, 10 années sur 12, z 3,07) ; avec le stop du bot, l'or perd quel que soit l'objectif (−0,11 à −0,14 R). **S&P 500 : rien.** Un stop plus serré (× 0,5) est le pire partout. Conséquence écrite d'avance : proposer stop × 1,5 et objectif 3 sur le Nasdaq (milieu du plateau, pas le meilleur chiffre) et stop 2 % objectif 3 sur le Bitcoin. |
| 2026-10-14 | Choix de Yanisse après l'essai 29 | **Nasdaq** : les signaux du bot sortent désormais avec un stop ×1,5 (par rapport au stop du bot), un objectif à 3 fois ce stop et une durée maximale de 24 h (`signals.EXIT_OVERRIDE`) : +0,15 R net sur 2014-2026, 10/12 années positives, objectif touché 26 % du temps. Le modèle appris continue de filtrer sur le contexte d'origine. **Bitcoin** (stop 2 %, objectif 3, jusqu'à 20 jours) non appliqué : trades jugés trop longs. Or et S&P 500 inchangés. |
| 2026-10-14 | **Essai 30** : 12 stratégies Bitcoin courtes trouvées par une recherche large (études, Quantpedia, blogs), Binance 5 min 2017-2026, frais 0,06 % (seuil z > 2,64) | **Prouvées : B10 cassure Larry Williams** (achat quand le prix dépasse l'ouverture du jour UTC + 0,5 × l'amplitude de la veille, vente à 00:00 UTC, ≈ 13 h) : 1 299 trades, +0,31 % net par trade, 6/8 années, avant 2020 +0,58, depuis +0,22, 2 dernières années +0,08, frais doublés +0,25, singes 997, z 3,25 ; **B11** (la même, au-dessus de la moyenne des 5 jours) : 704 trades, +0,44 %, z 3,47. Années faibles : 2022 (−0,26 / −0,55) et 2025 (−0,11 / −0,03). Pas robustes : heure du soir 21-23 UTC (B1-B3 : bat les singes mais ≈ 0 depuis deux ans), contre une grosse bougie (B4-B6 : marchait avant 2020 seulement), dernière demi-heure (B7-B8 : rien), plus haut de 10 jours (B9 : 2 dernières années −0,21), lundi de Tokyo (B12 : ne bat pas les singes). |
| 2026-10-14 | Choix de Yanisse après l'essai 30 | **En signaux réels** (Telegram et copie sur le démo MT5) depuis le 14/10 14:00 UTC : `cassure_williams` Bitcoin (B10). Ajout d'un **stop à l'ouverture du jour** (00:00 UTC), absent du test : sur 2017-2026, +0,32 % net par trade au lieu de +0,31 % (1 299 trades, même règle rejouée par `strategies.cassure_williams`). Pas de passage préalable en ombre. |
| 2026-10-14 | Choix de Yanisse : bot classique en ombre sur S&P 500, Bitcoin et Ethereum | Leurs signaux classiques ne sont plus envoyés ni copiés sur le démo (filtre `bot_en_ombre`, `engine.SHADOW_ASSETS`), mais suivis en silence. Raison : perdant sur 2014-2026 (essais 23 et 24) et aucun filtre appris ne le sauve (essais 25 et 26) ; l'Ethereum n'a pas de test long. Restent en réel : bot classique filtré par le modèle sur l'or et le Nasdaq, et les stratégies prouvées (zone de bruit et v2 Nasdaq, Donchian 1 h, swing W3 et cassure Williams Bitcoin, nuit asiatique or). |
| 2026-10-14 | **Essai 31** : pétrole et euro sur 2014-2026 (HistData, pétrole 2024-05/2026 complété par Dukascopy), frais du bot | **Rien ne passe.** Partie A (54 stratégies, seuil z > 3,30) : bot classique pétrole −0,08 R (8 004 trades, 0/12 années), euro −0,17 R (5 433, 0/12) ; meilleure cellule W1 pétrole +0,08 R, 9/12 années, mais négative sur les 2 dernières années. Partie B (11 idées du web) : P4 bande à l'ouverture pétrole +0,08 % net, 902 trades, singes 1000 (z 3,07), mais 2 dernières années −0,06 % ; P5 contre le rapport EIA +0,33 % net mais 50 trades seulement ; P1-P3 (élan de fin de séance) ≈ 0 avant frais, négatif après ; euro E1a et E2a (vente pendant Londres) battent les singes (987, 990) mais ≈ +0,01 % brut, nul depuis 2020 ; E1b, E2b, E6 rien. P6 (rapport API) mal mesuré : 144 trades seulement (bougies de 17:00 manquantes après 2015), négatif. Pétrole et euro restent « à l'essai », rien n'est envoyé. |
| 2026-10-14 | Choix de Yanisse : taille des copies démo | Au moins 0,50 $ par point sur le NAS100 (0,5 lot) et 1 $ sur le SP500 et l'or (`mt5_copy.MIN_POINT_VALUE`), tant que le risque au stop reste sous 10 % du solde ; rien pour les cryptos. Arrêt de la copie relevé de 100 $ à 300 $ de perte cumulée (`demo_rules`), 8 pertes d'affilée inchangé. Démo seulement. |
| 2026-10-14 | **Essai 32** : réajuster le stop pendant le trade (A entrée dès +1 R, B entrée dès +0,5 R, C suiveur à 1 R, D +1 R dès +2 R) sur les 8 stratégies en réel, 2014-2026 | **Aucune variante ne fait mieux** (32 cellules, seuil z 2,96 ; pré-enregistré 2,95). Le stop qui bouge coupe les gros gagnants : zone de bruit Nasdaq +0,21 R → +0,04 à +0,07 R (A, B, D), −0,04 R (C) ; W3 Bitcoin +0,39 R → +0,10 R (A) ; bot Nasdaq +0,15 R → +0,06 à +0,13 R ; Donchian 1 h et cassure Williams Bitcoin un peu moins bonnes. Nuit asiatique or et bot or : écart ≈ 0, pas mieux. Le stop de départ reste fixe partout. |
| 2026-10-15 | Choix de Yanisse : copies démo à la taille de la simulation | Le trade « nuit asiatique » or du 14/10 a fait +288,75 $ sur la simulation (1 MGC = 10 $ par point, risque 412 $ soit 38,7 % : lot minimal imposé) et +32,05 $ sur le démo (0,01 lot = 1 $ par point). Désormais chaque copie prend les mêmes $ par point que la position de la simulation (`mt5_copy.sim_sizes`, `mirror_lot`, lu sur docs/portfolio.json) ; 1 % du solde seulement si la simulation est illisible. Arrêt de la copie (300 $, 8 pertes d'affilée) inchangé en attendant sa réponse. |
| 2026-10-15 | Choix de Yanisse : risque des copies démo | Le trade « nuit asiatique » or du 14/10 a fait +288,75 $ sur la simulation (1 MGC = 10 $ par point, 10 % de risque visé, lot minimal imposé) contre +32,05 $ sur le démo (0,01 lot, 1 % de risque). Toutes les copies MT5 risquent désormais **5 % du solde démo** au stop (`mt5_copy.RISK_PCT`, 1 % avant) ; lot minimal toléré jusqu'à 10 %, planchers $/point inchangés. Un essai de copie à la taille exacte de la simulation (commit 0e25b3bf3) est annulé. |
| 2026-10-15 | Pré-enregistrement des essais 33 à 37 (idées des vidéos @kara_tools) | — |
| 2026-10-15 | **Essai 35** : structure de marché sur l'or (vidéo « lire le prix »), or 1 min HistData 2014 → 09/10/2026 regroupé en 1 h et 5 min, frais 0,30 $, 8 cellules (seuil z 2,50) | **Rien ne passe : les 8 cellules sont négatives.** 1 h : S1 creux fort + clôture + rapide −0,10 R (419 trades, PF 0,63, 2/12 années), S2 creux fort −0,08 R (1 022), S4 mèche −0,10 R (649) ; le témoin S3 creux faible fait mieux, +0,02 R (885, PF 1,02, 5/12 ; brut +0,12 R), le contraire de ce que dit la vidéo. 5 min : −0,15 à −0,24 R (4 574 à 11 467 trades, 0/12 années). Avant frais aussi négatif pour les creux forts (1 h −0,04 à −0,06 R, 5 min −0,02 à −0,04 R) : les règles de la vidéo (creux confirmé, repli ≥ 50 %, clôture, vitesse) ne donnent pas d'avantage sur l'or. Détail : une cassure n'est comptée que s'il y a au moins une bougie entre le sommet et la cassure. |
| 2026-10-15 | **Essai 34** : stop selon l'heure (k × amplitude médiane de l'heure d'entrée) contre stop constant de même taille moyenne, sur les entrées S2, 6 cellules (2,64) | **Pas mieux.** Écarts appariés −0,025 à +0,035 R, z −1,16 à +1,16 ; les deux versions restent négatives ou nulles (meilleure : témoin k = 3 en 1 h, +0,01 R). Adapter le stop à l'heure ne change pas le résultat. |
| 2026-10-15 | **Essai 33** : les annonces (emploi, inflation, Fed 2014-2024) | **33a** : à la minute d'une annonce, la bougie 1 min de l'or fait 2,75 $ contre 0,73 $ les autres jours à la même minute (×3,7). Sur les stops de l'essai 35 touchés dans la minute d'une annonce (31 cas), glissement au pire prix de la minute : 3,76 $ en moyenne, jusqu'à 15,44 $. **33b** (pas d'entrée 30 min avant à 15 min après, sortie 30 min avant) : écart positif partout mais minuscule, +0,002 à +0,019 R, aucune cellule prouvée (S4 5 min z 3,42 mais la stratégie reste à −0,19 R, contrôle « variante R > 0 » raté). Le filtre limite un peu la casse, il ne rend pas une stratégie gagnante. **33c** (journaux du démo MT5) : pas faite, le PC n'était pas relié à cette session. |
| 2026-10-15 | **Essai 37** : anciens extrêmes sur l'or (vidéo « 3 portes ») | **37a** : après le dépassement du plus haut ou du plus bas de la séance d'avant, le prix est encore au-delà 52,5 % du temps 15 min après (3 114 cas) et 50,6 % 1 h après ; témoin (niveau décalé de 0,25 % vers l'intérieur) 59,0 % et 58,0 %. Le « 64 sur 100 » de la vidéo ne se retrouve pas sur nos données, et le niveau de la veille ne fait pas mieux qu'un niveau quelconque. **37b** sortie 15 min −0,03 R (2 910 trades, PF 0,77), **37c** 1 h −0,05 R (2 900, PF 0,79) : écartées. |
| 2026-10-15 | **Essai 36** : profil de volume de la veille sur le Bitcoin (Binance 2017-2026) | **36a confirmé** : le prix passe moins de temps par tranche dans les zones creuses que dans les zones pleines (rapport 0,78 contre 0,94 avec le profil d'un autre jour, 200 tirages sur 200 battus) : la vidéo a raison sur la forme. **Mais on ne peut pas en vivre** : 36b traverser une zone creuse −0,44 R (22 973 trades, PF 0,28 ; brut −0,06 R), 36c dans la zone de valeur −0,45 R (8 924) ; stops ≈ 0,3 % du prix, les frais (0,06 %) pèsent 0,2 R par trade et même avant frais c'est négatif. Écartées. |
| 2026-10-15 | **Essai 33c** : journaux du démo MT5 (PC relié en fin d'essai) | Seulement **3 stops touchés** depuis le 13/10 (NAS100 copie, or pont, or manuel), tous remplis **exactement au prix du stop** (glissement 0), aucun pendant une annonce. Trop peu de cas pour conclure ; un compte démo remplit souvent sans glissement, le réel peut faire pire. À refaire quand le démo aura au moins 30 stops, dont quelques-uns près d'une annonce. |
| 2026-10-15 | Choix de Yanisse : bot classique or | Gardé en signaux réels, filtré par le modèle de l'essai 25 (≈ 6 % des signaux gardés), malgré la fragilité vue à l'essai 26. Courbe Labo −722 R = bot sans filtre. |
| 2026-10-16 | Choix de Yanisse : or = nuit asiatique seule | Bot classique or retiré des signaux réels (engine.SHADOW_ASSETS, suivi en ombre) : sans le filtre du modèle de l'essai 25 il fait −722 R sur 2014-2026. Nuit asiatique copiée sur le démo à 0,05 lot minimum (mt5_copy.MIN_LOT), ≈ 210 $ si le stop de sécurité à 1 % est touché. |
| 2026-10-16 | Demande de Yanisse : messages Telegram lisibles et signaux pris partout | Messages des stratégies refaits au format du bot (↗️ ACHAT / ↘️ VENTE en gras, prix en code, SL/TP alignés, Topstep + Simulation + MT5 à l'entrée) ; la sortie répond au message d'entrée (✅ GAIN / ❌ PERTE, raison, résultat Topstep frais compris et Simulation). Copie MT5 : 3 signaux manqués (nuit asiatique 15/10, zone de bruit et v2 16/10 14:00) car l'âge partait de la bougie d'entrée et non de l'annonce : corrigé ; SL trop court élargi au minimum du courtier au lieu d'un rejet 10016. Journal Topstep : zone de bruit et v2 au même instant avaient le même identifiant (suffixe v2). |
| 2026-10-16 | Demande de Yanisse : stratégies calculées sur le PC avec les prix live MT5 | Le pont rejoue les stratégies en signaux réels (strategies.LIVE) sur les bougies 5 min du courtier dès qu'une bougie se ferme (trading_bot/mt5_local.py) et copie tout de suite sur le démo. Bascule : si le calcul local échoue (pas de bougies, marché fermé), la copie reprend les signaux de GitHub comme avant ; un signal GitHub de la même stratégie, même sens, à moins de 3 h d'un signal local, n'ouvre pas une 2e position. Telegram, Topstep et Simulation restent sur GitHub. Écarts possibles : prix CFD ≠ contrats à terme, une cassure peut tomber une bougie plus tôt ou plus tard. |
| 2026-10-16 | Relevé du soir : copies MT5 contre Telegram | 2 défauts trouvés et corrigés. (1) Au redémarrage du pont (15:45 UTC), les copies GitHub que le PC voyait aussi (zone de bruit v2 0,8 lot, W3 Bitcoin 0,06) ont été fermées à tort : la zone de bruit v2 a ensuite fini à +1,62 % sur Telegram. (2) La vente Nasdaq du bot de 17:10 UTC a été copiée 8 min plus tard, ≈ 195 points plus bas : stop touché sur MT5 (−66 $) alors que le signal a touché son TP. Désormais un signal GitHub n'est plus copié si le prix a déjà fait plus de la moitié de la distance du stop depuis l'annonce. |
| 2026-10-18 | Pré-enregistrement de l'essai 38 (memecoins pump.fun) | — |
| 2026-10-18 | **Essai 38** : memecoins pump.fun (5 juin → 14 juillet 2026, 505 782 coins utilisables, morts compris), mise 0,5 SOL, frais 1,25 % par côté + 0,001 SOL, délai 2 s, 12 cellules (seuil z 2,64) | **Rien ne passe : les 12 cellules perdent.** Entrer dès le lancement (K1) : −9 à −13 % par trade, 82 à 86 % de trades perdants. Entrer après la montée : K2 (prix ×2) −8 à −15 % (61 025 trades), K3 (×3) −7 à −14 % (19 956), K5 (×5) **−5 à −12 %** (5 812). Meilleure : K5 suiveur 20 % −5,1 % par trade, PF 0,78, 69 % de perdants, −15 % sans les 5 % meilleurs. Négatif sur les deux moitiés, les 7 derniers jours et avant les frais doublés. Plusieurs cellules battent les singes (K5 T20 z 9,3) : entrer après une montée perd **moins** qu'un coin au hasard, mais perd quand même. Réserve : corpus tiers non vérifié sur la chaîne. Pas de suivi papier. |
| 2026-10-18 | Pré-enregistrement de l'essai 39 (memecoins, filtre des bons coins) | — |
| 2026-10-18 | **Essai 39** : memecoins pump.fun, ne garder que les « bons » coins (critères du web), 18 cellules (seuil z 2,77) | **Rien ne passe : les 18 cellules perdent.** **F1 coin « propre »** (10 plus gros porteurs ≤ 25 %, plus gros ≤ 10 %, créateur ≤ 5 %, aucune arnaque passée) : **pire que sans filtre**, −9 à −30 % par trade (95 à 1 642 trades), 72 à 83 % de perdants. **F2 market cap ≥ 100 SOL à l'entrée** : un peu mieux que sans filtre mais toujours perdant, −4,6 % (K5 T20, 5 038 trades, PF 0,79) à −9,3 % ; bat les singes (z 4 à 9) sans gagner. **F3 les deux** : −7 à −29 % (90 à 226 trades). Les critères anti-arnaque évitent peut-être les arnaques, mais ne rendent pas le trading rentable. Pas de suivi papier. |
| 2026-10-18 | Backtest du dimanche en échec (« All jobs have failed ») : le calcul réussit mais le push est refusé 4 fois, le bot du quart d'heure poussant pendant chaque rejeu de ~5 min. Correctif : `MERGE_ON_REJECT=1` (workflow hebdomadaire) fusionne l'état distant et repousse sans rejouer. Testé en local sur un faux dépôt. | Fait |
| 2026-10-19 | Cassure Williams Bitcoin : annoncée deux fois (07:05 et 08:51 Paris) et pas copiée sur MT5. Causes : (1) le recalcul de 05:35 UTC ne retrouvait plus le trade (bougies Yahoo revues), il a été effacé sans sortie puis réannoncé ; correctif `Engine._keep_announced` (un trade annoncé reste ouvert, fermé à son heure prévue). (2) Vantage refuse un commentaire d'ordre ≥ 30 caractères (« lab:cassure_williams:… » = 31) ; correctif `mt5_copy.COMMENT_MAX = 26`. Donchian 1 h Bitcoin bien copié (0,1 lot). | Fait |
| 2026-10-19 | Zone de bruit Nasdaq, journée à −2,6 R pour la v1 (pas de stop dur, sortie seulement aux demi-heures). Recalcul 2014-2026 : v1 +0,21 R/trade mais 30 % des trades sous −1,5 R (pire −21 R, pire mois −53 R) ; v2 +0,11 R/trade, pire mois −22 R ; les deux ≈ 0 sans leurs 1 % meilleurs trades, positives même en ratant 20 % des trades au hasard. Choix de Yanisse : v1 en ombre (`strategies.LIVE_END`), v2 reste en réel. | Fait |
| 2026-10-19 | Demande de Yanisse : PC allumé, tout vient du PC. Étape 1 : le pont annonce lui-même sur Telegram les signaux réels qu'il calcule sur MT5 (entrée dès la copie, sortie en réponse avec le résultat MT5, `pc_relay.py`), écrit chaque minute la variable de dépôt PC_ALIVE, et GitHub se tait sur ces signaux (il tient toujours Topstep et la Simulation ; il attend 15 min si le PC vit, reprend seul si la variable a plus de 10 min, `pc_link.py`). Après chaque entrée, l'agent IA est lancé en arrière-plan (arrêté après 90 s). Inactif tant que les jetons ne sont pas dans les variables d'environnement Windows du PC. | En cours |
| 2026-10-20 | Nuit du 19 au 20/10 : vente Donchian 1 h Bitcoin (bougie de 01:00 UTC) annoncée par GitHub à 03:05 UTC alors que le PC était allumé | Sur les prix MT5, l'achat précédent touche son SL à 01:00 sans cassure dans l'autre sens : pas de vente, donc rien d'annoncé par le PC. GitHub, sur ses prix à lui, voit la vente seulement à 03:05 (données Bitcoin de secours, Binance refusé), l'annonce faute de nouvelles du PC, et le pont la copie en retard (81 962 contre 81 633). Corrigé, comme Yanisse l'a demandé (PC allumé = prix MT5 pour tous les trades réels) : le PC publie dans PC_ALIVE la liste des stratégies qu'il calcule lui-même ; pour celles-là, GitHub ne publie plus rien (ni Telegram, ni Topstep, ni Simulation) et le pont ne copie plus un signal que les prix MT5 ne donnent pas. Corrigé aussi : le marqueur « annoncé par le PC » se perdait au recalcul horaire, et GitHub aurait envoyé la sortie en double. |
| 2026-10-20 | Demande de Yanisse (19/10), étape suivante : le bot classique du Nasdaq calculé sur le PC | Le pont rejoue le scan du bot de GitHub (mêmes critères, même bot appris, mêmes sorties : stop ×1,5, objectif 3 fois le stop, 24 h au plus) sur les bougies 5 min du CFD NAS100 à chaque bougie close (`trading_bot/mt5_bot.py`). Réglages appris relus sur GitHub chaque heure ; signaux du PC gardés à part (journal/bot_pc) avec leurs propres règles de prudence et suivis jusqu'au TP, au SL ou à l'expiration. Annonce Telegram, copie démo et agent IA comme les stratégies. GitHub se tait sur le bot Nasdaq tant que le PC le calcule (même signal à 30 min près : il tient Topstep et la Simulation ; sinon rien), et reprend seul PC éteint. Écart connu : le bot appris a été entraîné sur les contrats à terme NQ, pas sur le CFD. | En cours |
| 2026-10-20 | Résumé du soir du 19/10 : « 0 TP, 0 SL » alors que 5 trades réels ont perdu | Le résumé ne comptait que le bot classique (aucun trade le 19/10) ; les trades réels des stratégies (Donchian 1 h Bitcoin ×2, Cassure Williams, zone de bruit v1 et v2 : 5 perdants, −6,06 R) n'y figuraient pas. Corrigé (`summary.lab_day`) : le résumé montre d'abord les stratégies (chaque trade annoncé avec son résultat en R et en %), puis le bot classique. | Fait |
| 2026-10-20 | Essai 32 b (à titre d'information, demande de Yanisse) : « vrai » break even sur les 8 stratégies de l'essai 32 — stop posé à l'entrée + les frais aller-retour (une sortie au BE vaut 0, pas −frais comme dans l'essai 32), déclenché à +0,5 R, +1 R, +1,5 R ou +2 R. Mêmes contrôles que l'essai 32 (écart > 0, deux moitiés, 2 dernières années, 60 % des années, seuil z corrigé sur 32 cellules). Rien ne change en réel quel que soit le résultat sans l'accord de Yanisse. `trading_bot/essai32b.py` | Résultat (32 cellules, `data/essai32b.json`) : aucune n'améliore nettement. Plus le BE est déclenché tôt, plus on perd (+0,5 R : zone de bruit +0,21 → +0,03 R, W3 Bitcoin +0,39 → −0,09 R, bot Nasdaq +0,15 → +0,06 R) ; à +2 R il ne change presque rien. Meilleurs : Cassure Williams +1,5 R (+0,003 R) et nuit asiatique (+0,001 R), rien de significatif. Le BE coupe les trades qui reviennent toucher l'entrée avant de partir loin. Rien changé en réel. |
| 2026-10-20 | Avis de l'agent IA « à l'aveugle » sur la Cassure Williams Bitcoin de 16:05 Paris | La copie MT5 était refusée (règle d'arrêt de la copie : 8 pertes d'affilée), et pour un signal non copié le pont ne connaissait pas le symbole MT5 : l'agent a reçu 0 bougie (5 min, 1 h, jour) et a jugé sans graphique. Corrigé : le symbole est noté dès que le signal est vu (`mt5_copy`), l'agent reçoit ses bougies même quand la copie est refusée. | Fait |
| 2026-10-20 | Copie des signaux sur le démo MT5 (magic 200001) arrêtée par la règle « 8 pertes d'affilée » | Choix de Yanisse : c'est un démo, la copie continue même après 8 pertes d'affilée (`demo_rules.RULES[200001]["max_streak"] = None`). La limite de perte cumulée (300 $) reste. | Fait |
| 2026-10-20 | Demande de Yanisse : l'agent IA cherche lui-même des trades sur l'or (suite des passages horaires de l'assistant, 13-20/10 : 2 trades, 2 gagnants, +15,56 $) | Le pont réveille l'agent (dépôt privé, `agent/chasse.py` sur le PC) à 9h05, 14h35, 15h35 Paris et 20 min après chaque annonce USD forte, en semaine ; il reçoit les bougies or 5 min/15 min/1 h/jour et les annonces, et répond achat/vente/rien avec SL, TP, confiance. Le pont (`mt5_hunt.py`) refuse si confiance < 3, stop du mauvais côté ou objectif < 1 R ; sinon ordre démo à 1 % du solde (magic 777002, une position à la fois, sortie SL/TP ou 4 h, arrêt à 100 $ de perte cumulée), annonce Telegram avec la raison, sortie en réponse. Démo seulement. Bilan prévu après 20 trades : résultat en R, et comparaison avec les singes (même heure, même stop/objectif). Corrigé au passage : la raison n'était pas écrite dans journal/assistant.csv (`claude_desk.order`). | En cours |
| 2026-10-20 | Choix de Yanisse (fil Agent IA) : la chasse de l'agent aussi sur le Nasdaq 100 (démo) | Réveil à 15h50 Paris (20 min après l'ouverture de Wall Street) et 20 min après chaque annonce USD forte ; mêmes garde-fous que l'or, une position par marché, lot calculé avec la valeur du point du courtier (1 % du solde au SL). Bilan séparé or / Nasdaq après 20 trades chacun. | En cours |
| 2026-10-20 | Essai 40 (demande de Yanisse) : la méthode de Hugo (TikTok @cestmoa5, ICT « BPR ») codée sur le Nasdaq 2014-2026, bougies 5 min (pas de M1/M3 sur 12 ans). Règle de base C1 : fenêtres 9h-11h et 14h30-17h Paris ; zone HTF = FVG H1 non comblé (formé dans les 48 h) touché dans les 30 dernières minutes ; Fibo : achat seulement sous le milieu de l'amplitude de la veille, vente seulement au-dessus ; déclencheur M5 = IFVG (un FVG M5 opposé de moins d'1 h clôturé à travers) ; entrée à l'ouverture suivante, stop sous/sur l'extrême des 6 dernières bougies, objectif 2 R, sortie forcée 22h Paris ; 1 trade à la fois, arrêt du jour après 2 pertes ou 1 gain (son « +600 $ »). Variantes : C2 BPR strict, C3 FVG H4, C4 sans Fibo, C5 sans zone HTF, C6 objectif 1,5 R, C7 objectif 3 R, C8 matin seul, C9 après-midi seul. Résultat en R net (frais du bot Nasdaq). Contrôles : ≥ 200 trades, > 0, 60 % des années, deux moitiés (avant/depuis 2020), 2 dernières années, frais doublés, 1000 singes (même heure, n'importe quel jour, même sens, même stop en %, même objectif, même sortie) battus ≥ 950, seuil z corrigé sur 9 cellules. Rien ne passe en réel sans l'accord de Yanisse. `trading_bot/essai40.py` | Résultat (9 cellules, `data/essai40.json`) : rien ne passe. C1 −0,04 R net (299 trades, 35 % gagnants, 4/11 années positives, singes 646/1000). BPR strict C2 +0,07 R mais 152 trades, 5/11 années, singes 847. Toutes les cellules perdent avant 2020 et gagnent depuis 2024-2025 (C1 : 39 trades, +24 R sur les 2 dernières années) : période favorable récente, pas une méthode qui tient sur 12 ans. Rien changé. |
| 2026-10-20 | Essai 40 b (demande de Yanisse) : un compte Topstep 50K neuf qui applique chaque jour les règles d'argent de la vidéo (risque 300 $ par trade en micros MNQ, objectif 2 R = +600 $, arrêt du jour après un gain ou 2 pertes) sur les trades des cellules C1 et C2 de l'essai 40. Un compte neuf est ouvert chaque jour de bourse ; règles Topstep du bot (objectif 3 000 $, perte max 2 000 $ suiveuse en fin de journée, limite du jour 1 000 $, 50 micros max, cohérence 50 %), frais TopstepX + 1 tick de glissement. Mesure : % de comptes qui réussissent, qui sautent, et jours de trading pour réussir ; sur 2014-2026 et depuis 2020. Information seulement. `trading_bot/essai40.py --topstep` | Résultat (`data/essai40b.json`) : C1 réussit 21 % des comptes (37 % depuis 2020), C2 BPR strict 43 % (93 % depuis 2020, mais 152 trades en 12 ans, comptes ouverts des jours voisins = presque les mêmes trades). Les deux codées ne trouvent qu'environ 12 à 23 trades par an : il faut ~20 jours de trading avec un trade pour réussir, soit ~10 mois (C1) à ~1,5 an (C2) d'abonnement. Information seulement, rien changé. |
| 2026-10-20 | Choix de Yanisse (carte « Les deux ») : l'agent IA applique la méthode Hugo sur le Nasdaq démo, à la place du code strict de l'essai 40 (zones choisies « à l'œil » par Claude) | `trading_bot/hugo.py` (consigne de la méthode, réutilise l'appel Claude de l'agent sur le PC) + `trading_bot/mt5_hugo.py` (pont) : réveils 9h, 10h, 14h30, 15h45, 16h30 Paris en semaine, et commande Telegram /hugo (PC allumé, réponse même sans trade, avec la zone à surveiller). Garde-fous de la chasse (démo seul, confiance ≥ 3, objectif ≥ 1,5 R côté agent, 1 % du solde, sortie SL/TP/4 h), numéro magique 777003, arrêt 100 $ (demo_rules), règle de la vidéo : arrêt du jour après un gain ou 2 pertes. Compte Topstep 50K virtuel (300 $ de risque par trade) affiché à chaque sortie. Bilan après 20 trades, contre les singes. | En cours |
| 2026-10-21 | Essai 41 (demande de Yanisse) : peut-on trader le Nasdaq le matin, avant Wall Street ? Nasdaq 2014-2026, bougies 5 min, heures de Paris, toutes sorties au plus tard à 15h00 Paris (avant l'ouverture de 15h30). Cellules : M1 bot classique rejoué avec la plage 6h-13h UTC au lieu de 13h-20h ; M2 cassure du range de la nuit (1h-8h) entre 8h et 13h, stop au milieu du range ; M3 cassure de la première demi-heure de Francfort (9h-9h30), stop de l'autre côté ; M4 suite du mouvement de la nuit (22h veille → 9h), entrée 9h ; M5 contre ce mouvement ; M6 contre la première demi-heure de Francfort, entrée 9h30 ; M7 sens de la matinée (9h → 14h) tenu de 14h à 15h25. Stop de sécurité 0,5 % pour M4-M7. Mêmes contrôles que l'essai 24 (≥ 200 trades, R > 0 et PF ≥ 1,1, 60 % des années, deux moitiés, 2 dernières années, frais doublés, 2 régimes sur 3, 1000 singes ≥ 950, seuil z corrigé sur 7 cellules). Rien ne passe en réel sans l'accord de Yanisse. `trading_bot/essai41.py` | Résultat (`data/essai41.json`) : rien ne passe. Bot classique le matin −0,07 R (3 576 trades, PF 0,84, 3/12 années, singes 675). Meilleure : M3 cassure de Francfort +0,02 R (PF 1,03, 7/12 années, perd avant 2020, singes 924). Le reste ≈ 0 ou négatif. Le Nasdaq le matin ne donne rien de mécanique : on garde 15h-22h. Rien changé. |
| 2026-10-21 | Essai 42 (point 1 de la relecture Perplexity, accord de Yanisse) : le backtest du bot classique rejoue enfin comme en réel. Corrections de `backtest.run_backtest` : (a) chaque signal est suivi jusqu'à sa vraie expiration (24 h et stop ×1,5 / objectif 3 sur le Nasdaq depuis l'essai 29, 1 h ou 3 h ailleurs) au lieu de 12 bougies ; (b) un signal n'a de statut (stop, objectif) qu'une fois clos : tant qu'il est ouvert il bloque un nouveau signal ; refroidissement après un stop compté depuis sa clôture, pas de nouveau signal dans le même sens après un stop (comme `engine._policy_block` et `_direction_block`). Le stop reste compté au prix exact (point 2, essai à part). Nasdaq 2014-2026, années cachées 2017-2026. Cellules : N0 ancien rejeu (essai 23, sortie 1 h) brut, référence ; N1 nouveau rejeu brut ; N2 nouveau rejeu filtré par le modèle « groupe indices » appris sur les anciennes lignes (ce qui tourne en réel aujourd'hui), en walk-forward annuel ; N3 nouveau rejeu filtré par un modèle appris sur les nouvelles lignes Nasdaq (walk-forward). Contrôles de l'essai 26 (≥ 200 trades, R > 0 et PF ≥ 1,1, 60 % des années, deux moitiés, 2 dernières années, frais doublés, 2 régimes sur 3, singes ≥ 950, filtres au hasard ≥ 950, seuil z corrigé sur 4 cellules). Si N2 échoue, le filtre actuel du Nasdaq n'est plus justifié : carte à Yanisse, rien changé sans son accord. `trading_bot/essai42.py` | Résultat (`data/essai42.json`, 2017-2026) : N0 ancien rejeu +0,01 R (4 458 trades, 37 min en moyenne), pas robuste. N1 nouveau rejeu brut +0,12 R (2 309 trades, 230 min, PF 1,17, 8/8 années, singes 1000, z 6,75) : prouvé. N2 filtre actuel +0,22 R (672 trades, garde 29 %, PF 1,34, 7/8 années, filtres au hasard 972, z 1,97 < 2,24) : robuste, non prouvé. N3 filtre réappris +0,15 R, filtres au hasard 924 : pas robuste. Le bot Nasdaq tient avec les vraies sorties ; le filtre actuel reste robuste mais n'est pas prouvé meilleur qu'un tri au hasard. Réserve : stop encore compté au prix exact (point 2), plus optimiste sur des trades tenus la nuit. Carte posée à Yanisse, rien changé. |
| 2026-10-21 | Essai 42 b (point 2 de la relecture Perplexity) : un stop ou un objectif sauté par un trou de prix est exécuté à l'ouverture de la bougie (et plus au niveau exact), dans `tracker.resolve_with_candles` (suivi réel et backtest), comme `strategies.simulate`. On refait exactement l'essai 42 (mêmes cellules N0-N3, mêmes contrôles) sur un nouveau rejeu Nasdaq. Si N1 ou N2 tombe sous les seuils, le résultat de l'essai 42 ne tient pas. `python -m trading_bot.essai42 b` | Résultat (`data/essai42b.json`) : presque rien ne bouge. N1 +0,118 R prouvé, N2 filtre actuel +0,22 R robuste (filtres au hasard 968), N3 filtre réappris +0,17 R robuste (985). Le résultat de l'essai 42 tient avec le stop au vrai prix. |
| 2026-10-21 | Essai 43 (demande de Yanisse) : le bot classique tenu plus longtemps que 1 h, sur Nasdaq, or, S&P 500, Bitcoin, pétrole, euro, 2014-2026. Entrées du bot calculées une fois (analyse toutes les 15 min dans sa plage horaire), puis rejeu comme en réel pour chaque sortie (un seul signal ouvert, règles du jour, refroidissement depuis la clôture, niveau sauté exécuté à l'ouverture). Sorties : V0 sorties du bot, 1 h (référence) ; V1 sorties du bot jusqu'à la fermeture Topstep (22h10 Paris, pas d'entrée après 22h10 ni le week-end) ; V2 sorties du bot, 24 h (MT5) ; V3 stop ×1,5 objectif 3, fermeture Topstep ; V4 stop ×1,5 objectif 3, 24 h. Frais du bot (Topstep pour les futures). Contrôles de l'essai 24 (≥ 200 trades, R > 0 et PF ≥ 1,1, 60 % des années, deux moitiés, 2 dernières années, frais doublés, 2 régimes sur 3, singes ≥ 950), seuil z corrigé sur 30 cellules. Réserve : les frais de nuit (swap) du MT5 ne sont pas comptés (compte sans swap prévu). Rien en réel sans l'accord de Yanisse. `trading_bot/essai43.py` | Résultat (`data/essai43.json`, seuil z 2,94) : une seule cellule prouvée, Nasdaq V4 stop ×1,5 objectif 3 tenu 24 h : +0,087 R, 2 953 trades, PF 1,12, 11/12 années, singes 999, z 3,74 (c'est la sortie actuelle du Nasdaq). La même chose fermée à 22h10 (Topstep) : +0,03 R, pas robuste, donc le gain vient des trades tenus la nuit, impossible sur Topstep. Garder les sorties du bot plus longtemps (V1, V2) ne change rien nulle part. Or, S&P 500, Bitcoin, pétrole, euro : négatifs dans toutes les sorties (meilleure : Bitcoin V3 −0,05 R). Rien changé. |
| 2026-10-22 | Choix de Yanisse après l'essai 43 : le compte Topstep simulé ferme à 15:08 heure de Chicago (statut « Fermé 15:08 », prix de la dernière bougie 5 min finie) tout signal encore ouvert à 15:10, puisque le Nasdaq du bot est tenu jusqu'à 24 h ; la Simulation et la copie MT5 continuent de le tenir. `topstep.TopstepAccount.compute(price_at=…)`, `Engine._price_at` | Fait |
| 2026-10-22 | Point 4 de la relecture Perplexity (accord de Yanisse) : `learning.trade_r` n'apprend plus le meilleur entre la sortie du bot et une sortie à la main en gain ; seul le résultat du bot seul compte. Les statistiques d'apprentissage peuvent baisser un peu sur les signaux arrêtés à la main. | Fait |
| 2026-10-22 | Essai 44 (point 3 de la relecture Perplexity, accord de Yanisse) : le bot Nasdaq sur les bougies MT5 (CFD NAS100 Vantage) contre les bougies futures qu'il a apprises, sur la période commune la plus longue dispo dans MT5. Backtest corrigé de l'essai 42, même réglage. Mesures : part des signaux futures retrouvés sur MT5 (même sens, à moins de 15 min), même avis du filtre modèle, même issue (gain ou perte), écart de prix médian, R moyen avec et sans filtre de chaque côté. Information seulement : si moins de 70 % des signaux se retrouvent, ou si le filtre change d'avis sur plus d'un signal sur quatre, le modèle n'est pas fiable sur MT5 (carte à Yanisse). `trading_bot/essai44.py` (lancé sur le PC) | Résultat (30/05/2025 → 04/10/2026, journal du PC) : seuls 34 % des signaux futures se retrouvent sur MT5 (110 sur 324), sous le seuil de 70 %. Le bot fait pourtant pareil en moyenne : futures +0,12 R (324 signaux), MT5 +0,13 R (313). Sur les signaux communs, le filtre donne le même avis 86 % du temps et l'issue est la même 86 % du temps ; écart de prix médian +23,75 points. Filtre : futures garde 87 signaux à +0,56 R, MT5 garde 74 signaux à +0,32 R. Le bot vit aussi sur MT5, mais signal par signal ce ne sont pas les mêmes trades (petites différences de prix + un seul signal ouvert à la fois = décalage en cascade). Carte posée à Yanisse avec le choix du filtre. |
| 2026-10-22 | Choix de Yanisse (carte après les essais 42, 42 b et 44) : le bot Nasdaq garde son filtre actuel (modèle « groupe indices » de l'essai 26). Rien ne change. | Fait |
| 2026-10-22 | Essai 45 (demande de Yanisse) : sortir à un gain fixe (+0,5 R, +1 R, +1,5 R, +2 R ; +100 $ ≈ +2 R avec 5 % de risque sur le démo) au lieu de la sortie actuelle, sur les stratégies en réel (cassure Williams, Donchian 1 h, W3 Bitcoin, zone de bruit v2 Nasdaq, nuit asiatique or, bot Nasdaq), 2014-2026. Mêmes entrées, stop et sortie d'origine ; comparaison trade par trade, contrôles de l'essai 32 (écart > 0, deux moitiés, 2 dernières années, 60 % des années, variante > 0), seuil z corrigé sur 24 cellules. Rien en réel sans l'accord de Yanisse. `trading_bot/essai45.py` | Résultat (`data/essai45.json`) : 0 cellule sur 24 ne fait mieux. Un gain fixe coupe les gros gagnants partout : cassure Williams +0,22 → +0,03 à +0,13 R, Donchian 1 h +0,15 → −0,03 à +0,02 R, W3 +0,39 → −0,12 à −0,04 R, zone de bruit v2 +0,11 → 0 à +0,06 R, bot Nasdaq +0,15 → −0,01 à +0,11 R ; nuit asiatique inchangée (≈ +0,03 R). Même +2 R (≈ +100 $) fait perdre de 0,04 à 0,42 R par trade. On garde les sorties actuelles. Ne pas reproposer de gain fixe. |
| 2026-10-22 | Essai 46 (demande de Yanisse, vidéo TikTok « robot HFT » sur l'or) : la grille rejouée sur l'or 2014-2026 (bougies 5 min). Un panier d'achats et un de ventes en même temps, une position de plus tous les 3 $ contre le panier, sans stop, panier fermé en entier à +1 $ au-delà de son prix moyen. Compte 1 000 $, levier 1:500, coupure à 50 % de marge, frais 0,30 $ par once. Variantes : G1 lots fixes 0,05 ; G2 lots ×1,5 à chaque palier. Départ le premier lundi de chaque mois, suivi 6 mois au plus. Mesures : part des comptes qui sautent (en 7 j, 30 j, médiane), part qui atteint −300 $, résultat moyen et médian. Hypothèse : la grille saute dans la majorité des départs et perd en moyenne. Information seulement ; ensuite une version démo (magic à part, arrêt à −300 $) si Yanisse veut toujours la voir tourner. `trading_bot/essai46.py` | Résultat (`data/essai46.json`, 152 départs) : G1 lots fixes, le compte saute dans 99 % des départs (46 % en 7 jours, 86 % en 30 jours, médiane 7,7 jours), −300 $ atteint en 2,1 jours (médiane), résultat médian −921 $. G2 martingale : sauté 99 % (78 % en 7 jours, médiane 1,5 jour), médian −828 $. Le seul survivant de G2 (départ avril 2020) gonfle la moyenne : à ignorer, d'autant que le parcours des bougies 5 min est plutôt favorable à une grille. La grille ne vit pas. |
| 2026-10-22 | Choix de Yanisse : la copie démo des signaux (magic 200001) n'a plus de limite de perte (elle s'était arrêtée à −389,73 $ depuis le 14/10, limite 300 $) ; elle tourne comme le futur compte réel, 5 % de risque gardé. Démo seulement. `demo_rules.RULES[200001]` | Fait |
| 2026-10-22 | Demande de Yanisse : la chasse de l'agent IA (magic 777002) cherche 2 à 3 fois par heure. En plus des heures fixes et des annonces, réveil toutes les 20 min (réglable : `every_minutes` dans la config du pont, 0 = arrêt) : or 9h-12h et 14h30-18h Paris, Nasdaq 15h40-21h Paris, soit environ 21 réveils or et 16 Nasdaq par jour. Mêmes garde-fous (confiance ≥ 3, 1 % du solde, un trade à la fois, arrêt 100 $). Chaque réveil est un appel Claude sur l'abonnement de Yanisse. Méthode Hugo inchangée. `mt5_hunt.WATCH`, `slots(watch=, every=)` | Fait |
| 2026-10-23 | Choix de Yanisse (carte) : l'agent IA de la chasse (magic 777002) peut aussi proposer un ordre limite (« achat_limite » / « vente_limite » avec un prix d'attente). Le pont pose l'ordre limite sur le démo, l'annule s'il n'est pas touché en 2 h, et n'éveille pas l'agent sur ce marché pendant l'attente ; les 4 h de tenue comptent depuis l'exécution. Mêmes garde-fous (confiance ≥ 3, stop et objectif ≥ 1 R autour du prix d'attente, 1 % du solde). Telegram : annonce « ACHAT/VENTE LIMITE », puis « exécuté » ou « annulé » en réponse. Méthode Hugo inchangée. `mt5_hunt.PENDING_MAX`, `Hunter._pending` | Fait |
| 2026-10-23 | Demande de Yanisse : copier sur le démo MT5 les trades d'un canal Telegram de signaleur (d'abord BENAGOLD, or). Le compte Telegram de Yanisse écoute le canal sur son PC (`tg_listen.py`, Telethon, clés tapées par lui en variables Windows) ; le pont lit le format fixe du canal sans Claude (« SELL GOLD / Prix d'entrée : zone / Stop Loss / Take Profit 1-3 ») et « sécurisez » = stop au prix d'entrée ; tout autre message est ignoré. Un ordre par objectif (3 au plus), 1 % du solde visé, jusqu'à 3 % au lot minimum pour garder les 3 objectifs ; zone déjà quittée de plus d'un quart du stop : ordre limite au bord de la zone, annulé après 2 h ; fermeture au bout de 24 h ; jamais sans stop ; magic 300001, pas de limite de perte (comme la copie du bot). Démo seulement. `mt5_tgcopy.py`, `tg_parse.py` (Claude, pour un canal au format libre, désactivé par défaut) | Fait |
| 2026-10-23 | Demande de Yanisse (idée du « Time Machine » d'une vidéo TikTok @dan.ai.lab) : chaque trade de l'agent IA (chasse et méthode Hugo) affiche ce que le passé dit de sa forme. Tableau calculé une fois (`trading_bot/hit_table.py` → `data/hit_table.json`) : or et Nasdaq 2014-2026, entrée à chaque demi-heure de Paris, achat et vente, stop de 0,5 à 6 ATR (14 bougies 5 min), objectif 1 à 3 fois le stop, 4 h : part TP d'abord / SL d'abord (même bougie = SL). Information seulement (Telegram, journal), pas un filtre, aucun retard ni appel Claude. Constat au calcul : partout proche du hasard (or 15h30, achat, stop 2 ATR, 2 R : TP d'abord 23 %, SL d'abord 56 %), donc ce qui compte reste l'idée de l'agent. | Fait |
| 2026-10-23 | Demande de Yanisse : la méthode Hugo (magic 777003, Nasdaq démo) se réveille plus souvent. En plus des 5 heures fixes de la vidéo, veille toutes les `every_minutes` (20 min par défaut, réglage commun avec la chasse) de 9h à 17h Paris en semaine. Règles de journée inchangées (arrêt après 1 gain ou 2 pertes). Environ 20 appels Claude de plus par jour sur l'abonnement. `mt5_hugo.HugoHunter.WATCH` | Fait |
| 2026-10-23 | Demande de Yanisse : remettre le compte Topstep à zéro en gardant l'historique. Le bouton « Archiver et repartir à 50 000 $ » (Journal et réglages, ou /topstep reset) garde maintenant le compte entier (trades, journées, trades encore ouverts) dans data/topstep/history/<n>.json et docs/topstep/history/<n>.json, et la page montre une section « Comptes précédents » avec les trades de chaque compte archivé. Les 2 comptes archivés avant n'ont que leur résumé. `TopstepAccount.reset` | Fait |
| 2026-10-23 | Demande de Yanisse : l'agent IA donne aussi son avis sur les trades copiés d'un canal Telegram (magic 300001), en réponse à l'annonce, comme pour les signaux du bot (même lancement en arrière-plan, `pc_relay.Relay._agent`, stratégie « copie_telegram », objectif = TP1). `TgCopier._review` | Fait |
| 2026-10-24 | **Essai 47** (pré-enregistré, vidéo TikTok @thequantbuilder « Session Momentum », annoncée +508 % sur 6 ans, 1 448 trades) : Nasdaq 5 min 2014-2026 (data/history/long/nasdaq_5m.json, contrats à terme). Chaque jour de bourse, 1re bougie 5 min de New York (9:30-9:35 heure de New York) : clôture au-dessus de la moyenne exponentielle 12 bougies 5 min → achat à la clôture, en dessous → vente. Stop initial = l'autre extrémité de la 1re bougie. Variantes : **A** stop suiveur sur la moyenne 12 (sortie à la 1re clôture de l'autre côté), **B** sans suiveur, **C** objectif 2 R ; toutes fermées à 16:00 New York au plus. Frais 1,25 point par trade. Retenu seulement si moyenne > 0 R après frais sur 2014-2019 ET 2020-2026, et meilleur que le même trade dans un sens tiré au hasard (1 000 tirages, mieux que 95 %). `trading_bot/essai47.py` (1re bougie de moins de 2 points écartée : données creuses ; singes = mêmes jours, mêmes règles, sens au hasard, 500 tirages) | **Rien ne passe** (données 02/01/2014 → 20/09/2024, 2 575 trades). A suiveur −0,03 R (2014-2019 −0,03, 2020+ −0,02 ; 29 % de gagnants ; −0,36 R sans les 5 % meilleurs), B sans suiveur +0,02 R mais 2014-2019 −0,02 (2020+ +0,07 ; médiane −1,06 R), C objectif 2 R −0,09 R. Le sens de la bougie bat bien les singes (A −0,03 contre −0,12 au hasard) : il y a un petit élan, mais il est mangé par les frais et les stops serrés. Loin des +508 % annoncés. `data/essai47.json` |
| 2026-10-24 | **Essai 48** (pré-enregistré, demande de Yanisse, vidéo TikTok @_trading_elite_ « tasse avec anse ») : or, Nasdaq, Bitcoin, bougies 30 min (5 min regroupées), 2014-2024 (Bitcoin depuis 2017). Règles fixes : bord gauche = sommet le plus haut de ±5 bougies ; tasse de 20 à 150 bougies, profondeur D ≥ 4 ATR(14), creux dans le tiers central (forme arrondie) ; bord droit = sommet ±5 bougies à moins de 15 % de D du bord gauche ; anse de 3 à 30 bougies après le bord droit, repli entre 10 % et 50 % de D ; résistance = le plus haut des deux bords. Achat à la 1re clôture au-dessus de la résistance (au plus 30 bougies après le bord droit). Stop = plus bas de l'anse, objectif = entrée + D (« 100 % »), fermeture au bout de 5 jours au plus. Achat seulement. Frais : Nasdaq 1,25 pt, or 0,35 $, Bitcoin 0,1 %. Singes : même stop, même objectif, même durée, à la même heure un autre jour tiré au hasard (500 tirages). Retenu seulement si > 0 R sur 2014-2019 ET 2020+, au moins 100 trades, et mieux que 95 % des singes. `trading_bot/essai48.py` | **Rien ne passe** (données jusqu'en septembre 2024). Or : 95 tasses, +0,06 R (2014-2019 +0,07, 2020+ +0,04), objectif touché 34 %, singes −0,01 R mais battus seulement 69 % des fois, moins de 100 trades. Nasdaq : 108, +0,18 R mais 2020+ −0,11 R ; des achats au hasard à la même heure font déjà +0,10 R (le Nasdaq monte), battus 71 % des fois. Bitcoin : 113, −0,36 R, pire que les singes (−0,02). Sur 11 ans, la figure n'apparaît qu'une dizaine de fois par an et par marché. `data/essai48.json` |
| 2026-10-24 | **Essai 49** (pré-enregistré, demande de Yanisse, vidéo TikTok @arlo.fx « liquidity sweep » or, 5 règles) : or 5 min 2014-2024. Veille = séance 18:00 → 17:00 New York, plus haut PDH et plus bas PDL. Fenêtre : 08:00 Londres → 12:00 New York, un seul trade par jour (1er balayage). Balayage du haut = bougie 5 min dont le haut dépasse PDH et qui clôture en dessous ; une clôture au-dessus de PDH avant tout balayage = cassure, ce côté est abandonné pour la journée (idem en miroir pour PDL). Confirmation 5 min : clôture sous le plus bas des 6 bougies précédant le balayage, dans l'heure (12 bougies), sinon abandon ; si le prix repasse au-dessus de la mèche avant, abandon. Entrée à cette clôture, vente après un balayage du haut, achat après un balayage du bas. Stop = mèche du balayage + 0,25 ATR(14) « de la marge ». Objectif (non donné par la vidéo) : **A** 2 R, **B** l'autre extrême de la veille (PDL pour une vente), au moins 1 R. Fermeture à 17:00 New York au plus. Frais 0,35 $. Singes : même heure, autre jour au hasard, sens au hasard, mêmes distances (500 tirages). Retenu si > 0 R sur 2014-2019 ET 2020+, ≥ 100 trades, mieux que 95 % des singes. `trading_bot/essai49.py` | **Rien ne passe** (79 trades seulement en 11 ans) : A (2 R) +0,019 R (2014-2019 +0,012, 2020+ +0,024, 52 % gagnants, années tantôt + tantôt −), bat 76 % des singes ; B (autre extrême) −0,039 R (2020+ −0,071), bat 60 % des singes. Trop rare et pas mieux que le hasard. Rien changé sur le bot. |
| 2026-10-26 | **Essai 50** (pré-enregistré, demande de Yanisse) : zone de bruit Nasdaq 2014-2026, mêmes bougies et frais que l'essai 24, singes de l'essai 21. B = `noise_area_v2` en réel (référence). **E1** entrée dès qu'une bougie 5 min clôture hors zone (10:00-15:30), sortie comme B. **E2** entrée et sortie (sous max(borne, VWAP)) à chaque bougie 5 min, stop dur gardé. **S1** entrée aux demi-heures, stop = bord de la zone qui se déplace à chaque bougie (touché en cours de bougie), sans VWAP ni stop dur. **S2** = E1 + stop sur le bord. R = risque de B pour toutes. Retenue si mieux que B en R, > 0 sur 2014-2019 ET 2020+, ≥ 200 trades, bat 95 % des singes. `trading_bot/essai50.py` | **Rien ne bat B.** B 2 912 trades +0,111 R (2014-2019 +0,063, 2020+ +0,160 ; identique à l'essai 24). E1 4 182 +0,073 R (2014-2019 +0,012). E2 6 414 +0,007 R (2014-2019 −0,039). S1 3 637 +0,060 R (24 % gagnants). S2 7 745 +0,012 R (2014-2019 −0,022). Toutes battent les singes mais font moins que B : la règle des demi-heures et la sortie sous max(borne, VWAP) restent. Rien changé. |
| 2026-10-26 | **Essai 51** (pré-enregistré, idée de Yanisse : gagner plus souvent) : zone de bruit v2 Nasdaq 2014-2026, règles de B (essai 50) gardées, plus : dès que le trade atteint +X R, stop au bord de la zone moins une marge (en ATR 15 min), déplacé à chaque bougie, jamais sous le stop fixe. **M1** +1 R / marge 0,5 ; **M2** +0,5 R / 0,25 ; **M3** +1 R / 1 ; **M4** +0,5 R / 0,5. On regarde aussi le % de gagnants. Retenue si R ≥ B − 0,01, % de gagnants plus haut, > 0 sur 2014-2019 ET 2020+, bat 95 % des singes. `trading_bot/essai51.py` | **Rien ne passe** (le % de gagnants ne monte pas). B 2 912 trades +0,111 R, 35,1 % gagnants. M1 +0,109 R 35,0 % ; M2 +0,104 R 33,2 % ; M3 +0,109 R 34,8 % ; M4 +0,112 R 34,0 %. Le stop au bord change très peu : la sortie aux demi-heures sous max(borne, VWAP) fait déjà presque le même travail. Rien changé. |
| 2026-10-26 | **Essai 52** (pré-enregistré, demande de Yanisse : stratégies à fort % de réussite) : retour à la moyenne sur Nasdaq, S&P 500, or, Bitcoin 2014-2026. Achats au-dessus de la moyenne 200 j, entrée à la clôture du jour, stop 2 ATR jour, 10 j max : **R1** RSI(2) < 10 → sortie au-dessus de la moyenne 5 j (Connors) ; **R2** IBS < 0,2 → sortie le lendemain ; **R3** Double 7 ; **R4** 3 baisses d'affilée → 1re hausse. **R5** (Nasdaq, S&P, 5 min) : clôture à > 2 écarts-types du VWAP (10:00-15:00) → trade inverse, objectif VWAP, stop 1 ATR 15 min, fin 15:55. Frais et singes de l'essai 21 (même sens, même durée, autre jour). Retenue si ≥ 60 % de gagnants, > 0 R sur 2014-2019 ET 2020+, ≥ 150 trades, bat 95 % des singes. `trading_bot/essai52.py` | **Une seule passe, de justesse : R3 « Double 7 » Nasdaq** (162 trades, +0,208 R, 64,8 % gagnants, 2014-2019 +0,241, 2020+ +0,182, bat 963 singes sur 1000, z 2,0 ; non significatif une fois corrigé des 18 cellules). Taux de réussite élevés partout (55-73 %) mais pas d'avantage sur des achats au hasard de même durée : R1 Nasdaq 64 % +0,07 R (712), R4 S&P 70 % +0,085 R (894, 110 trades), R4 Bitcoin 73 % +0,086 R (862, 82 trades), R3 or 63 % mais singes mieux. R5 (VWAP ± 2 écarts-types, 5 min) perd : Nasdaq −0,11 R, S&P −0,17 R, 36 % gagnants. Proposé à Yanisse : R3 Nasdaq en ombre. |
| 2026-10-26 | Choix de Yanisse après l'essai 52 (« il n'y a qu'un trade par mois, on va le faire en réel ») : **Double 7 Nasdaq en signaux réels** (Telegram, copie démo MT5) et en ombre depuis le 26/10 12:00 UTC (`strategies.double7`, LIVE/SHADOW, OVERNIGHT 15 j). GitHub calcule sur bougies 1 h Yahoo sur 2 ans (`DAILY_1H`), le PC sur 300 jours de bougies 5 min MT5. Pas de passage préalable en ombre, contraire à la proposition. Le bot ne passe aucun ordre réel. | Fait |
| 2026-10-26 | Choix de Yanisse (fil BENAGOLD) : copie du canal, fermetures plus précises. Lecture des 48 messages « clôture » du canal : « Close now », « on clôture (toute) la position », « fermer la position », « Clôture !! +N PIPS » ferment tout ; « Clôture partielle » / « clôture une partie » ferme un seul ordre (TP le plus proche) ; témoignages (« belle clôture », « j'ai clôturé mon … », « clôtures ») ignorés. Avant : tout « clôtur… » fermait tout. `mt5_tgcopy.PARTIAL/CLOSE` | Fait |
| 2026-10-26 | **Essai 53** (pré-enregistré, demande de Yanisse : « peut-on établir la stratégie de BENAGOLD d'après ses trades ? »). Étape 1 faite avant (description de ses 178 signaux 31/03-26/10/2026 sur l'or MT5, script `journal\tg_retro.py` sur le PC) : ses repères nets contre des moments au hasard (même heure, même sens) sont **contre le mouvement de la dernière heure** (75 % contre 48 %) et **à ≤ 3 $ de l'extrême de la dernière heure côté stop** (47 % contre 19 %) ; pas d'OTE (11 % contre 7 %), pas de chiffre rond, pas de balayage. Mouvement médian de l'heure contre le trade 7 $ (≈ 0,18 %), distance médiane à l'extrême 3,6 $ (≈ 0,09 %), stop médian 9,8 $ (≈ 0,25 %), TP médians 1 / 2,1 / 3,6 fois le stop, 80 % des signaux entre 10h et 16h30 Paris. Règles codées (or 5 min 2014-2024, données jamais vues par ces règles) : chaque clôture 5 min de 10:00 à 17:00 Paris en semaine, **vente** si la clôture a monté d'au moins 0,15 % depuis l'ouverture d'il y a 60 min ET est à moins de 0,08 % du plus haut de ces 60 min (achat en miroir) ; entrée à la clôture, stop 0,25 % du prix, 3 parts égales avec objectifs 1 R, 2 R et 3,5 R, fermeture au bout de 24 h ; un trade à la fois, 2 par jour au plus. **F1** ces règles ; **F2** F1 + stop à l'entrée dès que l'objectif 1 est touché (son « Sécurisez ») ; **F3** F1 seulement dans le sens de la moyenne 20 bougies 4 h (vente sous la moyenne) ; **F4** F1 de 14:00 à 17:00 Paris seulement. Frais 0,35 $/once. Contrôles : ≥ 200 trades, > 0 R sur 2014-2019 ET 2020+, ≥ 60 % des années > 0, > 0 avec frais doublés, bat 95 % de 500 singes (même heure, autre jour, sens au hasard, mêmes distances), seuil z corrigé sur 4 cellules. Rien en réel sans l'accord de Yanisse. `trading_bot/essai53.py` (200 singes au lieu de 500, pour le temps de calcul) | **Rien ne passe** (or 5 min 2014 → 09/2024, `data/essai53.json`). F1 4 284 trades −0,085 R (36 % gagnants, 1/11 années > 0, bat 70 % des singes qui font −0,095 R) ; F2 avec « Sécurisez » −0,087 R mais 49 % gagnants ; F3 sens de la moyenne 4 h −0,072 R (3 019) ; F4 après-midi −0,074 R (3 776). Avant frais ≈ 0 : vendre après une heure de hausse près du plus haut (et l'inverse) ne fait pas mieux que le hasard. Sur ses propres signaux 2026 rejoués (1 min/5 min MT5, « Sécurisez » et fermetures du canal) : 177 joués, +0,09 R, 38 % gagnants, +825 $ à 0,02 lot ; ce qui marche chez lui ne vient pas d'une règle codable vue dans les prix (signaux avec « Sécurisez » +0,49 R contre −0,35 R sans, mais il l'envoie quand le trade va déjà bien). Rien changé. |
| 2026-10-26 | **Essai 54** (pré-enregistré, demande de Yanisse : nouvelles stratégies pour le bot ; idées connues des études, jamais testées chez nous) : Nasdaq et S&P 500, bougies 5 min 2014-2026 (celles de l'essai 52), achats seulement, frais et singes de l'essai 21 (même heure, autre jour, même sens, même durée). **O1 la nuit** : achat à la clôture de 16:00 New York, vente à l'ouverture de 9:30 de la séance suivante (week-end compris), stop de sécurité 1 %. **M1 fin de mois** : achat à la clôture de l'avant-dernier jour de bourse du mois, vente à la clôture du 3e jour de bourse du mois suivant, stop 2 ATR 14 jours. **F1 veille de la Fed** : achat à 14:00 New York la veille d'une décision de la Fed, vente à 13:55 le jour de la décision, stop 1 % (dates 2014-2024 du fichier des annonces, 2025-2026 calendrier officiel). R = gain ÷ risque au stop ; aussi en % du prix. Retenue si > 0 R sur 2014-2019 ET 2020+, ≥ 150 trades (F1 n'en a qu'environ 100 : pour information), > 0 avec frais doublés, bat 95 % des singes. Rien en réel sans l'accord de Yanisse. `trading_bot/essai54.py` | **Rien ne passe** (`data/essai54.json`). O1 la nuit : Nasdaq +0,019 R (2 928 trades, 54 % gagnants, +0,019 % par nuit) mais des achats au hasard à la même heure font autant (+0,020 R, battus 483/1000) ; S&P +0,011 R, battus 742. M1 fin de mois : Nasdaq +0,06 R (152, 7/13 années, singes 606), S&P ≈ 0. F1 veille de la Fed : Nasdaq +0,13 R et S&P +0,11 R (94-95 trades, 11/13 années sur le S&P) mais ≈ 0 avant 2020 et singes 773-822 : trop peu de trades et pas mieux que le hasard. Ces effets connus existent un peu (le marché monte), mais rien de plus qu'acheter à n'importe quel moment. Rien changé. |
| 2026-10-26 | **Essai 55** (pré-enregistré, demande de Yanisse : améliorer les stratégies actuelles et la durée du bot classique) : 2014-2026, mêmes bougies, frais et contrôles que les essais 24 et 43. **Z1** zone de bruit v2 Nasdaq gardée seulement les jours « agités » : amplitude moyenne des 14 jours d'avant (en % du prix) au-dessus de sa médiane des 250 jours d'avant ; **Z2** le contraire (pour information). **W1** cassure Williams Bitcoin gardée seulement si la clôture de la veille est au-dessus de la moyenne 100 jours ; **W2** moyenne 50 jours. Un filtre est retenu si : R des trades gardés > R de la stratégie, mieux sur 2014-2019 ET 2020+, ≥ 200 trades gardés, et mieux que 950 filtres au hasard sur 1000 qui gardent la même part. **N4 / N8 / N12** bot classique Nasdaq (stop ×1,5, objectif 3, sans le filtre modèle, rejeu de l'essai 43) tenu 4 h, 8 h, 12 h au lieu de 24 h ; retenu si les 10 contrôles de l'essai 24 passent et R ≥ celui de 24 h (+0,087 R). Rien en réel sans l'accord de Yanisse. `trading_bot/essai55.py` | **Rien ne passe** (`data/essai55.json`). Z1 zone de bruit les jours agités : 1 316 trades sur 2 717, +0,159 R contre +0,112 R, mieux sur 2014-2019 (+0,13 contre +0,06) et 2020+ (+0,18 contre +0,16), mais ne bat que 896 filtres au hasard sur 1000 (seuil 950) : piste à suivre, pas prouvée. Z2 jours calmes +0,07 R. W1 Williams au-dessus de la moyenne 100 j +0,24 R contre +0,22 R (674 trades, hasard 713) ; W2 moyenne 50 j +0,27 R contre +0,22 R (700, hasard 868) : pas prouvé. Bot Nasdaq tenu plus court : N4 +0,034 R, N8 +0,055 R, N12 +0,068 R, contre +0,087 R à 24 h : plus court = moins bien, on garde 24 h. Rien changé. |
| 2026-10-26 | **Essai 56** (pré-enregistré, demande de Yanisse, idée de l'étude d'origine de la zone de bruit : taille adaptée à l'agitation) : zone de bruit v2 Nasdaq et Double 7 Nasdaq, 2014-2026, mêmes trades et frais que les essais 55 et 52. Agitation = amplitude moyenne des 14 jours d'avant (% du prix) ; repère = sa médiane des 250 jours d'avant. **T0** risque fixe 1 % par trade (référence). **T1** risque 1 % × repère / agitation (plus petit quand ça bouge), borné entre 0,5 % et 2 %. **T2** l'inverse : 1 % × agitation / repère, mêmes bornes (l'essai 55 Z1 voit la zone de bruit meilleure les jours agités). Mesures en % du compte, sans intérêts composés : gain total, baisse maximale, rapport gain/baisse, par an. Retenue si le rapport gain/baisse est meilleur que T0 sur 2014-2019 ET 2020+, et meilleur que 950 sur 1000 tailles tirées au hasard (mêmes tailles mélangées entre les trades). Rien en réel sans l'accord de Yanisse. `trading_bot/essai56.py` | **Une cellule passe : T2 sur la zone de bruit v2** (`data/essai56.json`, 2 717 trades). Gain total +414 % du compte (sans composés) contre +305 % en taille fixe, baisse maximale 58,7 % contre 70,2 %, rapport gain/baisse 7,06 contre 4,35 ; 2014-2019 2,26 contre 1,05, 2020+ 10,73 contre 9,71 ; bat 985 tailles au hasard sur 1000. Réserve : 2018 pèse lourd (+154 %). T1 (plus petit quand ça bouge) est pire partout (2,03, bat 0). Double 7 : T2 meilleur rapport (7,63 contre 5,82) mais bat seulement 935 tailles au hasard sur 1000, T1 pire : rien. Carte posée à Yanisse pour appliquer T2 à la copie démo de la zone de bruit v2. |
| 2026-10-26 | **Essai 57** (pré-enregistré, demande de Yanisse : méthodes de day trading que les traders utilisent tous les jours, comme celles de BENAGOLD et Hugo ; règles prises dans le script public « ICT Silver Bullet Backtest » de TradingView et le guide TradeAlgo) : bougies 5 min 2014-2026, frais et singes de l'essai 21. **J1 « Silver Bullet » ICT** : dans la fenêtre, premier creux de prix (FVG) sur 3 bougies (haussier : plus bas de la 3e > plus haut de la 1re ; baissier en miroir) ; ordre limite au milieu du creux, valable jusqu'à la fin de la fenêtre ; stop au plus bas de la 1re bougie (plus haut pour une vente) ; objectif 2 R ; fermeture 16:00 New York ; un trade par jour. **J1a** Nasdaq 10:00-11:00 New York, **J1b** or 10:00-11:00, **J1c** or 3:00-4:00 (Londres). **J3 « Red to Green »** : si la séance ouvre (9:30) sous la clôture de la veille, achat à la 1re clôture 5 min au-dessus de la clôture de la veille entre 9:35 et 11:00, stop au plus bas de la séance, objectif le plus haut de la veille (au moins 1 R), fermeture 16:00 ; « Green to Red » en miroir ; un trade par jour. **J3a** Nasdaq, **J3b** S&P 500. Retenue si ≥ 200 trades, > 0 R sur 2014-2019 ET 2020+, > 0 avec frais doublés, bat 95 % des singes, z au-dessus du seuil corrigé sur 5 cellules. Rien en réel sans l'accord de Yanisse. `trading_bot/essai57.py` | **Rien ne passe** (`data/essai57.json`). J1a Silver Bullet Nasdaq −0,04 R (1 836 trades, 35 % gagnants, 2014-2019 −0,12, 2020+ +0,03, singes 887) ; J1b or 10-11 −0,22 R et J1c or Londres −0,36 R (0/13 années : stops de quelques dollars, les frais mangent tout) ; J3a Red to Green Nasdaq −0,05 R (1 202, singes 275), J3b S&P −0,14 R. Ces méthodes très suivies ne battent pas le hasard une fois codées. Rien changé. |
| 2026-10-26 | Choix de Yanisse (carte après l'essai 56, « ombre d'abord ») : chaque entrée de la zone de bruit v2 affiche dans Telegram la taille conseillée par l'essai 56 (×0,5 à ×2 selon l'agitation, soit 2,5 % à 10 % au lieu de 5 %), notée dans le trade (`taille_x`). Information seulement : la copie démo reste à 5 %. GitHub calcule sur les bougies 1 h Yahoo regroupées par jour, le PC sur les bougies jour MT5. `trading_bot/taille.py` | Fait |
| 2026-10-26 | Pré-enregistrement de l'essai 60 (memecoins, copie des portefeuilles, sortie en 3 lots ; d'abord numéroté 40 par erreur, numéro déjà pris) | — |
| 2026-10-26 | **Essai 58** (pré-enregistré, accord de Yanisse : améliorer le bot classique) : rejeu de l'essai 43 (entrées du bot 2014-2026, un seul signal ouvert, règles du jour), frais du bot, contrôles de l'essai 24. Nasdaq (stop ×1,5, objectif 3, 24 h = N24 de l'essai 55, +0,087 R) : **B1** seulement les jours agités (taille de l'essai 56 ≥ 1) ; **B2** tous les trades avec la taille T2 de l'essai 56 (mesure gain/baisse, comme l'essai 56). Or : le sens du bot bat les singes mais le stop serré fait payer les frais ; **G1** 1er signal du jour seulement, stop ×2, objectif 2 fois le stop, 24 h ; **G2** pareil avec stop ×3. B1, G1, G2 retenues si les 10 contrôles de l'essai 24 passent (et pour B1 R > N24 et mieux que 950 filtres au hasard sur 1000) ; B2 si gain/baisse meilleur que N24 sur 2014-2019 ET 2020+ et mieux que 950 tailles au hasard. **Essai 59** (information, demande de Yanisse : « miser plus ») : nos 7 stratégies en réel (zone de bruit v2, bot Nasdaq, Double 7, cassure Williams, Donchian 1 h et W3 Bitcoin, nuit asiatique or), chacune seule sur un compte de 1 000 $ avec intérêts composés, 1 %, 2 %, 5 % et 10 % du solde risqués par trade, 2014-2026 dans l'ordre réel, puis 1 000 ordres mélangés : solde final, pire baisse, part des parcours où le compte perd 50 % puis 90 %. Rien en réel sans l'accord de Yanisse. `trading_bot/essai58.py` | **Essai 58 : rien ne passe** (`data/essai58.json`). B1 bot Nasdaq jours agités +0,085 R (1 376 trades) contre +0,087 R pour tous : pas mieux. B2 taille selon l'agitation : gain/baisse 5,65 contre 5,88 (meilleur avant 2020, pire depuis, hasard 604). Or G1 stop ×2 −0,02 R (2 039), G2 stop ×3 +0,015 R (1 954, PF 1,02, 5/12 années) : le sens bat les singes (959-973) mais il reste trop peu par trade. **Essai 59 (mise, comptes de 1 000 $ composés, 2014-2026)** : à 1 % du solde par trade, toutes gagnent (bot Nasdaq 8 347 $, zone de bruit v2 15 786 $, Williams 15 096 $, Donchian 1 h 14 173 $, W3 10 852 $, nuit asiatique 2 110 $, Double 7 1 396 $), pire baisse 6 à 54 %. À 2 % : pire baisse 39 à 82 %, et 95-100 % des ordres mélangés passent par −50 % (sauf Williams, nuit asiatique, Double 7). **À 5 %** (mise actuelle de la copie démo) : pire baisse 73 à 100 % ; le compte passe par −90 % dans 91 à 99,7 % des ordres mélangés pour bot Nasdaq, zone de bruit v2, Donchian 1 h, W3. À 10 % : zone de bruit, bot Nasdaq, Donchian, W3 finissent à 0. Seuls Double 7 (pire baisse 26 % à 5 %) et la nuit asiatique supportent une grosse mise. Constat : 1 % (2 % au plus) par stratégie ; et plusieurs stratégies sur un même compte s'additionnent. |
| 2026-10-26 | **Essai 60** : memecoins pump.fun, copier les meilleurs portefeuilles de juin sur les coins de juillet (frais Axiom 1 % par côté en plus), sortie en 3 lots, 9 cellules (seuil z 2,54) | **Rien ne passe : les 9 cellules perdent.** **Copie des 100 meilleurs** (21 490 trades) : −11,2 à −12,7 % par trade, 78 à 80 % de perdants, ne bat pas les singes (162 à 226 sur 1 000). **Copie des 1 000 meilleurs** (51 493) : −12,4 à −12,8 %, **pire qu'un coin au hasard** (0 singe battu, z −4 à −10) : quand on les voit acheter, ils sont déjà dedans et on achète plus haut. Revendre quand le portefeuille revend (X1) ne fait pas mieux que le suiveur. **Sortie en 3 lots** (frais pump.fun seuls) : K2 −7,9 %, K3 −7,0 %, K5 −5,4 % par trade, presque pareil que le suiveur 20 % de l'essai 38 (−8,1 / −7,2 / −5,1). Avec les frais Axiom : −10,2 / −9,3 / −7,7 %. Singes de X1 : durée de garde arrondie à la plus proche de 8 durées. Pas de suivi papier. |
