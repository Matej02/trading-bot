"""Export vstupu pro kontrolu shody TS/Python (F33, F29, F31) do research_data/f2x_parita.json."""
import json
import os
import sys

import numpy as np
import pandas as pd

RD = r"D:\Trading bot\research_data"


def cand_df(d):
    return [dict(time=int(pd.Timestamp(t).tz_localize(None).value // 10**9), open=float(r.open), high=float(r.high), low=float(r.low), close=float(r.close))
            for t, r in d.iterrows()]


def yahoo(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))[["open", "high", "low", "close"]].astype(float)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    ok = (d.high >= d.low) & (d.low <= d.open) & (d.open <= d.high) & (d.low <= d.close) & (d.close <= d.high) & (d.close > 0)
    return d[ok].dropna()


def etf(tk):
    j = json.load(open(os.path.join(RD, "f33", "yahoo", f"{tk}.json")))["chart"]["result"][0]
    t = pd.to_datetime(j["timestamp"], unit="s").normalize()
    c = pd.Series(j["indicators"]["adjclose"][0]["adjclose"], index=t, dtype=float).dropna()
    return [dict(time=int(x.value // 10**9), open=v, high=v, low=v, close=v) for x, v in c.items()]


# F33 signaly z Pythonu (stejna logika jako f33_rebal.py)
src = open(r"D:\Trading bot\scratch\f33_rebal.py", encoding="utf-8").read()
ns = {"__file__": r"D:\Trading bot\scratch\f33_rebal.py"}
exec(compile(src.split('say("F33 Rebalancování')[0], "f33", "exec"), ns)
py33 = [dict(time=int(pd.Timestamp(v[1]).value // 10**9), dir="short" if v[0] == -1 else "long") for v in ns["SIG"].values()]
# F29: nedele s vynosem za 28 dni > 0 (BTC, Yahoo)
b = yahoo("BTCUSD")
py29 = []
for t in b.index[b.index.dayofweek == 6]:
    p = t - pd.Timedelta(days=28)
    if p in b.index and b.close[t] / b.close[p] - 1 > 0:
        py29.append(int(t.value // 10**9))
# F31: hodinove svicky SPX500mini z M1 brokera (cas posunuty na skutecne UTC) za 2026
sys.path.insert(0, r"D:\Trading bot\scratch")
import f2x_lib as LB  # noqa: E402
m = LB.load_m1("SPX500mini", "broker")
m = m[m.u >= pd.Timestamp("2025-10-01", tz="UTC")]
g = m.groupby(m.u.dt.floor("h"))
h1 = [dict(time=int(t.value // 10**9), open=float(o), high=float(hh), low=float(ll), close=float(cc))
      for t, o, hh, ll, cc in zip(g.o.first().index, g.o.first(), g.h.max(), g.l.min(), g.c.last())]
json.dump(dict(spx=cand_df(yahoo("SPX500mini")), spy=etf("SPY"), tlt=etf("TLT"), py33=py33, btc=cand_df(b), py29=py29, h1=h1),
          open(os.path.join(RD, "f2x_parita.json"), "w"))
print("F33 signalu", len(py33), "| F29 nedel long", len(py29), "| F31 hodin", len(h1))
