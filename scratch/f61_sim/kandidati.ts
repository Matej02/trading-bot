// Kontrola parity 2026-11-24: f76Signal, f73Signal, f79Signal (simulator) proti testu (Python) na historii.
import * as fs from "fs";
import { f73Signal, f76Signal, f79Signal, f79Exit } from "../../simulator/lib/f2x";
type C = { time: number; open: number; high: number; low: number; close: number };
const d = JSON.parse(fs.readFileSync(process.argv[2], "utf-8")) as Record<string, any>;
const spx = d.spx as C[], vix = d.vix as C[], tlt = d.tlt as C[], dax = d.dax as C[];
const iso = (t: number) => new Date(t * 1000).toISOString().slice(0, 10);
function cmp(name: string, got: string[], exp: string[], from: string) {
  const g = got.filter((x) => x >= from), e = exp.filter((x) => x >= from);
  const both = g.filter((x) => e.includes(x));
  console.log(`${name}: simulator ${g.length}, test ${e.length}, shoda ${both.length}`);
  console.log("  jen simulator:", g.filter((x) => !e.includes(x)).slice(0, 10).join(" "), "| jen test:", e.filter((x) => !g.includes(x)).slice(0, 10).join(" "));
}
const g76: string[] = [], g73: string[] = [];
for (let i = 300; i < spx.length; i++) {
  const c = spx.slice(0, i + 1);
  const t = c[i].time;
  if (f76Signal(c, vix.filter((x) => x.time <= t))) g76.push(iso(t));
  if (f73Signal(c, tlt.filter((x) => x.time <= t))) g73.push(iso(t));
}
cmp("F76 VIX>=30", g76, d.exp76, "2012-01-01");
cmp("F73 dluhopisy", g73, d.exp73, "2012-01-01");
const s79: string[] = [], x79: string[] = [];
for (let i = 30; i < dax.length; i++) {
  const c = dax.slice(0, i + 1);
  if (f79Signal(c, "GER_30mini")) s79.push(iso(c[i].time));
  if (f79Exit(c, "GER_30mini")) x79.push(iso(c[i].time));
}
console.log("F79 DAX signaly 2023-2026:", s79.filter((x) => x >= "2023-01-01").join(" "));
console.log("F79 DAX vystupy 2025-2026:", x79.filter((x) => x >= "2025-06-01").join(" "));
