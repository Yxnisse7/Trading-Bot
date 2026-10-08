# Trading-Bot — rapport

_Mis à jour le 08/10/2026 à 15:15 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **122**
- Taux de réussite cumulé (TP / (TP+SL)) : **44%** — hasard attendu 42%, avantage **+2%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-3.38 %** (brut -0.17 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **278** clôturés, 0 ouverts, taux de réussite 35% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 18 | 6 | 7 | 5 | 46% | -0.041 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 32 | 13 | 16 | 3 | 45% | -0.026 % |
| nasdaq | 36 | 15 | 15 | 6 | 50% | +0.012 % |
| sp500 | 25 | 7 | 11 | 7 | 39% | -0.017 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 67 | 20 | 30 | 17 | 40% | -0.042 % |
| short | 55 | 23 | 25 | 7 | 48% | -0.010 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 118 | 42 | 53 | 23 | 44% | -0.026 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 121 | 43 | 55 | 23 | 44% | -0.027 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 15 | 4 | 9 | 2 | 31% | -0.044 % |
| macd | 34 | 8 | 21 | 5 | 28% | -0.094 % |
| orb | 14 | 3 | 8 | 3 | 27% | -0.069 % |
| pdhl | 22 | 7 | 11 | 4 | 39% | -0.038 % |
| rsi | 105 | 38 | 46 | 21 | 45% | -0.019 % |
| trend_15m | 121 | 43 | 55 | 23 | 44% | -0.027 % |
| trend_1h | 121 | 43 | 55 | 23 | 44% | -0.027 % |
| trend_5m | 109 | 40 | 46 | 23 | 47% | -0.020 % |
| volume | 5 | 2 | 3 | 0 | 40% | -0.083 % |
| vwap | 119 | 43 | 53 | 23 | 45% | -0.022 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 53 | 16 | 27 | 10 | 37% | -0.050 % |
| actualité chargée | 69 | 27 | 28 | 14 | 49% | -0.011 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 7 | 5 | 0 | 2 | 100% | +0.142 % |
| 08h | 6 | 1 | 5 | 0 | 17% | -0.176 % |
| 09h | 5 | 1 | 3 | 1 | 25% | -0.145 % |
| 10h | 2 | 1 | 0 | 1 | 100% | +0.065 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
| 13h | 8 | 0 | 7 | 1 | 0% | -0.132 % |
| 14h | 15 | 6 | 7 | 2 | 46% | -0.009 % |
| 15h | 22 | 6 | 12 | 4 | 33% | -0.080 % |
| 16h | 8 | 2 | 4 | 2 | 33% | -0.005 % |
| 17h | 6 | 2 | 1 | 3 | 67% | +0.054 % |
| 18h | 10 | 6 | 2 | 2 | 75% | +0.061 % |
| 19h | 12 | 6 | 5 | 1 | 55% | +0.025 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 121 | 43 | 55 | 23 | 44% | -0.027 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 120 | 43 | 53 | 24 | 45% | -0.024 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 24, 67% terminés dans le bon sens, P&L moyen +0.002 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 278 | 81 | 150 | 47 | 35% | -0.040 % |
| corr | 14 | 1 | 10 | 3 | 9% | -0.203 % |
| level | 30 | 10 | 11 | 9 | 48% | -0.064 % |
| macd | 72 | 16 | 43 | 13 | 27% | -0.070 % |
| orb | 11 | 3 | 7 | 1 | 30% | -0.128 % |
| pdhl | 39 | 9 | 22 | 8 | 29% | -0.043 % |
| rsi | 189 | 59 | 106 | 24 | 36% | -0.039 % |
| trend_15m | 278 | 81 | 150 | 47 | 35% | -0.040 % |
| trend_1h | 271 | 78 | 148 | 45 | 35% | -0.041 % |
| trend_5m | 225 | 76 | 121 | 28 | 39% | -0.028 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 271 | 81 | 144 | 46 | 36% | -0.038 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| euro | 23 | 8 | 14 | 1 | 36% | -0.024 % |
| gold | 46 | 15 | 25 | 6 | 38% | -0.028 % |
| nasdaq | 71 | 26 | 36 | 9 | 42% | -0.021 % |
| oil | 45 | 14 | 22 | 9 | 39% | -0.041 % |
| sp500 | 70 | 15 | 44 | 11 | 25% | -0.049 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 08/10 10:35 | Or (XAU/USD) | long | 4156.4 | 4150.2 | ❌ SL | -0.17 % | 1 min |
| 07/10 21:55 | Or (XAU/USD) | short | 4130.1 | 4135.5 | ❌ SL | -0.15 % | 26 min |
| 07/10 17:01 | S&P 500 (ES) | short | 7817.75 | 7827.75 | ❌ SL | -0.14 % | 11 min |
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

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 59 | -0.18 R | en test |
| horizon ~3 h | 57 | -0.33 R | en test |
| confiance moyenne | 34 | -0.29 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 5 | -0.18 R | en test |
| reprise juste après un stop | 20 | -0.43 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 5 | -0.66 R | en test |
| nouvel actif : Pétrole WTI (CL) | 45 | -0.06 R | en test |
| nouvel actif : Euro / dollar (6E) | 23 | -0.38 R | en test |

Notes :

- trades réels : +0,07 R ± 0,20 R par trade avant frais sur 122 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- variante « indices le matin européen » en test : 59 trades, -0,18 R net, encore 41 trades avant décision
- variante « horizon ~3 h » en test : 57 trades, -0,33 R net, encore 43 trades avant décision
- variante « confiance moyenne » en test : 34 trades, -0,29 R net, encore 66 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 5 trades, -0,18 R net, encore 95 trades avant décision
- variante « reprise juste après un stop » en test : 20 trades, -0,43 R net, encore 80 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « horizon ~3 h sur Or (XAU/USD) » en test : 5 trades, -0,66 R net, encore 95 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 45 trades, -0,06 R net, encore 55 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 23 trades, -0,38 R net, encore 77 trades avant décision
- sortie : stop remonté à l'entrée après +0,5 R ferait mieux (-0,17 R net contre -0,27 R, réels et en ombre) : à décider
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
