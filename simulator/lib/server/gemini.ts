// Volani Gemini API (Google AI Studio, bezplatny plan). Klic jen na serveru (GEMINI_API_KEY).
// Nazvy modelu se v case meni - zkousi se postupne, prvni funkcni si server pamatuje.
const KEY = process.env.GEMINI_API_KEY;
const MODELS = [...new Set([process.env.GEMINI_MODEL, "gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"]
  .filter((m): m is string => !!m))];
let working: string | null = null;

export const geminiConfigured = () => !!KEY;

export async function askGemini(system: string, user: string): Promise<{ text: string; model: string }> {
  if (!KEY) throw new Error("na serveru chybí GEMINI_API_KEY");
  const order = working ? [working, ...MODELS.filter((m) => m !== working)] : MODELS;
  let last = "";
  for (const model of order) {
    const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-goog-api-key": KEY },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: system }] },
        contents: [{ role: "user", parts: [{ text: user }] }],
        generationConfig: { responseMimeType: "application/json", temperature: 0.2, maxOutputTokens: 2048 },
      }),
      cache: "no-store",
    });
    if (r.status === 429) throw new Error("vyčerpaný bezplatný limit Gemini – zkusím později");
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      last = j?.error?.message ?? `HTTP ${r.status}`;
      if (r.status === 404 || r.status === 400) continue; // model neexistuje / nepodporuje -> dalsi
      throw new Error(`Gemini: ${last}`);
    }
    const parts = (j?.candidates?.[0]?.content?.parts ?? []) as { text?: string }[];
    const text = parts.map((p) => p.text ?? "").join("").trim();
    if (!text) {
      last = j?.candidates?.[0]?.finishReason ?? "prázdná odpověď";
      continue;
    }
    working = model;
    return { text, model };
  }
  throw new Error(`Gemini: žádný model neodpověděl (${last})`);
}
