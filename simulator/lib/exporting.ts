// Stazeni dat: denik a obchody do CSV (cesky Excel: strednik, desetinna carka, BOM)
// a vsechno do jednoho JSON souboru (ten je nejlepsi poslat k rozboru).
import { SYSTEM } from "./strategies";
import { blockedBy, decisionVerdict } from "./verdict";
import type { ClosedTrade, CoreState, Deliberation, LogEntry, Shadow } from "./types";
import type { F93State } from "./server/f93Runner";

export interface ExportData {
  core: CoreState | null;
  journal: Deliberation[]; // chronologicky
  closed: ClosedTrade[]; // chronologicky
  shadows: Shadow[];
  log: LogEntry[]; // chronologicky
  f93?: F93State | null; // F93 vysledky firem - sledovani dopredu (jen ze serveru)
}

const AGENTS = ["Validátor", "Trh teď", "Kalendář", "Statistik", "Risk", "Ďáblův advokát", "AI analytik"];
const BOM = "﻿";

function cell(v: string | number | null | undefined): string {
  if (v == null) return "";
  const s = typeof v === "number" ? String(+v.toFixed(8)).replace(".", ",") : v;
  return /[;"\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function timeFmt(tz: string) {
  const f = new Intl.DateTimeFormat("sv-SE", {
    timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
  return (t: number) => f.format(new Date(t * 1000));
}

const csv = (rows: (string | number | null | undefined)[][]) => BOM + rows.map((r) => r.map(cell).join(";")).join("\r\n");
const sysName = (id: string) => SYSTEM[id]?.name ?? id;

export function journalCsv(d: ExportData, tz: string): string {
  const t = timeFmt(tz);
  const shadow = new Map(d.shadows.map((x) => [x.signalId, x]));
  const head = ["Čas", "Systém", "Trh", "Směr", "Cena signálu", "SL", "TP", "Rozhodnutí", "Loty", "Stínový výsledek (R)",
    "Bylo to dobré rozhodnutí?", "Kdo zastavil",
    "Rozhodčí", "Důvod signálu", ...AGENTS.flatMap((a) => [a, `${a} – proč`])];
  const rows = d.journal.map((j) => {
    const r = shadow.get(j.id)?.r;
    return [
      t(j.time), sysName(j.signal.system), j.signal.market, j.signal.dir === "long" ? "BUY" : "SELL", j.signal.price,
      j.signal.sl, j.signal.tp, j.decision === "beru" ? "BERU" : "NEBERU", j.lots, r == null ? "běží" : r,
      decisionVerdict(j, r).text, blockedBy(j).join(", "), j.summary,
      j.signal.reason,
      ...AGENTS.flatMap((a) => {
        const o = j.opinions.find((x) => x.agent === a);
        return o ? [`${o.vote === "ano" ? "ANO" : "NE"}${o.hard ? "" : " (rada)"}`, o.reason] : ["", ""];
      }),
    ];
  });
  return csv([head, ...rows]);
}

export function tradesCsv(d: ExportData, tz: string): string {
  const t = timeFmt(tz);
  const head = ["Otevřeno", "Zavřeno", "Trh", "Systém", "Směr", "Loty", "Vstup", "Výstup", "SL", "TP", "Důvod zavření",
    "P&L $", "Swap $", "Celkem $"];
  const rows = d.closed.map((c) => [
    t(c.openTime), t(c.closeTime), c.market, sysName(c.system), c.dir === "long" ? "BUY" : "SELL", c.lots, c.entry, c.exit,
    c.sl, c.tp, c.reason, +c.pnl.toFixed(2), +c.swap.toFixed(2), +(c.pnl + c.swap).toFixed(2),
  ]);
  return csv([head, ...rows]);
}

/** F93: signaly a vysledky sledovani dopredu (R = nasobek 1 ATR, jako v testu). */
export function f93Csv(d: ExportData): string {
  const head = ["Výsledky přijaty (NY)", "Den reakce", "Akcie", "z", "Směr", "Pořadí dne", "Pozdě", "Den obchodu", "Vstup (otevření)",
    "Výstup", "Stop zasažen", "R bez nákladů", "R běžné náklady", "R pesimistické"];
  const rows = (d.f93?.trades ?? []).map((t) => [
    t.event, t.dayD, t.ticker, +t.z.toFixed(3), t.dir > 0 ? "BUY" : "SELL", t.rank, t.late ? "ano" : "ne", t.dayK ?? "čeká",
    t.result?.entry, t.result?.exit, t.result ? (t.result.stopHit ? "ano" : "ne") : "", t.result?.rGross, t.result?.rNorm, t.result?.rPess,
  ]);
  return csv([head, ...rows]);
}

export function fullJson(d: ExportData): string {
  return JSON.stringify({ exported: new Date().toISOString(), note: "casy jsou unix sekundy (UTC)", ...d }, null, 1);
}

export function exportFile(d: ExportData, format: string, tz: string) {
  const day = new Date().toISOString().slice(0, 10);
  if (format === "journal") return { body: journalCsv(d, tz), name: `denik-${day}.csv`, type: "text/csv; charset=utf-8" };
  if (format === "f93") return { body: f93Csv(d), name: `f93-vysledky-firem-${day}.csv`, type: "text/csv; charset=utf-8" };
  if (format === "trades") return { body: tradesCsv(d, tz), name: `obchody-${day}.csv`, type: "text/csv; charset=utf-8" };
  return { body: fullJson(d), name: `simulator-data-${day}.json`, type: "application/json; charset=utf-8" };
}
