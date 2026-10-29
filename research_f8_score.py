"""F8 test C: makro skore (Trading Analyzer, CSV z FM 2017-2024) -> research_data/f8/f8_skore.txt
Signal ze skore dne s se obchoduje az na close dne s+1 (nevime, kdy byl snimek). Vynos v ATR(14) D1, minus spread."""
import glob
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L

OUT = []
SPLIT = pd.Timestamp("2022-01-01")


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def daily(pair):
    f = os.path.join("research_data", f"{pair}_H1.pkl")
    if not os.path.exists(f):
        return None
    df = pd.read_pickle(f)
    idx = df.index.tz_localize("Europe/London", ambiguous="NaT", nonexistent="shift_forward")
    ok = ~idx.isna()
    df, idx = df[ok], idx[ok]
    ny = idx.tz_convert("America/New_York").tz_localize(None)
    day = (ny + pd.Timedelta(hours=7)).normalize()
    d = df.groupby(day.values).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"))
    d = d[d.index.dayofweek < 5]
    d["atr"] = L.wilder_atr(d.h.to_numpy(), d.l.to_numpy(), d.c.to_numpy(), 14)
    pip = 0.01 if "JPY" in pair else 0.0001
    b = L.BROKER.get(pair)
    spr = float(np.median(b["spreadByHour"])) if b else 2.5 * pip  # krize bez dat brokera: 2,5 pipu
    d["cost_atr"] = spr / d.atr
    return d


def main():
    ev = []
    lev = []
    for f in sorted(glob.glob(os.path.join("research_data", "fm_score", "*.csv"))):
        pair = os.path.basename(f)[:-4].replace("_", "")
        s = pd.read_csv(f, parse_dates=["timestamp"]).sort_values("timestamp").set_index("timestamp").score
        d = daily(pair)
        if d is None:
            p(pair, "bez cen, vynecháno")
            continue
        c = d.c
        # vstup na close prvniho obchodniho dne PO dni skore
        pos = c.index.searchsorted(s.index, side="right")
        valid = pos < len(c)
        s = s[valid]
        pos = pos[valid]
        d1 = s.diff()
        d5 = s.diff(5)
        for i, (ts, sc) in enumerate(s.items()):
            e = pos[i]
            atr = d.atr.iloc[e]
            if not np.isfinite(atr) or atr <= 0:
                continue
            fwd = {}
            for N in (5, 10, 20):
                if e + N < len(c):
                    fwd[N] = (c.iloc[e + N] - c.iloc[e]) / atr
            for name, dd in (("d1", d1.iloc[i]), ("d5", d5.iloc[i])):
                if np.isfinite(dd) and abs(dd) >= 2:
                    dirn = 1 if dd > 0 else -1
                    for N, r in fwd.items():
                        ev.append(dict(pair=pair, ts=ts, sig=name, N=N, d=dirn, R=dirn * r - d.cost_atr.iloc[e]))
            # baseline: vsechny dny, oba smery (drift)
            for N, r in fwd.items():
                ev.append(dict(pair=pair, ts=ts, sig="vse_long", N=N, d=1, R=r - d.cost_atr.iloc[e]))
            # level bias
            if abs(sc) >= 5 and e + 1 < len(c):
                dirn = 1 if sc > 0 else -1
                lev.append(dict(pair=pair, ts=ts, d=dirn, R=dirn * (c.iloc[e + 1] - c.iloc[e]) / atr))
    E = pd.DataFrame(ev)
    E["oos"] = E.ts >= SPLIT
    p("TEST C – makro skóre FM (změna >= 2 body → směr; výnos v ATR D1 po spreadu; DEV 2017–2021, OOS 2022–2024-10)")
    for (sig, N), g in E.groupby(["sig", "N"]):
        for per, gg in (("DEV", g[~g.oos]), ("OOS", g[g.oos])):
            r = gg.R.to_numpy()
            t = r.mean() / (r.std(ddof=1) / np.sqrt(len(r))) if len(r) > 2 else np.nan
            p(f"  {sig:9s} N={N:2d} {per}: n={len(r):5d}  průměr {r.mean():+.3f} ATR  zásah {np.mean(r > 0) * 100:4.1f}%  t={t:+.2f} (překryv → t nadsazené)")
    Lv = pd.DataFrame(lev)
    Lv["oos"] = Lv.ts >= SPLIT
    p("  Bias |skóre| >= 5, držet 1 den (denní rebalance, bez nákladů na přepnutí):")
    for per, gg in (("DEV", Lv[~Lv.oos]), ("OOS", Lv[Lv.oos])):
        r = gg.R.to_numpy()
        p(f"   {per}: n={len(r)} průměr {r.mean():+.4f} ATR/den, zásah {np.mean(r > 0) * 100:.1f}%, Sharpe/den {r.mean() / r.std():+.3f}")
    open(os.path.join("research_data", "f8", "f8_skore.txt"), "w", encoding="utf-8").write("\n".join(OUT))


main()
