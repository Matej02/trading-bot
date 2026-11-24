// Systemy z fronty napadu F22-F33 (vyzkum 2026-11-07/08, vault: Vyzkum/Souhrn testu F21-F33 a prinosy):
//  F33 rebalancovani na konci mesice (proslo), F31 drift pred FOMC (kandidat), F29 krypto momentum (kandidat).
// Pravidla 1:1 podle planu zapsanych predem; odchylky od testu jsou popsane v definicich systemu (strategies.ts).
import { atr } from "./indicators";
import type { Candle, Dir } from "./types";
import { EXCHANGE_OF, euTradingDaysLeft, isEuTradingDay, type Exchange } from "./euCalendar";
import { isDayBeforeFomc, isFomcDay, nyParts, tradingDaysLeftInMonth } from "./usCalendar";

const DAY = 86400;

export interface F2xSignal { dir: Dir; sl: number; reason: string }

function atrLast(c: Candle[], n = 20): number | null {
  const a = atr(c.map((x) => x.high), c.map((x) => x.low), c.map((x) => x.close), n);
  const v = a[a.length - 1];
  return v != null && v > 0 ? v : null;
}

const pct = (x: number) => `${x >= 0 ? "+" : ""}${(x * 100).toFixed(2)} %`;

// ------------------------------------------------------------------ F33 rebalancovani na konci mesice

export const F33_THRESHOLD = 0.02;

/** Zavreni feedu v den t a posledni zavreni predchoziho mesice (denni svicky, cas = pulnoc UTC). */
function monthToDate(feed: Candle[], t: number): number | null {
  const d = new Date(t * 1000);
  const monthStart = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) / 1000;
  const today = feed.find((x) => x.time === t);
  const prev = [...feed].reverse().find((x) => x.time < monthStart);
  return today && prev ? today.close / prev.close - 1 : null;
}

/**
 * Signal na zavreni 4. obchodniho dne od konce mesice (L-3): vynos SPY - vynos TLT od konce minuleho mesice.
 * |rozdil| >= 2 p. b. -> obchod proti vitezi (akcie vedly -> short indexu, dluhopisy vedly -> long), SL 3 ATR20 (pojistka).
 */
export function f33Signal(c: Candle[], spy: Candle[], tlt: Candle[]): F2xSignal | null {
  const last = c[c.length - 1];
  if (!last || tradingDaysLeftInMonth(last.time) !== 3) return null;
  const rs = monthToDate(spy, last.time);
  const rb = monthToDate(tlt, last.time);
  if (rs == null || rb == null) return null;
  const diff = rs - rb;
  if (Math.abs(diff) < F33_THRESHOLD) return null;
  const a = atrLast(c);
  if (!a) return null;
  const dir: Dir = diff > 0 ? "short" : "long";
  return {
    dir, sl: dir === "long" ? last.close - 3 * a : last.close + 3 * a,
    reason: `F33: od začátku měsíce SPY ${pct(rs)}, TLT ${pct(rb)} (rozdíl ${pct(diff)}) – ` +
      `${dir === "short" ? "akcie vedou, fondy je na konci měsíce prodávají → short" : "dluhopisy vedou, fondy dokupují akcie → long"} ` +
      `do zavření posledního obchodního dne měsíce; SL 3 ATR jen jako pojistka.`,
  };
}

/** Vystup F33: na zavreni posledniho obchodniho dne mesice. */
export const f33Exit = (c: Candle[]) => c.length > 0 && tradingDaysLeftInMonth(c[c.length - 1].time) === 0;

// ------------------------------------------------------------------ F31 drift pred FOMC

/** Denni ATR20 z hodinovych svicek (dny podle NY data). */
function dailyAtrFrom1h(c: Candle[]): number | null {
  const days = new Map<string, { h: number; l: number; c: number }>();
  for (const x of c) {
    const k = nyParts(x.time).date;
    const d = days.get(k);
    if (!d) days.set(k, { h: x.high, l: x.low, c: x.close });
    else { d.h = Math.max(d.h, x.high); d.l = Math.min(d.l, x.low); d.c = x.close; }
  }
  const v = [...days.values()].slice(0, -1);   // posledni (rozpracovany) den ven
  if (v.length < 21) return null;
  const tr = v.slice(1).map((d, i) => Math.max(d.h - d.l, Math.abs(d.h - v[i].c), Math.abs(d.l - v[i].c)));
  const last20 = tr.slice(-20);
  return last20.reduce((a, b) => a + b, 0) / last20.length;
}

