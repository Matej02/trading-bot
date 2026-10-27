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
