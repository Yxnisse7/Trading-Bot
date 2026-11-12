# Trading-Bot — rapport

_Mis à jour le 12/11/2026 à 16:11 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **176**
- Taux de réussite cumulé (TP / (TP+SL)) : **41%** — hasard attendu 39%, avantage **+2%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-5.24 %** (brut -1.12 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **1430** clôturés, 2 ouverts, taux de réussite 38% (hasard attendu 37%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 73 | 29 | 38 | 6 | 43% | -0.005 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 91 | 24 | 44 | 23 | 35% | -0.064 % |
| short | 85 | 34 | 39 | 12 | 47% | +0.007 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 172 | 57 | 81 | 34 | 41% | -0.029 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 175 | 58 | 83 | 34 | 41% | -0.029 % |
| corr | 17 | 5 | 8 | 4 | 38% | -0.015 % |
| level | 20 | 4 | 12 | 4 | 25% | -0.059 % |
| macd | 51 | 14 | 26 | 11 | 35% | -0.033 % |
| orb | 25 | 7 | 13 | 5 | 35% | -0.036 % |
| pdhl | 24 | 9 | 11 | 4 | 45% | -0.003 % |
| rsi | 150 | 53 | 66 | 31 | 45% | -0.008 % |
| trend_15m | 175 | 58 | 83 | 34 | 41% | -0.029 % |
| trend_1h | 175 | 58 | 83 | 34 | 41% | -0.029 % |
| trend_5m | 157 | 54 | 72 | 31 | 43% | -0.020 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 173 | 58 | 81 | 34 | 42% | -0.026 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 71 | 22 | 32 | 17 | 41% | -0.022 % |
| actualité chargée | 105 | 36 | 51 | 18 | 41% | -0.035 % |

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
| 16h | 20 | 3 | 14 | 3 | 18% | -0.233 % |
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
| signaux du bot | 175 | 58 | 83 | 34 | 41% | -0.029 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 29 | 10 | 19 | 0 | 34% | -0.029 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 35, 57% terminés dans le bon sens, P&L moyen -0.005 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 1430 | 437 | 708 | 285 | 38% | -0.001 % |
| corr | 108 | 27 | 59 | 22 | 31% | -0.029 % |
| level | 138 | 50 | 54 | 34 | 48% | +0.051 % |
| macd | 359 | 91 | 194 | 74 | 32% | -0.037 % |
| orb | 91 | 28 | 36 | 27 | 44% | -0.015 % |
| pdhl | 148 | 60 | 70 | 18 | 46% | +0.112 % |
| rsi | 1065 | 347 | 518 | 200 | 40% | +0.014 % |
| trend_15m | 1430 | 437 | 708 | 285 | 38% | -0.001 % |
| trend_1h | 1404 | 429 | 696 | 279 | 38% | +0.000 % |
| trend_5m | 1277 | 404 | 636 | 237 | 39% | +0.003 % |
| volume | 19 | 3 | 13 | 3 | 19% | -0.164 % |
| vwap | 1403 | 432 | 694 | 277 | 38% | +0.000 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 50 | 12 | 21 | 17 | 36% | -0.072 % |
| ethereum | 47 | 10 | 26 | 11 | 28% | -0.154 % |
| euro | 58 | 18 | 35 | 5 | 34% | -0.025 % |
| gold | 537 | 181 | 219 | 137 | 45% | +0.008 % |
| nasdaq | 483 | 143 | 270 | 70 | 35% | +0.031 % |
| oil | 136 | 41 | 66 | 29 | 38% | -0.032 % |
| sp500 | 119 | 32 | 71 | 16 | 31% | -0.035 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 11/11 17:46 | Nasdaq 100 (NQ) | long | 28540.75 | 28306.25 | ❌ SL | -0.83 % | 373 min |
| 11/11 17:40 | Nasdaq 100 (NQ) | long | 28543.25 | 28439.75 | ❌ SL | -0.37 % | 315 min |
| 11/11 17:35 | Nasdaq 100 (NQ) | long | 28553.25 | 28448.0 | ❌ SL | -0.38 % | 259 min |
| 11/11 17:31 | Nasdaq 100 (NQ) | long | 28526.0 | 28306.25 | ❌ SL | -0.78 % | 388 min |
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

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.048 |
| trend_15m | 1.048 |
| trend_1h | 1.048 |
| adx | 1.048 |
| vwap | 0.798 |
| rsi | 1.128 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.168 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [10, 12, 19]

Corrections par actif :

- ethereum : {'trend_5m': 0.919, 'trend_15m': 0.919, 'trend_1h': 0.919, 'adx': 0.919, 'rsi': 0.84}
- euro : {'trend_5m': 0.853, 'trend_15m': 0.853, 'trend_1h': 0.853, 'adx': 0.853, 'vwap': 0.672, 'rsi': 0.945}
- nasdaq : {'trend_5m': 1.135, 'trend_15m': 1.135, 'trend_1h': 1.135, 'adx': 1.135, 'vwap': 0.85, 'rsi': 1.332}
- oil : {'rsi': 1.071}
- sp500 : {'trend_5m': 0.87, 'trend_15m': 0.87, 'trend_1h': 0.87, 'adx': 0.87, 'vwap': 0.66, 'rsi': 1.003, 'pdhl': 0.977}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 151 | -0.43 R | en test |
| horizon ~3 h | 194 | -0.29 R | en test |
| confiance moyenne | 74 | -0.05 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 21 | +0.43 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 45 | -0.09 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 28 | -0.52 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 41 | -0.35 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 57 | +0.15 R | en test |
| nouvel actif : Pétrole WTI (CL) | 136 | -0.08 R | en test |
| nouvel actif : Euro / dollar (6E) | 58 | -0.44 R | en test |

Notes :

- trades réels : +0,09 R ± 0,19 R par trade avant frais sur 176 trades (0 R = hasard)
- tendance (trend_5m, trend_15m, trend_1h, adx) : +0,08 R ± 0,06 R sur 2029 trades éq. → poids ×1,05
- vwap : +0,08 R ± 0,06 R sur 1912 trades éq. → poids ×1,06
- rsi : +0,12 R ± 0,07 R sur 1570 trades éq. → poids ×1,13
- pdhl : +0,25 R ± 0,18 R sur 231 trades éq. → poids ×1,17
- tranche 10h UTC : -0,26 R sur 107 trades éq. → évitée
- tranche 12h UTC : -0,44 R sur 67 trades éq. → évitée
- tranche 19h UTC : -0,30 R sur 86 trades éq. → évitée
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,18 R contre +0,08 R en global sur 99 trades éq. → poids ×0,88 sur cet actif
- ethereum, rsi : -0,23 R contre +0,12 R en global sur 71 trades éq. → poids ×0,74 sur cet actif
- euro, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,25 R contre +0,08 R en global sur 90 trades éq. → poids ×0,81 sur cet actif
- euro, vwap : -0,24 R contre +0,08 R en global sur 85 trades éq. → poids ×0,84 sur cet actif
- euro, rsi : -0,22 R contre +0,12 R en global sur 76 trades éq. → poids ×0,84 sur cet actif
- nasdaq, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,24 R contre +0,08 R en global sur 573 trades éq. → poids ×1,08 sur cet actif
- nasdaq, vwap : +0,25 R contre +0,08 R en global sur 566 trades éq. → poids ×1,06 sur cet actif
- nasdaq, rsi : +0,35 R contre +0,12 R en global sur 442 trades éq. → poids ×1,18 sur cet actif
- oil, rsi : -0,05 R contre +0,12 R en global sur 234 trades éq. → poids ×0,95 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,14 R contre +0,08 R en global sur 221 trades éq. → poids ×0,83 sur cet actif
- sp500, vwap : -0,14 R contre +0,08 R en global sur 216 trades éq. → poids ×0,83 sur cet actif
- sp500, rsi : -0,10 R contre +0,12 R en global sur 181 trades éq. → poids ×0,89 sur cet actif

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
