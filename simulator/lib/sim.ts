// Simulovany broker: plneni za bid/ask se spreadem tveho brokera, SL/TP, swapy
// o pulnoci UTC (3x v den brokera) a limity prop firmy.
import { MARKETS, quote, spreadAt } from "./markets";
import type { Account, Candle, ClosedTrade, Market, Position, Signal } from "./types";

export interface BrokerState {
  account: Account;
  positions: Position[];
  closed: ClosedTrade[];
}

export const DAILY_LOSS_DEFAULT = 2;
export const MAX_DD_LIMIT = 8;
export const PROFIT_TARGET = 8;

export const dayKey = (t: number) => new Date(t * 1000).toISOString().slice(0, 10);
export const sign = (d: "long" | "short") => (d === "long" ? 1 : -1);

export function freshBroker(start: number, t: number): BrokerState {
  const day = dayKey(t);
  return {
    account: { start, balance: start, dayStart: start, dayKey: day, peak: start, halted: null, passed: false, lastRollover: day },
    positions: [],
    closed: [],
  };
}

export function pnlMoney(p: { market: string; dir: "long" | "short"; lots: number; entry: number }, exit: number) {
  return (exit - p.entry) * sign(p.dir) * p.lots * MARKETS[p.market].moneyPerPrice;
}

/** Cena, za kterou by se pozice ted zavrela (long za bid, short za ask). */
export function exitPrice(p: Position, mid: number, t: number) {
  const q = quote(MARKETS[p.market], mid, t);
  return p.dir === "long" ? q.bid : q.ask;
}

/** Velikost pozice podle rizika u SL. lots = null -> pod minimem brokera. */
export function lotsFor(m: Market, entry: number, sl: number, riskPct: number, balance: number) {
  const perLot = Math.abs(entry - sl) * m.moneyPerPrice;
  const raw = perLot > 0 ? (balance * riskPct) / 100 / perLot : 0;
  const lots = Math.floor(raw / m.volStep + 1e-6) * m.volStep;
  return { raw, lots: lots < m.volMin ? null : +Math.min(lots, m.volMax).toFixed(8) };
}

export function openPosition(s: BrokerState, sig: Signal, lots: number, mid: number, t: number): Position {
  const q = quote(MARKETS[sig.market], mid, t);
  const p: Position = {
    id: `p${t}-${Math.random().toString(36).slice(2, 7)}`,
    market: sig.market, system: sig.system, signalId: sig.id, dir: sig.dir, lots,
    entry: sig.dir === "long" ? q.ask : q.bid, sl: sig.sl, tp: sig.tp, openTime: t, swap: 0, checkedTo: t,
  };
  s.positions.push(p);
  return p;
}

export function closePosition(s: BrokerState, p: Position, exit: number, t: number, reason: string): ClosedTrade {
  const pnl = pnlMoney(p, exit);
  s.account.balance += pnl + p.swap;
  s.positions = s.positions.filter((x) => x.id !== p.id);
  const c: ClosedTrade = { ...p, exit, closeTime: t, pnl, reason };
  s.closed.unshift(c);
  if (s.closed.length > 500) s.closed.length = 500;
  return c;
}

/** Swap za kazdou pulnoc UTC mezi from a to (jen pracovni dny, v den brokera 3x). */
export function swapBetween(m: Market, dir: "long" | "short", lots: number, from: number, to: number, price: number) {
  let total = 0;
  for (let d = Math.floor(from / 86400) * 86400 + 86400; d <= to; d += 86400) {
    const wd = (new Date((d - 86400) * 1000).getUTCDay() + 6) % 7; // den, ktery skoncil; 0 = pondeli
    if (wd > 4) continue;
    const frac = dir === "long" ? m.swapLong : m.swapShort;
    total += frac * price * m.moneyPerPrice * lots * (wd === m.roll3 ? 3 : 1);
  }
  return total;
}

export interface Hit {
  exit: number;
  time: number;
  reason: "SL" | "TP";
}