/**
 * Long na zavreni hodinove svicky 13:00-14:00 NY v posledni obchodni den pred rozhodnutim FOMC (tj. vstup ve 14:00 NY),
 * ven pred oznamenim (viz f31Exit). SL 3 denni ATR (pojistka).
 */
export function f31Signal(c: Candle[]): F2xSignal | null {
  const last = c[c.length - 1];
  if (!last) return null;
  const { date, hour } = nyParts(last.time);
  if (hour !== 13 || !isDayBeforeFomc(date)) return null;
  const a = dailyAtrFrom1h(c);
  if (!a) return null;
  return {
    dir: "long", sl: last.close - 3 * a,
    reason: "F31: zítra rozhoduje FOMC – long od 14:00 NY, ven zítra ve 13:00 NY (před oznámením ve 14:00). " +
      "Kandidát: 2019–26 +0,16 R na zasedání, 2013–18 bez výhody. SL 3 denní ATR jen jako pojistka.",
  };
}

/** Vystup F31: na zavreni svicky 12:00-13:00 NY v den rozhodnuti FOMC (hodinu pred oznamenim). */
export function f31Exit(c: Candle[]): boolean {
  const last = c[c.length - 1];
  if (!last) return false;
  const { date, hour } = nyParts(last.time);
  return hour === 12 && isFomcDay(date);
}

// ------------------------------------------------------------------ F46 zlato v asijske seanci (kandidat, 2026-11-19)

const londonFmt = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", hour12: false, weekday: "short",
});

/** Londynske datum, hodina a den v tydnu (0 = nedele) zacatku svicky. */
export function londonParts(t: number): { date: string; hour: number; dow: number } {
  const p = Object.fromEntries(londonFmt.formatToParts(new Date(t * 1000)).map((x) => [x.type, x.value]));
  const dow = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(p.weekday);
  return { date: `${p.year}-${p.month}-${p.day}`, hour: +p.hour % 24, dow };
}

/**
 * Hodina (Londyn) svicky, na jejimz zavreni F46 vstupuje. GC=F z Yahoo nema svicku behem denni prestavky CME 17:00-18:00 NY.
 * Ta je obvykle 22:00-23:00 Londyn -> svicka 22:00 chybi a vstupuje se na zavreni svicky 21:00 (22:00 Londyn; trh stoji,
 * cena ~ otevreni ve 23:00). V tydnech, kdy USA a UK nemaji stejny letni cas, je prestavka 21:00-22:00 Londyn -> vstup na
 * zavreni svicky 22:00 jako v testu. Oprava 2026-11-24 (export: pondeli 23. 11. bez signalu).
 */
export function f46EntryHour(t: number): number {
  const lon = londonParts(t).hour;
  const ny = nyParts(t).hour;
  const breakLon = (17 + ((lon - ny + 24) % 24)) % 24;
  return breakLon === 22 ? 21 : 22;
}

/**
 * Long na zavreni hodinove svicky 22:00-23:00 Londyn (vstup ve 23:00) v pondeli az ctvrtek, ven na zavreni svicky
 * 06:00-07:00 Londyn (viz f46Exit). V testu bez stopu; tady SL 3 denni ATR jen jako pojistka.
 */
export function f46Signal(c: Candle[]): F2xSignal | null {
  const last = c[c.length - 1];
  if (!last) return null;
  const { hour, dow } = londonParts(last.time);
  if (hour !== f46EntryHour(last.time) || dow < 1 || dow > 4) return null;
  const a = dailyAtrFrom1h(c);
  if (!a) return null;
  return {
    dir: "long", sl: last.close - 3 * a,
    reason: "F46: zlato v asijské seanci – long 23:00 → 07:00 Londýn. Kandidát (2026-11-19): převis nad ostatními hodinami " +
      "2009–18 t 5,1, 2019–26 t 2,0, 17 z 18 let; těsně neprošel (nejhorší třetina let ~0). SL 3 denní ATR jen jako pojistka.",
  };
}

/** Vystup F46: na zavreni svicky 06:00-07:00 Londyn. */
export function f46Exit(c: Candle[]): boolean {
  const last = c[c.length - 1];
  return !!last && londonParts(last.time).hour === 6;
}

// ------------------------------------------------------------------ F29 krypto momentum

