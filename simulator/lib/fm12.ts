// Experiment F12 - Mucka podle doplnujicich pravidel uzivatele (research_f12.py + research_f12_ms.py, prevedeno 1:1).
// 4H a denni svicky se skladaji z 1h (bloky od 17:00 NY), zony a balancni levely z 4H a 15m, vstup na 1m:
// sweep likvidity v POI -> zmena struktury (MSS) na 1m -> navrat na 0,618 nohy (zivy limit = signal na 1m svicce,
// ktera uroven zasahne) -> SL na sweepu, TP 2,5 R (rrr systemu). Killzones 9-11 a 13:30-17 prazskeho casu.
import { ltOf, wilderAtr } from "./fm";
import type { Candle } from "./types";

export interface Fm12Signal { dir: "long" | "short"; sl: number; reason: string }
export interface Fm12Input { c1: Candle[]; c15: Candle[]; c1h: Candle[]; pip: number; fx: boolean }

const K = 1.5, EPS = 0.1, FIB = 0.35;
const DAY = 86400;

export interface Tb { t: number[]; o: number[]; h: number[]; l: number[]; c: number[]; a: number[]; sec: number }
export interface Ev { i: number; d: number; flip: boolean; lvl: number; orig: number; brk: number; st: number; sti: number }
export interface Ms { tr: number[]; bosI: number[]; ev: Ev[] }

export function bars(c: Candle[], sec: number): Tb {
  const o = c.map((x) => x.open), h = c.map((x) => x.high), l = c.map((x) => x.low), cl = c.map((x) => x.close);
  return { t: c.map((x) => x.time), o, h, l, c: cl, a: wilderAtr(h, l, cl, 14), sec };
}

// posun casoveho pasma se meni jen pri zmene casu (DST) - staci ho spocitat jednou za hodinu (Intl je pomale)
const ltOff = new Map<number, number>();
export function lt(t: number): number {
  const hk = Math.floor(t / 3600);
  let off = ltOff.get(hk);
  if (off === undefined) {
    if (ltOff.size > 50_000) ltOff.clear();
    off = ltOf(hk * 3600) - hk * 3600;
    ltOff.set(hk, off);
  }
  return t + off;
}

/** Slozi svicky podle klice (lt // blok) - 4H a den od 17:00 NY jako v Pythonu (agg). */
export function groupBy(c: Candle[], block: number): Tb {
  const out: Candle[] = [];
  let key = NaN;
  for (const x of c) {
    const k = Math.floor(lt(x.time) / block);
    if (k !== key) {
      out.push({ ...x });
      key = k;
    } else {
      const y = out[out.length - 1];
      y.high = Math.max(y.high, x.high); y.low = Math.min(y.low, x.low); y.close = x.close;
    }
  }
  return bars(out, block);
}

