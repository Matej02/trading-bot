// Kontrola: experiment F9 (fm_*_h4) v TS dava stejne signaly jako Python (research_f9.py, H4 zaklad).
// Pouziti: npx tsx scripts/compare-fm.ts ../scratch/f9_parita.json
import { readFileSync } from "node:fs";
import { fmSignal, type FmSystem } from "../lib/fm";
import type { Candle } from "../lib/types";

const data = JSON.parse(readFileSync(process.argv[2], "utf8")) as Record<string, { candles: Candle[]; py: Record<string, [number, number, number][]> }>;
const MAP: Record<string, FmSystem> = { mss: "fm_mss_h4", prurazPivot: "fm_pruraz_h4", zona: "fm_zona_h4" };
for (const [mk, { candles, py }] of Object.entries(data)) {
  const t0 = candles[0].time + 60 * 86400;
  for (const [trig, sys] of Object.entries(MAP)) {
    const ts: [number, number, number][] = [];
    for (let i = 300; i < candles.length; i++) {
      if (candles[i].time < t0) continue;
      const s = fmSignal(sys, candles.slice(Math.max(0, i - 999), i + 1));
      if (s) ts.push([candles[i].time, s.dir === "long" ? 1 : -1, s.sl]);
    }
    const P = new Map(py[trig].map((x) => [`${x[0]}|${x[1]}`, x[2]]));
    let both = 0, slOk = 0;
    for (const x of ts) {
      const k = `${x[0]}|${x[1]}`;
      if (P.has(k)) { both++; if (Math.abs(P.get(k)! - x[2]) <= 1e-9 * Math.max(1, Math.abs(x[2]))) slOk++; }
    }
    const pyN = new Set(py[trig].map((x) => `${x[0]}|${x[1]}`)).size;
    console.log(`${mk} ${sys}: TS ${ts.length}, Python ${pyN}, shoda ${both} (SL stejny ${slOk}), jen TS ${ts.length - both}, jen Python ${pyN - both}`);
    const onlyTs = ts.filter((x) => !P.has(`${x[0]}|${x[1]}`)).slice(0, 3).map((x) => new Date(x[0] * 1000).toISOString());
    const T = new Set(ts.map((x) => `${x[0]}|${x[1]}`));
    const onlyPy = py[trig].filter((x) => !T.has(`${x[0]}|${x[1]}`)).slice(0, 3).map((x) => new Date(x[0] * 1000).toISOString());
    if (onlyTs.length || onlyPy.length) console.log("   jen TS:", onlyTs.join(" "), "| jen Py:", onlyPy.join(" "));
  }
}
