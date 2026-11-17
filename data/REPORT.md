# Trading-Bot — rapport

_Mis à jour le 17/11/2026 à 14:45 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **187**
- Taux de réussite cumulé (TP / (TP+SL)) : **38%** — hasard attendu 38%, avantage **+0%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-9.78 %** (brut -5.55 %)
- Signaux ouverts : **1**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **1585** clôturés, 4 ouverts, taux de réussite 37% (hasard attendu 37%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 16/11 16:11 | Nasdaq 100 (NQ) | short | 27473.0 | 26902.5 | 27663.0 | fort | signaux du bot | 16:11 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 84 | 29 | 49 | 6 | 37% | -0.059 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 95 | 24 | 48 | 23 | 33% | -0.074 % |
| short | 92 | 34 | 46 | 12 | 42% | -0.030 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 183 | 57 | 92 | 34 | 38% | -0.052 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 186 | 58 | 94 | 34 | 38% | -0.052 % |
| corr | 20 | 5 | 11 | 4 | 31% | -0.111 % |
| level | 20 | 4 | 12 | 4 | 25% | -0.059 % |
| macd | 53 | 14 | 28 | 11 | 33% | -0.057 % |
| orb | 28 | 7 | 16 | 5 | 30% | -0.102 % |
| pdhl | 24 | 9 | 11 | 4 | 45% | -0.003 % |
| rsi | 161 | 53 | 77 | 31 | 41% | -0.036 % |
| trend_15m | 186 | 58 | 94 | 34 | 38% | -0.052 % |
| trend_1h | 186 | 58 | 94 | 34 | 38% | -0.052 % |
| trend_5m | 168 | 54 | 83 | 31 | 39% | -0.046 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 184 | 58 | 92 | 34 | 39% | -0.049 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 71 | 22 | 32 | 17 | 41% | -0.022 % |
| actualité chargée | 116 | 36 | 62 | 18 | 37% | -0.071 % |

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
| 15h | 38 | 15 | 18 | 5 | 45% | +0.017 % |
| 16h | 24 | 3 | 18 | 3 | 14% | -0.254 % |
| 17h | 18 | 4 | 11 | 3 | 27% | -0.073 % |
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
| signaux du bot | 186 | 58 | 94 | 34 | 38% | -0.052 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 40 | 10 | 30 | 0 | 25% | -0.135 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 35, 57% terminés dans le bon sens, P&L moyen -0.005 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 1585 | 471 | 812 | 302 | 37% | -0.015 % |
| corr | 131 | 36 | 72 | 23 | 33% | -0.032 % |
| level | 148 | 52 | 59 | 37 | 47% | +0.035 % |
| macd | 404 | 106 | 220 | 78 | 33% | -0.051 % |
| orb | 103 | 31 | 45 | 27 | 41% | -0.050 % |
| pdhl | 163 | 63 | 81 | 19 | 44% | +0.080 % |
| rsi | 1186 | 373 | 601 | 212 | 38% | -0.000 % |
| trend_15m | 1585 | 471 | 812 | 302 | 37% | -0.015 % |
| trend_1h | 1559 | 463 | 800 | 296 | 37% | -0.014 % |
| trend_5m | 1421 | 438 | 735 | 248 | 37% | -0.011 % |
| volume | 32 | 7 | 21 | 4 | 25% | -0.091 % |
| vwap | 1551 | 466 | 795 | 290 | 37% | -0.013 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 86 | 21 | 42 | 23 | 33% | -0.100 % |
| ethereum | 74 | 17 | 44 | 13 | 28% | -0.186 % |
| euro | 63 | 19 | 38 | 6 | 33% | -0.024 % |
| gold | 565 | 186 | 234 | 145 | 44% | +0.003 % |
| nasdaq | 530 | 151 | 309 | 70 | 33% | +0.015 % |
| oil | 141 | 43 | 69 | 29 | 38% | -0.034 % |
| sp500 | 126 | 34 | 76 | 16 | 31% | -0.036 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 16/11 16:25 | Nasdaq 100 (NQ) | short | 27435.0 | 27603.0 | ❌ SL | -0.62 % | 57 min |
| 16/11 16:21 | Nasdaq 100 (NQ) | short | 27428.25 | 27598.5 | ❌ SL | -0.63 % | 61 min |
| 16/11 16:16 | Nasdaq 100 (NQ) | short | 27402.25 | 27593.0 | ❌ SL | -0.71 % | 40 min |
| 13/11 17:46 | Nasdaq 100 (NQ) | short | 27821.25 | 27911.0 | ❌ SL | -0.33 % | 19 min |
| 13/11 17:41 | Nasdaq 100 (NQ) | short | 27850.0 | 27940.5 | ❌ SL | -0.34 % | 26 min |
| 13/11 17:35 | Nasdaq 100 (NQ) | short | 27824.75 | 27923.75 | ❌ SL | -0.37 % | 31 min |
| 13/11 17:20 | Nasdaq 100 (NQ) | short | 27811.75 | 27922.75 | ❌ SL | -0.41 % | 46 min |
| 12/11 18:35 | Nasdaq 100 (NQ) | long | 28477.5 | 28398.75 | ❌ SL | -0.29 % | 75 min |
| 12/11 18:25 | Nasdaq 100 (NQ) | long | 28481.75 | 28402.5 | ❌ SL | -0.29 % | 85 min |
| 12/11 18:21 | Nasdaq 100 (NQ) | long | 28496.75 | 28418.5 | ❌ SL | -0.28 % | 88 min |
| 12/11 18:16 | Nasdaq 100 (NQ) | long | 28503.25 | 28425.0 | ❌ SL | -0.28 % | 92 min |
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

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.0 |
| trend_15m | 1.0 |
| trend_1h | 1.0 |
| adx | 1.0 |
| vwap | 0.75 |
| rsi | 1.032 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.072 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [10, 12, 19]

Corrections par actif :

- bitcoin : {'macd': 0.576}
- ethereum : {'trend_5m': 0.839, 'trend_15m': 0.839, 'trend_1h': 0.839, 'adx': 0.839, 'rsi': 0.745}
- euro : {'trend_5m': 0.958, 'trend_15m': 0.958, 'trend_1h': 0.958, 'adx': 0.958, 'vwap': 0.72, 'rsi': 0.882}
- nasdaq : {'trend_5m': 1.002, 'trend_15m': 1.002, 'trend_1h': 1.002, 'adx': 1.002, 'rsi': 1.125}
- sp500 : {'trend_5m': 0.925, 'trend_15m': 0.925, 'trend_1h': 0.925, 'adx': 0.925, 'vwap': 0.69, 'rsi': 1.021, 'pdhl': 1.029}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 152 | -0.44 R | en test |
| horizon ~3 h | 234 | -0.31 R | en test |
| confiance moyenne | 82 | -0.11 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 24 | +0.58 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 52 | -0.14 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 64 | -0.45 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 68 | -0.40 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 64 | +0.11 R | en test |
| nouvel actif : Pétrole WTI (CL) | 141 | -0.08 R | en test |
| nouvel actif : Euro / dollar (6E) | 63 | -0.42 R | en test |

Notes :

- trades réels : +0,02 R ± 0,18 R par trade avant frais sur 187 trades (0 R = hasard)
- rsi : +0,07 R ± 0,06 R sur 1741 trades éq. → poids ×1,03
- pdhl : +0,20 R ± 0,17 R sur 255 trades éq. → poids ×1,07
- tranche 10h UTC : -0,27 R sur 108 trades éq. → évitée
- tranche 12h UTC : -0,42 R sur 69 trades éq. → évitée
- tranche 19h UTC : -0,30 R sur 89 trades éq. → évitée
- bitcoin, macd : -0,49 R contre -0,04 R en global sur 45 trades éq. → poids ×0,58 sur cet actif
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,20 R contre +0,04 R en global sur 140 trades éq. → poids ×0,84 sur cet actif
- ethereum, rsi : -0,24 R contre +0,07 R en global sur 100 trades éq. → poids ×0,72 sur cet actif
- euro, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,21 R contre +0,04 R en global sur 102 trades éq. → poids ×0,96 sur cet actif
- euro, vwap : -0,21 R contre +0,05 R en global sur 96 trades éq. → poids ×0,96 sur cet actif
- euro, rsi : -0,24 R contre +0,07 R en global sur 84 trades éq. → poids ×0,85 sur cet actif
- nasdaq, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,17 R contre +0,04 R en global sur 632 trades éq. → poids ×1,00 sur cet actif
- nasdaq, rsi : +0,26 R contre +0,07 R en global sur 492 trades éq. → poids ×1,09 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,14 R contre +0,04 R en global sur 236 trades éq. → poids ×0,93 sur cet actif
- sp500, vwap : -0,13 R contre +0,05 R en global sur 232 trades éq. → poids ×0,92 sur cet actif
- sp500, rsi : -0,09 R contre +0,07 R en global sur 195 trades éq. → poids ×0,99 sur cet actif
- sp500, pdhl : -0,19 R contre +0,20 R en global sur 31 trades éq. → poids ×0,96 sur cet actif
- variante « indices le matin européen » en test : 152 trades, -0,44 R net, pas meilleure que les signaux réels
- variante « horizon ~3 h » en test : 234 trades, -0,31 R net, pas meilleure que les signaux réels

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 15/11/2026 | 72 | 16 | 53 | 3 | 23% | 25% | -2% | -0.99 % | -0.014 % |
| S&P 500 (ES) | 09/07/2026 → 15/11/2026 | 143 | 52 | 72 | 19 | 42% | 42% | +0% | +0.22 % | +0.002 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 15/11/2026 | 88 | 26 | 45 | 17 | 37% | 41% | -4% | -6.75 % | -0.077 % |
| Ethereum (ETH/USD) | 20/07/2026 → 15/11/2026 | 89 | 21 | 49 | 19 | 30% | 40% | -10% | -11.75 % | -0.132 % |
| Or (XAU/USD) | 09/07/2026 → 15/11/2026 | 174 | 51 | 78 | 45 | 40% | 42% | -2% | -3.91 % | -0.022 % |
| Pétrole WTI (CL) | 14/07/2026 → 15/11/2026 | 231 | 68 | 123 | 40 | 36% | 41% | -6% | -11.25 % | -0.049 % |
| Euro / dollar (6E) | 14/07/2026 → 15/11/2026 | 55 | 14 | 33 | 8 | 30% | 40% | -10% | -1.25 % | -0.023 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
