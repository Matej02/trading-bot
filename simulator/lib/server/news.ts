// Titulky zprav k trhu pro AI analytika: Google News (hledani podle trhu, posledni den) + Yahoo Finance
// (zpravy k tickeru). Obe RSS zdarma bez klice. V databazi podrzeno 15 min, aby se zdroje nebombardovaly.
import { MARKETS } from "../markets";
import type { KV } from "./kv";

const TTL = 15 * 60_000;
const MAX_AGE_H = 36;
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36";

const QUERY: Record<string, string> = {
  XAUUSD: "gold price", GAUUSD: "gold price", XAGUSD: "silver price", XPTUSD: "platinum price",
  CRUDE_OIL: "crude oil price", BRENT_OIL: "brent oil price", BTCUSD: "bitcoin price", ETHUSD: "ethereum price",
  SPX500mini: "S&P 500", US30mini: "Dow Jones", NAS100mini: "Nasdaq 100", GER_30mini: "DAX index",
  FRA_40mini: "CAC 40", EUR_50mini: "Euro Stoxx 50", ESP_35mini: "IBEX 35", GBR_100mini: "FTSE 100",
};

// Titulek musi trh zminit (Yahoo k tickeru prida i zpravy o tezarich, ETF apod.) a nesmi to byt reklama/clanek "co koupit".
const KEYS: Record<string, string> = {
  XAUUSD: "gold|bullion|xau", GAUUSD: "gold|bullion|xau", XAGUSD: "silver|xag", XPTUSD: "platinum|xpt",
  CRUDE_OIL: "oil|crude|brent|wti|opec", BRENT_OIL: "oil|crude|brent|wti|opec", BTCUSD: "bitcoin|btc|crypto",
  ETHUSD: "ethereum|ether|eth|crypto", SPX500mini: "s&p|wall street|stock market|stocks|dow|nasdaq",
  US30mini: "dow|wall street|stock market|stocks", NAS100mini: "nasdaq|tech stocks|wall street|stock market",
  GER_30mini: "dax|german|european (?:shares|stocks)", FRA_40mini: "cac|french|european (?:shares|stocks)",
  EUR_50mini: "stoxx|european (?:shares|stocks)", ESP_35mini: "ibex|spanish|spain", GBR_100mini: "ftse|london stocks|uk stocks|british stocks",
};
const CCY_NAME: Record<string, string> = {
  EUR: "euro", USD: "dollar|greenback|fed", JPY: "yen|boj", GBP: "pound|sterling|boe", AUD: "aussie|australian dollar|rba",
  CAD: "loonie|canadian dollar", CHF: "franc|snb", NZD: "kiwi|new zealand dollar", NOK: "krone|norwegian", SEK: "krona|swedish",
  ZAR: "rand", TRY: "lira",
};
const JUNK = /\b(?:drill(?:ing)?|intercepts?|exploration|market size|dividends?|stocks? to buy|buy now|price predictions?)\b/i;

function relevant(id: string) {
  const fx = id.length === 6 && !KEYS[id] ? [`${id.slice(0, 3)}/${id.slice(3)}`, id, CCY_NAME[id.slice(0, 3)], CCY_NAME[id.slice(3)]] : [];
  const re = new RegExp(`(?:^|[^a-z])(?:${(KEYS[id] ? [KEYS[id]] : fx).filter(Boolean).join("|")})(?:[^a-z]|$)`, "i");
  return (title: string) => re.test(title) && !JUNK.test(title);
}

export interface Headline { time: number; title: string }

const mem = new Map<string, { at: number; items: Headline[] }>();

function decode(s: string) {
  return s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/<[^>]+>/g, "")
    .replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(+n)).replace(/\s+/g, " ").trim();
}

async function rss(url: string): Promise<Headline[]> {
  const r = await fetch(url, { headers: { "User-Agent": UA }, cache: "no-store", signal: AbortSignal.timeout(4000) });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const xml = await r.text();
  return [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].flatMap(([, it]) => {
    const title = decode(it.match(/<title>([\s\S]*?)<\/title>/)?.[1] ?? "");
    const time = Date.parse(it.match(/<pubDate>([\s\S]*?)<\/pubDate>/)?.[1] ?? "") / 1000;
    return title && isFinite(time) ? [{ time, title }] : [];
  });
}

function query(id: string) {
  if (QUERY[id]) return QUERY[id];
  return id.length === 6 ? `"${id.slice(0, 3)}/${id.slice(3)}" OR ${id}` : MARKETS[id]?.name ?? id;
}

/** Nejnovejsi titulky k trhu (az 8, nejvys 36 h stare). Kdyz zdroje nejdou, vrati prazdny seznam. */
export async function marketNews(kv: KV | null, id: string): Promise<Headline[]> {
  const now = Date.now();
  const key = `sim:news:${id}`;
  const m = mem.get(id);
  if (m && now - m.at < TTL) return m.items;
  if (kv) {
    const [raw] = await kv.pipeline([["GET", key]]);
    const cached = typeof raw === "string" ? (JSON.parse(raw) as { at: number; items: Headline[] }) : null;
    if (cached && now - cached.at < TTL) return mem.set(id, cached), cached.items;
  }
  const q = encodeURIComponent(`${query(id)} when:1d`);
  const yahoo = MARKETS[id]?.yahoo;
  const got = await Promise.allSettled([
    rss(`https://news.google.com/rss/search?q=${q}&hl=en-US&gl=US&ceid=US:en`),
    yahoo ? rss(`https://feeds.finance.yahoo.com/rss/2.0/headline?s=${encodeURIComponent(yahoo)}&region=US&lang=en-US`) : Promise.resolve([]),
  ]);
  const seen = new Set<string>();
  const ok = relevant(id);
  const items = got.flatMap((g) => (g.status === "fulfilled" ? g.value : []))
    .filter((h) => now / 1000 - h.time < MAX_AGE_H * 3600 && ok(h.title))
    .sort((a, b) => b.time - a.time)
    .filter((h) => {
      const k = h.title.toLowerCase().replace(/ - [^-]+$/, "").replace(/\W+/g, " ").trim();
      return !seen.has(k) && !!seen.add(k);
    })
    .slice(0, 8);
  const entry = { at: now, items };
  mem.set(id, entry);
  if (kv && got.some((g) => g.status === "fulfilled")) await kv.pipeline([["SET", key, JSON.stringify(entry), "PX", TTL]]);
  return items;
}
