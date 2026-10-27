// Agenti, kteri o kazdem signalu rozhoduji spolu. Prvni ctyri jsou stejni jako
// v Python botovi (tv_agent/agents.py), dabluv advokat jen radi, rozhodci shrne.
import registry from "./registry.json";
import { atr, ema, rollingMedian } from "./indicators";
import { currencies, fmt, isCrypto, MARKETS, quote } from "./markets";
import { lotsFor, pnlMoney, sign, type BrokerState } from "./sim";
import { eventsFor, inMinutes, marketCurrencies, NEWS_AFTER_MIN, NEWS_BEFORE_MIN, releasesFor, releaseText, type CalEvent, type Release } from "./calendar";
import { momentumReturn, type SystemDef } from "./strategies";
import type { Candle, ClosedTrade, Market, Opinion, Settings, Signal } from "./types";

export interface AgentCtx {
  market: Market;
  signal: Signal;
  system: SystemDef;
  now: number;
  mid: number;
  candles: Candle[]; // uzavrene svicky systemu (u momenta denni)
  broker: BrokerState;
  equity: number;
  settings: Settings;
  seen: Set<string>;
  delayedMin: number;
  todayTrades: number;
  systemTrades: ClosedTrade[]; // uzavrene obchody tohoto systemu, nejnovejsi prvni
  events: CalEvent[] | null; // ekonomicky kalendar, null = nepodarilo se nacist
  releases: Release[]; // uz vyhlasene zpravy se skutecnou hodnotou
}

export interface Verdict {
  opinions: Opinion[];
  decision: "beru" | "neberu";
  summary: string;
  lots: number | null;
}

// denni swing setup drzi ~2 tydny - vstup az 12 h po zavreni svicky je v poradku (drift hlida limit ceny)
const MAX_AGE: Record<string, number> = { "1m": 90, "5m": 300, "15m": 600, "1h": 900, "1d": 12 * 3600 };

function validator(x: AgentCtx): Opinion {
  const base = { agent: "Validátor", role: "kontroluje, jestli je signál čerstvý a cena neutekla", hard: true };
  const s = x.signal;
  if (x.seen.has(s.id)) return { ...base, vote: "ne", reason: "Tenhle signál už jednou prošel – duplicita." };
  const age = x.now - s.time;
  const maxAge = MAX_AGE[x.system.tf];
  if (age > maxAge) return { ...base, vote: "ne", reason: `Signál je starý ${Math.round(age)} s (limit ${maxAge} s).` };
  const q = quote(x.market, x.mid, x.now);
  const entry = s.dir === "long" ? q.ask : q.bid;
  const drift = (entry - s.price) * sign(s.dir);
  const a = atr(x.candles.map((c) => c.high), x.candles.map((c) => c.low), x.candles.map((c) => c.close), 14);
  const lastAtr = a[a.length - 1] ?? 0;
  const limit = Math.max(2 * q.spread, 0.2 * lastAtr);
  if (drift > limit) {
    return { ...base, vote: "ne", reason: `Cena utekla o ${fmt(x.market, drift)} (limit ${fmt(x.market, limit)}) – vstup by byl moc drahý.` };
  }
  return { ...base, vote: "ano", reason: `Signál je čerstvý (${Math.round(age)} s), vstup je dražší jen o ${fmt(x.market, Math.max(drift, 0))} (limit ${fmt(x.market, limit)}).` };
}

