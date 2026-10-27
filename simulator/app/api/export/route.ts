// Stazeni vsech dat: ?format=journal|trades (CSV) nebo json, &tz=casove pasmo pro casy v CSV.
import { NextRequest, NextResponse } from "next/server";
import { exportFile } from "@/lib/exporting";
import { authMode, isAuthed } from "@/lib/server/auth";
import { exportAll } from "@/lib/server/db";
import { getKV } from "@/lib/server/kv";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const kv = getKV();
  if (!kv || authMode(kv) === "misconfigured") return NextResponse.json({ error: "no-db" }, { status: 503 });
  if (!isAuthed(req, kv)) return NextResponse.json({ error: "login" }, { status: 401 });
  const sp = req.nextUrl.searchParams;
  let tz = sp.get("tz") || "Europe/Prague";
  try {
    new Intl.DateTimeFormat("cs-CZ", { timeZone: tz });
  } catch {
    tz = "Europe/Prague";
  }
  const f = exportFile(await exportAll(kv), sp.get("format") ?? "json", tz);
  return new NextResponse(f.body, {
    headers: { "Content-Type": f.type, "Content-Disposition": `attachment; filename="${f.name}"`, "Cache-Control": "no-store" },
  });
}
