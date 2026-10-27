// Kontrola: stahne bot na serveru (bez prohlizece) data z Yahoo i Binance a spocita signal F2?
// Pouziti: npx tsx scripts/test-server-data.ts
import { closedCandles, fetchCandles, nowSec } from "../lib/data";
import { MARKETS } from "../lib/markets";
import { barSignal, barStatus } from "../lib/strategies";

async function main() {
  for (const id of ["XAUUSD", "SPX500mini", "BTCUSD"]) {
    const m = MARKETS[id];
    const { candles, delayed } = await fetchCandles(m, "1d");
    const closed = closedCandles(candles, "1d", nowSec());
    const last = closed[closed.length - 1];
    console.log(`${id}: ${closed.length} uzavrenych dennich svicek, posledni ${new Date(last.time * 1000).toISOString().slice(0, 10)} ` +
      `close ${last.close}, zpozdeni ${delayed} min | stav: ${barStatus("proraz_d1", closed, m.digits).text || "-"} | ` +
      `signal: ${barSignal("proraz_d1", closed)?.dir ?? "zadny"}`);
  }
}

main();
