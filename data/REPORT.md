# Trading-Bot — rapport

_Mis à jour le 03/11/2026 à 03:35 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **166**
- Taux de réussite cumulé (TP / (TP+SL)) : **44%** — hasard attendu 40%, avantage **+4%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **+0.13 %** (brut +4.15 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **1057** clôturés, 0 ouverts, taux de réussite 38% (hasard attendu 36%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 63 | 29 | 28 | 6 | 51% | +0.079 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 81 | 24 | 34 | 23 | 41% | -0.006 % |
| short | 85 | 34 | 39 | 12 | 47% | +0.007 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 162 | 57 | 71 | 34 | 45% | +0.003 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 165 | 58 | 73 | 34 | 44% | +0.002 % |
| corr | 17 | 5 | 8 | 4 | 38% | -0.015 % |
| level | 20 | 4 | 12 | 4 | 25% | -0.059 % |
| macd | 50 | 14 | 25 | 11 | 36% | -0.029 % |
| orb | 21 | 7 | 9 | 5 | 44% | +0.077 % |
| pdhl | 24 | 9 | 11 | 4 | 45% | -0.003 % |
| rsi | 142 | 53 | 58 | 31 | 48% | +0.020 % |
| trend_15m | 165 | 58 | 73 | 34 | 44% | +0.002 % |
| trend_1h | 165 | 58 | 73 | 34 | 44% | +0.002 % |
| trend_5m | 147 | 54 | 62 | 31 | 47% | +0.015 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 163 | 58 | 71 | 34 | 45% | +0.005 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 71 | 22 | 32 | 17 | 41% | -0.022 % |
| actualité chargée | 95 | 36 | 41 | 18 | 47% | +0.018 % |

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
| 17h | 12 | 4 | 5 | 3 | 44% | +0.026 % |
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
| signaux du bot | 165 | 58 | 73 | 34 | 44% | +0.002 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 19 | 10 | 9 | 0 | 53% | +0.238 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 35, 57% terminés dans le bon sens, P&L moyen -0.005 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 1057 | 329 | 543 | 185 | 38% | +0.015 % |
| corr | 86 | 20 | 50 | 16 | 29% | -0.037 % |
| level | 90 | 35 | 41 | 14 | 46% | +0.048 % |
| macd | 272 | 66 | 154 | 52 | 30% | -0.032 % |
| orb | 69 | 26 | 25 | 18 | 51% | +0.069 % |
| pdhl | 116 | 53 | 50 | 13 | 51% | +0.163 % |
| rsi | 805 | 263 | 413 | 129 | 39% | +0.026 % |
| trend_15m | 1057 | 329 | 543 | 185 | 38% | +0.015 % |
| trend_1h | 1041 | 321 | 539 | 181 | 37% | +0.015 % |
| trend_5m | 945 | 305 | 491 | 149 | 38% | +0.022 % |
| volume | 12 | 3 | 7 | 2 | 30% | -0.074 % |
| vwap | 1033 | 324 | 530 | 179 | 38% | +0.017 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 30 | 9 | 9 | 12 | 50% | -0.028 % |
| ethereum | 29 | 5 | 17 | 7 | 23% | -0.197 % |
| euro | 43 | 14 | 28 | 1 | 33% | -0.025 % |
| gold | 319 | 105 | 158 | 56 | 40% | -0.011 % |
| nasdaq | 414 | 135 | 209 | 70 | 39% | +0.093 % |
| oil | 109 | 31 | 53 | 25 | 37% | -0.057 % |
| sp500 | 113 | 30 | 69 | 14 | 30% | -0.042 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 09/10 21:30 | S&P 500 (ES) | long | 7868.5 | 7863.0 | ❌ SL | -0.08 % | 9 min |
| 09/10 19:30 | Nasdaq 100 (NQ) | short | 31078.0 | 31106.0 | ❌ SL | -0.10 % | 39 min |

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.082 |
| trend_15m | 1.082 |
| trend_1h | 1.082 |
| adx | 1.082 |
| vwap | 0.824 |
| rsi | 1.144 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.117 |
| pdhl | 1.352 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [11, 12, 19]

Corrections par actif :

- ethereum : {'trend_5m': 0.84, 'trend_15m': 0.84, 'trend_1h': 0.84, 'adx': 0.84, 'rsi': 0.831}
- euro : {'trend_5m': 0.938, 'trend_15m': 0.938, 'trend_1h': 0.938, 'adx': 0.938, 'vwap': 0.752, 'rsi': 1.101}
- gold : {'rsi': 1.131}
- nasdaq : {'trend_5m': 1.491, 'trend_15m': 1.491, 'trend_1h': 1.491, 'adx': 1.491, 'vwap': 1.124, 'rsi': 1.5, 'macd': 1.025, 'pdhl': 1.5}
- oil : {'trend_5m': 1.054, 'trend_15m': 1.054, 'trend_1h': 1.054, 'adx': 1.054, 'vwap': 0.774, 'rsi': 1.019}
- sp500 : {'trend_5m': 0.743, 'trend_15m': 0.743, 'trend_1h': 0.743, 'adx': 0.743, 'vwap': 0.562, 'rsi': 0.841}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 132 | -0.56 R | en test |
| horizon ~3 h | 160 | -0.11 R | en test |
| confiance moyenne | 69 | +0.03 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 12 | +1.53 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 39 | -0.16 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 8 | -0.58 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 23 | -0.46 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 36 | +0.09 R | en test |
| nouvel actif : Pétrole WTI (CL) | 109 | -0.14 R | en test |
| nouvel actif : Euro / dollar (6E) | 43 | -0.43 R | en test |

Notes :

- trades réels : +0,16 R ± 0,20 R par trade avant frais sur 166 trades (0 R = hasard)
- tendance (trend_5m, trend_15m, trend_1h, adx) : +0,10 R ± 0,07 R sur 1601 trades éq. → poids ×1,08
- vwap : +0,11 R ± 0,07 R sur 1498 trades éq. → poids ×1,10
- rsi : +0,13 R ± 0,07 R sur 1264 trades éq. → poids ×1,14
- orb : +0,31 R ± 0,26 R sur 108 trades éq. → poids ×1,12
- pdhl : +0,35 R ± 0,20 R sur 191 trades éq. → poids ×1,35
- tranche 11h UTC : -0,31 R sur 77 trades éq. → évitée
- tranche 12h UTC : -0,44 R sur 65 trades éq. → évitée
- tranche 19h UTC : -0,31 R sur 83 trades éq. → évitée
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,21 R contre +0,10 R en global sur 78 trades éq. → poids ×0,78 sur cet actif
- ethereum, rsi : -0,24 R contre +0,13 R en global sur 58 trades éq. → poids ×0,73 sur cet actif
- euro, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,24 R contre +0,10 R en global sur 68 trades éq. → poids ×0,87 sur cet actif
- euro, vwap : -0,22 R contre +0,11 R en global sur 64 trades éq. → poids ×0,91 sur cet actif
- euro, rsi : -0,20 R contre +0,13 R en global sur 55 trades éq. → poids ×0,96 sur cet actif
- gold, rsi : +0,01 R contre +0,13 R en global sur 354 trades éq. → poids ×0,99 sur cet actif
- nasdaq, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,40 R contre +0,10 R en global sur 496 trades éq. → poids ×1,38 sur cet actif
- nasdaq, vwap : +0,40 R contre +0,11 R en global sur 488 trades éq. → poids ×1,36 sur cet actif
- nasdaq, rsi : +0,49 R contre +0,13 R en global sur 388 trades éq. → poids ×1,47 sur cet actif
- nasdaq, macd : +0,25 R contre -0,03 R en global sur 133 trades éq. → poids ×1,03 sur cet actif
- nasdaq, pdhl : +1,10 R contre +0,35 R en global sur 51 trades éq. → poids ×1,50 sur cet actif

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 01/11/2026 | 63 | 16 | 44 | 3 | 27% | 25% | +2% | +1.66 % | +0.026 % |
| S&P 500 (ES) | 09/07/2026 → 01/11/2026 | 119 | 39 | 67 | 13 | 37% | 41% | -5% | -1.88 % | -0.016 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 01/11/2026 | 57 | 19 | 27 | 11 | 41% | 40% | +1% | -1.42 % | -0.025 % |
| Ethereum (ETH/USD) | 20/07/2026 → 01/11/2026 | 65 | 15 | 34 | 16 | 31% | 40% | -10% | -6.91 % | -0.106 % |
| Or (XAU/USD) | 09/07/2026 → 01/11/2026 | 147 | 46 | 66 | 35 | 41% | 42% | -1% | -2.33 % | -0.016 % |
| Pétrole WTI (CL) | 14/07/2026 → 01/11/2026 | 199 | 58 | 103 | 38 | 36% | 41% | -5% | -8.26 % | -0.042 % |
| Euro / dollar (6E) | 14/07/2026 → 01/11/2026 | 35 | 8 | 23 | 4 | 26% | 40% | -14% | -0.93 % | -0.027 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