/** Stroj market structure (research_f12_ms.ms_machine). Objem z Yahoo u forexu chybi -> podminka objemu vzdy projde. */
export function ms(T: Tb): Ms {
  const { o, h, l, c, a } = T;
  const n = c.length;
  const tr = new Array<number>(n).fill(0), bosI = new Array<number>(n).fill(-1);
  const ev: Ev[] = [];
  const body = c.map((x, i) => Math.abs(x - o[i]));
  const bavg = new Array<number>(n).fill(NaN);
  let s = 0;
  for (let i = 0; i < n; i++) { s += body[i]; if (i >= 20) s -= body[i - 20]; if (i >= 19) bavg[i] = s / 20; }
  let t = 0, strong = NaN, strongI = -1, weak = NaN, ext = NaN, extI = -1, bosIdx = -1;
  let cd = 0, cflip = false, clvl = NaN, corig = -1, cbrk = -1;
  let zdir = 0, zext = c[0], zexti = 0;
  const zl: [number, number][] = [], zh: [number, number][] = [];
  for (let i = 21; i < n; i++) {
    const ai = a[i];
    if (!(ai > 0)) continue;
    // ZigZag na zaviracich cenach
    if (zdir >= 0) {
      if (c[i] > zext) { zext = c[i]; zexti = i; }
      if (c[i] < zext - K * ai) {
        let hv = -Infinity;
        for (let q = Math.max(zexti - 1, 0); q <= Math.min(zexti + 1, n - 1); q++) hv = Math.max(hv, h[q]);
        zh.push([hv, zexti]); zdir = -1; zext = c[i]; zexti = i;
      }
    }
    if (zdir === -1) {
      if (c[i] < zext) { zext = c[i]; zexti = i; }
      if (c[i] > zext + K * ai) {
        let lv = Infinity;
        for (let q = Math.max(zexti - 1, 0); q <= Math.min(zexti + 1, n - 1); q++) lv = Math.min(lv, l[q]);
        zl.push([lv, zexti]); zdir = 1; zext = c[i]; zexti = i;
      }
    }
    // 1) potvrzeni kandidata
    if (cd !== 0 && cbrk === i - 1) {
      if ((c[i] - clvl) * cd > 0) {   // objem nad MA50 nebo stejna barva; bez objemu (forex z Yahoo) staci zavreni
        const lo = Math.min(corig, cbrk), hi = cbrk;
        let sv = cd === 1 ? l[lo] : h[lo], si = lo;
        for (let q = lo; q <= hi; q++) {
          if (cd === 1 ? l[q] < sv : h[q] > sv) { sv = cd === 1 ? l[q] : h[q]; si = q; }
        }
        let e = cd === 1 ? h[cbrk] : l[cbrk], ei = cbrk;
        if (cd === 1 ? h[i] > e : l[i] < e) { e = cd === 1 ? h[i] : l[i]; ei = i; }
        t = cd; strong = sv; strongI = si; weak = NaN; ext = e; extI = ei; bosIdx = i;
        ev.push({ i, d: cd, flip: cflip, lvl: clvl, orig: corig, brk: cbrk, st: sv, sti: si });
      }
      cd = 0;
    } else if (cd !== 0) cd = 0;
    // 2) extrem a weak level (kotva Fibo = strong nebo posledni swing ZigZagu pred extremem)
    if (t !== 0 && isNaN(weak) && bosIdx !== i) {
      if (t === 1 ? h[i] > ext : l[i] < ext) { ext = t === 1 ? h[i] : l[i]; extI = i; }
      let anc = strong;
      const zz = t === 1 ? zl : zh;
      for (let q = zz.length - 1; q >= Math.max(zz.length - 30, 0); q--) {
        if (zz[q][1] < extI) {
          if (zz[q][1] > strongI && (t === 1 ? zz[q][0] > anc : zz[q][0] < anc)) anc = zz[q][0];
          break;
        }
      }
      const leg = (ext - anc) * t;
      if (leg >= K * ai && (t === 1 ? l[i] <= ext - FIB * leg : h[i] >= ext + FIB * leg)) weak = ext;
    }
    // 3) novy kandidat
    const bd = c[i] - o[i];
    const mom = Math.abs(bd) >= bavg[i] && Math.abs(bd) <= 3 * ai;
    if (t === 0) {
      let hh = h[i - 20], hiI = i - 20, ll = l[i - 20], loI = i - 20;
      for (let q = i - 20; q < i; q++) { if (h[q] > hh) { hh = h[q]; hiI = q; } if (l[q] < ll) { ll = l[q]; loI = q; } }
      if (mom && bd > 0 && c[i] > hh + EPS * ai) [cd, cflip, clvl, corig, cbrk] = [1, true, hh, hiI, i];
      else if (mom && bd < 0 && c[i] < ll - EPS * ai) [cd, cflip, clvl, corig, cbrk] = [-1, true, ll, loI, i];
    } else {
      if (mom && bd * t < 0 && (c[i] - strong) * t < -EPS * ai) [cd, cflip, clvl, corig, cbrk] = [-t, true, strong, strongI, i];
      else if (!isNaN(weak) && mom && bd * t > 0 && (c[i] - weak) * t > EPS * ai) [cd, cflip, clvl, corig, cbrk] = [t, false, weak, extI, i];
    }
    tr[i] = t; bosI[i] = bosIdx;
  }
  return { tr, bosI, ev };
}

/** Index posledni svicky TF, ktera je uz zavrena v case t (konec svicky <= t). */
export function closedIdx(T: Tb, t: number): number {
  let lo = 0, hi = T.t.length - 1, r = -1;
  while (lo <= hi) { const m = (lo + hi) >> 1; if (T.t[m] + T.sec <= t) { r = m; lo = m + 1; } else hi = m - 1; }
  return r;
}

interface Zone { d: number; bot: number; top: number; a0: number; end: number }
interface Bal { d: number; lvl: number; a0: number; end: number }

