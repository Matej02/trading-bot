"use client";

import { useEffect, useRef, useState } from "react";
import {
  ColorType, CrosshairMode, LineStyle, TickMarkType, createChart,
  type IChartApi, type IPriceLine, type ISeriesApi, type SeriesMarker, type Time, type UTCTimestamp,
} from "lightweight-charts";

// cas v grafu v mistnim pasmu prohlizece (knihovna sama ukazuje UTC)
const fmtIn = (o: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat("cs-CZ", o);
const F_TIME = fmtIn({ hour: "2-digit", minute: "2-digit" });
const F_DAY = fmtIn({ day: "numeric", month: "numeric" });
const F_MONTH = fmtIn({ month: "short" });
const F_YEAR = fmtIn({ year: "numeric" });
const F_FULL = fmtIn({ day: "numeric", month: "numeric", year: "2-digit", hour: "2-digit", minute: "2-digit" });
const asDate = (t: Time) => new Date((t as number) * 1000);
function tickMark(t: Time, type: TickMarkType) {
  const d = asDate(t);
  if (type === TickMarkType.Year) return F_YEAR.format(d);
  if (type === TickMarkType.Month) return F_MONTH.format(d);
  if (type === TickMarkType.DayOfMonth) return F_DAY.format(d);
  return F_TIME.format(d);
}
import { store, subscribeLive } from "@/lib/data";
import { MARKETS } from "@/lib/markets";
import type { Candle, ClosedTrade, Deliberation, Position, TF } from "@/lib/types";

interface Props {
  marketId: string;
  tf: TF;
  positions: Position[];
  closed: ClosedTrade[];
  journal: Deliberation[];
}

const toBar = (c: Candle) => ({ time: c.time as UTCTimestamp, open: c.open, high: c.high, low: c.low, close: c.close });

export default function Chart({ marketId, tf, positions, closed, journal }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const series = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const lines = useRef<IPriceLine[]>([]);
  const candlesRef = useRef<Candle[]>([]);
  // meni se jen pri nove svicce, ne pri kazdem ticku - znacky se neprekresluji zbytecne
  const [barKey, setBarKey] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const m = MARKETS[marketId];

  // graf jednou
  useEffect(() => {
    if (!box.current) return;
    const c = createChart(box.current, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: "#131722" }, textColor: "#b2b5be", fontSize: 12 },
      grid: { vertLines: { color: "#1f2330" }, horzLines: { color: "#1f2330" } },
      crosshair: { mode: CrosshairMode.Normal },
      localization: { locale: "cs-CZ", timeFormatter: (t: Time) => F_FULL.format(asDate(t)) },
      timeScale: { timeVisible: true, secondsVisible: false, borderColor: "#2a2e39", tickMarkFormatter: tickMark },
      rightPriceScale: { borderColor: "#2a2e39" },
    });
    series.current = c.addCandlestickSeries({
      upColor: "#26a69a", downColor: "#ef5350", borderVisible: false, wickUpColor: "#26a69a", wickDownColor: "#ef5350",
    });
    chart.current = c;
    return () => {
      c.remove();
      chart.current = null;
      series.current = null;
      lines.current = [];
    };
  }, []);

  // data trhu + zive obnovovani
  useEffect(() => {
    if (!series.current) return;
    series.current.applyOptions({ priceFormat: { type: "price", precision: m.digits, minMove: 1 / 10 ** m.digits } });
    series.current.setData([]);
    candlesRef.current = [];
    setBarKey("");
    setErr(null);
    let first = true;
    const show = (c: Candle[]) => {
      candlesRef.current = c;
      setBarKey(`${marketId}|${tf}|${c.length}|${c[c.length - 1].time}`);
    };
    const off = store.on(m, tf, (c) => {
      if (!series.current || !c.length) return;
      const prev = candlesRef.current;
      if (first || prev.length === 0 || c.length - prev.length > 1 || c[0].time !== prev[0].time) {
        series.current.setData(c.map(toBar));
        if (first) chart.current?.timeScale().scrollToRealTime();
        first = false;
      } else {
        series.current.update(toBar(c[c.length - 1]));
      }
      show(c);
    });
    const have = store.peek(m, tf);
    if (have.length) {
      series.current.setData(have.map(toBar));
      show(have);
      first = false;
    }
    store.get(m, tf, 0).catch((e) => setErr((e as Error).message));
    const stop = subscribeLive(m, tf);
    return () => {
      off();
      stop();
    };
  }, [marketId, tf, m]);

  // bot pole meni na miste (push/unshift) -> zmeny se poznaji podle obsahu, ne podle reference
  const journalKey = `${journal.length}|${journal[0]?.id ?? ""}|${journal[0]?.positionId ?? ""}`;
  const closedKey = `${closed.length}|${closed[0]?.id ?? ""}`;
  const posKey = positions.map((p) => `${p.id}:${p.sl}:${p.tp}`).join(",");

  // vstupy (sipky), zamitnute signaly (sede x) a vystupy (ctverecky s vysledkem)
  useEffect(() => {
    const s = series.current;
    const candles = candlesRef.current;
    if (!s || !candles.length) return;
    const snap = (t: number) => {
      // znacka musi sedet na cas svicky, ve ktere udalost nastala
      if (t < candles[0].time) return null;
      let lo = 0, hi = candles.length - 1;
      while (lo < hi) {
        const mid = (lo + hi + 1) >> 1;
        if (candles[mid].time <= t) lo = mid;
        else hi = mid - 1;
      }
      return candles[lo].time;
    };
    const mk: SeriesMarker<Time>[] = [];
    for (const d of journal) {
      if (d.signal.market !== marketId) continue;
      const t = snap(d.time);
      if (t == null) continue;
      const long = d.signal.dir === "long";
      if (d.decision === "neberu") {
        mk.push({ time: t as UTCTimestamp, position: long ? "belowBar" : "aboveBar", color: "#787b86", shape: "circle", text: "×" });
      } else {
        mk.push({ time: t as UTCTimestamp, position: long ? "belowBar" : "aboveBar", color: long ? "#2962ff" : "#e91e63",
          shape: long ? "arrowUp" : "arrowDown", text: long ? "BUY" : "SELL" });
      }
    }
    for (const c of closed) {
      if (c.market !== marketId) continue;
      const t = snap(c.closeTime);
      if (t == null) continue;
      const win = c.pnl + c.swap >= 0;
      mk.push({ time: t as UTCTimestamp, position: c.dir === "long" ? "aboveBar" : "belowBar", color: win ? "#26a69a" : "#ef5350",
        shape: "square", text: `${c.reason} ${win ? "+" : ""}${(c.pnl + c.swap).toFixed(0)}$` });
    }
    mk.sort((a, b) => (a.time as number) - (b.time as number));
    s.setMarkers(mk);
  }, [barKey, closedKey, journalKey, marketId]);

  // vstup, SL a TP otevrenych pozic jako cary
  const ready = barKey !== "";
  useEffect(() => {
    const s = series.current;
    if (!s || !ready) return;
    lines.current.forEach((l) => s.removePriceLine(l));
    lines.current = [];
    for (const p of positions) {
      if (p.market !== marketId) continue;
      lines.current.push(s.createPriceLine({ price: p.entry, color: "#2962ff", lineWidth: 1, lineStyle: LineStyle.Solid,
        axisLabelVisible: true, title: `${p.dir === "long" ? "BUY" : "SELL"} ${p.lots}` }));
      lines.current.push(s.createPriceLine({ price: p.sl, color: "#ef5350", lineWidth: 1, lineStyle: LineStyle.Dashed,
        axisLabelVisible: true, title: "SL" }));
      if (p.tp != null) {
        lines.current.push(s.createPriceLine({ price: p.tp, color: "#26a69a", lineWidth: 1, lineStyle: LineStyle.Dashed,
          axisLabelVisible: true, title: "TP" }));
      }
    }
  }, [posKey, marketId, ready]);

  return (
    <div className="chart-wrap">
      <div ref={box} className="chart" />
      {!barKey && <div className="chart-msg">{err ? `Data se nepodařilo načíst: ${err}` : "Načítám svíčky…"}</div>}
    </div>
  );
}
