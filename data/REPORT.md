# Trading-Bot — rapport

_Mis à jour le 05/11/2026 à 10:41 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **168**
- Taux de réussite cumulé (TP / (TP+SL)) : **44%** — hasard attendu 40%, avantage **+4%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-0.36 %** (brut +3.68 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **1261** clôturés, 9 ouverts, taux de réussite 39% (hasard attendu 37%)

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
| adx | 1261 | 391 | 618 | 252 | 39% | +0.015 % |
| corr | 102 | 25 | 57 | 20 | 30% | -0.027 % |
| level | 127 | 49 | 46 | 32 | 52% | +0.066 % |
| macd | 301 | 71 | 164 | 66 | 30% | -0.026 % |
| orb | 75 | 26 | 27 | 22 | 49% | +0.057 % |
| pdhl | 133 | 55 | 65 | 13 | 46% | +0.121 % |
| rsi | 955 | 311 | 468 | 176 | 40% | +0.024 % |
| trend_15m | 1261 | 391 | 618 | 252 | 39% | +0.015 % |
| trend_1h | 1242 | 383 | 611 | 248 | 39% | +0.016 % |
| trend_5m | 1123 | 359 | 558 | 206 | 39% | +0.020 % |
| volume | 15 | 3 | 9 | 3 | 25% | -0.108 % |
| vwap | 1237 | 386 | 605 | 246 | 39% | +0.017 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 40 | 12 | 14 | 14 | 46% | -0.027 % |
| ethereum | 38 | 9 | 20 | 9 | 31% | -0.124 % |
| euro | 46 | 15 | 30 | 1 | 33% | -0.026 % |
| gold | 440 | 145 | 179 | 116 | 45% | +0.007 % |
| nasdaq | 460 | 143 | 247 | 70 | 37% | +0.067 % |
| oil | 122 | 37 | 58 | 27 | 39% | -0.024 % |
| sp500 | 115 | 30 | 70 | 15 | 30% | -0.042 % |

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
| trend_5m | 1.12 |
| trend_15m | 1.12 |
| trend_1h | 1.12 |
| adx | 1.12 |
| vwap | 0.852 |
| rsi | 1.173 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.107 |
| pdhl | 1.189 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [11, 12, 19]

Corrections par actif :

- ethereum : {'trend_5m': 1.054, 'trend_15m': 1.054, 'trend_1h': 1.054, 'adx': 1.054, 'rsi': 0.894}
- euro : {'trend_5m': 0.893, 'trend_15m': 0.893, 'trend_1h': 0.893, 'adx': 0.893, 'vwap': 0.715, 'rsi': 1.039}
- nasdaq : {'trend_5m': 1.358, 'trend_15m': 1.358, 'trend_1h': 1.358, 'adx': 1.358, 'vwap': 1.02, 'rsi': 1.5}
- oil : {'level': 0.696}
- sp500 : {'trend_5m': 0.733, 'trend_15m': 0.733, 'trend_1h': 0.733, 'adx': 0.733, 'vwap': 0.554, 'rsi': 0.832}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 150 | -0.43 R | en test |
| horizon ~3 h | 175 | -0.19 R | en test |
| confiance moyenne | 69 | +0.03 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 18 | +0.67 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 41 | -0.17 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 18 | -0.30 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 32 | -0.24 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 44 | +0.14 R | en test |
| nouvel actif : Pétrole WTI (CL) | 122 | -0.07 R | en test |
| nouvel actif : Euro / dollar (6E) | 46 | -0.45 R | en test |

Notes :

- trades réels : +0,15 R ± 0,20 R par trade avant frais sur 168 trades (0 R = hasard)
- tendance (trend_5m, trend_15m, trend_1h, adx) : +0,11 R ± 0,06 R sur 1806 trades éq. → poids ×1,12
- vwap : +0,12 R ± 0,06 R sur 1703 trades éq. → poids ×1,14
- rsi : +0,14 R ± 0,07 R sur 1415 trades éq. → poids ×1,17
- orb : +0,30 R ± 0,25 R sur 114 trades éq. → poids ×1,11
- pdhl : +0,27 R ± 0,20 R sur 208 trades éq. → poids ×1,19
- tranche 11h UTC : -0,31 R sur 77 trades éq. → évitée
- tranche 12h UTC : -0,44 R sur 65 trades éq. → évitée
- tranche 19h UTC : -0,31 R sur 83 trades éq. → évitée
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,13 R contre +0,11 R en global sur 87 trades éq. → poids ×0,94 sur cet actif
- ethereum, rsi : -0,21 R contre +0,14 R en global sur 62 trades éq. → poids ×0,76 sur cet actif
- euro, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,26 R contre +0,11 R en global sur 70 trades éq. → poids ×0,80 sur cet actif
- euro, vwap : -0,24 R contre +0,12 R en global sur 67 trades éq. → poids ×0,84 sur cet actif
- euro, rsi : -0,23 R contre +0,14 R en global sur 58 trades éq. → poids ×0,89 sur cet actif
- nasdaq, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,33 R contre +0,11 R en global sur 543 trades éq. → poids ×1,21 sur cet actif
- nasdaq, vwap : +0,34 R contre +0,12 R en global sur 535 trades éq. → poids ×1,20 sur cet actif
- nasdaq, rsi : +0,42 R contre +0,14 R en global sur 427 trades éq. → poids ×1,29 sur cet actif
- oil, level : -0,27 R contre +0,16 R en global sur 38 trades éq. → poids ×0,70 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,18 R contre +0,11 R en global sur 210 trades éq. → poids ×0,65 sur cet actif
- sp500, vwap : -0,18 R contre +0,12 R en global sur 205 trades éq. → poids ×0,65 sur cet actif

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
