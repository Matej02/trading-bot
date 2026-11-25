// Kontrola: F93 v TS (lib/f93.ts) dava stejne obchody a vysledky jako test v Pythonu (scratch/f93_sim/f93_export.py).
// Pouziti: npx tsx scripts/compare-f93.ts "../research_data/f88/f93_parita_vstup.json"
import { readFileSync } from "node:fs";
import { cleanDays, f93AllSignals, indexReturns, type F93Day } from "../lib/f93";

const J = JSON.parse(readFileSync(process.argv[2], "utf8")) as {
  spx: [string, number][]; stocks: Record<string, [string, number, number, number, number][]>; events: Record<string, string[]>;
  trades: { t: string; day: string; z: number; s: number; norm: number; pess: number; gross: number }[];
};
const ixr = indexReturns(J.spx.map(([d, c]) => ({ d, c })));
const ts = new Map<string, { z: number; s: number; norm: number; pess: number; gross: number }>();
for (const [t, rows] of Object.entries(J.stocks)) {
  const days: F93Day[] = cleanDays(rows.map(([d, o, h, l, c]) => ({ d, o, h, l, c })));
  for (const s of f93AllSignals(t, days, ixr, J.events[t] ?? [])) {
    if (s.dayK < "2004-09-01") continue;
    ts.set(`${t}|${s.dayK}`, { z: s.z, s: s.dir, norm: s.res.rNorm, pess: s.res.rPess, gross: s.res.rGross });
  }
}
const py = new Map(J.trades.map((x) => [`${x.t}|${x.day}`, x]));
let same = 0, dirDiff = 0, rDiff = 0, maxDz = 0, maxDr = 0;
const onlyPy: string[] = [], onlyTs: string[] = [];
for (const [k, p] of py) {
  const t = ts.get(k);
  if (!t) { onlyPy.push(k); continue; }
  if (t.s !== p.s) { dirDiff++; continue; }
  const dz = Math.abs(t.z - p.z), dr = Math.max(Math.abs(t.norm - p.norm), Math.abs(t.pess - p.pess), Math.abs(t.gross - p.gross));
  maxDz = Math.max(maxDz, dz); maxDr = Math.max(maxDr, dr);
  if (dr > 1e-9) rDiff++; else same++;
}
for (const k of ts.keys()) if (!py.has(k)) onlyTs.push(k);
const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / Math.max(xs.length, 1);
console.log(`F93 shoda: test ${py.size} obchodů, TS ${ts.size}, shodných ${same} (${(100 * same / py.size).toFixed(1)} %)`);
console.log(`  jiný směr ${dirDiff}, jiný výsledek ${rDiff}, max rozdíl z ${maxDz.toExponential(2)}, max rozdíl R ${maxDr.toExponential(2)}`);
console.log(`  jen v testu ${onlyPy.length}: ${onlyPy.slice(0, 8).join(", ")}`);
console.log(`  jen v TS ${onlyTs.length}: ${onlyTs.slice(0, 8).join(", ")}`);
console.log(`  průměr R (běžné náklady): test ${mean(J.trades.map((x) => x.norm)).toFixed(4)}, TS ${mean([...ts.values()].map((x) => x.norm)).toFixed(4)}`);
