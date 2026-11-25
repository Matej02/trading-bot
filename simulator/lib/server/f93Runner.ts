// F93 na serveru: jednou denne po zavreni US burzy stahne udalosti z EDGAR (SEC) a denni ceny z Yahoo,
// zapise nove signaly (vstup na otevreni dalsiho obchodniho dne) a vyhodnoti obchody, jejichz den uz skoncil.
// Jen sledovani dopredu: do brokera simulatoru ani do MT5 nic nejde. Stav v databazi pod klicem sim:f93.
import {
  cleanDays, f93SignalFor, f93Settle, F93_MAX_DAY, F93_TICKERS, dedupeEvents, indexReturns, nyWall,
  type F93Day, type F93Result,
} from "../f93";
import type { KV } from "./kv";

export const F93_KEY = "sim:f93";
const LOCK = "sim:f93:lock";
// sledovani dopredu od nasazeni: signaly s dnem reakce od tohoto data
export const F93_SINCE = "2026-11-25";
const CLOSE_DONE = "16:40"; // po tomhle case NY je denni svicka Yahoo uzavrena
const RETRY_MS = 20 * 60_000;
// SEC chce v User-Agent kontakt; volitelne SEC_UA ve Vercelu, jinak obecny nazev (bez osobnich udaju)
const SEC_UA = process.env.SEC_UA || "TradingSimulator research-bot";

export interface F93Trade {
  id: string; // ticker|den reakce
  ticker: string;
  event: string; // cas prijeti vysledku v NY
  dayD: string;
  z: number;
  dir: 1 | -1;
  atr: number;
  closeD: number;
  createdAt: number; // ms - kdy simulator signal poznal
  late: boolean; // signal zapsan az po otevreni dne vstupu (vypadek) - do prisneho vyhodnoceni nepocitat
  rank: number; // poradi podle |z| v ramci dne (meritko prop bere nejvys 3)
  dayK?: string; // den obchodu
  result?: F93Result;
}

export interface F93State {
  since: string;
  doneFor: string; // pro ktery uzavreny stav uz beh probehl
  lastTry: number;
  lastOk: number;
  lastError: string | null;
  lastDay: string | null; // posledni uzavreny den v datech
  trades: F93Trade[];
}

const empty = (): F93State => ({ since: F93_SINCE, doneFor: "", lastTry: 0, lastOk: 0, lastError: null, lastDay: null, trades: [] });

export async function loadF93(kv: KV): Promise<F93State> {
  const [raw] = await kv.pipeline([["GET", F93_KEY]]);
  try {
    return typeof raw === "string" ? { ...empty(), ...(JSON.parse(raw) as F93State) } : empty();
  } catch {
    return empty();
  }
}

/** Dnesni datum v NY a jestli uz je dnesni den uzavreny. doneKey = posledni uzavreny stav. */
function nyNow(now = Date.now()) {
  const w = nyWall(now);
  const today = w.slice(0, 10);
  const closed = w.slice(11, 16) >= CLOSE_DONE;
  return { w, today, closed, doneKey: closed ? `${today} po` : `${today} pred` };
}

async function getJson(url: string, headers: Record<string, string>) {
  const r = await fetch(url, { headers, cache: "no-store", signal: AbortSignal.timeout(12_000) });
  if (!r.ok) throw new Error(`${new URL(url).host} vrátilo ${r.status}`);
  return r.json();
}

type Num = number | null;

/** Denni svicky z Yahoo upravene o dividendy a splity (jako yfinance auto_adjust v testu). */
export async function yahooDaily(symbol: string): Promise<F93Day[]> {
  const j = await getJson(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1y`,
    { "User-Agent": "Mozilla/5.0" });
  const res = j?.chart?.result?.[0];
  if (!res?.timestamp) return [];
  const q = res.indicators.quote[0] as { open: Num[]; high: Num[]; low: Num[]; close: Num[] };
  const adj = (res.indicators.adjclose?.[0]?.adjclose ?? null) as Num[] | null;
  const fmt = new Intl.DateTimeFormat("en-CA", { timeZone: res.meta.exchangeTimezoneName ?? "America/New_York" });
  const rows: F93Day[] = [];
  (res.timestamp as number[]).forEach((ts, i) => {
    const [o, h, l, c] = [q.open[i], q.high[i], q.low[i], q.close[i]];
    if (o == null || h == null || l == null || c == null) return;
    const a = adj?.[i];
    const k = a != null && c > 0 ? a / c : 1;
    rows.push({ d: fmt.format(new Date(ts * 1000)), o: o * k, h: h * k, l: l * k, c: c * k });
  });
  rows.sort((x, y) => (x.d < y.d ? -1 : x.d > y.d ? 1 : 0));
  return cleanDays(rows);
}

/** Casy prijeti 8-K s polozkou 2.02 (vysledky) z EDGAR. */
export async function edgarEarnings(cik: number): Promise<string[]> {
  const j = await getJson(`https://data.sec.gov/submissions/CIK${String(cik).padStart(10, "0")}.json`,
    { "User-Agent": SEC_UA });
  const r = j?.filings?.recent;
  if (!r?.form) return [];
  const out: string[] = [];
  (r.form as string[]).forEach((f, i) => {
    if (f === "8-K" && String(r.items?.[i] ?? "").includes("2.02") && r.acceptanceDateTime?.[i]) out.push(r.acceptanceDateTime[i]);
  });
  return out;
}

