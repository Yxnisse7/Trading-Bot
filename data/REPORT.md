# Trading-Bot — rapport

_Mis à jour le 08/10/2026 à 21:25 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **128**
- Taux de réussite cumulé (TP / (TP+SL)) : **42%** — hasard attendu 42%, avantage **+1%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-4.22 %** (brut -0.85 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **292** clôturés, 2 ouverts, taux de réussite 36% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 20 | 6 | 9 | 5 | 40% | -0.068 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 32 | 13 | 16 | 3 | 45% | -0.026 % |
| nasdaq | 38 | 15 | 17 | 6 | 47% | +0.005 % |
| sp500 | 27 | 8 | 12 | 7 | 40% | -0.015 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 67 | 20 | 30 | 17 | 40% | -0.042 % |
| short | 61 | 24 | 30 | 7 | 44% | -0.023 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 124 | 43 | 58 | 23 | 43% | -0.032 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 127 | 44 | 60 | 23 | 42% | -0.032 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 15 | 4 | 9 | 2 | 31% | -0.044 % |
| macd | 37 | 9 | 23 | 5 | 28% | -0.094 % |
| orb | 14 | 3 | 8 | 3 | 27% | -0.069 % |
| pdhl | 23 | 8 | 11 | 4 | 42% | -0.032 % |
| rsi | 109 | 39 | 49 | 21 | 44% | -0.023 % |
| trend_15m | 127 | 44 | 60 | 23 | 42% | -0.032 % |
| trend_1h | 127 | 44 | 60 | 23 | 42% | -0.032 % |
| trend_5m | 115 | 41 | 51 | 23 | 45% | -0.026 % |
| volume | 5 | 2 | 3 | 0 | 40% | -0.083 % |
| vwap | 125 | 44 | 58 | 23 | 43% | -0.028 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 53 | 16 | 27 | 10 | 37% | -0.050 % |
| actualité chargée | 75 | 28 | 33 | 14 | 46% | -0.021 % |

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
| 15h | 23 | 6 | 13 | 4 | 32% | -0.090 % |
| 16h | 9 | 2 | 5 | 2 | 29% | -0.015 % |
| 17h | 9 | 3 | 3 | 3 | 50% | +0.003 % |
| 18h | 11 | 6 | 3 | 2 | 67% | +0.043 % |
| 19h | 12 | 6 | 5 | 1 | 55% | +0.025 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 127 | 44 | 60 | 23 | 42% | -0.032 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 126 | 44 | 58 | 24 | 43% | -0.029 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 24, 67% terminés dans le bon sens, P&L moyen +0.002 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 292 | 87 | 157 | 48 | 36% | -0.041 % |
| corr | 16 | 2 | 11 | 3 | 15% | -0.176 % |
| level | 32 | 11 | 12 | 9 | 48% | -0.070 % |
| macd | 77 | 17 | 46 | 14 | 27% | -0.082 % |
| orb | 12 | 3 | 7 | 2 | 30% | -0.156 % |
| pdhl | 39 | 9 | 22 | 8 | 29% | -0.043 % |
| rsi | 197 | 62 | 110 | 25 | 36% | -0.040 % |
| trend_15m | 292 | 87 | 157 | 48 | 36% | -0.041 % |
| trend_1h | 285 | 84 | 155 | 46 | 35% | -0.042 % |
| trend_5m | 236 | 80 | 127 | 29 | 39% | -0.029 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 285 | 87 | 151 | 47 | 37% | -0.038 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 15 | 4 | 3 | 8 | 57% | +0.030 % |
| ethereum | 13 | 2 | 8 | 3 | 20% | -0.203 % |
| euro | 23 | 8 | 14 | 1 | 36% | -0.024 % |
| gold | 46 | 15 | 25 | 6 | 38% | -0.028 % |
| nasdaq | 76 | 29 | 38 | 9 | 43% | -0.019 % |
| oil | 47 | 14 | 23 | 10 | 38% | -0.059 % |
| sp500 | 72 | 15 | 46 | 11 | 25% | -0.050 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 02/10 20:05 | Bitcoin (BTC/USD) | short | 84854.0 | 84531.0 | ✅ TP | +0.32 % | 26 min |
| 02/10 19:15 | Bitcoin (BTC/USD) | short | 84893.0 | 84574.0 | ✅ TP | +0.32 % | 8 min |
| 02/10 18:20 | Bitcoin (BTC/USD) | short | 85304.0 | 84974.0 | ✅ TP | +0.33 % | 53 min |
| 02/10 17:55 | Or (XAU/USD) | short | 4161.0 | 4153.9 | ✅ TP | +0.15 % | 1 min |
| 02/10 17:01 | Nasdaq 100 (NQ) | long | 31213.25 | 31154.0 | ❌ SL | -0.20 % | 0 min |
| 02/10 15:55 | Nasdaq 100 (NQ) | long | 31178.5 | 31212.75 | ⏱️ expiré | +0.10 % | 65 min |
| 02/10 15:35 | S&P 500 (ES) | long | 7789.75 | 7776.75 | ❌ SL | -0.18 % | 20 min |
| 01/10 20:20 | Nasdaq 100 (NQ) | short | 30714.5 | 30764.75 | ❌ SL | -0.17 % | 2 min |

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.0 |
| trend_15m | 1.0 |
| trend_1h | 1.0 |
| adx | 1.0 |
| vwap | 0.75 |
| rsi | 1.0 |
| macd | 0.984 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.0 |
| corr | 0.5 |

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 59 | -0.18 R | en test |
| horizon ~3 h | 59 | -0.36 R | en test |
| confiance moyenne | 35 | -0.23 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 5 | -0.18 R | en test |
| reprise juste après un stop | 26 | -0.31 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 7 | -0.39 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 5 | -0.66 R | en test |
| nouvel actif : Pétrole WTI (CL) | 47 | -0.10 R | en test |
| nouvel actif : Euro / dollar (6E) | 23 | -0.38 R | en test |

Notes :

- trades réels : +0,04 R ± 0,20 R par trade avant frais sur 128 trades (0 R = hasard)
- macd : -0,16 R ± 0,15 R sur 212 trades éq. → poids ×0,98
- variante « indices le matin européen » en test : 59 trades, -0,18 R net, encore 41 trades avant décision
- variante « horizon ~3 h » en test : 59 trades, -0,36 R net, encore 41 trades avant décision
- variante « confiance moyenne » en test : 35 trades, -0,23 R net, encore 65 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 5 trades, -0,18 R net, encore 95 trades avant décision
- variante « reprise juste après un stop » en test : 26 trades, -0,31 R net, encore 74 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 7 trades, -0,39 R net, encore 93 trades avant décision
- variante « horizon ~3 h sur Or (XAU/USD) » en test : 5 trades, -0,66 R net, encore 95 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 47 trades, -0,10 R net, encore 53 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 23 trades, -0,38 R net, encore 77 trades avant décision
- sortie : stop remonté à l'entrée après +0,5 R ferait mieux (-0,18 R net contre -0,27 R, réels et en ombre) : à décider
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
