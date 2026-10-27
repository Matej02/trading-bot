// Ekonomicky kalendar pro prohlizec (verejna data, jen se predava a podrzi v cache).
import { NextResponse } from "next/server";
import { getCalendar } from "@/lib/server/calendar";
import { getKV } from "@/lib/server/kv";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return NextResponse.json({ events: await getCalendar(getKV()) }, { headers: { "Cache-Control": "public, s-maxage=1800" } });
  } catch (e) {
    return NextResponse.json({ events: [], error: (e as Error).message }, { status: 502 });
  }
}
