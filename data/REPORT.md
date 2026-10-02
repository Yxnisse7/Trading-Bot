# Trading-Bot — rapport

_Mis à jour le 02/10/2026 à 16:20 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **100**
- Taux de réussite cumulé (TP / (TP+SL)) : **45%** — hasard attendu 42%, avantage **+3%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-3.68 %** (brut -0.89 %)
- Signaux ouverts : **1**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **192** clôturés, 1 ouverts, taux de réussite 34% (hasard attendu 41%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 02/10 15:55 | Nasdaq 100 (NQ) | long | 31178.5 | 31305.25 | 31094.0 | fort | signaux du bot | 16:55 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 15 | 3 | 7 | 5 | 30% | -0.113 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 27 | 12 | 12 | 3 | 50% | -0.010 % |
| nasdaq | 28 | 14 | 12 | 2 | 54% | +0.022 % |
| sp500 | 19 | 6 | 9 | 4 | 40% | -0.029 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 53 | 18 | 25 | 10 | 42% | -0.052 % |
| short | 47 | 19 | 21 | 7 | 48% | -0.020 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 96 | 36 | 44 | 16 | 45% | -0.035 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 99 | 37 | 46 | 16 | 45% | -0.036 % |
| corr | 12 | 2 | 6 | 4 | 25% | -0.101 % |
| level | 12 | 2 | 8 | 2 | 20% | -0.093 % |
| macd | 26 | 8 | 16 | 2 | 33% | -0.094 % |
| orb | 9 | 2 | 6 | 1 | 25% | -0.085 % |
| pdhl | 15 | 5 | 8 | 2 | 38% | -0.054 % |
| rsi | 85 | 34 | 37 | 14 | 48% | -0.024 % |
| trend_15m | 99 | 37 | 46 | 16 | 45% | -0.036 % |
| trend_1h | 99 | 37 | 46 | 16 | 45% | -0.036 % |
| trend_5m | 88 | 34 | 38 | 16 | 47% | -0.030 % |
| volume | 4 | 1 | 3 | 0 | 25% | -0.182 % |
| vwap | 97 | 37 | 44 | 16 | 46% | -0.030 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 44 | 15 | 23 | 6 | 39% | -0.056 % |
| actualité chargée | 56 | 22 | 23 | 11 | 49% | -0.022 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 7 | 5 | 0 | 2 | 100% | +0.142 % |
| 08h | 5 | 1 | 4 | 0 | 20% | -0.177 % |
| 09h | 4 | 1 | 2 | 1 | 33% | -0.144 % |
| 10h | 2 | 1 | 0 | 1 | 100% | +0.065 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
| 13h | 5 | 0 | 5 | 0 | 0% | -0.148 % |
| 14h | 14 | 5 | 7 | 2 | 42% | -0.022 % |
| 15h | 16 | 5 | 10 | 1 | 33% | -0.098 % |
| 16h | 6 | 1 | 3 | 2 | 25% | -0.044 % |
| 17h | 3 | 1 | 1 | 1 | 50% | -0.025 % |
| 18h | 7 | 5 | 1 | 1 | 83% | +0.042 % |
| 19h | 10 | 5 | 4 | 1 | 56% | +0.029 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 99 | 37 | 46 | 16 | 45% | -0.036 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 98 | 37 | 44 | 17 | 46% | -0.032 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 17, 59% terminés dans le bon sens, P&L moyen -0.015 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 192 | 54 | 103 | 35 | 34% | -0.046 % |
| corr | 12 | 1 | 8 | 3 | 11% | -0.213 % |
| level | 21 | 6 | 7 | 8 | 46% | -0.079 % |
| macd | 48 | 11 | 28 | 9 | 28% | -0.063 % |
| orb | 7 | 3 | 3 | 1 | 50% | -0.087 % |
| pdhl | 25 | 6 | 13 | 6 | 32% | -0.025 % |
| rsi | 128 | 35 | 76 | 17 | 32% | -0.056 % |
| trend_15m | 192 | 54 | 103 | 35 | 34% | -0.046 % |
| trend_1h | 187 | 51 | 102 | 34 | 33% | -0.047 % |
| trend_5m | 152 | 49 | 85 | 18 | 37% | -0.038 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 189 | 54 | 100 | 35 | 35% | -0.043 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| euro | 14 | 7 | 7 | 0 | 50% | -0.002 % |
| gold | 35 | 13 | 16 | 6 | 45% | +0.007 % |
| nasdaq | 45 | 16 | 22 | 7 | 42% | -0.022 % |
| oil | 29 | 9 | 15 | 5 | 38% | -0.069 % |
| sp500 | 46 | 6 | 34 | 6 | 15% | -0.076 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 02/10 15:35 | S&P 500 (ES) | long | 7789.75 | 7776.75 | ❌ SL | -0.18 % | 20 min |
| 01/10 20:20 | Nasdaq 100 (NQ) | short | 30714.5 | 30764.75 | ❌ SL | -0.17 % | 2 min |
| 01/10 17:15 | S&P 500 (ES) | short | 7680.0 | 7687.75 | ❌ SL | -0.11 % | 0 min |
| 01/10 16:55 | Nasdaq 100 (NQ) | short | 30706.75 | 30645.25 | ✅ TP | +0.19 % | 0 min |
| 01/10 16:10 | S&P 500 (ES) | short | 7698.0 | 7689.5 | ⏱️ expiré | +0.10 % | 60 min |
| 01/10 11:35 | Or (XAU/USD) | short | 4189.3 | 4182.8 | ✅ TP | +0.14 % | 24 min |
| 30/09 21:15 | Nasdaq 100 (NQ) | long | 30841.75 | 30807.0 | ❌ SL | -0.12 % | 34 min |
| 30/09 18:35 | Nasdaq 100 (NQ) | long | 30862.25 | 30835.25 | ❌ SL | -0.10 % | 10 min |
| 30/09 18:15 | Or (XAU/USD) | short | 4192.0 | 4187.3 | ⏱️ expiré | +0.09 % | 60 min |
| 30/09 17:30 | Nasdaq 100 (NQ) | long | 30822.0 | 30887.5 | ✅ TP | +0.20 % | 18 min |
| 30/09 16:40 | Nasdaq 100 (NQ) | long | 30827.25 | 30861.25 | ⏱️ expiré | +0.10 % | 65 min |
| 30/09 16:01 | Nasdaq 100 (NQ) | long | 30771.0 | 30885.5 | ✅ TP | +0.36 % | 4 min |
| 30/09 09:55 | Or (XAU/USD) | long | 4225.6 | 4232.4 | ✅ TP | +0.14 % | 26 min |
| 29/09 21:15 | Nasdaq 100 (NQ) | long | 30651.5 | 30614.25 | ❌ SL | -0.13 % | 25 min |
| 29/09 20:15 | Or (XAU/USD) | long | 4195.6 | 4203.0 | ✅ TP | +0.16 % | 0 min |
| 29/09 16:30 | Or (XAU/USD) | long | 4206.8 | 4196.3 | ❌ SL | -0.27 % | 6 min |
| 28/09 21:50 | S&P 500 (ES) | short | 7742.5 | 7744.5 | ⏱️ expiré | -0.04 % | 60 min |
| 28/09 21:20 | Or (XAU/USD) | short | 4165.1 | 4153.8 | ✅ TP | +0.25 % | 40 min |
| 28/09 18:25 | S&P 500 (ES) | short | 7744.0 | 7764.5 | ❌ SL | -0.27 % | 5 min |
| 28/09 17:45 | Or (XAU/USD) | short | 4154.9 | 4165.7 | ❌ SL | -0.28 % | 37 min |
| 28/09 17:35 | Nasdaq 100 (NQ) | short | 30485.25 | 30534.0 | ❌ SL | -0.17 % | 34 min |
| 28/09 17:20 | S&P 500 (ES) | short | 7744.0 | 7746.75 | ⏱️ expiré | -0.05 % | 60 min |
| 28/09 16:50 | Nasdaq 100 (NQ) | short | 30501.25 | 30402.25 | ✅ TP | +0.31 % | 4 min |
| 28/09 15:40 | Or (XAU/USD) | short | 4171.0 | 4181.5 | ❌ SL | -0.27 % | 1 min |
| 28/09 10:05 | Or (XAU/USD) | short | 4191.1 | 4180.0 | ✅ TP | +0.24 % | 16 min |
| 28/09 09:01 | Or (XAU/USD) | short | 4205.3 | 4194.6 | ✅ TP | +0.23 % | 9 min |
| 25/09 18:15 | S&P 500 (ES) | long | 7807.0 | 7797.0 | ❌ SL | -0.14 % | 4 min |
| 25/09 16:05 | Bitcoin (BTC/USD) | short | 83227.0 | 83434.0 | ❌ SL | -0.31 % | 2 min |
| 25/09 12:50 | Or (XAU/USD) | long | 4338.6 | 4349.4 | ✅ TP | +0.23 % | 16 min |
| 24/09 21:10 | S&P 500 (ES) | long | 7772.5 | 7766.5 | ❌ SL | -0.09 % | 5 min |

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

Corrections par actif :

- sp500 : {'trend_5m': 0.839, 'trend_15m': 0.839, 'trend_1h': 0.839, 'adx': 0.839, 'vwap': 0.603, 'rsi': 0.939}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 40 | -0.42 R | en test |
| horizon ~3 h | 39 | -0.40 R | en test |
| confiance moyenne | 23 | -0.23 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 4 | +0.04 R | en test |
| reprise juste après un stop | 15 | -0.40 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| nouvel actif : Pétrole WTI (CL) | 29 | -0.13 R | en test |
| nouvel actif : Euro / dollar (6E) | 14 | +0.02 R | en test |

Notes :

- trades réels : +0,06 R ± 0,23 R par trade avant frais sur 100 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,27 R contre -0,01 R en global sur 123 trades éq. → poids ×0,84 sur cet actif
- sp500, vwap : -0,27 R contre +0,01 R en global sur 120 trades éq. → poids ×0,80 sur cet actif
- sp500, rsi : -0,24 R contre -0,01 R en global sur 108 trades éq. → poids ×0,94 sur cet actif
- variante « indices le matin européen » en test : 40 trades, -0,42 R net, encore 60 trades avant décision
- variante « horizon ~3 h » en test : 39 trades, -0,40 R net, encore 61 trades avant décision
- variante « confiance moyenne » en test : 23 trades, -0,23 R net, encore 77 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 4 trades, +0,04 R net, encore 96 trades avant décision
- variante « reprise juste après un stop » en test : 15 trades, -0,40 R net, encore 85 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 29 trades, -0,13 R net, encore 71 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 14 trades, +0,02 R net, encore 86 trades avant décision
- sortie : stop remonté à l'entrée après +1,0 R ferait mieux (-0,06 R net contre -0,08 R, backtest) : à décider

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 30/09/2026 | 82 | 21 | 39 | 22 | 35% | 41% | -6% | -1.06 % | -0.013 % |
| S&P 500 (ES) | 09/07/2026 → 30/09/2026 | 101 | 35 | 50 | 16 | 41% | 42% | -1% | -0.23 % | -0.002 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 30/09/2026 | 52 | 17 | 23 | 12 | 42% | 41% | +2% | -1.93 % | -0.037 % |
| Ethereum (ETH/USD) | 20/07/2026 → 30/09/2026 | 56 | 11 | 27 | 18 | 29% | 40% | -11% | -6.67 % | -0.119 % |
| Or (XAU/USD) | 09/07/2026 → 30/09/2026 | 124 | 41 | 50 | 33 | 45% | 42% | +3% | -1.40 % | -0.011 % |
| Pétrole WTI (CL) | 14/07/2026 → 30/09/2026 | 181 | 60 | 81 | 40 | 43% | 41% | +1% | +3.92 % | +0.022 % |
| Euro / dollar (6E) | 14/07/2026 → 30/09/2026 | 22 | 5 | 14 | 3 | 26% | 40% | -14% | -0.54 % | -0.025 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
