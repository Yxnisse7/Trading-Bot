# Trading-Bot — rapport

_Mis à jour le 02/10/2026 à 20:05 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **105**
- Taux de réussite cumulé (TP / (TP+SL)) : **46%** — hasard attendu 42%, avantage **+4%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-2.99 %** (brut -0.04 %)
- Signaux ouverts : **1**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **195** clôturés, 1 ouverts, taux de réussite 34% (hasard attendu 41%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 02/10 20:05 | Bitcoin (BTC/USD) | short | 84854.0 | 84531.0 | 85070.0 | fort | signaux du bot | 21:05 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 17 | 5 | 7 | 5 | 42% | -0.062 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 28 | 13 | 12 | 3 | 52% | -0.004 % |
| nasdaq | 30 | 14 | 13 | 3 | 52% | +0.017 % |
| sp500 | 19 | 6 | 9 | 4 | 40% | -0.029 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 55 | 18 | 26 | 11 | 41% | -0.051 % |
| short | 50 | 22 | 21 | 7 | 51% | -0.003 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 101 | 39 | 45 | 17 | 46% | -0.026 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 104 | 40 | 47 | 17 | 46% | -0.027 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 13 | 3 | 8 | 2 | 27% | -0.062 % |
| macd | 26 | 8 | 16 | 2 | 33% | -0.094 % |
| orb | 10 | 2 | 7 | 1 | 22% | -0.096 % |
| pdhl | 18 | 6 | 9 | 3 | 40% | -0.042 % |
| rsi | 89 | 36 | 38 | 15 | 49% | -0.017 % |
| trend_15m | 104 | 40 | 47 | 17 | 46% | -0.027 % |
| trend_1h | 104 | 40 | 47 | 17 | 46% | -0.027 % |
| trend_5m | 93 | 37 | 39 | 17 | 49% | -0.021 % |
| volume | 5 | 2 | 3 | 0 | 40% | -0.083 % |
| vwap | 102 | 40 | 45 | 17 | 47% | -0.022 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 46 | 15 | 24 | 7 | 38% | -0.056 % |
| actualité chargée | 59 | 25 | 23 | 11 | 52% | -0.007 % |

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
| 13h | 6 | 0 | 5 | 1 | 0% | -0.107 % |
| 14h | 14 | 5 | 7 | 2 | 42% | -0.022 % |
| 15h | 18 | 6 | 11 | 1 | 35% | -0.089 % |
| 16h | 7 | 2 | 3 | 2 | 40% | +0.009 % |
| 17h | 4 | 2 | 1 | 1 | 67% | +0.060 % |
| 18h | 7 | 5 | 1 | 1 | 83% | +0.042 % |
| 19h | 10 | 5 | 4 | 1 | 56% | +0.029 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 104 | 40 | 47 | 17 | 46% | -0.027 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 103 | 40 | 45 | 18 | 47% | -0.024 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 18, 61% terminés dans le bon sens, P&L moyen -0.008 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 195 | 54 | 105 | 36 | 34% | -0.049 % |
| corr | 12 | 1 | 8 | 3 | 11% | -0.213 % |
| level | 21 | 6 | 7 | 8 | 46% | -0.079 % |
| macd | 51 | 11 | 30 | 10 | 27% | -0.072 % |
| orb | 8 | 3 | 4 | 1 | 43% | -0.127 % |
| pdhl | 26 | 6 | 14 | 6 | 30% | -0.040 % |
| rsi | 131 | 35 | 78 | 18 | 31% | -0.060 % |
| trend_15m | 195 | 54 | 105 | 36 | 34% | -0.049 % |
| trend_1h | 190 | 51 | 104 | 35 | 33% | -0.050 % |
| trend_5m | 155 | 49 | 87 | 19 | 36% | -0.041 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 192 | 54 | 102 | 36 | 35% | -0.045 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| euro | 15 | 7 | 7 | 1 | 50% | -0.006 % |
| gold | 35 | 13 | 16 | 6 | 45% | +0.007 % |
| nasdaq | 45 | 16 | 22 | 7 | 42% | -0.022 % |
| oil | 30 | 9 | 16 | 5 | 36% | -0.081 % |
| sp500 | 47 | 6 | 35 | 6 | 15% | -0.078 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 02/10 19:15 | Bitcoin (BTC/USD) | short | 84893.0 | 84574.0 | ✅ TP | +0.32 % | 8 min |
| 02/10 18:20 | Bitcoin (BTC/USD) | short | 85304.0 | 84974.0 | ✅ TP | +0.33 % | 53 min |
| 02/10 17:55 | Or (XAU/USD) | short | 4161.0 | 4153.9 | ✅ TP | +0.15 % | 1 min |
| 02/10 17:01 | Nasdaq 100 (NQ) | long | 31213.25 | 31154.0 | ❌ SL | -0.20 % | 0 min |
| 02/10 15:55 | Nasdaq 100 (NQ) | long | 31178.5 | 31212.75 | ⏱️ expiré | +0.10 % | 65 min |
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

- sp500 : {'trend_5m': 0.807, 'trend_15m': 0.807, 'trend_1h': 0.807, 'adx': 0.807, 'vwap': 0.579, 'rsi': 0.911}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 40 | -0.42 R | en test |
| horizon ~3 h | 39 | -0.40 R | en test |
| confiance moyenne | 23 | -0.23 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 4 | +0.04 R | en test |
| reprise juste après un stop | 16 | -0.44 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| nouvel actif : Pétrole WTI (CL) | 30 | -0.16 R | en test |
| nouvel actif : Euro / dollar (6E) | 15 | -0.05 R | en test |

Notes :

- trades réels : +0,09 R ± 0,22 R par trade avant frais sur 105 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,27 R contre -0,00 R en global sur 124 trades éq. → poids ×0,81 sur cet actif
- sp500, vwap : -0,28 R contre +0,01 R en global sur 121 trades éq. → poids ×0,77 sur cet actif
- sp500, rsi : -0,25 R contre -0,01 R en global sur 109 trades éq. → poids ×0,91 sur cet actif
- variante « indices le matin européen » en test : 40 trades, -0,42 R net, encore 60 trades avant décision
- variante « horizon ~3 h » en test : 39 trades, -0,40 R net, encore 61 trades avant décision
- variante « confiance moyenne » en test : 23 trades, -0,23 R net, encore 77 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 4 trades, +0,04 R net, encore 96 trades avant décision
- variante « reprise juste après un stop » en test : 16 trades, -0,44 R net, encore 84 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 30 trades, -0,16 R net, encore 70 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 15 trades, -0,05 R net, encore 85 trades avant décision
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
