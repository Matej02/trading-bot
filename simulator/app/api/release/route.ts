// Zavreni stranky na zarizeni, ktere ridi bota: posledni ulozeni a uvolneni rizeni
// (posila prohlizec pres sendBeacon, takze bez cekani na odpoved).
import { NextRequest, NextResponse } from "next/server";
import { authMode, isAuthed } from "@/lib/server/auth";
import { releaseLease, saveState } from "@/lib/server/db";
import { getKV } from "@/lib/server/kv";
import type { SaveBody } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const kv = getKV();
  if (!kv || authMode(kv) === "misconfigured" || !isAuthed(req, kv)) return NextResponse.json({ ok: false }, { status: 401 });
  const body = JSON.parse((await req.text()) || "{}") as { device?: string; save?: SaveBody };
  if (!body.device) return NextResponse.json({ ok: false }, { status: 400 });
  if (body.save?.device === body.device) await saveState(kv, body.save);
  await releaseLease(kv, body.device);
  return NextResponse.json({ ok: true });
}
