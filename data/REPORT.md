# Trading-Bot — rapport

_Mis à jour le 07/10/2026 à 10:10 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **117**
- Taux de réussite cumulé (TP / (TP+SL)) : **46%** — hasard attendu 42%, avantage **+5%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-2.51 %** (brut +0.62 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **238** clôturés, 0 ouverts, taux de réussite 35% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 18 | 6 | 7 | 5 | 46% | -0.041 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 29 | 13 | 13 | 3 | 50% | -0.009 % |
| nasdaq | 35 | 15 | 14 | 6 | 52% | +0.017 % |
| sp500 | 24 | 7 | 10 | 7 | 41% | -0.012 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 66 | 20 | 29 | 17 | 41% | -0.040 % |
| short | 51 | 23 | 21 | 7 | 52% | +0.003 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 113 | 42 | 48 | 23 | 47% | -0.019 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 116 | 43 | 50 | 23 | 46% | -0.020 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 14 | 4 | 8 | 2 | 33% | -0.035 % |
| macd | 30 | 8 | 17 | 5 | 32% | -0.086 % |
| orb | 13 | 3 | 7 | 3 | 30% | -0.064 % |
| pdhl | 20 | 7 | 9 | 4 | 44% | -0.027 % |
| rsi | 100 | 38 | 41 | 21 | 48% | -0.012 % |
| trend_15m | 116 | 43 | 50 | 23 | 46% | -0.020 % |
| trend_1h | 116 | 43 | 50 | 23 | 46% | -0.020 % |
| trend_5m | 105 | 40 | 42 | 23 | 49% | -0.014 % |
| volume | 5 | 2 | 3 | 0 | 40% | -0.083 % |
| vwap | 114 | 43 | 48 | 23 | 47% | -0.015 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 51 | 16 | 25 | 10 | 39% | -0.045 % |
| actualité chargée | 66 | 27 | 25 | 14 | 52% | -0.003 % |

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
| 13h | 6 | 0 | 5 | 1 | 0% | -0.107 % |
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
| signaux du bot | 116 | 43 | 50 | 23 | 46% | -0.020 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 115 | 43 | 48 | 24 | 47% | -0.017 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 24, 67% terminés dans le bon sens, P&L moyen +0.002 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 238 | 69 | 127 | 42 | 35% | -0.039 % |
| corr | 14 | 1 | 10 | 3 | 9% | -0.203 % |
| level | 25 | 7 | 9 | 9 | 44% | -0.081 % |
| macd | 63 | 13 | 39 | 11 | 25% | -0.079 % |
| orb | 11 | 3 | 7 | 1 | 30% | -0.128 % |
| pdhl | 29 | 8 | 15 | 6 | 35% | -0.019 % |
| rsi | 163 | 50 | 91 | 22 | 35% | -0.036 % |
| trend_15m | 238 | 69 | 127 | 42 | 35% | -0.039 % |
| trend_1h | 233 | 66 | 126 | 41 | 34% | -0.040 % |
| trend_5m | 192 | 64 | 104 | 24 | 38% | -0.026 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 234 | 69 | 123 | 42 | 36% | -0.036 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| euro | 19 | 7 | 11 | 1 | 39% | -0.023 % |
| gold | 37 | 14 | 17 | 6 | 45% | +0.007 % |
| nasdaq | 59 | 20 | 31 | 8 | 39% | -0.028 % |
| oil | 41 | 14 | 20 | 7 | 41% | -0.036 % |
| sp500 | 59 | 11 | 39 | 9 | 22% | -0.056 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 30/09 16:01 | Nasdaq 100 (NQ) | long | 30771.0 | 30885.5 | ✅ TP | +0.36 % | 4 min |
| 30/09 09:55 | Or (XAU/USD) | long | 4225.6 | 4232.4 | ✅ TP | +0.14 % | 26 min |

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

- sp500 : {'trend_5m': 0.974, 'trend_15m': 0.974, 'trend_1h': 0.974, 'adx': 0.974, 'vwap': 0.711}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 44 | -0.37 R | en test |
| horizon ~3 h | 53 | -0.32 R | en test |
| confiance moyenne | 30 | -0.16 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 4 | +0.04 R | en test |
| reprise juste après un stop | 18 | -0.35 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 1 | -1.12 R | en test |
| nouvel actif : Pétrole WTI (CL) | 41 | -0.04 R | en test |
| nouvel actif : Euro / dollar (6E) | 19 | -0.34 R | en test |

Notes :

- trades réels : +0,11 R ± 0,21 R par trade avant frais sur 117 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,19 R contre +0,01 R en global sur 141 trades éq. → poids ×0,97 sur cet actif
- sp500, vwap : -0,19 R contre +0,02 R en global sur 138 trades éq. → poids ×0,95 sur cet actif
- variante « indices le matin européen » en test : 44 trades, -0,37 R net, encore 56 trades avant décision
- variante « horizon ~3 h » en test : 53 trades, -0,32 R net, encore 47 trades avant décision
- variante « confiance moyenne » en test : 30 trades, -0,16 R net, encore 70 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 4 trades, +0,04 R net, encore 96 trades avant décision
- variante « reprise juste après un stop » en test : 18 trades, -0,35 R net, encore 82 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « horizon ~3 h sur Or (XAU/USD) » en test : 1 trades, -1,12 R net, encore 99 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 41 trades, -0,04 R net, encore 59 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 19 trades, -0,34 R net, encore 81 trades avant décision
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