/** Na zavreni nedelni denni svicky: vynos za 28 dni > 0 -> long na tyden (vystup po 7 dnech pres maxHoldBars). */
export function f29Signal(c: Candle[]): F2xSignal | null {
  const last = c[c.length - 1];
  if (!last || new Date(last.time * 1000).getUTCDay() !== 0) return null;
  const past = c.find((x) => x.time === last.time - 28 * DAY);
  if (!past) return null;
  const mom = last.close / past.close - 1;
  if (!(mom > 0)) return null;
  const a = atrLast(c);
  if (!a) return null;
  return {
    dir: "long", sl: last.close - 3 * a,
    reason: `F29: výnos za 28 dní ${pct(mom)} > 0 → long na týden (do dalšího pondělí). Kandidát (těsně neprošel: ` +
      `2022–26 t 1,33, ale Sharpe lepší než stále long). SL 3 ATR jen jako pojistka.`,
  };
}

// ------------------------------------------------------------------ F61 prelom mesice v Evrope (kandidat, 2026-11-20)

/** Kolikaty obchodni den mesice je den t podle kalendare burzy (1 = prvni). */
function euDayOfMonth(ex: Exchange, t: number): number {
  const d = new Date(t * 1000);
  let n = 0;
  for (let x = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1) / 1000; x <= t; x += DAY) if (isEuTradingDay(ex, x)) n++;
  return n;
}

/**
 * Na zavreni predposledniho obchodniho dne mesice (podle kalendare burzy) long, ven na zavreni 3. obchodniho dne dalsiho
 * mesice (viz f61Exit). V testu vstup na otevreni posledniho dne a bez stopu; tady SL 3 ATR20 jen jako pojistka.
 */
export function f61Signal(c: Candle[], marketId: string): F2xSignal | null {
  const ex = EXCHANGE_OF[marketId];
  const last = c[c.length - 1];
  if (!ex || !last || !isEuTradingDay(ex, last.time) || euTradingDaysLeft(ex, last.time) !== 1) return null;
  const a = atrLast(c);
  if (!a) return null;
  return {
    dir: "long", sl: last.close - 3 * a,
    reason: "F61: přelom měsíce v Evropě – long od zítřka (poslední obchodní den měsíce) do zavření 3. obchodního dne dalšího měsíce. " +
      "Kandidát (2026-11-20): EuroStoxx+IBEX 1992–2026 převis +0,15 R (t 1,92, laťka 2,0), broker 2019+ na 5 indexech +0,25 R, " +
      "kladné všech 5. Jen sledování dopředu v simulátoru, ne MT5. SL 3 ATR jen jako pojistka.",
  };
}

/** Vystup F61: na zavreni 3. obchodniho dne mesice. */
export function f61Exit(c: Candle[], marketId: string): boolean {
  const ex = EXCHANGE_OF[marketId];
  const last = c[c.length - 1];
  return !!ex && !!last && isEuTradingDay(ex, last.time) && euDayOfMonth(ex, last.time) === 3;
}

// ------------------------------------------------------------------ kandidati F73, F76, F79 (vyzkum 2026-11-24)
// Vault: Vyzkum/F73 az F78 ... a F79 az F81 ... - neprosly prisnou proverkou (3/5 bodu), jen sledovani dopredu v simulatoru.

/** Jako v testu: novy vstup az po vystupu predchoziho (drzeni h svicek); stav se dopocita z historie. Vraci, zda signal na posledni svicce vstupuje. */
function firesNonOverlap(flags: boolean[], h: number): boolean {
  let busy = -1;
  let fired = false;
  for (let i = 0; i < flags.length; i++) {
    fired = false;
    if (flags[i] && i > busy) {
      busy = i + h;
      fired = true;
    }
  }
  return fired;
}

/** Kvantil s linearni interpolaci (jako pandas quantile). */
function quantile(xs: number[], q: number): number {
  const s = [...xs].sort((a, b) => a - b);
  const pos = (s.length - 1) * q;
  const lo = Math.floor(pos);
  return lo + 1 < s.length ? s[lo] + (s[lo + 1] - s[lo]) * (pos - lo) : s[lo];
}

export const F76_VIX = 30;
export const F76_HOLD = 20;

