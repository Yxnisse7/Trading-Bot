# Trading-Bot — rapport

_Mis à jour le 28/09/2026 à 17:55 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **78**
- Taux de réussite cumulé (TP / (TP+SL)) : **45%** — hasard attendu 41%, avantage **+4%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-3.53 %** (brut -1.03 %)
- Signaux ouverts : **3**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **122** clôturés, 4 ouverts, taux de réussite 40% (hasard attendu 41%)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 28/09 17:20 | S&P 500 (ES) | short | 7744.0 | 7728.0 | 7754.5 | fort | signaux du bot | 18:20 |
| 28/09 17:35 | Nasdaq 100 (NQ) | short | 30485.25 | 30426.75 | 30534.0 | fort | signaux du bot | 18:35 |
| 28/09 17:45 | Or (XAU/USD) | short | 4154.9 | 4138.7 | 4165.7 | fort | signaux du bot | 18:45 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 15 | 3 | 7 | 5 | 30% | -0.113 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 20 | 8 | 10 | 2 | 44% | -0.025 % |
| nasdaq | 19 | 11 | 7 | 1 | 61% | +0.024 % |
| sp500 | 13 | 6 | 6 | 1 | 50% | -0.000 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 43 | 14 | 20 | 9 | 41% | -0.067 % |
| short | 35 | 16 | 16 | 3 | 50% | -0.018 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 74 | 29 | 34 | 11 | 46% | -0.043 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 77 | 30 | 36 | 11 | 45% | -0.044 % |
| corr | 10 | 2 | 5 | 3 | 29% | -0.113 % |
| level | 7 | 2 | 5 | 0 | 29% | -0.067 % |
| macd | 18 | 6 | 12 | 0 | 33% | -0.124 % |
| orb | 6 | 2 | 4 | 0 | 33% | -0.052 % |
| pdhl | 12 | 3 | 8 | 1 | 27% | -0.118 % |
| rsi | 65 | 27 | 28 | 10 | 49% | -0.030 % |
| trend_15m | 77 | 30 | 36 | 11 | 45% | -0.044 % |
| trend_1h | 77 | 30 | 36 | 11 | 45% | -0.044 % |
| trend_5m | 69 | 29 | 29 | 11 | 50% | -0.032 % |
| volume | 4 | 1 | 3 | 0 | 25% | -0.182 % |
| vwap | 75 | 30 | 34 | 11 | 47% | -0.037 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 33 | 12 | 17 | 4 | 41% | -0.060 % |
| actualité chargée | 45 | 18 | 19 | 8 | 49% | -0.034 % |

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
| 14h | 9 | 3 | 6 | 0 | 33% | -0.088 % |
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
| signaux du bot | 77 | 30 | 36 | 11 | 45% | -0.044 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 76 | 30 | 34 | 12 | 47% | -0.039 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 12, 58% terminés dans le bon sens, P&L moyen -0.038 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 122 | 39 | 58 | 25 | 40% | -0.024 % |
| corr | 10 | 0 | 7 | 3 | 0% | -0.269 % |
| level | 15 | 4 | 4 | 7 | 50% | -0.045 % |
| macd | 27 | 7 | 14 | 6 | 33% | +0.003 % |
| orb | 4 | 3 | 0 | 1 | 100% | +0.075 % |
| pdhl | 13 | 3 | 5 | 5 | 38% | -0.018 % |
| rsi | 73 | 23 | 39 | 11 | 37% | -0.026 % |
| trend_15m | 122 | 39 | 58 | 25 | 40% | -0.024 % |
| trend_1h | 120 | 37 | 58 | 25 | 39% | -0.026 % |
| trend_5m | 90 | 34 | 45 | 11 | 43% | -0.007 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 121 | 39 | 57 | 25 | 41% | -0.020 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| gold | 26 | 11 | 12 | 3 | 48% | +0.023 % |
| nasdaq | 32 | 15 | 14 | 3 | 52% | +0.022 % |
| oil | 15 | 5 | 7 | 3 | 42% | -0.038 % |
| sp500 | 26 | 5 | 16 | 5 | 24% | -0.043 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 23/09 17:25 | S&P 500 (ES) | short | 7792.25 | 7782.75 | ✅ TP | +0.11 % | 9 min |
| 23/09 16:55 | Bitcoin (BTC/USD) | short | 84534.0 | 84748.0 | ❌ SL | -0.31 % | 20 min |
| 23/09 15:25 | Or (XAU/USD) | short | 4342.4 | 4348.1 | ❌ SL | -0.15 % | 2 min |
| 23/09 15:01 | Nasdaq 100 (NQ) | short | 30954.25 | 30978.25 | ❌ SL | -0.09 % | 22 min |
| 23/09 15:01 | S&P 500 (ES) | short | 7820.75 | 7824.25 | ❌ SL | -0.05 % | 23 min |
| 23/09 14:45 | Or (XAU/USD) | short | 4343.8 | 4335.2 | ✅ TP | +0.18 % | 25 min |
| 23/09 13:35 | Or (XAU/USD) | short | 4343.0 | 4334.6 | ✅ TP | +0.17 % | 2 min |
| 23/09 09:50 | Or (XAU/USD) | short | 4358.5 | 4353.8 | ⏱️ expiré | +0.09 % | 60 min |
| 23/09 09:05 | Or (XAU/USD) | short | 4369.9 | 4361.3 | ✅ TP | +0.18 % | 7 min |

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

- ethereum : {'trend_5m': 0.68, 'trend_15m': 0.68, 'trend_1h': 0.68, 'adx': 0.68, 'rsi': 0.98}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 30 | -0.34 R | en test |
| horizon ~3 h | 20 | -0.01 R | en test |
| confiance moyenne | 17 | -0.10 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 1 | +1.09 R | en test |
| reprise juste après un stop | 11 | -0.04 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| nouvel actif : Pétrole WTI (CL) | 15 | -0.07 R | en test |
| nouvel actif : Euro / dollar (6E) | 0 | n/a | en test |

Notes :

- trades réels : +0,09 R ± 0,26 R par trade avant frais sur 78 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,32 R contre +0,07 R en global sur 51 trades éq. → poids ×0,68 sur cet actif
- ethereum, rsi : -0,25 R contre +0,07 R en global sur 40 trades éq. → poids ×0,98 sur cet actif
- variante « indices le matin européen » en test : 30 trades, -0,34 R net, encore 70 trades avant décision
- variante « horizon ~3 h » en test : 20 trades, -0,01 R net, encore 80 trades avant décision
- variante « confiance moyenne » en test : 17 trades, -0,10 R net, encore 83 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 1 trades, +1,09 R net, encore 99 trades avant décision
- variante « reprise juste après un stop » en test : 11 trades, -0,04 R net, encore 89 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 15 trades, -0,07 R net, encore 85 trades avant décision

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
