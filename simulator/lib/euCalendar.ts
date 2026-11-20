// Burzovni kalendare evropskych indexu pro F61 (prelom mesice v Evrope): Xetra/Eurex (DAX, Euro Stoxx 50),
// Euronext Paris (CAC 40), BME Madrid (IBEX 35), London Stock Exchange (FTSE 100).
// Denni svicky maji cas = pulnoc UTC obchodniho dne burzy (viz yahoo.ts), proto se pracuje s pulnocemi UTC.
// Zdroj svatku: pravidla burz (stav 2026); mimoradne svatky (napr. kralovske v UK) je potreba doplnit rucne do EXTRA.

const DAY = 86400;
const utc = (y: number, m: number, d: number) => Date.UTC(y, m, d) / 1000;
const wday = (t: number) => new Date(t * 1000).getUTCDay();

function easter(y: number): number {
  const a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4;
  const f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31), day = ((h + l - 7 * m + 114) % 31) + 1;
  return utc(y, month - 1, day);
}

function firstMonday(y: number, m: number): number {
  const f = wday(utc(y, m, 1));
  return utc(y, m, 1 + ((1 - f + 7) % 7));
}

function lastMonday(y: number, m: number): number {
  const last = utc(y, m + 1, 0);
  return last - ((wday(last) - 1 + 7) % 7) * DAY;
}

export type Exchange = "xetra" | "euronext" | "bme" | "lse";

export const EXCHANGE_OF: Record<string, Exchange> = {
  GER_30mini: "xetra", EUR_50mini: "xetra", FRA_40mini: "euronext", ESP_35mini: "bme", GBR_100mini: "lse",
};

/** Mimoradne zavrene dny (YYYY-MM-DD) navic k pravidlum. */
const EXTRA: Record<Exchange, string[]> = { xetra: [], euronext: [], bme: [], lse: [] };

const cache = new Map<string, Set<number>>();

function holidays(ex: Exchange, y: number): Set<number> {
  const key = `${ex}${y}`;
  const hit = cache.get(key);
  if (hit) return hit;
  const e = easter(y);
  const h: number[] = [utc(y, 0, 1), e - 2 * DAY, e + DAY, utc(y, 11, 25), utc(y, 11, 26)];
  if (ex !== "lse") h.push(utc(y, 4, 1));
  if (ex === "xetra") h.push(utc(y, 11, 24), utc(y, 11, 31));
  if (ex === "lse") {
    // Novy rok a Vanoce v UK: pripadnou-li na vikend, presouvaji se na nejblizsi volny pracovni den
    const ny = utc(y, 0, 1);
    if (wday(ny) === 6) h.push(ny + 2 * DAY);
    if (wday(ny) === 0) h.push(ny + DAY);
    const xmas = utc(y, 11, 25);
    if (wday(xmas) === 6) h.push(xmas + 2 * DAY, xmas + 3 * DAY);   // so -> po 27., boxing day ut 28.
    if (wday(xmas) === 0) h.push(xmas + 2 * DAY);                   // ne -> ut 27. (po 26. je boxing day)
    if (wday(xmas) === 5) h.push(xmas + 3 * DAY);                   // boxing day v sobotu -> po 28.
    h.push(firstMonday(y, 4), lastMonday(y, 4), lastMonday(y, 7));
  }
  for (const d of EXTRA[ex]) if (d.startsWith(`${y}-`)) h.push(Date.parse(`${d}T00:00:00Z`) / 1000);
  const s = new Set(h);
  cache.set(key, s);
  return s;
}

const midnight = (t: number) => Math.floor(t / DAY) * DAY;

export function isEuTradingDay(ex: Exchange, t: number): boolean {
  const d = midnight(t);
  const wd = wday(d);
  return wd !== 0 && wd !== 6 && !holidays(ex, new Date(d * 1000).getUTCFullYear()).has(d);
}

/** Kolik obchodnich dni burzy zbyva v mesici PO dni t (0 = t je posledni obchodni den mesice). */
export function euTradingDaysLeft(ex: Exchange, t: number): number {
  const d0 = new Date(midnight(t) * 1000);
  const end = utc(d0.getUTCFullYear(), d0.getUTCMonth() + 1, 0);
  let n = 0;
  for (let d = midnight(t) + DAY; d <= end; d += DAY) if (isEuTradingDay(ex, d)) n++;
  return n;
}
