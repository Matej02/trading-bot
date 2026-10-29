import sys, time
sys.path.insert(0, r"D:\Trading bot")
import numpy as np
import research_f9 as G
t0 = time.time()
H, a1, f, ev = G.prepare("EURUSD")
print({k: len(v[0]) for k, v in ev.items()}, round(time.time()-t0,1))
rows = G.simulate_events(H, a1, f, ev)
import pandas as pd
d = pd.DataFrame(rows)
print(len(d), round(time.time()-t0,1))
print(d.groupby("trig")["R2.0"].agg(["count","mean"]).round(3))
print({k: round(d[k].mean(),2) for k in G.FILT})
