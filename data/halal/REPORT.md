# Trading-Bot — rapport

_Mis à jour le 23/09/2026 à 13:55 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **0**
- Taux de réussite cumulé (TP / (TP+SL)) : **n/a** — hasard attendu n/a, avantage **n/a**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **+0.00 %** (brut +0.00 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **0** clôturés, 0 ouverts, taux de réussite n/a (hasard attendu n/a)

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
