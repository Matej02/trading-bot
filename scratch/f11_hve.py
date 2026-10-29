import sys
sys.path.insert(0, r"D:\Trading bot")
import numpy as np, pandas as pd
import research_f8 as F, f7_lib as L
d = pd.read_pickle(r"D:\Trading bot\research_data\f10\f10_HVE.pkl")
OOS = pd.Timestamp("2022-01-01", tz="UTC").value // 10**9
d["oos"] = d.t >= OOS
d["grp"] = np.where(d.mk.isin(["XAUUSD", "XAGUSD"]), "kovy", np.where(d.mk.str.contains("mini"), "indexy", np.where(d.mk.str.contains("OIL"), "ropa", "forex")))
print(d.groupby(["grp", "d", "oos"]).R.agg(["count", "mean"]).round(3).unstack())
print()
for var, g in d[(d.d == 1) & d.grp.isin(["kovy", "indexy"])].groupby("var"):
    print(f"{var:32s}", g.groupby("oos").R.agg(["count", "mean"]).round(3).values.tolist())
# nahodne LONG vstupy na stejnych trzich a rocich, stejny SL v ATR D1, stejne R, max 30 dni, BE pri 1R
rng = np.random.default_rng(3)
sel = d[(d.d == 1) & d.grp.isin(["kovy", "indexy"]) & (d["var"] == "trend=False sl20=False R=2")]
res = []
for mk, g in sel.groupby("mk"):
    H = F.load(mk); Dd = F.resample(H, H["day"])
    yr = pd.to_datetime(H["t"][Dd["st"]], unit="s").year.to_numpy()
    for x in g.itertuples():
        y = pd.Timestamp(x.t, unit="s").year
        ks = np.flatnonzero((yr == y))[1:]
        for _ in range(10):
            k = int(rng.choice(ks)); i0 = Dd["st"][k]
            if i0 >= len(H["c"]) - 2: continue
            a = Dd["a"][k - 1]; E0 = H["o"][i0] + H["spr"][i0]; risk = x.risk_atrD * a
            if not risk > 0: continue
            SL = E0 - risk; TP = E0 + 2 * risk
            r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], i0, i0, 1, 1, E0, SL, E0 + risk, 1e-9, TP, 1 - 1e-9,
                            np.full(1, np.nan), 0, min(i0 + 30 * 24, len(H["c"]) - 1), np.nan, H["hend"], 0, 0.0, H["cum_sw"], H["swl"])
            if r[0]: res.append((x.oos, r[1]))
rb = pd.DataFrame(res, columns=["oos", "R"])
print("\nnahodne LONG (stejne trhy/roky/SL/R/BE):", rb.groupby("oos").R.agg(["count", "mean"]).round(3).values.tolist())
print("strategie (trend=False sl20=False R=2) LONG:", sel.groupby("oos").R.agg(["count", "mean"]).round(3).values.tolist())
