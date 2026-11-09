"""
F33 na MT5 s PC do 20:00: vstup na otevreni L-2 (9:30 NY = 15:30 Praha, jako v testu) a vystup v L v 19:45 Praha
(misto zavreni 16:00 NY). Popisne porovnani s vystupem na zavreni, minutova data (HistData do 2019-02, broker potom).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "f33_rebal.py"), encoding="utf-8").read()
ns = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "f33_rebal.py")}
exec(compile(src.split('say("F33 Rebalancování')[0], "f33", "exec"), ns)
SIG = ns["SIG"]
rows = []
for mk in ("SPX500mini", "NAS100mini"):
    for src_, lo, hi in (("hd", None, LB.SPLIT), ("broker", LB.SPLIT, None)):
        d = LB.load_m1(mk, src_)
        if lo is not None:
            d = d[d.u >= lo]
        if hi is not None:
            d = d[d.u < hi]
        tick = LB.add_costs(mk, d, LB.broker_ref(mk))
        ny = d.u.dt.tz_convert("America/New_York")
        pr = d.u.dt.tz_convert("Europe/Prague")
        d = d.assign(date=ny.dt.date, mod=ny.dt.hour * 60 + ny.dt.minute, prmod=pr.dt.hour * 60 + pr.dt.minute)
        atr = LB.daily_atr(d, "America/New_York")
        by = {k: g for k, g in d.groupby("date")}
        for (y, m), (dd, d_sig, d_in, d_out, diff) in SIG.items():
            gi, go = by.get(d_in.date()), by.get(d_out.date())
            a = atr.get(d_in.date(), np.nan)
            if gi is None or go is None or not a > 0:
                continue
            e = gi[(gi["mod"] >= 570) & (gi["mod"] <= 575)]
            xc = go[(go["mod"] >= 955) & (go["mod"] <= 959)]
            x19 = go[go.prmod >= 19 * 60 + 45]
            if e.empty or xc.empty or x19.empty:
                continue
            E = e.o.iloc[0] + (e.spr.iloc[0] + tick if dd == 1 else -tick)

            def pnl(X, spr):
                X = X - tick if dd == 1 else X + spr + tick
                return dd * (X - E) / a
            rows.append(dict(mk=mk, ym=(y, m), t=e.u.iloc[0], R_close=pnl(xc.c.iloc[-1], xc.spr.iloc[-1]),
                             R_1945=pnl(x19.o.iloc[0], x19.spr.iloc[0]), d=dd))
T = pd.DataFrame(rows)
M = T.groupby("ym").agg(R_close=("R_close", "mean"), R_1945=("R_1945", "mean"), t=("t", "first"))
for name, g in (("2010–2018", M[M.t < LB.SPLIT]), ("2019–2026", M[M.t >= LB.SPLIT]), ("celé", M)):
    s1, s2 = LB.st(g.R_close), LB.st(g.R_1945)
    print(f"{name:10s} výstup na zavření 16:00 NY: {LB.fmt(s1)}")
    print(f"{'':10s} výstup 19:45 Praha:        {LB.fmt(s2)}")
