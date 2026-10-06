# Trading-Bot — rapport

_Mis à jour le 06/10/2026 à 17:45 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **113**
- Taux de réussite cumulé (TP / (TP+SL)) : **47%** — hasard attendu 42%, avantage **+6%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-2.24 %** (brut +0.85 %)
- Signaux ouverts : **2**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **226** clôturés, 2 ouverts, taux de réussite 37% (hasard attendu 41%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 06/10 17:05 | Nasdaq 100 (NQ) | long | 31576.25 | 31654.75 | 31523.75 | fort | signaux du bot | 18:05 |
| 06/10 17:15 | S&P 500 (ES) | long | 7889.0 | 7902.25 | 7880.25 | fort | signaux du bot | 18:15 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 18 | 6 | 7 | 5 | 46% | -0.041 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 29 | 13 | 13 | 3 | 50% | -0.009 % |
| nasdaq | 33 | 15 | 13 | 5 | 54% | +0.022 % |
| sp500 | 22 | 7 | 9 | 6 | 44% | -0.008 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 62 | 20 | 27 | 15 | 43% | -0.039 % |
| short | 51 | 23 | 21 | 7 | 52% | +0.003 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 109 | 42 | 46 | 21 | 48% | -0.018 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 112 | 43 | 48 | 21 | 47% | -0.019 % |
| corr | 13 | 3 | 6 | 4 | 33% | -0.081 % |
| level | 14 | 4 | 8 | 2 | 33% | -0.035 % |
| macd | 27 | 8 | 16 | 3 | 33% | -0.090 % |
| orb | 11 | 3 | 7 | 1 | 30% | -0.072 % |
| pdhl | 20 | 7 | 9 | 4 | 44% | -0.027 % |
| rsi | 96 | 38 | 39 | 19 | 49% | -0.009 % |
| trend_15m | 112 | 43 | 48 | 21 | 47% | -0.019 % |
| trend_1h | 112 | 43 | 48 | 21 | 47% | -0.019 % |
| trend_5m | 101 | 40 | 40 | 21 | 50% | -0.012 % |
| volume | 5 | 2 | 3 | 0 | 40% | -0.083 % |
| vwap | 110 | 43 | 46 | 21 | 48% | -0.013 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 50 | 16 | 24 | 10 | 40% | -0.044 % |
| actualité chargée | 63 | 27 | 24 | 12 | 53% | -0.001 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 7 | 5 | 0 | 2 | 100% | +0.142 % |
| 08h | 5 | 1 | 4 | 0 | 20% | -0.177 % |
| 09h | 5 | 1 | 3 | 1 | 25% | -0.145 % |
| 10h | 2 | 1 | 0 | 1 | 100% | +0.065 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
| 13h | 6 | 0 | 5 | 1 | 0% | -0.107 % |
| 14h | 15 | 6 | 7 | 2 | 46% | -0.009 % |
| 15h | 19 | 6 | 11 | 2 | 35% | -0.083 % |
| 16h | 7 | 2 | 3 | 2 | 40% | +0.009 % |
| 17h | 6 | 2 | 1 | 3 | 67% | +0.054 % |
| 18h | 9 | 6 | 1 | 2 | 86% | +0.081 % |
| 19h | 11 | 6 | 4 | 1 | 60% | +0.041 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 112 | 43 | 48 | 21 | 47% | -0.019 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 111 | 43 | 46 | 22 | 48% | -0.015 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 22, 68% terminés dans le bon sens, P&L moyen +0.004 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 226 | 69 | 118 | 39 | 37% | -0.036 % |
| corr | 14 | 1 | 10 | 3 | 9% | -0.203 % |
| level | 25 | 7 | 9 | 9 | 44% | -0.081 % |
| macd | 60 | 13 | 37 | 10 | 26% | -0.077 % |
| orb | 8 | 3 | 4 | 1 | 43% | -0.127 % |
| pdhl | 29 | 8 | 15 | 6 | 35% | -0.019 % |
| rsi | 157 | 50 | 87 | 20 | 36% | -0.035 % |
| trend_15m | 226 | 69 | 118 | 39 | 37% | -0.036 % |
| trend_1h | 221 | 66 | 117 | 38 | 36% | -0.037 % |
| trend_5m | 184 | 64 | 98 | 22 | 40% | -0.024 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 222 | 69 | 114 | 39 | 38% | -0.033 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| euro | 19 | 7 | 11 | 1 | 39% | -0.023 % |
| gold | 37 | 14 | 17 | 6 | 45% | +0.007 % |
| nasdaq | 53 | 20 | 25 | 8 | 44% | -0.015 % |
| oil | 40 | 14 | 20 | 6 | 41% | -0.043 % |
| sp500 | 54 | 11 | 36 | 7 | 23% | -0.054 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 06/10 11:45 | Or (XAU/USD) | long | 4183.8 | 4178.4 | ❌ SL | -0.15 % | 19 min |
| 05/10 21:01 | Nasdaq 100 (NQ) | long | 31315.25 | 31368.75 | ✅ TP | +0.16 % | 17 min |
| 05/10 20:10 | S&P 500 (ES) | long | 7829.25 | 7839.25 | ⏱️ expiré | +0.12 % | 60 min |
| 05/10 19:56 | Nasdaq 100 (NQ) | long | 31303.5 | 31309.5 | ⏱️ expiré | +0.01 % | 65 min |
| 05/10 19:10 | S&P 500 (ES) | long | 7822.25 | 7829.0 | ⏱️ expiré | +0.08 % | 60 min |
| 05/10 17:01 | Nasdaq 100 (NQ) | long | 31225.0 | 31240.25 | ⏱️ expiré | +0.04 % | 60 min |
| 05/10 16:15 | S&P 500 (ES) | long | 7794.5 | 7808.75 | ✅ TP | +0.17 % | 4 min |
| 02/10 20:05 | Bitcoin (BTC/USD) | short | 84854.0 | 84531.0 | ✅ TP | +0.32 % | 26 min |
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

- sp500 : {'vwap': 0.742}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 44 | -0.37 R | en test |
| horizon ~3 h | 47 | -0.22 R | en test |
| confiance moyenne | 26 | -0.06 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 4 | +0.04 R | en test |
| reprise juste après un stop | 17 | -0.33 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| horizon ~3 h sur Or (XAU/USD) | 1 | -1.12 R | en test |
| nouvel actif : Pétrole WTI (CL) | 40 | -0.06 R | en test |
| nouvel actif : Euro / dollar (6E) | 19 | -0.34 R | en test |

Notes :

- trades réels : +0,13 R ± 0,21 R par trade avant frais sur 113 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- sp500, vwap : -0,16 R contre +0,04 R en global sur 132 trades éq. → poids ×0,99 sur cet actif
- variante « indices le matin européen » en test : 44 trades, -0,37 R net, encore 56 trades avant décision
- variante « horizon ~3 h » en test : 47 trades, -0,22 R net, encore 53 trades avant décision
- variante « confiance moyenne » en test : 26 trades, -0,06 R net, encore 74 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 4 trades, +0,04 R net, encore 96 trades avant décision
- variante « reprise juste après un stop » en test : 17 trades, -0,33 R net, encore 83 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « horizon ~3 h sur Or (XAU/USD) » en test : 1 trades, -1,12 R net, encore 99 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 40 trades, -0,06 R net, encore 60 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 19 trades, -0,34 R net, encore 81 trades avant décision
- sortie : stop remonté à l'entrée après +1,0 R ferait mieux (-0,06 R net contre -0,09 R, backtest) : à décider

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 04/10/2026 | 87 | 22 | 42 | 23 | 34% | 42% | -7% | -1.15 % | -0.013 % |
| S&P 500 (ES) | 09/07/2026 → 04/10/2026 | 104 | 35 | 53 | 16 | 40% | 42% | -2% | -0.64 % | -0.006 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 04/10/2026 | 55 | 20 | 23 | 12 | 47% | 41% | +6% | -0.99 % | -0.018 % |
| Ethereum (ETH/USD) | 20/07/2026 → 04/10/2026 | 56 | 11 | 27 | 18 | 29% | 40% | -11% | -6.67 % | -0.119 % |
| Or (XAU/USD) | 09/07/2026 → 04/10/2026 | 130 | 43 | 52 | 35 | 45% | 42% | +3% | -1.47 % | -0.011 % |
| Pétrole WTI (CL) | 14/07/2026 → 04/10/2026 | 186 | 60 | 85 | 41 | 41% | 41% | +0% | +2.42 % | +0.013 % |
| Euro / dollar (6E) | 14/07/2026 → 04/10/2026 | 31 | 9 | 19 | 3 | 32% | 40% | -8% | -0.65 % | -0.021 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
