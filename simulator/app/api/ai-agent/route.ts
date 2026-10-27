// AI analytik: posoudi jeden signal pres Gemini a vrati ANO/NE s duvodem (jen pro prihlaseneho).
import { NextRequest, NextResponse } from "next/server";
import type { AiContext } from "@/lib/aiPrompt";
import { aiOpinion } from "@/lib/server/ai";
import { authMode, isAuthed } from "@/lib/server/auth";
import { getKV } from "@/lib/server/kv";

export const dynamic = "force-dynamic";
export const maxDuration = 30; // AI zkousi i nahradni modely, kdyz je Gemini pretizeny

export async function POST(req: NextRequest) {
  const kv = getKV();
  if (!kv || authMode(kv) === "misconfigured") return NextResponse.json({ error: "chybí databáze nebo heslo" }, { status: 503 });
  if (!isAuthed(req, kv)) return NextResponse.json({ error: "login" }, { status: 401 });
  const ctx = (await req.json().catch(() => null)) as AiContext | null;
  if (!ctx?.market || !ctx.dir) return NextResponse.json({ error: "chybí data signálu" }, { status: 400 });
  const r = await aiOpinion(kv, ctx);
  return NextResponse.json(r.data, { status: r.status });
}
