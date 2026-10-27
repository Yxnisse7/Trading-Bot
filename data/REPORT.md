# Trading-Bot — rapport

_Mis à jour le 27/10/2026 à 21:11 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **160**
- Taux de réussite cumulé (TP / (TP+SL)) : **43%** — hasard attendu 40%, avantage **+3%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-2.08 %** (brut +1.88 %)
- Signaux ouverts : **4**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **910** clôturés, 18 ouverts, taux de réussite 35% (hasard attendu 36%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 27/10 16:05 | Nasdaq 100 (NQ) | long | 29702.25 | 29907.0 | 29634.0 | fort | signaux du bot | 16:05 |
| 27/10 16:10 | Nasdaq 100 (NQ) | long | 29727.25 | 29943.25 | 29655.25 | fort | signaux du bot | 16:10 |
| 27/10 16:15 | Nasdaq 100 (NQ) | long | 29732.5 | 29948.5 | 29660.5 | fort | signaux du bot | 16:15 |
| 27/10 16:20 | Nasdaq 100 (NQ) | long | 29717.0 | 29927.5 | 29647.0 | fort | signaux du bot | 16:20 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 57 | 25 | 26 | 6 | 49% | +0.049 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 77 | 20 | 34 | 23 | 37% | -0.043 % |
| short | 83 | 34 | 37 | 12 | 48% | +0.015 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 156 | 53 | 69 | 34 | 43% | -0.011 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 159 | 54 | 71 | 34 | 43% | -0.012 % |
| corr | 17 | 5 | 8 | 4 | 38% | -0.015 % |
| level | 20 | 4 | 12 | 4 | 25% | -0.059 % |
| macd | 47 | 11 | 25 | 11 | 31% | -0.077 % |
| orb | 17 | 3 | 9 | 5 | 25% | -0.073 % |
| pdhl | 24 | 9 | 11 | 4 | 45% | -0.003 % |
| rsi | 136 | 49 | 56 | 31 | 47% | +0.005 % |
| trend_15m | 159 | 54 | 71 | 34 | 43% | -0.012 % |
| trend_1h | 159 | 54 | 71 | 34 | 43% | -0.012 % |
| trend_5m | 141 | 50 | 60 | 31 | 45% | -0.000 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 157 | 54 | 69 | 34 | 44% | -0.008 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 69 | 22 | 30 | 17 | 42% | -0.013 % |
| actualité chargée | 91 | 32 | 41 | 18 | 44% | -0.013 % |

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
| signaux du bot | 159 | 54 | 71 | 34 | 43% | -0.012 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 13 | 6 | 7 | 0 | 46% | +0.178 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 35, 57% terminés dans le bon sens, P&L moyen -0.005 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 910 | 265 | 492 | 153 | 35% | -0.013 % |
| corr | 80 | 15 | 49 | 16 | 23% | -0.077 % |
| level | 67 | 24 | 29 | 14 | 45% | -0.052 % |
| macd | 234 | 52 | 144 | 38 | 27% | -0.078 % |
| orb | 38 | 17 | 14 | 7 | 55% | +0.054 % |
| pdhl | 105 | 42 | 50 | 13 | 46% | +0.076 % |
| rsi | 687 | 211 | 373 | 103 | 36% | -0.003 % |
| trend_15m | 910 | 265 | 492 | 153 | 35% | -0.013 % |
| trend_1h | 895 | 257 | 489 | 149 | 34% | -0.014 % |
| trend_5m | 801 | 242 | 441 | 118 | 35% | -0.008 % |
| volume | 11 | 2 | 7 | 2 | 22% | -0.128 % |
| vwap | 886 | 260 | 479 | 147 | 35% | -0.012 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 29 | 9 | 8 | 12 | 53% | -0.015 % |
| ethereum | 27 | 4 | 16 | 7 | 20% | -0.211 % |
| euro | 36 | 12 | 23 | 1 | 34% | -0.025 % |
| gold | 244 | 71 | 126 | 47 | 36% | -0.025 % |
| nasdaq | 373 | 114 | 206 | 53 | 36% | +0.032 % |
| oil | 92 | 26 | 47 | 19 | 36% | -0.065 % |
| sp500 | 109 | 29 | 66 | 14 | 31% | -0.042 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 09/10 17:30 | Or (XAU/USD) | long | 4213.0 | 4213.8 | ⏱️ expiré | -0.00 % | 64 min |
| 09/10 17:01 | Nasdaq 100 (NQ) | short | 31076.5 | 31044.0 | ✅ TP | +0.09 % | 5 min |
| 09/10 15:45 | Or (XAU/USD) | long | 4213.6 | 4210.5 | ⏱️ expiré | -0.09 % | 60 min |
| 09/10 10:10 | Or (XAU/USD) | long | 4218.7 | 4212.3 | ❌ SL | -0.17 % | 39 min |
| 09/10 09:00 | Or (XAU/USD) | long | 4218.5 | 4217.1 | ⏱️ expiré | -0.05 % | 60 min |
| 09/10 08:10 | Bitcoin (BTC/USD) | long | 82381.0 | 82558.0 | ⏱️ expiré | +0.15 % | 60 min |

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.0 |
| trend_15m | 1.0 |
| trend_1h | 1.0 |
| adx | 1.0 |
| vwap | 0.75 |
| rsi | 1.0 |
| macd | 0.925 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.0 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [11, 12, 19]

Corrections par actif :

- ethereum : {'trend_5m': 0.844, 'trend_15m': 0.844, 'trend_1h': 0.844, 'adx': 0.844, 'rsi': 0.799}
- gold : {'rsi': 0.993}
- nasdaq : {'trend_5m': 1.175, 'trend_15m': 1.175, 'trend_1h': 1.175, 'adx': 1.175, 'vwap': 0.868, 'rsi': 1.26}
- sp500 : {'trend_5m': 0.854, 'trend_15m': 0.854, 'trend_1h': 0.854, 'adx': 0.854, 'vwap': 0.638, 'rsi': 0.909}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 131 | -0.56 R | en test |
| horizon ~3 h | 140 | -0.28 R | en test |
| confiance moyenne | 68 | -0.01 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 11 | +1.54 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 35 | -0.13 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 7 | -0.50 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 21 | -0.51 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 32 | +0.03 R | en test |
| nouvel actif : Pétrole WTI (CL) | 92 | -0.17 R | en test |
| nouvel actif : Euro / dollar (6E) | 36 | -0.41 R | en test |

Notes :

- trades réels : +0,11 R ± 0,19 R par trade avant frais sur 160 trades (0 R = hasard)
- macd : -0,15 R ± 0,12 R sur 398 trades éq. → poids ×0,93
- tranche 11h UTC : -0,31 R sur 77 trades éq. → évitée
- tranche 12h UTC : -0,45 R sur 65 trades éq. → évitée
- tranche 19h UTC : -0,31 R sur 82 trades éq. → évitée
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,26 R contre +0,03 R en global sur 73 trades éq. → poids ×0,84 sur cet actif
- ethereum, rsi : -0,28 R contre +0,06 R en global sur 54 trades éq. → poids ×0,80 sur cet actif
- gold, rsi : -0,06 R contre +0,06 R en global sur 290 trades éq. → poids ×0,99 sur cet actif
- nasdaq, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,25 R contre +0,03 R en global sur 449 trades éq. → poids ×1,17 sur cet actif
- nasdaq, vwap : +0,25 R contre +0,04 R en global sur 441 trades éq. → poids ×1,16 sur cet actif
- nasdaq, rsi : +0,34 R contre +0,06 R en global sur 351 trades éq. → poids ×1,26 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,18 R contre +0,03 R en global sur 198 trades éq. → poids ×0,85 sur cet actif
- sp500, vwap : -0,18 R contre +0,04 R en global sur 194 trades éq. → poids ×0,85 sur cet actif
- sp500, rsi : -0,15 R contre +0,06 R en global sur 165 trades éq. → poids ×0,91 sur cet actif
- variante « indices le matin européen » en test : 131 trades, -0,56 R net, pas meilleure que les signaux réels
- variante « horizon ~3 h » en test : 140 trades, -0,28 R net, pas meilleure que les signaux réels
- variante « confiance moyenne » en test : 68 trades, -0,01 R net, encore 32 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 11 trades, +1,54 R net, encore 89 trades avant décision
- variante « reprise juste après un stop » en test : 28 trades, -0,31 R net, encore 72 trades avant décision
- variante « nouvel actif : S&P 500 (ES) » en test : 35 trades, -0,13 R net, encore 65 trades avant décision

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 23/10/2026 | 60 | 14 | 43 | 3 | 25% | 25% | -0% | +0.11 % | +0.002 % |
| S&P 500 (ES) | 09/07/2026 → 23/10/2026 | 111 | 35 | 63 | 13 | 36% | 41% | -6% | -1.96 % | -0.018 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 25/10/2026 | 50 | 17 | 24 | 9 | 41% | 41% | +1% | -1.92 % | -0.038 % |
| Ethereum (ETH/USD) | 20/07/2026 → 25/10/2026 | 60 | 12 | 33 | 15 | 27% | 40% | -14% | -8.07 % | -0.135 % |
| Or (XAU/USD) | 09/07/2026 → 23/10/2026 | 138 | 42 | 61 | 35 | 41% | 42% | -1% | -2.54 % | -0.018 % |
| Pétrole WTI (CL) | 14/07/2026 → 23/10/2026 | 196 | 59 | 100 | 37 | 37% | 41% | -4% | -6.93 % | -0.035 % |
| Euro / dollar (6E) | 14/07/2026 → 23/10/2026 | 35 | 8 | 23 | 4 | 26% | 40% | -14% | -0.93 % | -0.027 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
