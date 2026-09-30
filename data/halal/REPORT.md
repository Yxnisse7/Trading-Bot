# Trading-Bot — rapport

_Mis à jour le 30/09/2026 à 03:20 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **3**
- Taux de réussite cumulé (TP / (TP+SL)) : **0%** — hasard attendu 40%, avantage **-40%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-3.50 %** (brut -2.75 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **0** clôturés, 0 ouverts, taux de réussite n/a (hasard attendu n/a)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 2 | 0 | 2 | 0 | 0% | -1.071 % |
| ethereum | 1 | 0 | 1 | 0 | 0% | -1.361 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 3 | 0 | 3 | 0 | 0% | -1.167 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 2 | 0 | 2 | 0 | 0% | -1.243 % |
| moyen | 1 | 0 | 1 | 0 | 0% | -1.017 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 3 | 0 | 3 | 0 | 0% | -1.167 % |
| level | 2 | 0 | 2 | 0 | 0% | -1.189 % |
| macd | 2 | 0 | 2 | 0 | 0% | -1.243 % |
| pdhl | 2 | 0 | 2 | 0 | 0% | -1.243 % |
| rsi | 2 | 0 | 2 | 0 | 0% | -1.243 % |
| trend_15m | 3 | 0 | 3 | 0 | 0% | -1.167 % |
| trend_1h | 3 | 0 | 3 | 0 | 0% | -1.167 % |
| volume | 1 | 0 | 1 | 0 | 0% | -1.017 % |
| vwap | 2 | 0 | 2 | 0 | 0% | -1.243 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 1 | 0 | 1 | 0 | 0% | -1.125 % |
| actualité chargée | 2 | 0 | 2 | 0 | 0% | -1.189 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 10h | 1 | 0 | 1 | 0 | 0% | -1.361 % |
| 11h | 1 | 0 | 1 | 0 | 0% | -1.125 % |
| 13h | 1 | 0 | 1 | 0 | 0% | -1.017 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| signaux du bot | 3 | 0 | 3 | 0 | 0% | -1.167 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 12h | 3 | 0 | 3 | 0 | 0% | -1.167 % |

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

- trades réels : -1,00 R ± 0,00 R par trade avant frais sur 3 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bitcoin (BTC) | 30/07/2026 → 27/09/2026 | 17 | 6 | 7 | 4 | 46% | 42% | +5% | -1.53 % | -0.090 % |
| Ethereum (ETH) | 30/07/2026 → 27/09/2026 | 27 | 11 | 11 | 5 | 50% | 42% | +8% | -0.76 % | -0.028 % |
| ETF USA islamique (ISDU) | 06/07/2026 → 25/09/2026 | 12 | 1 | 7 | 4 | 12% | 40% | -28% | +0.36 % | +0.030 % |
| ETF Monde islamique (ISDW) | 06/07/2026 → 25/09/2026 | 11 | 4 | 3 | 4 | 57% | 40% | +17% | +2.50 % | +0.227 % |
| Or physique Royal Mint (RMAU) | 03/07/2026 → 25/09/2026 | 4 | 2 | 1 | 1 | 67% | 40% | +27% | +1.46 % | +0.364 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