/**
 * Projde svicky od `from` a najde prvni zasah SL/TP. Long se zavira na bidu, short
 * na asku (svicky jsou stredni cena, spread se pricte). SL i TP v jedne svicce = SL.
 * Svicka, ve ktere pozice vznikla, se bere jen svou zaviraci cenou.
 */
export function findHit(
  m: Market, dir: "long" | "short", sl: number, tp: number | null, candles: Candle[], tfSec: number, from: number, now: number,
): { hit: Hit | null; checkedTo: number } {
  let checkedTo = from;
  for (const c of candles) {
    const end = Math.min(c.time + tfSec, now);
    if (end <= checkedTo) continue;
    const half = spreadAt(m, c.time) / 2;
    const partial = c.time < checkedTo;
    const hi = partial ? c.close : c.high;
    const lo = partial ? c.close : c.low;
    const open = partial ? c.close : c.open;
    if (dir === "long") {
      const bidOpen = open - half;
      if (bidOpen <= sl) return { hit: { exit: bidOpen, time: c.time, reason: "SL" }, checkedTo: end };
      if (lo - half <= sl) return { hit: { exit: sl, time: c.time, reason: "SL" }, checkedTo: end };
      if (tp != null && hi - half >= tp) return { hit: { exit: tp, time: c.time, reason: "TP" }, checkedTo: end };
    } else {
      const askOpen = open + half;
      if (askOpen >= sl) return { hit: { exit: askOpen, time: c.time, reason: "SL" }, checkedTo: end };
      if (hi + half >= sl) return { hit: { exit: sl, time: c.time, reason: "SL" }, checkedTo: end };
      if (tp != null && lo + half <= tp) return { hit: { exit: tp, time: c.time, reason: "TP" }, checkedTo: end };
    }
    checkedTo = end;
  }
  return { hit: null, checkedTo };
}

export function equity(s: BrokerState, prices: Map<string, { mid: number; t: number }>, t: number) {
  let e = s.account.balance;
  for (const p of s.positions) {
    const px = prices.get(p.market);
    e += p.swap + (px ? pnlMoney(p, exitPrice(p, px.mid, t)) : 0);
  }
  return e;
}

/**
 * Denni zacatek, maximum a limity (z equity - prisnejsi, jako u prop firem).
 * Denni limit = do konce dne jen sber dat, drawdown limit = challenge neprosla.
 * hit = prave ted se neco zaslo (bot pak zavre pozice).
 */
/** Denni limit ztraty, ktery opravdu plati: v ucicim rezimu (Statistik nevetuje) je vypnuty - jde o data. */
export function dailyLimitOf(st: { statistikBlocks: boolean; dailyLossPct: number }): number | null {
  return st.statistikBlocks ? st.dailyLossPct : null;
}

export function updateAccount(s: BrokerState, eq: number, t: number, dailyLimitPct: number | null) {
  const a = s.account;
  const day = dayKey(t);
  if (day !== a.dayKey) {
    a.dayKey = day;
    a.dayStart = a.balance;
  }
  a.peak = Math.max(a.peak, a.balance);
  const daily = ((a.dayStart - eq) / a.start) * 100;
  const dd = ((a.peak - eq) / a.start) * 100;
  let hit: string | null = null;
  if (!a.halted && dd >= MAX_DD_LIMIT) {
    a.halted = `drawdown ${dd.toFixed(2)} % (limit ${MAX_DD_LIMIT} %)`;
    hit = `DRAWDOWN ${dd.toFixed(2)} % – challenge neprošla`;
  }
  if (dailyLimitPct != null && a.pausedDay !== day && daily >= dailyLimitPct) {
    a.pausedDay = day;
    hit ??= `DENNÍ LIMIT ${daily.toFixed(2)} % (limit ${dailyLimitPct} %)`;
  }
  if (((a.balance - a.start) / a.start) * 100 >= PROFIT_TARGET) a.passed = true;
  return { daily, dd, hit };
}
