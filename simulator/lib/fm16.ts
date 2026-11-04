// Experiment F16 - Hakimi (research_f16_hak.py, vybrana varianta: vlna 4, FVG v pasmu Fibo 0,618-0,75, vstup po potvrzeni,
// SL pod pasmem/0,75, TP high vlny = LOC likvidita). Trend H4 z 1h (bloky od 17:00 NY), vlny ZigZagem na zaviracich cenach 15m
// (otocka 2 ATR 15m). Signal na zavreni 15m svicky, ktera po doteku pasma poprve zavre zpet za 0,618 ve smeru. RR >= 2,5, den do 22:00 Praha.
import { lastSwing, wilderAtr } from "./fm";
import { bars, closedIdx, czHour, groupBy, type Tb } from "./fm12";
import type { Candle } from "./types";

export interface Fm16Signal { dir: "long" | "short"; sl: number; tp: number; reason: string }

const KZZ = 2;

function zigzag(c: number[], a: number[]): [number, number, number][] {
  const out: [number, number, number][] = [];
  let d = 0, ext = c[0], ei = 0;
  for (let i = 1; i < c.length; i++) {
    if (!(a[i] > 0)) continue;
    if (d >= 0) {
      if (c[i] > ext) { ext = c[i]; ei = i; }
      if (c[i] < ext - KZZ * a[i]) { out.push([ei, i, 1]); d = -1; ext = c[i]; ei = i; continue; }
    }
    if (d <= 0) {
      if (c[i] < ext) { ext = c[i]; ei = i; }
      if (c[i] > ext + KZZ * a[i]) { out.push([ei, i, -1]); d = 1; ext = c[i]; ei = i; }
    }
  }
  return out;
}

function wavePrice(X: Tb, i: number, typ: number): number {
  let v = typ === 1 ? -Infinity : Infinity;
  for (let r = Math.max(0, i - 1); r <= Math.min(X.h.length - 1, i + 1); r++) v = typ === 1 ? Math.max(v, X.h[r]) : Math.min(v, X.l[r]);
  return v;
}

const dayFmt = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Prague", year: "numeric", month: "2-digit", day: "2-digit" });

export function fm16Signal(c15: Candle[], c1h: Candle[]): Fm16Signal | null {
  if (c15.length < 300 || c1h.length < 24 * 30) return null;
  const X = bars(c15, 900), H4 = groupBy(c1h, 4 * 3600);
  const j = X.t.length - 1;
  const tr4 = lastSwing(H4.h, H4.l, 2).tr;
  const zz = zigzag(X.c, X.a);
  const dayJ = dayFmt.format(new Date(X.t[j] * 1000));
  if (czHour(X.t[j]) >= 22) return null;
  for (let q = zz.length - 1; q >= 5; q--) {
    const [iEnd, conf, typ] = zz[q];
    if (conf >= j) continue;
    const tConf = X.t[conf] + 900;                       // prvni minuta po potvrzeni swingu = i0
    if (dayFmt.format(new Date(tConf * 1000)) !== dayJ) break;
    const d = typ;
    const iSt = zz[q - 1][0];
    const pEnd = wavePrice(X, iEnd, typ), pSt = wavePrice(X, iSt, -typ), prevExt = wavePrice(X, zz[q - 2][0], typ);
    const k4 = closedIdx(H4, tConf);
    if (k4 < 2 || tr4[k4] !== d) continue;
    if ((pEnd - prevExt) * d <= 0) continue;
    const w1St = wavePrice(X, zz[q - 3][0], -typ), w1End = wavePrice(X, zz[q - 2][0], typ);
    if (Math.abs(pEnd - pSt) <= Math.abs(w1End - w1St)) continue;
    const leg = Math.abs(pEnd - pSt);
    const f618 = pEnd - d * 0.618 * leg, f75 = pEnd - d * 0.75 * leg;
    let top = d === 1 ? f618 : f75, bot = d === 1 ? f75 : f618;
    let fv: [number, number] | null = null;
    for (let r = Math.min(iSt, iEnd) + 2; r <= Math.max(iSt, iEnd); r++) {
      let g: [number, number] | null = null;
      if (d === 1 && X.l[r] > X.h[r - 2]) g = [X.h[r - 2], X.l[r]];
      else if (d === -1 && X.h[r] < X.l[r - 2]) g = [X.h[r], X.l[r - 2]];
      if (g && g[0] <= top && g[1] >= bot) fv = g;
    }
    if (!fv) continue;
    top = Math.min(top, fv[1]); bot = Math.max(bot, fv[0]);
    if (top <= bot) continue;
    const a15 = X.a[conf];
    const sl = d === 1 ? Math.min(bot, f75) - 0.1 * a15 : Math.max(top, f75) + 0.1 * a15;
    const tpx = pEnd;
    // den musi mit po potvrzeni aspon 30 min do 22:00
    if (czHour(tConf) >= 21.5) continue;
    // od svicky po potvrzeni: dotek pasma, pak prvni zavreni zpet za 0,618 se spravnou barvou = tato svicka j
    let touched = false, ck = -1;
    for (let k = conf + 1; k <= j; k++) {
      if (d === 1 ? X.l[k] <= sl : X.h[k] >= sl) break;
      if (d === 1 ? X.h[k] >= tpx : X.l[k] <= tpx) break;
      if (d === 1 ? X.l[k] <= top : X.h[k] >= bot) touched = true;
      if (touched && (X.c[k] - f618) * d > 0 && (X.c[k] - X.o[k]) * d > 0) { ck = k; break; }
    }
    if (ck !== j) continue;
    const E = X.c[j];
    const risk = (E - sl) * d;
    if (risk <= 0) continue;
    const rt = (tpx - E) * d / risk;
    if (rt < 2.5) continue;
    const R = Math.min(rt, 8);
    const f = (v: number) => v.toPrecision(6);
    return {
      dir: d === 1 ? "long" : "short", sl, tp: E + d * R * risk,
      reason: `Trend H4 ${d === 1 ? "nahoru" : "dolů"}, pullback vlny 4 do Fibo 0,618–0,75 s FVG (${f(bot)}–${f(top)}), ` +
        `15m svíčka zavřela zpět za 0,618. SL pod pásmem, TP high vlny 3 = likvidita (${R.toFixed(1)} R).`,
    };
  }
  return null;
}
