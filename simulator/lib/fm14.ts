// Experiment F14 - Patek (research_f14_pat.py, vybrana varianta: model A, M15, cele session, TP protejsi H4 zona).
// Trend H4 (2 vyssi high + 2 vyssi low pivotu N=2) -> pullback v poslednich 24 svickach M15 dojde do H4 S/R zony (>= 2 H4
// pivoty do 0,25 ATR H4) -> nizsi high / vyssi low z pivotu M15 (N=3) -> close za poslednim pivotem = vstup trhem ->
// SL za LH/HL + 10 ticku -> TP nejblizsi protejsi H4 zona (2-5 R). Session Praha 9-22.
import { pivots, wilderAtr } from "./fm";
import { bars, closedIdx, czHour, groupBy, type Tb } from "./fm12";
import type { Candle } from "./types";

export interface Fm14Signal { dir: "long" | "short"; sl: number; tp: number; reason: string }
export interface Fm14Input { c15: Candle[]; c1h: Candle[]; tick: number }

const TOL = 0.25, WIN4 = 300;

/** research_f8.last_swing(h, l, N) - jen trend. */
function swingTrend(h: number[], l: number[], N: number): number[] {
  const { ph, pl } = pivots(h, l, N);
  const n = h.length, tr = new Array<number>(n).fill(0);
  const hs: number[] = [], ls: number[] = [];
  for (let i = 0; i < n; i++) {
    const p = i - N;
    if (p >= 0) {
      if (ph[p]) hs.push(h[p]);
      if (pl[p]) ls.push(l[p]);
    }
    if (hs.length >= 2 && ls.length >= 2) {
      const a = hs.length - 1, b = ls.length - 1;
      if (hs[a] > hs[a - 1] && ls[b] > ls[b - 1]) tr[i] = 1;
      else if (hs[a] < hs[a - 1] && ls[b] < ls[b - 1]) tr[i] = -1;
    }
  }
  return tr;
}

/** H4 pivoty (high i low) potvrzene do k4 v okne WIN4: ceny serazene podle indexu potvrzeni. */
function h4Pivots(H4: Tb, k4: number): number[] {
  const { ph, pl } = pivots(H4.h, H4.l, 2);
  const out: number[] = [];
  for (let j = 0; j < H4.h.length; j++) {
    const conf = j + 2;
    if (conf > k4 || conf < k4 - WIN4) continue;
    if (ph[j]) out.push(H4.h[j]);
    if (pl[j]) out.push(H4.l[j]);
  }
  return out;
}

function zoneNear(p: number[], x: number, a4: number): [number, number] | null {
  const m = p.filter((v) => Math.abs(v - x) <= TOL * a4);
  return m.length >= 2 ? [Math.min(...m), Math.max(...m)] : null;
}

function nextZone(p: number[], E: number, d: number, a4: number): number {
  const s = [...p].sort((a, b) => a - b);
  const cand = d === 1 ? s.filter((v) => v > E) : s.filter((v) => v < E).reverse();
  for (const x of cand) {
    const m = s.filter((v) => Math.abs(v - x) <= TOL * a4);
    if (m.length >= 2) return d === 1 ? Math.min(...m) : Math.max(...m);
  }
  return NaN;
}

export function fm14Signal(x: Fm14Input): Fm14Signal | null {
  if (x.c15.length < 100 || x.c1h.length < 24 * 30) return null;
  const X = bars(x.c15, 900), H4 = groupBy(x.c1h, 4 * 3600);
  const j = X.t.length - 1;
  const hEnd = czHour(X.t[j] + 840);
  if (!(hEnd >= 9 && hEnd < 22)) return null;
  const k4 = closedIdx(H4, X.t[j] + 900);
  if (k4 < 5) return null;
  const tr4 = swingTrend(H4.h, H4.l, 2);
  const d = tr4[k4];
  if (d === 0) return null;
  const a4 = wilderAtr(H4.h, H4.l, H4.c, 14)[k4];
  if (!(a4 > 0)) return null;
  // M15 pivoty N=3 potvrzene do svicky j (pivot p je znamy po zavreni p+3)
  const { ph, pl } = pivots(X.h, X.l, 3);
  const piH: [number, number][] = [], piL: [number, number][] = [];
  for (let p = 0; p + 3 <= j; p++) {
    if (ph[p]) piH.push([p, X.h[p]]);
    if (pl[p]) piL.push([p, X.l[p]]);
  }
  if (piH.length < 2 || piL.length < 2) return null;
  let ext: number;
  if (d === -1) {
    const h1 = piH[piH.length - 1][1], h0 = piH[piH.length - 2][1], lastL = piL[piL.length - 1][1];
    if (!(h1 < h0) || !(X.c[j] < lastL && X.c[j - 1] >= lastL)) return null;
    ext = h1;
  } else {
    const l1 = piL[piL.length - 1][1], l0 = piL[piL.length - 2][1], lastH = piH[piH.length - 1][1];
    if (!(l1 > l0) || !(X.c[j] > lastH && X.c[j - 1] <= lastH)) return null;
    ext = l1;
  }
  const E = X.c[j];
  const P = h4Pivots(H4, k4);
  let pull = d === -1 ? -Infinity : Infinity;
  for (let r = Math.max(0, j - 24); r <= j; r++) pull = d === -1 ? Math.max(pull, X.h[r]) : Math.min(pull, X.l[r]);
  const z = zoneNear(P, pull, a4);
  if (!z || (d === -1 && z[1] < E) || (d === 1 && z[0] > E)) return null;
  const sl = ext - d * 10 * x.tick;
  const risk = (E - sl) * d;
  if (risk <= 0) return null;
  const tz = nextZone(P, E, d, a4);
  if (!isFinite(tz)) return null;
  const rt = (tz - E) * d / risk;
  if (rt < 2) return null;
  const R = Math.min(rt, 5);
  const f = (v: number) => v.toPrecision(6);
  return {
    dir: d === 1 ? "long" : "short", sl, tp: E + d * R * risk,
    reason: `Trend H4 ${d === 1 ? "nahoru" : "dolů"}, pullback odmítnut v H4 S/R zóně ${f(z[0])}–${f(z[1])}, ` +
      `${d === 1 ? "vyšší low" : "nižší high"} na M15 a průraz posledního pivotu. SL za ${d === 1 ? "HL" : "LH"}, TP další H4 zóna (${R.toFixed(1)} R).`,
  };
}
