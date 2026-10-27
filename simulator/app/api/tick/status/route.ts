// Kdy naposledy budik (cron) spustil bota na serveru - jen cas a stav, bez dat uctu (verejne kvuli kontrole cronu).
import { NextResponse } from "next/server";
import { getKV } from "@/lib/server/kv";

export const dynamic = "force-dynamic";

export async function GET() {
  const kv = getKV();
  if (!kv) return NextResponse.json({ ok: false, msg: "chybí databáze" }, { status: 503 });
  const [raw] = await kv.pipeline([["GET", "sim:tick:last"]]);
  const last = typeof raw === "string" ? (JSON.parse(raw) as { at: number; msg: string }) : null;
  if (!last) return NextResponse.json({ ok: false, msg: "cron bota zatím nikdy nespustil" });
  const state = last.msg.startsWith("chyba") ? "chyba" : last.msg.includes("čeká") ? "čeká – bota řídí otevřená stránka" : "řídil server";
  return NextResponse.json({ ok: true, lastAt: new Date(last.at).toISOString(), agoMin: Math.round((Date.now() - last.at) / 60_000), state },
    { headers: { "Cache-Control": "no-store" } });
}
