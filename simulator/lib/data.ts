// Trzni data: krypto zive z Binance (WebSocket), ostatni z Yahoo pres /api/candles.
import type { Candle, Market, TF } from "./types";
import { TF_SEC } from "./types";
import { yahooCandles } from "./yahoo";

const BINANCE_REST = "https://data-api.binance.vision/api/v3/klines";
const BINANCE_WS = "wss://data-stream.binance.vision/ws";

export const nowSec = () => Math.floor(Date.now() / 1000);

export async function fetchCandles(m: Market, tf: TF, live = false): Promise<{ candles: Candle[]; delayed: number }> {
  if (m.binance) {
    const r = await fetch(`${BINANCE_REST}?symbol=${m.binance}&interval=${tf}&limit=${live ? 5 : 1000}`);
    if (!r.ok) throw new Error(`Binance vratil ${r.status}`);
    const rows: (string | number)[][] = await r.json();
    return {
      candles: rows.map((k) => ({ time: Number(k[0]) / 1000, open: +k[1], high: +k[2], low: +k[3], close: +k[4] })),
      delayed: 0,
    };
  }
  let j: { candles: Candle[]; delayed: number };
  if (typeof window === "undefined") {
    j = await yahooCandles(m, tf, live); // bot na serveru vola Yahoo primo
  } else {
    const r = await fetch(`/api/candles?symbol=${encodeURIComponent(m.id)}&tf=${tf}${live ? "&live=1" : ""}`);
    const body = (await r.json()) as { candles: Candle[]; delayed: number; error?: string };
    if (!r.ok) throw new Error(body.error ?? `chyba ${r.status}`);
    j = body;
  }
  const k = m.priceScale;
  if (k !== 1) {
    j.candles = j.candles.map((c) => ({ time: c.time, open: c.open * k, high: c.high * k, low: c.low * k, close: c.close * k }));
  }
  return j;
}

/** Spoji novejsi svicky do existujicich (stejny cas = prepsat, novejsi = pridat). */
export function merge(a: Candle[], b: Candle[]): Candle[] {
  if (!a.length) return b.slice();
  const out = a.slice();
  for (const c of b) {
    const last = out[out.length - 1];
    if (c.time > last.time) out.push(c);
    else if (c.time === last.time) out[out.length - 1] = c;
    else {
      const i = out.findIndex((x) => x.time === c.time);
      if (i >= 0) out[i] = c;
    }
  }
  return out;
}

/** Jen uzavrene svicky - posledni se muze jeste tvorit. */
export function closedCandles(c: Candle[], tf: TF, now: number): Candle[] {
  if (!c.length) return c;
  return c[c.length - 1].time + TF_SEC[tf] > now ? c.slice(0, -1) : c;
}

type Listener = (c: Candle[]) => void;

/** Sdilena pamet svicek pro graf i bota - kazdy trh/timeframe se stahuje jen jednou. */
class CandleStore {
  private data = new Map<string, Candle[]>();
  private fetched = new Map<string, number>();
  private inflight = new Map<string, Promise<Candle[]>>();
  private listeners = new Map<string, Set<Listener>>();
  readonly delayed = new Map<string, number>();
  readonly errors = new Map<string, string>();
  /** posledni znama stredni cena kazdeho trhu (z jakehokoli timeframu) */
  readonly lastPrice = new Map<string, { mid: number; t: number }>();

  key(m: Market, tf: TF) {
    return `${m.id}|${tf}`;
  }

  peek(m: Market, tf: TF): Candle[] {
    return this.data.get(this.key(m, tf)) ?? [];
  }

  /** Vrati svicky; kdyz jsou starsi nez maxAge sekund, doplni je. */
  get(m: Market, tf: TF, maxAge: number): Promise<Candle[]> {
    const k = this.key(m, tf);
    const have = this.data.get(k);
    if (have && nowSec() - (this.fetched.get(k) ?? 0) < maxAge) return Promise.resolve(have);
    const running = this.inflight.get(k);
    if (running) return running;
    const p = (async () => {
      try {
        // po delsi pauze (karta na pozadi, telefon se zhasnutym displejem) by kratke doplneni
        // nechalo v datech diru a zasah SL/TP v ni by se nezapocital -> stahne se cela historie
        const fresh = !!have?.length && nowSec() - have[have.length - 1].time < TF_SEC[tf] * 4;
        const { candles, delayed } = await fetchCandles(m, tf, fresh);
        const merged = have?.length ? merge(have, candles) : candles;
        this.set(m, tf, merged);
        this.delayed.set(m.id, delayed);
        this.errors.delete(k);
        return merged;
      } catch (e) {
        this.errors.set(k, (e as Error).message);
        if (have) return have;
        throw e;
      } finally {
        this.fetched.set(k, nowSec());
        this.inflight.delete(k);
      }
    })();
    this.inflight.set(k, p);
    return p;
  }

  push(m: Market, tf: TF, c: Candle) {
    this.set(m, tf, merge(this.peek(m, tf), [c]));
  }

  private set(m: Market, tf: TF, c: Candle[]) {
    const k = this.key(m, tf);
    this.data.set(k, c);
    if (c.length) {
      const last = c[c.length - 1];
      const prev = this.lastPrice.get(m.id);
      const t = Math.min(last.time + TF_SEC[tf], nowSec());
      if (!prev || t >= prev.t) this.lastPrice.set(m.id, { mid: last.close, t });
    }
    this.listeners.get(k)?.forEach((fn) => fn(c));
  }

  on(m: Market, tf: TF, fn: Listener): () => void {
    const k = this.key(m, tf);
    if (!this.listeners.has(k)) this.listeners.set(k, new Set());
    this.listeners.get(k)!.add(fn);
    return () => this.listeners.get(k)?.delete(fn);
  }
}

export const store = new CandleStore();

/** Zive obnovovani pro graf: Binance pres WebSocket, Yahoo kazdych 15 s. */
export function subscribeLive(m: Market, tf: TF): () => void {
  if (m.binance) {
    let ws: WebSocket | null = null;
    let stopped = false;
    let retry: ReturnType<typeof setTimeout> | undefined;
    const open = () => {
      ws = new WebSocket(`${BINANCE_WS}/${m.binance!.toLowerCase()}@kline_${tf}`);
      ws.onmessage = (e) => {
        const k = JSON.parse(e.data).k;
        store.push(m, tf, { time: k.t / 1000, open: +k.o, high: +k.h, low: +k.l, close: +k.c });
      };
      ws.onclose = () => {
        if (!stopped) retry = setTimeout(open, 3000);
      };
    };
    open();
    return () => {
      stopped = true;
      clearTimeout(retry);
      ws?.close();
    };
  }
  const id = setInterval(() => store.get(m, tf, 0).catch(() => {}), 15000);
  return () => clearInterval(id);
}