/** Zona u strong levelu kazdeho BOS (base z malych svicek, max 6, hranice pres tela), plati do stari / 25 % / prurazu. */
function zones(T: Tb, S: Ms, T15: Tb, age: number): Zone[] {
  const out: Zone[] = [];
  const body = T.c.map((x, i) => Math.abs(x - T.o[i]));
  for (const e of S.ev) {
    const si = e.sti;
    if (si < 1 || !(T.a[si] > 0)) continue;
    const small = (q: number) => body[q] <= 0.6 * T.a[q];
    let s = si, f = si;
    while (f + 1 < e.brk && small(f + 1) && f - s + 1 < 6) f++;
    while (s - 1 >= 0 && small(s - 1) && f - s + 1 < 6) s--;
    let top = -Infinity, bot = Infinity;
    for (let q = s; q <= f; q++) { top = Math.max(top, T.o[q], T.c[q]); bot = Math.min(bot, T.o[q], T.c[q]); }
    if (top - bot < 0.1 * T.a[si]) {
      if (e.d === 1) for (let q = s; q <= f; q++) bot = Math.min(bot, T.l[q]);
      else for (let q = s; q <= f; q++) top = Math.max(top, T.h[q]);
    }
    const a0 = T.t[e.i] + T.sec, hz = top - bot;
    let end = a0 + age * DAY, deep = false;
    for (let q = 0; q < T15.t.length; q++) {
      if (T15.t[q] < a0) continue;
      if (T15.t[q] >= a0 + age * DAY) break;
      if (e.d === 1) {
        if (T15.c[q] < bot) { end = T15.t[q] + T15.sec; break; }
        if (T15.l[q] < top - 0.25 * hz) deep = true;
        else if (deep && T15.l[q] > top) { end = T15.t[q]; break; }
      } else {
        if (T15.c[q] > top) { end = T15.t[q] + T15.sec; break; }
        if (T15.h[q] > bot + 0.25 * hz) deep = true;
        else if (deep && T15.h[q] < bot) { end = T15.t[q]; break; }
      }
    }
    out.push({ d: e.d, bot, top, a0, end });
  }
  return out;
}

/** Balancni level = protazeny BOS, plati jen prvni navrat (nejdyl 1 den). */
function balances(T: Tb, S: Ms, T15: Tb, age: number): Bal[] {
  const out: Bal[] = [];
  for (const e of S.ev) {
    const a0 = T.t[e.i] + T.sec;
    let f = -1;
    for (let q = 0; q < T15.t.length; q++) {
      if (T15.t[q] < a0) continue;
      if (T15.t[q] >= a0 + age * DAY) break;
      const a15 = T15.a[q];
      if (e.d === 1 ? T15.l[q] <= e.lvl + 0.1 * a15 : T15.h[q] >= e.lvl - 0.1 * a15) { f = q; break; }
    }
    if (f < 0) continue;
    let g = Math.min(f + 96, T15.t.length - 1);
    for (let q = f + 1; q < Math.min(f + 96, T15.t.length); q++) {
      const a15 = T15.a[q];
      if (e.d === 1 ? T15.l[q] > e.lvl + 0.5 * a15 : T15.h[q] < e.lvl - 0.5 * a15) { g = q; break; }
    }
    out.push({ d: e.d, lvl: e.lvl, a0: T15.t[f], end: T15.t[g] + T15.sec });
  }
  return out;
}

const czFmt = new Intl.DateTimeFormat("en-US", { timeZone: "Europe/Prague", hourCycle: "h23", hour: "numeric", minute: "numeric" });
const czOff = new Map<number, number>();
/** Prazsky cas jako hodina dne (9,5 = 9:30); posun pasma se pamatuje po hodinach. */
export function czHour(t: number): number {
  const hk = Math.floor(t / 3600);
  let off = czOff.get(hk);
  if (off === undefined) {
    if (czOff.size > 50_000) czOff.clear();
    const p: Record<string, string> = {};
    for (const x of czFmt.formatToParts(new Date(hk * 3600 * 1000))) p[x.type] = x.value;
    off = (((+p.hour % 24) - Math.floor(((hk % 24) + 24) % 24)) + 24) % 24;
    czOff.set(hk, off);
  }
  const s = (((t % 86400) + 86400) % 86400) / 3600 + off;
  return s % 24;
}
const KZ: [number, number][] = [[9, 11], [13.5, 17]];

