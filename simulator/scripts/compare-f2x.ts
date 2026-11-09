// Kontrola shody: F33 (rebalancovani), F29 (krypto momentum) a F31 (drift pred FOMC) v TS vs. Python testy.
// Pouziti: npx tsx scripts/compare-f2x.ts <research_data/f2x_parita.json z scratch/f2x_parita_export.py>
import { readFileSync } from "node:fs";
import { f31Exit } from "../lib/f2x";
import { barSignal } from "../lib/strategies";
import type { Candle } from "../lib/types";
import { nyParts } from "../lib/usCalendar";

const J = JSON.parse(readFileSync(process.argv[2], "utf8")) as {
  spx: Candle[]; spy: Candle[]; tlt: Candle[]; py33: { time: number; dir: string }[];
  btc: Candle[]; py29: number[]; h1: Candle[];
};
const day = (t: number) => new Date(t * 1000).toISOString().slice(0, 10);

// F33: signal na denni svicce SPX500mini (L-3), SPY/TLT jen do toho dne
const ts33: { time: number; dir: string }[] = [];
let k = 0;
for (let i = 30; i < J.spx.length; i++) {
  const t = J.spx[i].time;
  if (t < Date.UTC(2003, 1, 1) / 1000) continue;
  while (k < J.spy.length && J.spy[k].time <= t) k++;
  const spy = J.spy.slice(0, k);
  const tlt = J.tlt.filter((x) => x.time <= t);
  const s = barSignal("f33_rebal_d1", J.spx.slice(0, i + 1), undefined, "SPX500mini", { SPY: spy, TLT: tlt });
  if (s) ts33.push({ time: t, dir: s.dir });
}
const P = new Map(J.py33.map((x) => [x.time, x.dir]));
const T = new Map(ts33.map((x) => [x.time, x.dir]));
const both = ts33.filter((x) => P.get(x.time) === x.dir).length;
console.log(`F33: TS ${ts33.length}, Python ${J.py33.length}, shoda (den i směr) ${both}`);
console.log("  jen Python:", J.py33.filter((x) => T.get(x.time) !== x.dir).map((x) => `${day(x.time)} ${x.dir}`).join(", ") || "-");
console.log("  jen TS:", ts33.filter((x) => P.get(x.time) !== x.dir).map((x) => `${day(x.time)} ${x.dir}`).join(", ") || "-");

// F29: nedele s 28dennim vynosem > 0
const ts29: number[] = [];
for (let i = 30; i < J.btc.length; i++) {
  if (barSignal("f29_krypto_mom_d1", J.btc.slice(0, i + 1), undefined, "BTCUSD")) ts29.push(J.btc[i].time);
}
const P29 = new Set(J.py29);
console.log(`F29: TS ${ts29.length}, Python ${J.py29.length}, shoda ${ts29.filter((x) => P29.has(x)).length}`);

// F31: vstupy a vystupy na hodinovych svickach 2026 (S&P z MT5, skutecne UTC)
const ent: string[] = [], ex: string[] = [];
for (let i = 600; i < J.h1.length; i++) {
  const w = J.h1.slice(i - 599, i + 1);
  const p = nyParts(J.h1[i].time);
  if (barSignal("f31_fomc_h1", w, undefined, "SPX500fut")) ent.push(`${p.date} ${p.hour}:00 NY`);
  if (f31Exit(w)) ex.push(`${p.date} ${p.hour}:00 NY`);
}
console.log(`F31 vstupy (svíčka začínající v):  ${ent.join(" | ")}`);
console.log(`F31 výstupy (svíčka začínající v): ${ex.join(" | ")}`);
