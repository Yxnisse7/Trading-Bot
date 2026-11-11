# Trading-Bot — rapport

_Mis à jour le 11/11/2026 à 04:51 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **172**
- Taux de réussite cumulé (TP / (TP+SL)) : **42%** — hasard attendu 39%, avantage **+3%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-2.88 %** (brut +1.20 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **1337** clôturés, 0 ouverts, taux de réussite 38% (hasard attendu 37%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 69 | 29 | 34 | 6 | 46% | +0.029 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 87 | 24 | 40 | 23 | 38% | -0.040 % |
| short | 85 | 34 | 39 | 12 | 47% | +0.007 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 168 | 57 | 77 | 34 | 43% | -0.015 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 171 | 58 | 79 | 34 | 42% | -0.016 % |
| corr | 17 | 5 | 8 | 4 | 38% | -0.015 % |
| level | 20 | 4 | 12 | 4 | 25% | -0.059 % |
| macd | 51 | 14 | 26 | 11 | 35% | -0.033 % |
| orb | 25 | 7 | 13 | 5 | 35% | -0.036 % |
| pdhl | 24 | 9 | 11 | 4 | 45% | -0.003 % |
| rsi | 146 | 53 | 62 | 31 | 46% | +0.008 % |
| trend_15m | 171 | 58 | 79 | 34 | 42% | -0.016 % |
| trend_1h | 171 | 58 | 79 | 34 | 42% | -0.016 % |
| trend_5m | 153 | 54 | 68 | 31 | 44% | -0.005 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 169 | 58 | 77 | 34 | 43% | -0.012 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 71 | 22 | 32 | 17 | 41% | -0.022 % |
| actualité chargée | 101 | 36 | 47 | 18 | 43% | -0.013 % |

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
| 15h | 35 | 15 | 15 | 5 | 50% | +0.074 % |
| 16h | 16 | 3 | 10 | 3 | 23% | -0.144 % |
| 17h | 14 | 4 | 7 | 3 | 36% | -0.012 % |
| 18h | 14 | 7 | 5 | 2 | 58% | +0.003 % |
| 19h | 17 | 6 | 9 | 2 | 40% | -0.035 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 21h | 1 | 0 | 0 | 1 | n/a | -0.272 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 171 | 58 | 79 | 34 | 42% | -0.016 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 25 | 10 | 15 | 0 | 40% | +0.061 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 35, 57% terminés dans le bon sens, P&L moyen -0.005 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 1337 | 401 | 664 | 272 | 38% | +0.002 % |
| corr | 107 | 26 | 59 | 22 | 31% | -0.031 % |
| level | 131 | 50 | 48 | 33 | 51% | +0.069 % |
| macd | 323 | 75 | 177 | 71 | 30% | -0.032 % |
| orb | 81 | 27 | 32 | 22 | 46% | +0.010 % |
| pdhl | 140 | 58 | 69 | 13 | 46% | +0.114 % |
| rsi | 998 | 318 | 491 | 189 | 39% | +0.016 % |
| trend_15m | 1337 | 401 | 664 | 272 | 38% | +0.002 % |
| trend_1h | 1314 | 393 | 655 | 266 | 38% | +0.003 % |
| trend_5m | 1191 | 369 | 598 | 224 | 38% | +0.006 % |
| volume | 18 | 3 | 12 | 3 | 20% | -0.156 % |
| vwap | 1311 | 396 | 650 | 265 | 38% | +0.003 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 49 | 12 | 20 | 17 | 38% | -0.067 % |
| ethereum | 46 | 10 | 25 | 11 | 29% | -0.148 % |
| euro | 52 | 17 | 32 | 3 | 35% | -0.024 % |
| gold | 469 | 147 | 194 | 128 | 43% | -0.001 % |
| nasdaq | 472 | 143 | 259 | 70 | 36% | +0.046 % |
| oil | 133 | 41 | 64 | 28 | 39% | -0.021 % |
| sp500 | 116 | 31 | 70 | 15 | 31% | -0.038 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 09/11 17:31 | Nasdaq 100 (NQ) | long | 27891.75 | 27729.5 | ❌ SL | -0.59 % | 1258 min |
| 09/11 17:25 | Nasdaq 100 (NQ) | long | 27900.5 | 27725.5 | ❌ SL | -0.64 % | 1264 min |
| 09/11 17:20 | Nasdaq 100 (NQ) | long | 27915.0 | 27740.0 | ❌ SL | -0.64 % | 1269 min |
| 09/11 17:15 | Nasdaq 100 (NQ) | long | 27923.25 | 27744.5 | ❌ SL | -0.65 % | 1274 min |
| 03/11 18:26 | Nasdaq 100 (NQ) | long | 28369.75 | 28306.0 | ❌ SL | -0.23 % | 128 min |
| 03/11 18:16 | Nasdaq 100 (NQ) | long | 28365.5 | 28297.0 | ❌ SL | -0.25 % | 138 min |
| 02/11 16:20 | Nasdaq 100 (NQ) | short | 28704.0 | 28794.25 | ❌ SL | -0.32 % | 0 min |
| 02/11 16:15 | Nasdaq 100 (NQ) | short | 28699.0 | 28789.5 | ❌ SL | -0.33 % | 1 min |
| 27/10 16:20 | Nasdaq 100 (NQ) | long | 29717.0 | 29927.5 | ✅ TP | +0.70 % | 744 min |
| 27/10 16:15 | Nasdaq 100 (NQ) | long | 29732.5 | 29953.0 | ✅ TP | +0.73 % | 765 min |
| 27/10 16:10 | Nasdaq 100 (NQ) | long | 29727.25 | 29953.0 | ✅ TP | +0.75 % | 770 min |
| 27/10 16:05 | Nasdaq 100 (NQ) | long | 29702.25 | 29907.0 | ✅ TP | +0.68 % | 703 min |
| 26/10 18:01 | Nasdaq 100 (NQ) | long | 29428.0 | 29351.5 | ❌ SL | -0.27 % | 748 min |
| 26/10 17:55 | Nasdaq 100 (NQ) | long | 29417.25 | 29341.0 | ❌ SL | -0.27 % | 756 min |
| 22/10 21:05 | Nasdaq 100 (NQ) | short | 29095.75 | 29173.0 | ❌ SL | -0.28 % | 55 min |
| 22/10 21:01 | Nasdaq 100 (NQ) | short | 29102.0 | 29178.5 | ❌ SL | -0.27 % | 59 min |
| 22/10 20:55 | Nasdaq 100 (NQ) | short | 29112.25 | 29182.5 | ❌ SL | -0.25 % | 65 min |
| 22/10 20:50 | Nasdaq 100 (NQ) | short | 29093.75 | 29167.0 | ❌ SL | -0.26 % | 69 min |
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

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.054 |
| trend_15m | 1.054 |
| trend_1h | 1.054 |
| adx | 1.054 |
| vwap | 0.804 |
| rsi | 1.127 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.155 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [12, 19]

Corrections par actif :

- ethereum : {'trend_5m': 0.941, 'trend_15m': 0.941, 'trend_1h': 0.941, 'adx': 0.941, 'rsi': 0.875}
- euro : {'trend_5m': 0.928, 'trend_15m': 0.928, 'trend_1h': 0.928, 'adx': 0.928, 'vwap': 0.745, 'rsi': 1.055}
- nasdaq : {'trend_5m': 1.249, 'trend_15m': 1.249, 'trend_1h': 1.249, 'adx': 1.249, 'vwap': 0.938, 'rsi': 1.472}
- oil : {'rsi': 1.095}
- sp500 : {'trend_5m': 0.842, 'trend_15m': 0.842, 'trend_1h': 0.842, 'adx': 0.842, 'vwap': 0.638, 'rsi': 0.955, 'pdhl': 0.969}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 150 | -0.43 R | en test |
| horizon ~3 h | 187 | -0.24 R | en test |
| confiance moyenne | 73 | -0.03 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 18 | +0.67 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 42 | -0.13 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 27 | -0.49 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 40 | -0.33 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 48 | +0.08 R | en test |
| nouvel actif : Pétrole WTI (CL) | 133 | -0.06 R | en test |
| nouvel actif : Euro / dollar (6E) | 52 | -0.40 R | en test |

Notes :

- trades réels : +0,12 R ± 0,19 R par trade avant frais sur 172 trades (0 R = hasard)
- tendance (trend_5m, trend_15m, trend_1h, adx) : +0,08 R ± 0,06 R sur 1934 trades éq. → poids ×1,05
- vwap : +0,09 R ± 0,06 R sur 1817 trades éq. → poids ×1,07
- rsi : +0,12 R ± 0,07 R sur 1501 trades éq. → poids ×1,13
- pdhl : +0,25 R ± 0,19 R sur 223 trades éq. → poids ×1,16
- tranche 12h UTC : -0,44 R sur 67 trades éq. → évitée
- tranche 19h UTC : -0,30 R sur 86 trades éq. → évitée
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,17 R contre +0,08 R en global sur 98 trades éq. → poids ×0,89 sur cet actif
- ethereum, rsi : -0,21 R contre +0,12 R en global sur 70 trades éq. → poids ×0,78 sur cet actif
- euro, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,22 R contre +0,08 R en global sur 84 trades éq. → poids ×0,88 sur cet actif
- euro, vwap : -0,21 R contre +0,09 R en global sur 80 trades éq. → poids ×0,93 sur cet actif
- euro, rsi : -0,19 R contre +0,12 R en global sur 70 trades éq. → poids ×0,94 sur cet actif
- nasdaq, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,29 R contre +0,08 R en global sur 559 trades éq. → poids ×1,18 sur cet actif
- nasdaq, vwap : +0,29 R contre +0,09 R en global sur 552 trades éq. → poids ×1,17 sur cet actif
- nasdaq, rsi : +0,40 R contre +0,12 R en global sur 431 trades éq. → poids ×1,31 sur cet actif
- oil, rsi : -0,04 R contre +0,12 R en global sur 232 trades éq. → poids ×0,97 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,15 R contre +0,08 R en global sur 218 trades éq. → poids ×0,80 sur cet actif
- sp500, vwap : -0,15 R contre +0,09 R en global sur 213 trades éq. → poids ×0,79 sur cet actif
- sp500, rsi : -0,11 R contre +0,12 R en global sur 179 trades éq. → poids ×0,85 sur cet actif
- sp500, pdhl : -0,19 R contre +0,25 R en global sur 31 trades éq. → poids ×0,84 sur cet actif

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 08/11/2026 | 66 | 16 | 47 | 3 | 25% | 25% | +0% | +2.23 % | +0.034 % |
| S&P 500 (ES) | 09/07/2026 → 08/11/2026 | 130 | 47 | 67 | 16 | 41% | 42% | -0% | -0.89 % | -0.007 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 08/11/2026 | 68 | 24 | 33 | 11 | 42% | 41% | +1% | -3.10 % | -0.045 % |
| Ethereum (ETH/USD) | 20/07/2026 → 08/11/2026 | 69 | 15 | 37 | 17 | 29% | 40% | -12% | -8.34 % | -0.121 % |
| Or (XAU/USD) | 09/07/2026 → 08/11/2026 | 162 | 47 | 74 | 41 | 39% | 42% | -3% | -4.25 % | -0.026 % |
| Pétrole WTI (CL) | 14/07/2026 → 08/11/2026 | 220 | 63 | 117 | 40 | 35% | 41% | -6% | -11.80 % | -0.054 % |
| Euro / dollar (6E) | 14/07/2026 → 08/11/2026 | 46 | 10 | 29 | 7 | 26% | 40% | -14% | -1.25 % | -0.027 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
