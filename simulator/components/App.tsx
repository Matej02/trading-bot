"use client";

import { useEffect, useReducer, useRef, useState } from "react";
import Chart from "./Chart";
import AgentRoom from "./AgentRoom";
import Gate from "./Gate";
import { AccountPanel, ExportButtons, JournalPanel, Log, ManualTrade, Positions, Radar, Settings } from "./Panels";
import { getBot, type Bot } from "@/lib/bot";
import { store } from "@/lib/data";
import { BROKER_ACCOUNT, CHART_ORDER, fmt, MARKETS, quote } from "@/lib/markets";
import { SYSTEM } from "@/lib/strategies";
import type { Deliberation, TF } from "@/lib/types";

const TFS: TF[] = ["1m", "5m", "15m", "1h", "1d"];
const GROUPS: [string, string][] = [["CRYPTO", "Krypto"], ["FOREX", "Forex"], ["FUTURE CFDs", "Ropa"],
  ["MINI CASH CFDs", "Indexy"], ["METALS", "Kovy"]];
type Tab = "zive" | "pozice" | "denik" | "nastaveni" | "log";

export default function App() {
  const [bot, setBot] = useState<Bot | null>(null);
  const [, rerender] = useReducer((x: number) => x + 1, 0);
  const [marketId, setMarketId] = useState("BTCUSD");
  const [tf, setTf] = useState<TF>("1m");
  const [tab, setTab] = useState<Tab>("zive");
  const [toasts, setToasts] = useState<Deliberation[]>([]);
  const lastSeen = useRef<string | null>(null);
  const primed = useRef(false);

  useEffect(() => {
    const b = getBot();
    setBot(b);
    // upozorneni na kazde nove rozhodnuti agentu (ne na historii nactenou ze serveru)
    const off = b.on(() => {
      const j = b.state.journal;
      if (b.phase !== "ready" || !primed.current) {
        primed.current = b.phase === "ready";
        lastSeen.current = j[0]?.id ?? null;
        rerender();
        return;
      }
      const fresh: Deliberation[] = [];
      for (const d of j) {
        if (d.id === lastSeen.current) break;
        fresh.push(d);
      }
      if (fresh.length) {
        lastSeen.current = j[0].id;
        setToasts((t) => [...fresh.slice(0, 3), ...t].slice(0, 4));
        fresh.slice(0, 3).forEach((d) => setTimeout(() => setToasts((t) => t.filter((x) => x.id !== d.id)), 9000));
        // graf skoci na trh, kde se prave obchoduje
        const taken = fresh.find((d) => d.decision === "beru");
        if (taken && b.state.settings.follow) {
          const id = taken.signal.market;
          setMarketId(id);
          setTf((t) => (!MARKETS[id].binance && t === "1m" ? "1h" : t));
        }
      }
      rerender();
    });
    b.init();
    const id = setInterval(rerender, 1000); // ziva cena a P&L kazdou vterinu
    return () => {
      off();
      clearInterval(id);
    };
  }, []);

  if (!bot) return <div className="loading">Spouštím simulátor…</div>;
  if (bot.phase !== "ready") return <Gate bot={bot} />;
  const viewer = bot.role === "viewer";
  const s = bot.state;
  const m = MARKETS[marketId];
  const px = store.lastPrice.get(marketId);
  const q = px ? quote(m, px.mid, Math.floor(Date.now() / 1000)) : null;
  const delayed = store.delayed.get(marketId) ?? 0;
  const pick = (id: string) => {
    setMarketId(id);
    setTf((t) => (!MARKETS[id].binance && t === "1m" ? "1h" : t));
  };
  const on = s.settings.botOn;
  const today = new Date().toISOString().slice(0, 10);
  const todays = s.journal.filter((d) => new Date(d.time * 1000).toISOString().slice(0, 10) === today);
  const takenToday = todays.filter((d) => d.decision === "beru").length;

  return (
    <div className="app">
      <header className="top">
        <div className="brand">Simulátor <span className="muted">· živý trh</span></div>
        <select className="mk-select" value={marketId} onChange={(e) => pick(e.target.value)}>
          {GROUPS.map(([g, label]) => (
            <optgroup key={g} label={label}>
              {CHART_ORDER.filter((id) => MARKETS[id].group === g).map((id) => (
                <option key={id} value={id}>{id} – {MARKETS[id].name}</option>
              ))}
            </optgroup>
          ))}
        </select>
        <div className="tfs">
          {TFS.map((t) => (
            <button key={t} className={`tf ${t === tf ? "on" : ""}`} onClick={() => setTf(t)}>{t}</button>
          ))}
        </div>
        <div className="quote">
          {q ? (
            <>
              <span className="down">{fmt(m, q.bid)}</span>
              <span className="muted small"> spread {fmt(m, q.spread)} </span>
              <span className="up">{fmt(m, q.ask)}</span>
            </>
          ) : <span className="muted">–</span>}
        </div>
        <div className="src small muted">
          {m.binance ? "Binance · živě" : delayed ? `Yahoo · zpoždění ${delayed} min` : "Yahoo · skoro živě"}
        </div>
        <div className="storage small">
          {bot.mode === "server"
            ? <span className="up" title={bot.db === "soubor" ? "uloženo v souboru na tomhle počítači" : "uloženo v databázi"}>☁ účet na serveru</span>
            : <span className="warn" title={bot.setupNote}>⚠ jen v tomhle prohlížeči</span>}
          {bot.mode === "server" && (bot.serverTick && Date.now() - bot.serverTick.at < 15 * 60_000
            ? <span className="up" title={bot.serverTick.msg}> · server 24/7 před {Math.max(0, Math.round((Date.now() - bot.serverTick.at) / 60_000))} min</span>
            : <span className="warn" title={bot.serverTick?.msg ?? "cron zatím nikdy nespustil bota"}> · server 24/7 neběží</span>)}
          {bot.syncNote && <span className="down"> · {bot.syncNote}</span>}
          {bot.auth === "password" && <button className="link-btn" onClick={() => bot.logout()}>odhlásit</button>}
        </div>
        {viewer ? (
          <button className="activate go" onClick={() => bot.takeOver()}>⇄ PŘEVZÍT ŘÍZENÍ</button>
        ) : (
          <button className={`activate ${on ? "stop" : "go"}`} onClick={() => bot.activate(!on)}>
            {on ? "■ ZASTAVIT" : "▶ AKTIVOVAT"}
          </button>
        )}
      </header>

      {viewer ? (
        <div className="notice small">
          Bota teď řídí <b>{bot.lease?.label ?? "jiné zařízení"}</b> – tady jen sleduješ (obnovuje se každou minutu).
          Chceš obchodovat odsud? Klikni <b>PŘEVZÍT ŘÍZENÍ</b>, to druhé zařízení pak bude jen sledovat.
        </div>
      ) : on ? (
        <div className="live-strip">
          <span className="dot" /> <b>AKTIVNÍ</b>
          <span>{s.settings.mode === "vse" ? "bere každý obchod, který projde tvrdými kontrolami" : "opatrný režim – rozhoduje i většina poradců"}</span>
          <span className="sep">·</span>
          <span>dnes {todays.length} signálů, <b className="up">{takenToday} vzato</b>, {todays.length - takenToday} zamítnuto</span>
          <span className="sep">·</span>
          <span>{s.broker.positions.length} otevřených pozic</span>
          <label className="follow small">
            <input type="checkbox" checked={s.settings.follow}
              onChange={(e) => bot.update((st) => { st.settings.follow = e.target.checked; })} />
            graf skáče na nové obchody
          </label>
        </div>
      ) : (
        <div className="notice small">
          Bot je vypnutý. Klikni <b>AKTIVOVAT</b> vpravo nahoře – pak bere každý obchod, který projde tvrdými kontrolami
          (limity účtu, víkend, velikost pozice), a uvidíš ho v grafu, v Místnosti agentů i v upozorněních.
          SIMULACE – žádné skutečné peníze, podmínky z účtu {BROKER_ACCOUNT}. Běží, jen když je stránka otevřená.
          {bot.mode === "local" && " Data se teď ukládají jen v tomhle prohlížeči – po připojení databáze a hesla na Vercelu budou na serveru."}
        </div>
      )}

      <main className="main">
        <section className="left">
          <Chart marketId={marketId} tf={tf} positions={s.broker.positions} closed={s.broker.closed} journal={s.journal} />
          <div className="tabs">
            {([["zive", "Bot živě"], ["pozice", `Pozice (${s.broker.positions.length})`], ["denik", "Deník a stínové výsledky"],
              ["nastaveni", "Nastavení"], ["log", "Log"]] as [Tab, string][]).map(([k, label]) => (
              <button key={k} className={`tab ${tab === k ? "on" : ""}`} onClick={() => setTab(k)}>{label}</button>
            ))}
            {bot.status && <span className="small muted status">{bot.status}</span>}
          </div>
          <div className="tab-body">
            {tab === "zive" && (
              <>
                <ManualTrade bot={bot} marketId={marketId} tf={tf} />
                <div className="room-title flat">Co bot právě sleduje</div>
                <Radar bot={bot} />
              </>
            )}
            {tab === "pozice" && <Positions broker={s.broker} onClose={viewer ? undefined : (id) => bot.update(() => bot.closeAtMarket(id))} onPick={pick} />}
            {tab === "denik" && (
              <>
                <ExportButtons bot={bot} />
                <JournalPanel state={s} />
              </>
            )}
            {tab === "nastaveni" && <Settings bot={bot} state={s} />}
            {tab === "log" && <Log state={s} />}
          </div>
        </section>
        <aside className="right">
          <AccountPanel broker={s.broker} eq={bot.equityNow()} dailyLimit={s.settings.dailyLossPct} />
          <div className="room-title">Místnost agentů</div>
          <AgentRoom journal={s.journal} onPick={pick} />
        </aside>
      </main>

      <div className="toasts">
        {toasts.map((d) => (
          <button key={d.id} className={`toast ${d.decision}`} onClick={() => pick(d.signal.market)}>
            <span className={`badge ${d.decision}`}>{d.decision === "beru" ? "BERU" : "NEBERU"}</span>{" "}
            <b>{d.signal.market}</b> <span className={`dir ${d.signal.dir}`}>{d.signal.dir === "long" ? "BUY" : "SELL"}</span>
            <div className="small muted">{SYSTEM[d.signal.system]?.name} · {d.summary}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
