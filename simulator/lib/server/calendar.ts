// Kalendar ze zdroje ForexFactory (tento tyden), v databazi podrzeny hodinu - zdroj nema rad caste dotazy.
import { parseFF, type CalEvent } from "../calendar";
import type { KV } from "./kv";

const URL_ = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";
const KEY = "sim:calendar";
let mem: { at: number; events: CalEvent[] } | null = null;

export async function getCalendar(kv: KV | null): Promise<CalEvent[]> {
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
