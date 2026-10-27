// Stav simulatoru na serveru: GET nacte (vcetne historie), POST ulozi zmeny od zarizeni, ktere ridi bota.
import { NextRequest, NextResponse } from "next/server";
import { authMode, isAuthed } from "@/lib/server/auth";
import { loadState, saveState } from "@/lib/server/db";
import { getKV } from "@/lib/server/kv";
import type { SaveBody } from "@/lib/types";

export const dynamic = "force-dynamic";

function gate(req: NextRequest) {
  const kv = getKV();
  if (!kv) return { res: NextResponse.json({ error: "no-db" }, { status: 503 }) };
  const mode = authMode(kv);
  if (mode === "misconfigured") return { res: NextResponse.json({ error: "no-password" }, { status: 503 }) };
  if (!isAuthed(req, kv)) return { res: NextResponse.json({ error: "login" }, { status: 401 }) };
  return { kv, mode };
}

export async function GET(req: NextRequest) {
  const g = gate(req);
  if (!g.kv) return g.res;
  const sp = req.nextUrl.searchParams;
  const journal = Math.min(Math.max(Number(sp.get("journal")) || 300, 1), 1000);
  try {
    const data = await loadState(g.kv, journal, sp.get("light") === "1");
    return NextResponse.json({ ...data, db: g.kv.kind, auth: g.mode });
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 502 });
  }
}

export async function POST(req: NextRequest) {
  const g = gate(req);
  if (!g.kv) return g.res;
  const body = (await req.json().catch(() => null)) as SaveBody | null;
  if (!body || typeof body.device !== "string" || !body.device) {
    return NextResponse.json({ error: "chybí zařízení" }, { status: 400 });
  }
  try {
    const r = await saveState(g.kv, body);
    return NextResponse.json(r, { status: r.ok ? 200 : 409 });
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 502 });
  }
}
