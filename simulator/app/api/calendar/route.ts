// Ekonomicky kalendar pro prohlizec (verejna data, jen se predava a podrzi v cache).
import { NextResponse } from "next/server";
import { getCalendar } from "@/lib/server/calendar";
import { getKV } from "@/lib/server/kv";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const cal = await getCalendar(getKV());
    const ok = !!cal.events || cal.releases.length > 0;
    // kdyz ForexFactory nejde, kratka cache - at se kalendar brzy zkusi znovu
    const cache = cal.events ? "public, s-maxage=300" : "public, s-maxage=60";
    return NextResponse.json(cal, { status: ok ? 200 : 502, headers: ok ? { "Cache-Control": cache } : {} });
  } catch (e) {
    return NextResponse.json({ events: [], releases: [], error: (e as Error).message }, { status: 502 });
  }
}
