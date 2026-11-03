// Kontrola: experiment F12 (fm12_mucka_m1) v TS dava stejne signaly jako Python (scratch/f12_parita.py).
// Pouziti: npx tsx scripts/compare-f12.ts ../scratch/f12_parita_EURUSD.json
import { readFileSync } from "node:fs";
import { fm12Signal } from "../lib/fm12";
import type { Candle } from "../lib/types";

const D = JSON.parse(readFileSync(process.argv[2], "utf8")) as {
  mk: string; A: number; B: number; pip: number; fx: boolean; c1: Candle[]; c15: Candle[]; c1h: Candle[]; py: [number, number, number][];
};
const kzFmt = new Intl.DateTimeFormat("en-US", { timeZone: "Europe/Prague", hourCycle: "h23", hour: "numeric", minute: "numeric" });
const czh = (t: number) => { const p = Object.fromEntries(kzFmt.formatToParts(new Date(t * 1000)).map((x) => [x.type, x.value])); return (+p.hour % 24) + +p.minute / 60; };
const ts: [number, number, number][] = [];
let j15 = 0, j1h = 0;
for (let i = 0; i < D.c1.length; i++) {
  const t = D.c1[i].time;
  if (t < D.A || t >= D.B) continue;
  const h = czh(t);
  if (!((h >= 9 && h < 11) || (h >= 13.5 && h < 17))) continue;
  const tEnd = t + 60;
  while (j15 < D.c15.length && D.c15[j15].time + 900 <= tEnd) j15++;
  while (j1h < D.c1h.length && D.c1h[j1h].time + 3600 <= tEnd) j1h++;
  const s = fm12Signal({ c1: D.c1.slice(Math.max(0, i - 6999), i + 1), c15: D.c15.slice(Math.max(0, j15 - 3000), j15),
    c1h: D.c1h.slice(Math.max(0, j1h - 6500), j1h), pip: D.pip, fx: D.fx });
  if (s) ts.push([t, s.dir === "long" ? 1 : -1, s.sl]);
}
const P = new Map(D.py.map((x) => [`${x[0]}|${x[1]}`, x[2]]));
let both = 0, slOk = 0;
for (const x of ts) {
  const k = `${x[0]}|${x[1]}`;
  if (P.has(k)) { both++; if (Math.abs(P.get(k)! - x[2]) <= 1e-6 * Math.max(1, Math.abs(x[2]))) slOk++; }
}
console.log(`${D.mk} fm12: TS ${ts.length}, Python ${D.py.length}, shoda ${both} (SL stejny ${slOk}), jen TS ${ts.length - both}, jen Python ${D.py.length - both}`);
const T = new Set(ts.map((x) => `${x[0]}|${x[1]}`));
console.log("   jen TS:", ts.filter((x) => !P.has(`${x[0]}|${x[1]}`)).slice(0, 6).map((x) => new Date(x[0] * 1000).toISOString()).join(" "));
console.log("   jen Py:", D.py.filter((x) => !T.has(`${x[0]}|${x[1]}`)).slice(0, 6).map((x) => new Date(x[0] * 1000).toISOString()).join(" "));
