# Trading-Bot — rapport

_Mis à jour le 23/09/2026 à 22:45 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **61**
- Taux de réussite cumulé (TP / (TP+SL)) : **50%** — hasard attendu 41%, avantage **+9%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-2.50 %** (brut -0.43 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **41** clôturés, 1 ouverts, taux de réussite 48% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 11 | 3 | 4 | 4 | 43% | -0.070 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 14 | 5 | 7 | 2 | 42% | -0.039 % |
| nasdaq | 16 | 10 | 5 | 1 | 67% | +0.023 % |
| sp500 | 9 | 5 | 3 | 1 | 62% | +0.027 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 38 | 12 | 17 | 9 | 41% | -0.075 % |
| short | 23 | 13 | 8 | 2 | 62% | +0.015 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 57 | 24 | 23 | 10 | 51% | -0.038 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 60 | 25 | 25 | 10 | 50% | -0.039 % |
| corr | 10 | 2 | 5 | 3 | 29% | -0.113 % |
| level | 5 | 1 | 4 | 0 | 20% | -0.133 % |
| macd | 13 | 6 | 7 | 0 | 46% | -0.102 % |
| orb | 5 | 2 | 3 | 0 | 40% | -0.048 % |
| pdhl | 8 | 2 | 6 | 0 | 25% | -0.128 % |
| rsi | 51 | 22 | 19 | 10 | 54% | -0.029 % |
| trend_15m | 60 | 25 | 25 | 10 | 50% | -0.039 % |
| trend_1h | 60 | 25 | 25 | 10 | 50% | -0.039 % |
| trend_5m | 54 | 24 | 20 | 10 | 55% | -0.026 % |
| volume | 2 | 1 | 1 | 0 | 50% | -0.043 % |
| vwap | 58 | 25 | 23 | 10 | 52% | -0.030 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 24 | 8 | 12 | 4 | 40% | -0.076 % |
| actualité chargée | 37 | 17 | 13 | 7 | 57% | -0.018 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 5 | 3 | 0 | 2 | 100% | +0.124 % |
| 08h | 3 | 0 | 3 | 0 | 0% | -0.265 % |
| 09h | 3 | 0 | 2 | 1 | 0% | -0.237 % |
| 10h | 1 | 0 | 0 | 1 | n/a | -0.098 % |
| 11h | 4 | 2 | 1 | 1 | 67% | +0.114 % |
| 12h | 5 | 3 | 2 | 0 | 60% | +0.043 % |
| 13h | 3 | 0 | 3 | 0 | 0% | -0.098 % |
| 14h | 7 | 2 | 5 | 0 | 29% | -0.114 % |
| 15h | 8 | 4 | 4 | 0 | 50% | -0.102 % |
| 16h | 2 | 1 | 0 | 1 | 100% | +0.077 % |
| 17h | 2 | 1 | 0 | 1 | 100% | +0.014 % |
| 18h | 4 | 3 | 0 | 1 | 100% | +0.064 % |
| 19h | 5 | 4 | 1 | 0 | 80% | +0.084 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 60 | 25 | 25 | 10 | 50% | -0.039 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 59 | 25 | 23 | 11 | 52% | -0.033 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 11, 55% terminés dans le bon sens, P&L moyen -0.047 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 41 | 16 | 17 | 8 | 48% | -0.038 % |
| corr | 8 | 0 | 5 | 3 | 0% | -0.272 % |
| level | 7 | 2 | 3 | 2 | 40% | -0.151 % |
| macd | 6 | 1 | 4 | 1 | 20% | -0.160 % |
| orb | 2 | 2 | 0 | 0 | 100% | +0.112 % |
| pdhl | 1 | 0 | 1 | 0 | 0% | -0.095 % |
| rsi | 14 | 8 | 5 | 1 | 62% | +0.096 % |
| trend_15m | 41 | 16 | 17 | 8 | 48% | -0.038 % |
| trend_1h | 39 | 14 | 17 | 8 | 45% | -0.045 % |
| trend_5m | 24 | 13 | 10 | 1 | 57% | +0.025 % |
| vwap | 40 | 16 | 16 | 8 | 50% | -0.026 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 5 | 1 | 0 | 4 | 100% | +0.070 % |
| ethereum | 10 | 1 | 6 | 3 | 14% | -0.225 % |
| gold | 6 | 3 | 3 | 0 | 50% | +0.051 % |
| nasdaq | 13 | 8 | 4 | 1 | 67% | +0.056 % |
| oil | 4 | 1 | 3 | 0 | 25% | -0.203 % |
| sp500 | 3 | 2 | 1 | 0 | 67% | +0.047 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 22/09 17:01 | Or (XAU/USD) | short | 4358.8 | 4366.2 | ❌ SL | -0.19 % | 0 min |
| 22/09 16:45 | Nasdaq 100 (NQ) | long | 30953.75 | 30901.0 | ❌ SL | -0.18 % | 7 min |
| 22/09 13:40 | Or (XAU/USD) | short | 4354.2 | 4361.8 | ❌ SL | -0.19 % | 21 min |
| 22/09 12:55 | Bitcoin (BTC/USD) | long | 85942.0 | 85909.14 | ⏱️ expiré | -0.10 % | 60 min |
| 22/09 11:40 | Bitcoin (BTC/USD) | long | 85960.0 | 85924.53 | ⏱️ expiré | -0.10 % | 60 min |
| 22/09 10:10 | Or (XAU/USD) | short | 4336.6 | 4346.7 | ❌ SL | -0.25 % | 9 min |
| 22/09 09:25 | Or (XAU/USD) | short | 4358.5 | 4348.4 | ✅ TP | +0.21 % | 4 min |
| 22/09 05:55 | Ethereum (ETH/USD) | short | 2733.7 | 2732.44 | ⏱️ expiré | -0.03 % | 60 min |
| 22/09 01:55 | Bitcoin (BTC/USD) | long | 86554.0 | 86208.0 | ❌ SL | -0.46 % | 44 min |
| 22/09 00:34 | Bitcoin (BTC/USD) | long | 86455.0 | 86369.87 | ⏱️ expiré | -0.16 % | 61 min |
| 22/09 00:26 | Ethereum (ETH/USD) | long | 2776.6 | 2772.37 | ⏱️ expiré | -0.23 % | 65 min |
| 21/09 21:40 | Bitcoin (BTC/USD) | long | 86600.0 | 87020.0 | ✅ TP | +0.42 % | 45 min |
| 21/09 20:10 | S&P 500 (ES) | long | 7828.25 | 7835.0 | ✅ TP | +0.08 % | 11 min |
| 21/09 20:10 | Nasdaq 100 (NQ) | long | 30715.0 | 30758.75 | ✅ TP | +0.13 % | 17 min |

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

- ethereum : {'trend_5m': 0.963, 'trend_15m': 0.963, 'trend_1h': 0.963, 'adx': 0.963}
- oil : {'trend_5m': 0.964, 'trend_15m': 0.964, 'trend_1h': 0.964, 'adx': 0.964, 'vwap': 0.652}
- sp500 : {'trend_5m': 1.021, 'trend_15m': 1.021, 'trend_1h': 1.021, 'adx': 1.021}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 3 | -1.16 R | en test |
| horizon ~3 h | 4 | +0.64 R | en test |
| confiance moyenne | 0 | n/a | en test |
| entrées dans l'heure avant l'ouverture américaine | 0 | n/a | en test |
| reprise juste après un stop | 3 | +1.27 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 4 | -0.38 R | en test |
| nouvel actif : Pétrole WTI (CL) | 4 | -0.44 R | en test |
| nouvel actif : Euro / dollar (6E) | 0 | n/a | en test |

Notes :

- trades réels : +0,17 R ± 0,29 R par trade avant frais sur 61 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,23 R contre +0,06 R en global sur 50 trades éq. → poids ×0,96 sur cet actif
- oil, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,15 R contre +0,06 R en global sur 119 trades éq. → poids ×0,96 sur cet actif
- oil, vwap : -0,16 R contre +0,10 R en global sur 116 trades éq. → poids ×0,87 sur cet actif
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : +0,34 R contre +0,06 R en global sur 72 trades éq. → poids ×1,02 sur cet actif
- variante « indices le matin européen » en test : 3 trades, -1,16 R net, encore 97 trades avant décision
- variante « horizon ~3 h » en test : 4 trades, +0,64 R net, encore 96 trades avant décision
- variante « reprise juste après un stop » en test : 3 trades, +1,27 R net, encore 97 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 4 trades, -0,38 R net, encore 96 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 4 trades, -0,44 R net, encore 96 trades avant décision

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 24/07/2026 → 22/09/2026 | 65 | 19 | 38 | 8 | 33% | 41% | -8% | -1.33 % | -0.021 % |
| S&P 500 (ES) | 24/07/2026 → 22/09/2026 | 92 | 46 | 42 | 4 | 52% | 41% | +11% | +1.07 % | +0.012 % |
| Bitcoin (BTC/USD) | 24/07/2026 → 22/09/2026 | 44 | 14 | 20 | 10 | 41% | 41% | +1% | -1.70 % | -0.039 % |
| Ethereum (ETH/USD) | 24/07/2026 → 22/09/2026 | 52 | 11 | 27 | 14 | 29% | 40% | -11% | -6.64 % | -0.128 % |
| Or (XAU/USD) | 24/07/2026 → 22/09/2026 | 112 | 27 | 48 | 37 | 36% | 42% | -6% | -3.06 % | -0.027 % |
| Pétrole WTI (CL) | 24/07/2026 → 22/09/2026 | 122 | 36 | 73 | 13 | 33% | 41% | -8% | -7.77 % | -0.064 % |
| Euro / dollar (6E) | 24/07/2026 → 22/09/2026 | 15 | 5 | 8 | 2 | 38% | 40% | -2% | -0.20 % | -0.013 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
