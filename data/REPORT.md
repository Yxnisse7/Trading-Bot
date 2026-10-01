# Trading-Bot — rapport

_Mis à jour le 01/10/2026 à 17:50 (Europe/Paris)._

## Vue d'ensemble

- Trades clôturés : **98**
- Taux de réussite cumulé (TP / (TP+SL)) : **46%** — hasard attendu 42%, avantage **+4%**
- P&L théorique cumulé, net des coûts estimés (somme des % par trade, sans levier) : **-3.33 %** (brut -0.56 %)
- Signaux ouverts : **0**
- Signaux fantômes (suivis en silence pour l'apprentissage) : **174** clôturés, 1 ouverts, taux de réussite 37% (hasard attendu 41%)

## Statistiques

### Par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 15 | 3 | 7 | 5 | 30% | -0.113 % |
| ethereum | 11 | 2 | 6 | 3 | 25% | -0.163 % |
| gold | 27 | 12 | 12 | 3 | 50% | -0.010 % |
| nasdaq | 27 | 14 | 11 | 2 | 56% | +0.029 % |
| sp500 | 18 | 6 | 8 | 4 | 43% | -0.021 % |

### Par sens

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| long | 52 | 18 | 24 | 10 | 43% | -0.049 % |
| short | 46 | 19 | 20 | 7 | 49% | -0.017 % |

### Par confiance

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| fort | 94 | 36 | 42 | 16 | 46% | -0.032 % |
| manuel | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| moyen | 3 | 1 | 2 | 0 | 33% | -0.052 % |

### Par critère technique

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 97 | 37 | 44 | 16 | 46% | -0.033 % |
| corr | 11 | 2 | 5 | 4 | 29% | -0.094 % |
| level | 11 | 2 | 7 | 2 | 22% | -0.086 % |
| macd | 25 | 8 | 15 | 2 | 35% | -0.091 % |
| orb | 9 | 2 | 6 | 1 | 25% | -0.085 % |
| pdhl | 15 | 5 | 8 | 2 | 38% | -0.054 % |
| rsi | 84 | 34 | 36 | 14 | 49% | -0.022 % |
| trend_15m | 97 | 37 | 44 | 16 | 46% | -0.033 % |
| trend_1h | 97 | 37 | 44 | 16 | 46% | -0.033 % |
| trend_5m | 87 | 34 | 37 | 16 | 48% | -0.028 % |
| volume | 4 | 1 | 3 | 0 | 25% | -0.182 % |
| vwap | 95 | 37 | 42 | 16 | 47% | -0.027 % |

### Par contexte d'actualité

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| actualité calme | 42 | 15 | 21 | 6 | 42% | -0.050 % |
| actualité chargée | 56 | 22 | 23 | 11 | 49% | -0.022 % |

### Par heure d'émission (UTC)

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 00h | 2 | 1 | 1 | 0 | 50% | -0.049 % |
| 01h | 1 | 1 | 0 | 0 | 100% | +0.407 % |
| 03h | 1 | 0 | 0 | 1 | n/a | -0.034 % |
| 06h | 1 | 0 | 1 | 0 | 0% | -0.409 % |
| 07h | 7 | 5 | 0 | 2 | 100% | +0.142 % |
| 08h | 5 | 1 | 4 | 0 | 20% | -0.177 % |
| 09h | 4 | 1 | 2 | 1 | 33% | -0.144 % |
| 10h | 2 | 1 | 0 | 1 | 100% | +0.065 % |
| 11h | 6 | 2 | 2 | 2 | 50% | +0.045 % |
| 12h | 6 | 3 | 3 | 0 | 50% | -0.021 % |
| 13h | 4 | 0 | 4 | 0 | 0% | -0.141 % |
| 14h | 14 | 5 | 7 | 2 | 42% | -0.022 % |
| 15h | 16 | 5 | 10 | 1 | 33% | -0.098 % |
| 16h | 6 | 1 | 3 | 2 | 25% | -0.044 % |
| 17h | 3 | 1 | 1 | 1 | 50% | -0.025 % |
| 18h | 6 | 5 | 0 | 1 | 100% | +0.078 % |
| 19h | 10 | 5 | 4 | 1 | 56% | +0.029 % |
| 20h | 1 | 0 | 1 | 0 | 0% | -0.138 % |
| 22h | 2 | 0 | 0 | 2 | n/a | -0.195 % |
| 23h | 1 | 0 | 1 | 0 | 0% | -0.460 % |

### Par source

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| demandes manuelles | 1 | 0 | 0 | 1 | n/a | -0.159 % |
| signaux du bot | 97 | 37 | 44 | 16 | 46% | -0.033 % |

### Par horizon

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 96 | 37 | 42 | 17 | 47% | -0.029 % |
| 3h | 2 | 0 | 2 | 0 | 0% | -0.280 % |

Trades expirés : 17, 59% terminés dans le bon sens, P&L moyen -0.015 %.

## Signaux fantômes (apprentissage)

Setups rejetés pour confiance insuffisante, suivis sans notification. Ils servent uniquement aux statistiques par critère et à l'apprentissage.

### Fantômes par critère

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| adx | 174 | 53 | 90 | 31 | 37% | -0.035 % |
| corr | 11 | 0 | 8 | 3 | 0% | -0.260 % |
| level | 19 | 6 | 6 | 7 | 50% | -0.054 % |
| macd | 45 | 11 | 27 | 7 | 29% | -0.052 % |
| orb | 7 | 3 | 3 | 1 | 50% | -0.087 % |
| pdhl | 21 | 6 | 9 | 6 | 40% | +0.001 % |
| rsi | 113 | 34 | 65 | 14 | 34% | -0.043 % |
| trend_15m | 174 | 53 | 90 | 31 | 37% | -0.035 % |
| trend_1h | 169 | 50 | 89 | 30 | 36% | -0.036 % |
| trend_5m | 136 | 48 | 74 | 14 | 39% | -0.025 % |
| volume | 1 | 1 | 0 | 0 | 100% | +0.260 % |
| vwap | 171 | 53 | 87 | 31 | 38% | -0.031 % |

### Fantômes par actif

| Segment | Trades | TP | SL | Expirés | Taux de réussite | P&L moyen |
|---|---:|---:|---:|---:|---:|---:|
| bitcoin | 12 | 2 | 2 | 8 | 50% | +0.010 % |
| ethereum | 11 | 1 | 7 | 3 | 12% | -0.242 % |
| euro | 13 | 7 | 6 | 0 | 54% | +0.004 % |
| gold | 34 | 12 | 16 | 6 | 43% | -0.001 % |
| nasdaq | 41 | 16 | 20 | 5 | 44% | -0.013 % |
| oil | 26 | 9 | 13 | 4 | 41% | -0.028 % |
| sp500 | 37 | 6 | 26 | 5 | 19% | -0.061 % |

## Derniers trades

| Émis | Actif | Sens | Entrée | Clôture | Résultat | P&L | Durée |
|---|---|---|---:|---:|---|---:|---:|
| 01/10 17:15 | S&P 500 (ES) | short | 7680.0 | 7687.75 | ❌ SL | -0.11 % | 0 min |
| 01/10 16:55 | Nasdaq 100 (NQ) | short | 30706.75 | 30645.25 | ✅ TP | +0.19 % | 0 min |
| 01/10 16:10 | S&P 500 (ES) | short | 7698.0 | 7689.5 | ⏱️ expiré | +0.10 % | 60 min |
| 01/10 11:35 | Or (XAU/USD) | short | 4189.3 | 4182.8 | ✅ TP | +0.14 % | 24 min |
| 30/09 21:15 | Nasdaq 100 (NQ) | long | 30841.75 | 30807.0 | ❌ SL | -0.12 % | 34 min |
| 30/09 18:35 | Nasdaq 100 (NQ) | long | 30862.25 | 30835.25 | ❌ SL | -0.10 % | 10 min |
| 30/09 18:15 | Or (XAU/USD) | short | 4192.0 | 4187.3 | ⏱️ expiré | +0.09 % | 60 min |
| 30/09 17:30 | Nasdaq 100 (NQ) | long | 30822.0 | 30887.5 | ✅ TP | +0.20 % | 18 min |
| 30/09 16:40 | Nasdaq 100 (NQ) | long | 30827.25 | 30861.25 | ⏱️ expiré | +0.10 % | 65 min |
| 30/09 16:01 | Nasdaq 100 (NQ) | long | 30771.0 | 30885.5 | ✅ TP | +0.36 % | 4 min |
| 30/09 09:55 | Or (XAU/USD) | long | 4225.6 | 4232.4 | ✅ TP | +0.14 % | 26 min |
| 29/09 21:15 | Nasdaq 100 (NQ) | long | 30651.5 | 30614.25 | ❌ SL | -0.13 % | 25 min |
| 29/09 20:15 | Or (XAU/USD) | long | 4195.6 | 4203.0 | ✅ TP | +0.16 % | 0 min |
| 29/09 16:30 | Or (XAU/USD) | long | 4206.8 | 4196.3 | ❌ SL | -0.27 % | 6 min |
| 28/09 21:50 | S&P 500 (ES) | short | 7742.5 | 7744.5 | ⏱️ expiré | -0.04 % | 60 min |
| 28/09 21:20 | Or (XAU/USD) | short | 4165.1 | 4153.8 | ✅ TP | +0.25 % | 40 min |
| 28/09 18:25 | S&P 500 (ES) | short | 7744.0 | 7764.5 | ❌ SL | -0.27 % | 5 min |
| 28/09 17:45 | Or (XAU/USD) | short | 4154.9 | 4165.7 | ❌ SL | -0.28 % | 37 min |
| 28/09 17:35 | Nasdaq 100 (NQ) | short | 30485.25 | 30534.0 | ❌ SL | -0.17 % | 34 min |
| 28/09 17:20 | S&P 500 (ES) | short | 7744.0 | 7746.75 | ⏱️ expiré | -0.05 % | 60 min |
| 28/09 16:50 | Nasdaq 100 (NQ) | short | 30501.25 | 30402.25 | ✅ TP | +0.31 % | 4 min |
| 28/09 15:40 | Or (XAU/USD) | short | 4171.0 | 4181.5 | ❌ SL | -0.27 % | 1 min |
| 28/09 10:05 | Or (XAU/USD) | short | 4191.1 | 4180.0 | ✅ TP | +0.24 % | 16 min |
| 28/09 09:01 | Or (XAU/USD) | short | 4205.3 | 4194.6 | ✅ TP | +0.23 % | 9 min |
| 25/09 18:15 | S&P 500 (ES) | long | 7807.0 | 7797.0 | ❌ SL | -0.14 % | 4 min |
| 25/09 16:05 | Bitcoin (BTC/USD) | short | 83227.0 | 83434.0 | ❌ SL | -0.31 % | 2 min |
| 25/09 12:50 | Or (XAU/USD) | long | 4338.6 | 4349.4 | ✅ TP | +0.23 % | 16 min |
| 24/09 21:10 | S&P 500 (ES) | long | 7772.5 | 7766.5 | ❌ SL | -0.09 % | 5 min |
| 24/09 20:25 | S&P 500 (ES) | long | 7763.5 | 7768.5 | ✅ TP | +0.05 % | 0 min |
| 24/09 19:35 | Nasdaq 100 (NQ) | long | 30722.75 | 30694.0 | ❌ SL | -0.10 % | 7 min |

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

- sp500 : {'trend_5m': 0.975, 'trend_15m': 0.975, 'trend_1h': 0.975, 'adx': 0.975, 'vwap': 0.702}

| Variante testée en fantôme | Trades | Gain net moyen | Statut |
|---|---:|---:|---|
| indices le matin européen | 34 | -0.36 R | en test |
| horizon ~3 h | 37 | -0.36 R | en test |
| confiance moyenne | 21 | -0.11 R | en test |
| entrées dans l'heure avant l'ouverture américaine | 2 | +0.01 R | en test |
| reprise juste après un stop | 13 | -0.23 R | en test |
| nouvel actif : Ethereum (ETH/USD) | 5 | -0.55 R | en test |
| nouvel actif : Pétrole WTI (CL) | 26 | -0.04 R | en test |
| nouvel actif : Euro / dollar (6E) | 13 | +0.11 R | en test |

Notes :

- trades réels : +0,08 R ± 0,23 R par trade avant frais sur 98 trades (0 R = hasard)
- aucun critère ne s'écarte du hasard au-delà de la marge de sécurité : poids par défaut conservés
- sp500, tendance (trend_5m, trend_15m, trend_1h, adx) : -0,19 R contre +0,02 R en global sur 114 trades éq. → poids ×0,97 sur cet actif
- sp500, vwap : -0,20 R contre +0,04 R en global sur 111 trades éq. → poids ×0,94 sur cet actif
- variante « indices le matin européen » en test : 34 trades, -0,36 R net, encore 66 trades avant décision
- variante « horizon ~3 h » en test : 37 trades, -0,36 R net, encore 63 trades avant décision
- variante « confiance moyenne » en test : 21 trades, -0,11 R net, encore 79 trades avant décision
- variante « entrées dans l'heure avant l'ouverture américaine » en test : 2 trades, +0,01 R net, encore 98 trades avant décision
- variante « reprise juste après un stop » en test : 13 trades, -0,23 R net, encore 87 trades avant décision
- variante « nouvel actif : Ethereum (ETH/USD) » en test : 5 trades, -0,55 R net, encore 95 trades avant décision
- variante « nouvel actif : Pétrole WTI (CL) » en test : 26 trades, -0,04 R net, encore 74 trades avant décision
- variante « nouvel actif : Euro / dollar (6E) » en test : 13 trades, +0,11 R net, encore 87 trades avant décision
- sortie : stop remonté à l'entrée après +1,0 R ferait mieux (-0,06 R net contre -0,08 R, backtest) : à décider

## Backtests (données historiques 5 min)

| Actif | Période | Signaux | TP | SL | Expirés | Taux de réussite | Hasard attendu | Avantage | P&L net | Espérance nette / trade |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nasdaq 100 (NQ) | 09/07/2026 → 30/09/2026 | 82 | 21 | 39 | 22 | 35% | 41% | -6% | -1.06 % | -0.013 % |
| S&P 500 (ES) | 09/07/2026 → 30/09/2026 | 101 | 35 | 50 | 16 | 41% | 42% | -1% | -0.23 % | -0.002 % |
| Bitcoin (BTC/USD) | 20/07/2026 → 30/09/2026 | 52 | 17 | 23 | 12 | 42% | 41% | +2% | -1.93 % | -0.037 % |
| Ethereum (ETH/USD) | 20/07/2026 → 30/09/2026 | 56 | 11 | 27 | 18 | 29% | 40% | -11% | -6.67 % | -0.119 % |
| Or (XAU/USD) | 09/07/2026 → 30/09/2026 | 124 | 41 | 50 | 33 | 45% | 42% | +3% | -1.40 % | -0.011 % |
| Pétrole WTI (CL) | 14/07/2026 → 30/09/2026 | 181 | 60 | 81 | 40 | 43% | 41% | +1% | +3.92 % | +0.022 % |
| Euro / dollar (6E) | 14/07/2026 → 30/09/2026 | 22 | 5 | 14 | 3 | 26% | 40% | -14% | -0.54 % | -0.025 % |

---

⚠️ Signaux générés automatiquement à partir de données publiques gratuites et d'une analyse algorithmique. Ceci n'est PAS un conseil financier. Aucune stratégie ne garantit un gain. Validez d'abord en paper trading (compte simulé) avant tout passage en argent réel. Vous seul décidez et exécutez vos trades.
