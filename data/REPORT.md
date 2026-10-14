# Trading-Bot — rapport

_Mis à jour le 14/10/2026 à 20:25 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **149**
- Taux de réussite cumulé (TP / (TP+SL)) : **44%** — hasard attendu 42%, avantage **+2%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-3.17 %** (brut +0.68 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **445** clôturés, 14 ouverts, taux de réussite 41% (hasard attendu 40%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 46 | 21 | 19 | 6 | 52% | +0.037 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 75 | 20 | 32 | 23 | 38% | -0.037 % |
| short | 74 | 30 | 32 | 12 | 48% | -0.005 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 145 | 49 | 62 | 34 | 44% | -0.020 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 148 | 50 | 64 | 34 | 44% | -0.020 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 18 | 4 | 10 | 4 | 29% | -0.036 % |
| macd | 46 | 11 | 24 | 11 | 31% | -0.073 % |
| orb | 17 | 3 | 9 | 5 | 25% | -0.073 % |
| pdhl | 23 | 8 | 11 | 4 | 42% | -0.032 % |
| rsi | 127 | 45 | 51 | 31 | 47% | -0.008 % |
| trend_15m | 148 | 50 | 64 | 34 | 44% | -0.020 % |
| trend_1h | 148 | 50 | 64 | 34 | 44% | -0.020 % |
| trend_5m | 132 | 46 | 55 | 31 | 46% | -0.013 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 146 | 50 | 62 | 34 | 45% | -0.016 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 68 | 21 | 30 | 17 | 41% | -0.023 % |
| actualité chargée | 81 | 29 | 34 | 18 | 46% | -0.020 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 04h | 1 | 0 | 0 | 1 | n/a | +0.090 % |
| 05h | 1 | 0 | 0 | 1 | n/a | +0.182 % |
| 06h | 2 | 0 | 1 | 1 | 0% | -0.127 % |
| 07h | 8 | 5 | 0 | 3 | 100% | +0.118 % |
| 08h | 7 | 1 | 6 | 0 | 14% | -0.175 % |
| 09h | 5 | 1 | 3 | 1 | 25% | -0.145 % |
| 10h | 2 | 1 | 0 | 1 | 100% | +0.065 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
| 13h | 9 | 0 | 7 | 2 | 0% | -0.128 % |
| 14h | 20 | 8 | 8 | 4 | 50% | +0.020 % |
| 15h | 27 | 9 | 13 | 5 | 41% | -0.044 % |
| 16h | 10 | 2 | 5 | 3 | 29% | -0.017 % |
| 17h | 10 | 3 | 4 | 3 | 43% | -0.007 % |
| 18h | 12 | 7 | 3 | 2 | 70% | +0.046 % |
| 19h | 14 | 6 | 6 | 2 | 50% | +0.011 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 21h | 1 | 0 | 0 | 1 | n/a | -0.272 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 148 | 50 | 64 | 34 | 44% | -0.020 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 2 | 2 | 0 | 0 | 100% | +0.618 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 35, 57% terminés dans le bon sens, P&L moyen -0.005 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 445 | 152 | 217 | 76 | 41% | +0.016 % |
| corr | 24 | 4 | 17 | 3 | 19% | -0.150 % |
| level | 44 | 18 | 13 | 13 | 58% | -0.028 % |
| macd | 105 | 27 | 60 | 18 | 31% | -0.046 % |
| orb | 21 | 9 | 7 | 5 | 56% | +0.030 % |
| pdhl | 60 | 20 | 30 | 10 | 40% | +0.112 % |
| rsi | 312 | 118 | 155 | 39 | 43% | +0.034 % |
| trend_15m | 445 | 152 | 217 | 76 | 41% | +0.016 % |
| trend_1h | 437 | 149 | 215 | 73 | 41% | +0.016 % |
| trend_5m | 365 | 138 | 182 | 45 | 43% | +0.032 % |
| volume | 2 | 1 | 0 | 1 | 100% | -0.021 % |
| vwap | 431 | 150 | 209 | 72 | 42% | +0.019 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 22 | 7 | 3 | 12 | 70% | +0.021 % |
| ethereum | 15 | 2 | 10 | 3 | 17% | -0.231 % |
| euro | 23 | 8 | 14 | 1 | 36% | -0.024 % |
| gold | 101 | 24 | 58 | 19 | 29% | -0.049 % |
| nasdaq | 143 | 73 | 54 | 16 | 57% | +0.157 % |
| oil | 58 | 17 | 28 | 13 | 38% | -0.058 % |
| sp500 | 83 | 21 | 50 | 12 | 30% | -0.041 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 14/10 17:31 | Nasdaq 100 (NQ) | short | 30405.0 | 30215.0 | ✅ TP | +0.61 % | 52 min |
| 14/10 16:10 | Nasdaq 100 (NQ) | short | 30489.0 | 30296.5 | ✅ TP | +0.62 % | 119 min |
| 13/10 17:05 | Nasdaq 100 (NQ) | short | 30700.0 | 30644.25 | ✅ TP | +0.17 % | 29 min |
| 13/10 07:35 | Bitcoin (BTC/USD) | long | 83542.0 | 83743.99 | ⏱️ expiré | +0.18 % | 60 min |
| 12/10 21:01 | Or (XAU/USD) | short | 4190.9 | 4192.9 | ⏱️ expiré | -0.07 % | 64 min |
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

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.046 |
| trend_15m | 1.046 |
| trend_1h | 1.046 |
| adx | 1.046 |
| vwap | 0.802 |
| rsi | 1.115 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.0 |
| corr | 0.5 |

Corrections par actif :

- ethereum : {'trend_5m': 0.857, 'trend_15m': 0.857, 'trend_1h': 0.857, 'adx': 0.857, 'rsi': 0.839}
- gold : {'trend_5m': 0.97, 'trend_15m': 0.97, 'trend_1h': 0.97, 'adx': 0.97, 'vwap': 0.725, 'rsi': 0.969}
- nasdaq : {'trend_5m': 1.5, 'trend_15m': 1.5, 'trend_1h': 1.5, 'adx': 1.5, 'vwap': 1.203, 'rsi': 1.5, 'macd': 1.043, 'pdhl': 1.049}
- sp500 : {'trend_5m': 0.9, 'trend_15m': 0.9, 'trend_1h': 0.9, 'adx': 0.9, 'vwap': 0.682, 'rsi': 0.972}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 70 | -0.13 R | en test |
| horizon ~3 h | 70 | -0.34 R | en test |
| confiance moyenne | 56 | -0.11 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 10 | +1.40 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 9 | +0.44 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 0 | n/a | en test |
| nouvel actif : Ethereum (ETH/USD) | 9 | -0.58 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 12 | -0.59 R | en test |
| nouvel actif : Pétrole WTI (CL) | 58 | -0.12 R | en test |
| nouvel actif : Euro / dollar (6E) | 23 | -0.38 R | en test |

Notes :

- trades réels : +0,08 R ± 0,19 R par trade avant frais sur 149 trades (0 R = hasard)
- tendance (trend_5m, trend_15m, trend_1h, adx) : +0,10 R ± 0,08 R sur 987 trades éq. → poids ×1,05
- vwap : +0,11 R ± 0,08 R sur 897 trades éq. → poids ×1,07
- rsi : +0,13 R ± 0,09 R sur 783 trades éq. → poids ×1,12
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,23 R contre +0,10 R en global sur 59 trades éq. → poids ×0,82 sur cet actif
- ethereum, rsi : -0,27 R contre +0,13 R en global sur 40 trades éq. → poids ×0,75 sur cet actif
- gold, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,08 R contre +0,10 R en global sur 215 trades éq. → poids ×0,93 sur cet actif
- gold, vwap : -0,07 R contre +0,11 R en global sur 214 trades éq. → poids ×0,90 sur cet actif
- gold, rsi : -0,08 R contre +0,13 R en global sur 169 trades éq. → poids ×0,87 sur cet actif
- nasdaq, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,51 R contre +0,10 R en global sur 236 trades éq. → poids ×1,50 sur cet actif
- nasdaq, vwap : +0,53 R contre +0,11 R en global sur 228 trades éq. → poids ×1,50 sur cet actif
- nasdaq, rsi : +0,61 R contre +0,13 R en global sur 186 trades éq. → poids ×1,50 sur cet actif
- nasdaq, macd : +0,31 R contre -0,08 R en global sur 58 trades éq. → poids ×1,04 sur cet actif
- nasdaq, pdhl : +0,68 R contre +0,13 R en global sur 33 trades éq. → poids ×1,05 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,13 R contre +0,10 R en global sur 175 trades éq. → poids ×0,86 sur cet actif
- sp500, vwap : -0,12 R contre +0,11 R en global sur 170 trades éq. → poids ×0,85 sur cet actif
- sp500, rsi : -0,10 R contre +0,13 R en global sur 148 trades éq. → poids ×0,87 sur cet actif
- variante « indices le matin européen » en test : 70 trades, -0,13 R net, encore 30 trades avant décision
- variante « horizon ~3 h » en test : 70 trades, -0,34 R net, encore 30 trades avant décision
- variante « confiance moyenne » en test : 56 trades, -0,11 R net, encore 44 trades avant décision

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
