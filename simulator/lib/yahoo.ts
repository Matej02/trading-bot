// Svicky z Yahoo Finance (forex, indexy, kovy, ropa). Vola se ze serveru - v prohlizeci pres /api/candles
// (CORS), na serveru (bot 24/7) primo.
import type { Candle, Market } from "./types";

// [plna historie, kratke doplneni pri zivem obnovovani]
export const YAHOO_RANGE: Record<string, [string, string]> = {
  "1m": ["5d", "1d"], "5m": ["1mo", "5d"], "15m": ["1mo", "5d"], "1h": ["1y", "5d"], "1d": ["5y", "1mo"],
};
const INTERVAL: Record<string, string> = { "1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "1d": "1d" };

type Num = number | null;

/** Svicky v cenach Yahoo (bez prepoctu priceScale). delayed = zpozdeni dat v minutach. */
export async function yahooCandles(m: Market, tf: string, live: boolean): Promise<{ candles: Candle[]; delayed: number }> {
  const range = YAHOO_RANGE[tf][live ? 1 : 0];
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(m.yahoo)}` +
    `?interval=${INTERVAL[tf]}&range=${range}&includePrePost=false`;
  const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0" }, cache: "no-store" });
  if (!r.ok) throw new Error(`Yahoo vrátilo ${r.status}`);
  const j = await r.json();
  const res = j?.chart?.result?.[0];
  if (!res?.timestamp) return { candles: [], delayed: 0 };
  const q = res.indicators.quote[0] as { open: Num[]; high: Num[]; low: Num[]; close: Num[] };
  // datum obchodniho dne v case burzy, vcetne letniho casu (pevny gmtoffset by v lete posunul den)
  const localDate = new Intl.DateTimeFormat("en-CA", { timeZone: res.meta.exchangeTimezoneName ?? "UTC" });

  const byTime = new Map<number, Candle>();
  (res.timestamp as number[]).forEach((ts, i) => {
    const [o, h, l, c] = [q.open[i], q.high[i], q.low[i], q.close[i]];
    if (o == null || h == null || l == null || c == null) return;
    // denni svicka = obchodni den burzy -> pulnoc UTC toho dne (stejne jako datum v Pythonu)
    const t = tf === "1d" ? Date.parse(`${localDate.format(new Date(ts * 1000))}T00:00:00Z`) / 1000 : ts;
    byTime.set(t, { time: t, open: o, high: h, low: l, close: c });
  });
  const candles = [...byTime.values()].sort((a, b) => a.time - b.time);

  // Yahoo pridava na konec bod s aktualnim casem (napr. 12:25:45). Bez opravy by se rozpracovana
  // svicka tvarila jako uzavrena a strategie by na ni obchodovala. Bod se zarovna na mrizku
  // intervalu (u US akcii zacina hodina v :30): patri-li do predchozi svicky, spoji se s ni,
  // jinak je to rozpracovana svicka se spravnym casem.
  const sec = ({ "1m": 60, "5m": 300, "15m": 900, "1h": 3600 } as Record<string, number>)[tf];
  if (sec && candles.length > 1) {
    const last = candles[candles.length - 1];
    const prev = candles[candles.length - 2];
    const off = ((prev.time % sec) + sec) % sec;
    if ((last.time - off) % sec !== 0) {
      const aligned = Math.floor((last.time - off) / sec) * sec + off;
      if (aligned === prev.time) {
        candles.pop();
        prev.close = last.close;
        prev.high = Math.max(prev.high, last.high);
        prev.low = Math.min(prev.low, last.low);
      } else {
        last.time = aligned;
      }
    }
  }
  return { candles, delayed: Math.round((res.meta.exchangeDataDelayedBy ?? 0) / 60) };
}
