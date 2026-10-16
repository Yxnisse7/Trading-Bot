# Trading-Bot — rapport

_Mis à jour le 16/10/2026 à 19:21 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **152**
- Taux de réussite cumulé (TP / (TP+SL)) : **44%** — hasard attendu 41%, avantage **+3%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-1.80 %** (brut +2.08 %)
- Signaux ouverts : **2**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **529** clôturés, 8 ouverts, taux de réussite 40% (hasard attendu 39%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 16/10 18:25 | Nasdaq 100 (NQ) | short | 29682.5 | 29483.5 | 29749.0 | fort | signaux du bot | 18:25 |
| 16/10 19:10 | Nasdaq 100 (NQ) | short | 29599.5 | 29401.5 | 29665.5 | fort | signaux du bot | 19:10 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 49 | 23 | 20 | 6 | 53% | +0.062 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 75 | 20 | 32 | 23 | 38% | -0.037 % |
| short | 77 | 32 | 33 | 12 | 49% | +0.013 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 148 | 51 | 63 | 34 | 45% | -0.010 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 151 | 52 | 65 | 34 | 44% | -0.011 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 18 | 4 | 10 | 4 | 29% | -0.036 % |
| macd | 46 | 11 | 24 | 11 | 31% | -0.073 % |
| orb | 17 | 3 | 9 | 5 | 25% | -0.073 % |
| pdhl | 23 | 8 | 11 | 4 | 42% | -0.032 % |
| rsi | 130 | 47 | 52 | 31 | 47% | +0.003 % |
| trend_15m | 151 | 52 | 65 | 34 | 44% | -0.011 % |
| trend_1h | 151 | 52 | 65 | 34 | 44% | -0.011 % |
| trend_5m | 135 | 48 | 56 | 31 | 46% | -0.002 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 149 | 52 | 63 | 34 | 45% | -0.007 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 68 | 21 | 30 | 17 | 41% | -0.023 % |
| actualité chargée | 84 | 31 | 35 | 18 | 47% | -0.003 % |

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
| 15h | 29 | 11 | 13 | 5 | 46% | +0.013 % |
| 16h | 10 | 2 | 5 | 3 | 29% | -0.017 % |
| 17h | 10 | 3 | 4 | 3 | 43% | -0.007 % |
| 18h | 12 | 7 | 3 | 2 | 70% | +0.046 % |
| 19h | 15 | 6 | 7 | 2 | 46% | -0.003 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 21h | 1 | 0 | 0 | 1 | n/a | -0.272 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 151 | 52 | 65 | 34 | 44% | -0.011 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 5 | 4 | 1 | 0 | 80% | +0.520 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 35, 57% terminés dans le bon sens, P&L moyen -0.005 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 529 | 179 | 268 | 82 | 40% | +0.006 % |
| corr | 37 | 7 | 24 | 6 | 23% | -0.162 % |
| level | 47 | 19 | 15 | 13 | 56% | -0.034 % |
| macd | 135 | 32 | 81 | 22 | 28% | -0.072 % |
| orb | 21 | 9 | 7 | 5 | 56% | +0.030 % |
| pdhl | 68 | 20 | 38 | 10 | 34% | +0.072 % |
| rsi | 384 | 143 | 199 | 42 | 42% | +0.020 % |
| trend_15m | 529 | 179 | 268 | 82 | 40% | +0.006 % |
| trend_1h | 521 | 176 | 266 | 79 | 40% | +0.006 % |
| trend_5m | 445 | 164 | 232 | 49 | 41% | +0.018 % |
| volume | 8 | 1 | 5 | 2 | 17% | -0.236 % |
| vwap | 514 | 177 | 260 | 77 | 41% | +0.009 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 29 | 9 | 8 | 12 | 53% | -0.015 % |
| ethereum | 27 | 4 | 16 | 7 | 20% | -0.211 % |
| euro | 34 | 11 | 22 | 1 | 33% | -0.026 % |
| gold | 104 | 26 | 58 | 20 | 31% | -0.043 % |
| nasdaq | 185 | 86 | 83 | 16 | 51% | +0.117 % |
| oil | 62 | 18 | 30 | 14 | 38% | -0.059 % |
| sp500 | 88 | 25 | 51 | 12 | 33% | -0.035 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 16/10 17:55 | Nasdaq 100 (NQ) | short | 29730.75 | 29496.75 | ✅ TP | +0.78 % | 72 min |
| 16/10 17:50 | Nasdaq 100 (NQ) | short | 29734.75 | 29496.25 | ✅ TP | +0.79 % | 77 min |
| 14/10 21:01 | Nasdaq 100 (NQ) | short | 30159.0 | 30218.0 | ❌ SL | -0.21 % | 29 min |
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

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.063 |
| trend_15m | 1.063 |
| trend_1h | 1.063 |
| adx | 1.063 |
| vwap | 0.812 |
| rsi | 1.139 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.0 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [11]

Corrections par actif :

- ethereum : {'trend_5m': 0.767, 'trend_15m': 0.767, 'trend_1h': 0.767, 'adx': 0.767, 'vwap': 0.792, 'rsi': 0.699}
- euro : {'trend_5m': 1.024, 'trend_15m': 1.024, 'trend_1h': 1.024, 'adx': 1.024}
- gold : {'trend_5m': 1.014, 'trend_15m': 1.014, 'trend_1h': 1.014, 'adx': 1.014, 'vwap': 0.748, 'rsi': 1.004}
- nasdaq : {'trend_5m': 1.5, 'trend_15m': 1.5, 'trend_1h': 1.5, 'adx': 1.5, 'vwap': 1.212, 'rsi': 1.5}
- sp500 : {'trend_5m': 0.974, 'trend_15m': 0.974, 'trend_1h': 0.974, 'adx': 0.974, 'vwap': 0.74, 'rsi': 1.032}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 82 | -0.26 R | en test |
| horizon ~3 h | 75 | -0.40 R | en test |
| confiance moyenne | 57 | -0.09 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 11 | +1.54 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 14 | +0.57 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 7 | -0.50 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 21 | -0.51 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 12 | -0.59 R | en test |
| nouvel actif : Pétrole WTI (CL) | 62 | -0.13 R | en test |
| nouvel actif : Euro / dollar (6E) | 34 | -0.43 R | en test |

Notes :

- trades réels : +0,11 R ± 0,19 R par trade avant frais sur 152 trades (0 R = hasard)
- tendance (trend_5m, trend_15m, trend_1h, adx) : +0,10 R ± 0,08 R sur 1073 trades éq. → poids ×1,06
- vwap : +0,11 R ± 0,08 R sur 982 trades éq. → poids ×1,08
- rsi : +0,14 R ± 0,09 R sur 857 trades éq. → poids ×1,14
- tranche 11h UTC : -0,29 R sur 76 trades éq. → évitée
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,24 R contre +0,10 R en global sur 71 trades éq. → poids ×0,72 sur cet actif
- ethereum, vwap : -0,23 R contre +0,11 R en global sur 35 trades éq. → poids ×0,98 sur cet actif
- ethereum, rsi : -0,28 R contre +0,14 R en global sur 50 trades éq. → poids ×0,61 sur cet actif
- euro, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,22 R contre +0,10 R en global sur 59 trades éq. → poids ×0,96 sur cet actif
- gold, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,06 R contre +0,10 R en global sur 218 trades éq. → poids ×0,95 sur cet actif
- gold, vwap : -0,06 R contre +0,11 R en global sur 216 trades éq. → poids ×0,92 sur cet actif
- gold, rsi : -0,06 R contre +0,14 R en global sur 171 trades éq. → poids ×0,88 sur cet actif
- nasdaq, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,49 R contre +0,10 R en global sur 280 trades éq. → poids ×1,50 sur cet actif
- nasdaq, vwap : +0,50 R contre +0,11 R en global sur 272 trades éq. → poids ×1,49 sur cet actif
- nasdaq, rsi : +0,58 R contre +0,14 R en global sur 227 trades éq. → poids ×1,50 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,10 R contre +0,10 R en global sur 180 trades éq. → poids ×0,92 sur cet actif
- sp500, vwap : -0,09 R contre +0,11 R en global sur 175 trades éq. → poids ×0,91 sur cet actif
- sp500, rsi : -0,08 R contre +0,14 R en global sur 152 trades éq. → poids ×0,91 sur cet actif
- variante « indices le matin européen » en test : 82 trades, -0,26 R net, encore 18 trades avant décision
- variante « horizon ~3 h » en test : 75 trades, -0,40 R net, encore 25 trades avant décision

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
