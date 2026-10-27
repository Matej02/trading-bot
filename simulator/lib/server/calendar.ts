// Kalendar ze zdroje ForexFactory (tento tyden), v databazi podrzeny hodinu - zdroj nema rad caste dotazy.
// Skutecne hodnoty po vyhlaseni ForexFactory nema - ty jsou z FXStreet (zdarma bez klice).
import { parseFF, type CalEvent, type Calendar, type Release } from "../calendar";
import type { KV } from "./kv";

const URL_ = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";
const KEY = "sim:calendar";
let mem: { at: number; events: CalEvent[] } | null = null;

async function ffEvents(kv: KV | null): Promise<CalEvent[]> {
  const now = Date.now();
  if (mem && now - mem.at < 3600_000) return mem.events;
  if (kv) {
    const [raw] = await kv.pipeline([["GET", KEY]]);
    const cached = typeof raw === "string" ? (JSON.parse(raw) as { at: number; events: CalEvent[] }) : null;
    if (cached && now - cached.at < 3600_000) return (mem = cached).events;
  }
  const r = await fetch(URL_, { headers: { "User-Agent": "Mozilla/5.0" }, cache: "no-store" });
  if (!r.ok) {
    if (mem) return mem.events; // radsi starsi kalendar nez zadny
    throw new Error(`kalendář vrátil ${r.status}`);
  }
  mem = { at: now, events: parseFF(await r.json()) };
  if (kv) await kv.pipeline([["SET", KEY, JSON.stringify(mem)]]);
  return mem.events;
}

// ---------------------------------------------------------- vyhlasene zpravy (FXStreet)
// Kalendar FXStreet (verejne API jejich webu, zdarma bez klice) ma cas v UTC, skutecnou hodnotu, prognozu
// i to, jestli cislo vyslo pro menu lepe nez cekano. Bere se zvlast (nazvy se s ForexFactory nedaji
// spolehlive sparovat: "HPI" vs "Housing Price Index"); ForexFactory zustava pro hlidani pristich zprav.

type FxRow = {
  dateUtc: string; currencyCode: string; name: string; actual: number | null; consensus: number | null;
  previous: number | null; unit: string | null; isBetterThanExpected: boolean | null; volatility: string;
};
const REL_TTL = 10 * 60_000;
const REL_KEY = "sim:releases";
let relMem: { at: number; releases: Release[] } | null = null;
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36";
const IMPACT: Record<string, Release["impact"]> = { HIGH: "High", MEDIUM: "Medium" };

const val = (v: number | null, unit: string | null) => (v == null ? undefined : `${v}${unit === "%" ? "%" : ""}`);

/** Dulezite zpravy vyhlasene za poslednich 36 h se skutecnou hodnotou. */
export async function getReleases(kv: KV | null): Promise<Release[]> {
  const now = Date.now();
  if (relMem && now - relMem.at < REL_TTL) return relMem.releases;
  if (kv) {
    const [raw] = await kv.pipeline([["GET", REL_KEY]]);
    const cached = typeof raw === "string" ? (JSON.parse(raw) as { at: number; releases: Release[] }) : null;
    if (cached && now - cached.at < REL_TTL) return (relMem = cached).releases;
  }
  const iso = (t: number) => new Date(t).toISOString().slice(0, 19) + "Z";
  const r = await fetch(`https://calendar-api.fxstreet.com/en/api/v1/eventDates/${iso(now - 36 * 3600_000)}/${iso(now)}`, {
    headers: { "User-Agent": UA, Referer: "https://www.fxstreet.com/", Accept: "application/json" },
    cache: "no-store", signal: AbortSignal.timeout(5000),
  });
  if (!r.ok) throw new Error(`FXStreet ${r.status}`);
  const releases = ((await r.json()) as FxRow[]).flatMap((x): Release[] => {
    const actual = val(x.actual, x.unit);
    const impact = IMPACT[x.volatility];
    if (!actual || !impact) return [];
    return [{ time: Date.parse(x.dateUtc) / 1000, currency: x.currencyCode, impact, title: x.name.trim(), actual,
      forecast: val(x.consensus, x.unit), previous: val(x.previous, x.unit), better: x.isBetterThanExpected }];
  });
  relMem = { at: now, releases };
  if (kv) await kv.pipeline([["SET", REL_KEY, JSON.stringify(relMem), "PX", REL_TTL]]);
  return releases;
}

/** Pristi zpravy (ForexFactory) + uz vyhlasene se skutecnou hodnotou (FXStreet; kdyz nejde, prazdne). */
export async function getCalendar(kv: KV | null): Promise<Calendar> {
  const [ff, releases] = await Promise.all([
    ffEvents(kv).then((events) => ({ events, error: undefined }), (e: Error) => ({ events: null, error: e.message })),
    getReleases(kv).catch(() => [] as Release[]),
  ]);
  return { ...ff, releases };
}
