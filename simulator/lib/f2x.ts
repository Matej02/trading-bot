// Systemy z fronty napadu F22-F33 (vyzkum 2026-11-07/08, vault: Vyzkum/Souhrn testu F21-F33 a prinosy):
//  F33 rebalancovani na konci mesice (proslo), F31 drift pred FOMC (kandidat), F29 krypto momentum (kandidat).
// Pravidla 1:1 podle planu zapsanych predem; odchylky od testu jsou popsane v definicich systemu (strategies.ts).
import { atr } from "./indicators";
import type { Candle, Dir } from "./types";
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
