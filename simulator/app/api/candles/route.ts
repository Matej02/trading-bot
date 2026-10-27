// Svicky z Yahoo Finance pro forex, indexy, kovy a ropu. Prohlizec na Yahoo primo
// nesmi (CORS), tak to jde pres tuhle funkci. Jen trhy ze seznamu - neni to otevrena proxy.
import { NextRequest, NextResponse } from "next/server";
import { MARKETS } from "@/lib/markets";

export const dynamic = "force-dynamic";

// [plna historie, kratke doplneni pri zivem obnovovani]
const RANGE: Record<string, [string, string]> = {
  "1m": ["5d", "1d"], "5m": ["1mo", "5d"], "15m": ["1mo", "5d"], "1h": ["1y", "5d"], "1d": ["5y", "1mo"],
};
const INTERVAL: Record<string, string> = { "1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "1d": "1d" };

type Num = number | null;

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const m = MARKETS[sp.get("symbol") ?? ""];
  const tf = sp.get("tf") ?? "";
  if (!m || !RANGE[tf]) {
    return NextResponse.json({ error: "neznamy trh nebo timeframe" }, { status: 400 });
  }
  const range = RANGE[tf][sp.get("live") ? 1 : 0];
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(m.yahoo)}` +
    `?interval=${INTERVAL[tf]}&range=${range}&includePrePost=false`;

  let r: Response;
  try {
    r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0" }, cache: "no-store" });
  } catch {
    return NextResponse.json({ error: "Yahoo neodpovida" }, { status: 502 });
  }
  if (!r.ok) return NextResponse.json({ error: `Yahoo vratilo ${r.status}` }, { status: 502 });

  const j = await r.json();
  const res = j?.chart?.result?.[0];
  if (!res?.timestamp) return NextResponse.json({ candles: [], delayed: 0 });
  const q = res.indicators.quote[0] as { open: Num[]; high: Num[]; low: Num[]; close: Num[] };
  // datum obchodniho dne v case burzy, vcetne letniho casu (pevny gmtoffset by v lete posunul den)
  const localDate = new Intl.DateTimeFormat("en-CA", { timeZone: res.meta.exchangeTimezoneName ?? "UTC" });

  const byTime = new Map<number, { time: number; open: number; high: number; low: number; close: number }>();
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
    const live = candles[candles.length - 1];
    const prev = candles[candles.length - 2];
    const off = ((prev.time % sec) + sec) % sec;
    if ((live.time - off) % sec !== 0) {
      const aligned = Math.floor((live.time - off) / sec) * sec + off;
      if (aligned === prev.time) {
        candles.pop();
        prev.close = live.close;
        prev.high = Math.max(prev.high, live.high);
        prev.low = Math.min(prev.low, live.low);
      } else {
        live.time = aligned;
      }
    }
  }

  return NextResponse.json(
    { candles, delayed: Math.round((res.meta.exchangeDataDelayedBy ?? 0) / 60) },
    { headers: { "Cache-Control": tf === "1d" ? "public, s-maxage=600" : "public, s-maxage=10" } },
  );
}
