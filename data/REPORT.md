# Trading-Bot — rapport

_Mis à jour le 27/11/2026 à 09:41 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **190**
- Taux de réussite cumulé (TP / (TP+SL)) : **38%** — hasard attendu 38%, avantage **-0%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-9.75 %** (brut -5.49 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **2022** clôturés, 0 ouverts, taux de réussite 34% (hasard attendu 36%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 24 | 6 | 9 | 9 | 40% | -0.050 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 39 | 13 | 17 | 9 | 43% | -0.034 % |
| nasdaq | 87 | 29 | 51 | 7 | 36% | -0.056 % |
| sp500 | 29 | 8 | 13 | 8 | 38% | -0.018 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 95 | 24 | 48 | 23 | 33% | -0.074 % |
| short | 95 | 34 | 48 | 13 | 41% | -0.029 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 186 | 57 | 94 | 35 | 38% | -0.051 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 189 | 58 | 96 | 35 | 38% | -0.051 % |
| corr | 21 | 5 | 12 | 4 | 29% | -0.122 % |
| level | 20 | 4 | 12 | 4 | 25% | -0.059 % |
| macd | 55 | 14 | 29 | 12 | 33% | -0.043 % |
| orb | 30 | 7 | 17 | 6 | 29% | -0.083 % |
| pdhl | 25 | 9 | 12 | 4 | 43% | -0.017 % |
| rsi | 163 | 53 | 78 | 32 | 40% | -0.033 % |
| trend_15m | 189 | 58 | 96 | 35 | 38% | -0.051 % |
| trend_1h | 189 | 58 | 96 | 35 | 38% | -0.051 % |
| trend_5m | 171 | 54 | 85 | 32 | 39% | -0.045 % |
| volume | 6 | 2 | 3 | 1 | 40% | -0.114 % |
| vwap | 187 | 58 | 94 | 35 | 38% | -0.048 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 71 | 22 | 32 | 17 | 41% | -0.022 % |
| actualité chargée | 119 | 36 | 64 | 19 | 36% | -0.069 % |

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
| 15h | 40 | 15 | 19 | 6 | 44% | +0.025 % |
| 16h | 24 | 3 | 18 | 3 | 14% | -0.254 % |
| 17h | 19 | 4 | 12 | 3 | 25% | -0.087 % |
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
| signaux du bot | 189 | 58 | 96 | 35 | 38% | -0.051 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 145 | 48 | 62 | 35 | 44% | -0.026 % |
| 24h | 43 | 10 | 32 | 1 | 24% | -0.124 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 36, 58% terminés dans le bon sens, P&L moyen +0.022 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 2022 | 577 | 1102 | 343 | 34% | -0.040 % |
| corr | 214 | 61 | 126 | 27 | 33% | -0.007 % |
| level | 186 | 57 | 88 | 41 | 39% | -0.039 % |
| macd | 511 | 136 | 289 | 86 | 32% | -0.034 % |
| orb | 128 | 43 | 57 | 28 | 43% | +0.051 % |
| pdhl | 209 | 73 | 109 | 27 | 40% | +0.022 % |
| rsi | 1554 | 461 | 845 | 248 | 35% | -0.030 % |
| trend_15m | 2022 | 577 | 1102 | 343 | 34% | -0.040 % |
| trend_1h | 1996 | 569 | 1090 | 337 | 34% | -0.040 % |
| trend_5m | 1836 | 536 | 1011 | 289 | 35% | -0.037 % |
| volume | 54 | 12 | 36 | 6 | 25% | -0.118 % |
| vwap | 1979 | 567 | 1081 | 331 | 34% | -0.039 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 132 | 33 | 68 | 31 | 33% | -0.107 % |
| ethereum | 107 | 25 | 66 | 16 | 27% | -0.214 % |
| euro | 81 | 30 | 44 | 7 | 41% | -0.014 % |
| gold | 687 | 214 | 307 | 166 | 41% | -0.013 % |
| nasdaq | 704 | 180 | 452 | 72 | 28% | -0.037 % |
| oil | 165 | 50 | 82 | 33 | 38% | -0.038 % |
| sp500 | 146 | 45 | 83 | 18 | 35% | -0.010 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 24/11 16:56 | Nasdaq 100 (NQ) | short | 26135.75 | 26288.5 | ❌ SL | -0.59 % | 73 min |
| 19/11 18:11 | Nasdaq 100 (NQ) | short | 26921.0 | 27011.0 | ❌ SL | -0.34 % | 12 min |
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

Tranches horaires évitées (UTC) : [9, 10, 12, 19]

Corrections par actif :

- bitcoin : {'macd': 0.525, 'pdhl': 0.84}
- ethereum : {'trend_5m': 0.848, 'trend_15m': 0.848, 'trend_1h': 0.848, 'adx': 0.848, 'vwap': 0.702, 'rsi': 0.702, 'macd': 0.979, 'pdhl': 0.5}
- nasdaq : {'pdhl': 1.134}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 166 | -0.49 R | en test |
| horizon ~3 h | 322 | -0.28 R | en test |
| confiance moyenne | 91 | -0.11 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 31 | +0.30 R | en test |
| reprise juste après un stop | 33 | -0.06 R | en test |
| nouvel actif : S&P 500 (ES) | 72 | +0.06 R | en test |
| nouvel actif : Bitcoin (BTC/USD) | 110 | -0.42 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 101 | -0.44 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 77 | +0.04 R | en test |
| nouvel actif : Pétrole WTI (CL) | 165 | -0.10 R | en test |
| nouvel actif : Euro / dollar (6E) | 81 | -0.23 R | en test |

Notes :

- trades réels : +0,02 R ± 0,18 R par trade avant frais sur 190 trades (0 R = hasard)
- tranche 09h UTC : -0,21 R sur 167 trades éq. → évitée
- tranche 10h UTC : -0,27 R sur 110 trades éq. → évitée
- tranche 12h UTC : -0,42 R sur 71 trades éq. → évitée
- tranche 19h UTC : -0,28 R sur 94 trades éq. → évitée
- bitcoin, macd : -0,46 R contre -0,04 R en global sur 64 trades éq. → poids ×0,53 sur cet actif
- bitcoin, pdhl : -0,26 R contre +0,11 R en global sur 44 trades éq. → poids ×0,84 sur cet actif
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,21 R contre +0,00 R en global sur 186 trades éq. → poids ×0,85 sur cet actif
- ethereum, vwap : -0,21 R contre +0,01 R en global sur 115 trades éq. → poids ×0,94 sur cet actif
- ethereum, rsi : -0,27 R contre +0,03 R en global sur 135 trades éq. → poids ×0,70 sur cet actif
- ethereum, macd : -0,28 R contre -0,04 R en global sur 71 trades éq. → poids ×0,98 sur cet actif
- ethereum, pdhl : -0,53 R contre +0,11 R en global sur 34 trades éq. → poids ×0,50 sur cet actif
- nasdaq, pdhl : +0,58 R contre +0,11 R en global sur 75 trades éq. → poids ×1,13 sur cet actif
- variante « indices le matin européen » en test : 166 trades, -0,49 R net, pas meilleure que les signaux réels
- variante « horizon ~3 h » en test : 322 trades, -0,28 R net, pas meilleure que les signaux réels
- variante « confiance moyenne » en test : 91 trades, -0,11 R net, encore 9 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 31 trades, +0,30 R net, encore 69 trades avant décision
- variante « reprise juste après un stop » en test : 33 trades, -0,06 R net, encore 67 trades avant décision
- variante « nouvel actif : S&P 500 (ES) » en test : 72 trades, +0,06 R net, encore 28 trades avant décision
- variante « nouvel actif : Bitcoin (BTC/USD) » en test : 110 trades, -0,42 R net, pas meilleure que les signaux réels

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 23/11/2026 | 79 | 19 | 55 | 5 | 26% | 25% | +1% | +3.84 % | +0.049 % |
| S&P 500 (ES) | 09/07/2026 → 23/11/2026 | 157 | 57 | 78 | 22 | 42% | 42% | +1% | +1.39 % | +0.009 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 23/11/2026 | 115 | 34 | 61 | 20 | 36% | 41% | -5% | -7.48 % | -0.065 % |
| Ethereum (ETH/USD) | 20/07/2026 → 23/11/2026 | 109 | 29 | 57 | 23 | 34% | 40% | -7% | -11.66 % | -0.107 % |
| Or (XAU/USD) | 09/07/2026 → 23/11/2026 | 185 | 56 | 85 | 44 | 40% | 42% | -2% | -4.10 % | -0.022 % |
| Pétrole WTI (CL) | 14/07/2026 → 23/11/2026 | 238 | 62 | 129 | 47 | 32% | 41% | -9% | -14.99 % | -0.063 % |
| Euro / dollar (6E) | 14/07/2026 → 23/11/2026 | 60 | 15 | 38 | 7 | 28% | 40% | -12% | -1.46 % | -0.024 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
