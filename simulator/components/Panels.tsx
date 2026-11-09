"use client";

import { useEffect, useState } from "react";
import { closedCandles, store } from "@/lib/data";
import { aiScore } from "@/lib/aiScore";
import { eventsFor, inMinutes, marketCurrencies, releasesFor, releaseText, type Calendar } from "@/lib/calendar";
import { exportFile } from "@/lib/exporting";
import { blockedBy, decisionStats, decisionVerdict } from "@/lib/verdict";
import { fmt, MARKETS, quote, spreadAt } from "@/lib/markets";
import { exitPrice, lotsFor, MAX_DD_LIMIT, pnlMoney, PROFIT_TARGET, type BrokerState } from "@/lib/sim";
import { lastAtr, manualLevels, SYSTEM, SYSTEMS } from "@/lib/strategies";
import type { Bot, BotState } from "@/lib/bot";
import type { Deliberation, Shadow, TF } from "@/lib/types";

const money = (v: number) => `${v >= 0 ? "" : "−"}${Math.abs(v).toLocaleString("cs-CZ", { maximumFractionDigits: 2, minimumFractionDigits: 2 })} $`;
const dt = (t: number) => new Date(t * 1000).toLocaleString("cs-CZ", { day: "numeric", month: "numeric", hour: "2-digit", minute: "2-digit" });

function Bar({ label, value, limit, good }: { label: string; value: number; limit: number; good?: boolean }) {
  const pct = Math.max(0, Math.min(100, (value / limit) * 100));
  const color = good ? "#26a69a" : pct > 75 ? "#ef5350" : pct > 40 ? "#f0b90b" : "#2962ff";
  return (
    <div className="bar">
      <div className="bar-top">
        <span>{label}</span>
        <span>{value.toFixed(2)} % / {limit} %</span>
      </div>
      <div className="bar-track"><div className="bar-fill" style={{ width: `${pct}%`, background: color }} /></div>
    </div>
  );
}

export function AccountPanel({ broker, eq, dailyLimit, prop }: { broker: BrokerState; eq: number; dailyLimit: number | null; prop: boolean }) {
  const a = broker.account;
  const daily = Math.max(0, ((a.dayStart - eq) / a.start) * 100);
  const dd = Math.max(0, ((a.peak - eq) / a.start) * 100);
  const profit = ((a.balance - a.start) / a.start) * 100;
  // kazda pozice zacina v minusu o spread (nakup za ask, prodej za bid) - at je videt, kolik minusu to je
  const spreadCost = broker.positions.reduce((s, p) => {
    const m = MARKETS[p.market];
    return s + spreadAt(m, p.openTime) * p.lots * m.moneyPerPrice;
  }, 0);
  const swaps = broker.positions.reduce((s, p) => s + p.swap, 0);
  const today = new Date().toISOString().slice(0, 10);
  const closedToday = broker.closed.filter((c) => new Date(c.closeTime * 1000).toISOString().slice(0, 10) === today);
  const realizedToday = closedToday.reduce((s, c) => s + c.pnl + c.swap, 0);
  return (
    <div className="panel">
      <div className="acc-grid">
        <div><div className="muted small">Balance</div><div className="big">{money(a.balance)}</div></div>
        <div><div className="muted small">Equity</div><div className={`big ${eq >= a.balance ? "up" : "down"}`}>{money(eq)}</div></div>
        <div><div className="muted small">Otevřený P&amp;L</div><div className={eq - a.balance >= 0 ? "up" : "down"}>{money(eq - a.balance)}</div></div>
        <div><div className="muted small">Pozic</div><div>{broker.positions.length}</div></div>
      </div>
      <div className="small muted costs">
        Z otevřeného P&amp;L je spread při vstupu {money(-spreadCost)}{swaps ? `, swapy ${money(swaps)}` : ""}.
        Dnes uzavřeno {closedToday.length} {closedToday.length === 1 ? "obchod" : closedToday.length >= 2 && closedToday.length <= 4 ? "obchody" : "obchodů"}:{" "}
        <span className={realizedToday >= 0 ? "up" : "down"}>{money(realizedToday)}</span>.
      </div>
      {dailyLimit != null ? <Bar label="Denní ztráta" value={daily} limit={dailyLimit} />
        : <div className="small muted">Denní ztráta {daily.toFixed(2)} % · limit vypnutý (učící režim)</div>}
      {prop ? <>
        <Bar label="Drawdown" value={dd} limit={MAX_DD_LIMIT} />
        <Bar label="Zisk k cíli" value={Math.max(0, profit)} limit={PROFIT_TARGET} good />
      </> : <div className="small muted">Drawdown {dd.toFixed(2)} % · výsledek {profit >= 0 ? "+" : ""}{profit.toFixed(2)} % · limity 8 % vypnuté (učící režim)</div>}
      {prop && a.halted && <div className="alert down">Challenge NEPROŠLA: {a.halted}. Signály se dál sbírají do statistiky, reset v Nastavení.</div>}
      {!a.halted && dailyLimit != null && a.pausedDay === a.dayKey && (
        <div className="alert down">Dnes padl denní limit {dailyLimit} % – živé obchody stop do zítřka, signály se dál sbírají do statistiky.</div>
      )}
      {prop && a.passed && !a.halted && <div className="alert up">Cíl {PROFIT_TARGET} % splněn – v simulaci.</div>}
    </div>
  );
}

