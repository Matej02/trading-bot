"use client";

import { useState } from "react";
import { MARKETS, fmt } from "@/lib/markets";
import { SYSTEM } from "@/lib/strategies";
import type { Deliberation } from "@/lib/types";

const INITIAL: Record<string, string> = { "Validátor": "V", "Trh teď": "T", "Statistik": "S", "Risk": "R", "Ďáblův advokát": "Ď" };
const time = (t: number) => new Date(t * 1000).toLocaleTimeString("cs-CZ", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
const date = (t: number) => new Date(t * 1000).toLocaleDateString("cs-CZ", { day: "numeric", month: "numeric" });

export default function AgentRoom({ journal, onPick }: { journal: Deliberation[]; onPick: (market: string) => void }) {
  const [open, setOpen] = useState<string | null>(null);
  if (!journal.length) {
    const d = new Date();
    const local = (h: number) => new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), h)).getHours();
    return (
      <div className="empty">
        Zatím žádný signál. Ukázky na 1m kryptu se ozvou obvykle do pár minut, H1 strategie jen ve 13–17 UTC
        ({local(13)}–{local(17)} u nás), momentum jednou denně v {local(15)}:00 a {local(19)}:00 našeho času.
        Nebo pošli vlastní obchod tlačítky BUY / SELL v záložce Bot živě.
      </div>
    );
  }
  return (
    <div className="room">
      {journal.slice(0, 40).map((d, i) => {
        const expanded = open ? open === d.id : i < 2;
        const m = MARKETS[d.signal.market];
        const isNew = Date.now() / 1000 - d.time < 60;
        return (
          <div key={d.id} className={`card ${d.decision}${isNew ? " new" : ""}`}>
            <button className="card-head" onClick={() => setOpen(expanded ? "__none" : d.id)}>
              <span className="muted">{date(d.time)} {time(d.time)}</span>
              <span className="sys">{SYSTEM[d.signal.system]?.name ?? d.signal.system}</span>
              <span
                className="mk link"
                onClick={(e) => {
                  e.stopPropagation();
                  onPick(d.signal.market);
                }}
              >
                {d.signal.market}
              </span>
              <span className={`dir ${d.signal.dir}`}>{d.signal.dir === "long" ? "BUY" : "SELL"}</span>
              <span className={`badge ${d.decision}`}>{d.decision === "beru" ? "BERU" : "NEBERU"}</span>
            </button>
            {expanded && (
              <div className="card-body">
                <div className="sig">
                  <b>Signál:</b> {d.signal.reason} Cena {fmt(m, d.signal.price)}, SL {fmt(m, d.signal.sl)}
                  {d.signal.tp != null ? `, TP ${fmt(m, d.signal.tp)}` : ", bez TP"}.
                </div>
                {d.opinions.map((o) => (
                  <div key={o.agent} className="op">
                    <span className={`av ${o.vote}`}>{INITIAL[o.agent] ?? o.agent[0]}</span>
                    <div>
                      <div>
                        <b>{o.agent}</b> <span className={`vote ${o.vote}`}>{o.vote === "ano" ? "ANO" : "NE"}</span>
                        <span className="muted small"> {o.hard ? "· může vetovat" : "· jen radí"} · {o.role}</span>
                      </div>
                      <div className="reason">{o.reason}</div>
                    </div>
                  </div>
                ))}
                <div className="op judge">
                  <span className={`av ${d.decision === "beru" ? "ano" : "ne"}`}>⚖</span>
                  <div>
                    <b>Rozhodčí</b>
                    <div className="reason">{d.summary}{d.lots ? ` Otevírám ${d.lots} lotu.` : ""}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
