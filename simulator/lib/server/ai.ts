// AI analytik na serveru: limit dotazu (bezplatny plan Gemini) + zadani + odpoved. Pouziva ho
// /api/ai-agent (prohlizec) i bot bezici na serveru.
import { buildPrompt, parseAnswer, type AiAnswer, type AiContext } from "../aiPrompt";
import type { Res } from "../remote";
import { askGemini, geminiConfigured } from "./gemini";
import type { KV } from "./kv";

export async function aiOpinion(kv: KV, ctx: AiContext): Promise<Res<AiAnswer & { model: string }>> {
  if (!geminiConfigured()) return { status: 503, data: { error: "na serveru chybí GEMINI_API_KEY" } };
  const now = new Date();
  const minuteKey = `sim:ai:min:${Math.floor(now.getTime() / 60000)}`;
  const dayKey = `sim:ai:day:${now.toISOString().slice(0, 10)}`;
  const [perMin, perDay] = await kv.pipeline([["INCR", minuteKey], ["INCR", dayKey]]);
  if (Number(perMin) === 1) await kv.pipeline([["EXPIRE", minuteKey, 120]]);
  if (Number(perDay) === 1) await kv.pipeline([["EXPIRE", dayKey, 2 * 86400]]);
  if (Number(perMin) > 12) return { status: 429, data: { error: "moc signálů najednou (limit 12/min)" } };
  if (Number(perDay) > 1000) return { status: 429, data: { error: "denní limit 1000 dotazů vyčerpán" } };
  try {
    const { system, user } = buildPrompt(ctx);
    const { text, model } = await askGemini(system, user);
    return { status: 200, data: { ...parseAnswer(text), model } };
  } catch (e) {
    return { status: 502, data: { error: (e as Error).message } };
  }
}
