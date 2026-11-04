"""Parita F15: Python kandidati (research_f15_hve, parity=True) -> scratch/f15_parita_<trh>.json pro scripts/compare-f15.ts."""
import json, os, sys
import numpy as np, pandas as pd
os.chdir(r"D:\Trading bot"); sys.path.insert(0, r"D:\Trading bot")
import research_f15_hve as V
MK = sys.argv[1]
A = pd.Timestamp(sys.argv[2], tz="UTC").value // 10**9
B = pd.Timestamp(sys.argv[3], tz="UTC").value // 10**9
H = V.prep(MK)[0]
py = [r for r in V.run_market(MK, dict(tf="den", base=3, dvw=1, lnl=1, entry="limit", cot="0", parity=True)) if A <= r[0] < B]
m = (H["t"] >= A - 420 * 86400) & (H["t"] < B)
c1h = [dict(time=int(t), open=float(o), high=float(h), low=float(l), close=float(c)) for t, o, h, l, c in
       zip(H["t"][m], H["o"][m], H["h"][m], H["l"][m], H["c"][m])]
json.dump(dict(mk=MK, A=int(A), B=int(B), c1h=c1h, py=py), open(os.path.join("scratch", f"f15_parita_{MK}.json"), "w"))
print(MK, "Python signalu", len(py))
