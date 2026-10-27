// Prihlaseni jednim heslem (APP_PASSWORD ve Vercelu). Relace = podepsana cookie na 30 dni.
import { createHash, createHmac, timingSafeEqual } from "node:crypto";
import type { NextRequest } from "next/server";
import { KV_TOKEN, type KV } from "./kv";

export const COOKIE = "sim_session";
export const SESSION_DAYS = 30;
const PASSWORD = process.env.APP_PASSWORD;

/** open = lokalni soubor bez hesla, password = vyzaduje prihlaseni, misconfigured = databaze bez hesla */
export function authMode(kv: KV | null): "open" | "password" | "misconfigured" {
  if (PASSWORD) return "password";
  return kv?.kind === "soubor" ? "open" : "misconfigured";
}

// klic pro podpis: zmena hesla odhlasi vsechna zarizeni
const secret = () => createHash("sha256").update(`${PASSWORD}|${KV_TOKEN ?? "local"}|trading-simulator`).digest();
const sign = (exp: string) => createHmac("sha256", secret()).update(exp).digest("base64url");

export function makeSession() {
  const exp = String(Math.floor(Date.now() / 1000) + SESSION_DAYS * 86400);
  return `${exp}.${sign(exp)}`;
}

function validSession(v: string | undefined) {
  const [exp, sig] = (v ?? "").split(".");
  if (!exp || !sig || Number(exp) < Date.now() / 1000) return false;
  const a = Buffer.from(sig), b = Buffer.from(sign(exp));
  return a.length === b.length && timingSafeEqual(a, b);
}

export function checkPassword(p: string) {
  if (!PASSWORD) return false;
  const a = createHash("sha256").update(p).digest();
  const b = createHash("sha256").update(PASSWORD).digest();
  return timingSafeEqual(a, b);
}

export function isAuthed(req: NextRequest, kv: KV | null) {
  const mode = authMode(kv);
  return mode === "open" || (mode === "password" && validSession(req.cookies.get(COOKIE)?.value));
}
