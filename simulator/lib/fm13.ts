// Experiment F13 - Veselovsky (research_f13_ves.py, vybrana varianta: 1m, uroven = sweep likvidity, vstup 50 % OB, TP cil biasu).
// Daily bias (jeho pravidla) -> killzone (Praha Londyn 8-11 / long do 11:30, NY 14-17) -> sweep Asie (2-8), PDL/PDH nebo
// 15m swingu poprve touto nohou, pod/nad NY daily open -> MSS na 1m (close za strong levelem s momentem) s FVG v noze ->
// limit na 50 % tel OB z nohy MSS (zive: signal na 1m svicce, ktera uroven zasahne) -> SL 2 pipy za sweep -> TP = PDH/PDL.
import { pivots, wilderAtr } from "./fm";
import { bars, closedIdx, czHour, groupBy, lt, ms, type Tb } from "./fm12";
import type { Candle } from "./types";

export interface Fm13Signal { dir: "long" | "short"; sl: number; tp: number; reason: string }
export interface Fm13Input { c1: Candle[]; c15: Candle[]; c1h: Candle[]; pip: number; fx: boolean }

const DAY = 86400;

/** Bias pro den k z dennich svicek (k-1 vcera, k-2 predvcerem) - research_f13_ves.michal_bias. */
function michalBias(D: Tb, k: number): number {
  if (k < 2) return 0;
  const { o, h, l, c } = D, p = k - 1, q = k - 2;
  if (c[p] > h[q]) return 1;
  if (c[p] < l[q]) return -1;
  if (h[p] > h[q] && c[p] < h[q]) return -1;
  if (l[p] < l[q] && c[p] > l[q]) return 1;
  const bt = Math.max(o[q], c[q]), bb = Math.min(o[q], c[q]);
  if (c[p] > bt) return c[p] >= bt + 0.5 * (h[q] - bt) ? 1 : -1;
  if (c[p] < bb) return c[p] <= bb - 0.5 * (bb - l[q]) ? -1 : 1;
  return 0;
}

const czDateFmt = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Prague", year: "numeric", month: "2-digit", day: "2-digit" });
const czDayCache = new Map<number, string>();
function czDay(t: number): string {
  const hk = Math.floor(t / 3600);
  let s = czDayCache.get(hk);
  if (s === undefined) {
    if (czDayCache.size > 50_000) czDayCache.clear();
    s = czDateFmt.format(new Date(hk * 3600 * 1000));
    czDayCache.set(hk, s);
  }
  return s;
}

/** Konec killzone (cas v hodinach Prahy), ve ktere lezi h, nebo null. */
function kzEnd(h: number, d: number): number | null {
  if (h >= 8 && h < (d === 1 ? 11.5 : 11)) return d === 1 ? 11.5 : 11;
  if (h >= 14 && h < 17) return 17;
  return null;
}

