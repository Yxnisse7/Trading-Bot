# Trading-Bot — rapport

_Mis à jour le 20/10/2026 à 19:31 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **154**
- Taux de réussite cumulé (TP / (TP+SL)) : **45%** — hasard attendu 41%, avantage **+4%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-0.48 %** (brut +3.42 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **613** clôturés, 2 ouverts, taux de réussite 39% (hasard attendu 38%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 51 | 25 | 20 | 6 | 56% | +0.086 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 75 | 20 | 32 | 23 | 38% | -0.037 % |
| short | 79 | 34 | 33 | 12 | 51% | +0.029 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 150 | 53 | 63 | 34 | 46% | -0.001 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 153 | 54 | 65 | 34 | 45% | -0.002 % |
| corr | 15 | 5 | 6 | 4 | 45% | +0.017 % |
| level | 18 | 4 | 10 | 4 | 29% | -0.036 % |
| macd | 46 | 11 | 24 | 11 | 31% | -0.073 % |
| orb | 17 | 3 | 9 | 5 | 25% | -0.073 % |
| pdhl | 24 | 9 | 11 | 4 | 45% | -0.003 % |
| rsi | 132 | 49 | 52 | 31 | 49% | +0.013 % |
| trend_15m | 153 | 54 | 65 | 34 | 45% | -0.002 % |
| trend_1h | 153 | 54 | 65 | 34 | 45% | -0.002 % |
| trend_5m | 137 | 50 | 56 | 31 | 47% | +0.007 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 151 | 54 | 63 | 34 | 46% | +0.002 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 69 | 22 | 30 | 17 | 42% | -0.013 % |
| actualité chargée | 85 | 32 | 35 | 18 | 48% | +0.005 % |

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
| 16h | 11 | 3 | 5 | 3 | 38% | +0.044 % |
| 17h | 11 | 4 | 4 | 3 | 50% | +0.053 % |
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
| signaux du bot | 153 | 54 | 65 | 34 | 45% | -0.002 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 7 | 6 | 1 | 0 | 86% | +0.560 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 35, 57% terminés dans le bon sens, P&L moyen -0.005 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 613 | 202 | 312 | 99 | 39% | +0.006 % |
| corr | 53 | 11 | 30 | 12 | 27% | -0.085 % |
| level | 47 | 19 | 15 | 13 | 56% | -0.034 % |
| macd | 155 | 37 | 95 | 23 | 28% | -0.064 % |
| orb | 21 | 9 | 7 | 5 | 56% | +0.030 % |
| pdhl | 82 | 30 | 42 | 10 | 42% | +0.087 % |
| rsi | 451 | 162 | 230 | 59 | 41% | +0.020 % |
| trend_15m | 613 | 202 | 312 | 99 | 39% | +0.006 % |
| trend_1h | 604 | 199 | 309 | 96 | 39% | +0.006 % |
| trend_5m | 523 | 186 | 271 | 66 | 41% | +0.018 % |
| volume | 8 | 1 | 5 | 2 | 17% | -0.236 % |
| vwap | 598 | 200 | 304 | 94 | 40% | +0.007 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 29 | 9 | 8 | 12 | 53% | -0.015 % |
| ethereum | 27 | 4 | 16 | 7 | 20% | -0.211 % |
| euro | 34 | 11 | 22 | 1 | 33% | -0.026 % |
| gold | 122 | 34 | 67 | 21 | 34% | -0.036 % |
| nasdaq | 230 | 95 | 104 | 31 | 48% | +0.101 % |
| oil | 77 | 23 | 39 | 15 | 37% | -0.062 % |
| sp500 | 94 | 26 | 56 | 12 | 32% | -0.038 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 16/10 19:10 | Nasdaq 100 (NQ) | short | 29599.5 | 29401.5 | ✅ TP | +0.66 % | 53 min |
| 16/10 18:25 | Nasdaq 100 (NQ) | short | 29682.5 | 29483.5 | ✅ TP | +0.66 % | 49 min |
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

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.072 |
| trend_15m | 1.072 |
| trend_1h | 1.072 |
| adx | 1.072 |
| vwap | 0.819 |
| rsi | 1.165 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.0 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [11]

Corrections par actif :

- ethereum : {'trend_5m': 0.734, 'trend_15m': 0.734, 'trend_1h': 0.734, 'adx': 0.734, 'vwap': 0.8, 'rsi': 0.641}
- euro : {'trend_5m': 0.972, 'trend_15m': 0.972, 'trend_1h': 0.972, 'adx': 0.972, 'vwap': 0.783}
- gold : {'trend_5m': 1.023, 'trend_15m': 1.023, 'trend_1h': 1.023, 'adx': 1.023, 'vwap': 0.756, 'rsi': 0.991}
- nasdaq : {'trend_5m': 1.5, 'trend_15m': 1.5, 'trend_1h': 1.5, 'adx': 1.5, 'vwap': 1.226, 'rsi': 1.5, 'pdhl': 1.045}
- sp500 : {'trend_5m': 0.932, 'trend_15m': 0.932, 'trend_1h': 0.932, 'adx': 0.932, 'vwap': 0.7, 'rsi': 1.038}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 93 | -0.35 R | en test |
| horizon ~3 h | 77 | -0.42 R | en test |
| confiance moyenne | 58 | -0.07 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 11 | +1.54 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 20 | +0.15 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 7 | -0.50 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 21 | -0.51 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 17 | -0.36 R | en test |
| nouvel actif : Pétrole WTI (CL) | 77 | -0.16 R | en test |
| nouvel actif : Euro / dollar (6E) | 34 | -0.43 R | en test |

Notes :

- trades réels : +0,15 R ± 0,19 R par trade avant frais sur 154 trades (0 R = hasard)
- tendance (trend_5m, trend_15m, trend_1h, adx) : +0,10 R ± 0,07 R sur 1203 trades éq. → poids ×1,07
- vwap : +0,11 R ± 0,08 R sur 1102 trades éq. → poids ×1,09
- rsi : +0,15 R ± 0,08 R sur 965 trades éq. → poids ×1,17
- tranche 11h UTC : -0,29 R sur 80 trades éq. → évitée
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,24 R contre +0,10 R en global sur 78 trades éq. → poids ×0,68 sur cet actif
- ethereum, vwap : -0,23 R contre +0,11 R en global sur 35 trades éq. → poids ×0,98 sur cet actif
- ethereum, rsi : -0,29 R contre +0,15 R en global sur 56 trades éq. → poids ×0,55 sur cet actif
- euro, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,24 R contre +0,10 R en global sur 63 trades éq. → poids ×0,91 sur cet actif
- euro, vwap : -0,22 R contre +0,11 R en global sur 60 trades éq. → poids ×0,96 sur cet actif
- gold, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,05 R contre +0,10 R en global sur 240 trades éq. → poids ×0,95 sur cet actif
- gold, vwap : -0,05 R contre +0,11 R en global sur 238 trades éq. → poids ×0,92 sur cet actif
- gold, rsi : -0,06 R contre +0,15 R en global sur 192 trades éq. → poids ×0,85 sur cet actif
- nasdaq, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,47 R contre +0,10 R en global sur 335 trades éq. → poids ×1,50 sur cet actif
- nasdaq, vwap : +0,48 R contre +0,11 R en global sur 328 trades éq. → poids ×1,50 sur cet actif
- nasdaq, rsi : +0,56 R contre +0,15 R en global sur 274 trades éq. → poids ×1,50 sur cet actif
- nasdaq, pdhl : +0,66 R contre +0,17 R en global sur 45 trades éq. → poids ×1,04 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,11 R contre +0,10 R en global sur 191 trades éq. → poids ×0,87 sur cet actif
- sp500, vwap : -0,11 R contre +0,11 R en global sur 186 trades éq. → poids ×0,85 sur cet actif
- sp500, rsi : -0,07 R contre +0,15 R en global sur 162 trades éq. → poids ×0,89 sur cet actif

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 18/10/2026 | 113 | 3 | 34 | 76 | 8% | 25% | -17% | +0.35 % | +0.003 % |
| S&P 500 (ES) | 09/07/2026 → 18/10/2026 | 123 | 46 | 59 | 18 | 44% | 41% | +2% | -0.03 % | -0.000 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 18/10/2026 | 64 | 23 | 28 | 13 | 45% | 40% | +5% | -1.59 % | -0.025 % |
| Ethereum (ETH/USD) | 20/07/2026 → 18/10/2026 | 67 | 14 | 34 | 19 | 29% | 40% | -11% | -8.40 % | -0.125 % |
| Or (XAU/USD) | 09/07/2026 → 18/10/2026 | 146 | 44 | 63 | 39 | 41% | 42% | -1% | -3.16 % | -0.022 % |
| Pétrole WTI (CL) | 14/07/2026 → 18/10/2026 | 212 | 67 | 98 | 47 | 41% | 41% | -1% | +1.20 % | +0.006 % |
| Euro / dollar (6E) | 14/07/2026 → 18/10/2026 | 40 | 10 | 26 | 4 | 28% | 40% | -12% | -1.02 % | -0.025 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
