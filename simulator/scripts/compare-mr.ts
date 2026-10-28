// Kontrola: RSI(2) pullback (mr_rsi2_d1) v TS dava stejne signaly jako Python (research_f6.py).
// Pouziti: npx tsx scripts/compare-mr.ts <json z Pythonu>
import { readFileSync } from "node:fs";
import { barSignal } from "../lib/strategies";
import type { Candle } from "../lib/types";

const { candles, py } = JSON.parse(readFileSync(process.argv[2], "utf8")) as { candles: Candle[]; py: number[] };
const ts: number[] = [];
for (let i = 200; i < candles.length; i++) {
  if (candles[i].time < 1262304000) continue;
  if (barSignal("mr_rsi2_d1", candles.slice(0, i + 1))) ts.push(candles[i].time);
}
const P = new Set(py), T = new Set(ts);
const both = ts.filter((x) => P.has(x)).length;
console.log(`TS ${ts.length}, Python ${py.length}, shoda ${both}, jen TS ${ts.length - both}, jen Python ${py.length - both}`);