export function fm13Signal(x: Fm13Input): Fm13Signal | null {
  if (x.c1.length < 1500 || x.c15.length < 200 || x.c1h.length < 24 * 30) return null;
  const T1 = bars(x.c1, 60), T15 = bars(x.c15, 900), D = groupBy(x.c1h, DAY);
  const L = T1.t.length - 1;
  const S1 = ms(T1);
  const aD = wilderAtr(D.h, D.l, D.c, 14);
  const { ph, pl } = pivots(T15.h, T15.l, 2);
  for (let qi = S1.ev.length - 1; qi >= 1; qi--) {
    const e = S1.ev[qi];
    const ic = e.i;
    if (T1.t[L] - T1.t[ic] > 4 * 3600) break;
    if (!e.flip || S1.ev[qi - 1].d !== -e.d || ic >= L) continue;
    const d = e.d;
    const hc = czHour(T1.t[ic]);
    const ke = kzEnd(hc, d);
    const hL = czHour(T1.t[L]);
    // posledni svicka musi lezet ve stejne killzone jako MSS a pred jejim koncem
    if (ke === null || czDay(T1.t[L]) !== czDay(T1.t[ic]) || hL < hc || hL >= ke) continue;
    const tic = T1.t[ic] + 60;
    const kD = closedIdx(D, tic) + 1;              // den (17:00 NY), do ktereho patri MSS
    if (kD < 2 || kD > D.t.length) continue;
    if (michalBias(D, kD) !== d) continue;
    const pd = kD - 1;
    const tgt = d === 1 ? D.h[pd] : D.l[pd];
    // zacatek dne 17:00 NY v 1m datech
    const dayKey = Math.floor(lt(T1.t[ic]) / DAY);
    let sDay = ic;
    while (sDay > 0 && Math.floor(lt(T1.t[sDay - 1]) / DAY) === dayKey) sDay--;
    let hit = false;
    for (let r = sDay; r <= ic; r++) if (d === 1 ? T1.h[r] >= tgt : T1.l[r] <= tgt) { hit = true; break; }
    if (hit) continue;                              // cil biasu uz trefen -> den hotovy
    const sti = e.sti, sv = e.st;
    if (ic - sti > 180 || czHour(T1.t[sti]) < 8) continue;
    // Asie 2-8 Praha dne MSS
    const dk = czDay(T1.t[ic]);
    let aH = -Infinity, aL = Infinity, i8 = -1;
    for (let r = Math.max(0, sti - 1200); r <= sti; r++) {
      if (czDay(T1.t[r]) !== dk) continue;
      const hr = czHour(T1.t[r]);
      if (hr >= 2 && hr < 8) { aH = Math.max(aH, T1.h[r]); aL = Math.min(aL, T1.l[r]); }
      if (hr >= 8 && i8 < 0) i8 = r;
    }
    if (!isFinite(aH) || i8 < 0) continue;
    i8 = Math.max(i8, sDay);
    const levels: [number, number][] = [[d === 1 ? aL : aH, i8], [d === 1 ? D.l[pd] : D.h[pd], i8]];
    // posledni potvrzeny 15m swing (pivot N=2, potvrzeni po zavreni svicky j+2) pred sweepem
    for (let j = T15.t.length - 3; j >= 0; j--) {
      const conf = T15.t[j + 2] + 900;            // konec svicky j+2
      if (conf > T1.t[sti]) continue;
      if (d === 1 ? pl[j] : ph[j]) {
        let f0 = sti;
        while (f0 > 0 && T1.t[f0 - 1] >= conf - 60) f0--;
        levels.push([d === 1 ? T15.l[j] : T15.h[j], Math.max(f0, i8)]);
        break;
      }
    }
    let took = false;
    for (const [lv, f0] of levels) {
      if ((sv - lv) * d >= 0) continue;
      for (let r = f0; r <= sti; r++) {
        if (d === 1 ? T1.l[r] < lv : T1.h[r] > lv) { took = r >= sti - 60; break; }
      }
      if (took) break;
    }
    if (!took) continue;
    // NY daily open (0:00 NY) dne sweepu
    const nyKey = Math.floor((lt(T1.t[sti]) - 7 * 3600) / DAY);
    let r0 = sti;
    while (r0 > 0 && Math.floor((lt(T1.t[r0 - 1]) - 7 * 3600) / DAY) === nyKey) r0--;
    const nydo = T1.o[r0];
    if (d === 1 ? !(sv < nydo) : !(sv > nydo)) continue;
    // displacement: FVG v noze MSS
    let fvg = false;
    for (let r = sti + 2; r <= ic; r++) if (d === 1 ? T1.l[r] > T1.h[r - 2] : T1.h[r] < T1.l[r - 2]) { fvg = true; break; }
    if (!fvg) continue;
    // OB = posledni rada svicek opacne barvy pred impulzem (jen tela), vstup na 50 %
    let ob = e.brk - 1;
    while (ob > sti && (T1.c[ob] - T1.o[ob]) * d >= 0) ob--;
    if ((T1.c[ob] - T1.o[ob]) * d >= 0) continue;
    let s = ob;
    while (s - 1 >= sti && (T1.c[s - 1] - T1.o[s - 1]) * d < 0 && ob - s < 4) s--;
    let blo = Infinity, bhi = -Infinity;
    for (let r = s; r <= ob; r++) { blo = Math.min(blo, T1.o[r], T1.c[r]); bhi = Math.max(bhi, T1.o[r], T1.c[r]); }
    const E = 0.5 * (blo + bhi);
    if (d === 1 ? E >= T1.c[ic] : E <= T1.c[ic]) continue;
    const sl = sv - d * 2 * x.pip;
    const risk = (E - sl) * d;
    const a = aD[pd];
    if (!(a > 0) || risk <= 0 || risk > (x.fx ? 15 * x.pip : 0.21 * a)) continue;
    const rt = (tgt - E) * d / risk;
    if (rt < 2) continue;
    const tp = E + d * Math.min(rt, 10) * risk;
    // limit na E: signal jen na prvni 1m svicce po MSS, ktera ho zasahne
    let touch = -1;
    for (let r = ic + 1; r <= L; r++) if (d === 1 ? T1.l[r] <= E : T1.h[r] >= E) { touch = r; break; }
    if (touch !== L) continue;
    const f = (v: number) => v.toPrecision(6);
    return {
      dir: d === 1 ? "long" : "short", sl, tp,
      reason: `Daily bias ${d === 1 ? "bullish" : "bearish"} (cíl ${f(tgt)}), sweep likvidity ${f(sv)} ${d === 1 ? "pod" : "nad"} NY open, ` +
        `MSS na 1m s FVG v killzone, návrat na 50 % OB (${f(E)}). SL 2 pipy za sweep, TP cíl biasu (${Math.min(rt, 10).toFixed(1)} R).`,
    };
  }
  return null;
}
