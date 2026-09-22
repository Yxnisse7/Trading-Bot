# Trading-Bot — rapport

_Mis à jour le 22/09/2026 à 05:40 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **37**
- Taux de réussite cumulé (TP / (TP+SL)) : **43%** — hasard attendu 41%, avantage **+2%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-2.51 %** (brut -0.99 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **20** clôturés, 0 ouverts, taux de réussite 50% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 8 | 3 | 3 | 2 | 50% | -0.032 % |
| ethereum | 10 | 2 | 6 | 2 | 25% | -0.176 % |
| gold | 5 | 1 | 3 | 1 | 25% | -0.116 % |
| nasdaq | 9 | 5 | 3 | 1 | 62% | +0.009 % |
| sp500 | 5 | 2 | 2 | 1 | 50% | +0.002 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 32 | 9 | 16 | 7 | 36% | -0.087 % |
| short | 5 | 4 | 1 | 0 | 80% | +0.056 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 33 | 12 | 15 | 6 | 44% | -0.066 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 36 | 13 | 17 | 6 | 43% | -0.065 % |
| corr | 8 | 2 | 4 | 2 | 33% | -0.105 % |
| level | 4 | 1 | 3 | 0 | 25% | -0.119 % |
| macd | 8 | 2 | 6 | 0 | 25% | -0.198 % |
| orb | 2 | 1 | 1 | 0 | 50% | +0.010 % |
| pdhl | 5 | 1 | 4 | 0 | 20% | -0.170 % |
| rsi | 28 | 10 | 12 | 6 | 45% | -0.063 % |
| trend_15m | 36 | 13 | 17 | 6 | 43% | -0.065 % |
| trend_1h | 36 | 13 | 17 | 6 | 43% | -0.065 % |
| trend_5m | 31 | 12 | 13 | 6 | 48% | -0.051 % |
| volume | 2 | 1 | 1 | 0 | 50% | -0.043 % |
| vwap | 34 | 13 | 15 | 6 | 46% | -0.051 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 12 | 4 | 6 | 2 | 40% | -0.133 % |
| actualité chargée | 25 | 9 | 11 | 5 | 45% | -0.036 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 2 | 1 | 0 | 1 | 100% | +0.071 % |
| 08h | 2 | 0 | 2 | 0 | 0% | -0.272 % |
| 09h | 2 | 0 | 2 | 0 | 0% | -0.306 % |
| 11h | 2 | 1 | 0 | 1 | 100% | +0.239 % |
| 12h | 4 | 2 | 2 | 0 | 50% | +0.009 % |
| 14h | 5 | 2 | 3 | 0 | 40% | -0.061 % |
| 15h | 4 | 1 | 3 | 0 | 25% | -0.232 % |
| 16h | 1 | 0 | 0 | 1 | n/a | +0.013 % |
| 17h | 1 | 0 | 0 | 1 | n/a | -0.097 % |
| 18h | 3 | 2 | 0 | 1 | 100% | +0.062 % |
| 19h | 3 | 2 | 1 | 0 | 67% | +0.071 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 36 | 13 | 17 | 6 | 43% | -0.065 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 35 | 13 | 15 | 7 | 46% | -0.056 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 7, 57% terminés dans le bon sens, P&L moyen -0.053 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 20 | 8 | 8 | 4 | 50% | -0.071 % |
| corr | 5 | 0 | 3 | 2 | 0% | -0.251 % |
| level | 2 | 2 | 0 | 0 | 100% | +0.145 % |
| orb | 1 | 1 | 0 | 0 | 100% | +0.113 % |
| rsi | 1 | 1 | 0 | 0 | 100% | +0.113 % |
| trend_15m | 20 | 8 | 8 | 4 | 50% | -0.071 % |
| trend_1h | 18 | 6 | 8 | 4 | 43% | -0.089 % |
| trend_5m | 7 | 5 | 2 | 0 | 71% | +0.060 % |
| vwap | 19 | 8 | 7 | 4 | 53% | -0.049 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 2 | 0 | 0 | 2 | n/a | -0.078 % |
| ethereum | 6 | 0 | 4 | 2 | 0% | -0.290 % |
| gold | 3 | 1 | 2 | 0 | 33% | -0.043 % |
| nasdaq | 8 | 6 | 2 | 0 | 75% | +0.066 % |
| sp500 | 1 | 1 | 0 | 0 | 100% | +0.084 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 22/09 01:55 | Bitcoin (BTC/USD) | long | 86554.0 | 86208.0 | ❌ SL | -0.46 % | 44 min |
| 22/09 00:34 | Bitcoin (BTC/USD) | long | 86455.0 | 86369.87 | ⏱️ expiré | -0.16 % | 61 min |
| 22/09 00:26 | Ethereum (ETH/USD) | long | 2776.6 | 2772.37 | ⏱️ expiré | -0.23 % | 65 min |
| 21/09 21:40 | Bitcoin (BTC/USD) | long | 86600.0 | 87020.0 | ✅ TP | +0.42 % | 45 min |
| 21/09 20:10 | S&P 500 (ES) | long | 7828.25 | 7835.0 | ✅ TP | +0.08 % | 11 min |
| 21/09 20:10 | Nasdaq 100 (NQ) | long | 30715.0 | 30758.75 | ✅ TP | +0.13 % | 17 min |
| 21/09 20:10 | Bitcoin (BTC/USD) | long | 85955.0 | 85986.64 | ⏱️ expiré | -0.02 % | 60 min |
| 21/09 17:55 | Ethereum (ETH/USD) | long | 2761.3 | 2749.6 | ❌ SL | -0.50 % | 7 min |
| 21/09 17:40 | Bitcoin (BTC/USD) | long | 85983.0 | 85712.0 | ❌ SL | -0.38 % | 26 min |
| 21/09 16:10 | S&P 500 (ES) | long | 7773.25 | 7769.0 | ❌ SL | -0.06 % | 5 min |
| 21/09 14:40 | Bitcoin (BTC/USD) | long | 85263.0 | 85024.0 | ❌ SL | -0.34 % | 44 min |
| 21/09 14:25 | Ethereum (ETH/USD) | long | 2724.8 | 2741.2 | ✅ TP | +0.52 % | 36 min |
| 21/09 13:25 | Bitcoin (BTC/USD) | long | 84597.0 | 84946.0 | ✅ TP | +0.35 % | 35 min |
| 21/09 13:25 | Ethereum (ETH/USD) | long | 2718.7 | 2724.27 | ⏱️ expiré | +0.12 % | 60 min |
| 21/09 09:25 | Or (XAU/USD) | short | 4388.9 | 4381.8 | ✅ TP | +0.14 % | 17 min |
| 21/09 08:25 | Ethereum (ETH/USD) | long | 2676.0 | 2667.2 | ❌ SL | -0.41 % | 10 min |
| 21/09 03:10 | Ethereum (ETH/USD) | long | 2687.2 | 2700.3 | ✅ TP | +0.41 % | 12 min |
| 19/09 11:10 | Ethereum (ETH/USD) | long | 2651.2 | 2641.9 | ❌ SL | -0.43 % | 21 min |
| 19/09 02:55 | Bitcoin (BTC/USD) | long | 81402.0 | 81713.0 | ✅ TP | +0.32 % | 4 min |
| 19/09 02:40 | Ethereum (ETH/USD) | long | 2619.5 | 2610.6 | ❌ SL | -0.42 % | 37 min |
| 18/09 21:55 | Nasdaq 100 (NQ) | long | 29854.75 | 29914.75 | ✅ TP | +0.19 % | 10 min |
| 18/09 21:55 | Ethereum (ETH/USD) | long | 2635.9 | 2627.4 | ❌ SL | -0.40 % | 31 min |
| 18/09 17:40 | Nasdaq 100 (NQ) | short | 29737.75 | 29708.25 | ✅ TP | +0.09 % | 13 min |
| 18/09 16:40 | Nasdaq 100 (NQ) | short | 29728.25 | 29707.25 | ✅ TP | +0.06 % | 1 min |
| 18/09 16:40 | S&P 500 (ES) | short | 7689.0 | 7693.5 | ❌ SL | -0.07 % | 11 min |
| 18/09 14:55 | S&P 500 (ES) | short | 7702.5 | 7697.5 | ✅ TP | +0.05 % | 29 min |
| 18/09 14:10 | Nasdaq 100 (NQ) | long | 29825.75 | 29769.25 | ❌ SL | -0.20 % | 9 min |
| 18/09 11:40 | Or (XAU/USD) | long | 4427.4 | 4420.3 | ❌ SL | -0.18 % | 0 min |
| 18/09 10:36 | Or (XAU/USD) | long | 4429.4 | 4414.3 | ❌ SL | -0.36 % | 68 min |
| 18/09 10:10 | Or (XAU/USD) | long | 4434.4 | 4427.2 | ❌ SL | -0.18 % | 20 min |

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
| level | 0.25 |
| volume | 0.25 |
| orb | 0.25 |
| pdhl | 1.0 |
| corr | 0.5 |

Dernières notes :

- level: win rate 39% sur 90 trades → poids 0.25 → 0.25
- orb: win rate 36% sur 39 trades → poids 0.25 → 0.25
- volume: win rate 37% sur 54 trades → poids 0.25 → 0.25

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 19/07/2026 → 17/09/2026 | 112 | 34 | 55 | 23 | 38% | 41% | -3% | -1.90 % | -0.017 % |
| Nasdaq 100 (NQ) | 19/07/2026 → 17/09/2026 | 64 | 28 | 33 | 3 | 46% | 41% | +5% | +2.48 % | +0.039 % |
| S&P 500 (ES) | 19/07/2026 → 17/09/2026 | 129 | 58 | 61 | 10 | 49% | 41% | +7% | +0.60 % | +0.005 % |
| S&P 500 (ES) | 19/07/2026 → 17/09/2026 | 56 | 18 | 32 | 6 | 36% | 42% | -6% | -1.74 % | -0.031 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 17/09/2026 | 46 | 18 | 20 | 8 | 47% | 41% | +7% | -0.88 % | -0.019 % |
| Ethereum (ETH/USD) | 20/07/2026 → 17/09/2026 | 50 | 12 | 25 | 13 | 32% | 40% | -8% | -3.93 % | -0.079 % |
| Or (XAU/USD) | 19/07/2026 → 17/09/2026 | 133 | 33 | 57 | 43 | 37% | 42% | -5% | -3.55 % | -0.027 % |
| Or (XAU/USD) | 19/07/2026 → 17/09/2026 | 76 | 31 | 35 | 10 | 47% | 43% | +4% | +0.37 % | +0.005 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
