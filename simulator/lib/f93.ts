// F93 druhy den po vysledcich firem - jen sledovani dopredu (kandidat, neproslo jen na pesimistickych nakladech).
// Vault: Vyzkum/F92 a F93 Vysledky firem behem dne.md. Prevod 1:1 z scratch/f92_vysledky_den.py + f88_pead.py:
// - udalosti: 8-K s polozkou 2.02 z EDGAR, dalsi udalost stejne firmy do 20 dni od posledni ponechane se zahodi;
// - den reakce D: prijato do 16:00 NY -> ten den (nebo nejblizsi dalsi obchodni den), po 16:00 -> dalsi obchodni den;
// - z = nadvynos akcie nad S&P 500 za den D (zavreni -> zavreni) / smerodatna odchylka nadvynosu za 60 dni pred D;
// - |z| >= 2 -> vstup na otevreni D+1 ve smeru reakce, vystup na zavreni D+1, stop 1 ATR(20) z dne D
//   (zasah pres low/high = -1 R, pesimisticky); naklady na stranu pul spreadu 0,05 % + provize 0,004 % (pesimisticky 0,10 %).
// Ciste funkce bez site - stejne je pouziva server (lib/server/f93Runner.ts) i kontrola shody (scripts/f93-parity.ts).

export interface F93Day { d: string; o: number; h: number; l: number; c: number } // d = YYYY-MM-DD (den burzy)

export const F93_Z = 2.0;
export const F93_DEDUPE_DAYS = 20;
export const F93_COST = { norm: 0.0005, pess: 0.001, comm: 0.00004 };
export const F93_MAX_DAY = 3; // v meritku prop zkousky nejvys 3 obchody denne (prednost nejvyssi |z|)

// 40 americkych akcii FTMO z testu (CIK z SEC company_tickers.json, stejne jako ve vyzkumu)
export const F93_TICKERS: [string, number][] = [
  ["AAPL", 320193], ["AMD", 2488], ["AMZN", 1018724], ["AVGO", 1730168], ["BA", 12927], ["BAC", 70858], ["BRK-B", 1067983],
  ["CSCO", 858877], ["CVX", 93410], ["DIS", 1744489], ["FDX", 1048911], ["GE", 40545], ["GM", 1467858], ["GME", 1326380],
  ["GOOG", 1652044], ["IBM", 51143], ["INTC", 50863], ["JNJ", 200406], ["JPM", 19617], ["KO", 21344], ["LMT", 936468],
  ["MCD", 63908], ["META", 1326801], ["MSFT", 789019], ["MSTR", 1050446], ["NFLX", 1065280], ["NKE", 320187], ["NVDA", 1045810],
  ["PFE", 78003], ["PLTR", 1321655], ["QCOM", 804328], ["RTX", 101829], ["SBUX", 829224], ["SNOW", 1640147], ["T", 732717],
  ["TSLA", 1318605], ["V", 1403161], ["WMT", 104169], ["XOM", 2115436], ["ZM", 1585521],
];

const nyFmt = new Intl.DateTimeFormat("sv-SE", {
  timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit",
  hourCycle: "h23",
});

/** Cas v New Yorku jako "YYYY-MM-DD HH:MM:SS" (jako tz_convert + tz_localize(None) v pandas). */
export function nyWall(isoUtc: string | number): string {
  return nyFmt.format(new Date(isoUtc));
}

const wallMs = (w: string) => Date.parse(w.replace(" ", "T") + "Z");

/** Vycisteni jako F85.clean: platne OHLC, kladne ceny, bez duplicit, jen po-pa. Vstup serazeny podle data. */
export function cleanDays(rows: F93Day[]): F93Day[] {
  const out: F93Day[] = [];
  const seen = new Set<string>();
  for (const r of rows) {
    const ok = r.h >= r.l && r.l <= r.c && r.c <= r.h && r.l <= r.o && r.o <= r.h && r.c > 0 && r.l > 0 &&
      [r.o, r.h, r.l, r.c].every(Number.isFinite);
    if (!ok || seen.has(r.d)) continue;
    const wd = new Date(r.d + "T00:00:00Z").getUTCDay();
    if (wd === 0 || wd === 6) continue;
    seen.add(r.d);
    out.push(r);
  }
  return out;
}

/** Udalosti jedne firmy: casy prijeti (UTC ISO) -> ponechane casy v NY (vzestupne), jako F88.events(). */
export function dedupeEvents(acceptIso: string[]): string[] {
  const w = acceptIso.map(nyWall).sort();
  const keep: string[] = [];
  let last: number | null = null;
  for (const x of w) {
    const t = wallMs(x);
    if (last != null && Math.floor((t - last) / 86_400_000) <= F93_DEDUPE_DAYS) continue;
    keep.push(x);
    last = t;
  }
  return keep;
}