function nextWeekday(d: string): string {
  const t = new Date(d + "T00:00:00Z");
  do t.setUTCDate(t.getUTCDate() + 1); while (t.getUTCDay() === 0 || t.getUTCDay() === 6);
  return t.toISOString().slice(0, 10);
}

async function pool<T, R>(xs: T[], n: number, fn: (x: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(xs.length);
  let i = 0;
  await Promise.all(Array.from({ length: n }, async () => {
    while (i < xs.length) {
      const k = i++;
      out[k] = await fn(xs[k]);
    }
  }));
  return out;
}

/** Je cas na beh? (novy uzavreny den, nebo opakovani po chybe) */
export function f93Due(s: F93State, now = Date.now()): boolean {
  return s.doneFor !== nyNow(now).doneKey && now - s.lastTry > RETRY_MS;
}

/** Jeden beh: stahne data, prida signaly, vyhodnoti hotove obchody. Vraci kratkou zpravu. */
export async function runF93(kv: KV, force = false): Promise<string> {
  const s = await loadF93(kv);
  const now = Date.now();
  if (!force && !f93Due(s, now)) return "F93: není co dělat";
  const [lock] = await kv.pipeline([["SET", LOCK, String(now), "NX", "PX", 120_000]]);
  if (lock !== "OK") return "F93: běží jinde";
  const ny = nyNow(now);
  s.lastTry = now;
  try {
    const usable = (d: F93Day[]) => d.filter((x) => x.d < ny.today || (x.d === ny.today && ny.closed));
    const spx = usable(await yahooDaily("^GSPC"));
    if (spx.length < 100) throw new Error("málo dat S&P 500 z Yahoo");
    const ixr = indexReturns(spx);
    const data = await pool(F93_TICKERS, 6, async ([t, cik]) => {
      const [days, ev] = await Promise.all([yahooDaily(t), edgarEarnings(cik)]);
      return { t, days: usable(days), ev };
    });
    const byId = new Map(s.trades.map((x) => [x.id, x]));
    let added = 0, settled = 0;
    for (const { t, days, ev } of data) {
      for (const et of dedupeEvents(ev)) {
        if (et.slice(0, 10) < "2026-09-01") continue;
        const sig = f93SignalFor(t, days, ixr, et);
        if (!sig || sig.dayD < s.since) continue;
        const id = `${t}|${sig.dayD}`;
        if (byId.has(id)) continue;
        // pozde = signal poznany az po otevreni dne vstupu (vypadek budiku); svatky se neresi (jen vikend)
        const kIdx = days.findIndex((x) => x.d === sig.dayD) + 1;
        const nextWd = nextWeekday(sig.dayD);
        const late = kIdx < days.length || ny.today > nextWd || (ny.today === nextWd && ny.w.slice(11, 16) >= "09:30");
        const tr: F93Trade = { id, ticker: t, event: et, dayD: sig.dayD, z: sig.z, dir: sig.dir, atr: sig.atr, closeD: sig.close,
          createdAt: now, late, rank: 0 };
        byId.set(id, tr);
        added++;
      }
      for (const tr of byId.values()) {
        if (tr.ticker !== t || tr.result) continue;
        const k = days.findIndex((x) => x.d === tr.dayD) + 1;
        if (k <= 0 || k >= days.length) continue;
        const res = f93Settle(days[k], tr.dir, tr.atr);
        if (res) {
          tr.dayK = days[k].d;
          tr.result = res;
          settled++;
        }
      }
    }
    const trades = [...byId.values()].sort((a, b) => (a.dayD < b.dayD ? -1 : a.dayD > b.dayD ? 1 : Math.abs(b.z) - Math.abs(a.z)));
    let prev = "", r = 0;
    for (const tr of trades) {
      r = tr.dayD === prev ? r + 1 : 1;
      prev = tr.dayD;
      tr.rank = r;
    }
    s.trades = trades;
    s.lastDay = spx[spx.length - 1]?.d ?? null;
    s.doneFor = ny.doneKey;
    s.lastOk = now;
    s.lastError = null;
    await kv.pipeline([["SET", F93_KEY, JSON.stringify(s)], ["DEL", LOCK]]);
    return `F93: nové signály ${added}, vyhodnoceno ${settled} (data do ${s.lastDay})`;
  } catch (e) {
    s.lastError = (e as Error).message;
    await kv.pipeline([["SET", F93_KEY, JSON.stringify(s)], ["DEL", LOCK]]);
    return `F93 chyba: ${s.lastError}`;
  }
}

/** Beh s casovym limitem (aby nezdrzel bota v ticku). */
export async function runF93Bounded(kv: KV, ms = 25_000): Promise<string> {
  return Promise.race([runF93(kv), new Promise<string>((r) => setTimeout(() => r("F93: časový limit, zkusí se znovu"), ms))]);
}

export { F93_MAX_DAY };
