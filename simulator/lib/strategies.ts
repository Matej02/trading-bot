// Strategie prevedene 1:1 z Python bota (strategy.py, strategy_bbsqueeze.py, strategy_momentum.py).
import { atr, ema, rollingMedian, rollingRankPct, rsiLast, sma, stdev } from "./indicators";
import { fmSignal, ltOf, type FmSystem } from "./fm";
import { MARKET_IDS, MARKETS } from "./markets";
import type { Candle, Dir, TF } from "./types";

export interface SystemDef {
  id: string;
  name: string;
  tf: TF;
  markets: string[];
  kind: "bar" | "momentum";
  holdsWeekends: boolean;
  desc: string;
  maxHoldBars?: number; // nejdele tolik svicek, pak se zavre za trzni cenu (jako v testu)
  noTp?: boolean; // bez TP - ven az podle pravidla vystupu (exitRule), stopu nebo casu
  exitRule?: "sma5"; // ven, kdyz denni svicka zavre nad SMA5 (long) / pod (short)
  window?: number; // kolik uzavrenych svicek dostane strategie (vychozi 400 u intradennich)
  rrr?: number; // vlastni TP v R (jinak podle nastaveni)
}

/** Experiment F9: trhy z vyzkumu (26 + krypto), na kterych byly kombinace FM konceptu testovane. */
export const FM_MARKETS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY",
  "AUDJPY", "CADJPY", "CHFJPY", "NZDJPY", "EURCAD", "GBPNZD", "XAUUSD", "XAGUSD", "SPX500mini", "NAS100mini", "US30mini",
  "GER_30mini", "GBR_100mini", "FRA_40mini", "EUR_50mini", "CRUDE_OIL", "BRENT_OIL", "BTCUSD", "ETHUSD"]
  // akciove indexy maji z Yahoo jen hodiny burzy (^GSPC...) - H4 bloky by nesedely s testem na 23h CFD, proto ven
  .filter((m) => MARKET_IDS.includes(m) && !MARKETS[m].yahoo?.startsWith("^"));
const FM_NOTE = "Experiment F9 (koncepty z FM PDF, signál na zavření H4, SL podle konceptu, TP 3R, nejdéle 8 dní). " +
  "NEOVĚŘENO – v testu 2010–2026 na 28 trzích žádná z 2 208 kombinací neprošla; tahle byla nejlepší na vývoji 2010–17. " +
  "Živě forex, kovy, ropa a krypto (21 trhů); akciové indexy ne – Yahoo dává jen hodiny burzy. ";

/** US indexy pro mean reversion (F6: vyhoda byla silnejsi uz ve vyberu do 2018). */
export const US_INDEXES = ["SPX500mini", "NAS100mini", "US30mini"];

