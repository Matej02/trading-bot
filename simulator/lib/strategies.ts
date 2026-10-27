// Strategie prevedene 1:1 z Python bota (strategy.py, strategy_bbsqueeze.py, strategy_momentum.py).
import { atr, ema, rollingMedian, rollingRankPct, sma, stdev } from "./indicators";
import { MARKET_IDS } from "./markets";
import type { Candle, Dir, TF } from "./types";

export interface SystemDef {
  id: string;
  name: string;
  tf: TF;
  markets: string[];
  kind: "bar" | "momentum";
  holdsWeekends: boolean;
  desc: string;
}

export const SYSTEMS: SystemDef[] = [
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
  tp: number;
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

/** Signal na posledni UZAVRENE svicce (c uz neobsahuje tvorici se svicku). */
export function barSignal(system: string, c: Candle[]): BarSignal | null {
  if (c.length < 150) return null;
  const { open, high, low, close } = arrays(c);
  const i = c.length - 1;
  const a = atr(high, low, close, 14);
  const aMed = rollingMedian(a, 100);
  if (a[i] == null || aMed[i] == null) return null;

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
  const { high, low, close } = arrays(c);
  const i = c.length - 1;
  const f = (v: number) => v.toFixed(digits);
  const hour = new Date(c[i].time * 1000).getUTCHours();
  const sessionRule = system === "bbsqueeze_h1" || system === "pullback_h1";
  if (sessionRule && !inSession(c[i].time)) {
    return { text: `mimo obchodní okno 13–17 UTC (poslední svíčka ${hour}:00 UTC)`, tone: "off" };
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
