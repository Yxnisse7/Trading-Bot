# Trading-Bot — rapport

_Mis à jour le 19/11/2026 à 13:41 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **188**
- Taux de réussite cumulé (TP / (TP+SL)) : **38%** — hasard attendu 38%, avantage **+0%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-8.81 %** (brut -4.57 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **1700** clôturés, 1 ouverts, taux de réussite 36% (hasard attendu 37%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 85 | 29 | 49 | 7 | 37% | -0.046 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 95 | 24 | 48 | 23 | 33% | -0.074 % |
| short | 93 | 34 | 46 | 13 | 42% | -0.019 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 184 | 57 | 92 | 35 | 38% | -0.046 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 187 | 58 | 94 | 35 | 38% | -0.046 % |
| corr | 20 | 5 | 11 | 4 | 31% | -0.111 % |
| level | 20 | 4 | 12 | 4 | 25% | -0.059 % |
| macd | 54 | 14 | 28 | 12 | 33% | -0.038 % |
| orb | 29 | 7 | 16 | 6 | 30% | -0.065 % |
| pdhl | 24 | 9 | 11 | 4 | 45% | -0.003 % |
| rsi | 162 | 53 | 77 | 32 | 41% | -0.030 % |
| trend_15m | 187 | 58 | 94 | 35 | 38% | -0.046 % |
| trend_1h | 187 | 58 | 94 | 35 | 38% | -0.046 % |
| trend_5m | 169 | 54 | 83 | 32 | 39% | -0.040 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 185 | 58 | 92 | 35 | 39% | -0.043 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 71 | 22 | 32 | 17 | 41% | -0.022 % |
| actualité chargée | 117 | 36 | 62 | 19 | 37% | -0.062 % |

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
| 15h | 39 | 15 | 18 | 6 | 45% | +0.041 % |
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
| signaux du bot | 187 | 58 | 94 | 35 | 38% | -0.046 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 41 | 10 | 30 | 1 | 25% | -0.108 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 36, 58% terminés dans le bon sens, P&L moyen +0.022 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 1700 | 498 | 890 | 312 | 36% | -0.025 % |
| corr | 148 | 37 | 88 | 23 | 30% | -0.070 % |
| level | 149 | 52 | 60 | 37 | 46% | +0.031 % |
| macd | 428 | 111 | 234 | 83 | 32% | -0.052 % |
| orb | 106 | 32 | 46 | 28 | 41% | -0.029 % |
| pdhl | 175 | 63 | 92 | 20 | 41% | +0.044 % |
| rsi | 1287 | 397 | 669 | 221 | 37% | -0.013 % |
| trend_15m | 1700 | 498 | 890 | 312 | 36% | -0.025 % |
| trend_1h | 1674 | 490 | 878 | 306 | 36% | -0.025 % |
| trend_5m | 1532 | 464 | 810 | 258 | 36% | -0.022 % |
| volume | 35 | 8 | 22 | 5 | 27% | -0.053 % |
| vwap | 1666 | 493 | 873 | 300 | 36% | -0.024 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 100 | 23 | 52 | 25 | 31% | -0.116 % |
| ethereum | 78 | 19 | 46 | 13 | 29% | -0.175 % |
| euro | 67 | 22 | 38 | 7 | 37% | -0.020 % |
| gold | 600 | 200 | 252 | 148 | 44% | +0.004 % |
| nasdaq | 574 | 153 | 349 | 72 | 30% | -0.014 % |
| oil | 150 | 45 | 75 | 30 | 38% | -0.042 % |
| sp500 | 131 | 36 | 78 | 17 | 32% | -0.031 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 16/11 16:25 | Nasdaq 100 (NQ) | short | 27435.0 | 27603.0 | ❌ SL | -0.62 % | 57 min |
| 16/11 16:21 | Nasdaq 100 (NQ) | short | 27428.25 | 27598.5 | ❌ SL | -0.63 % | 61 min |
| 16/11 16:16 | Nasdaq 100 (NQ) | short | 27402.25 | 27593.0 | ❌ SL | -0.71 % | 40 min |
| 16/11 16:11 | Nasdaq 100 (NQ) | short | 27473.0 | 27203.75 | ⏱️ expiré | +0.97 % | 1444 min |
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

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.0 |
| trend_15m | 1.0 |
| trend_1h | 1.0 |
| adx | 1.0 |
| vwap | 0.75 |
| rsi | 1.0 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.0 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [10, 12, 19]

Corrections par actif :

- bitcoin : {'macd': 0.584}
- ethereum : {'trend_5m': 0.906, 'trend_15m': 0.906, 'trend_1h': 0.906, 'adx': 0.906, 'rsi': 0.765}
- sp500 : {'trend_5m': 0.997, 'trend_15m': 0.997, 'trend_1h': 0.997, 'adx': 0.997, 'vwap': 0.746}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 152 | -0.44 R | en test |
| horizon ~3 h | 258 | -0.33 R | en test |
| confiance moyenne | 83 | -0.13 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 24 | +0.58 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 57 | -0.08 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 78 | -0.49 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 72 | -0.37 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 67 | +0.13 R | en test |
| nouvel actif : Pétrole WTI (CL) | 150 | -0.10 R | en test |
| nouvel actif : Euro / dollar (6E) | 67 | -0.35 R | en test |

Notes :

- trades réels : +0,03 R ± 0,18 R par trade avant frais sur 188 trades (0 R = hasard)
- tranche 10h UTC : -0,27 R sur 108 trades éq. → évitée
- tranche 12h UTC : -0,42 R sur 69 trades éq. → évitée
- tranche 19h UTC : -0,30 R sur 89 trades éq. → évitée
- bitcoin, macd : -0,47 R contre -0,04 R en global sur 51 trades éq. → poids ×0,58 sur cet actif
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,18 R contre +0,03 R en global sur 144 trades éq. → poids ×0,91 sur cet actif
- ethereum, rsi : -0,24 R contre +0,06 R en global sur 104 trades éq. → poids ×0,77 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,12 R contre +0,03 R en global sur 242 trades éq. → poids ×1,00 sur cet actif
- sp500, vwap : -0,12 R contre +0,03 R en global sur 237 trades éq. → poids ×0,99 sur cet actif
- variante « indices le matin européen » en test : 152 trades, -0,44 R net, pas meilleure que les signaux réels
- variante « horizon ~3 h » en test : 258 trades, -0,33 R net, pas meilleure que les signaux réels
- variante « confiance moyenne » en test : 83 trades, -0,13 R net, encore 17 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 24 trades, +0,58 R net, encore 76 trades avant décision
- variante « reprise juste après un stop » en test : 28 trades, -0,31 R net, encore 72 trades avant décision
- variante « nouvel actif : S&P 500 (ES) » en test : 57 trades, -0,08 R net, encore 43 trades avant décision
- variante « nouvel actif : Bitcoin (BTC/USD) » en test : 78 trades, -0,49 R net, encore 22 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 72 trades, -0,37 R net, encore 28 trades avant décision
- variante « horizon ~3 h sur Or (XAU/USD) » en test : 67 trades, +0,13 R net, encore 33 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 150 trades, -0,10 R net, pas meilleure que les signaux réels
- variante « nouvel actif : Euro / dollar (6E) » en test : 67 trades, -0,35 R net, encore 33 trades avant décision

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