/** Trhy, na kterych byl setup F2 testovany a overeny. */
export const F2_MARKETS = ["BTCUSD", "ETHUSD", "XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "SPX500mini", "NAS100mini", "GER_30mini"];

export const SYSTEMS: SystemDef[] = [
  {
    id: "proraz_d1", name: "Průraz 20 dní + týdenní trend (ověřeno F2)", tf: "1d", markets: F2_MARKETS, kind: "bar",
    holdsWeekends: true, maxHoldBars: 48,
    desc: "Jediný setup, který prošel ověřením: zavření nad 20denním max / pod min jen ve směru týdenního trendu, " +
      "SL 2 ATR, TP 1:2 (ověřeno 1:1,5 a 1:2). Holdout 2024–26 se swapy +0,34 R/obchod, PF 1,64, úspěšnost ~48 %, " +
      "drží ~2 týdny, ~1 obchod za 5 dní na 9 trzích.",
  },
  {
    id: "mr_rsi2_d1", name: "RSI(2) pullback – US indexy (kandidát F6)", tf: "1d", markets: US_INDEXES, kind: "bar",
    holdsWeekends: true, maxHoldBars: 10, noTp: true, exitRule: "sma5",
    desc: "Mean reversion: zavření nad SMA200 a RSI(2) pod 10 → long, ven při zavření nad SMA5, stop 3 ATR(20), " +
      "nejdéle 10 dní. F6: úspěšnost ~70 % ve všech obdobích, US indexy 2019+ PF 1,9; formálně zatím neověřeno.",
  },
  {
    id: "ukazka_ema_m1", name: "Ukázka – EMA 9/21 na 1m", tf: "1m", markets: ["BTCUSD", "ETHUSD"], kind: "bar",
    holdsWeekends: true,
    desc: "Nejčastější signály (křížení EMA 9 a 21), aby šlo pořád vidět, co agenti berou a co ne. Bez edge.",
  },
  {
    id: "ukazka_m1", name: "Ukázka – BB squeeze na 1m", tf: "1m", markets: ["BTCUSD", "ETHUSD"], kind: "bar",
    holdsWeekends: true,
    desc: "Rychlá ukázka celého toku signál → agenti → obchod na živém kryptu. Bez edge, jen na předvedení.",
  },
  {
    id: "bbsqueeze_h1", name: "BB squeeze H1", tf: "1h", markets: ["EURUSD", "AUDJPY"], kind: "bar",
    holdsWeekends: false, desc: "Průraz Bollingerových pásem po stažení, 13–17 UTC. V testu se spready neprošla.",
  },
  {
    id: "pullback_h1", name: "Pullback H1", tf: "1h", markets: ["EURUSD"], kind: "bar",
    holdsWeekends: false, desc: "Návrat k EMA20 ve směru trendu EMA50/200, 13–17 UTC. V testu se spready neprošla.",
  },
  {
    id: "fm_mss_h4", name: "FM: sweep likvidity → MSS, trend D1+H4 (experiment F9)", tf: "1h", markets: FM_MARKETS,
    kind: "bar", holdsWeekends: false, maxHoldBars: 192, window: 1000, rrr: 3,
    desc: FM_NOTE + "Sweep PDH/PDL nebo high/low Asie (SFP), do 12 H4 svíček zavření za high/low, ze kterého šel pohyb do sweepu, " +
      "jen ve směru struktury D1 i H4; SL za extrém sweepu. Test: 2010–17 +0,05 R, 2018–21 −0,06 R, 2022–26 −0,03 R (n 604).",
  },
  {
    id: "fm_pruraz_h4", name: "FM: průraz H4 pivotu, trend H4 + daily bias (experiment F9)", tf: "1h", markets: FM_MARKETS,
    kind: "bar", holdsWeekends: false, maxHoldBars: 192, window: 1000, rrr: 3,
    desc: FM_NOTE + "Zavření H4 za posledním potvrzeným pivotem (N=3, Pátek), jen ve směru struktury H4 a barvy včerejší denní svíčky " +
      "(Můčka); SL za opačný pivot. Test: 2010–17 +0,03 R, 2018–21 −0,07 R, 2022–26 −0,05 R (n 1 867).",
  },
  {
    id: "fm_zona_h4", name: "FM: S/D zóna H4 + potvrzovací svíčka, trend D1+H4 (experiment F9)", tf: "1h", markets: FM_MARKETS,
    kind: "bar", holdsWeekends: false, maxHoldBars: 192, window: 1000, rrr: 3,
    desc: FM_NOTE + "Zóna po FM (báze 1–6 malých svíček, impulz ≥ 2 ATR s BOS), první návrat, svíčka zavře zpět za proximal " +
      "(Hvězda), jen ve směru struktury D1 i H4; SL za distal. Test: 2010–17 −0,07 R, 2018–21 0,00 R, 2022–26 −0,08 R (n 323).",
  },
  {
    id: "momentum_d1_L250", name: "Momentum 250 dní (40 trhů)", tf: "1d", markets: MARKET_IDS, kind: "momentum",
    holdsWeekends: true,
    desc: "Long/short podle znaménka výnosu za 250 dní, 1× denně. Hrubě edge má, po swapu brokera ne.",
  },
];

/** Rucni BUY/SELL z grafu - jde pres agenty stejne jako signaly bota. tf se doplni podle grafu. */
export const MANUAL: SystemDef = {
  id: "rucne", name: "Ruční obchod", tf: "1m", markets: [], kind: "bar", holdsWeekends: false,
  desc: "Tvůj obchod z grafu, SL 1,5 ATR podle zobrazeného timeframu, TP podle nastaveného poměru zisk : riziko.",
};

export const SYSTEM = Object.fromEntries([...SYSTEMS, MANUAL].map((s) => [s.id, s])) as Record<string, SystemDef>;

export interface BarSignal {
  dir: Dir;
  sl: number;
  tp: number | null; // null = bez TP (system s pravidlem vystupu)
  reason: string;
}

const inSession = (t: number) => {
  const h = new Date(t * 1000).getUTCHours();
  return h >= 13 && h < 17;
};

function slTp(entry: number, a: number, dir: Dir) {
  return dir === "long" ? { sl: entry - 1.5 * a, tp: entry + 2.5 * a } : { sl: entry + 1.5 * a, tp: entry - 2.5 * a };
}

function arrays(c: Candle[]) {
  return {
    open: c.map((x) => x.open), high: c.map((x) => x.high), low: c.map((x) => x.low), close: c.map((x) => x.close),
  };
}

/**
 * Tydenni trend k posledni denni svicce (jako htf_trend v research_f2.py): tydny od nedele, jen UZAVRENE
 * tydny; +1 = tydenni close nad EMA50 a EMA50 vys nez pred 3 tydny, -1 opacne, 0 jinak.
 */
export function weeklyTrend(c: Candle[]): number {
  const decision = c[c.length - 1].time + 86400; // rozhoduje se na konci posledni denni svicky
  const weeks = new Map<number, number>();
  for (const k of c) weeks.set(Math.floor((k.time / 86400 + 4) / 7), k.close); // 1. 1. 1970 je ctvrtek
  const closes = [...weeks.entries()].filter(([w]) => (w * 7 - 4 + 7) * 86400 <= decision).map(([, v]) => v);
  if (closes.length < 54) return 0;
  const e = ema(closes, 50);
  const n = closes.length - 1;
  if (closes[n] > e[n]! && e[n]! > e[n - 3]!) return 1;
  if (closes[n] < e[n]! && e[n]! < e[n - 3]!) return -1;
  return 0;
}

/** Signal na posledni UZAVRENE svicce (c uz neobsahuje tvorici se svicku). */
export function barSignal(system: string, c: Candle[]): BarSignal | null {
  if (system.startsWith("fm_")) {
    const s = fmSignal(system as FmSystem, c);
    return s ? { dir: s.dir, sl: s.sl, tp: null, reason: s.reason } : null;
  }
  if (c.length < 150) return null;
  const { open, high, low, close } = arrays(c);
  const i = c.length - 1;
  const a = atr(high, low, close, 14);
  const aMed = rollingMedian(a, 100);
  if (a[i] == null || aMed[i] == null) return null;

  if (system === "proraz_d1") {
    const trend = weeklyTrend(c);
    const hi = Math.max(...high.slice(i - 20, i));
    const lo = Math.min(...low.slice(i - 20, i));
    const d = 2 * a[i]!;
    if (close[i] > hi && trend === 1) {
      return { dir: "long", sl: close[i] - d, tp: close[i] + 2 * d,
        reason: `Denní svíčka zavřela nad 20denním maximem (${hi}) a týdenní trend je nahoru (cena nad rostoucí EMA50).` };
    }
    if (close[i] < lo && trend === -1) {
      return { dir: "short", sl: close[i] + d, tp: close[i] - 2 * d,
        reason: `Denní svíčka zavřela pod 20denním minimem (${lo}) a týdenní trend je dolů (cena pod klesající EMA50).` };
    }
    return null;
  }

  if (system === "mr_rsi2_d1") {
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
    const up = mid.map((m, k) => (m == null || sd[k] == null ? null : m + 2 * sd[k]!));
    const lo = mid.map((m, k) => (m == null || sd[k] == null ? null : m - 2 * sd[k]!));
    const width = up.map((u, k) => (u == null || lo[k] == null ? null : (u - lo[k]!) / mid[k]!));
    const rank = rollingRankPct(width, 100);
    if (rank[i] == null || rank[i - 1] == null) return null;
    if (system === "bbsqueeze_h1" && !inSession(c[i].time)) return null; // ukazka jede nonstop
    if (rank[i - 1]! > 0.25) return null;
    const pct = Math.round(rank[i - 1]! * 100);
    if (close[i] > up[i]!) {
      return { dir: "long", ...slTp(close[i], a[i]!, "long"),
        reason: `Po stažení pásem (šířka v nejužších ${pct} % za 100 svíček) zavřela svíčka nad horním pásmem.` };
    }
    if (close[i] < lo[i]!) {
      return { dir: "short", ...slTp(close[i], a[i]!, "short"),
        reason: `Po stažení pásem (šířka v nejužších ${pct} % za 100 svíček) zavřela svíčka pod dolním pásmem.` };
    }
    return null;
  }

  if (system === "ukazka_ema_m1") {
    const e9 = ema(close, 9), e21 = ema(close, 21);
    if (e9[i]! > e21[i]! && e9[i - 1]! <= e21[i - 1]!) {
      return { dir: "long", ...slTp(close[i], a[i]!, "long"), reason: "EMA9 překřížila EMA21 zdola nahoru." };
    }
    if (e9[i]! < e21[i]! && e9[i - 1]! >= e21[i - 1]!) {
      return { dir: "short", ...slTp(close[i], a[i]!, "short"), reason: "EMA9 překřížila EMA21 shora dolů." };
    }
    return null;
  }

  if (system === "pullback_h1") {
    const e20 = ema(close, 20), e50 = ema(close, 50), e200 = ema(close, 200);
    if (a[i]! < 0.6 * aMed[i]!) return null;
    if (!inSession(c[i].time)) return null;
    const up = e50[i]! > e200[i]!, down = e50[i]! < e200[i]!;
    const pbUp = low[i - 1] <= e20[i - 1]! && close[i] > e20[i]!;
    const pbDown = high[i - 1] >= e20[i - 1]! && close[i] < e20[i]!;
    if (up && pbUp && close[i] > open[i]) {
      return { dir: "long", ...slTp(close[i], a[i]!, "long"),
        reason: "Uptrend (EMA50 nad EMA200), cena se stáhla k EMA20 a zavřela zpět nad ní rostoucí svíčkou." };
    }
    if (down && pbDown && close[i] < open[i]) {
      return { dir: "short", ...slTp(close[i], a[i]!, "short"),
        reason: "Downtrend (EMA50 pod EMA200), cena se stáhla k EMA20 a zavřela zpět pod ní klesající svíčkou." };
    }
    return null;
  }
  return null;
}

export type Tone = "wait" | "near" | "off";

/** Lidsky popis, na co strategie na posledni uzavrene svicce ceka (panel "Bot zive"). */
export function barStatus(system: string, c: Candle[], digits: number): { text: string; tone: Tone } {
  if (c.length < 150) return { text: `načítám data (${c.length}/150 svíček)`, tone: "off" };
  if (system.startsWith("fm_")) {
    const lt = ltOf(c[c.length - 1].time);
    const h = Math.floor((((lt % 14400) + 14400) % 14400) / 3600);
    return { text: `experiment F9 – vyhodnocuje se na zavření H4 bloku (za ${3 - h} h)`, tone: "wait" };
  }
  const { high, low, close } = arrays(c);
  const i = c.length - 1;
  const f = (v: number) => v.toFixed(digits);
  const hour = new Date(c[i].time * 1000).getUTCHours();
  const sessionRule = system === "bbsqueeze_h1" || system === "pullback_h1";
  if (sessionRule && !inSession(c[i].time)) {
    return { text: `mimo obchodní okno 13–17 UTC (poslední svíčka ${hour}:00 UTC)`, tone: "off" };
  }
  if (system === "mr_rsi2_d1") {
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
    const width = mid.map((m, k) => (m == null || sd[k] == null ? null : (4 * sd[k]!) / m));
    const rank = rollingRankPct(width, 100);
    if (rank[i - 1] == null) return { text: "málo dat pro pásma", tone: "off" };
    const pct = Math.round(rank[i - 1]! * 100);
    if (rank[i - 1]! > 0.25) return { text: `pásma nejsou stažená (šířka v ${pct} % rozsahu, potřeba ≤ 25 %)`, tone: "wait" };
    return {
      text: `pásma stažená (${pct} %) – čeká na zavření nad ${f(mid[i]! + 2 * sd[i]!)} nebo pod ${f(mid[i]! - 2 * sd[i]!)} (teď ${f(close[i])})`,
      tone: "near",
    };
  }
  if (system === "proraz_d1") {
    const trend = weeklyTrend(c);
    // dalsi denni svicka musi zavrit za extremem poslednich 20 dni (vcetne te posledni)
    const hi = Math.max(...high.slice(i - 19, i + 1));
    const lo = Math.min(...low.slice(i - 19, i + 1));
    if (trend === 1) {
      const a = atr(high, low, close, 14)[i] ?? 0;
      return { text: `týdenní trend nahoru – long při denním zavření nad ${f(hi)} (teď ${f(close[i])})`, tone: hi - close[i] < a ? "near" : "wait" };
    }
    if (trend === -1) {
      const a = atr(high, low, close, 14)[i] ?? 0;
      return { text: `týdenní trend dolů – short při denním zavření pod ${f(lo)} (teď ${f(close[i])})`, tone: close[i] - lo < a ? "near" : "wait" };
    }
    return { text: "týdenní trend nejasný (cena kolem týdenní EMA50) – neobchoduje", tone: "off" };
  }
  if (system === "ukazka_ema_m1") {
    const e9 = ema(close, 9), e21 = ema(close, 21);
    const gap = e9[i]! - e21[i]!;
    const a = atr(high, low, close, 14)[i] ?? 0;
    const near = a > 0 && Math.abs(gap) < 0.3 * a;
    return {
      text: `EMA9 ${gap > 0 ? "nad" : "pod"} EMA21 o ${f(Math.abs(gap))} – signál při překřížení${near ? " (blízko)" : ""}`,
      tone: near ? "near" : "wait",
    };
  }
  if (system === "pullback_h1") {
    const e20 = ema(close, 20), e50 = ema(close, 50), e200 = ema(close, 200);
    const a = atr(high, low, close, 14), med = rollingMedian(a, 100);
    if (a[i] != null && med[i] != null && a[i]! < 0.6 * med[i]!) return { text: "trh spí (ATR pod 60 % mediánu)", tone: "off" };
    const trend = e50[i]! > e200[i]! ? "uptrend" : "downtrend";
    return { text: `${trend} – čeká na stažení k EMA20 (${f(e20[i]!)}) a zavření zpět ve směru trendu (teď ${f(close[i])})`, tone: "wait" };
  }
  return { text: "", tone: "off" };
}

/** ATR(14) posledni uzavrene svicky - pro SL/TP rucniho obchodu. */
export function lastAtr(c: Candle[]): number | null {
  const { high, low, close } = arrays(c);
  return atr(high, low, close, 14)[c.length - 1] ?? null;
}

/** SL 1.5 ATR, TP = rrr x vzdalenost SL. */
export function manualLevels(entry: number, a: number, dir: Dir, rrr: number) {
  const d = 1.5 * a, s = dir === "long" ? 1 : -1;
  return { sl: entry - s * d, tp: entry + s * rrr * d };
}

// --- momentum (strategy_momentum.py)
export const MOM_LOOKBACK = 250;
export const MOM_VOL_WINDOW = 60;
export const MOM_SL_SIGMA = 10;
export const MOM_RISK_PCT = (0.5 / Math.sqrt(40)) * MOM_SL_SIGMA; // ~0.79 % na trh u pojistneho SL

/** +1 / -1 podle znamenka vynosu za 250 obchodnich dni, 0 = malo dat. */
export function momentumTarget(closes: number[]): number {
  if (closes.length < MOM_LOOKBACK + 1) return 0;
  return Math.sign(closes[closes.length - 1] / closes[closes.length - 1 - MOM_LOOKBACK] - 1);
}

export function momentumReturn(closes: number[]): number {
  return closes[closes.length - 1] / closes[closes.length - 1 - MOM_LOOKBACK] - 1;
}

/** Denni volatilita jako podil ceny (std dennich zmen za 60 dni, ddof=1). */
export function relVol(closes: number[]): number {
  const r = closes.slice(-MOM_VOL_WINDOW - 1).map((v, i, a) => (i ? v / a[i - 1] - 1 : NaN)).slice(1);
  const m = r.reduce((x, y) => x + y, 0) / r.length;
  return Math.sqrt(r.reduce((x, y) => x + (y - m) ** 2, 0) / (r.length - 1));
}

/** Uzavrene denni close pro momentum: bez dnesni svicky, u krypta jen pracovni dny. */
export function dailyCloses(c: Candle[], crypto: boolean, now: number): number[] {
  const today = Math.floor(now / 86400) * 86400;
  return c
    .filter((x) => x.time < today && (!crypto || ((new Date(x.time * 1000).getUTCDay() + 6) % 7) < 5))
    .map((x) => x.close);
}
