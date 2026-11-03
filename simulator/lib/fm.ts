// Experiment F9 - kombinace konceptu z FM PDF (research_f9.py, H4 zaklad). Prevedeno 1:1 z Pythonu.
// H4 svicky se skladaji z uzavrenych H1 svicek (bloky po 4 h od 17:00 NY), den = 17:00-17:00 NY.
// Signal jen na zavreni H4 bloku; SL podle konceptu, TP v R (rrr systemu).
import type { Candle } from "./types";

export type FmSystem = "fm_mss_h4" | "fm_pruraz_h4" | "fm_zona_h4";
export interface FmSignal { dir: "long" | "short"; sl: number; reason: string }

const nyFmt = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York", hourCycle: "h23", year: "numeric", month: "numeric", day: "numeric", hour: "numeric", minute: "numeric",
});
/** NY cas jako by byl UTC + 7 h (0:00 = 17:00 NY), stejne jako lt v Pythonu. */
export function ltOf(t: number): number {
  const p: Record<string, string> = {};
  for (const x of nyFmt.formatToParts(new Date(t * 1000))) p[x.type] = x.value;
  return Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour % 24, +p.minute) / 1000 + 7 * 3600;
}

interface Bars { o: number[]; h: number[]; l: number[]; c: number[]; hl: number[]; day: number[]; st: number[]; en: number[] }

function group(o: number[], h: number[], l: number[], c: number[], lt: number[], key: number[]): Bars {
  const B: Bars = { o: [], h: [], l: [], c: [], hl: [], day: [], st: [], en: [] };
  for (let i = 0; i < key.length; i++) {
    if (i === 0 || key[i] !== key[i - 1]) {
      if (i > 0) B.en.push(i - 1);
      B.st.push(i); B.o.push(o[i]); B.h.push(h[i]); B.l.push(l[i]); B.c.push(c[i]);
      B.hl.push(Math.floor((((lt[i] % 86400) + 86400) % 86400) / 3600)); B.day.push(Math.floor(lt[i] / 86400));
    } else {
      const k = B.c.length - 1;
      B.h[k] = Math.max(B.h[k], h[i]); B.l[k] = Math.min(B.l[k], l[i]); B.c[k] = c[i];
    }
  }
  if (key.length) B.en.push(key.length - 1);
  return B;
}

/** pandas ewm(alpha=1/n, adjust=False, min_periods=n) na TR (prvni TR = h-l). */
export function wilderAtr(h: number[], l: number[], c: number[], n = 14): number[] {
  const out: number[] = [];
  let y = NaN;
  for (let i = 0; i < c.length; i++) {
    const pc = i === 0 ? c[0] : c[i - 1];
    const tr = Math.max(h[i] - l[i], Math.abs(h[i] - pc), Math.abs(l[i] - pc));
    y = i === 0 ? tr : (1 - 1 / n) * y + tr / n;
    out.push(i >= n - 1 ? y : NaN);
  }
  return out;
}

export function pivots(h: number[], l: number[], N: number) {
  const n = h.length, ph = new Array<boolean>(n).fill(false), pl = new Array<boolean>(n).fill(false);
  for (let i = N; i < n - N; i++) {
    let okh = true, okl = true;
    for (let j = i - N; j <= i + N; j++) {
      if (j === i) continue;
      if (h[j] > h[i] || (j < i && h[j] === h[i])) okh = false;
      if (l[j] < l[i] || (j < i && l[j] === l[i])) okl = false;
    }
    ph[i] = okh; pl[i] = okl;
  }
  return { ph, pl };
}

/** Posledni potvrzeny swing high/low (potvrzeni N svicek po pivotu) a trend (2 vyssi high + 2 vyssi low = 1). */
export function lastSwing(h: number[], l: number[], N: number) {
  const { ph, pl } = pivots(h, l, N);
  const n = h.length, sh: number[] = [], sl: number[] = [], tr: number[] = [];
  const hs: number[] = [], ls: number[] = [];
  let ch = NaN, cl = NaN;
  for (let i = 0; i < n; i++) {
    const p = i - N;
    if (p >= 0) {
      if (ph[p]) { ch = h[p]; hs.push(h[p]); }
      if (pl[p]) { cl = l[p]; ls.push(l[p]); }
    }
    sh.push(ch); sl.push(cl);
    let t = 0;
    if (hs.length >= 2 && ls.length >= 2) {
      const a = hs.length, b = ls.length;
      if (hs[a - 1] > hs[a - 2] && ls[b - 1] > ls[b - 2]) t = 1;
      else if (hs[a - 1] < hs[a - 2] && ls[b - 1] < ls[b - 2]) t = -1;
    }
    tr.push(t);
  }
  return { sh, sl, tr };
}

