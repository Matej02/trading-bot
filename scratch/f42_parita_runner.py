"""Kontrola shody: rozhodovani runneru (f2x_live.rsi2_signal / rsi2_exit) vs. test F42 na dennich datech brokera 2019-2026."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"D:\Trading bot")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_live as FX  # noqa: E402
import f42_rsi2 as F  # noqa: E402

tot = ok_sig = ok_exit = n_tr = 0
for mk in F.US:
    d = F.broker(mk)
    c = d.close
    s200, s5, rsi = c.rolling(200).mean(), c.rolling(5).mean(), F.rsi_wilder(c)
    test_sig = ((c > s200) & (rsi < 10)).to_numpy()
    days = [x.date() for x in d.index]
    cl = [float(x) for x in c]
    for i in range(260, len(d)):
        s, _ = FX.rsi2_signal(days[: i + 1], cl[: i + 1])
        tot += 1
        ok_sig += (bool(s) == bool(test_sig[i]))
        if test_sig[i] and i + 1 < len(d):
            e = i + 1
            # test: prvni k >= e s C>S5 nebo k == e+9
            kt = next((k for k in range(e, min(e + 10, len(d))) if cl[k] > s5.iloc[k] or k == e + 9), None)
            kr = None
            for k in range(e, min(e + 11, len(d))):
                if FX.rsi2_exit(days[: k + 1], cl[: k + 1], days[e]):
                    kr = k
                    break
            n_tr += 1
            ok_exit += (kt == kr)
print(f"signál: shoda {ok_sig}/{tot} dní; výstup (den): shoda {ok_exit}/{n_tr} signálů")
