// Titulky zprav k trhu, ktere dostava AI analytik (verejne zdroje, jen se predavaji a podrzi v cache).
import { NextResponse } from "next/server";
import { MARKETS } from "@/lib/markets";
import { getKV } from "@/lib/server/kv";
import { marketNews } from "@/lib/server/news";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const id = new URL(req.url).searchParams.get("market") ?? "";
  if (!MARKETS[id]) return NextResponse.json({ error: "neznámý trh" }, { status: 400 });
  const items = await marketNews(getKV(), id);
  return NextResponse.json({ market: id, items }, { headers: { "Cache-Control": "public, s-maxage=900" } });
}