/** F76: zavreni VIX >= 30 ve stejny den -> long indexu na 20 obchodnich dni, SL 3 ATR20 (pojistka). */
export function f76Signal(c: Candle[], vix: Candle[]): F2xSignal | null {
  const last = c[c.length - 1];
  const v = new Map(vix.map((x) => [x.time, x.close]));
  const vNow = last ? v.get(last.time) : undefined;
  if (vNow == null) return null;
  if (!firesNonOverlap(c.map((x) => (v.get(x.time) ?? 0) >= F76_VIX), F76_HOLD)) return null;
  const a = atrLast(c);
  if (!a) return null;
  return {
    dir: "long", sl: last.close - 3 * a,
    reason: `F76: VIX ${vNow.toFixed(1)} ≥ ${F76_VIX} – long na ${F76_HOLD} obchodních dní (kupovat strach). Kandidát (3/5 bodů): ` +
      "převis vývoj 1990–2018 +0,22 R (t 2,14), 2019–26 +0,21 R (t 0,96, jen 24 obchodů), broker +0,34 R; na DAXu záporný. " +
      "Jen sledování dopředu v simulátoru, ne MT5. SL 3 ATR jen jako pojistka.",
  };
}

export const F73_HOLD = 5;

/** F73: 5denni vynos TLT >= 90. percentil za predchozich 252 dni a 5denni vynos indexu < 0 -> long na 5 dni. */
export function f73Signal(c: Candle[], tlt: Candle[]): F2xSignal | null {
  const last = c[c.length - 1];
  if (!last || tlt.length < 260 || !tlt.some((x) => x.time === last.time)) return null;
  const r5 = tlt.map((x, j) => (j >= 5 ? x.close / tlt[j - 5].close - 1 : NaN));
  const flagT = new Map<number, boolean>();
  for (let j = 257; j < tlt.length; j++) {
    const hist = r5.slice(j - 252, j).filter((x) => Number.isFinite(x));
    if (hist.length >= 200) flagT.set(tlt[j].time, r5[j] >= quantile(hist, 0.9));
  }
  const from = Math.max(5, c.length - 300);
  const flags = c.slice(from).map((x, k) => {
    const i = k + from;
    return (flagT.get(x.time) ?? false) && x.close / c[i - 5].close - 1 < 0;
  });
  if (!firesNonOverlap(flags, F73_HOLD)) return null;
  const a = atrLast(c);
  if (!a) return null;
  const jt = tlt.findIndex((x) => x.time === last.time);
  return {
    dir: "long", sl: last.close - 3 * a,
    reason: `F73: útěk do dluhopisů – TLT za 5 dní ${pct(r5[jt])} (≥ 90. percentil za rok) a index za 5 dní ${pct(last.close / c[c.length - 6].close - 1)} ` +
      `→ long na ${F73_HOLD} obchodních dní. Kandidát (3/5 bodů): převis vývoj 2004–18 +0,07 R (t 1,57), 2019–26 +0,07 R, broker +0,13 R. ` +
      "Jen sledování dopředu v simulátoru, ne MT5. SL 3 ATR jen jako pojistka.",
  };
}

/** F79 Halloween: signal na zavreni posledniho obchodniho dne rijna az brezna -> long na cely dalsi mesic (listopad-duben). */
const F79_SIGNAL_MONTHS = new Set([10, 11, 12, 1, 2, 3]);
export const F79_SL_ATR = 8;

export function f79Signal(c: Candle[], marketId: string): F2xSignal | null {
  const ex = EXCHANGE_OF[marketId];
  const last = c[c.length - 1];
  if (!ex || !last || !isEuTradingDay(ex, last.time) || euTradingDaysLeft(ex, last.time) !== 0) return null;
  const m = new Date(last.time * 1000).getUTCMonth() + 1;
  if (!F79_SIGNAL_MONTHS.has(m)) return null;
  const a = atrLast(c);
  if (!a) return null;
  return {
    dir: "long", sl: last.close - F79_SL_ATR * a,
    reason: "F79 Halloween: long na celý další měsíc (držení listopad–duben, vždy na měsíc), ven na zavření posledního obchodního dne měsíce. " +
      "Kandidát (3/5 bodů): DAX, FTSE, CAC převis +0,17 až +0,20 R za měsíc (t 1,8–2,2), US indexy od 2019 bez výhody. " +
      `V testu bez stopu, tady SL ${F79_SL_ATR} ATR jen proti katastrofě. Jen sledování dopředu v simulátoru, ne MT5.`,
  };
}

/** Vystup F79: na zavreni posledniho obchodniho dne mesice podle burzy. */
export function f79Exit(c: Candle[], marketId: string): boolean {
  const ex = EXCHANGE_OF[marketId];
  const last = c[c.length - 1];
  return !!ex && !!last && isEuTradingDay(ex, last.time) && euTradingDaysLeft(ex, last.time) === 0;
}
