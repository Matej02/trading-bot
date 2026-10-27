// Backend pro bota bezicího na serveru (24/7): databaze, Gemini a kalendar primo, bez HTTP.
import type { Backend } from "../remote";
import { aiOpinion } from "./ai";
import { getCalendar } from "./calendar";
import { loadState, saveState } from "./db";
import type { KV } from "./kv";

export function serverBackend(kv: KV): Backend {
  return {
    async load(light) {
      try {
        return { status: 200, data: { ...(await loadState(kv, 300, light)), db: kv.kind, auth: "password" } };
      } catch (e) {
        return { status: 502, data: { error: (e as Error).message } };
      }
    },
    async save(b) {
      try {
        const r = await saveState(kv, b);
        return { status: r.ok ? 200 : 409, data: r };
      } catch (e) {
        return { status: 502, data: { error: (e as Error).message } };
      }
    },
    ai: (ctx) => aiOpinion(kv, ctx),
    async calendar() {
      try {
        return await getCalendar(kv);
      } catch {
        return null;
      }
    },
  };
}
