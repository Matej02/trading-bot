// Zadani pro AI analytika (Gemini) a cteni jeho odpovedi.

export interface AiContext {
  market: string;
  marketName: string;
  systemName: string;
  tf: string;
  dir: "long" | "short";
  price: number;
  sl: number;
  tp: number | null;
  rrr: number | null;
  spread: number;
  spreadPctOfSl: number; // kolik procent vzdalenosti SL sebere spread
  atr: number | null;
  ema20: number | null;
  ema50: number | null;
  ema200: number | null;
  rsi14: number | null;
  closes: number[]; // poslednich az 40 uzavrenych svicek
  rangeHigh: number;
  rangeLow: number;
  reason: string; // proc strategie signal dala
  opinions: { agent: string; vote: string; reason: string }[];
  dailyLossPct: number;
  dailyLimitPct: number;
  openPositions: number;
  history: { n: number; winrate: number; avgR: number } | null; // vysledky teto strategie v simulaci (stinove)
  digits: number;
  events: string[]; // dulezite zpravy pro meny trhu v pristich 24 h
  released?: string[]; // uz vyhlasene zpravy za poslednich 24 h se skutecnou hodnotou proti prognoze
  news?: string[]; // titulky zprav k trhu (doplni server, lib/server/news.ts)
}

export interface AiAnswer {
  vote: "ano" | "ne";
  confidence: number;
  reason: string;
  risks: string[];
}

const SYSTEM = `Jsi zkušený, skeptický obchodník a risk manager. Posuzuješ JEDEN konkrétní obchodní signál v simulaci
a rozhoduješ, jestli ho vzít. Nemáš sklon souhlasit - většina krátkodobých signálů nemá výhodu, a když si nejsi jistý,
odpověz "ne". Hodnoť hlavně:
- zda spread nesebere příliš velkou část vzdálenosti SL (nad ~20 % je to špatně, nad 40 % téměř jistá ztráta),
- směr trendu (EMA 20/50/200) vůči směru obchodu a zda vstup nehoní už ujetý pohyb,
- RSI (překoupenost/přeprodanost proti směru), polohu ceny v nedávném rozsahu,
- poměr zisk:riziko a realističnost TP vzhledem k ATR,
- dosavadní výsledky této strategie v simulaci, pokud jsou k dispozici,
- blížící se ekonomické zprávy (u krátkých obchodů velké riziko, u swingových menší),
- čerstvě vyhlášená čísla (nad/pod prognózou) a titulky zpráv: jdou fundamenty a nálada PROTI směru obchodu?
  Titulky ber kriticky - jeden článek nic neznamená, rozhoduje jasná převaha nebo zásadní událost.
Cílem uživatele je co nejvyšší úspěšnost: sporný obchod raději vynech.
Odpověz POUZE JSON objektem: {"vote":"ano"|"ne","confidence":0-100,"reason":"max 2 krátké věty česky","risks":["max 3 krátká rizika česky"]}`;

export function buildPrompt(c: AiContext) {
  const f = (v: number | null) => (v == null ? "?" : v.toFixed(c.digits));
  const rel = (e: number | null) => (e == null ? "?" : c.price > e ? "cena NAD" : "cena POD");
  const h = c.history;
  const user = [
    `Trh: ${c.market} (${c.marketName}), strategie: ${c.systemName}, timeframe ${c.tf}.`,
    `Směr: ${c.dir === "long" ? "LONG (nákup)" : "SHORT (prodej)"}. Důvod strategie: ${c.reason}`,
    `Vstup ~${f(c.price)}, SL ${f(c.sl)}, TP ${c.tp == null ? "žádný (drží do otočení trendu)" : f(c.tp)}${c.rrr ? `, poměr zisk:riziko 1:${c.rrr.toFixed(2)}` : ""}.`,
    `Spread ${f(c.spread)} = ${c.spreadPctOfSl.toFixed(0)} % vzdálenosti SL. ATR(14) ${f(c.atr)}.`,
    `EMA20 ${f(c.ema20)} (${rel(c.ema20)}), EMA50 ${f(c.ema50)} (${rel(c.ema50)}), EMA200 ${f(c.ema200)} (${rel(c.ema200)}). RSI(14) ${c.rsi14 == null ? "?" : c.rsi14.toFixed(0)}.`,
    `Rozsah posledních ${c.closes.length} svíček: ${f(c.rangeLow)} – ${f(c.rangeHigh)}. Zavírací ceny (nejstarší → nejnovější): ${c.closes.map((x) => x.toFixed(c.digits)).join(", ")}.`,
    `Účet: denní ztráta ${c.dailyLossPct.toFixed(2)} % z limitu ${c.dailyLimitPct} %, otevřených pozic ${c.openPositions}.`,
    h ? `Tato strategie v simulaci: ${h.n} uzavřených signálů, úspěšnost ${h.winrate.toFixed(0)} %, průměr ${h.avgR.toFixed(2)} R.` : "Tato strategie zatím nemá v simulaci výsledky.",
    c.events?.length ? `Zprávy pro tento trh v příštích 24 h: ${c.events.join("; ")}.` : "Žádné důležité zprávy pro tento trh v příštích 24 h.",
    c.released?.length ? `Vyhlášená čísla za posledních 24 h: ${c.released.join("; ")}.` : "Za posledních 24 h nevyšla žádná důležitá čísla pro tento trh (nebo je nemám).",
    c.news?.length ? `Titulky zpráv k trhu (nejnovější první):\n${c.news.map((n) => `- ${n}`).join("\n")}` : "Titulky zpráv k trhu nejsou k dispozici.",
    `Názory ostatních agentů: ${c.opinions.map((o) => `${o.agent}: ${o.vote.toUpperCase()} – ${o.reason}`).join(" | ")}`,
  ].join("\n");
  return { system: SYSTEM, user };
}

export function parseAnswer(text: string): AiAnswer {
  const m = text.match(/\{[\s\S]*\}/);
  const j = JSON.parse(m ? m[0] : text) as Partial<AiAnswer>;
  const vote = String(j.vote ?? "").toLowerCase().startsWith("a") ? "ano" : "ne";
  return {
    vote,
    confidence: Math.max(0, Math.min(100, Math.round(Number(j.confidence) || 0))),
    reason: String(j.reason ?? "").slice(0, 400) || "bez zdůvodnění",
    risks: (Array.isArray(j.risks) ? j.risks : []).slice(0, 3).map((r) => String(r).slice(0, 160)),
  };
}
