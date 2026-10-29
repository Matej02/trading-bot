import sys
sys.path.insert(0, r"D:\Trading bot")
import numpy as np, pandas as pd
import research_f9 as G, research_f9_eval as E
df = pd.read_pickle(r"D:\Trading bot\research_data\f9\f9_udalosti" + (sys.argv[1] if len(sys.argv) > 1 else "") + ".pkl").sort_values(["mk", "i"]).reset_index(drop=True)
df["per"] = np.where(df.t < G.SPLIT1, "dev", np.where(df.t < G.SPLIT2, "val", "hold"))
bt = {t: g for t, g in df.groupby("trig")}
res = []
for trig, sub, R in E.combos():
    g = bt[trig]; m = np.ones(len(g), bool)
    for f in sub: m &= g[f].to_numpy()
    gg = E.nonoverlap(g[m], R)
    s = {per: E.st(gg[gg.per == per][f"R{R}"]) for per in ("dev", "val", "hold")}
    if s["dev"]["n"] >= 100: res.append((trig, sub, R, s))
res.sort(key=lambda x: -x[3]["dev"]["exp"])
print("TOP 15 podle vyvoje (n>=100):")
for trig, sub, R, s in res[:8]:
    print(f"  {E.name(trig, sub, R):55s} " + " | ".join(f"{k} {E.fm(v)}" for k, v in s.items()))
pos = [x for x in res if x[3]["dev"]["exp"] > 0]
print("kladnych na vyvoji:", len(pos), "z", len(res), "| z nich kladnych i ve validaci:", sum(x[3]["val"]["exp"] > 0 for x in pos))
# bez nakladu: hrube - pricteni spreadu zpet neni v datech; hruby odhad: median nakladu ~ spread/risk
