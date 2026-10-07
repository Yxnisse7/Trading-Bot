// Règles du Topstep Trading Combine 50K, partagées par odds.mjs et firms.mjs.
// Topstep, Trading Combine 50K, parcours Standard (help.topstep.com, octobre 2026) : objectif 3 000 $,
// perte maximale 2 000 $ qui suit le plus haut de fin de journée et se fige au solde de départ, règle de
// cohérence 50 %, 49 $/mois, remise à zéro 49 $, activation 149 $. La perte journalière (1 000 $) n'est pas
// une règle éliminatoire chez Topstep : elle coupe seulement la journée. Le moteur ne sait que la traiter
// comme un échec, elle est donc laissée de côté (léger optimisme quand 2 pertes suffisent à l'atteindre).
export const TOPSTEP_50K = {
  challengeId: "topstep-50k-combine",
  name: "Topstep Trading Combine 50K (Standard)",
  productType: "futures",
  accountSize: 50_000,
  steps: [{ profitTargetAmount: 3_000, minTradingDays: 2, consistency: { maxBestDayProfitPct: 50 } }],
  dailyLoss: null,
  maxLoss: { amount: 2_000, mode: "trailing-realized-eod", locksAtInitial: true },
  fees: { price: 49, billing: "monthly", resetFee: 49, activationFee: 149 },
  funded: { profitSplitPct: 90, payoutFrequency: "on-demand" },
};
