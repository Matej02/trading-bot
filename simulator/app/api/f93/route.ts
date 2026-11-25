// F93 (druhy den po vysledcich firem) - stav sledovani dopredu. Kdyz je na rade novy uzavreny den, nejdriv ho dopocita.
import { NextRequest, NextResponse } from "next/server";
import { authMode, isAuthed } from "@/lib/server/auth";
import { f93Due, loadF93, runF93Bounded } from "@/lib/server/f93Runner";
import { getKV } from "@/lib/server/kv";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

export async function GET(req: NextRequest) {
  const kv = getKV();
  if (!kv || authMode(kv) === "misconfigured") return NextResponse.json({ error: "no-db" }, { status: 503 });
  if (!isAuthed(req, kv)) return NextResponse.json({ error: "login" }, { status: 401 });
  let msg: string | null = null;
  if (f93Due(await loadF93(kv))) msg = await runF93Bounded(kv, 40_000);
  return NextResponse.json({ msg, state: await loadF93(kv) }, { headers: { "Cache-Control": "no-store" } });
}