function marketNow(x: AgentCtx): Opinion {
  const base = { agent: "Trh teď", role: "hlídá víkend, rollover a spread", hard: true };
  const d = new Date(x.now * 1000);
  const wd = (d.getUTCDay() + 6) % 7;
  const h = d.getUTCHours();
  const q = quote(x.market, x.mid, x.now);
  if (!isCrypto(x.market)) {
    if (wd >= 5) return { ...base, vote: "ne", reason: "Víkend – trh je zavřený." };
    if (wd === 4 && h >= 19 && !x.system.holdsWeekends) {
      return { ...base, vote: "ne", reason: "Pátek večer – riziko gapu přes víkend, krátkodobý obchod nedává smysl." };
    }
    if (h === 21 || h === 22) {
      return { ...base, vote: "ne", reason: `Rollover okno (${h}:00 UTC) – spread tu skáče na násobky normálu.` };
    }
  }
  const delay = x.delayedMin ? ` Pozor: data zpožděná o ${x.delayedMin} min.` : "";
  return { ...base, vote: "ano", reason: `Spread ${fmt(x.market, q.spread)} je běžný pro ${h}:00 UTC.${delay}` };
}

function calendar(x: AgentCtx): Opinion {
  const base = { agent: "Kalendář", role: "hlídá důležité ekonomické zprávy", hard: true };
  const ccy = marketCurrencies(x.market).join("/");
  if (!x.events) return { ...base, vote: "ano", reason: "Kalendář se teď nepodařilo načíst – zprávy nekontroluju." };
  const near = eventsFor(x.events, x.market, x.now - NEWS_AFTER_MIN * 60, x.now + NEWS_BEFORE_MIN * 60);
  if (near.length) {
    const e = near[0];
    const when = e.time >= x.now ? `za ${inMinutes(e.time - x.now)} vyjde` : `před ${inMinutes(x.now - e.time)} vyšla`;
    return { ...base, vote: "ne", reason: `${when} zpráva s vysokým dopadem: ${e.currency} ${e.title} – vstup kolem zprávy je loterie (skoky, široký spread).` };
  }
  const next = eventsFor(x.events, x.market, x.now, x.now + 7 * 86400)[0];
  // posledni vyhlasena zprava (do 4 h) se skutecnou hodnotou - jen informace, veto zustava jen kolem zpravy
  const recent = releasesFor(x.releases, x.market, x.now - 4 * 3600, x.now);
  const last = recent.find((e) => e.impact === "High" && e.forecast) ?? recent.find((e) => e.forecast) ?? recent[0];
  return {
    ...base, vote: "ano",
    reason: `Žádná důležitá zpráva pro ${ccy} v nejbližších ${NEWS_BEFORE_MIN} min.${next ? ` Další: ${next.currency} ${next.title} za ${inMinutes(next.time - x.now)}.` : ""}` +
      (last ? ` Naposledy vyšlo: ${releaseText(last)} (před ${inMinutes(x.now - last.time)}).` : ""),
  };
}

type RegRec = { status: string; note?: string; holdout_pf?: number; holdout_n?: number };

function statistician(x: AgentCtx): Opinion {
  const hard = x.settings.statistikBlocks;
  const base = { agent: "Statistik", role: "pouští jen setupy s ověřenou výhodou", hard };
  const reg = (registry as unknown as Record<string, Record<string, RegRec>>)[x.signal.system] ?? {};
  const rec = reg[x.signal.market] ?? reg["*"];
  const t = x.systemTrades;
  let sim = "V simulaci zatím žádný uzavřený obchod.";
  if (t.length) {
    const w = t.filter((c) => c.pnl + c.swap > 0).reduce((a, c) => a + c.pnl + c.swap, 0);
    const l = -t.filter((c) => c.pnl + c.swap < 0).reduce((a, c) => a + c.pnl + c.swap, 0);
    sim = `V simulaci ${t.length} obchodů, PF ${l ? (w / l).toFixed(2) : "∞"}.`;
  }
  if (!rec) return { ...base, vote: "ne", reason: `Setup není v registru – neověřený. ${sim}` };
  if (rec.status !== "validated") {
    const mode = hard ? "" : " (v simulaci jen radím, neblokuju)";
    return { ...base, vote: "ne", reason: `Neověřeno: ${rec.note ?? rec.status}. ${sim}${mode}` };
  }
  if ((rec.holdout_pf ?? 0) < 1.1 || (rec.holdout_n ?? 0) < 100) {
    return { ...base, vote: "ne", reason: `Slabá evidence: PF ${rec.holdout_pf}, n ${rec.holdout_n}. ${sim}` };
  }
  return { ...base, vote: "ano", reason: `Ověřeno: holdout PF ${rec.holdout_pf}, n ${rec.holdout_n}. ${sim}` };
}