/** Index dne reakce D (jako F88.reaction_day): po 16:00 NY prvni den po datu, jinak prvni den od data. */
export function reactionDay(days: F93Day[], etWall: string): number {
  const d0 = etWall.slice(0, 10);
  const mins = Number(etWall.slice(11, 13)) * 60 + Number(etWall.slice(14, 16));
  const after = mins >= 16 * 60;
  let i = 0;
  while (i < days.length && (after ? days[i].d <= d0 : days[i].d < d0)) i++;
  return i;
}

/** ATR(20) jako prumer true range za 20 dni vcetne dne i (prvni den bez predchoziho zavreni = chybi). */
export function atr20(days: F93Day[], i: number): number {
  if (i < 20) return NaN;
  let s = 0;
  for (let j = i - 19; j <= i; j++) {
    const pc = days[j - 1].c;
    s += Math.max(days[j].h - days[j].l, Math.abs(days[j].h - pc), Math.abs(days[j].l - pc));
  }
  return s / 20;
}

/** Denni vynosy S&P 500 podle data (pct_change na vlastni rade indexu). */
export function indexReturns(spx: { d: string; c: number }[]): Map<string, number> {
  const m = new Map<string, number>();
  for (let i = 1; i < spx.length; i++) m.set(spx[i].d, spx[i].c / spx[i - 1].c - 1);
  return m;
}

function nanStd(xs: number[]): number {
  const v = xs.filter(Number.isFinite);
  if (v.length < 2) return NaN;
  const mean = v.reduce((a, b) => a + b, 0) / v.length;
  return Math.sqrt(v.reduce((a, b) => a + (b - mean) ** 2, 0) / (v.length - 1));
}

export interface F93Signal {
  ticker: string;
  event: string; // cas prijeti v NY
  dayD: string; // den reakce
  z: number;
  dir: 1 | -1;
  atr: number; // 1 ATR(20) z dne D = riziko na akcii (jednotka R)
  close: number; // zavreni dne D
}

/** Signal pro udalost, pokud je den D uz v datech (uzavreny). Vraci null, kdyz |z| < 2 nebo chybi data. */
export function f93SignalFor(ticker: string, days: F93Day[], ixr: Map<string, number>, etWall: string): F93Signal | null {
  const D = reactionDay(days, etWall);
  if (D < 62 || D >= days.length) return null;
  const exc = (j: number) => {
    const r = days[j].c / days[j - 1].c - 1;
    const x = ixr.get(days[j].d);
    return x == null ? NaN : r - x;
  };
  const hist: number[] = [];
  for (let j = D - 60; j < D; j++) hist.push(exc(j));
  const sd = nanStd(hist);
  const z = exc(D) / sd;
  if (!(sd > 0) || !Number.isFinite(z) || Math.abs(z) < F93_Z) return null;
  const atr = atr20(days, D);
  if (!(atr > 0) || !Number.isFinite(atr)) return null;
  return { ticker, event: etWall, dayD: days[D].d, z, dir: z > 0 ? 1 : -1, atr, close: days[D].c };
}

export interface F93Result { entry: number; exit: number; stopHit: boolean; rGross: number; rNorm: number; rPess: number }

/** Vysledek obchodu otevreni -> zavreni dne k se stopem 1 ATR (jednotka R = 1 ATR z dne D). */
export function f93Settle(day: F93Day, dir: 1 | -1, atr: number): F93Result | null {
  const E = day.o;
  if (!(E > 0) || !(atr > 0)) return null;
  const worst = dir > 0 ? day.l - E : E - day.h;
  const stopHit = worst <= -atr;
  const X = stopHit ? E - dir * atr : day.c;
  const gross = dir * (X - E);
  const r = (half: number) => (gross - (half + F93_COST.comm) * (E + X)) / atr;
  return { entry: E, exit: X, stopHit, rGross: gross / atr, rNorm: r(F93_COST.norm), rPess: r(F93_COST.pess) };
}

/** Vsechny signaly jedne firmy z jejich udalosti (pro kontrolu shody s testem). */
export function f93AllSignals(ticker: string, days: F93Day[], ixr: Map<string, number>, acceptIso: string[]) {
  const out: (F93Signal & { dayK: string; res: F93Result })[] = [];
  for (const et of dedupeEvents(acceptIso)) {
    const s = f93SignalFor(ticker, days, ixr, et);
    if (!s) continue;
    const k = days.findIndex((x) => x.d === s.dayD) + 1;
    if (k <= 0 || k >= days.length) continue;
    const res = f93Settle(days[k], s.dir, s.atr);
    if (res) out.push({ ...s, dayK: days[k].d, res });
  }
  return out;
}
