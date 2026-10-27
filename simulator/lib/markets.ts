import data from "./broker.json";
import type { Market } from "./types";

type Raw = Omit<Market, "id">;

export const BROKER_ACCOUNT: string = data.account;

export const MARKETS: Record<string, Market> = Object.fromEntries(
  Object.entries(data.markets as Record<string, Raw>).map(([id, m]) => [id, { id, ...m }]),
);

export const MARKET_IDS = Object.keys(MARKETS);

/** Poradi v nabidce grafu: nejdriv to, co je videt nejvic zive */
export const CHART_ORDER = [
  "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDJPY", "XAUUSD", "SPX500mini", "NAS100mini",
  "GER_30mini", ...MARKET_IDS.filter((id) => !["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY",
    "AUDJPY", "XAUUSD", "SPX500mini", "NAS100mini", "GER_30mini"].includes(id)),
];

export function spreadAt(m: Market, t: number): number {
  return m.spreadByHour[new Date(t * 1000).getUTCHours()];
}

/** Ze stredni ceny udela bid/ask se spreadem brokera v dane hodine */
export function quote(m: Market, mid: number, t: number) {
  const s = spreadAt(m, t);
  return { bid: mid - s / 2, ask: mid + s / 2, spread: s };
}

export function fmt(m: Market | undefined, p: number | null | undefined): string {
  if (p == null || !isFinite(p)) return "-";
  return p.toFixed(m ? m.digits : 5);
}

export const isCrypto = (m: Market) => m.group === "CRYPTO";
export const isFxOrMetal = (m: Market) => m.group === "FOREX" || m.group === "METALS";

/** Meny pro hlidani expozice (jen forex a kovy), napr. EURUSD -> [EUR, USD] */
export function currencies(m: Market): [string, string] | null {
  if (!isFxOrMetal(m) || m.id.length !== 6) return null;
  return [m.id.slice(0, 3), m.id.slice(3, 6)];
}
