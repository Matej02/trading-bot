"""Prida do simulatoru kandidata F6: RSI(2) pullback long na US indexech (vystup nad SMA5, bez TP)."""
import json
import os

os.chdir(r"D:\Trading bot\simulator")


def edit(p, pairs):
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert old in s, (p, old[:80])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(s)


edit("lib/strategies.ts", [
    ('import { atr, ema, rollingMedian, rollingRankPct, sma, stdev } from "./indicators";',
     'import { atr, ema, rollingMedian, rollingRankPct, rsiLast, sma, stdev } from "./indicators";'),
    ("""  maxHoldBars?: number; // nejdele tolik svicek, pak se zavre za trzni cenu (jako v testu)
}""", """  maxHoldBars?: number; // nejdele tolik svicek, pak se zavre za trzni cenu (jako v testu)
  noTp?: boolean; // bez TP - ven az podle pravidla vystupu (exitRule), stopu nebo casu
  exitRule?: "sma5"; // ven, kdyz denni svicka zavre nad SMA5 (long) / pod (short)
}

/** US indexy pro mean reversion (F6: vyhoda byla silnejsi uz ve vyberu do 2018). */
export const US_INDEXES = ["SPX500mini", "NAS100mini", "US30mini"];"""),
    ("""  {
    id: "ukazka_ema_m1",""", """  {
    id: "mr_rsi2_d1", name: "RSI(2) pullback – US indexy (kandidát F6)", tf: "1d", markets: US_INDEXES, kind: "bar",
    holdsWeekends: true, maxHoldBars: 10, noTp: true, exitRule: "sma5",
    desc: "Mean reversion: zavření nad SMA200 a RSI(2) pod 10 → long, ven při zavření nad SMA5, stop 3 ATR(20), " +
      "nejdéle 10 dní. F6: úspěšnost ~70 % ve všech obdobích, US indexy 2019+ PF 1,9; formálně zatím neověřeno.",
  },
  {
    id: "ukazka_ema_m1","""),
    ("""  if (system === "bbsqueeze_h1" || system === "ukazka_m1") {
    const mid = sma(close, 20);
    const sd = stdev(close, 20);
    const up = mid.map""", """  if (system === "mr_rsi2_d1") {
    const s200 = sma(close, 200);
    const r2 = rsiLast(close, 2);
    const a20 = atr(high, low, close, 20);
    if (s200[i] == null || r2 == null || a20[i] == null) return null;
    if (close[i] > s200[i]! && r2 < 10) {
      return { dir: "long", sl: close[i] - 3 * a20[i]!, tp: null,
        reason: `Pullback v uptrendu: zavření nad SMA200 a RSI(2) ${r2.toFixed(1)} < 10. Ven při zavření nad SMA5, stop 3 ATR, nejdéle 10 dní.` };
    }
    return null;
  }

  if (system === "bbsqueeze_h1" || system === "ukazka_m1") {
    const mid = sma(close, 20);
    const sd = stdev(close, 20);
    const up = mid.map"""),
    ("""  if (system === "bbsqueeze_h1" || system === "ukazka_m1") {
    const mid = sma(close, 20);
    const sd = stdev(close, 20);
    const width""", """  if (system === "mr_rsi2_d1") {
    const s200 = sma(close, 200);
    const r2 = rsiLast(close, 2);
    if (s200[i] == null || r2 == null) return { text: "málo dat (SMA200)", tone: "off" };
    if (close[i] <= s200[i]!) return { text: `pod SMA200 (${f(s200[i]!)}) – neobchoduje`, tone: "off" };
    return { text: `nad SMA200 · RSI(2) ${r2.toFixed(1)} – long, až RSI(2) při zavření klesne pod 10 (teď ${f(close[i])})`,
      tone: r2 < 25 ? "near" : "wait" };
  }
  if (system === "bbsqueeze_h1" || system === "ukazka_m1") {
    const mid = sma(close, 20);
    const sd = stdev(close, 20);
    const width"""),
])

# BarSignal.tp muze byt null
s = open("lib/strategies.ts", encoding="utf-8").read()
import re
m = re.search(r"export interface BarSignal \{[^}]*\}", s)
print(m.group(0))
open("lib/strategies.ts", "w", encoding="utf-8").write(s)
