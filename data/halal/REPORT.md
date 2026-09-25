# Trading-Bot — rapport

_Mis à jour le 25/09/2026 à 14:15 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **2**
- Taux de réussite cumulé (TP / (TP+SL)) : **0%** — hasard attendu 40%, avantage **-40%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-2.14 %** (brut -1.64 %)
- Signaux ouverts : **1**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **0** clôturés, 0 ouverts, taux de réussite n/a (hasard attendu n/a)

## Signaux ouverts

| Heure | Actif | Sens | Entrée | TP | SL | Confiance | Source | Expire |
|---|---|---|---:|---:|---:|---|---|---|
| 25/09 12:55 | Ethereum (ETH) | long | 2718.0 | 2763.2 | 2687.8 | fort | signaux du bot | 00:55 |

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 2 | 0 | 2 | 0 | 0% | -1.071 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 2 | 0 | 2 | 0 | 0% | -1.071 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 1 | 0 | 1 | 0 | 0% | -1.125 % |
| moyen | 1 | 0 | 1 | 0 | 0% | -1.017 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 2 | 0 | 2 | 0 | 0% | -1.071 % |
| level | 1 | 0 | 1 | 0 | 0% | -1.017 % |
| macd | 1 | 0 | 1 | 0 | 0% | -1.125 % |
| pdhl | 1 | 0 | 1 | 0 | 0% | -1.125 % |
| rsi | 1 | 0 | 1 | 0 | 0% | -1.125 % |
| trend_15m | 2 | 0 | 2 | 0 | 0% | -1.071 % |
| trend_1h | 2 | 0 | 2 | 0 | 0% | -1.071 % |
| volume | 1 | 0 | 1 | 0 | 0% | -1.017 % |
| vwap | 1 | 0 | 1 | 0 | 0% | -1.125 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 1 | 0 | 1 | 0 | 0% | -1.125 % |
| actualité chargée | 1 | 0 | 1 | 0 | 0% | -1.017 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 11h | 1 | 0 | 1 | 0 | 0% | -1.125 % |
| 13h | 1 | 0 | 1 | 0 | 0% | -1.017 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| signaux du bot | 2 | 0 | 2 | 0 | 0% | -1.071 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 12h | 2 | 0 | 2 | 0 | 0% | -1.071 % |

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

Notes :

- trades réels : -1,00 R ± 0,00 R par trade avant frais sur 2 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bitcoin (BTC) | 26/07/2026 → 23/09/2026 | 16 | 5 | 7 | 4 | 42% | 42% | +0% | -2.18 % | -0.136 % |
| Ethereum (ETH) | 26/07/2026 → 23/09/2026 | 22 | 10 | 8 | 4 | 56% | 42% | +13% | -0.82 % | -0.037 % |
| ETF USA islamique (ISDU) | 01/07/2026 → 23/09/2026 | 14 | 1 | 6 | 7 | 14% | 40% | -26% | +1.14 % | +0.081 % |
| ETF Monde islamique (ISDW) | 01/07/2026 → 23/09/2026 | 10 | 3 | 3 | 4 | 50% | 40% | +10% | +1.89 % | +0.189 % |
| Or physique Royal Mint (RMAU) | 01/07/2026 → 23/09/2026 | 1 | 0 | 0 | 1 | n/a | 40% | n/a | +0.71 % | +0.709 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
