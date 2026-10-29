import pandas as pd, numpy as np
OOS = pd.Timestamp("2022-01-01", tz="UTC").value // 10**9
fs = {"KIM": "f10/f10_KIM", "PAT": "f10/f10_PAT", "MUC": "f10/f10_MUC", "VES": "f11/f11_VES", "HAK": "f11/f11_HAK", "SRA": "f10/f10_SRA", "VAL": "f10/f10_VAL", "HVE": "f10/f10_HVE"}
up = ["XAUUSD", "NAS100mini", "SPX500mini", "US30mini", "GER_30mini"]
for k, f in fs.items():
    d = pd.read_pickle(f"D:/Trading bot/research_data/{f}.pkl"); d = d[np.isfinite(d.R)]
    g = d[d.mk.isin(up)]
    if g.empty: continue
    t = g.groupby(["d", g.t >= OOS]).R.agg(["count", "mean"]).round(3).unstack()
    print(k, "| long DEV/OOS:", t.loc[1].tolist() if 1 in t.index else None, "| short:", t.loc[-1].tolist() if -1 in t.index else None)
