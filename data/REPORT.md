# Trading-Bot — rapport

_Mis à jour le 18/09/2026 à 15:04 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **11**
- Taux de réussite cumulé (TP / (TP+SL)) : **12%** — hasard attendu 40%, avantage **-28%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-1.52 %** (brut -1.30 %)
- Signaux ouverts : **1**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **0** clôturés, 0 ouverts, taux de réussite n/a (hasard attendu n/a)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 18/09 14:55 | S&P 500 (ES) | short | 7702.5 | 7697.5 | 7706.5 | fort | signaux du bot | 15:55 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| ethereum | 1 | 0 | 1 | 0 | 0% | -0.417 % |
| gold | 4 | 0 | 3 | 1 | 0% | -0.181 % |
| nasdaq | 5 | 1 | 3 | 1 | 25% | -0.078 % |
| sp500 | 1 | 0 | 0 | 1 | n/a | +0.013 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 11 | 1 | 7 | 3 | 12% | -0.138 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 8 | 0 | 5 | 3 | 0% | -0.170 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 11 | 1 | 7 | 3 | 12% | -0.138 % |
| level | 2 | 0 | 2 | 0 | 0% | -0.299 % |
| pdhl | 3 | 0 | 3 | 0 | 0% | -0.247 % |
| rsi | 7 | 0 | 4 | 3 | 0% | -0.169 % |
| trend_15m | 11 | 1 | 7 | 3 | 12% | -0.138 % |
| trend_1h | 11 | 1 | 7 | 3 | 12% | -0.138 % |
| trend_5m | 7 | 0 | 4 | 3 | 0% | -0.169 % |
| vwap | 9 | 1 | 5 | 3 | 17% | -0.100 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 3 | 0 | 3 | 0 | 0% | -0.252 % |
| actualité chargée | 8 | 1 | 4 | 3 | 20% | -0.096 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 07h | 1 | 0 | 0 | 1 | n/a | +0.000 % |
| 08h | 2 | 0 | 2 | 0 | 0% | -0.272 % |
| 09h | 1 | 0 | 1 | 0 | 0% | -0.180 % |
| 12h | 1 | 0 | 1 | 0 | 0% | -0.199 % |
| 14h | 2 | 1 | 1 | 0 | 50% | -0.117 % |
| 15h | 1 | 0 | 1 | 0 | 0% | -0.139 % |
| 16h | 1 | 0 | 0 | 1 | n/a | +0.013 % |
| 17h | 1 | 0 | 0 | 1 | n/a | -0.097 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| signaux du bot | 11 | 1 | 7 | 3 | 12% | -0.138 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 9 | 1 | 5 | 3 | 17% | -0.106 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

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
| orb | 0.522 |
| pdhl | 1.0 |
| corr | 0.5 |

Dernières notes :

- level: win rate 37% sur 86 trades → poids 0.25 → 0.25
- orb: win rate 33% sur 36 trades → poids 0.614 → 0.522
- volume: win rate 37% sur 52 trades → poids 0.25 → 0.25

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
