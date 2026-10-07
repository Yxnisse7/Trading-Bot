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
