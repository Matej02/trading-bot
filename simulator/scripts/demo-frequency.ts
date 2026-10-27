// Jak casto da ukazkova strategie signal na zivych 1m datech z Binance (poslednich ~1000 minut)?
// Pouziti: npx tsx scripts/demo-frequency.ts
import { barSignal } from "../lib/strategies";

async function main() {
  for (const sym of ["BTCUSDT", "ETHUSDT"]) {
    const rows: (string | number)[][] = await (await fetch(
      `https://data-api.binance.vision/api/v3/klines?symbol=${sym}&interval=1m&limit=1000`)).json();
    const c = rows.map((k) => ({ time: Number(k[0]) / 1000, open: +k[1], high: +k[2], low: +k[3], close: +k[4] })).slice(0, -1);
    let n = 0;
    for (let i = 150; i < c.length; i++) if (barSignal("ukazka_m1", c.slice(Math.max(0, i - 399), i + 1))) n++;
    console.log(`${sym}: ${n} signalu za ${c.length - 150} minut (~${((n / (c.length - 150)) * 60).toFixed(1)} za hodinu)`);
  }
}

main();
