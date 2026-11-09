// Burzovni kalendar NYSE (svatky) a terminy FOMC - pro systemy F31 (drift pred FOMC) a F33 (rebalancovani na konci mesice).
// Denni svicky v simulatoru maji cas = pulnoc UTC obchodniho dne burzy (viz yahoo.ts), proto se tu pracuje s pulnocemi UTC.

const DAY = 86400;
const utc = (y: number, m: number, d: number) => Date.UTC(y, m, d) / 1000;

function nthWeekday(y: number, m: number, wd: number, n: number): number {
  const first = new Date(Date.UTC(y, m, 1)).getUTCDay();
  return utc(y, m, 1 + ((wd - first + 7) % 7) + 7 * (n - 1));
}

function lastWeekday(y: number, m: number, wd: number): number {
  const last = new Date(Date.UTC(y, m + 1, 0));
  return utc(y, m, last.getUTCDate() - ((last.getUTCDay() - wd + 7) % 7));
}

/** Velikonocni nedele (gregoriansky kalendar, anonymni algoritmus). */
function easter(y: number): number {
  const a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4;
  const f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31), day = ((h + l - 7 * m + 114) % 31) + 1;
  return utc(y, month - 1, day);
}

/** Svatek pripadne na sobotu -> patek, na nedeli -> pondeli (pravidlo NYSE). */
function observed(t: number): number {
  const wd = new Date(t * 1000).getUTCDay();
  return wd === 6 ? t - DAY : wd === 0 ? t + DAY : t;
}

const cache = new Map<number, Set<number>>();

/** Dny, kdy je NYSE zavrena (pulnoci UTC). */
export function nyseHolidays(y: number): Set<number> {
  const hit = cache.get(y);
  if (hit) return hit;
  const ny = utc(y, 0, 1);
  const nyWd = new Date(ny * 1000).getUTCDay();
  const h = [
    nyWd === 0 ? ny + DAY : nyWd === 6 ? NaN : ny, // Novy rok v sobotu se nepresouva na 31. 12.
    nthWeekday(y, 0, 1, 3), // Martin Luther King
    nthWeekday(y, 1, 1, 3), // Presidents Day
    easter(y) - 2 * DAY, // Velky patek
    lastWeekday(y, 4, 1), // Memorial Day
    y >= 2022 ? observed(utc(y, 5, 19)) : NaN, // Juneteenth
    observed(utc(y, 6, 4)), // Den nezavislosti
    nthWeekday(y, 8, 1, 1), // Labor Day
    nthWeekday(y, 10, 4, 4), // Dikuvzdani
    observed(utc(y, 11, 25)), // Vanoce
  ].filter((x) => !Number.isNaN(x));
  const s = new Set(h);
  cache.set(y, s);
  return s;
}

const midnight = (t: number) => Math.floor(t / DAY) * DAY;

export function isTradingDay(t: number): boolean {
  const d = midnight(t);
  const wd = new Date(d * 1000).getUTCDay();
  return wd !== 0 && wd !== 6 && !nyseHolidays(new Date(d * 1000).getUTCFullYear()).has(d);
}

/** Kolik obchodnich dni NYSE zbyva v mesici PO dni t (0 = t je posledni obchodni den mesice). */
export function tradingDaysLeftInMonth(t: number): number {
  const d0 = new Date(midnight(t) * 1000);
  const end = utc(d0.getUTCFullYear(), d0.getUTCMonth() + 1, 0);
  let n = 0;
  for (let d = midnight(t) + DAY; d <= end; d += DAY) if (isTradingDay(d)) n++;
  return n;
}

/** Dalsi obchodni den NYSE po dni t (pulnoc UTC). */
export function nextTradingDay(t: number): number {
  let d = midnight(t) + DAY;
  while (!isTradingDay(d)) d += DAY;
  return d;
}

/**
 * Rozhodnuti FOMC (posledni den radneho zasedani, oznameni 14:00 NY). Zdroj: federalreserve.gov (fomccalendars),
 * overeno 2026-11-05; 2027 je predbezne. Po poslednim terminu se system F31 sam zastavi - doplnit dalsi rok.
 */
export const FOMC_DATES = ["2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28",
  "2026-12-09", "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08"];
const FOMC = new Set(FOMC_DATES);

const nyFmt = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", hourCycle: "h23",
});

/** Datum (YYYY-MM-DD) a hodina v New Yorku. */
export function nyParts(t: number): { date: string; hour: number } {
  const p = Object.fromEntries(nyFmt.formatToParts(new Date(t * 1000)).map((x) => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, hour: +p.hour };
}

export const isFomcDay = (date: string) => FOMC.has(date);

/** Je den `date` (YYYY-MM-DD v NY) posledni obchodni den pred rozhodnutim FOMC? */
export function isDayBeforeFomc(date: string): boolean {
  const next = nextTradingDay(Date.parse(`${date}T00:00:00Z`) / 1000);
  return FOMC.has(new Date(next * 1000).toISOString().slice(0, 10));
}

export const lastFomcDate = FOMC_DATES[FOMC_DATES.length - 1];
