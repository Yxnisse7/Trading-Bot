# Trading-Bot — rapport

_Mis à jour le 18/09/2026 à 10:35 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **7**
- Taux de réussite cumulé (TP / (TP+SL)) : **25%** — hasard attendu 40%, avantage **-15%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-0.60 %** (brut -0.45 %)
- Signaux ouverts : **1**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **0** clôturés, 0 ouverts, taux de réussite n/a (hasard attendu n/a)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 18/09 10:10 | Or (XAU/USD) | long | 4434.4 | 4445.3 | 4427.2 | fort | signaux du bot | 11:10 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| ethereum | 1 | 0 | 1 | 0 | 0% | -0.417 % |
| gold | 1 | 0 | 0 | 1 | n/a | +0.000 % |
| nasdaq | 4 | 1 | 2 | 1 | 33% | -0.048 % |
| sp500 | 1 | 0 | 0 | 1 | n/a | +0.013 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 7 | 1 | 3 | 3 | 25% | -0.085 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 5 | 0 | 2 | 3 | 0% | -0.128 % |
| moyen | 2 | 1 | 1 | 0 | 50% | +0.022 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 7 | 1 | 3 | 3 | 25% | -0.085 % |
| level | 1 | 0 | 1 | 0 | 0% | -0.417 % |
| rsi | 5 | 0 | 2 | 3 | 0% | -0.128 % |
| trend_15m | 7 | 1 | 3 | 3 | 25% | -0.085 % |
| trend_1h | 7 | 1 | 3 | 3 | 25% | -0.085 % |
| trend_5m | 5 | 0 | 2 | 3 | 0% | -0.128 % |
| vwap | 6 | 1 | 2 | 3 | 33% | -0.030 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 2 | 0 | 2 | 0 | 0% | -0.278 % |
| actualité chargée | 5 | 1 | 1 | 3 | 50% | -0.008 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 07h | 1 | 0 | 0 | 1 | n/a | +0.000 % |
| 14h | 2 | 1 | 1 | 0 | 50% | -0.117 % |
| 15h | 1 | 0 | 1 | 0 | 0% | -0.139 % |
| 16h | 1 | 0 | 0 | 1 | n/a | +0.013 % |
| 17h | 1 | 0 | 0 | 1 | n/a | -0.097 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| signaux du bot | 7 | 1 | 3 | 3 | 25% | -0.085 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 7 | 1 | 3 | 3 | 25% | -0.085 % |

Trades expirés : 3, 67% terminés dans le bon sens, P&L moyen -0.028 %.

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

Dernières notes :

- level: win rate 38% sur 68 trades → poids 0.25 → 0.25
- volume: win rate 35% sur 26 trades → poids 0.25 → 0.25

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
