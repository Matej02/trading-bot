// Kontrola: davaji strategie v TypeScriptu stejne signaly jako Python bot?
// Pouziti: npx tsx scripts/compare-signals.ts <soubor.json z dump_signals.py>
import { readFileSync } from "node:fs";
import { barSignal } from "../lib/strategies";
import type { Candle } from "../lib/types";

interface PySignal { i: number; system: string; dir: string; sl: number; tp: number }
const data = JSON.parse(readFileSync(process.argv[2], "utf8")) as { candles: Candle[]; signals: PySignal[] };
const py = new Map(data.signals.map((s) => [`${s.system}|${s.i}`, s]));
let same = 0, onlyPy = 0, onlyTs = 0, levelDiff = 0;
for (const system of ["bbsqueeze_h1", "pullback_h1"]) {
  for (let i = 399; i < data.candles.length; i++) {
    const ts = barSignal(system, data.candles.slice(i - 399, i + 1));
    const p = py.get(`${system}|${i}`);
    if (ts && p) {
      if (ts.dir === p.dir) same++;
      else onlyPy++;
      if (Math.abs(ts.sl - p.sl) > 1e-9 || Math.abs((ts.tp ?? NaN) - p.tp) > 1e-9) levelDiff++;
    } else if (p) {
      onlyPy++;
      console.log("jen Python:", system, i, p.dir);
    } else if (ts) {
      onlyTs++;
      console.log("jen TS:", system, i, ts.dir);
    }
  }
}
console.log(`shodne ${same}, jen Python ${onlyPy}, jen TS ${onlyTs}, jine SL/TP ${levelDiff}`);
process.exit(onlyPy || onlyTs || levelDiff ? 1 : 0);
