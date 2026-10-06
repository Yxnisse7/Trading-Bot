# Trading-Bot — rapport

_Mis à jour le 06/10/2026 à 06:15 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **112**
- Taux de réussite cumulé (TP / (TP+SL)) : **48%** — hasard attendu 42%, avantage **+6%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-2.09 %** (brut +0.98 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **211** clôturés, 0 ouverts, taux de réussite 35% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 18 | 6 | 7 | 5 | 46% | -0.041 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 28 | 13 | 12 | 3 | 52% | -0.004 % |
| nasdaq | 33 | 15 | 13 | 5 | 54% | +0.022 % |
| sp500 | 22 | 7 | 9 | 6 | 44% | -0.008 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 61 | 20 | 26 | 15 | 43% | -0.037 % |
| short | 51 | 23 | 21 | 7 | 52% | +0.003 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 108 | 42 | 45 | 21 | 48% | -0.017 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 111 | 43 | 47 | 21 | 48% | -0.017 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 14 | 4 | 8 | 2 | 33% | -0.035 % |
| macd | 27 | 8 | 16 | 3 | 33% | -0.090 % |
| orb | 11 | 3 | 7 | 1 | 30% | -0.072 % |
| pdhl | 20 | 7 | 9 | 4 | 44% | -0.027 % |
| rsi | 95 | 38 | 38 | 19 | 50% | -0.008 % |
| trend_15m | 111 | 43 | 47 | 21 | 48% | -0.017 % |
| trend_1h | 111 | 43 | 47 | 21 | 48% | -0.017 % |
| trend_5m | 100 | 40 | 39 | 21 | 51% | -0.010 % |
| volume | 5 | 2 | 3 | 0 | 40% | -0.083 % |
| vwap | 109 | 43 | 45 | 21 | 49% | -0.012 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 50 | 16 | 24 | 10 | 40% | -0.044 % |
| actualité chargée | 62 | 27 | 23 | 12 | 54% | +0.002 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 7 | 5 | 0 | 2 | 100% | +0.142 % |
| 08h | 5 | 1 | 4 | 0 | 20% | -0.177 % |
| 09h | 4 | 1 | 2 | 1 | 33% | -0.144 % |
| 10h | 2 | 1 | 0 | 1 | 100% | +0.065 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
| 13h | 6 | 0 | 5 | 1 | 0% | -0.107 % |
| 14h | 15 | 6 | 7 | 2 | 46% | -0.009 % |
| 15h | 19 | 6 | 11 | 2 | 35% | -0.083 % |
| 16h | 7 | 2 | 3 | 2 | 40% | +0.009 % |
| 17h | 6 | 2 | 1 | 3 | 67% | +0.054 % |
| 18h | 9 | 6 | 1 | 2 | 86% | +0.081 % |
| 19h | 11 | 6 | 4 | 1 | 60% | +0.041 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 111 | 43 | 47 | 21 | 48% | -0.017 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 110 | 43 | 45 | 22 | 49% | -0.014 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 22, 68% terminés dans le bon sens, P&L moyen +0.004 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 211 | 61 | 111 | 39 | 35% | -0.042 % |
| corr | 13 | 1 | 9 | 3 | 10% | -0.204 % |
| level | 23 | 6 | 8 | 9 | 43% | -0.069 % |
| macd | 55 | 12 | 33 | 10 | 27% | -0.070 % |
| orb | 8 | 3 | 4 | 1 | 43% | -0.127 % |
| pdhl | 27 | 7 | 14 | 6 | 33% | -0.033 % |
| rsi | 145 | 42 | 83 | 20 | 34% | -0.050 % |
| trend_15m | 211 | 61 | 111 | 39 | 35% | -0.042 % |
| trend_1h | 206 | 58 | 110 | 38 | 35% | -0.043 % |
| trend_5m | 170 | 56 | 92 | 22 | 38% | -0.033 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 207 | 61 | 107 | 39 | 36% | -0.038 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| euro | 18 | 7 | 10 | 1 | 41% | -0.020 % |
| gold | 35 | 13 | 16 | 6 | 45% | +0.007 % |
| nasdaq | 50 | 19 | 23 | 8 | 45% | -0.013 % |
| oil | 33 | 10 | 17 | 6 | 37% | -0.068 % |
| sp500 | 52 | 9 | 36 | 7 | 20% | -0.061 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 30/09 16:01 | Nasdaq 100 (NQ) | long | 30771.0 | 30885.5 | ✅ TP | +0.36 % | 4 min |
| 30/09 09:55 | Or (XAU/USD) | long | 4225.6 | 4232.4 | ✅ TP | +0.14 % | 26 min |
| 29/09 21:15 | Nasdaq 100 (NQ) | long | 30651.5 | 30614.25 | ❌ SL | -0.13 % | 25 min |
| 29/09 20:15 | Or (XAU/USD) | long | 4195.6 | 4203.0 | ✅ TP | +0.16 % | 0 min |
| 29/09 16:30 | Or (XAU/USD) | long | 4206.8 | 4196.3 | ❌ SL | -0.27 % | 6 min |
| 28/09 21:50 | S&P 500 (ES) | short | 7742.5 | 7744.5 | ⏱️ expiré | -0.04 % | 60 min |
| 28/09 21:20 | Or (XAU/USD) | short | 4165.1 | 4153.8 | ✅ TP | +0.25 % | 40 min |

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

- sp500 : {'trend_5m': 0.961, 'trend_15m': 0.961, 'trend_1h': 0.961, 'adx': 0.961, 'vwap': 0.698}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 44 | -0.37 R | en test |
| horizon ~3 h | 42 | -0.30 R | en test |
| confiance moyenne | 26 | -0.06 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 4 | +0.04 R | en test |
| reprise juste après un stop | 16 | -0.44 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 0 | n/a | en test |
| nouvel actif : Pétrole WTI (CL) | 33 | -0.13 R | en test |
| nouvel actif : Euro / dollar (6E) | 18 | -0.26 R | en test |

Notes :

- trades réels : +0,15 R ± 0,21 R par trade avant frais sur 112 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,18 R contre +0,02 R en global sur 133 trades éq. → poids ×0,96 sur cet actif
- sp500, vwap : -0,19 R contre +0,04 R en global sur 130 trades éq. → poids ×0,93 sur cet actif
- variante « indices le matin européen » en test : 44 trades, -0,37 R net, encore 56 trades avant décision
- variante « horizon ~3 h » en test : 42 trades, -0,30 R net, encore 58 trades avant décision
- variante « confiance moyenne » en test : 26 trades, -0,06 R net, encore 74 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 4 trades, +0,04 R net, encore 96 trades avant décision
- variante « reprise juste après un stop » en test : 16 trades, -0,44 R net, encore 84 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 33 trades, -0,13 R net, encore 67 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 18 trades, -0,26 R net, encore 82 trades avant décision
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
