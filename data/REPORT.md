# Trading-Bot — rapport

_Mis à jour le 24/09/2026 à 16:25 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **65**
- Taux de réussite cumulé (TP / (TP+SL)) : **47%** — hasard attendu 41%, avantage **+6%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-3.36 %** (brut -1.09 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **68** clôturés, 2 ouverts, taux de réussite 41% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 14 | 3 | 6 | 5 | 33% | -0.099 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 15 | 5 | 8 | 2 | 38% | -0.052 % |
| nasdaq | 16 | 10 | 5 | 1 | 67% | +0.023 % |
| sp500 | 9 | 5 | 3 | 1 | 62% | +0.027 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 38 | 12 | 17 | 9 | 41% | -0.075 % |
| short | 27 | 13 | 11 | 3 | 54% | -0.019 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 61 | 24 | 26 | 11 | 48% | -0.050 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 64 | 25 | 28 | 11 | 47% | -0.050 % |
| corr | 10 | 2 | 5 | 3 | 29% | -0.113 % |
| level | 5 | 1 | 4 | 0 | 20% | -0.133 % |
| macd | 14 | 6 | 8 | 0 | 43% | -0.119 % |
| orb | 5 | 2 | 3 | 0 | 40% | -0.048 % |
| pdhl | 11 | 2 | 8 | 1 | 20% | -0.149 % |
| rsi | 53 | 22 | 21 | 10 | 51% | -0.039 % |
| trend_15m | 64 | 25 | 28 | 11 | 47% | -0.050 % |
| trend_1h | 64 | 25 | 28 | 11 | 47% | -0.050 % |
| trend_5m | 58 | 24 | 23 | 11 | 51% | -0.039 % |
| volume | 3 | 1 | 2 | 0 | 33% | -0.140 % |
| vwap | 62 | 25 | 26 | 11 | 49% | -0.042 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 25 | 8 | 13 | 4 | 38% | -0.087 % |
| actualité chargée | 40 | 17 | 15 | 8 | 53% | -0.029 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 5 | 3 | 0 | 2 | 100% | +0.124 % |
| 08h | 4 | 0 | 4 | 0 | 0% | -0.282 % |
| 09h | 3 | 0 | 2 | 1 | 0% | -0.237 % |
| 10h | 1 | 0 | 0 | 1 | n/a | -0.098 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
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
| signaux du bot | 64 | 25 | 28 | 11 | 47% | -0.050 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 63 | 25 | 26 | 12 | 49% | -0.044 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 12, 58% terminés dans le bon sens, P&L moyen -0.038 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 68 | 22 | 32 | 14 | 41% | -0.036 % |
| corr | 9 | 0 | 6 | 3 | 0% | -0.254 % |
| level | 10 | 3 | 3 | 4 | 50% | -0.032 % |
| macd | 11 | 1 | 8 | 2 | 11% | -0.094 % |
| orb | 2 | 2 | 0 | 0 | 100% | +0.112 % |
| pdhl | 7 | 2 | 3 | 2 | 40% | +0.003 % |
| rsi | 35 | 13 | 19 | 3 | 41% | +0.000 % |
| trend_15m | 68 | 22 | 32 | 14 | 41% | -0.036 % |
| trend_1h | 66 | 20 | 32 | 14 | 38% | -0.041 % |
| trend_5m | 44 | 18 | 23 | 3 | 44% | -0.009 % |
| vwap | 67 | 22 | 31 | 14 | 42% | -0.030 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 10 | 1 | 6 | 3 | 14% | -0.225 % |
| gold | 8 | 3 | 5 | 0 | 38% | -0.022 % |
| nasdaq | 21 | 11 | 9 | 1 | 55% | +0.023 % |
| oil | 7 | 2 | 4 | 1 | 33% | -0.060 % |
| sp500 | 10 | 3 | 6 | 1 | 33% | -0.024 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 17 | -0.48 R | en test |
| horizon ~3 h | 6 | +0.06 R | en test |
| confiance moyenne | 5 | -0.14 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 0 | n/a | en test |
| reprise juste après un stop | 6 | +0.45 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 4 | -0.38 R | en test |
| nouvel actif : Pétrole WTI (CL) | 7 | -0.09 R | en test |
| nouvel actif : Euro / dollar (6E) | 0 | n/a | en test |

Notes :

- trades réels : +0,12 R ± 0,28 R par trade avant frais sur 65 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- variante « indices le matin européen » en test : 17 trades, -0,48 R net, encore 83 trades avant décision
- variante « horizon ~3 h » en test : 6 trades, +0,06 R net, encore 94 trades avant décision
- variante « confiance moyenne » en test : 5 trades, -0,14 R net, encore 95 trades avant décision
- variante « reprise juste après un stop » en test : 6 trades, +0,45 R net, encore 94 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 4 trades, -0,38 R net, encore 96 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 7 trades, -0,09 R net, encore 93 trades avant décision

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
