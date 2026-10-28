// Zpetne hodnoceni rozhodnuti: kazdy signal (vzaty i nevzaty) se sleduje jako stinovy obchod az do SL / TP /
// konce drzeni. Podle toho, jak by dopadl, se rozhodnuti oznaci jako spravne nebo spatne.
import type { Deliberation, Shadow } from "./types";

export interface DecisionVerdict { ok: boolean | null; text: string }

export function decisionVerdict(d: Pick<Deliberation, "decision">, r: number | null | undefined): DecisionVerdict {
  if (r == null) return { ok: null, text: "ještě běží" };
  const R = `${Math.abs(r).toFixed(2)} R`;
  if (d.decision === "beru") return r > 0 ? { ok: true, text: `správně – vydělal ${R}` } : { ok: false, text: `špatně – prodělal ${R}` };
  return r > 0 ? { ok: false, text: `chyba – ušlo ${R}` } : { ok: true, text: `správně – ušetřeno ${R}` };
}

/** Kdo obchod zastavil: tvrda veta, jinak poradci proti (rezim "opatrny"). */
export function blockedBy(d: Deliberation): string[] {
  if (d.decision === "beru") return [];
  const hard = d.opinions.filter((o) => o.hard && o.vote === "ne").map((o) => o.agent);
  return hard.length ? hard : d.opinions.filter((o) => o.vote === "ne").map((o) => o.agent);
}

export interface DecisionStats {
  n: number; correct: number;
  takenN: number; takenOk: number;
  rejN: number; rejOk: number; saved: number; missed: number; // R: zamitnute ztratove (usetreno) / ziskove (uslo)
  byBlocker: { agent: string; n: number; ok: number; net: number }[]; // net = usetreno - uslo
}

export function decisionStats(journal: Deliberation[], shadows: Shadow[]): DecisionStats {
  const sh = new Map(shadows.map((x) => [x.signalId, x]));
  const s: DecisionStats = { n: 0, correct: 0, takenN: 0, takenOk: 0, rejN: 0, rejOk: 0, saved: 0, missed: 0, byBlocker: [] };
  const by = new Map<string, { agent: string; n: number; ok: number; net: number }>();
  for (const d of journal) {
    const r = sh.get(d.id)?.r;
    if (r == null) continue;
    const ok = decisionVerdict(d, r).ok!;
    s.n++;
    if (ok) s.correct++;
    if (d.decision === "beru") {
      s.takenN++;
      if (ok) s.takenOk++;
      continue;
    }
    s.rejN++;
    if (ok) { s.rejOk++; s.saved += -r; } else s.missed += r;
    for (const a of blockedBy(d)) {
      const b = by.get(a) ?? { agent: a, n: 0, ok: 0, net: 0 };
      b.n++;
      if (ok) b.ok++;
      b.net += -r;
      by.set(a, b);
    }
  }
  s.byBlocker = [...by.values()].sort((a, b) => b.n - a.n);
  return s;
}