interface Zone { d: number; prox: number; dist: number; act: number }

/** S/D zony po FM (research_f8.find_zones, k_out = 2): baze 1-6 malych svicek, pohyb ven, BOS do 5 svicek. */
function findZones(B: Bars, a: number[], kOut = 2, bmax = 6, baseBody = 0.5): Zone[] {
  const { o, h, l, c } = B, n = c.length;
  const body = c.map((x, i) => x - o[i]);
  const { sh, sl } = lastSwing(h, l, 3);
  const Z: Zone[] = [];
  const skip: Record<number, number> = { 1: -1, [-1]: -1 };
  for (let j = 20; j < n - 1; j++) {
    const aj = a[j - 1];
    if (!(aj > 0)) continue;
    for (const d of [1, -1]) {
      if (j <= skip[d] || d * body[j] < 0.5 * aj) continue;
      let s = 0, m = 0;
      for (let k = j; k < Math.min(j + 3, n); k++) {
        if (d * body[k] <= 0) break;
        s += d * body[k]; m++;
        if (s >= kOut * aj) break;
      }
      if (s < kOut * aj) continue;
      let b0 = j;
      while (b0 - 1 >= 0 && j - (b0 - 1) <= bmax && Math.abs(body[b0 - 1]) <= baseBody * aj) b0--;
      if (b0 === j) continue;
      let prox: number, dist: number, lvl: number;
      if (d === 1) {
        prox = Math.max(...o.slice(b0, j), ...c.slice(b0, j)); dist = Math.min(...l.slice(b0, j + 1)); lvl = sh[b0];
      } else {
        prox = Math.min(...o.slice(b0, j), ...c.slice(b0, j)); dist = Math.max(...h.slice(b0, j + 1)); lvl = sl[b0];
      }
      const hgt = (prox - dist) * d;
      if (!Number.isFinite(lvl) || hgt <= 0 || hgt > 3 * aj) continue;
      let act = -1;
      for (let k = j; k < Math.min(j + 5, n); k++) if ((c[k] - lvl) * d > 0) { act = k; break; }
      if (act < 0) continue;
      act = Math.max(act, j + m - 1);
      Z.push({ d, prox, dist, act });
      skip[d] = j + m - 1;
    }
  }
  return Z;
}

