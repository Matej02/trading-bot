// Experiment F15 - Hvezda (research_f15_hve.py, vybrana varianta: den, base max 3, H4 zona v D1 zone, level nad levelem,
// limit na proximal, bez COT). H4 a D1 svicky z 1h (bloky od 17:00 NY). Zony = research_f8.find_zones (pohyb ven >= 1,5 ATR,
// base 1-3 malych svicek, proximal = tela base, distal = knot, aktivace po BOS). Zivy limit = signal na 1h svicce, ktera
// proximal poprve zasahne. SL pod distal 2. zony (level nad levelem), TP nejblizsi protejsi D1 zona (2-6 R).
import { lastSwing, wilderAtr } from "./fm";
import { groupBy, type Tb } from "./fm12";
import type { Candle } from "./types";

export interface Fm15Signal { dir: "long" | "short"; sl: number; tp: number; reason: string }
interface Z { d: number; prox: number; dist: number; act: number; inv: number; tr: number; atr: number }

const K_OUT = 1.5, BMAX = 3, BASE = 0.5;

/** research_f8.find_zones vcetne zneplatneni (prvni close za distal), trendu pri aktivaci a ATR. */
function findZones(T: Tb): Z[] {
  const { o, h, l, c, a } = T, n = c.length;
  const body = c.map((x, i) => x - o[i]);
  const { sh, sl, tr } = lastSwing(h, l, 3);
  const out: Z[] = [];
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
        if (s >= K_OUT * aj) break;
      }
      if (s < K_OUT * aj) continue;
      let b0 = j;
      while (b0 - 1 >= 0 && j - (b0 - 1) <= BMAX && Math.abs(body[b0 - 1]) <= BASE * aj) b0--;
      if (b0 === j) continue;
      let prox: number, dist: number, lvl: number;
      if (d === 1) { prox = Math.max(...o.slice(b0, j), ...c.slice(b0, j)); dist = Math.min(...l.slice(b0, j + 1)); lvl = sh[b0]; }
      else { prox = Math.min(...o.slice(b0, j), ...c.slice(b0, j)); dist = Math.max(...h.slice(b0, j + 1)); lvl = sl[b0]; }
      const hgt = (prox - dist) * d;
      if (!Number.isFinite(lvl) || hgt <= 0 || hgt > 3 * aj) continue;
      let act = -1;
      for (let k = j; k < Math.min(j + 5, n); k++) if ((c[k] - lvl) * d > 0) { act = k; break; }
      if (act < 0) continue;
      act = Math.max(act, j + m - 1);
      let inv = n;
      for (let k = act + 1; k < n; k++) if ((c[k] - dist) * d < 0) { inv = k; break; }
      out.push({ d, prox, dist, act, inv, tr: tr[act], atr: aj });
      skip[d] = j + m - 1;
    }
  }
  return out;
}

/** Konec svicky TF (cas) a cas zneplatneni zony (konec svicky inv, nebo nekonecno). */
const actEnd = (T: Tb, z: Z) => T.t[z.act] + T.sec;
const invEnd = (T: Tb, z: Z) => (z.inv < T.t.length ? T.t[z.inv] + T.sec : Infinity);

