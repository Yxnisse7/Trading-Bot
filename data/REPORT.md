# Trading-Bot — rapport

_Mis à jour le 07/10/2026 à 16:31 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **119**
- Taux de réussite cumulé (TP / (TP+SL)) : **45%** — hasard attendu 42%, avantage **+4%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-2.92 %** (brut +0.24 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **253** clôturés, 1 ouverts, taux de réussite 36% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 18 | 6 | 7 | 5 | 46% | -0.041 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 30 | 13 | 14 | 3 | 48% | -0.017 % |
| nasdaq | 36 | 15 | 15 | 6 | 50% | +0.012 % |
| sp500 | 24 | 7 | 10 | 7 | 41% | -0.012 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 66 | 20 | 29 | 17 | 41% | -0.040 % |
| short | 53 | 23 | 23 | 7 | 50% | -0.005 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 115 | 42 | 50 | 23 | 46% | -0.023 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 118 | 43 | 52 | 23 | 45% | -0.023 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 14 | 4 | 8 | 2 | 33% | -0.035 % |
| macd | 31 | 8 | 18 | 5 | 31% | -0.089 % |
| orb | 13 | 3 | 7 | 3 | 30% | -0.064 % |
| pdhl | 20 | 7 | 9 | 4 | 44% | -0.027 % |
| rsi | 102 | 38 | 43 | 21 | 47% | -0.015 % |
| trend_15m | 118 | 43 | 52 | 23 | 45% | -0.023 % |
| trend_1h | 118 | 43 | 52 | 23 | 45% | -0.023 % |
| trend_5m | 107 | 40 | 44 | 23 | 48% | -0.017 % |
| volume | 5 | 2 | 3 | 0 | 40% | -0.083 % |
| vwap | 116 | 43 | 50 | 23 | 46% | -0.018 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 51 | 16 | 25 | 10 | 39% | -0.045 % |
| actualité chargée | 68 | 27 | 27 | 14 | 50% | -0.009 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 7 | 5 | 0 | 2 | 100% | +0.142 % |
| 08h | 5 | 1 | 4 | 0 | 20% | -0.177 % |
| 09h | 5 | 1 | 3 | 1 | 25% | -0.145 % |
| 10h | 2 | 1 | 0 | 1 | 100% | +0.065 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
| 13h | 8 | 0 | 7 | 1 | 0% | -0.132 % |
| 14h | 15 | 6 | 7 | 2 | 46% | -0.009 % |
| 15h | 21 | 6 | 11 | 4 | 35% | -0.077 % |
| 16h | 8 | 2 | 4 | 2 | 33% | -0.005 % |
| 17h | 6 | 2 | 1 | 3 | 67% | +0.054 % |
| 18h | 10 | 6 | 2 | 2 | 75% | +0.061 % |
| 19h | 11 | 6 | 4 | 1 | 60% | +0.041 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 118 | 43 | 52 | 23 | 45% | -0.023 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 117 | 43 | 50 | 24 | 46% | -0.020 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 24, 67% terminés dans le bon sens, P&L moyen +0.002 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 253 | 76 | 134 | 43 | 36% | -0.037 % |
| corr | 14 | 1 | 10 | 3 | 9% | -0.203 % |
| level | 28 | 10 | 9 | 9 | 53% | -0.060 % |
| macd | 68 | 16 | 41 | 11 | 28% | -0.071 % |
| orb | 11 | 3 | 7 | 1 | 30% | -0.128 % |
| pdhl | 31 | 9 | 15 | 7 | 38% | -0.013 % |
| rsi | 171 | 54 | 94 | 23 | 36% | -0.035 % |
| trend_15m | 253 | 76 | 134 | 43 | 36% | -0.037 % |
| trend_1h | 248 | 73 | 133 | 42 | 35% | -0.038 % |
| trend_5m | 206 | 71 | 110 | 25 | 39% | -0.024 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 249 | 76 | 130 | 43 | 37% | -0.034 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| euro | 21 | 7 | 13 | 1 | 35% | -0.027 % |
| gold | 42 | 15 | 21 | 6 | 42% | -0.011 % |
| nasdaq | 64 | 24 | 31 | 9 | 44% | -0.017 % |
| oil | 41 | 14 | 20 | 7 | 41% | -0.036 % |
| sp500 | 62 | 13 | 40 | 9 | 25% | -0.052 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 07/10 15:50 | Nasdaq 100 (NQ) | short | 31181.0 | 31226.75 | ❌ SL | -0.16 % | 7 min |
| 07/10 15:35 | Or (XAU/USD) | short | 4115.2 | 4124.9 | ❌ SL | -0.26 % | 15 min |
| 06/10 20:15 | Nasdaq 100 (NQ) | long | 31552.0 | 31518.5 | ❌ SL | -0.12 % | 9 min |
| 06/10 18:20 | S&P 500 (ES) | long | 7889.75 | 7882.5 | ❌ SL | -0.10 % | 9 min |
| 06/10 17:15 | S&P 500 (ES) | long | 7889.0 | 7889.25 | ⏱️ expiré | -0.01 % | 64 min |
| 06/10 17:05 | Nasdaq 100 (NQ) | long | 31576.25 | 31567.75 | ⏱️ expiré | -0.04 % | 60 min |
| 06/10 11:45 | Or (XAU/USD) | long | 4183.8 | 4178.4 | ❌ SL | -0.15 % | 19 min |
| 05/10 21:01 | Nasdaq 100 (NQ) | long | 31315.25 | 31368.75 | ✅ TP | +0.16 % | 17 min |
| 05/10 20:10 | S&P 500 (ES) | long | 7829.25 | 7839.25 | ⏱️ expiré | +0.12 % | 60 min |
| 05/10 19:56 | Nasdaq 100 (NQ) | long | 31303.5 | 31309.5 | ⏱️ expiré | +0.01 % | 65 min |
| 05/10 19:10 | S&P 500 (ES) | long | 7822.25 | 7829.0 | ⏱️ expiré | +0.08 % | 60 min |
| 05/10 17:01 | Nasdaq 100 (NQ) | long | 31225.0 | 31240.25 | ⏱️ expiré | +0.04 % | 60 min |
| 05/10 16:15 | S&P 500 (ES) | long | 7794.5 | 7808.75 | ✅ TP | +0.17 % | 4 min |
| 02/10 20:05 | Bitcoin (BTC/USD) | short | 84854.0 | 84531.0 | ✅ TP | +0.32 % | 26 min |
| 02/10 19:15 | Bitcoin (BTC/USD) | short | 84893.0 | 84574.0 | ✅ TP | +0.32 % | 8 min |
| 02/10 18:20 | Bitcoin (BTC/USD) | short | 85304.0 | 84974.0 | ✅ TP | +0.33 % | 53 min |
| 02/10 17:55 | Or (XAU/USD) | short | 4161.0 | 4153.9 | ✅ TP | +0.15 % | 1 min |
| 02/10 17:01 | Nasdaq 100 (NQ) | long | 31213.25 | 31154.0 | ❌ SL | -0.20 % | 0 min |
| 02/10 15:55 | Nasdaq 100 (NQ) | long | 31178.5 | 31212.75 | ⏱️ expiré | +0.10 % | 65 min |
| 02/10 15:35 | S&P 500 (ES) | long | 7789.75 | 7776.75 | ❌ SL | -0.18 % | 20 min |
| 01/10 20:20 | Nasdaq 100 (NQ) | short | 30714.5 | 30764.75 | ❌ SL | -0.17 % | 2 min |
| 01/10 17:15 | S&P 500 (ES) | short | 7680.0 | 7687.75 | ❌ SL | -0.11 % | 0 min |
| 01/10 16:55 | Nasdaq 100 (NQ) | short | 30706.75 | 30645.25 | ✅ TP | +0.19 % | 0 min |
| 01/10 16:10 | S&P 500 (ES) | short | 7698.0 | 7689.5 | ⏱️ expiré | +0.10 % | 60 min |
| 01/10 11:35 | Or (XAU/USD) | short | 4189.3 | 4182.8 | ✅ TP | +0.14 % | 24 min |
| 30/09 21:15 | Nasdaq 100 (NQ) | long | 30841.75 | 30807.0 | ❌ SL | -0.12 % | 34 min |
| 30/09 18:35 | Nasdaq 100 (NQ) | long | 30862.25 | 30835.25 | ❌ SL | -0.10 % | 10 min |
| 30/09 18:15 | Or (XAU/USD) | short | 4192.0 | 4187.3 | ⏱️ expiré | +0.09 % | 60 min |
| 30/09 17:30 | Nasdaq 100 (NQ) | long | 30822.0 | 30887.5 | ✅ TP | +0.20 % | 18 min |
| 30/09 16:40 | Nasdaq 100 (NQ) | long | 30827.25 | 30861.25 | ⏱️ expiré | +0.10 % | 65 min |

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.0 |
| trend_15m | 1.0 |
| trend_1h | 1.0 |
| adx | 1.0 |
| vwap | 0.75 |
| rsi | 1.0 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.0 |
| corr | 0.5 |

Corrections par actif :

- sp500 : {'vwap': 0.739}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 51 | -0.23 R | en test |
| horizon ~3 h | 54 | -0.29 R | en test |
| confiance moyenne | 32 | -0.23 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 5 | -0.18 R | en test |
| reprise juste après un stop | 18 | -0.35 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 3 | -0.37 R | en test |
| nouvel actif : Pétrole WTI (CL) | 41 | -0.04 R | en test |
| nouvel actif : Euro / dollar (6E) | 21 | -0.42 R | en test |

Notes :

- trades réels : +0,09 R ± 0,21 R par trade avant frais sur 119 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- sp500, vwap : -0,18 R contre +0,02 R en global sur 141 trades éq. → poids ×0,99 sur cet actif
- variante « indices le matin européen » en test : 51 trades, -0,23 R net, encore 49 trades avant décision
- variante « horizon ~3 h » en test : 54 trades, -0,29 R net, encore 46 trades avant décision
- variante « confiance moyenne » en test : 32 trades, -0,23 R net, encore 68 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 5 trades, -0,18 R net, encore 95 trades avant décision
- variante « reprise juste après un stop » en test : 18 trades, -0,35 R net, encore 82 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « horizon ~3 h sur Or (XAU/USD) » en test : 3 trades, -0,37 R net, encore 97 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 41 trades, -0,04 R net, encore 59 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 21 trades, -0,42 R net, encore 79 trades avant décision
- sortie : stop remonté à l'entrée après +1,0 R ferait mieux (-0,06 R net contre -0,09 R, backtest) : à décider

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 04/10/2026 | 87 | 22 | 42 | 23 | 34% | 42% | -7% | -1.15 % | -0.013 % |
| S&P 500 (ES) | 09/07/2026 → 04/10/2026 | 104 | 35 | 53 | 16 | 40% | 42% | -2% | -0.64 % | -0.006 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 04/10/2026 | 55 | 20 | 23 | 12 | 47% | 41% | +6% | -0.99 % | -0.018 % |
| Ethereum (ETH/USD) | 20/07/2026 → 04/10/2026 | 56 | 11 | 27 | 18 | 29% | 40% | -11% | -6.67 % | -0.119 % |
| Or (XAU/USD) | 09/07/2026 → 04/10/2026 | 130 | 43 | 52 | 35 | 45% | 42% | +3% | -1.47 % | -0.011 % |
| Pétrole WTI (CL) | 14/07/2026 → 04/10/2026 | 186 | 60 | 85 | 41 | 41% | 41% | +0% | +2.42 % | +0.013 % |
| Euro / dollar (6E) | 14/07/2026 → 04/10/2026 | 31 | 9 | 19 | 3 | 32% | 40% | -8% | -0.65 % | -0.021 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
