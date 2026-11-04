// Kontrola: experiment F15 (fm15_hve_h1) v TS dava stejne signaly jako Python (scratch/f15_parita.py).
// Pouziti: npx tsx scripts/compare-f15.ts ../scratch/f15_parita_EURUSD.json
import { readFileSync } from "node:fs";
import { fm15Signal } from "../lib/fm15";
import type { Candle } from "../lib/types";

const D = JSON.parse(readFileSync(process.argv[2], "utf8")) as { mk: string; A: number; B: number; c1h: Candle[]; py: [number, number, number][] };
const ts: [number, number, number][] = [];
for (let i = 0; i < D.c1h.length; i++) {
  const t = D.c1h[i].time;
  if (t < D.A || t >= D.B) continue;
  const s = fm15Signal(D.c1h.slice(Math.max(0, i - 6499), i + 1));
  if (s) ts.push([t, s.dir === "long" ? 1 : -1, s.sl]);
}
const P = new Map(D.py.map((x) => [`${x[0]}|${x[1]}`, x[2]]));
let both = 0, slOk = 0;
for (const x of ts) {
  const k = `${x[0]}|${x[1]}`;
  if (P.has(k)) { both++; if (Math.abs(P.get(k)! - x[2]) <= 1e-6 * Math.max(1, Math.abs(x[2]))) slOk++; }
}
console.log(`${D.mk} fm15: TS ${ts.length}, Python ${D.py.length}, shoda ${both} (SL stejny ${slOk}), jen TS ${ts.length - both}, jen Python ${D.py.length - both}`);
const T = new Set(ts.map((x) => `${x[0]}|${x[1]}`));
console.log("   jen TS:", ts.filter((x) => !P.has(`${x[0]}|${x[1]}`)).slice(0, 6).map((x) => new Date(x[0] * 1000).toISOString()).join(" "));
console.log("   jen Py:", D.py.filter((x) => !T.has(`${x[0]}|${x[1]}`)).slice(0, 6).map((x) => new Date(x[0] * 1000).toISOString()).join(" "));
