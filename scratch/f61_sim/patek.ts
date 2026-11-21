// Kontrola opravy 2026-11-20: patecni signal denniho systemu se o vikendu nevetuje, hodinovy ano.
import * as fs from "fs";
import { codeOpinions } from "../../simulator/lib/agents";
import { MARKETS } from "../../simulator/lib/markets";
import { SYSTEMS } from "../../simulator/lib/strategies";

const core = JSON.parse(fs.readFileSync(process.argv[2], "utf-8")).core;
const DAY = 86400;
const fri = Date.UTC(2026, 10, 27) / 1000;           // patek 27. 11. 2026, pulnoc UTC = cas denni svicky
const sat = fri + DAY + 120;                          // sobota 00:02 UTC = zpracovani uzavrene svicky
const candles = Array.from({ length: 300 }, (_, i) => {
  const p = 24000 + Math.sin(i / 7) * 200;
  return { time: fri - (299 - i) * DAY, open: p, high: p + 150, low: p - 150, close: p };
});

function trh(sysId: string, market: string, barTime: number, now: number, tf: string) {
  const system = SYSTEMS.find((s) => s.id === sysId)!;
  const m = MARKETS[market];
  const price = candles[candles.length - 1].close;
  const ctx = {
    market: m, system, now, mid: price, candles, broker: core.broker, equity: core.broker.account.balance, settings: core.settings,
    seen: new Set<string>(), delayedMin: 0, todayTrades: 0, systemTrades: [], events: [], releases: [],
    signal: { id: `test-${sysId}`, system: sysId, market, dir: "long", price, time: now - 60, barTime, sl: price - 600, tp: null,
      reason: "test", riskPct: core.settings.riskPct },
  } as never;
  const op = codeOpinions(ctx).opinions.find((o) => o.agent === "Trh teď")!;
  console.log(`${sysId.padEnd(18)} ${tf} ${market.padEnd(11)} -> ${op.vote}: ${op.reason}`);
}

trh("f61_prelom_eu_d1", "GER_30mini", fri, sat, "1d");
trh("mr_rsi2_d1", "SPX500mini", fri, sat, "1d");
trh("f46_zlato_asie_h1", "XAUUSD", sat - 3600, sat, "1h");
trh("f61_prelom_eu_d1", "GER_30mini", fri - DAY, sat, "1d");   // ctvrtecni svicka o vikendu -> veto
