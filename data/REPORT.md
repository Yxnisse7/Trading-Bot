# Trading-Bot — rapport

_Mis à jour le 22/09/2026 à 21:01 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **47**
- Taux de réussite cumulé (TP / (TP+SL)) : **43%** — hasard attendu 41%, avantage **+2%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-3.15 %** (brut -1.32 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **23** clôturés, 0 ouverts, taux de réussite 53% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 10 | 3 | 3 | 4 | 50% | -0.046 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 9 | 2 | 6 | 1 | 25% | -0.112 % |
| nasdaq | 12 | 7 | 4 | 1 | 64% | +0.008 % |
| sp500 | 5 | 2 | 2 | 1 | 50% | +0.002 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 37 | 11 | 17 | 9 | 39% | -0.080 % |
| short | 10 | 5 | 4 | 1 | 56% | -0.018 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 43 | 15 | 19 | 9 | 44% | -0.066 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 46 | 16 | 21 | 9 | 43% | -0.065 % |
| corr | 10 | 2 | 5 | 3 | 29% | -0.113 % |
| level | 5 | 1 | 4 | 0 | 20% | -0.133 % |
| macd | 10 | 3 | 7 | 0 | 30% | -0.171 % |
| orb | 4 | 1 | 3 | 0 | 25% | -0.087 % |
| pdhl | 8 | 2 | 6 | 0 | 25% | -0.128 % |
| rsi | 37 | 13 | 15 | 9 | 46% | -0.058 % |
| trend_15m | 46 | 16 | 21 | 9 | 43% | -0.065 % |
| trend_1h | 46 | 16 | 21 | 9 | 43% | -0.065 % |
| trend_5m | 40 | 15 | 16 | 9 | 48% | -0.051 % |
| volume | 2 | 1 | 1 | 0 | 50% | -0.043 % |
| vwap | 44 | 16 | 19 | 9 | 46% | -0.054 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 18 | 6 | 9 | 3 | 40% | -0.107 % |
| actualité chargée | 29 | 10 | 12 | 7 | 45% | -0.042 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 3 | 2 | 0 | 1 | 100% | +0.118 % |
| 08h | 3 | 0 | 3 | 0 | 0% | -0.265 % |
| 09h | 3 | 0 | 2 | 1 | 0% | -0.237 % |
| 10h | 1 | 0 | 0 | 1 | n/a | -0.098 % |
| 11h | 3 | 1 | 1 | 1 | 50% | +0.094 % |
| 12h | 4 | 2 | 2 | 0 | 50% | +0.009 % |
| 14h | 6 | 2 | 4 | 0 | 33% | -0.081 % |
| 15h | 5 | 1 | 4 | 0 | 20% | -0.224 % |
| 16h | 1 | 0 | 0 | 1 | n/a | +0.013 % |
| 17h | 2 | 1 | 0 | 1 | 100% | +0.014 % |
| 18h | 4 | 3 | 0 | 1 | 100% | +0.064 % |
| 19h | 3 | 2 | 1 | 0 | 67% | +0.071 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 46 | 16 | 21 | 9 | 43% | -0.065 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 45 | 16 | 19 | 10 | 46% | -0.058 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 10, 50% terminés dans le bon sens, P&L moyen -0.061 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 23 | 9 | 8 | 6 | 53% | -0.047 % |
| corr | 5 | 0 | 3 | 2 | 0% | -0.251 % |
| level | 3 | 2 | 0 | 1 | 100% | +0.112 % |
| orb | 1 | 1 | 0 | 0 | 100% | +0.113 % |
| rsi | 1 | 1 | 0 | 0 | 100% | +0.113 % |
| trend_15m | 23 | 9 | 8 | 6 | 53% | -0.047 % |
| trend_1h | 21 | 7 | 8 | 6 | 47% | -0.061 % |
| trend_5m | 8 | 6 | 2 | 0 | 75% | +0.069 % |
| vwap | 22 | 9 | 7 | 6 | 56% | -0.027 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 4 | 0 | 0 | 4 | n/a | +0.009 % |
| ethereum | 6 | 0 | 4 | 2 | 0% | -0.290 % |
| gold | 3 | 1 | 2 | 0 | 33% | -0.043 % |
| nasdaq | 9 | 7 | 2 | 0 | 78% | +0.074 % |
| sp500 | 1 | 1 | 0 | 0 | 100% | +0.084 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
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

- ethereum : {'trend_5m': 0.807, 'trend_15m': 0.807, 'trend_1h': 0.807, 'adx': 0.807}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 0 | n/a | en test |
| horizon ~3 h | 0 | n/a | en test |
| confiance moyenne | 0 | n/a | en test |

Notes :

- trades réels : +0,01 R ± 0,33 R par trade avant frais sur 47 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- ethereum, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,29 R contre +0,06 R en global sur 45 trades éq. → poids ×0,81 sur cet actif

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 24/07/2026 → 22/09/2026 | 65 | 19 | 38 | 8 | 33% | 41% | -8% | -1.34 % | -0.021 % |
| S&P 500 (ES) | 24/07/2026 → 22/09/2026 | 97 | 41 | 47 | 9 | 47% | 41% | +6% | +0.14 % | +0.001 % |
| Bitcoin (BTC/USD) | 24/07/2026 → 22/09/2026 | 46 | 20 | 15 | 11 | 57% | 41% | +16% | +1.61 % | +0.035 % |
| Ethereum (ETH/USD) | 24/07/2026 → 22/09/2026 | 50 | 10 | 27 | 13 | 27% | 40% | -13% | -8.77 % | -0.175 % |
| Or (XAU/USD) | 24/07/2026 → 22/09/2026 | 111 | 42 | 44 | 25 | 49% | 42% | +7% | +0.05 % | +0.001 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