function risk(x: AgentCtx): { op: Opinion; lots: number | null } {
  const base = { agent: "Risk", role: "hlídá limity prop firmy, velikost a expozici", hard: true };
  const a = x.broker.account;
  const no = (reason: string) => ({ op: { ...base, vote: "ne" as const, reason }, lots: null });
  const limit = x.settings.dailyLossPct;
  if (a.halted) return no(`Challenge neprošla (${a.halted}) – živé obchody neberu, signály jen sbírám do statistiky.`);
  if (a.pausedDay === a.dayKey) {
    return no(`Dnes padl denní limit ztráty ${limit} % – do konce dne neberu živé obchody, signály jen sbírám do statistiky.`);
  }
  if (a.passed) return no("Cíl challenge je splněný – dál neriskovat.");
  if (x.todayTrades >= x.settings.maxTradesPerDay) return no(`Dnes už ${x.todayTrades} obchodů (limit ${x.settings.maxTradesPerDay}).`);
  if (x.broker.positions.length >= x.settings.maxOpen) return no(`Otevřeno ${x.broker.positions.length} pozic (limit ${x.settings.maxOpen}).`);
  if (x.broker.positions.some((p) => p.system === x.signal.system && p.market === x.market.id)) {
    return no("Tenhle systém už má na trhu otevřenou pozici – nevrstvím.");
  }

  const q = quote(x.market, x.mid, x.now);
  const entry = x.signal.dir === "long" ? q.ask : q.bid;
  const { lots, raw } = lotsFor(x.market, entry, x.signal.sl, x.signal.riskPct, a.balance);
  if (!lots) return no(`Velikost ${raw.toFixed(3)} lotu je pod minimem brokera (${x.market.volMin}) – větší pozice by nesla víc rizika, než je dovoleno.`);

  const riskMoney = Math.abs(pnlMoney({ market: x.market.id, dir: x.signal.dir, lots, entry }, x.signal.sl));
  const dailyLoss = Math.max(0, a.dayStart - x.equity);
  if (((dailyLoss + riskMoney) / a.start) * 100 > limit) {
    return no(`Při zásahu SL by denní ztráta byla ${(((dailyLoss + riskMoney) / a.start) * 100).toFixed(2)} % – nad limitem ${limit} %.`);
  }
  const cur = currencies(x.market);
  if (cur) {
    const exp: Record<string, number> = {};
    const add = (m: string, dir: "long" | "short") => {
      const [base, quoteCur] = currencies(MARKETS[m])!;
      exp[base] = (exp[base] ?? 0) + sign(dir);
      exp[quoteCur] = (exp[quoteCur] ?? 0) - sign(dir);
    };
    for (const p of x.broker.positions) if (currencies(MARKETS[p.market])) add(p.market, p.dir);
    add(x.market.id, x.signal.dir);
    const worst = Object.entries(exp).sort((u, v) => Math.abs(v[1]) - Math.abs(u[1]))[0];
    if (worst && Math.abs(worst[1]) > 2) return no(`Moc velká expozice na ${worst[0]} (${worst[1] > 0 ? "+" : ""}${worst[1]} pozic stejným směrem).`);
  }
  return {
    op: { ...base, vote: "ano", reason: `${lots} lotu, riziko u SL ${riskMoney.toFixed(0)} $ (${((riskMoney / a.balance) * 100).toFixed(2)} % účtu). Denní ztráta zatím ${((dailyLoss / a.start) * 100).toFixed(2)} %.` },
    lots,
  };
}

