// Kontrola: experiment F16 (fm16_hak_m15) v TS dava stejne signaly jako Python (scratch/f16_parita.py).
// Pouziti: npx tsx scripts/compare-f16.ts ../scratch/f16_parita_NAS100mini.json
import { readFileSync } from "node:fs";
import { fm16Signal } from "../lib/fm16";
import type { Candle } from "../lib/types";

const D = JSON.parse(readFileSync(process.argv[2], "utf8")) as {
  mk: string; A: number; B: number; c15: Candle[]; c1h: Candle[]; py: [number, number, number][];
};
const ts: [number, number, number][] = [];
let j1h = 0;
for (let i = 0; i < D.c15.length; i++) {
  const t = D.c15[i].time;
  if (t < D.A || t >= D.B) continue;
  while (j1h < D.c1h.length && D.c1h[j1h].time + 3600 <= t + 900) j1h++;
  const s = fm16Signal(D.c15.slice(Math.max(0, i - 2999), i + 1), D.c1h.slice(Math.max(0, j1h - 6500), j1h));
  if (s) ts.push([t, s.dir === "long" ? 1 : -1, s.sl]);
}
const P = new Map(D.py.map((x) => [`${x[0]}|${x[1]}`, x[2]]));
let both = 0, slOk = 0;
for (const x of ts) {
  const k = `${x[0]}|${x[1]}`;
  if (P.has(k)) { both++; if (Math.abs(P.get(k)! - x[2]) <= 1e-6 * Math.max(1, Math.abs(x[2]))) slOk++; }
}
console.log(`${D.mk} fm16: TS ${ts.length}, Python ${D.py.length}, shoda ${both} (SL stejny ${slOk}), jen TS ${ts.length - both}, jen Python ${D.py.length - both}`);
const T = new Set(ts.map((x) => `${x[0]}|${x[1]}`));
console.log("   jen TS:", ts.filter((x) => !P.has(`${x[0]}|${x[1]}`)).slice(0, 6).map((x) => new Date(x[0] * 1000).toISOString()).join(" "));
console.log("   jen Py:", D.py.filter((x) => !T.has(`${x[0]}|${x[1]}`)).slice(0, 6).map((x) => new Date(x[0] * 1000).toISOString()).join(" "));
