# Trading-Bot — rapport

_Mis à jour le 09/10/2026 à 19:45 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **136**
- Taux de réussite cumulé (TP / (TP+SL)) : **42%** — hasard attendu 42%, avantage **+1%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-4.47 %** (brut -0.83 %)
- Signaux ouverts : **1**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **315** clôturés, 2 ouverts, taux de réussite 37% (hasard attendu 41%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 09/10 19:30 | Nasdaq 100 (NQ) | short | 31078.0 | 31044.25 | 31106.0 | fort | signaux du bot | 20:30 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 23 | 6 | 9 | 8 | 40% | -0.060 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 36 | 13 | 17 | 6 | 43% | -0.032 % |
| nasdaq | 39 | 16 | 17 | 6 | 48% | +0.007 % |
| sp500 | 27 | 8 | 12 | 7 | 40% | -0.015 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 73 | 20 | 31 | 22 | 39% | -0.040 % |
| short | 63 | 25 | 30 | 8 | 45% | -0.025 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 132 | 44 | 59 | 29 | 43% | -0.032 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 135 | 45 | 61 | 29 | 42% | -0.032 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 16 | 4 | 9 | 3 | 31% | -0.047 % |
| macd | 40 | 9 | 23 | 8 | 28% | -0.097 % |
| orb | 14 | 3 | 8 | 3 | 27% | -0.069 % |
| pdhl | 23 | 8 | 11 | 4 | 42% | -0.032 % |
| rsi | 116 | 40 | 50 | 26 | 44% | -0.021 % |
| trend_15m | 135 | 45 | 61 | 29 | 42% | -0.032 % |
| trend_1h | 135 | 45 | 61 | 29 | 42% | -0.032 % |
| trend_5m | 121 | 42 | 52 | 27 | 45% | -0.024 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 133 | 45 | 59 | 29 | 43% | -0.028 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 60 | 17 | 28 | 15 | 38% | -0.046 % |
| actualité chargée | 76 | 28 | 33 | 15 | 46% | -0.022 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 04h | 1 | 0 | 0 | 1 | n/a | +0.090 % |
| 06h | 2 | 0 | 1 | 1 | 0% | -0.127 % |
| 07h | 8 | 5 | 0 | 3 | 100% | +0.118 % |
| 08h | 7 | 1 | 6 | 0 | 14% | -0.175 % |
| 09h | 5 | 1 | 3 | 1 | 25% | -0.145 % |
| 10h | 2 | 1 | 0 | 1 | 100% | +0.065 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
| 13h | 9 | 0 | 7 | 2 | 0% | -0.128 % |
| 14h | 15 | 6 | 7 | 2 | 46% | -0.009 % |
| 15h | 25 | 7 | 13 | 5 | 35% | -0.079 % |
| 16h | 9 | 2 | 5 | 2 | 29% | -0.015 % |
| 17h | 9 | 3 | 3 | 3 | 50% | +0.003 % |
| 18h | 11 | 6 | 3 | 2 | 67% | +0.043 % |
| 19h | 12 | 6 | 5 | 1 | 55% | +0.025 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 21h | 1 | 0 | 0 | 1 | n/a | -0.272 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 135 | 45 | 61 | 29 | 42% | -0.032 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 134 | 45 | 59 | 30 | 43% | -0.029 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 30, 63% terminés dans le bon sens, P&L moyen -0.004 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 315 | 94 | 162 | 59 | 37% | -0.038 % |
| corr | 16 | 2 | 11 | 3 | 15% | -0.176 % |
| level | 38 | 16 | 12 | 10 | 57% | -0.030 % |
| macd | 79 | 17 | 47 | 15 | 27% | -0.086 % |
| orb | 12 | 3 | 7 | 2 | 30% | -0.156 % |
| pdhl | 40 | 9 | 23 | 8 | 28% | -0.044 % |
| rsi | 206 | 64 | 114 | 28 | 36% | -0.041 % |
| trend_15m | 315 | 94 | 162 | 59 | 37% | -0.038 % |
| trend_1h | 308 | 91 | 160 | 57 | 36% | -0.039 % |
| trend_5m | 247 | 82 | 132 | 33 | 38% | -0.031 % |
| volume | 2 | 1 | 0 | 1 | 100% | -0.021 % |
| vwap | 306 | 94 | 156 | 56 | 38% | -0.036 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 22 | 7 | 3 | 12 | 70% | +0.021 % |
| ethereum | 13 | 2 | 8 | 3 | 20% | -0.203 % |
| euro | 23 | 8 | 14 | 1 | 36% | -0.024 % |
| gold | 52 | 17 | 25 | 10 | 40% | -0.019 % |
| nasdaq | 85 | 31 | 42 | 12 | 42% | -0.022 % |
| oil | 47 | 14 | 23 | 10 | 38% | -0.059 % |
| sp500 | 73 | 15 | 47 | 11 | 24% | -0.051 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 09/10 17:30 | Or (XAU/USD) | long | 4213.0 | 4213.8 | ⏱️ expiré | -0.00 % | 64 min |
| 09/10 17:01 | Nasdaq 100 (NQ) | short | 31076.5 | 31044.0 | ✅ TP | +0.09 % | 5 min |
| 09/10 15:45 | Or (XAU/USD) | long | 4213.6 | 4210.5 | ⏱️ expiré | -0.09 % | 60 min |
| 09/10 10:10 | Or (XAU/USD) | long | 4218.7 | 4212.3 | ❌ SL | -0.17 % | 39 min |
| 09/10 09:00 | Or (XAU/USD) | long | 4218.5 | 4217.1 | ⏱️ expiré | -0.05 % | 60 min |
| 09/10 08:10 | Bitcoin (BTC/USD) | long | 82381.0 | 82558.0 | ⏱️ expiré | +0.15 % | 60 min |
| 09/10 06:25 | Bitcoin (BTC/USD) | long | 82386.0 | 82510.0 | ⏱️ expiré | +0.09 % | 65 min |
| 08/10 23:30 | Bitcoin (BTC/USD) | short | 81615.0 | 81787.75 | ⏱️ expiré | -0.27 % | 60 min |
| 08/10 20:20 | Nasdaq 100 (NQ) | short | 30911.75 | 30950.75 | ❌ SL | -0.14 % | 4 min |
| 08/10 19:50 | Bitcoin (BTC/USD) | short | 80510.0 | 80718.0 | ❌ SL | -0.32 % | 4 min |
| 08/10 19:35 | S&P 500 (ES) | short | 7794.25 | 7799.5 | ❌ SL | -0.08 % | 1 min |
| 08/10 19:01 | S&P 500 (ES) | short | 7812.5 | 7804.0 | ✅ TP | +0.10 % | 0 min |
| 08/10 18:10 | Nasdaq 100 (NQ) | short | 31193.0 | 31220.5 | ❌ SL | -0.10 % | 6 min |
| 08/10 17:40 | Bitcoin (BTC/USD) | short | 81243.0 | 81445.0 | ❌ SL | -0.31 % | 9 min |
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

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.0 |
| trend_15m | 1.0 |
| trend_1h | 1.0 |
| adx | 1.0 |
| vwap | 0.75 |
| rsi | 1.0 |
| macd | 0.949 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.0 |
| corr | 0.5 |

Corrections par actif :

- sp500 : {'trend_5m': 0.988, 'trend_15m': 0.988, 'trend_1h': 0.988, 'adx': 0.988, 'vwap': 0.74}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 61 | -0.14 R | en test |
| horizon ~3 h | 63 | -0.40 R | en test |
| confiance moyenne | 48 | -0.06 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 5 | -0.18 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 7 | -0.39 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 7 | -0.58 R | en test |
| nouvel actif : Pétrole WTI (CL) | 47 | -0.10 R | en test |
| nouvel actif : Euro / dollar (6E) | 23 | -0.38 R | en test |

Notes :

- trades réels : +0,04 R ± 0,19 R par trade avant frais sur 136 trades (0 R = hasard)
- macd : -0,17 R ± 0,15 R sur 215 trades éq. → poids ×0,95
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,19 R contre -0,01 R en global sur 157 trades éq. → poids ×0,99 sur cet actif
- sp500, vwap : -0,19 R contre -0,00 R en global sur 151 trades éq. → poids ×0,99 sur cet actif
- variante « indices le matin européen » en test : 61 trades, -0,14 R net, encore 39 trades avant décision
- variante « horizon ~3 h » en test : 63 trades, -0,40 R net, encore 37 trades avant décision
- variante « confiance moyenne » en test : 48 trades, -0,06 R net, encore 52 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 5 trades, -0,18 R net, encore 95 trades avant décision
- variante « reprise juste après un stop » en test : 28 trades, -0,31 R net, encore 72 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 7 trades, -0,39 R net, encore 93 trades avant décision
- variante « horizon ~3 h sur Or (XAU/USD) » en test : 7 trades, -0,58 R net, encore 93 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 47 trades, -0,10 R net, encore 53 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 23 trades, -0,38 R net, encore 77 trades avant décision
- sortie : stop remonté à l'entrée après +0,5 R ferait mieux (-0,15 R net contre -0,23 R, réels et en ombre) : à décider
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
