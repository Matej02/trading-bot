// Prihlaseni heslem z APP_PASSWORD. Max 10 pokusu za 15 minut z jedne adresy.
import { NextRequest, NextResponse } from "next/server";
import { authMode, checkPassword, COOKIE, makeSession, SESSION_DAYS } from "@/lib/server/auth";
import { getKV } from "@/lib/server/kv";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const kv = getKV();
  const mode = authMode(kv);
  if (mode === "open") return NextResponse.json({ ok: true });
  if (!kv || mode === "misconfigured") return NextResponse.json({ error: "Na serveru chybí databáze nebo APP_PASSWORD." }, { status: 503 });

  const ip = (req.headers.get("x-forwarded-for") ?? "local").split(",")[0].trim();
  const key = `sim:rl:${ip}`;
  const [tries] = await kv.pipeline([["INCR", key]]);
  if (Number(tries) === 1) await kv.pipeline([["EXPIRE", key, 900]]);
  if (Number(tries) > 10) return NextResponse.json({ error: "Moc pokusů – zkus to za 15 minut." }, { status: 429 });

  const { password } = (await req.json().catch(() => ({}))) as { password?: string };
  if (!checkPassword(String(password ?? ""))) return NextResponse.json({ error: "Špatné heslo." }, { status: 401 });

  const res = NextResponse.json({ ok: true });
  res.cookies.set(COOKIE, makeSession(), {
    httpOnly: true, sameSite: "lax", secure: process.env.NODE_ENV === "production" && !!process.env.VERCEL, path: "/",
    maxAge: SESSION_DAYS * 86400,
  });
  return res;
}
