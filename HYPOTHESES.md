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
