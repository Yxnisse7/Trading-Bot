# Trading-Bot — rapport

_Mis à jour le 19/09/2026 à 08:55 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **19**
- Taux de réussite cumulé (TP / (TP+SL)) : **38%** — hasard attendu 41%, avantage **-4%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-1.69 %** (brut -1.20 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **5** clôturés, 0 ouverts, taux de réussite 50% (hasard attendu 40%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 1 | 1 | 0 | 0 | 100% | +0.322 % |
| ethereum | 3 | 0 | 3 | 0 | 0% | -0.413 % |
| gold | 4 | 0 | 3 | 1 | 0% | -0.181 % |
| nasdaq | 8 | 4 | 3 | 1 | 57% | -0.006 % |
| sp500 | 3 | 1 | 1 | 1 | 50% | -0.000 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 15 | 3 | 9 | 3 | 25% | -0.122 % |
| short | 4 | 3 | 1 | 0 | 75% | +0.034 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 16 | 5 | 8 | 3 | 38% | -0.096 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 19 | 6 | 10 | 3 | 38% | -0.089 % |
| corr | 2 | 0 | 2 | 0 | 0% | -0.411 % |
| level | 4 | 1 | 3 | 0 | 25% | -0.119 % |
| macd | 2 | 1 | 1 | 0 | 50% | -0.114 % |
| orb | 2 | 1 | 1 | 0 | 50% | +0.010 % |
| pdhl | 4 | 1 | 3 | 0 | 25% | -0.105 % |
| rsi | 13 | 3 | 7 | 3 | 30% | -0.144 % |
| trend_15m | 19 | 6 | 10 | 3 | 38% | -0.089 % |
| trend_1h | 19 | 6 | 10 | 3 | 38% | -0.089 % |
| trend_5m | 14 | 5 | 6 | 3 | 45% | -0.067 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.322 % |
| vwap | 17 | 6 | 8 | 3 | 43% | -0.063 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 5 | 2 | 3 | 0 | 40% | -0.122 % |
| actualité chargée | 14 | 4 | 7 | 3 | 36% | -0.077 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 07h | 1 | 0 | 0 | 1 | n/a | +0.000 % |
| 08h | 2 | 0 | 2 | 0 | 0% | -0.272 % |
| 09h | 1 | 0 | 1 | 0 | 0% | -0.180 % |
| 12h | 2 | 1 | 1 | 0 | 50% | -0.072 % |
| 14h | 4 | 2 | 2 | 0 | 50% | -0.061 % |
| 15h | 2 | 1 | 1 | 0 | 50% | -0.025 % |
| 16h | 1 | 0 | 0 | 1 | n/a | +0.013 % |
| 17h | 1 | 0 | 0 | 1 | n/a | -0.097 % |
| 19h | 2 | 1 | 1 | 0 | 50% | -0.106 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| signaux du bot | 19 | 6 | 10 | 3 | 38% | -0.089 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 17 | 6 | 8 | 3 | 43% | -0.067 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 3, 67% terminés dans le bon sens, P&L moyen -0.028 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 5 | 2 | 2 | 1 | 50% | -0.154 % |
| corr | 3 | 0 | 2 | 1 | 0% | -0.323 % |
| level | 1 | 1 | 0 | 0 | 100% | +0.113 % |
| orb | 1 | 1 | 0 | 0 | 100% | +0.113 % |
| rsi | 1 | 1 | 0 | 0 | 100% | +0.113 % |
| trend_15m | 5 | 2 | 2 | 1 | 50% | -0.154 % |
| trend_1h | 3 | 0 | 2 | 1 | 0% | -0.323 % |
| vwap | 5 | 2 | 2 | 1 | 50% | -0.154 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| ethereum | 3 | 0 | 2 | 1 | 0% | -0.323 % |
| nasdaq | 1 | 1 | 0 | 0 | 100% | +0.113 % |
| sp500 | 1 | 1 | 0 | 0 | 100% | +0.084 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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
| 18/09 09:10 | Or (XAU/USD) | long | 4432.4 | 4433.3 | ⏱️ expiré | +0.00 % | 60 min |
| 17/09 22:01 | Nasdaq 100 (NQ) | long | 29781.0 | 29742.75 | ❌ SL | -0.14 % | 9 min |
| 17/09 19:15 | Nasdaq 100 (NQ) | long | 29753.25 | 29727.5 | ⏱️ expiré | -0.10 % | 64 min |
| 17/09 18:01 | S&P 500 (ES) | long | 7703.5 | 7705.25 | ⏱️ expiré | +0.01 % | 64 min |
| 17/09 17:01 | Nasdaq 100 (NQ) | long | 29695.5 | 29657.25 | ❌ SL | -0.14 % | 4 min |
| 17/09 16:45 | Ethereum (ETH/USD) | long | 2462.6 | 2454.3 | ❌ SL | -0.42 % | 15 min |
| 17/09 16:15 | Nasdaq 100 (NQ) | long | 29674.5 | 29731.5 | ✅ TP | +0.18 % | 11 min |

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

- level: win rate 38% sur 89 trades → poids 0.25 → 0.25
- orb: win rate 36% sur 39 trades → poids 0.25 → 0.25
- volume: win rate 38% sur 53 trades → poids 0.25 → 0.25

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
