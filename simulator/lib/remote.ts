// Volani serveru z prohlizece (stav, prihlaseni, uvolneni rizeni).
import type { AiAnswer, AiContext } from "./aiPrompt";
import type { Calendar } from "./calendar";
import type { Lease, LoadResult, SaveBody } from "./types";

export interface Res<T> {
  status: number; // 0 = bez spojeni
  data: Partial<T> & { error?: string };
}

async function call<T>(url: string, init?: RequestInit): Promise<Res<T>> {
  try {
    const r = await fetch(url, { cache: "no-store", ...init });
    return { status: r.status, data: await r.json().catch(() => ({})) };
  } catch {
    return { status: 0, data: { error: "bez spojení se serverem" } as Res<T>["data"] };
  }
}

const json = (body: unknown, keepalive = false): RequestInit => ({
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), keepalive,
});

export const apiLoad = (light: boolean) => call<LoadResult>(`/api/state?journal=300${light ? "&light=1" : ""}`);
export const apiSave = (b: SaveBody, keepalive = false) =>
  call<{ ok: boolean; lease: Lease | null }>("/api/state", json(b, keepalive && JSON.stringify(b).length < 60_000));
export const apiLogin = (password: string) => call<{ ok: boolean }>("/api/login", json({ password }));
export const apiLogout = () => call<{ ok: boolean }>("/api/logout", { method: "POST" });

/** AI analytik - kdyz do 20 s neodpovi, signal se rozhodne bez nej. */
export const apiAi = (ctx: AiContext) =>
  call<AiAnswer & { model: string; news?: number }>("/api/ai-agent", { ...json(ctx), signal: AbortSignal.timeout(20_000) });

export async function apiCalendar(): Promise<Calendar | null> {
  const r = await call<Calendar>("/api/calendar");
  return r.status === 200 && r.data.releases ? { events: r.data.events ?? null, releases: r.data.releases } : null;
}

/** Co bot potrebuje od okoli: v prohlizeci pres API, na serveru (bot 24/7) primo databaze a Gemini. */
export interface Backend {
  load(light: boolean): Promise<Res<LoadResult>>;
  save(b: SaveBody, keepalive?: boolean): Promise<Res<{ ok: boolean; lease: Lease | null }>>;
  ai(ctx: AiContext): Promise<Res<AiAnswer & { model: string; news?: number }>>;
  calendar(): Promise<Calendar | null>;
}

export const browserBackend: Backend = { load: apiLoad, save: apiSave, ai: apiAi, calendar: apiCalendar };

/** Pri zavreni stranky: posledni ulozeni + uvolneni rizeni (sendBeacon dobehne i po zavreni). */
export function apiRelease(device: string, save?: SaveBody) {
  const body = JSON.stringify({ device, save: save && JSON.stringify(save).length < 60_000 ? save : undefined });
  navigator.sendBeacon?.("/api/release", new Blob([body], { type: "application/json" }));
}

/** Id teto karty (rozliseni, ktere zarizeni ridi bota). Kazda karta ma vlastni - dve karty
 *  ve stejnem prohlizeci by jinak obchodovaly obe; obnoveni stranky id zachova. */
export function deviceInfo() {
  let id = "";
  try {
    id = sessionStorage.getItem("tradingSim.device") ?? "";
    if (!id) {
      id = Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
      sessionStorage.setItem("tradingSim.device", id);
    }
  } catch {
    id = Math.random().toString(36).slice(2, 10);
  }
  const ua = typeof navigator !== "undefined" ? navigator.userAgent : "";
  return { id, label: /Mobi|Android|iPhone|iPad/i.test(ua) ? "mobil" : "počítač" };
}