/** Signal na posledni H4 svicce (jen kdyz posledni H1 svicka uzavira H4 blok). c = uzavrene H1 svicky. */
export function fmSignal(system: FmSystem, c: Candle[]): FmSignal | null {
  if (c.length < 300) return null;
  const lt = c.map((x) => ltOf(x.time));
  const last = lt[lt.length - 1];
  if (Math.floor((((last % 14400) + 14400) % 14400) / 3600) !== 3) return null; // posledni hodina H4 bloku
  const o1 = c.map((x) => x.open), h1 = c.map((x) => x.high), l1 = c.map((x) => x.low), c1 = c.map((x) => x.close);
  const B = group(o1, h1, l1, c1, lt, lt.map((x) => Math.floor(x / 14400)));
  const { o, h, l } = B, cl = B.c, n = cl.length, i = n - 1;
  const a = wilderAtr(h, l, cl, 14);
  if (!(a[i] > 0)) return null;
  // den (17:00 NY) z H4 svicek
  const D = group(o, h, l, cl, B.st.map((s) => lt[s]), B.day);
  const di: number[] = [];
  for (let k = 0, d = -1; k < n; k++) { if (k === 0 || B.day[k] !== B.day[k - 1]) d++; di.push(d); }
  const today = di[i];
  const trD = lastSwing(D.h, D.l, 2).tr;
  const trendD1 = today >= 1 ? trD[today - 1] : 0;
  const trendH4 = lastSwing(h, l, 2).tr[i];
  const biasM = today >= 1 && D.c[today - 1] !== D.o[today - 1] ? Math.sign(D.c[today - 1] - D.o[today - 1]) : 0;

  let sig: { d: number; sl: number; why: string } | null = null;

  if (system === "fm_mss_h4") {
    // sweepy PDH/PDL a Asie (stejne jako numba trig_sweeps), pak MSS do 12 svicek
    const sw: { s: number; d: number }[] = [];
    let asH = -Infinity, asL = Infinity, swPDl = false, swPDh = false, swAl = false, swAh = false;
    let lowday = Infinity, highday = -Infinity, lowpost = Infinity, highpost = -Infinity;
    for (let k = 1; k < n; k++) {
      if (B.day[k] !== B.day[k - 1]) {
        asH = -Infinity; asL = Infinity; swPDl = swPDh = swAl = swAh = false;
        lowday = Infinity; highday = -Infinity; lowpost = Infinity; highpost = -Infinity;
      }
      const hl = B.hl[k];
      if (hl >= 3 && hl < 9) { asH = Math.max(asH, h[k]); asL = Math.min(asL, l[k]); }
      if (di[k] >= 1) {
        const pdh = D.h[di[k] - 1], pdl = D.l[di[k] - 1];
        if (!swPDl && l[k] < pdl) { swPDl = true; if (cl[k] > pdl) sw.push({ s: k, d: 1 }); }
        if (!swPDh && h[k] > pdh) { swPDh = true; if (cl[k] < pdh) sw.push({ s: k, d: -1 }); }
      }
      lowday = Math.min(lowday, l[k]); highday = Math.max(highday, h[k]);
      if (hl >= 9 && hl < 19 && Number.isFinite(asL) && asH > -Infinity) {
        lowpost = Math.min(lowpost, l[k]); highpost = Math.max(highpost, h[k]);
        if (!swAl && l[k] < asL) { swAl = true; if (cl[k] > asL) sw.push({ s: k, d: 1 }); }
        if (!swAh && h[k] > asH) { swAh = true; if (cl[k] < asH) sw.push({ s: k, d: -1 }); }
      }
    }
    for (const { s, d } of sw) {
      if (s < 7 || s >= i || s < i - 12) continue;
      const lvl = d === 1 ? Math.max(...h.slice(s - 6, s + 1)) : Math.min(...l.slice(s - 6, s + 1));
      let ext = d === 1 ? l[s] : h[s], hit = -1;
      for (let k = s + 1; k < Math.min(s + 13, n); k++) {
        ext = d === 1 ? Math.min(ext, l[k]) : Math.max(ext, h[k]);
        if ((cl[k] - lvl) * d > 0) { hit = k; break; }
      }
      if (hit === i) {
        sig = { d, sl: ext - d * 0.1 * a[i], why: `Sweep likvidity (PDH/PDL nebo Asie) a pak změna struktury: H4 zavřela za ${lvl}` };
        break;
      }
    }
    if (sig && !(trendD1 === sig.d && trendH4 === sig.d)) sig = null;
  }

  if (system === "fm_pruraz_h4") {
    const { sh, sl } = lastSwing(h, l, 3);
    if (Number.isFinite(sh[i]) && cl[i] > sh[i] && cl[i - 1] <= sh[i] && Number.isFinite(sl[i])) {
      sig = { d: 1, sl: sl[i] - 0.1 * a[i], why: `H4 zavřela nad posledním pivot high (${sh[i]})` };
    } else if (Number.isFinite(sl[i]) && cl[i] < sl[i] && cl[i - 1] >= sl[i] && Number.isFinite(sh[i])) {
      sig = { d: -1, sl: sh[i] + 0.1 * a[i], why: `H4 zavřela pod posledním pivot low (${sl[i]})` };
    }
    if (sig && !(trendH4 === sig.d && biasM === sig.d)) sig = null;
  }

  if (system === "fm_zona_h4") {
    for (const z of findZones(B, a)) {
      const i0 = z.act + 1;
      if (i0 > i) continue;
      let t0 = -1, dead = false;
      for (let k = i0; k <= i; k++) {
        if (t0 < 0 && (z.d === 1 ? l[k] <= z.prox : h[k] >= z.prox)) t0 = k;
        if (k < i && (cl[k] - z.dist) * z.d < 0) { dead = true; break; }
      }
      if (dead || t0 < 0 || i > t0 + 6) continue;
      let first = -1;
      for (let k = t0; k <= i; k++) if ((cl[k] - z.prox) * z.d > 0) { first = k; break; }
      if (first === i) {
        sig = { d: z.d, sl: z.dist - z.d * 0.1 * a[i], why: `Návrat do H4 ${z.d === 1 ? "demand" : "supply"} zóny (${z.dist}–${z.prox}) a potvrzovací svíčka zpět za proximal` };
        break;
      }
    }
    if (sig && !(trendD1 === sig.d && trendH4 === sig.d)) sig = null;
  }

  if (!sig) return null;
  const risk = Math.abs(cl[i] - sig.sl);
  if (risk < 0.2 * a[i] || risk > 4 * a[i]) return null;
  const tr = (x: number) => (x === 1 ? "nahoru" : x === -1 ? "dolů" : "bez trendu");
  return {
    dir: sig.d === 1 ? "long" : "short", sl: sig.sl,
    reason: `${sig.why}; trend D1 ${tr(trendD1)}, H4 ${tr(trendH4)}${system === "fm_pruraz_h4" ? `, včerejší svíčka ${tr(biasM)}` : ""}.`,
  };
}
