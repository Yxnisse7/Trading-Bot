# Trading-Bot — rapport

_Mis à jour le 30/09/2026 à 02:15 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **87**
- Taux de réussite cumulé (TP / (TP+SL)) : **44%** — hasard attendu 41%, avantage **+2%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-4.33 %** (brut -1.70 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **142** clôturés, 0 ouverts, taux de réussite 38% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 15 | 3 | 7 | 5 | 30% | -0.113 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 24 | 10 | 12 | 2 | 45% | -0.026 % |
| nasdaq | 21 | 11 | 9 | 1 | 55% | +0.008 % |
| sp500 | 16 | 6 | 7 | 3 | 46% | -0.023 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 46 | 15 | 22 | 9 | 41% | -0.068 % |
| short | 41 | 17 | 19 | 5 | 47% | -0.029 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 83 | 31 | 39 | 13 | 44% | -0.048 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 86 | 32 | 41 | 13 | 44% | -0.049 % |
| corr | 10 | 2 | 5 | 3 | 29% | -0.113 % |
| level | 10 | 2 | 6 | 2 | 25% | -0.083 % |
| macd | 22 | 8 | 13 | 1 | 38% | -0.097 % |
| orb | 8 | 2 | 6 | 0 | 25% | -0.108 % |
| pdhl | 12 | 3 | 8 | 1 | 27% | -0.118 % |
| rsi | 74 | 29 | 33 | 12 | 47% | -0.037 % |
| trend_15m | 86 | 32 | 41 | 13 | 44% | -0.049 % |
| trend_1h | 86 | 32 | 41 | 13 | 44% | -0.049 % |
| trend_5m | 76 | 29 | 34 | 13 | 46% | -0.045 % |
| volume | 4 | 1 | 3 | 0 | 25% | -0.182 % |
| vwap | 84 | 32 | 39 | 13 | 45% | -0.042 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 39 | 13 | 21 | 5 | 38% | -0.070 % |
| actualité chargée | 48 | 19 | 20 | 9 | 49% | -0.034 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 6 | 4 | 0 | 2 | 100% | +0.142 % |
| 08h | 5 | 1 | 4 | 0 | 20% | -0.177 % |
| 09h | 3 | 0 | 2 | 1 | 0% | -0.237 % |
| 10h | 2 | 1 | 0 | 1 | 100% | +0.065 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
| 13h | 4 | 0 | 4 | 0 | 0% | -0.141 % |
| 14h | 10 | 3 | 7 | 0 | 30% | -0.106 % |
| 15h | 14 | 4 | 9 | 1 | 31% | -0.118 % |
| 16h | 4 | 1 | 2 | 1 | 33% | -0.065 % |
| 17h | 3 | 1 | 1 | 1 | 50% | -0.025 % |
| 18h | 6 | 5 | 0 | 1 | 100% | +0.078 % |
| 19h | 9 | 5 | 3 | 1 | 62% | +0.046 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 86 | 32 | 41 | 13 | 44% | -0.049 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 85 | 32 | 39 | 14 | 45% | -0.044 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 14, 50% terminés dans le bon sens, P&L moyen -0.039 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 142 | 44 | 71 | 27 | 38% | -0.024 % |
| corr | 10 | 0 | 7 | 3 | 0% | -0.269 % |
| level | 15 | 4 | 4 | 7 | 50% | -0.045 % |
| macd | 33 | 9 | 18 | 6 | 33% | -0.011 % |
| orb | 5 | 3 | 1 | 1 | 75% | +0.003 % |
| pdhl | 14 | 4 | 5 | 5 | 44% | +0.037 % |
| rsi | 90 | 27 | 51 | 12 | 35% | -0.022 % |
| trend_15m | 142 | 44 | 71 | 27 | 38% | -0.024 % |
| trend_1h | 140 | 42 | 71 | 27 | 37% | -0.025 % |
| trend_5m | 107 | 39 | 56 | 12 | 41% | -0.007 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 140 | 44 | 69 | 27 | 39% | -0.020 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| gold | 30 | 12 | 14 | 4 | 46% | +0.016 % |
| nasdaq | 37 | 16 | 18 | 3 | 47% | -0.004 % |
| oil | 21 | 8 | 9 | 4 | 47% | +0.031 % |
| sp500 | 31 | 5 | 21 | 5 | 19% | -0.058 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 24/09 20:25 | S&P 500 (ES) | long | 7763.5 | 7768.5 | ✅ TP | +0.05 % | 0 min |
| 24/09 19:35 | Nasdaq 100 (NQ) | long | 30722.75 | 30694.0 | ❌ SL | -0.10 % | 7 min |
| 24/09 17:25 | S&P 500 (ES) | short | 7728.75 | 7733.75 | ❌ SL | -0.07 % | 10 min |
| 24/09 17:25 | Nasdaq 100 (NQ) | short | 30519.5 | 30553.0 | ❌ SL | -0.12 % | 25 min |
| 24/09 17:15 | Or (XAU/USD) | short | 4285.4 | 4290.7 | ❌ SL | -0.14 % | 7 min |
| 24/09 14:35 | Bitcoin (BTC/USD) | short | 83370.0 | 83605.0 | ❌ SL | -0.34 % | 21 min |
| 24/09 13:35 | Bitcoin (BTC/USD) | short | 83461.0 | 83364.01 | ⏱️ expiré | +0.06 % | 60 min |
| 24/09 13:15 | Or (XAU/USD) | short | 4290.5 | 4300.0 | ❌ SL | -0.24 % | 4 min |
| 24/09 10:50 | Bitcoin (BTC/USD) | short | 83315.0 | 83543.0 | ❌ SL | -0.33 % | 7 min |
| 23/09 21:40 | S&P 500 (ES) | short | 7771.25 | 7763.75 | ✅ TP | +0.09 % | 10 min |
| 23/09 18:01 | Nasdaq 100 (NQ) | short | 30729.25 | 30682.5 | ✅ TP | +0.14 % | 48 min |
| 23/09 17:55 | S&P 500 (ES) | short | 7785.75 | 7778.25 | ✅ TP | +0.09 % | 5 min |
| 23/09 17:25 | Nasdaq 100 (NQ) | short | 30794.5 | 30760.25 | ✅ TP | +0.10 % | 9 min |

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

- ethereum : {'trend_5m': 0.759, 'trend_15m': 0.759, 'trend_1h': 0.759, 'adx': 0.759}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 33 | -0.34 R | en test |
| horizon ~3 h | 29 | -0.30 R | en test |
| confiance moyenne | 18 | -0.08 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 1 | +1.09 R | en test |
| reprise juste après un stop | 12 | -0.12 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| nouvel actif : Pétrole WTI (CL) | 21 | +0.09 R | en test |
| nouvel actif : Euro / dollar (6E) | 0 | n/a | en test |

Notes :

- trades réels : +0,03 R ± 0,25 R par trade avant frais sur 87 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,32 R contre +0,04 R en global sur 51 trades éq. → poids ×0,76 sur cet actif
- variante « indices le matin européen » en test : 33 trades, -0,34 R net, encore 67 trades avant décision
- variante « horizon ~3 h » en test : 29 trades, -0,30 R net, encore 71 trades avant décision
- variante « confiance moyenne » en test : 18 trades, -0,08 R net, encore 82 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 1 trades, +1,09 R net, encore 99 trades avant décision
- variante « reprise juste après un stop » en test : 12 trades, -0,12 R net, encore 88 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 21 trades, +0,09 R net, encore 79 trades avant décision

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 29/07/2026 → 27/09/2026 | 60 | 18 | 30 | 12 | 38% | 42% | -5% | -0.34 % | -0.006 % |
| S&P 500 (ES) | 29/07/2026 → 27/09/2026 | 81 | 33 | 35 | 13 | 49% | 42% | +7% | +0.48 % | +0.006 % |
| Bitcoin (BTC/USD) | 29/07/2026 → 27/09/2026 | 50 | 20 | 19 | 11 | 51% | 41% | +11% | +0.31 % | +0.006 % |
| Ethereum (ETH/USD) | 29/07/2026 → 27/09/2026 | 51 | 9 | 28 | 14 | 24% | 40% | -16% | -9.83 % | -0.193 % |
| Or (XAU/USD) | 29/07/2026 → 27/09/2026 | 85 | 27 | 33 | 25 | 45% | 42% | +3% | -1.11 % | -0.013 % |
| Pétrole WTI (CL) | 29/07/2026 → 27/09/2026 | 142 | 52 | 58 | 32 | 47% | 41% | +6% | +8.94 % | +0.063 % |
| Euro / dollar (6E) | 29/07/2026 → 27/09/2026 | 14 | 2 | 9 | 3 | 18% | 40% | -22% | -0.39 % | -0.028 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