/** Signal na posledni uzavrene 1m svicce, pokud prave zasahla 0,618 po MSS splnujicim vsechna pravidla. */
export function fm12Signal(x: Fm12Input): Fm12Signal | null {
  if (x.c1.length < 500 || x.c15.length < 300 || x.c1h.length < 24 * 40) return null;
  const T1 = bars(x.c1, 60), T15 = bars(x.c15, 900), H4 = groupBy(x.c1h, 4 * 3600), D = groupBy(x.c1h, DAY);
  const L = T1.t.length - 1;
  const tL = T1.t[L] + 60;
  const hL = czHour(T1.t[L]);
  const kz = KZ.find((w) => w[0] <= hL && hL < w[1]);
  if (!kz) return null;
  const S1 = ms(T1);
  let S4: Ms | null = null, S15: Ms | null = null, Z: Zone[] = [], B: Bal[] = [];
  // zmeny struktury na 1m v teze killzone, od nejnovejsi (kazda ma vlastni limit na 0,618)
  for (let qi = S1.ev.length - 1; qi >= 1; qi--) {
    const e = S1.ev[qi];
    const ic = e.i;
    if (T1.t[L] - T1.t[ic] > 3 * 3600) break;
    if (!e.flip || S1.ev[qi - 1].d !== -e.d || ic >= L) continue;
    const d = e.d, prev = S1.ev[qi - 1];
    if (!(prev.brk <= e.sti && e.sti <= prev.brk + 60)) continue;
    const hc = czHour(T1.t[ic]);
    if (!(kz[0] <= hc && hc < kz[1]) || czHour(T1.t[ic]) > hL) continue;
    const tic = T1.t[ic] + 60;
    // daily bias = barva vcerejsi svicky (den 17:00 NY)
    const kD = closedIdx(D, tic) + 1;   // den, do ktereho patri tic
    if (kD < 2 || kD > D.t.length) continue;
    const pd = kD - 1;
    if (D.c[pd] === D.o[pd] || (D.c[pd] > D.o[pd] ? 1 : -1) !== d) continue;
    // 4H struktura ve smeru a BOS do 30 dni
    if (!S4) {
      S4 = ms(H4); S15 = ms(T15);
      Z = [...zones(H4, S4, T15, 30), ...zones(T15, S15, T15, 5)];
      B = [...balances(H4, S4, T15, 30), ...balances(T15, S15, T15, 5)];
    }
    const k4 = closedIdx(H4, tic);
    if (k4 < 1 || S4.tr[k4] !== d) continue;
    const b4 = S4.bosI[k4];
    if (b4 < 0 || tic - (H4.t[b4] + H4.sec) > 30 * DAY) continue;
    // POI: zona nebo balancni level (4H 30 dni, 15m 5 dni)
    const sv = e.st, tsw = T1.t[e.sti] + 60;
    const a15 = T15.a[Math.max(0, closedIdx(T15, tsw))];
    const inZ = Z.some((z) => z.d === d && z.a0 <= tsw && tsw <= z.end &&
      (d === 1 ? sv <= z.top && sv >= z.bot - 0.5 * (z.top - z.bot) : sv >= z.bot && sv <= z.top + 0.5 * (z.top - z.bot)));
    const inB = B.some((b) => b.d === d && b.a0 <= tsw && tsw <= b.end &&
      (d === 1 ? sv <= b.lvl + 0.2 * a15 && sv >= b.lvl - 0.5 * a15 : sv >= b.lvl - 0.2 * a15 && sv <= b.lvl + 0.5 * a15));
    if (!inZ && !inB) continue;
    // navrat na 0,618 nohy od sweepu k maximu po MSS - signal jen na prvni svicce, ktera uroven zasahne
    let ext = d === 1 ? -Infinity : Infinity;
    for (let r = e.sti; r <= ic; r++) ext = d === 1 ? Math.max(ext, T1.h[r]) : Math.min(ext, T1.l[r]);
    let touch = -1, lvl = NaN;
    for (let r = ic + 1; r <= L; r++) {
      const hr = czHour(T1.t[r]);
      if (!(kz[0] <= hr && hr < kz[1])) break;
      lvl = ext - d * 0.618 * Math.abs(ext - sv);
      if (d === 1 ? T1.l[r] <= lvl : T1.h[r] >= lvl) { touch = r; break; }
      if (d === 1 ? T1.l[r] < sv : T1.h[r] > sv) break;
      ext = d === 1 ? Math.max(ext, T1.h[r]) : Math.min(ext, T1.l[r]);
    }
    if (touch !== L) continue;
    // SL na sweepu: min 6 pipu (forex) / 0,086 ATR D1, nad 15 pipu / 0,21 ATR D1 se neobchoduje
    const aD = wilderAtr(D.h, D.l, D.c, 14)[pd];
    if (!(aD > 0)) continue;
    const px = T1.c[L];
    const mn = x.fx ? 6 * x.pip : 0.086 * aD, mx = x.fx ? 15 * x.pip : 0.21 * aD;
    let sl = sv;
    let risk = (px - sl) * d;
    if (risk <= 0) continue;
    if (risk < mn) { sl = px - d * mn; risk = mn; }
    if (risk > mx) continue;
    const f = (v: number) => v.toPrecision(6);
    return {
      dir: d === 1 ? "long" : "short", sl,
      reason: `Sweep ${d === 1 ? "low" : "high"} ${f(sv)} v ${inZ ? "zóně (4H/15m, BOS)" : "balančním levelu"}, MSS na 1m v killzone, ` +
        `návrat na 0,618 (${f(lvl)}); daily bias a 4H struktura ve směru. SL na sweepu.`,
    };
  }
  return null;
}