/** Rucni BUY/SELL na zobrazenem trhu - o vstupu rozhodnou agenti. */
export function ManualTrade({ bot, marketId, tf }: { bot: Bot; marketId: string; tf: TF }) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [last, setLast] = useState<Deliberation | null>(null);
  const m = MARKETS[marketId];
  const now = Math.floor(Date.now() / 1000);
  const px = store.lastPrice.get(marketId);
  const a = lastAtr(closedCandles(store.peek(m, tf), tf, now));
  const q = px ? quote(m, px.mid, now) : null;
  const send = async (dir: "long" | "short") => {
    setBusy(true);
    setResult(null);
    const d = await bot.manualSignal(marketId, tf, dir);
    setLast(typeof d === "string" ? null : d);
    setResult(typeof d === "string" ? d : `${d.decision === "beru" ? "BERU" : "NEBERU"} – ${d.summary}`);
    setBusy(false);
  };
  // zamitnuto jen radou poradcu (zadne tvrde veto) -> posledni slovo mas ty
  const canOverride = last && last.decision === "neberu" && !last.positionId &&
    !last.opinions.some((o) => o.hard && o.vote === "ne") && now - last.time < 120;
  const override = () => {
    if (!last) return;
    const err = bot.forceManual(last.id);
    setResult(err ?? `Otevřeno i přes radu agentů – ${last.lots} lotu. Ve stínových výsledcích se ukáže, kdo měl pravdu.`);
    setLast(null);
  };
  const preview = (dir: "long" | "short") => {
    if (!a || !q || !px) return null;
    const { sl, tp } = manualLevels(px.mid, a, dir, bot.state.settings.rrr);
    const { lots } = lotsFor(m, dir === "long" ? q.ask : q.bid, sl, bot.state.settings.riskPct, bot.state.broker.account.balance);
    return `SL ${fmt(m, sl)} · TP ${fmt(m, tp)} · ${lots ?? "pod min."} lotu`;
  };
  return (
    <div className="manual">
      <div className="manual-head">
        <b>Ruční obchod – {marketId}</b>
        <span className="muted small"> SL 1,5 ATR z grafu {tf}, RRR 1:{bot.state.settings.rrr}, riziko {bot.state.settings.riskPct} % · o vstupu rozhodnou agenti</span>
      </div>
      <div className="manual-btns">
        <button className="btn buy" disabled={busy || !q || bot.role === "viewer"} onClick={() => send("long")}>
          <b>BUY {q ? fmt(m, q.ask) : ""}</b><span className="small">{preview("long") ?? "čekám na data"}</span>
        </button>
        <button className="btn sell" disabled={busy || !q || bot.role === "viewer"} onClick={() => send("short")}>
          <b>SELL {q ? fmt(m, q.bid) : ""}</b><span className="small">{preview("short") ?? "čekám na data"}</span>
        </button>
      </div>
      {result && <div className={`manual-res ${result.startsWith("BERU") || result.startsWith("Otevřeno") ? "up" : "muted"}`}>{result} Podrobnosti v Místnosti agentů →</div>}
      {canOverride && (
        <button className="btn small override" onClick={override}>
          Přesto vzít – tvrdé kontroly prošly, proti jsou jen poradci
        </button>
      )}
    </div>
  );
}

