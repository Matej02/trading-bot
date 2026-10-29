"""Vyber 3 experimentalnich systemu (nejlepsi na vyvoji v ramci spoustece, H4) + export pro kontrolu TS/Python."""
import json, sys
sys.path.insert(0, r"D:\Trading bot")
import numpy as np, pandas as pd
import research_f9 as G, research_f9_eval as E
df = pd.read_pickle(r"D:\Trading bot\research_data\f9\f9_udalosti_H4.pkl").sort_values(["mk", "i"]).reset_index(drop=True)
df["per"] = np.where(df.t < G.SPLIT1, "dev", np.where(df.t < G.SPLIT2, "val", "hold"))
bt = {t: g for t, g in df.groupby("trig")}
pick = {}
for trig in ("mss", "prurazPivot", "zona"):
    best = None
    for t2, sub, R in E.combos():
        if t2 != trig: continue
        g = bt[trig]; m = np.ones(len(g), bool)
        for f in sub: m &= g[f].to_numpy()
        gg = E.nonoverlap(g[m], R)
        s = {per: E.st(gg[gg.per == per][f"R{R}"]) for per in ("dev", "val", "hold")}
        if s["dev"]["n"] >= 100 and (best is None or s["dev"]["exp"] > best[3]["dev"]["exp"]):
            best = (trig, sub, R, s)
    pick[trig] = best
    print(E.name(best[0], best[1], best[2]), " | ".join(f"{k} {E.fm(v)}" for k, v in best[3].items()))
json.dump({k: dict(filters=list(v[1]), R=v[2], stats={p: {kk: float(vv) for kk, vv in s.items()} for p, s in v[3].items()}) for k, v in pick.items()},
          open(r"D:\Trading bot\research_data\f9\f9_experiment.json", "w"), indent=1)
# export pro paritu: EURUSD a XAUUSD posledni ~2 roky H1 svicek + casy signalu (UTC cas posledni H1 svicky H4 bloku)
out = {}
for mk in ("EURUSD", "XAUUSD", "BTCUSD"):
    H1 = G.F.load(mk)
    H4, a1, f, ev = G.prepare(mk, "H4")
    key = H1["lt"] // 14400
    st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]]); en = np.r_[st[1:] - 1, len(key) - 1]
    t0 = H1["t"][-1] - 2 * 365 * 86400
    sig = {}
    for trig, (trg, sub, R, s) in pick.items():
        I, Dd, SL = ev[trig]
        ts = []
        for i, d, sl in zip(I.astype(int), Dd.astype(int), SL):
            if not all((bool(f[k][i]) if k == "kz" else int(f[k][i]) == d) for k in sub): continue
            risk = abs(H4["c"][i] - sl)
            if risk < 0.2 * a1[i] or risk > 4 * a1[i]: continue
            tt = int(H1["t"][en[i]])
            if tt >= t0 + 60 * 86400: ts.append([tt, int(d), float(sl)])
        sig[trig] = ts
    m = H1["t"] >= t0
    out[mk] = dict(candles=[dict(time=int(t), open=float(o), high=float(h), low=float(l), close=float(c))
                            for t, o, h, l, c in zip(H1["t"][m], H1["o"][m], H1["h"][m], H1["l"][m], H1["c"][m])], py=sig)
    print(mk, {k: len(v) for k, v in sig.items()})
json.dump(out, open(r"D:\Trading bot\scratch\f9_parita.json", "w"))
