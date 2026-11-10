# Trading-Bot — rapport

_Mis à jour le 10/11/2026 à 14:05 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **168**
- Taux de réussite cumulé (TP / (TP+SL)) : **44%** — hasard attendu 40%, avantage **+4%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-0.36 %** (brut +3.68 %)
- Signaux ouverts : **4**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **1325** clôturés, 12 ouverts, taux de réussite 38% (hasard attendu 37%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 09/11 17:15 | Nasdaq 100 (NQ) | long | 27923.25 | 28460.0 | 27744.5 | fort | signaux du bot | 17:15 |
| 09/11 17:20 | Nasdaq 100 (NQ) | long | 27915.0 | 28440.5 | 27740.0 | fort | signaux du bot | 17:20 |
| 09/11 17:25 | Nasdaq 100 (NQ) | long | 27900.5 | 28426.0 | 27725.5 | fort | signaux du bot | 17:25 |
| 09/11 17:31 | Nasdaq 100 (NQ) | long | 27891.75 | 28379.0 | 27729.5 | fort | signaux du bot | 17:31 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 65 | 29 | 30 | 6 | 49% | +0.069 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 83 | 24 | 36 | 23 | 40% | -0.012 % |
| short | 85 | 34 | 39 | 12 | 47% | +0.007 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 164 | 57 | 73 | 34 | 44% | -0.000 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 167 | 58 | 75 | 34 | 44% | -0.001 % |
| corr | 17 | 5 | 8 | 4 | 38% | -0.015 % |
| level | 20 | 4 | 12 | 4 | 25% | -0.059 % |
| macd | 51 | 14 | 26 | 11 | 35% | -0.033 % |
| orb | 21 | 7 | 9 | 5 | 44% | +0.077 % |
| pdhl | 24 | 9 | 11 | 4 | 45% | -0.003 % |
| rsi | 144 | 53 | 60 | 31 | 47% | +0.016 % |
| trend_15m | 167 | 58 | 75 | 34 | 44% | -0.001 % |
| trend_1h | 167 | 58 | 75 | 34 | 44% | -0.001 % |
| trend_5m | 149 | 54 | 64 | 31 | 46% | +0.011 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 165 | 58 | 73 | 34 | 44% | +0.003 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 71 | 22 | 32 | 17 | 41% | -0.022 % |
| actualité chargée | 97 | 36 | 43 | 18 | 46% | +0.013 % |

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
| 16h | 12 | 3 | 6 | 3 | 33% | +0.018 % |
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
| signaux du bot | 167 | 58 | 75 | 34 | 44% | -0.001 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 21 | 10 | 11 | 0 | 48% | +0.192 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 35, 57% terminés dans le bon sens, P&L moyen -0.005 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 1325 | 401 | 652 | 272 | 38% | +0.009 % |
| corr | 107 | 26 | 59 | 22 | 31% | -0.031 % |
| level | 131 | 50 | 48 | 33 | 51% | +0.069 % |
| macd | 323 | 75 | 177 | 71 | 30% | -0.032 % |
| orb | 77 | 27 | 28 | 22 | 49% | +0.050 % |
| pdhl | 140 | 58 | 69 | 13 | 46% | +0.114 % |
| rsi | 997 | 318 | 490 | 189 | 39% | +0.017 % |
| trend_15m | 1325 | 401 | 652 | 272 | 38% | +0.009 % |
| trend_1h | 1302 | 393 | 643 | 266 | 38% | +0.010 % |
| trend_5m | 1179 | 369 | 586 | 224 | 39% | +0.014 % |
| volume | 18 | 3 | 12 | 3 | 20% | -0.156 % |
| vwap | 1299 | 396 | 638 | 265 | 38% | +0.010 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 49 | 12 | 20 | 17 | 38% | -0.067 % |
| ethereum | 46 | 10 | 25 | 11 | 29% | -0.148 % |
| euro | 52 | 17 | 32 | 3 | 35% | -0.024 % |
| gold | 469 | 147 | 194 | 128 | 43% | -0.001 % |
| nasdaq | 460 | 143 | 247 | 70 | 37% | +0.067 % |
| oil | 133 | 41 | 64 | 28 | 39% | -0.021 % |
| sp500 | 116 | 31 | 70 | 15 | 31% | -0.038 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 12/10 16:50 | Nasdaq 100 (NQ) | short | 30889.75 | 30934.5 | ❌ SL | -0.15 % | 53 min |
| 12/10 16:25 | S&P 500 (ES) | short | 7856.5 | 7859.0 | ⏱️ expiré | -0.04 % | 65 min |
| 12/10 16:25 | Or (XAU/USD) | short | 4191.6 | 4193.7 | ⏱️ expiré | -0.07 % | 65 min |
| 12/10 16:15 | Nasdaq 100 (NQ) | short | 30943.75 | 30882.75 | ✅ TP | +0.19 % | 5 min |

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.079 |
| trend_15m | 1.079 |
| trend_1h | 1.079 |
| adx | 1.079 |
| vwap | 0.824 |
| rsi | 1.135 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.114 |
| pdhl | 1.155 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [12, 19]

Corrections par actif :

- ethereum : {'trend_5m': 0.935, 'trend_15m': 0.935, 'trend_1h': 0.935, 'adx': 0.935, 'rsi': 0.872}
- euro : {'trend_5m': 0.922, 'trend_15m': 0.922, 'trend_1h': 0.922, 'adx': 0.922, 'vwap': 0.741, 'rsi': 1.054}
- nasdaq : {'trend_5m': 1.352, 'trend_15m': 1.352, 'trend_1h': 1.352, 'adx': 1.352, 'vwap': 1.017, 'rsi': 1.5}
- oil : {'rsi': 1.094}
- sp500 : {'trend_5m': 0.833, 'trend_15m': 0.833, 'trend_1h': 0.833, 'adx': 0.833, 'vwap': 0.631, 'rsi': 0.952, 'pdhl': 0.969}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 150 | -0.43 R | en test |
| horizon ~3 h | 175 | -0.19 R | en test |
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

- trades réels : +0,15 R ± 0,20 R par trade avant frais sur 168 trades (0 R = hasard)
- tendance (trend_5m, trend_15m, trend_1h, adx) : +0,09 R ± 0,06 R sur 1920 trades éq. → poids ×1,08
- vwap : +0,10 R ± 0,06 R sur 1803 trades éq. → poids ×1,10
- rsi : +0,12 R ± 0,07 R sur 1499 trades éq. → poids ×1,13
- orb : +0,29 R ± 0,25 R sur 118 trades éq. → poids ×1,11
- pdhl : +0,25 R ± 0,19 R sur 223 trades éq. → poids ×1,16
- tranche 12h UTC : -0,44 R sur 67 trades éq. → évitée
- tranche 19h UTC : -0,30 R sur 86 trades éq. → évitée
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,17 R contre +0,09 R en global sur 98 trades éq. → poids ×0,87 sur cet actif
- ethereum, rsi : -0,21 R contre +0,12 R en global sur 70 trades éq. → poids ×0,77 sur cet actif
- euro, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,22 R contre +0,09 R en global sur 84 trades éq. → poids ×0,85 sur cet actif
- euro, vwap : -0,21 R contre +0,10 R en global sur 80 trades éq. → poids ×0,90 sur cet actif
- euro, rsi : -0,19 R contre +0,12 R en global sur 70 trades éq. → poids ×0,93 sur cet actif
- nasdaq, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,33 R contre +0,09 R en global sur 544 trades éq. → poids ×1,25 sur cet actif
- nasdaq, vwap : +0,33 R contre +0,10 R en global sur 537 trades éq. → poids ×1,23 sur cet actif
- nasdaq, rsi : +0,41 R contre +0,12 R en global sur 429 trades éq. → poids ×1,33 sur cet actif
- oil, rsi : -0,04 R contre +0,12 R en global sur 232 trades éq. → poids ×0,96 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,15 R contre +0,09 R en global sur 218 trades éq. → poids ×0,77 sur cet actif
- sp500, vwap : -0,15 R contre +0,10 R en global sur 213 trades éq. → poids ×0,77 sur cet actif
- sp500, rsi : -0,11 R contre +0,12 R en global sur 179 trades éq. → poids ×0,84 sur cet actif

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