function devilsAdvocate(x: AgentCtx): Opinion {
  const base = { agent: "Ďáblův advokát", role: "hledá důvody, proč obchod NEbrat", hard: false };
  const c = x.candles;
  const close = c.map((k) => k.close);
  const cons: string[] = [];
  if (x.system.kind === "momentum") {
    if (close.length > 251) {
      const r = momentumReturn(close);
      if (Math.abs(r) < 0.02) cons.push(`trend je slabý (${(r * 100).toFixed(1)} % za rok), snadno se otočí`);
    }
  } else if (c.length > 120) {
    const a = atr(c.map((k) => k.high), c.map((k) => k.low), close, 14);
    const med = rollingMedian(a, 100);
    const e20 = ema(close, 20), e200 = ema(close, 200);
    const i = c.length - 1;
    if (a[i] != null && Math.abs(close[i] - e20[i]!) > 2 * a[i]!) cons.push("cena je přes 2 ATR od EMA20 – honíš už ujetý pohyb");
    if (a[i] != null && med[i] != null && a[i]! < 0.6 * med[i]!) cons.push("trh spí (ATR pod 60 % mediánu), spread je proti pohybu velký");
    const against = x.signal.dir === "long" ? close[i] < e200[i]! : close[i] > e200[i]!;
    if (against) cons.push("obchod jde proti dlouhodobému trendu (EMA200)");
  }
  const last3 = x.systemTrades.slice(0, 3);
  if (last3.length === 3 && last3.every((t) => t.pnl + t.swap < 0)) cons.push("poslední 3 obchody tohohle systému skončily ztrátou");
  const hold = (x.signal.dir === "long" ? x.market.swapLong : x.market.swapShort) * 100;
  if (x.system.kind === "momentum" && hold < -0.01) cons.push(`držení stojí ${hold.toFixed(3)} % ceny za noc na swapu`);
  if (cons.length) return { ...base, vote: "ne", reason: `Proti: ${cons.join("; ")}.` };
  return { ...base, vote: "ano", reason: "Nenašel jsem rozumný důvod proti." };
}

/** Kodovi agenti reknou svoje (AI analytik se pta az na ne - vidi jejich nazory). */
export function codeOpinions(x: AgentCtx) {
  const r = risk(x);
  return { opinions: [validator(x), marketNow(x), calendar(x), statistician(x), r.op, devilsAdvocate(x)], lots: r.lots };
}

/** Rozhodci: tvrde veto = neberu; jinak podle rezimu (bere co jde / opatrny = vetsina poradcu). */
export function judge(x: AgentCtx, opinions: Opinion[], lots: number | null, note = ""): Verdict {
  const hardNo = opinions.filter((o) => o.hard && o.vote === "ne");
  const softNo = opinions.filter((o) => !o.hard && o.vote === "ne");
  const yes = opinions.filter((o) => o.vote === "ano").length;
  let decision: "beru" | "neberu" = "beru";
  let summary: string;
  if (hardNo.length) {
    decision = "neberu";
    summary = `Neberu – veto: ${hardNo.map((o) => o.agent).join(", ")}.`;
  } else if (x.settings.mode === "vse") {
    summary = softNo.length
      ? `Beru – tvrdé kontroly prošly. Proti: ${softNo.map((o) => o.agent).join(", ")} (v režimu „bere co jde“ jen radí).`
      : `Beru – tvrdé kontroly prošly, nikdo proti.`;
  } else if (softNo.length >= 2) {
    decision = "neberu";
    summary = `Neberu – tvrdé kontroly prošly, ale většina poradců je proti (${softNo.map((o) => o.agent).join(", ")}).`;
  } else {
    summary = `Beru – tvrdé kontroly prošly, ${yes}× pro, ${softNo.length}× proti (jen rada).`;
  }
  return { opinions, decision, summary: summary + note, lots: decision === "beru" ? lots : null };
}

export const AI_AGENT = "AI analytik";
