# Trading-Bot — rapport

_Mis à jour le 28/09/2026 à 10:05 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **75**
- Taux de réussite cumulé (TP / (TP+SL)) : **44%** — hasard attendu 42%, avantage **+3%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-3.81 %** (brut -1.36 %)
- Signaux ouverts : **1**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **101** clôturés, 4 ouverts, taux de réussite 38% (hasard attendu 41%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 28/09 10:05 | Or (XAU/USD) | short | 4191.1 | 4180.0 | 4198.5 | fort | signaux du bot | 11:05 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 15 | 3 | 7 | 5 | 30% | -0.113 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 18 | 7 | 9 | 2 | 44% | -0.026 % |
| nasdaq | 18 | 10 | 7 | 1 | 59% | +0.008 % |
| sp500 | 13 | 6 | 6 | 1 | 50% | -0.000 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 43 | 14 | 20 | 9 | 41% | -0.067 % |
| short | 32 | 14 | 15 | 3 | 48% | -0.029 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 71 | 27 | 33 | 11 | 45% | -0.049 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 74 | 28 | 35 | 11 | 44% | -0.049 % |
| corr | 10 | 2 | 5 | 3 | 29% | -0.113 % |
| level | 6 | 1 | 5 | 0 | 17% | -0.131 % |
| macd | 17 | 6 | 11 | 0 | 35% | -0.116 % |
| orb | 6 | 2 | 4 | 0 | 33% | -0.052 % |
| pdhl | 12 | 3 | 8 | 1 | 27% | -0.118 % |
| rsi | 62 | 25 | 27 | 10 | 48% | -0.036 % |
| trend_15m | 74 | 28 | 35 | 11 | 44% | -0.049 % |
| trend_1h | 74 | 28 | 35 | 11 | 44% | -0.049 % |
| trend_5m | 66 | 27 | 28 | 11 | 49% | -0.038 % |
| volume | 4 | 1 | 3 | 0 | 25% | -0.182 % |
| vwap | 72 | 28 | 33 | 11 | 46% | -0.042 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 32 | 11 | 17 | 4 | 39% | -0.072 % |
| actualité chargée | 43 | 17 | 18 | 8 | 49% | -0.035 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 6 | 4 | 0 | 2 | 100% | +0.142 % |
| 08h | 4 | 0 | 4 | 0 | 0% | -0.282 % |
| 09h | 3 | 0 | 2 | 1 | 0% | -0.237 % |
| 10h | 2 | 1 | 0 | 1 | 100% | +0.065 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
| 13h | 3 | 0 | 3 | 0 | 0% | -0.098 % |
| 14h | 8 | 2 | 6 | 0 | 25% | -0.139 % |
| 15h | 11 | 4 | 7 | 0 | 36% | -0.105 % |
| 16h | 3 | 1 | 1 | 1 | 50% | +0.006 % |
| 17h | 3 | 1 | 1 | 1 | 50% | -0.025 % |
| 18h | 5 | 4 | 0 | 1 | 100% | +0.062 % |
| 19h | 6 | 4 | 2 | 0 | 67% | +0.055 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 74 | 28 | 35 | 11 | 44% | -0.049 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 73 | 28 | 33 | 12 | 46% | -0.045 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 12, 58% terminés dans le bon sens, P&L moyen -0.038 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 101 | 30 | 49 | 22 | 38% | -0.034 % |
| corr | 10 | 0 | 7 | 3 | 0% | -0.269 % |
| level | 14 | 4 | 4 | 6 | 50% | -0.054 % |
| macd | 22 | 4 | 12 | 6 | 25% | -0.033 % |
| orb | 4 | 3 | 0 | 1 | 100% | +0.075 % |
| pdhl | 13 | 3 | 5 | 5 | 38% | -0.018 % |
| rsi | 60 | 18 | 32 | 10 | 36% | -0.021 % |
| trend_15m | 101 | 30 | 49 | 22 | 38% | -0.034 % |
| trend_1h | 99 | 28 | 49 | 22 | 36% | -0.037 % |
| trend_5m | 71 | 25 | 36 | 10 | 41% | -0.011 % |
| vwap | 100 | 30 | 48 | 22 | 38% | -0.029 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| gold | 15 | 5 | 9 | 1 | 36% | -0.029 % |
| nasdaq | 27 | 13 | 12 | 2 | 52% | +0.009 % |
| oil | 12 | 4 | 5 | 3 | 44% | +0.016 % |
| sp500 | 24 | 5 | 14 | 5 | 26% | -0.038 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 23/09 17:25 | S&P 500 (ES) | short | 7792.25 | 7782.75 | ✅ TP | +0.11 % | 9 min |
| 23/09 16:55 | Bitcoin (BTC/USD) | short | 84534.0 | 84748.0 | ❌ SL | -0.31 % | 20 min |
| 23/09 15:25 | Or (XAU/USD) | short | 4342.4 | 4348.1 | ❌ SL | -0.15 % | 2 min |
| 23/09 15:01 | Nasdaq 100 (NQ) | short | 30954.25 | 30978.25 | ❌ SL | -0.09 % | 22 min |
| 23/09 15:01 | S&P 500 (ES) | short | 7820.75 | 7824.25 | ❌ SL | -0.05 % | 23 min |
| 23/09 14:45 | Or (XAU/USD) | short | 4343.8 | 4335.2 | ✅ TP | +0.18 % | 25 min |
| 23/09 13:35 | Or (XAU/USD) | short | 4343.0 | 4334.6 | ✅ TP | +0.17 % | 2 min |
| 23/09 09:50 | Or (XAU/USD) | short | 4358.5 | 4353.8 | ⏱️ expiré | +0.09 % | 60 min |
| 23/09 09:05 | Or (XAU/USD) | short | 4369.9 | 4361.3 | ✅ TP | +0.18 % | 7 min |
| 22/09 21:30 | Nasdaq 100 (NQ) | long | 31006.75 | 31046.75 | ✅ TP | +0.12 % | 3 min |
| 22/09 20:15 | Nasdaq 100 (NQ) | long | 30970.0 | 30994.75 | ✅ TP | +0.07 % | 4 min |
| 22/09 19:01 | Nasdaq 100 (NQ) | long | 30942.75 | 30984.25 | ✅ TP | +0.12 % | 50 min |

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

- ethereum : {'trend_5m': 0.725, 'trend_15m': 0.725, 'trend_1h': 0.725, 'adx': 0.725}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 26 | -0.28 R | en test |
| horizon ~3 h | 15 | -0.17 R | en test |
| confiance moyenne | 11 | -0.55 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 0 | n/a | en test |
| reprise juste après un stop | 9 | -0.08 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| nouvel actif : Pétrole WTI (CL) | 12 | +0.09 R | en test |
| nouvel actif : Euro / dollar (6E) | 0 | n/a | en test |

Notes :

- trades réels : +0,06 R ± 0,26 R par trade avant frais sur 75 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,32 R contre +0,05 R en global sur 51 trades éq. → poids ×0,72 sur cet actif
- variante « indices le matin européen » en test : 26 trades, -0,28 R net, encore 74 trades avant décision
- variante « horizon ~3 h » en test : 15 trades, -0,17 R net, encore 85 trades avant décision
- variante « confiance moyenne » en test : 11 trades, -0,55 R net, encore 89 trades avant décision
- variante « reprise juste après un stop » en test : 9 trades, -0,08 R net, encore 91 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 12 trades, +0,09 R net, encore 88 trades avant décision

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
