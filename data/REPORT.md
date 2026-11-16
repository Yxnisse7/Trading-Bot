# Trading-Bot — rapport

_Mis à jour le 16/11/2026 à 10:56 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **184**
- Taux de réussite cumulé (TP / (TP+SL)) : **39%** — hasard attendu 38%, avantage **+1%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-7.83 %** (brut -3.63 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **1562** clôturés, 2 ouverts, taux de réussite 37% (hasard attendu 37%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 81 | 29 | 46 | 6 | 39% | -0.037 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 95 | 24 | 48 | 23 | 33% | -0.074 % |
| short | 89 | 34 | 43 | 12 | 44% | -0.009 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 180 | 57 | 89 | 34 | 39% | -0.042 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 183 | 58 | 91 | 34 | 39% | -0.042 % |
| corr | 17 | 5 | 8 | 4 | 38% | -0.015 % |
| level | 20 | 4 | 12 | 4 | 25% | -0.059 % |
| macd | 51 | 14 | 26 | 11 | 35% | -0.033 % |
| orb | 25 | 7 | 13 | 5 | 35% | -0.036 % |
| pdhl | 24 | 9 | 11 | 4 | 45% | -0.003 % |
| rsi | 158 | 53 | 74 | 31 | 42% | -0.024 % |
| trend_15m | 183 | 58 | 91 | 34 | 39% | -0.042 % |
| trend_1h | 183 | 58 | 91 | 34 | 39% | -0.042 % |
| trend_5m | 165 | 54 | 80 | 31 | 40% | -0.035 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 181 | 58 | 89 | 34 | 39% | -0.039 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 71 | 22 | 32 | 17 | 41% | -0.022 % |
| actualité chargée | 113 | 36 | 59 | 18 | 38% | -0.055 % |

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
| signaux du bot | 183 | 58 | 91 | 34 | 39% | -0.042 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 37 | 10 | 27 | 0 | 27% | -0.092 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 35, 57% terminés dans le bon sens, P&L moyen -0.005 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 1562 | 461 | 799 | 302 | 37% | -0.020 % |
| corr | 127 | 35 | 69 | 23 | 34% | -0.032 % |
| level | 148 | 52 | 59 | 37 | 47% | +0.035 % |
| macd | 392 | 103 | 211 | 78 | 33% | -0.046 % |
| orb | 96 | 31 | 38 | 27 | 45% | -0.011 % |
| pdhl | 163 | 63 | 81 | 19 | 44% | +0.080 % |
| rsi | 1169 | 363 | 594 | 212 | 38% | -0.009 % |
| trend_15m | 1562 | 461 | 799 | 302 | 37% | -0.020 % |
| trend_1h | 1536 | 453 | 787 | 296 | 37% | -0.019 % |
| trend_5m | 1398 | 428 | 722 | 248 | 37% | -0.017 % |
| volume | 29 | 5 | 20 | 4 | 20% | -0.197 % |
| vwap | 1528 | 456 | 782 | 290 | 37% | -0.018 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 86 | 21 | 42 | 23 | 33% | -0.100 % |
| ethereum | 74 | 17 | 44 | 13 | 28% | -0.186 % |
| euro | 62 | 19 | 37 | 6 | 34% | -0.023 % |
| gold | 564 | 186 | 233 | 145 | 44% | +0.004 % |
| nasdaq | 513 | 143 | 300 | 70 | 32% | +0.001 % |
| oil | 139 | 42 | 68 | 29 | 38% | -0.034 % |
| sp500 | 124 | 33 | 75 | 16 | 31% | -0.036 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 22/10 21:01 | Nasdaq 100 (NQ) | short | 29102.0 | 29178.5 | ❌ SL | -0.27 % | 59 min |
| 22/10 20:55 | Nasdaq 100 (NQ) | short | 29112.25 | 29182.5 | ❌ SL | -0.25 % | 65 min |
| 22/10 20:50 | Nasdaq 100 (NQ) | short | 29093.75 | 29167.0 | ❌ SL | -0.26 % | 69 min |

## Apprentissage

| Critère | Poids actuel |
|---|---:|
| trend_5m | 1.0 |
| trend_15m | 1.0 |
| trend_1h | 1.0 |
| adx | 1.0 |
| vwap | 0.75 |
| rsi | 1.014 |
| macd | 1.0 |
| level | 1.0 |
| volume | 0.75 |
| orb | 1.0 |
| pdhl | 1.072 |
| corr | 0.5 |

Tranches horaires évitées (UTC) : [10, 12, 19]

Corrections par actif :

- bitcoin : {'macd': 0.55}
- ethereum : {'trend_5m': 0.847, 'trend_15m': 0.847, 'trend_1h': 0.847, 'adx': 0.847, 'rsi': 0.751}
- euro : {'trend_5m': 0.994, 'trend_15m': 0.994, 'trend_1h': 0.994, 'adx': 0.994, 'vwap': 0.748, 'rsi': 0.919}
- nasdaq : {'rsi': 1.072}
- sp500 : {'trend_5m': 0.93, 'trend_15m': 0.93, 'trend_1h': 0.93, 'adx': 0.93, 'vwap': 0.693, 'pdhl': 1.029}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 152 | -0.44 R | en test |
| horizon ~3 h | 220 | -0.38 R | en test |
| confiance moyenne | 82 | -0.11 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 21 | +0.43 R | en test |
| reprise juste après un stop | 28 | -0.31 R | en test |
| nouvel actif : S&P 500 (ES) | 50 | -0.14 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 64 | -0.45 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 68 | -0.40 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 63 | +0.13 R | en test |
| nouvel actif : Pétrole WTI (CL) | 139 | -0.08 R | en test |
| nouvel actif : Euro / dollar (6E) | 62 | -0.41 R | en test |

Notes :

- trades réels : +0,04 R ± 0,19 R par trade avant frais sur 184 trades (0 R = hasard)
- rsi : +0,07 R ± 0,06 R sur 1722 trades éq. → poids ×1,01
- pdhl : +0,20 R ± 0,17 R sur 255 trades éq. → poids ×1,07
- tranche 10h UTC : -0,27 R sur 108 trades éq. → évitée
- tranche 12h UTC : -0,42 R sur 69 trades éq. → évitée
- tranche 19h UTC : -0,30 R sur 89 trades éq. → évitée
- bitcoin, macd : -0,49 R contre -0,03 R en global sur 45 trades éq. → poids ×0,55 sur cet actif
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,20 R contre +0,04 R en global sur 140 trades éq. → poids ×0,85 sur cet actif
- ethereum, rsi : -0,24 R contre +0,07 R en global sur 100 trades éq. → poids ×0,74 sur cet actif
- euro, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,20 R contre +0,04 R en global sur 101 trades éq. → poids ×0,99 sur cet actif
- euro, vwap : -0,20 R contre +0,05 R en global sur 95 trades éq. → poids ×1,00 sur cet actif
- euro, rsi : -0,23 R contre +0,07 R en global sur 83 trades éq. → poids ×0,91 sur cet actif
- nasdaq, rsi : +0,24 R contre +0,07 R en global sur 478 trades éq. → poids ×1,06 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,14 R contre +0,04 R en global sur 234 trades éq. → poids ×0,93 sur cet actif
- sp500, vwap : -0,13 R contre +0,05 R en global sur 230 trades éq. → poids ×0,92 sur cet actif
- sp500, pdhl : -0,19 R contre +0,20 R en global sur 31 trades éq. → poids ×0,96 sur cet actif
- variante « indices le matin européen » en test : 152 trades, -0,44 R net, pas meilleure que les signaux réels
- variante « horizon ~3 h » en test : 220 trades, -0,38 R net, pas meilleure que les signaux réels
- variante « confiance moyenne » en test : 82 trades, -0,11 R net, encore 18 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 21 trades, +0,43 R net, encore 79 trades avant décision

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
