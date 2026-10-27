// Ulozeni dat na serveru: Upstash Redis (na Vercelu), lokalne bez databaze soubor .data/store.json.
// Pouziva se jen malá podmnozina prikazu Redisu, aby sel soubor napodobit.
import { promises as fs } from "node:fs";
import path from "node:path";

export type Cmd = (string | number)[];

export interface KV {
  kind: "upstash" | "soubor";
  pipeline(cmds: Cmd[]): Promise<unknown[]>;
}

export const KV_URL = process.env.KV_REST_API_URL ?? process.env.UPSTASH_REDIS_REST_URL;
export const KV_TOKEN = process.env.KV_REST_API_TOKEN ?? process.env.UPSTASH_REDIS_REST_TOKEN;

function upstash(): KV {
  return {
    kind: "upstash",
    async pipeline(cmds) {
      if (!cmds.length) return [];
      const r = await fetch(`${KV_URL}/pipeline`, {
        method: "POST",
        headers: { Authorization: `Bearer ${KV_TOKEN}`, "Content-Type": "application/json" },
        body: JSON.stringify(cmds.map((c) => c.map(String))),
        cache: "no-store",
      });
      if (!r.ok) throw new Error(`databáze vrátila ${r.status}`);
      const out = (await r.json()) as { result?: unknown; error?: string }[];
      return out.map((x) => {
        if (x.error) throw new Error(`databáze: ${x.error}`);
        return x.result ?? null;
      });
    },
  };
}

// ---------------------------------------------------------- lokalni soubor

type Entry = { t: "s"; v: string; exp?: number } | { t: "l"; v: string[] } | { t: "h"; v: Record<string, string> };
const FILE = path.join(process.cwd(), ".data", "store.json");
const WRITES = new Set(["SET", "DEL", "RPUSH", "LTRIM", "HSET", "INCR", "EXPIRE"]);
let data: Record<string, Entry> | null = null;
let queue: Promise<unknown> = Promise.resolve();

function idx(n: number, len: number) {
  return n < 0 ? Math.max(len + n, 0) : Math.min(n, len);
}

function exec(d: Record<string, Entry>, cmd: Cmd): unknown {
  const [op, key, ...a] = cmd.map(String);
  let e = d[key];
  if (e?.t === "s" && e.exp && Date.now() > e.exp) {
    delete d[key];
    e = undefined as unknown as Entry;
  }
  switch (op.toUpperCase()) {
    case "GET":
      return e?.t === "s" ? e.v : null;
    case "SET": {
      const nx = a.includes("NX");
      if (nx && e) return null;
      const px = a.indexOf("PX");
      d[key] = { t: "s", v: a[0], exp: px >= 0 ? Date.now() + Number(a[px + 1]) : undefined };
      return "OK";
    }
    case "DEL":
      return delete d[key] ? 1 : 0;
    case "INCR": {
      const v = (e?.t === "s" ? Number(e.v) : 0) + 1;
      d[key] = { t: "s", v: String(v), exp: e?.t === "s" ? e.exp : undefined };
      return v;
    }
    case "EXPIRE":
      if (e?.t === "s") e.exp = Date.now() + Number(a[0]) * 1000;
      return e ? 1 : 0;
    case "RPUSH": {
      const l = e?.t === "l" ? e : (d[key] = { t: "l", v: [] });
      l.v.push(...a);
      return l.v.length;
    }
    case "LLEN":
      return e?.t === "l" ? e.v.length : 0;
    case "LRANGE": {
      if (e?.t !== "l") return [];
      const len = e.v.length;
      return e.v.slice(idx(Number(a[0]), len), idx(Number(a[1]), len - 1) + 1);
    }
    case "LTRIM": {
      if (e?.t !== "l") return "OK";
      const len = e.v.length;
      e.v = e.v.slice(idx(Number(a[0]), len), idx(Number(a[1]), len - 1) + 1);
      return "OK";
    }
    case "HSET": {
      const h = e?.t === "h" ? e : (d[key] = { t: "h", v: {} });
      let added = 0;
      for (let i = 0; i + 1 < a.length; i += 2) {
        if (!(a[i] in h.v)) added++;
        h.v[a[i]] = a[i + 1];
      }
      return added;
    }
    case "HMGET":
      return a.map((f) => (e?.t === "h" ? e.v[f] ?? null : null));
    case "HGETALL":
      return e?.t === "h" ? Object.entries(e.v).flat() : [];
    case "HLEN":
      return e?.t === "h" ? Object.keys(e.v).length : 0;
    default:
      throw new Error(`soubor neumí ${op}`);
  }
}

function fileKV(): KV {
  return {
    kind: "soubor",
    pipeline(cmds) {
      const run = queue.then(async () => {
        if (!data) {
          try {
            data = JSON.parse(await fs.readFile(FILE, "utf8"));
          } catch {
            data = {};
          }
        }
        const res = cmds.map((c) => exec(data!, c));
        if (cmds.some((c) => WRITES.has(String(c[0]).toUpperCase()))) {
          await fs.mkdir(path.dirname(FILE), { recursive: true });
          await fs.writeFile(`${FILE}.tmp`, JSON.stringify(data));
          await fs.rename(`${FILE}.tmp`, FILE);
        }
        return res;
      });
      queue = run.catch(() => {});
      return run;
    },
  };
}

let kv: KV | null | undefined;

/** Upstash, kdyz je pripojeny; jinak soubor - ale jen mimo Vercel (tam se soubory nedrzi). */
export function getKV(): KV | null {
  if (kv === undefined) kv = KV_URL && KV_TOKEN ? upstash() : process.env.VERCEL ? null : fileKV();
  return kv;
}
