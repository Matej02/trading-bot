// Kontrola: titulky k trhum, vyhlasene zpravy se skutecnou hodnotou a co z toho dostane AI.
// Pouziti: npx tsx scripts/test-news.ts
import { releasesFor, releaseText } from "../lib/calendar";
import { MARKETS } from "../lib/markets";
import { getCalendar } from "../lib/server/calendar";
import { marketNews } from "../lib/server/news";

async function main() {
  const { events, releases } = await getCalendar(null);
  const now = Date.now() / 1000;
  console.log(`Kalendar: ${events?.length ?? "nedostupny"} pristich/tydennich udalosti (ForexFactory), vyhlasenych za 36 h: ${releases.length} (FXStreet)`);
  for (const e of [...releases].sort((a, b) => a.time - b.time)) {
    console.log(`   ${new Date(e.time * 1000).toISOString().slice(5, 16)} ${e.impact.padEnd(6)} ${releaseText(e)}`);
  }
  for (const id of ["EURUSD", "XAUUSD", "BTCUSD", "SPX500mini"]) {
    const n = await marketNews(null, id);
    console.log(`\n${id}: ${n.length} titulku | vyhlaseno pro trh za 24 h: ${releasesFor(releases, MARKETS[id], now - 86400, now).length}`);
    for (const h of n.slice(0, 4)) console.log(`   ${((now - h.time) / 3600).toFixed(1)} h  ${h.title.slice(0, 110)}`);
  }
}

main();
