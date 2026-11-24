"""Export dat pro kontrolu parity F73/F76/F79 (simulator TS vs test Python), 2026-11-24."""
import json, os, sys
sys.path.insert(0, r"D:\Trading bot\scratch")
import pandas as pd
import f73_f78 as T
import f42_rsi2 as F
def cand(df):
    return [dict(time=int(pd.Timestamp(i).value // 10**9), open=float(r.open), high=float(r.high), low=float(r.low), close=float(r.close)) for i, r in df.iterrows()]
def ser(s):
    return [dict(time=int(pd.Timestamp(i).value // 10**9), open=float(v), high=float(v), low=float(v), close=float(v)) for i, v in s.items()]
spx = F.yahoo("SPX500mini"); spx = spx[spx.index >= "2010-01-01"]
dax = F.yahoo("GER_30mini"); dax = dax[dax.index >= "2015-01-01"]
out = dict(spx=cand(spx), dax=cand(dax), vix=ser(T.VIX[T.VIX.index >= "2010-01-01"]), tlt=ser(T.TLT[T.TLT.index >= "2009-01-01"]))
# ocekavane signaly z testu (den signalu), stejna logika neprekryvani bez vlivu stopu
def nonover(flags, h):
    busy, res = -1, []
    for i, f in enumerate(flags):
        if f and i > busy:
            busy = i + h; res.append(i)
    return res
f76 = T.ext(T.SIG_VIX30, spx)
f73 = T.ext(T.SIG_TLT, spx) & (spx.close / spx.close.shift(5) - 1 < 0).to_numpy()
out["exp76"] = [str(spx.index[i].date()) for i in nonover(f76, 20)]
out["exp73"] = [str(spx.index[i].date()) for i in nonover(f73, 5)]
json.dump(out, open(os.path.join(os.path.dirname(__file__), "kandidati.json"), "w"))
print(len(out["exp76"]), len(out["exp73"]))
