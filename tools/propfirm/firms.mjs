// Comparaison des prop firms : les mêmes trades (en R) rejoués sur chaque compte d'évaluation de 50K.
// Règles des firmes : annuaire public de LuxAlgo (données de luxalgo.com/prop-firms), traduites par leur
// adaptateur (`@luxalgo/prop-firm-sim-core/directory`), qui refuse un compte dont la perte maximale est
// ambiguë. Pour quelques firmes futures refusées, le type de perte maximale est complété ici (OVERRIDES),
// d'après plusieurs sources publiques recoupées en octobre 2026. Topstep : nos règles vérifiées.
// Entrée : JSON { profiles: [{key,label,rSeries,tradesPerDay}], risks: [$], firms: [lignes de l'annuaire] }.
import { readFileSync, writeFileSync } from "node:fs";
import { simulate } from "@luxalgo/prop-firm-sim-core";
import { adaptFirm } from "@luxalgo/prop-firm-sim-core/directory";
import { TOPSTEP_50K } from "./topstep_spec.mjs";

const EOD = { maxLossMode: "trailing-realized-eod", maxLossLocksAtInitial: true };
const INTRADAY = { maxLossMode: "trailing-intraday-unrealized", maxLossLocksAtInitial: true };
export const OVERRIDES = {
  "alpha-futures-standard-1-step-50k": { ...EOD, consistencyMaxBestDayPct: 50 },
  "alpha-futures-advanced-plan-1-step-50k": { ...EOD, consistencyMaxBestDayPct: 50 },
  "alpha-futures-zero-1-step-50k": EOD,
  "earn2trade-the-gauntlet-mini-50k-1-step-50k": EOD,
  "earn2trade-trader-career-path-50k-1-step-50k": EOD,
  "tradeday-50k-eod-evaluation-1-step-50k": { ...EOD, consistencyMaxBestDayPct: 30 },
  "tradeday-50k-intraday-evaluation-1-step-50k": { ...INTRADAY, consistencyMaxBestDayPct: 30 },
  "tradeify-growth-plan-1-step-50k": EOD,
  // Apex : comptes « Full » d'avant mars 2026 (perte maximale qui suit le plus haut, positions ouvertes comprises)
  "apex-trader-funding-rithmic-50k-full-1-step-50k": INTRADAY,
  "apex-trader-funding-tradovate-50k-full-1-step-50k": INTRADAY,
  "apex-trader-funding-wealthcharts-1-step-50k": INTRADAY,
  // FTMO 1-Step (lancé en février 2026) : l'annuaire indique 90 $ et une perte maximale fixe ; la plupart des
  // sources donnent environ 319 $, 10 % qui suit le plus haut de fin de journée et une règle « meilleur jour » 50 %
  "ftmo-normal-challenge-1-step-50k": { ...EOD, price: 319, consistencyMaxBestDayPct: 50 },
};

export function challenges(firms, size = 50_000) {
  const out = [{ firmId: "topstep", firm: "Topstep", productType: "futures", spec: TOPSTEP_50K, inferred: [],
                 overnight: false, weekend: false, source: "règles vérifiées sur help.topstep.com (octobre 2026)" }];
  for (const f of firms) {
    const fixed = { ...f, challenges: f.challenges.map((c) => ({ ...c, ...(OVERRIDES[c.challengeId] || {}) })) };
    for (const a of adaptFirm(fixed)) {
      if (a.spec.accountSize !== size || !a.spec.steps.length) continue;
      const row = f.challenges.find((c) => c.challengeId === a.challengeId) || {};
      if (row.steps === 0) continue;                       // financement immédiat : pas d'évaluation à réussir
      out.push({ firmId: a.propfirmId, firm: a.firmName, productType: a.productType, spec: a.spec,
                 inferred: a.inferredFields, completed: Boolean(OVERRIDES[a.challengeId]),
                 overnight: row.overnightHolding ?? null, weekend: row.weekendHolding ?? null,
                 source: row.sourceUrl || "annuaire LuxAlgo" });
    }
  }
  return out;
}

const fees = (s) => ({ price: s.fees?.price ?? null, billing: s.fees?.billing ?? null,
                       activation: s.fees?.activationFee ?? null, reset: s.fees?.resetFee ?? null });

if (import.meta.url === `file://${process.argv[1]}`) {
  const [, , inPath, outPath, pathsArg] = process.argv;
  const input = JSON.parse(readFileSync(inPath, "utf8"));
  const paths = Number(pathsArg || 5_000);
  const out = { paths, seed: 42, challenges: [], errors: [] };
  for (const c of challenges(input.firms)) {
    const row = { firmId: c.firmId, firm: c.firm, name: c.spec.name, productType: c.productType, steps: c.spec.steps.length,
                  targetPct: c.spec.steps.map((s) => s.profitTargetPct ?? (s.profitTargetAmount / c.spec.accountSize * 100)),
                  maxLoss: c.spec.maxLoss, dailyLoss: c.spec.dailyLoss ?? null, fees: fees(c.spec),
                  inferred: c.inferred, completed: c.completed || false, source: c.source,
                  overnight: c.overnight, weekend: c.weekend, results: {} };
    for (const p of input.profiles) {
      row.results[p.key] = [];
      for (const risk of input.risks) {
        try {
          const r = simulate(c.spec, { kind: "bootstrap", rSeries: p.rSeries, blockMeanLength: 5, tradesPerDay: p.tradesPerDay,
                                       tradesPerDayModel: "poisson", risk: { mode: "fixed-amount", value: risk } },
                             { seed: 42, paths, includeHistograms: false });
          const a = r.perAttempt, j = r.journey || {};
          row.results[p.key].push({ risk, pass: a.passProbability, attempts: j.attempts?.mean ?? null,
                                    cost: j.cost?.mean ?? null, days: a.avgDaysWhenPassed ?? null,
                                    ev: r.ev?.evTotal ?? null, evPositive: r.ev?.pPositive ?? null });
        } catch (e) { out.errors.push(`${c.spec.name} : ${String(e.message || e).slice(0, 200)}`); }
      }
    }
    out.challenges.push(row);
  }
  writeFileSync(outPath, JSON.stringify(out));
}
