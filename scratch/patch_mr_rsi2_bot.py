"""Bot: TP podle systemu (noTp) a vystup podle pravidla (exitRule sma5) pro skutecne i stinove obchody."""
import os

os.chdir(r"D:\Trading bot\simulator")


def edit(p, pairs):
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert old in s, (p, old[:80])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8").write(s)


edit("lib/strategies.ts", [
    ("""export interface BarSignal {
  dir: Dir;
  sl: number;
  tp: number;
  reason: string;
}""", """export interface BarSignal {
  dir: Dir;
  sl: number;
  tp: number | null; // null = bez TP (system s pravidlem vystupu)
  reason: string;
}"""),
])

edit("lib/bot.ts", [
    ("""    if (prev == null || last.time <= prev) return;
    const bs = barSignal(systemId, win);""", """    if (prev == null || last.time <= prev) return;
    if (sys.exitRule) this.ruleExit(systemId, id, closed);
    const bs = barSignal(systemId, win);"""),
    ("""    const rrr = this.state.settings.rrr;
    await this.handleSignal({
      id: `${systemId}-${id}-${last.time}`, system: systemId, market: id, dir: bs.dir, price: last.close,
      time: last.time + TF_SEC[sys.tf], barTime: last.time, sl: bs.sl,
      tp: last.close + (bs.dir === "long" ? 1 : -1) * rrr * Math.abs(last.close - bs.sl),
      reason: `${bs.reason} RRR 1:${rrr}.`, riskPct: this.state.settings.riskPct,
    }, closed);
  }""", """    const rrr = this.state.settings.rrr;
    await this.handleSignal({
      id: `${systemId}-${id}-${last.time}`, system: systemId, market: id, dir: bs.dir, price: last.close,
      time: last.time + TF_SEC[sys.tf], barTime: last.time, sl: bs.sl,
      tp: sys.noTp ? null : last.close + (bs.dir === "long" ? 1 : -1) * rrr * Math.abs(last.close - bs.sl),
      reason: sys.noTp ? bs.reason : `${bs.reason} RRR 1:${rrr}.`, riskPct: this.state.settings.riskPct,
    }, closed);
  }

  /** Vystup podle pravidla strategie na zavreni svicky (napr. nad SMA5) - skutecne pozice i stinove obchody. */
  private ruleExit(systemId: string, id: string, closed: Candle[]) {
    const s = this.state;
    const sys = SYSTEM[systemId];
    const last = closed[closed.length - 1];
    if (sys.exitRule !== "sma5" || closed.length < 5) return;
    const sma5 = closed.slice(-5).reduce((a, c) => a + c.close, 0) / 5;
    const out = (dir: string) => (dir === "long" ? last.close > sma5 : last.close < sma5);
    const why = `zavření ${last.close} ${"nad/pod"} SMA5 ${sma5.toFixed(MARKETS[id].digits)}`.replace("nad/pod", last.close > sma5 ? "nad" : "pod");
    for (const p of s.broker.positions.filter((x) => x.system === systemId && x.market === id && x.openTime <= last.time + TF_SEC[sys.tf])) {
      if (out(p.dir)) this.closeAtMarket(p.id, why);
    }
    const px = store.lastPrice.get(id)?.mid;
    if (px == null) return;
    const now = nowSec();
    for (const x of s.shadows.filter((y) => y.system === systemId && y.market === id && y.r == null && y.openTime <= last.time + TF_SEC[sys.tf])) {
      if (!out(x.dir)) continue;
      const q = quote(MARKETS[id], px, now);
      x.r = (((x.dir === "long" ? q.bid : q.ask) - x.entry) * (x.dir === "long" ? 1 : -1)) / Math.abs(x.entry - x.sl);
      x.checkedTo = now;
      this.recordShadow(x, false);
      this.logVerdict(x);
    }
  }"""),
])
print("ok")
