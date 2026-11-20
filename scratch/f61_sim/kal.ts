// Kontrola kalendare F61: kdy by system vstupoval (IN = zavreni predposledniho dne) a vystupoval (OUT = 3. den mesice).
import { EXCHANGE_OF, euTradingDaysLeft, isEuTradingDay } from "../../simulator/lib/euCalendar";
import { f61Exit } from "../../simulator/lib/f2x";

const DAY = 86400;
for (const mk of ["GER_30mini", "GBR_100mini", "FRA_40mini", "ESP_35mini"]) {
  const ex = EXCHANGE_OF[mk];
  const out: string[] = [];
  const c: { time: number; open: number; high: number; low: number; close: number }[] = [];
  for (let t = Date.UTC(2026, 10, 1) / 1000; t < Date.UTC(2027, 9, 1) / 1000; t += DAY) {
    if (!isEuTradingDay(ex, t)) continue;
    c.push({ time: t, open: 1, high: 1, low: 1, close: 1 });
    const d = new Date(t * 1000).toISOString().slice(0, 10);
    if (euTradingDaysLeft(ex, t) === 1) out.push(`IN ${d}`);
    if (f61Exit(c, mk)) out.push(`OUT ${d}`);
  }
  console.log(mk, out.join(" | "));
}
