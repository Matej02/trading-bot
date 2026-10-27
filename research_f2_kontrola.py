"""
F2 - kontrolni skupina pro proraz 1d s tydennim trendem (SL 2 ATR): pridava samotny proraz neco,
nebo staci byt kazdy den ve smeru tydenniho trendu? Stejne trhy, stejne SL/TP, stejne naklady vcetne swapu.
Kdyz kontrola vyjde stejne, vysledek F2 je jen "byt long v rostoucim trhu" (drift), ne vyhoda vstupu.
"""
import numpy as np
import pandas as pd

import research_f2 as f
from research_f2_detail import line


def run(k, rrr, every_day):
    out = []
    for mk in list(f.BINANCE) + f.MT5_MARKETS:
        df = f.load(mk, "1d")
        b = f.broker[mk]
        spread = np.array(b["spreadByHour"])[df.index.hour]
        t = (df.index.astype("int64") // 10**9).values.astype(np.int64)
        o, h, l, c = (df[x].values for x in ("open", "high", "low", "close"))
        a = f.atr(h, l, c)
        trend = f.htf_trend(df, "1D", "1W", 86400)
        if every_day:
            sig = trend.astype(np.int8)  # kazdy den ve smeru trendu (po skonceni obchodu hned dalsi)
        else:
            raw = f.signals(df, "proraz")
            sig = np.where(raw == trend, raw, 0).astype(np.int8)
        e, d, r, bars = f.simulate(t, o, h, l, c, spread, sig, a, k, rrr, f.MAX_HOLD, 86400 * 4 + 3 * 86400)
        entry = o[e] + d * spread[e] / 2
        dist = k * a[e - 1]
        nights = bars * (1.0 if b["group"] == "CRYPTO" else 1.4)
        swap_r = np.where(d == 1, b["swapLong"], b["swapShort"]) * entry * nights / dist
        out.append(pd.DataFrame({"time": df.index[e], "dir": d, "R": r + swap_r, "bars": bars}))
    return pd.concat(out, ignore_index=True)


for rrr in (1.5, 2.0):
    print(f"\n=== SL 2 ATR, RRR 1:{rrr}, vse se swapem ===")
    for name, ed in (("proraz + trend", False), ("kazdy den + trend", True)):
        tr = run(2.0, rrr, ed)
        for part, x in (("vyber do 2023", tr[tr.time < f.SPLIT]), ("holdout 2024+", tr[tr.time >= f.SPLIT])):
            print(line(f"{name} | {part}", x, "R"))
            print(line(f"   z toho longy", x[x.dir == 1], "R"))
