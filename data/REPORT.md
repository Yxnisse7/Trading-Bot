# Trading-Bot — rapport

_Mis à jour le 17/09/2026 à 17:05 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **2**
- Taux de réussite cumulé (TP / (TP+SL)) : **50%** — hasard attendu 40%, avantage **+10%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-0.23 %** (brut -0.14 %)
- Signaux ouverts : **1**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **0** clôturés, 0 ouverts, taux de réussite n/a (hasard attendu n/a)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 17/09 17:01 | Nasdaq 100 (NQ) | long | 29695.5 | 29747.5 | 29657.25 | moyen | signaux du bot | 18:01 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| ethereum | 1 | 0 | 1 | 0 | 0% | -0.417 % |
| nasdaq | 1 | 1 | 0 | 0 | 100% | +0.182 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 2 | 1 | 1 | 0 | 50% | -0.117 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 1 | 0 | 1 | 0 | 0% | -0.417 % |
| moyen | 1 | 1 | 0 | 0 | 100% | +0.182 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 2 | 1 | 1 | 0 | 50% | -0.117 % |
| level | 1 | 0 | 1 | 0 | 0% | -0.417 % |
| rsi | 1 | 0 | 1 | 0 | 0% | -0.417 % |
| trend_15m | 2 | 1 | 1 | 0 | 50% | -0.117 % |
| trend_1h | 2 | 1 | 1 | 0 | 50% | -0.117 % |
| trend_5m | 1 | 0 | 1 | 0 | 0% | -0.417 % |
| vwap | 1 | 1 | 0 | 0 | 100% | +0.182 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 1 | 0 | 1 | 0 | 0% | -0.417 % |
| actualité chargée | 1 | 1 | 0 | 0 | 100% | +0.182 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 14h | 2 | 1 | 1 | 0 | 50% | -0.117 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| signaux du bot | 2 | 1 | 1 | 0 | 50% | -0.117 % |

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
| level | 0.614 |
| volume | 0.46 |

Dernières notes :

- level: win rate 38% sur 68 trades → poids 0.722 → 0.614
- volume: win rate 35% sur 26 trades → poids 0.541 → 0.46

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 19/07/2026 → 17/09/2026 | 115 | 34 | 56 | 25 | 38% | 41% | -4% | -2.02 % | -0.018 % |
| S&P 500 (ES) | 19/07/2026 → 17/09/2026 | 130 | 57 | 62 | 11 | 48% | 41% | +7% | +0.26 % | +0.002 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 17/09/2026 | 46 | 18 | 20 | 8 | 47% | 41% | +7% | -0.88 % | -0.019 % |
| Ethereum (ETH/USD) | 20/07/2026 → 17/09/2026 | 49 | 12 | 24 | 13 | 33% | 40% | -7% | -3.43 % | -0.070 % |
| Or (XAU/USD) | 19/07/2026 → 17/09/2026 | 133 | 33 | 57 | 43 | 37% | 42% | -5% | -3.55 % | -0.027 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
