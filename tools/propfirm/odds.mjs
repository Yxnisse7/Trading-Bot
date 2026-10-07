// Chances de réussir le Combine Topstep 50K à partir des trades réels (en R) du bot.
// Moteur : @luxalgo/prop-firm-sim-core (MIT, LuxAlgo), Monte Carlo par bootstrap en blocs (les séries de
// pertes sont conservées). Aucun réseau : les règles Topstep sont écrites ici (Topstep n'est pas dans le
// répertoire de LuxAlgo). Entrée : JSON { profiles: [{key, label, rSeries, tradesPerDay}], risks: [$] }.
// Sortie : JSON avec la probabilité de réussite par profil et par risque, et la règle qui fait échouer.
import { readFileSync, writeFileSync } from "node:fs";
import { simulate } from "@luxalgo/prop-firm-sim-core";

import { TOPSTEP_50K } from "./topstep_spec.mjs";
export { TOPSTEP_50K };

const [, , inPath, outPath, pathsArg] = process.argv;
const input = JSON.parse(readFileSync(inPath, "utf8"));
const paths = Number(pathsArg || 10_000);
const out = { spec: TOPSTEP_50K, paths, seed: 42, profiles: [] };
for (const p of input.profiles) {
  const row = { key: p.key, label: p.label, n: p.rSeries.length, tradesPerDay: p.tradesPerDay, risks: [] };
  if (p.rSeries.length < 10) { row.error = "moins de 10 trades"; out.profiles.push(row); continue; }
  for (const risk of input.risks) {
    try {
      const r = simulate(TOPSTEP_50K, {
        kind: "bootstrap", rSeries: p.rSeries, blockMeanLength: 5,
        tradesPerDay: p.tradesPerDay, tradesPerDayModel: "poisson",
        risk: { mode: "fixed-amount", value: risk },
      }, { seed: 42, paths });
      // même tentative limitée à 10 jours de bourse (2 semaines) : ce qui reste quand on veut aller vite
      const fast = simulate({ ...TOPSTEP_50K, steps: TOPSTEP_50K.steps.map((st) => ({ ...st, maxDays: 10 })) }, {
        kind: "bootstrap", rSeries: p.rSeries, blockMeanLength: 5, tradesPerDay: p.tradesPerDay,
        tradesPerDayModel: "poisson", risk: { mode: "fixed-amount", value: risk },
      }, { seed: 42, paths, includeHistograms: false, simulateFunded: false });
      const a = r.perAttempt;
      const j = r.journey || {};
      row.risks.push({ risk, pass: a.passProbability, pass10: fast.perAttempt.passProbability, ci: a.passProbabilityCi ? [a.passProbabilityCi.low, a.passProbabilityCi.high] : null,
                       fail: a.failureBreakdown, daysPassed: a.avgDaysWhenPassed, daysFailed: a.avgDaysWhenFailed,
                       funded: j.fundedProbability ?? null, attemptCap: j.attemptCap ?? null,
                       attempts: j.attempts ? j.attempts.mean : null, cost: j.cost ? j.cost.mean : null,
                       costP90: j.cost ? j.cost.p90 : null,
                       fundedDays: j.daysToFunded ? { p50: j.daysToFunded.p50, p90: j.daysToFunded.p90 } : null });
      if (!out.flags) out.flags = (r.assumptions?.flags ?? []).map((f) => f.id);
    } catch (e) { row.risks.push({ risk, error: String(e.message || e).slice(0, 300) }); }
  }
  out.profiles.push(row);
}
writeFileSync(outPath, JSON.stringify(out, null, 1));
