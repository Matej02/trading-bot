// Kontrola oprav 2026-11-24: (2) F46 hodina vstupu podle prestavky CME, (3) minimalni lot se stropem jako runner.
import * as fs from "fs";
import { codeOpinions } from "../../simulator/lib/agents";
import { f46EntryHour, f46Signal } from "../../simulator/lib/f2x";
import { MARKETS } from "../../simulator/lib/markets";
import { SYSTEMS } from "../../simulator/lib/strategies";

const H = 3600;
const at = (iso: string) => Date.parse(iso) / 1000;
for (const [nm, iso] of [["zima (23. 11.)", "2026-11-23T12:00:00Z"], ["leto (15. 7.)", "2026-07-15T12:00:00Z"],
  ["posun USA/UK (28. 10.)", "2026-10-28T12:00:00Z"], ["posun USA/UK (18. 3. 2027)", "2027-03-18T12:00:00Z"]] as const) {
  console.log(`F46 vstupni svicka ${nm}: ${f46EntryHour(at(iso))}:00 Londyn`);
}
// pondeli 23. 11.: hodinove svicky bez 22:00 (jako GC=F), posledni uzavrena 21:00 -> signal
const mk = (t0: number, n: number) => Array.from({ length: n }, (_, i) => {
  const p = 4000 + Math.sin(i / 5) * 20;
  return { time: t0 + i * H, open: p, high: p + 5, low: p - 5, close: p };
});
const c = mk(at("2026-11-23T23:00:00Z") - 599 * H, 600).filter((x) => x.time !== at("2026-11-23T22:00:00Z"));
const lastIdx = c.findIndex((x) => x.time === at("2026-11-23T21:00:00Z"));
console.log("F46 pondeli 23. 11., posledni svicka 21:00 Londyn -> signal:", f46Signal(c.slice(0, lastIdx + 1)) ? "ANO" : "NE");
const c22 = [...c.slice(0, lastIdx + 1), { ...c[lastIdx], time: at("2026-11-23T22:00:00Z") }];
console.log("F46 pondeli 23. 11., svicka 22:00 (kdyby existovala) -> signal:", f46Signal(c22) ? "ANO (chyba, dvakrat)" : "NE");

// minimalni lot: RSI2 SPX 16. 11. (0,732 lotu), stav z exportu 24. 11.
const core = JSON.parse(fs.readFileSync(process.argv[2], "utf-8")).core;
function risk(sysId: string, market: string, price: number, sl: number) {
  const system = SYSTEMS.find((s) => s.id === sysId)!;
  const ctx = {
    market: MARKETS[market], system, now: at("2026-11-17T00:01:00Z"), mid: price, candles: [], broker: { ...core.broker, positions: [] },
    equity: core.broker.account.balance, settings: core.settings, seen: new Set<string>(), delayedMin: 0, todayTrades: 0,
    systemTrades: [], events: [], releases: [],
    signal: { id: "t", system: sysId, market, dir: "long", price, time: at("2026-11-17T00:00:00Z"), barTime: at("2026-11-16T00:00:00Z"),
      sl, tp: null, reason: "test", riskPct: core.settings.riskPct },
  } as never;
  const r = codeOpinions(ctx);
  const op = r.opinions.find((o) => o.agent === "Risk")!;
  console.log(`${sysId} ${market}: lots ${r.lots} | ${op.vote}: ${op.reason}`);
}
risk("mr_rsi2_d1", "SPX500mini", 7417, 7417 - 336);     // 0,732 lotu pri 0,25 % -> min. lot ~0,34 %
risk("mr_rsi2_d1", "NAS100mini", 27197, 27197 - 1500);  // min. lot ~1,5 % -> dal ne
risk("proraz_d1", "NAS100mini", 27197, 27197 - 1500);   // system bez stropu -> jako drive
