// Volani Gemini API (Google AI Studio, bezplatny plan). Klic jen na serveru (GEMINI_API_KEY).
// Nazvy modelu se v case meni - zkousi se postupne, prvni funkcni si server pamatuje.
// Pretizeny model (503 "high demand"), vycerpany limit modelu (429) nebo timeout -> zkusi se dalsi model;
// kazdy model ma v bezplatnem planu vlastni limit, Flash-Lite bezi na jine kapacite.
const KEY = process.env.GEMINI_API_KEY;
const MODELS = [...new Set([process.env.GEMINI_MODEL, "gemini-flash-latest", "gemini-2.5-flash", "gemini-flash-lite-latest",
  "gemini-2.5-flash-lite", "gemini-2.0-flash"].filter((m): m is string => !!m))];
const ATTEMPT_MS = 8000; // jeden model nejdele tolik
const TOTAL_MS = 17000; // prohlizec ceka na AI 20 s
let working: string | null = null;

export const geminiConfigured = () => !!KEY;

export async function askGemini(system: string, user: string): Promise<{ text: string; model: string }> {
  if (!KEY) throw new Error("na serveru chybí GEMINI_API_KEY");
  const order = working ? [working, ...MODELS.filter((m) => m !== working)] : MODELS;
  const start = Date.now();
  const fails: string[] = [];
  for (const model of order) {
    const left = TOTAL_MS - (Date.now() - start);
    if (left < 2000) break;
    let r: Response;
    try {
      r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-goog-api-key": KEY },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: system }] },
          contents: [{ role: "user", parts: [{ text: user }] }],
          generationConfig: { responseMimeType: "application/json", temperature: 0.2, maxOutputTokens: 2048 },
        }),
        cache: "no-store",
        signal: AbortSignal.timeout(Math.min(ATTEMPT_MS, left)),
      });
    } catch {
      fails.push(`${model}: neodpověděl včas`);
      continue;
    }
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      const why = r.status === 429 ? "vyčerpaný limit" : r.status === 503 ? "přetížený" : r.status === 404 ? "neexistuje"
        : (j?.error?.message ?? `HTTP ${r.status}`).slice(0, 80);
      fails.push(`${model}: ${why}`);
      if (r.status === 401 || r.status === 403) break; // spatny klic - dalsi model nepomuze
      continue;
    }
    const parts = (j?.candidates?.[0]?.content?.parts ?? []) as { text?: string }[];
    const text = parts.map((p) => p.text ?? "").join("").trim();
    if (!text) {
      fails.push(`${model}: ${j?.candidates?.[0]?.finishReason ?? "prázdná odpověď"}`);
      continue;
    }
    working = model;
    return { text, model };
  }
  throw new Error(`Gemini: žádný model neodpověděl (${fails.join("; ") || "nebyl čas"})`);
}
