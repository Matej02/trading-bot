// Kontrola: dava proraz_d1 v TS stejne signaly jako research_f2.py? (okno 1300 dennich svicek jako 5 let z Yahoo)
// Pouziti: npx tsx scripts/compare-f2.ts <soubor.json>
import { readFileSync } from "node:fs";
import { barSignal } from "../lib/strategies";
import type { Candle } from "../lib/types";

const data = JSON.parse(readFileSync(process.argv[2], "utf8")) as Record<string, { candles: Candle[]; sig: number[] }>;
let bad = 0;
for (const [mk, { candles, sig }] of Object.entries(data)) {
  let same = 0, onlyPy = 0, onlyTs = 0;
  for (let i = Math.max(1300, candles.length - 1500); i < candles.length; i++) {
    const ts = barSignal("proraz_d1", candles.slice(i - 1299, i + 1));
    const t = ts ? (ts.dir === "long" ? 1 : -1) : 0;
    const p = sig[i];
    if (t === p) { if (t) same++; }
    else if (p && !t) onlyPy++;
    else if (t && !p) onlyTs++;
    else onlyPy++; // opacny smer
  }
  console.log(`${mk}: shodne ${same}, jen Python ${onlyPy}, jen TS ${onlyTs}`);
  bad += onlyPy + onlyTs;
}
process.exit(bad ? 1 : 0);