const TONE: Record<string, string> = { near: "blízko signálu", wait: "čeká", off: "stojí", err: "chyba" };

/** Co bot prave sleduje a proc zatim nebere. */
export function Radar({ bot }: { bot: Bot }) {
  const items = [...bot.radar.values()].sort((x, y) =>
    SYSTEMS.findIndex((s) => s.id === x.system) - SYSTEMS.findIndex((s) => s.id === y.system) || x.market.localeCompare(y.market));
  if (!bot.state.settings.botOn) return <div className="empty">Bot je vypnutý – klikni AKTIVOVAT vpravo nahoře.</div>;
  if (!items.length) return <div className="empty">Bot se rozbíhá, za pár vteřin tu bude, co sleduje…</div>;
  return (
    <table className="tbl radar">
      <thead><tr><th>Strategie</th><th>Trh</th><th>Stav</th><th>Na co čeká / proč zatím nebere</th></tr></thead>
      <tbody>
        {items.map((r) => (
          <tr key={`${r.system}|${r.market}`}>
            <td className="small">{SYSTEM[r.system]?.name ?? r.system}</td>
            <td>{r.market}</td>
            <td><span className={`tone ${r.tone}`}>{TONE[r.tone]}</span></td>
            <td className="wrap">{r.text}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Co bot vi o zpravach k trhu v grafu: pristi zpravy, vyhlasena cisla a titulky (to same dostava AI analytik). */
export function NewsPanel({ marketId }: { marketId: string }) {
  const [cal, setCal] = useState<Calendar | null>(null);
  const [news, setNews] = useState<{ market: string; items: { time: number; title: string }[] } | null>(null);
  useEffect(() => {
    let on = true;
    const load = () => {
      fetch("/api/calendar").then((r) => r.json()).then((j: Calendar) => on && setCal(j)).catch(() => {});
      fetch(`/api/news?market=${encodeURIComponent(marketId)}`).then((r) => r.json()).then((j) => on && setNews(j)).catch(() => {});
    };
    load();
    const t = setInterval(load, 10 * 60_000);
    return () => { on = false; clearInterval(t); };
  }, [marketId]);
  const m = MARKETS[marketId];
  if (!m) return null;
  const now = Date.now() / 1000;
  const next = cal?.events ? eventsFor(cal.events, m, now, now + 48 * 3600, ["High", "Medium"]).slice(0, 5) : [];
  const done = cal ? releasesFor(cal.releases, m, now - 86400, now).slice(0, 6) : [];
  const heads = news?.market === marketId ? news.items : [];
  return (
    <div className="news">
      <div className="muted small">Měny, které trhem hýbou: {marketCurrencies(m).join(", ")} · totéž dostává AI analytik u každého signálu</div>
      <div className="news-cols">
        <div>
          <div className="news-h">Příští zprávy (48 h)</div>
          {!cal ? <div className="muted small">načítám…</div> : !cal.events ? <div className="down small">kalendář se teď nepodařilo načíst</div>
            : next.length ? next.map((e) => (
              <div key={`${e.time}${e.title}`} className="small"><span className={e.impact === "High" ? "down" : "warn"}>●</span> {e.currency} {e.title}
                <span className="muted"> za {inMinutes(e.time - now)}{e.forecast ? ` · prognóza ${e.forecast}` : ""}</span></div>))
              : <div className="muted small">nic důležitého</div>}
        </div>
        <div>
          <div className="news-h">Vyhlášeno za 24 h</div>
          {done.length ? done.map((e) => (
            <div key={`${e.time}${e.title}`} className={`small ${e.better == null ? "" : e.better ? "up" : "down"}`}>
              {releaseText(e)} <span className="muted">před {inMinutes(now - e.time)}</span></div>))
            : <div className="muted small">{cal ? "nic důležitého" : "načítám…"}</div>}
        </div>
      </div>
      <div className="news-h">Titulky zpráv</div>
      {heads.length ? heads.map((h) => (
        <div key={h.title} className="small">{h.title} <span className="muted">před {inMinutes(now - h.time)}</span></div>))
        : <div className="muted small">{news ? "žádné čerstvé titulky" : "načítám…"}</div>}
    </div>
  );
}

export function Positions({ broker, onClose, onPick }: { broker: BrokerState; onClose?: (id: string) => void; onPick: (m: string) => void }) {
  if (!broker.positions.length) return <div className="empty">Žádné otevřené pozice.</div>;
  const now = Math.floor(Date.now() / 1000);
  return (
    <table className="tbl">
      <thead>
        <tr><th>Trh</th><th>Směr</th><th>Loty</th><th>Vstup</th><th>Teď</th><th>SL</th><th>TP</th><th>P&amp;L</th><th>Swap</th><th>Systém</th><th>Otevřeno</th><th /></tr>
      </thead>
      <tbody>
        {broker.positions.map((p) => {
          const m = MARKETS[p.market];
          const px = store.lastPrice.get(p.market);
          const exit = px ? exitPrice(p, px.mid, now) : null;
          const pnl = exit != null ? pnlMoney(p, exit) : 0;
          return (
            <tr key={p.id}>
              <td className="link" onClick={() => onPick(p.market)}>{p.market}</td>
              <td className={`dir ${p.dir}`}>{p.dir === "long" ? "BUY" : "SELL"}</td>
              <td>{p.lots}</td>
              <td>{fmt(m, p.entry)}</td>
              <td>{fmt(m, exit)}</td>
              <td>{fmt(m, p.sl)}</td>
              <td>{p.tp != null ? fmt(m, p.tp) : "–"}</td>
              <td className={pnl >= 0 ? "up" : "down"}>{money(pnl)}</td>
              <td className={p.swap >= 0 ? "up" : "down"}>{money(p.swap)}</td>
              <td className="small">{SYSTEM[p.system]?.name ?? p.system}</td>
              <td className="small muted">{dt(p.openTime)}</td>
              <td>{onClose && <button className="btn small" onClick={() => onClose(p.id)}>Zavřít</button>}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function rStats(xs: Shadow[]) {
  const done = xs.filter((x) => x.r != null);
  const mean = done.length ? done.reduce((a, x) => a + x.r!, 0) / done.length : 0;
  const win = done.length ? (done.filter((x) => x.r! > 0).length / done.length) * 100 : 0;
  return { n: done.length, open: xs.length - done.length, mean, win };
}

/** Stazeni dat: ze serveru cela historie, v lokalnim rezimu to, co je v tomhle prohlizeci. */
export function ExportButtons({ bot }: { bot: Bot }) {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const local = (format: string) => {
    const s = bot.state;
    const f = exportFile({
      core: null, journal: [...s.journal].reverse(), closed: [...s.broker.closed].reverse(), shadows: s.shadows,
      log: [...s.log].reverse(),
    }, format, tz);
    const url = URL.createObjectURL(new Blob([f.body], { type: f.type }));
    const a = Object.assign(document.createElement("a"), { href: url, download: f.name });
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const items: [string, string][] = [["journal", "Deník (CSV)"], ["trades", "Obchody (CSV)"], ["json", "Vše pro rozbor (JSON)"]];
  return (
    <div className="export">
      <span className="small muted">Stáhnout {bot.mode === "server" ? `celou historii (${bot.journalTotal} záznamů v deníku)` : "data z tohoto prohlížeče"}:</span>
      {items.map(([f, label]) =>
        bot.mode === "server"
          ? <a key={f} className="btn small" href={`/api/export?format=${f}&tz=${encodeURIComponent(tz)}`}>{label}</a>
          : <button key={f} className="btn small" onClick={() => local(f)}>{label}</button>)}
    </div>
  );
}

/** Zpetne hodnoceni rozhodnuti: vcetne nevzatych obchodu - pomohlo zamitnuti, nebo ulo zisk? */
function DecisionCard({ state }: { state: BotState }) {
  const s = decisionStats(state.journal, state.shadows);
  if (!s.n) return <div className="muted small">Rozhodnutí zpětně: zatím žádný signál nedoběhl (každý, i nevzatý, se sleduje až do SL / TP).</div>;
  const pct = (a: number, b: number) => (b ? `${((a / b) * 100).toFixed(0)} %` : "–");
  const net = s.saved - s.missed;
  return (
    <>
      <div className="stats">
        <div className="stat">
          <div className="muted small">Rozhodnutí zpětně – správně</div>
          <div>{s.correct} z {s.n} ({pct(s.correct, s.n)})</div>
        </div>
        <div className="stat">
          <div className="muted small">Vzaté obchody</div>
          <div>{s.takenOk} z {s.takenN} vydělalo ({pct(s.takenOk, s.takenN)})</div>
        </div>
        <div className="stat">
          <div className="muted small">Nevzaté obchody</div>
          <div>{s.rejOk} z {s.rejN} by prodělalo ({pct(s.rejOk, s.rejN)}) · ušetřeno {s.saved.toFixed(1)} R, ušlo {s.missed.toFixed(1)} R ·{" "}
            <span className={net >= 0 ? "up" : "down"}>zamítání {net >= 0 ? "pomohlo" : "škodilo"} {net >= 0 ? "+" : ""}{net.toFixed(1)} R</span></div>
        </div>
      </div>
      {s.byBlocker.length > 0 && (
        <table className="tbl">
          <thead><tr><th>Kdo obchod zastavil</th><th>Zastavil</th><th>Z toho správně</th><th>Přínos (ušetřeno − ušlo)</th></tr></thead>
          <tbody>
            {s.byBlocker.map((b) => (
              <tr key={b.agent}>
                <td>{b.agent}</td>
                <td>{b.n}</td>
                <td>{b.ok} ({pct(b.ok, b.n)})</td>
                <td className={b.net >= 0 ? "up" : "down"}>{b.net >= 0 ? "+" : ""}{b.net.toFixed(1)} R</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}

/** Co funguje: vysledky vsech signalu (i nevzatych) po strategiich a trzich, nejlepsi nahore. */
function ComboTable({ shadows }: { shadows: Shadow[] }) {
  const groups = new Map<string, Shadow[]>();
  for (const x of shadows) {
    const k = `${x.system}|${x.market}`;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k)!.push(x);
  }
  const rows = [...groups.entries()].map(([k, xs]) => {
    const st = rStats(xs);
    return { k, system: xs[0].system, market: xs[0].market, ...st, sum: st.mean * st.n, taken: xs.filter((x) => x.taken).length };
  }).filter((r) => r.n > 0).sort((a, b) => b.mean - a.mean || b.n - a.n);
  if (!rows.length) return null;
  return (
    <>
      <div className="muted small">Co funguje – strategie × trh (všechny signály stínově, i nevzaté; nejlepší nahoře). Spolehlivé to začne
        být až kolem 30 uzavřených signálů na řádek.</div>
      <table className="tbl">
        <thead><tr><th>Strategie</th><th>Trh</th><th>Uzavř.</th><th>Win</th><th>⌀ R</th><th>Součet R</th><th>Vzato živě</th><th>Běží</th></tr></thead>
        <tbody>
          {rows.slice(0, 40).map((r) => (
            <tr key={r.k}>
              <td className="small">{SYSTEM[r.system]?.name ?? r.system}</td>
              <td>{r.market}</td>
              <td>{r.n}{r.n < 30 && <span className="muted small"> (málo)</span>}</td>
              <td>{r.win.toFixed(0)} %</td>
              <td className={r.mean >= 0 ? "up" : "down"}>{r.mean.toFixed(2)}</td>
              <td className={r.sum >= 0 ? "up" : "down"}>{r.sum.toFixed(1)}</td>
              <td>{r.taken}</td>
              <td>{r.open}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

/** Skore AI analytika na zivych signalech - podle nej dostane (nebo ztrati) pravo veta. */
function AiScoreCard({ shadows }: { shadows: Shadow[] }) {
  const a = aiScore(shadows);
  const cell = (g: typeof a.ano) => g.n
    ? <>{g.n} · win {g.win.toFixed(0)} % · <span className={g.mean >= 0 ? "up" : "down"}>⌀ {g.mean.toFixed(2)} R</span></>
    : "zatím nic";
  return (
    <div className="stat">
      <div className="muted small">AI analytik – skóre na živých signálech {a.earned ? "· má právo veta" : "· jen radí"}</div>
      <div>Řekl ANO: {cell(a.ano)} &nbsp;|&nbsp; Řekl NE: {cell(a.ne)}</div>
      <div className="muted small">{a.text}</div>
    </div>
  );
}

export function JournalPanel({ state }: { state: BotState }) {
  const shadowBy = new Map(state.shadows.map((x) => [x.signalId, x]));
  const taken = rStats(state.shadows.filter((x) => x.taken));
  const rejected = rStats(state.shadows.filter((x) => !x.taken));
  // kdo mel pravdu: vysledek signalu, ktere agent pustil vs vetoval
  const agents = ["Validátor", "Trh teď", "Kalendář", "Statistik", "Risk", "Ďáblův advokát", "AI analytik"].map((name) => {
    const yes: Shadow[] = [], no: Shadow[] = [];
    for (const d of state.journal) {
      const sh = shadowBy.get(d.id);
      const op = d.opinions.find((o) => o.agent === name);
      if (sh && op) (op.vote === "ano" ? yes : no).push(sh);
    }
    return { name, yes: rStats(yes), no: rStats(no) };
  });
  const closed = state.broker.closed;
  // po strategiich: kolik signalu denne, uspesnost, prumer R a jak dlouho se drzi (scalp / daytrade / swing)
  const bySystem = [...new Set(state.shadows.map((x) => x.system))].map((id) => {
    const sh = state.shadows.filter((x) => x.system === id);
    const st = rStats(sh.filter((x) => x.taken));
    const all = rStats(sh);
    const days = new Set(sh.map((x) => new Date(x.openTime * 1000).toISOString().slice(0, 10))).size || 1;
    const held = closed.filter((c) => c.system === id).map((c) => c.closeTime - c.openTime);
    const avgHold = held.length ? held.reduce((a, b) => a + b, 0) / held.length : null;
    const style = avgHold == null ? "–" : avgHold < 3600 ? "scalp" : avgHold < 86400 ? "daytrade" : "swing";
    return { id, perDay: sh.length / days, st, all, avgHold, style };
  });
  const hold = (s: number | null) => s == null ? "–" : s < 3600 ? `${Math.round(s / 60)} min` : s < 86400 ? `${(s / 3600).toFixed(1)} h` : `${(s / 86400).toFixed(1)} dne`;
  return (
    <div className="journal">
      <div className="stats">
        <div className="stat">
          <div className="muted small">Přijaté signály (stínově)</div>
          <div>{taken.n} uzavř. · ⌀ {taken.mean.toFixed(2)} R · win {taken.win.toFixed(0)} %</div>
        </div>
        <div className="stat">
          <div className="muted small">Zamítnuté signály (stínově)</div>
          <div>{rejected.n} uzavř. · ⌀ {rejected.mean.toFixed(2)} R · win {rejected.win.toFixed(0)} %</div>
        </div>
        <div className="stat">
          <div className="muted small">Skutečné obchody (účet)</div>
          <div>{closed.length} · {money(closed.reduce((a, c) => a + c.pnl + c.swap, 0))}</div>
        </div>
      </div>
      <div className="muted small">
        Stínově = jak by signál dopadl, i když ho agenti zamítli (R = násobek rizika). Agenti mají smysl, jen když
        přijaté vycházejí lépe než zamítnuté – a to až po desítkách obchodů.
      </div>
      <table className="tbl">
        <thead><tr><th>Strategie</th><th>Signálů/den</th><th>Přijaté: uzavř. · win · ⌀ R</th><th>Všechny signály: win · ⌀ R</th><th>Drží ⌀</th><th>Styl</th></tr></thead>
        <tbody>
          {bySystem.map((r) => (
            <tr key={r.id}>
              <td>{SYSTEM[r.id]?.name ?? r.id}</td>
              <td>{r.perDay.toFixed(1)}</td>
              <td>{r.st.n} · {r.st.win.toFixed(0)} % · <span className={r.st.mean >= 0 ? "up" : "down"}>{r.st.mean.toFixed(2)} R</span></td>
              <td>{r.all.win.toFixed(0)} % · <span className={r.all.mean >= 0 ? "up" : "down"}>{r.all.mean.toFixed(2)} R</span></td>
              <td>{hold(r.avgHold)}</td>
              <td>{r.style}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <DecisionCard state={state} />
      <AiScoreCard shadows={state.shadows} />
      <ComboTable shadows={state.shadows} />
      <table className="tbl">
        <thead><tr><th>Agent</th><th>Když řekl ANO</th><th>Když řekl NE</th></tr></thead>
        <tbody>
          {agents.map((a) => (
            <tr key={a.name}>
              <td>{a.name}</td>
              <td>{a.yes.n} · ⌀ {a.yes.mean.toFixed(2)} R</td>
              <td>{a.no.n} · ⌀ {a.no.mean.toFixed(2)} R</td>
            </tr>
          ))}
        </tbody>
      </table>
      <table className="tbl">
        <thead><tr><th>Čas</th><th>Systém</th><th>Trh</th><th>Směr</th><th>Rozhodnutí</th><th>Kdo zastavil</th><th>Stínový výsledek</th><th>Bylo to dobře?</th></tr></thead>
        <tbody>
          {state.journal.slice(0, 100).map((d: Deliberation) => {
            const sh = shadowBy.get(d.id);
            return (
              <tr key={d.id}>
                <td className="small muted">{dt(d.time)}</td>
                <td className="small">{SYSTEM[d.signal.system]?.name ?? d.signal.system}</td>
                <td>{d.signal.market}</td>
                <td className={`dir ${d.signal.dir}`}>{d.signal.dir === "long" ? "BUY" : "SELL"}</td>
                <td><span className={`badge ${d.decision}`}>{d.decision === "beru" ? "BERU" : "NEBERU"}</span></td>
                <td className="small muted">{blockedBy(d).join(", ") || "–"}</td>
                <td className={sh?.r == null ? "muted" : sh.r >= 0 ? "up" : "down"}>
                  {sh?.r == null ? "běží" : `${sh.r >= 0 ? "+" : ""}${sh.r.toFixed(2)} R`}
                </td>
                {(() => {
                  const v = decisionVerdict(d, sh?.r);
                  return <td className={`small ${v.ok == null ? "muted" : v.ok ? "up" : "down"}`}>{v.ok == null ? v.text : `${v.ok ? "✓" : "✗"} ${v.text}`}</td>;
                })()}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function Settings({ bot, state }: { bot: Bot; state: BotState }) {
  const s = state.settings;
  return (
    <div className="settings">
      {bot.role === "viewer" && <div className="alert">Bota řídí jiné zařízení – nastavení změníš po převzetí řízení.</div>}
      <div className="muted small">Teď: <b>{s.statistikBlocks ? "jen ověřené" : "učící režim – bere všechno"}</b></div>
      <div className="row gap">
        <button className={`btn ${!s.statistikBlocks ? "on" : ""}`} onClick={() => bot.update((st) => {
          st.settings.statistikBlocks = false;
          st.settings.mode = "vse";
          for (const sys of SYSTEMS) st.settings.systems[sys.id] = true;
        })}>
          Učící režim – brát všechno
        </button>
        <span className="muted small">Všechny strategie obchodují na simulovaném účtu (i neověřené a ztrátové), aby bylo co
          nejvíc obchodů a šlo poznat, co funguje. Denní limit ztráty, drawdown 8 % ani cíl +8 % ho nezastaví; ostatní tvrdé kontroly platí dál.</span>
      </div>
      <div className="row gap">
        <button className={`btn ${s.statistikBlocks ? "on" : ""}`} onClick={() => bot.update((st) => {
          st.settings.statistikBlocks = true;
          for (const sys of SYSTEMS) if (sys.id.startsWith("ukazka")) st.settings.systems[sys.id] = false;
        })}>
          Obchodovat jen ověřené
        </button>
        <span className="muted small">Statistik začne vetovat vše neověřené (živě se pak obchoduje jen průraz z F2) a ukázky
          na 1m se vypnou. Ostatní strategie dál sbírají signály do statistiky.</span>
      </div>
      <h4>Režim po aktivaci</h4>
      <label className="row">
        <input type="radio" name="mode" checked={s.mode === "vse"} onChange={() => bot.update((st) => { st.settings.mode = "vse"; })} />
        <span><b>Bere co jde</b> – vezme každý obchod, který projde tvrdými kontrolami (Validátor, Trh teď, Risk).
          Statistik a Ďáblův advokát jen radí.</span>
      </label>
      <label className="row">
        <input type="radio" name="mode" checked={s.mode === "opatrny"} onChange={() => bot.update((st) => { st.settings.mode = "opatrny"; })} />
        <span><b>Opatrný</b> – když jsou proti aspoň dva poradci, nebere.</span>
      </label>
      <label className="row">
        <input type="checkbox" checked={s.statistikBlocks}
          onChange={(e) => bot.update((st) => { st.settings.statistikBlocks = e.target.checked; })} />
        <span><b>Statistik může vetovat</b> – jako v ostrém botovi. Vypnuto = v simulaci jen radí, aby šly obchody vidět.</span>
      </label>
      <label className="row">
        <input type="checkbox" checked={s.ai} onChange={(e) => bot.update((st) => { st.settings.ai = e.target.checked; })} />
        <span><b>AI analytik (Gemini)</b> – ke každému signálu napíše ANO/NE s důvodem.
          {bot.aiNote && <span className="down small"> Poslední problém: {bot.aiNote}</span>}</span>
      </label>
      <label className="row">
        <input type="checkbox" checked={s.aiVeto === "auto"} disabled={!s.ai}
          onChange={(e) => bot.update((st) => { st.settings.aiVeto = e.target.checked ? "auto" : "nikdy"; })} />
        <span><b>AI smí vetovat, až si to vyslouží</b> – {aiScore(state.shadows).text}</span>
      </label>
      <label className="row">
        <span>Riziko na obchod (H1 a ukázka)</span>
        <select value={s.riskPct} onChange={(e) => bot.update((st) => { st.settings.riskPct = +e.target.value; })}>
          {[0.1, 0.25, 0.5, 1].map((v) => <option key={v} value={v}>{v} %</option>)}
        </select>
      </label>
      <label className="row">
        <span>Denní limit ztráty (pak do konce dne jen sběr dat){!s.statistikBlocks && <b> – v učícím režimu neplatí</b>}</span>
        <select value={s.dailyLossPct} onChange={(e) => bot.update((st) => { st.settings.dailyLossPct = +e.target.value; })}>
          {[1, 1.5, 2, 3, 4].map((v) => <option key={v} value={v}>{v} %</option>)}
        </select>
      </label>
      <label className="row">
        <span>Poměr zisk : riziko (TP = násobek vzdálenosti SL)</span>
        <select value={s.rrr} onChange={(e) => bot.update((st) => { st.settings.rrr = +e.target.value; })}>
          {[1, 1.5, 2, 2.5, 3].map((v) => <option key={v} value={v}>1 : {v}</option>)}
        </select>
      </label>
      <label className="row">
        <span>Max. obchodů za den</span>
        <input type="number" min={1} max={200} value={s.maxTradesPerDay}
          onChange={(e) => bot.update((st) => { st.settings.maxTradesPerDay = Math.max(1, +e.target.value || 1); })} />
      </label>
      <h4>Strategie</h4>
      {SYSTEMS.map((sys) => (
        <label key={sys.id} className="row">
          <input type="checkbox" checked={!!s.systems[sys.id]}
            onChange={(e) => bot.update((st) => { st.settings.systems[sys.id] = e.target.checked; })} />
          <span><b>{sys.name}</b> <span className="muted small">({sys.markets.length > 3 ? `${sys.markets.length} trhů` : sys.markets.join(", ")}, {sys.tf})</span><br />
            <span className="muted small">{sys.desc}</span></span>
        </label>
      ))}
      <div className="row gap">
        <button className="btn" onClick={() => bot.requestMomentum()}>Rozhodnout momentum teď (všech 40 trhů)</button>
        <button className="btn danger" onClick={() => { if (confirm("Smazat účet, pozice i deník a začít znovu se 100 000 $? Nastavení i výběr strategií zůstanou, bota pak znovu aktivuj.")) bot.reset(); }}>
          Reset účtu
        </button>
      </div>
    </div>
  );
}

export function Log({ state }: { state: BotState }) {
  if (!state.log.length) return <div className="empty">Zatím prázdné.</div>;
  return (
    <div className="log">
      {state.log.slice(0, 100).map((l, i) => (
        <div key={i}><span className="muted">{dt(l.t)}</span> {l.text}</div>
      ))}
    </div>
  );
}
