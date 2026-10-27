// Svicky z Yahoo Finance pro forex, indexy, kovy a ropu. Prohlizec na Yahoo primo
// nesmi (CORS), tak to jde pres tuhle funkci. Jen trhy ze seznamu - neni to otevrena proxy.
import { NextRequest, NextResponse } from "next/server";
import { MARKETS } from "@/lib/markets";
import { YAHOO_RANGE, yahooCandles } from "@/lib/yahoo";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const m = MARKETS[sp.get("symbol") ?? ""];
  const tf = sp.get("tf") ?? "";
  if (!m || !YAHOO_RANGE[tf]) {
    return NextResponse.json({ error: "neznamy trh nebo timeframe" }, { status: 400 });
  }
  try {
    const data = await yahooCandles(m, tf, !!sp.get("live"));
    return NextResponse.json(data, {
      headers: { "Cache-Control": tf === "1d" ? "public, s-maxage=600" : "public, s-maxage=10" },
    });
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 502 });
  }
}
