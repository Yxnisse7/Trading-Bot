# Trading-Bot — rapport

_Mis à jour le 12/10/2026 à 21:25 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **144**
- Taux de réussite cumulé (TP / (TP+SL)) : **42%** — hasard attendu 42%, avantage **+1%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-4.69 %** (brut -0.95 %)
- Signaux ouverts : **1**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **332** clôturés, 1 ouverts, taux de réussite 37% (hasard attendu 42%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 12/10 21:01 | Or (XAU/USD) | short | 4190.9 | 4184.2 | 4195.8 | fort | signaux du bot | 22:01 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 23 | 6 | 9 | 8 | 40% | -0.060 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 38 | 13 | 17 | 8 | 43% | -0.033 % |
| nasdaq | 43 | 18 | 19 | 6 | 49% | +0.007 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 74 | 20 | 32 | 22 | 38% | -0.040 % |
| short | 70 | 27 | 32 | 11 | 46% | -0.024 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 140 | 46 | 62 | 32 | 43% | -0.031 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 143 | 47 | 64 | 32 | 42% | -0.032 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 17 | 4 | 10 | 3 | 29% | -0.049 % |
| macd | 43 | 9 | 24 | 10 | 27% | -0.095 % |
| orb | 17 | 3 | 9 | 5 | 25% | -0.073 % |
| pdhl | 23 | 8 | 11 | 4 | 42% | -0.032 % |
| rsi | 122 | 42 | 51 | 29 | 45% | -0.021 % |
| trend_15m | 143 | 47 | 64 | 32 | 42% | -0.032 % |
| trend_1h | 143 | 47 | 64 | 32 | 42% | -0.032 % |
| trend_5m | 129 | 44 | 55 | 30 | 44% | -0.024 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 141 | 47 | 62 | 32 | 43% | -0.028 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 64 | 18 | 30 | 16 | 38% | -0.046 % |
| actualité chargée | 80 | 29 | 34 | 17 | 46% | -0.022 % |

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
| 14h | 19 | 7 | 8 | 4 | 47% | -0.011 % |
| 15h | 25 | 7 | 13 | 5 | 35% | -0.079 % |
| 16h | 10 | 2 | 5 | 3 | 29% | -0.017 % |
| 17h | 10 | 3 | 4 | 3 | 43% | -0.007 % |
| 18h | 12 | 7 | 3 | 2 | 70% | +0.046 % |
| 19h | 13 | 6 | 6 | 1 | 50% | +0.017 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 21h | 1 | 0 | 0 | 1 | n/a | -0.272 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 143 | 47 | 64 | 32 | 42% | -0.032 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 142 | 47 | 62 | 33 | 43% | -0.029 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 33, 58% terminés dans le bon sens, P&L moyen -0.008 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 332 | 96 | 167 | 69 | 37% | -0.038 % |
| corr | 16 | 2 | 11 | 3 | 15% | -0.176 % |
| level | 41 | 16 | 12 | 13 | 57% | -0.035 % |
| macd | 82 | 17 | 49 | 16 | 26% | -0.084 % |
| orb | 15 | 3 | 7 | 5 | 30% | -0.105 % |
| pdhl | 42 | 9 | 24 | 9 | 27% | -0.048 % |
| rsi | 214 | 66 | 116 | 32 | 36% | -0.041 % |
| trend_15m | 332 | 96 | 167 | 69 | 37% | -0.038 % |
| trend_1h | 324 | 93 | 165 | 66 | 36% | -0.039 % |
| trend_5m | 258 | 84 | 136 | 38 | 38% | -0.032 % |
| volume | 2 | 1 | 0 | 1 | 100% | -0.021 % |
| vwap | 322 | 96 | 161 | 65 | 37% | -0.036 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 22 | 7 | 3 | 12 | 70% | +0.021 % |
| ethereum | 13 | 2 | 8 | 3 | 20% | -0.203 % |
| euro | 23 | 8 | 14 | 1 | 36% | -0.024 % |
| gold | 61 | 18 | 27 | 16 | 40% | -0.018 % |
| nasdaq | 89 | 32 | 43 | 14 | 43% | -0.018 % |
| oil | 50 | 14 | 25 | 11 | 36% | -0.070 % |
| sp500 | 74 | 15 | 47 | 12 | 24% | -0.050 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 12/10 20:55 | Nasdaq 100 (NQ) | short | 30883.75 | 30857.25 | ✅ TP | +0.08 % | 5 min |
| 12/10 18:10 | Or (XAU/USD) | short | 4188.9 | 4189.6 | ⏱️ expiré | -0.04 % | 65 min |
| 12/10 16:50 | Nasdaq 100 (NQ) | short | 30889.75 | 30934.5 | ❌ SL | -0.15 % | 53 min |
| 12/10 16:25 | S&P 500 (ES) | short | 7856.5 | 7859.0 | ⏱️ expiré | -0.04 % | 65 min |
| 12/10 16:25 | Or (XAU/USD) | short | 4191.6 | 4193.7 | ⏱️ expiré | -0.07 % | 65 min |
| 12/10 16:15 | Nasdaq 100 (NQ) | short | 30943.75 | 30882.75 | ✅ TP | +0.19 % | 5 min |
| 09/10 21:30 | S&P 500 (ES) | long | 7868.5 | 7863.0 | ❌ SL | -0.08 % | 9 min |
| 09/10 19:30 | Nasdaq 100 (NQ) | short | 31078.0 | 31106.0 | ❌ SL | -0.10 % | 39 min |
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

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.0 |
| trend_15m | 1.0 |
| trend_1h | 1.0 |
| adx | 1.0 |
| vwap | 0.75 |
| rsi | 1.0 |
| macd | 0.914 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.0 |
| corr | 0.5 |

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 63 | -0.15 R | en test |
| horizon ~3 h | 66 | -0.36 R | en test |
| confiance moyenne | 54 | -0.07 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 5 | -0.18 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 7 | -0.39 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 10 | -0.49 R | en test |
| nouvel actif : Pétrole WTI (CL) | 50 | -0.14 R | en test |
| nouvel actif : Euro / dollar (6E) | 23 | -0.38 R | en test |

Notes :

- trades réels : +0,03 R ± 0,18 R par trade avant frais sur 144 trades (0 R = hasard)
- macd : -0,17 R ± 0,14 R sur 229 trades éq. → poids ×0,91
- variante « indices le matin européen » en test : 63 trades, -0,15 R net, encore 37 trades avant décision
- variante « horizon ~3 h » en test : 66 trades, -0,36 R net, encore 34 trades avant décision
- variante « confiance moyenne » en test : 54 trades, -0,07 R net, encore 46 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 5 trades, -0,18 R net, encore 95 trades avant décision
- variante « reprise juste après un stop » en test : 28 trades, -0,31 R net, encore 72 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 7 trades, -0,39 R net, encore 93 trades avant décision
- variante « horizon ~3 h sur Or (XAU/USD) » en test : 10 trades, -0,49 R net, encore 90 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 50 trades, -0,14 R net, encore 50 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 23 trades, -0,38 R net, encore 77 trades avant décision
- sortie : stop remonté à l'entrée après +0,5 R ferait mieux (-0,15 R net contre -0,22 R, réels et en ombre) : à décider

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 11/10/2026 | 98 | 25 | 47 | 26 | 35% | 41% | -7% | -1.17 % | -0.012 % |
| S&P 500 (ES) | 09/07/2026 → 11/10/2026 | 115 | 42 | 54 | 19 | 44% | 42% | +2% | -0.10 % | -0.001 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 11/10/2026 | 59 | 22 | 25 | 12 | 47% | 40% | +6% | -1.00 % | -0.017 % |
| Ethereum (ETH/USD) | 20/07/2026 → 11/10/2026 | 58 | 12 | 28 | 18 | 30% | 40% | -10% | -6.67 % | -0.115 % |
| Or (XAU/USD) | 09/07/2026 → 11/10/2026 | 139 | 45 | 58 | 36 | 44% | 42% | +2% | -2.31 % | -0.017 % |
| Pétrole WTI (CL) | 14/07/2026 → 11/10/2026 | 193 | 64 | 88 | 41 | 42% | 41% | +1% | +3.61 % | +0.019 % |
| Euro / dollar (6E) | 14/07/2026 → 11/10/2026 | 35 | 9 | 22 | 4 | 29% | 40% | -11% | -0.86 % | -0.024 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
