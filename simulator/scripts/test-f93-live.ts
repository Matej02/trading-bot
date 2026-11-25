// Zivy test F93 na serveru bez databaze (KV v pameti): (1) beh runF93 s pravymi daty Yahoo + EDGAR,
// (2) shoda signalu za posledni rok z zivych dat s obchody testu (scratch/f93_sim/f93_export.py).
// Pouziti: npx tsx scripts/test-f93-live.ts "../research_data/f88/f93_parita_vstup.json"
import { readFileSync } from "node:fs";
import { f93AllSignals, F93_TICKERS, indexReturns } from "../lib/f93";
import { edgarEarnings, loadF93, runF93, yahooDaily } from "../lib/server/f93Runner";
import type { Cmd, KV } from "../lib/server/kv";

const mem = new Map<string, string>();
const kv: KV = {
  kind: "soubor",
  async pipeline(cmds: Cmd[]) {
    return cmds.map(([op, k, v, ...a]) => {
      const key = String(k);
      if (op === "GET") return mem.get(key) ?? null;
      if (op === "DEL") return mem.delete(key) ? 1 : 0;
      if (op === "SET") {
        if (a.includes("NX") && mem.has(key)) return null;
        mem.set(key, String(v));
        return "OK";
      }
      throw new Error(`neznamy prikaz ${op}`);
    });
  },
};

async function main() {
  const t0 = Date.now();
  console.log(await runF93(kv, true), `(${((Date.now() - t0) / 1000).toFixed(1)} s)`);
  const s = await loadF93(kv);
  console.log("stav:", { since: s.since, doneFor: s.doneFor, lastDay: s.lastDay, lastError: s.lastError, signaly: s.trades.length });
  console.log("druhy beh hned:", await runF93(kv));

  const J = JSON.parse(readFileSync(process.argv[2], "utf8")) as { trades: { t: string; day: string; s: number; norm: number }[] };
  const ixr = indexReturns(await yahooDaily("^GSPC"));
  const live = new Map<string, { s: number; norm: number }>();
  for (const [t, cik] of F93_TICKERS) {
    const [days, ev] = await Promise.all([yahooDaily(t), edgarEarnings(cik)]);
    for (const x of f93AllSignals(t, days, ixr, ev)) live.set(`${t}|${x.dayK}`, { s: x.dir, norm: x.res.rNorm });
  }
  const lo = "2026-03-01"; // 1 rok dat Yahoo: z potrebuje ~62 dni historie, ATR 20
  const hiTest = J.trades.reduce((m, x) => (x.day > m ? x.day : m), "");
  const test = J.trades.filter((x) => x.day >= lo);
  const liveIn = [...live.entries()].filter(([k]) => k.split("|")[1] >= lo && k.split("|")[1] <= hiTest);
  let same = 0, maxDr = 0;
  const onlyT: string[] = [];
  for (const x of test) {
    const l = live.get(`${x.t}|${x.day}`);
    if (l && l.s === x.s) { same++; maxDr = Math.max(maxDr, Math.abs(l.norm - x.norm)); } else onlyT.push(`${x.t}|${x.day}`);
  }
  const testKeys = new Set(test.map((x) => `${x.t}|${x.day}`));
  console.log(`živá data ${lo}–${hiTest}: test ${test.length}, živě ${liveIn.length}, shoda ${same}, max rozdíl R ${maxDr.toFixed(4)}`);
  console.log("  jen v testu:", onlyT.join(", ") || "-");
  console.log("  jen živě:", liveIn.filter(([k]) => !testKeys.has(k)).map(([k]) => k).join(", ") || "-");
}
main();
