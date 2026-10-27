// Bot 24/7: budi ho cron (cron-job.org) kazdych 5 minut adresou /api/tick?key=TICK_SECRET.
// Ridi jen, kdyz neridi zadny prohlizec. Zamek: nejvys 1 beh za 4 minuty (i kdyby to nekdo volal porad).
import { timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";
import { Bot } from "@/lib/bot";
import { authMode } from "@/lib/server/auth";
import { serverBackend } from "@/lib/server/backend";
import { getKV } from "@/lib/server/kv";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

const SECRET = process.env.TICK_SECRET;

function keyOk(key: string | null) {
  if (!SECRET || !key) return false;
  const a = Buffer.from(key), b = Buffer.from(SECRET);
  return a.length === b.length && timingSafeEqual(a, b);
}

async function run(req: NextRequest) {
  const kv = getKV();
  if (!kv) return NextResponse.json({ ok: false, msg: "chybí databáze" }, { status: 503 });
  // lokalne bez hesla (soubor) jde spustit i bez klice; na serveru je klic povinny
  if (SECRET ? !keyOk(req.nextUrl.searchParams.get("key")) : authMode(kv) !== "open") {
    return NextResponse.json({ ok: false, msg: SECRET ? "špatný klíč" : "na serveru chybí TICK_SECRET" }, { status: SECRET ? 401 : 503 });
  }
  const [lock] = await kv.pipeline([["SET", "sim:tick:lock", String(Date.now()), "NX", "PX", 240_000]]);
  if (lock !== "OK") return NextResponse.json({ ok: true, msg: "bot běžel před chvílí – další běh nejdřív za 4 min" });
  let msg: string;
  try {
    msg = await new Bot(serverBackend(kv), { id: "server", label: "server 24/7" }).runServerTick();
  } catch (e) {
    msg = `chyba: ${(e as Error).message}`;
  }
  await kv.pipeline([["SET", "sim:tick:last", JSON.stringify({ at: Date.now(), msg })]]);
  return NextResponse.json({ ok: !msg.startsWith("chyba"), msg });
}

export const GET = run;
export const POST = run;
