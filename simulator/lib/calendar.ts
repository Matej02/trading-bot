// Ekonomicky kalendar (ForexFactory, zdarma bez klice): agent "Kalendar" blokuje vstupy tesne
// pred a po zpravach s vysokym dopadem na meny daneho trhu.
import type { Market } from "./types";

export interface CalEvent {
  time: number; // unix s
  currency: string;
  impact: string; // High / Medium / Low / Holiday
  title: string;
  forecast?: string;
  previous?: string;
}

/** Uz vyhlasena zprava se skutecnou hodnotou (FXStreet, lib/server/calendar.ts). */
export interface Release {
  time: number;
  currency: string;
  impact: "High" | "Medium";
  title: string;
  actual: string;
  forecast?: string;
  previous?: string;
  better: boolean | null; // vyslo pro menu lepe nez prognoza
}

/** events = null: ForexFactory se nepodarilo nacist (vyhlasene zpravy z FXStreet mohou prijit i tak) */
export interface Calendar { events: CalEvent[] | null; releases: Release[]; error?: string }

export const NEWS_BEFORE_MIN = 30; // tolik minut pred zpravou se nevstupuje
export const NEWS_AFTER_MIN = 15; // a tolik po ni (nejvetsi skoky a spready)

const INDEX_CCY: Record<string, string> = {
  SPX500mini: "USD", US30mini: "USD", NAS100mini: "USD", GER_30mini: "EUR", FRA_40mini: "EUR", EUR_50mini: "EUR",
  ESP_35mini: "EUR", GBR_100mini: "GBP",
};

/** Meny, jejichz zpravy hybou trhem: forex obe, kovy/ropa/krypto USD, indexy mena burzy. */
export function marketCurrencies(m: Market): string[] {
  if (INDEX_CCY[m.id]) return [INDEX_CCY[m.id]];
  if (m.group === "FOREX" && m.id.length === 6) return [m.id.slice(0, 3), m.id.slice(3, 6)];
  if (m.id.endsWith("EUR")) return ["USD", "EUR"];
  return ["USD"];
}

/** Zpravy pro trh od - do (unix s), serazene podle casu. */
export function eventsFor(events: CalEvent[], m: Market, from: number, to: number, impacts = ["High"]) {
  const ccy = new Set(marketCurrencies(m));
  return events.filter((e) => ccy.has(e.currency) && impacts.includes(e.impact) && e.time >= from && e.time <= to)
    .sort((a, b) => a.time - b.time);
}

export function parseFF(raw: { title: string; country: string; date: string; impact: string; forecast?: string; previous?: string }[]) {
  return raw.flatMap((e): CalEvent[] => {
    const t = Date.parse(e.date) / 1000;
    return isFinite(t) ? [{ time: t, currency: e.country, impact: e.impact, title: e.title, forecast: e.forecast, previous: e.previous }] : [];
  });
}

export function inMinutes(sec: number) {
  const m = Math.round(sec / 60);
  if (Math.abs(m) < 90) return `${m} min`;
  const h = sec / 3600;
  return Math.abs(h) < 36 ? `${h.toFixed(1)} h` : `${(h / 24).toFixed(1)} dne`;
}

/** Cislo z hodnoty kalendare: "3.1%", "1.40M" -> 3.1, 1.4 (prognoza i skutecnost jsou ze stejneho zdroje) */
function num(v?: string) {
  const m = v?.replace(/,/g, "").match(/^\s*(-?\d+(?:\.\d+)?)/);
  return m ? parseFloat(m[1]) : null;
}

/** Jak zprava dopadla proti prognoze: "nad prognózou" / "pod prognózou" / "podle prognózy" / "". */
export function surprise(e: Release) {
  const a = num(e.actual), f = num(e.forecast);
  if (a == null || f == null) return "";
  if (Math.abs(a - f) <= Math.abs(f) * 1e-9) return "podle prognózy";
  return a > f ? "nad prognózou" : "pod prognózou";
}

/** Vyhlasena zprava jednou vetou: "USD CPI y/y: vyšlo 3.1% (prognóza 2.9%, předtím 3.0%) – nad prognózou" */
export function releaseText(e: Release) {
  const s = surprise(e);
  const b = e.better == null || s === "podle prognózy" ? "" : e.better ? `, pro ${e.currency} lepší, než se čekalo` : `, pro ${e.currency} horší, než se čekalo`;
  return `${e.currency} ${e.title}: vyšlo ${e.actual} (prognóza ${e.forecast || "?"}, předtím ${e.previous || "?"})${s ? ` – ${s}${b}` : ""}`;
}

/** Uz vyhlasene zpravy pro trh od - do, nejnovejsi prvni. */
export function releasesFor(releases: Release[], m: Market, from: number, to: number) {
  const ccy = new Set(marketCurrencies(m));
  return releases.filter((e) => ccy.has(e.currency) && e.time >= from && e.time <= to).sort((a, b) => b.time - a.time);
}

