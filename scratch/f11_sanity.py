"""Kontrola motoru: prurazF2 (zavreni nad 20dennim max ve smeru tydenniho trendu, SL 2 ATR, TP 2x SL, max 48 dni)
na D1 slozenych z M1 a simulace na M1 stejnou funkci X.sim jako mentori."""
import sys
sys.path.insert(0, r"D:\Trading bot")
import numpy as np, pandas as pd
import research_f10 as X
rows = []
for mk in ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "NAS100mini", "SPX500mini", "GER_30mini"]:
    M = X.load1(mk); D = X.agg(M, M["day"])
    c = pd.Series(D["c"]); wk = (D["day"] + 3) // 7
    wc = c.groupby(wk).last(); e50 = wc.ewm(span=50, adjust=False).mean()
    tr_w = pd.Series(np.where((wc > e50) & (e50 > e50.shift(3)), 1, np.where((wc < e50) & (e50 < e50.shift(3)), -1, 0)), index=wc.index)
    hi20 = pd.Series(D["h"]).rolling(20).max().shift(1).to_numpy(); lo20 = pd.Series(D["l"]).rolling(20).min().shift(1).to_numpy()
    busy = -1
    for k in range(300, len(D["c"]) - 1):
        w = wk[k] - 1  # posledni UZAVRENY tyden
        if w not in tr_w.index: continue
        t = tr_w[w]; d = 0
        if D["c"][k] > hi20[k] and t == 1: d = 1
        if D["c"][k] < lo20[k] and t == -1: d = -1
        if not d or D["en"][k] <= busy: continue
        i0 = D["en"][k] + 1; E = M["o"][i0]; a = D["a"][k]; SL = E - d * 2 * a; TP = E + d * 4 * a
        s = X.sim(M, d, E, SL, TP, i0, i0, 1, i0 + 48 * 1440)
        if s: rows.append(dict(mk=mk, t=M["t"][i0], R=s["R"])); busy = s["ex"]
df = pd.DataFrame(rows); df["oos"] = df.t >= X.OOS
print(df.groupby("oos").R.agg(["count", "mean"]).round(3)); print(df.groupby("mk").R.agg(["count", "mean"]).round(3))
