// AI analytik: posoudi jeden signal pres Gemini a vrati ANO/NE s duvodem.
// Jen pro prihlaseneho; limit 12 dotazu za minutu a 1000 denne (bezplatny plan Gemini).
import { NextRequest, NextResponse } from "next/server";
import { buildPrompt, parseAnswer, type AiContext } from "@/lib/aiPrompt";
import { authMode, isAuthed } from "@/lib/server/auth";
import { askGemini, geminiConfigured } from "@/lib/server/gemini";
import { getKV } from "@/lib/server/kv";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const kv = getKV();
  if (!kv || authMode(kv) === "misconfigured") return NextResponse.json({ error: "chybí databáze nebo heslo" }, { status: 503 });
  if (!isAuthed(req, kv)) return NextResponse.json({ error: "login" }, { status: 401 });
  if (!geminiConfigured()) return NextResponse.json({ error: "na serveru chybí GEMINI_API_KEY" }, { status: 503 });

  const now = new Date();
  const minuteKey = `sim:ai:min:${Math.floor(now.getTime() / 60000)}`;
  const dayKey = `sim:ai:day:${now.toISOString().slice(0, 10)}`;
  const [perMin, perDay] = await kv.pipeline([["INCR", minuteKey], ["INCR", dayKey]]);
  if (Number(perMin) === 1) await kv.pipeline([["EXPIRE", minuteKey, 120]]);
  if (Number(perDay) === 1) await kv.pipeline([["EXPIRE", dayKey, 2 * 86400]]);
  if (Number(perMin) > 12) return NextResponse.json({ error: "moc signálů najednou (limit 12/min)" }, { status: 429 });
  if (Number(perDay) > 1000) return NextResponse.json({ error: "denní limit 1000 dotazů vyčerpán" }, { status: 429 });

  const ctx = (await req.json().catch(() => null)) as AiContext | null;
  if (!ctx?.market || !ctx.dir) return NextResponse.json({ error: "chybí data signálu" }, { status: 400 });
  try {
    const { system, user } = buildPrompt(ctx);
    const { text, model } = await askGemini(system, user);
    return NextResponse.json({ ...parseAnswer(text), model });
  } catch (e) {
    return NextResponse.json({ error: (e as Error).message }, { status: 502 });
  }
}