export function fm15Signal(c1h: Candle[]): Fm15Signal | null {
  if (c1h.length < 24 * 120) return null;
  const L = c1h.length - 1, now = c1h[L];
  const H4all = groupBy(c1h, 4 * 3600), Dall = groupBy(c1h, 86400);
  // zony jen z uzavrenych svicek: posledni (rozpracovany) H4 blok a den se vynechaji, pokud jeste nekonci touto hodinou
  const cut = (T: Tb): Tb => {
    const k = T.t.length - 1;
    const closed = now.time + 3600 >= T.t[k] + T.sec;
    if (closed) return T;
    const s = (x: number[]) => x.slice(0, k);
    return { t: s(T.t), o: s(T.o), h: s(T.h), l: s(T.l), c: s(T.c), a: s(T.a), sec: T.sec };
  };
  const H4 = cut(H4all), D1 = cut(Dall);
  H4.a = wilderAtr(H4.h, H4.l, H4.c, 14); D1.a = wilderAtr(D1.h, D1.l, D1.c, 14);
  // aktualni H4 blok (do ktereho patri tato hodina) a jeho hodiny
  const kNow = H4all.t.length - 1, t4 = H4all.t[kNow];
  const ZL = findZones(H4), ZH = findZones(D1);
  for (const zl of ZL) {
    const d = zl.d, a0 = actEnd(H4, zl);
    if (a0 > t4) continue;
    // H4 zona uvnitr aktivni D1 zony ve smeru trendu D1 ("denni level v tydennim" o patro niz)
    const [lo1, hi1] = [Math.min(zl.prox, zl.dist), Math.max(zl.prox, zl.dist)];
    const inHi = ZH.some((zh) => zh.d === d && zh.tr === d && actEnd(D1, zh) <= a0 && a0 < invEnd(D1, zh) &&
      lo1 <= Math.max(zh.prox, zh.dist) && hi1 >= Math.min(zh.prox, zh.dist));
    if (!inHi) continue;
    if (invEnd(H4, zl) <= t4) continue;
    // prvni dotek: zadny drivejsi H4 blok po aktivaci (nejdyl 120) se proximal nedotkl, tento blok ano
    let earlier = false, cnt = 0;
    for (let k = 0; k < H4.t.length; k++) {
      if (H4.t[k] < a0) continue;
      cnt++;
      if (d === 1 ? H4.l[k] <= zl.prox : H4.h[k] >= zl.prox) { earlier = true; break; }
    }
    if (earlier || cnt >= 120) continue;
    // v tomto H4 bloku: tato hodina je prvni, ktera proximal zasahne
    let firstHere = -1;
    for (let r = L; r >= 0 && c1h[r].time >= t4; r--) if (d === 1 ? c1h[r].low <= zl.prox : c1h[r].high >= zl.prox) firstHere = r;
    if (firstHere !== L) continue;
    // level nad levelem: 2. zona stejneho smeru za distal do 2 ATR, aktivni pri doteku
    const z2s = ZL.filter((y) => y !== zl && y.d === d && actEnd(H4, y) <= t4 && t4 < invEnd(H4, y) &&
      (zl.dist - y.prox) * d >= 0 && (zl.dist - y.prox) * d <= 2 * zl.atr);
    if (!z2s.length) continue;
    const z2 = z2s.reduce((p, y) => (Math.abs(zl.dist - y.prox) < Math.abs(zl.dist - p.prox) ? y : p));
    const sl = z2.dist - d * 0.05 * zl.atr;
    const E = zl.prox;
    const risk = (E - sl) * d;
    if (risk <= 0) continue;
    const opp = ZH.filter((y) => y.d === -d && actEnd(D1, y) <= t4 && t4 < invEnd(D1, y) && (y.prox - zl.prox) * d > 0);
    if (!opp.length) continue;
    const yb = opp.reduce((p, y) => (Math.abs(y.prox - zl.prox) < Math.abs(p.prox - zl.prox) ? y : p));
    const rt = (yb.prox - E) * d / risk;
    if (rt < 2) continue;
    const R = Math.min(rt, 6);
    const f = (v: number) => v.toPrecision(6);
    return {
      dir: d === 1 ? "long" : "short", sl, tp: E + d * R * risk,
      reason: `${d === 1 ? "Demand" : "Supply"} H4 ${f(Math.min(zl.prox, zl.dist))}–${f(Math.max(zl.prox, zl.dist))} uvnitř D1 zóny ve směru trendu D1, ` +
        `první dotek proximal; level nad levelem → SL za 2. zónou (${f(sl)}), TP protější D1 zóna (${R.toFixed(1)} R).`,
    };
  }
  return null;
}
