// Data simulatoru v databazi. Stav (ucet, pozice, nastaveni) je jeden zaznam, historie
// se jen pridava: denik a stiny jako hash + seznam id (poradi), obchody a log jako seznam.
import type { ClosedTrade, CoreState, Deliberation, Lease, LoadResult, LogEntry, SaveBody, SaveResult, Shadow } from "../types";
import type { Cmd, KV } from "./kv";

const K = {
  core: "sim:core", jHash: "sim:journal", jIds: "sim:journal:ids", shHash: "sim:shadows", shIds: "sim:shadows:ids",
  closed: "sim:closed", log: "sim:log", lease: "sim:lease", tick: "sim:tick:last", rev: "sim:rev",
};
export const LEASE_MS = 120_000;

const parse = <T>(v: unknown): T | null => (typeof v === "string" ? (JSON.parse(v) as T) : null);
const parseAll = <T>(v: unknown): T[] => ((v as (string | null)[]) ?? []).flatMap((x) => (x ? [JSON.parse(x) as T] : []));
const unique = (ids: string[]) => [...new Set(ids)];

/**
 * Pozice se zavira jen jednou - vic radku se stejnym id je pozustatek zdvojeneho behu (10. 11. 2026
 * zavrel zastaraly prohlizec stejne pozice podruhe). Plati posledni zaznam, ten je v zustatku.
 * Vstup i vystup chronologicky.
 */
export function dedupeClosed(closed: ClosedTrade[]): ClosedTrade[] {
  const last = new Map<string, number>();
  closed.forEach((c, i) => last.set(c.id, i));
  return closed.filter((c, i) => last.get(c.id) === i);
}

async function hmget<T>(kv: KV, key: string, ids: string[]): Promise<T[]> {
  const out: T[] = [];
  for (let i = 0; i < ids.length; i += 500) {
    const [vals] = await kv.pipeline([["HMGET", key, ...ids.slice(i, i + 500)]]);
    out.push(...parseAll<T>(vals));
  }
  return out;
}

/** light = rychle obnoveni pro sledujici zarizeni (jen konec historie). */
export async function loadState(kv: KV, journal: number, light: boolean): Promise<Omit<LoadResult, "db" | "auth">> {
  const [core, jIds, jTotal, closed, log, lease, shIds, tick, rev] = await kv.pipeline([
    ["GET", K.core], ["LRANGE", K.jIds, -journal, -1], ["LLEN", K.jIds],
    ["LRANGE", K.closed, light ? -30 : -500, -1], ["LRANGE", K.log, light ? -30 : -200, -1], ["GET", K.lease],
    ["LRANGE", K.shIds, light ? -100 : 0, -1], ["GET", K.tick], ["GET", K.rev],
  ]);
  const ids = unique(jIds as string[]);
  const [entries, shadows] = await Promise.all([
    hmget<Deliberation>(kv, K.jHash, ids),
    hmget<Shadow>(kv, K.shHash, unique(shIds as string[])),
  ]);
  return {
    core: parse<CoreState>(core),
    journal: entries.reverse(),
    journalTotal: Number(jTotal) || 0,
    closed: dedupeClosed(parseAll<ClosedTrade>(closed)).reverse(),
    shadows,
    log: parseAll<LogEntry>(log).reverse(),
    lease: parse<Lease>(lease),
    now: Date.now(),
    serverTick: parse<{ at: number; msg: string }>(tick),
    rev: Number(rev) || 0,
  };
}

/**
 * Ulozi zmeny. Nic nezapise (ok=false) kdyz:
 * - bota ridi jine zarizeni a tohle ho nepreviza;
 * - zarizeni vychazi ze zastaraleho stavu (baseRev != verze na serveru), tj. mezitim ulozil nekdo
 *   jiny. Tak vznikl zdvojeny beh 10. 11. 2026: karta v pozadi ztratila rizeni, server odbavil
 *   denni momentum a karta ho po probuzeni se starym stavem udelala znovu a prepsala ucet.
 * Prevzeti a reset verzi nekontroluji (prevzeti tesne predtim nacte cerstvy stav).
 */
export async function saveState(kv: KV, b: SaveBody): Promise<SaveResult> {
  const now = Date.now();
  const [raw, rawRev] = await kv.pipeline([["GET", K.lease], ["GET", K.rev]]);
  const lease = parse<Lease>(raw);
  const rev = Number(rawRev) || 0;
  if (lease && lease.device !== b.device && lease.until > now && !b.takeover) return { ok: false, lease, rev };
  if (!b.takeover && !b.reset && b.baseRev !== rev) return { ok: false, lease, rev, stale: true };

  const mine: Lease = { device: b.device, label: b.label, until: now + LEASE_MS };
  const next = b.reset ? 1 : rev + 1;
  const cmds: Cmd[] = [];
  if (b.reset) cmds.push(...Object.values(K).map((k) => ["DEL", k]));
  cmds.push(["SET", K.lease, JSON.stringify(mine)], ["SET", K.rev, String(next)]);
  if (b.core) cmds.push(["SET", K.core, JSON.stringify(b.core)]);
  const jAll = [...(b.journalNew ?? []), ...(b.journalUpd ?? [])];
  if (jAll.length) cmds.push(["HSET", K.jHash, ...jAll.flatMap((d) => [d.id, JSON.stringify(d)])]);
  if (b.journalNew?.length) cmds.push(["RPUSH", K.jIds, ...b.journalNew.map((d) => d.id)]);
  const shAll = [...(b.shadowsNew ?? []), ...(b.shadowsUpd ?? [])];
  if (shAll.length) cmds.push(["HSET", K.shHash, ...shAll.flatMap((x) => [x.signalId, JSON.stringify(x)])]);
  if (b.shadowsNew?.length) cmds.push(["RPUSH", K.shIds, ...b.shadowsNew.map((x) => x.signalId)]);
  if (b.closed?.length) cmds.push(["RPUSH", K.closed, ...b.closed.map((c) => JSON.stringify(c))]);
  if (b.log?.length) cmds.push(["RPUSH", K.log, ...b.log.map((l) => JSON.stringify(l))], ["LTRIM", K.log, -1000, -1]);
  await kv.pipeline(cmds);
  return { ok: true, lease: mine, rev: next };
}

export async function releaseLease(kv: KV, device: string) {
  const [raw] = await kv.pipeline([["GET", K.lease]]);
  if (parse<Lease>(raw)?.device === device) await kv.pipeline([["DEL", K.lease]]);
}

/** Vsechno pro stazeni - historie chronologicky (nejstarsi prvni). */
export async function exportAll(kv: KV) {
  const [core, jIds, shIds, closed, log] = await kv.pipeline([
    ["GET", K.core], ["LRANGE", K.jIds, 0, -1], ["LRANGE", K.shIds, 0, -1], ["LRANGE", K.closed, 0, -1], ["LRANGE", K.log, 0, -1],
  ]);
  return {
    core: parse<CoreState>(core),
    journal: await hmget<Deliberation>(kv, K.jHash, unique(jIds as string[])),
    shadows: await hmget<Shadow>(kv, K.shHash, unique(shIds as string[])),
    closed: dedupeClosed(parseAll<ClosedTrade>(closed)),
    log: parseAll<LogEntry>(log),
  };
}
