"""Parita F14: Python kandidati (research_f14_pat, parity=True) -> scratch/f14_parita_<trh>.json pro scripts/compare-f14.ts."""
import json, os, sys
import numpy as np, pandas as pd
os.chdir(r"D:\Trading bot"); sys.path.insert(0, r"D:\Trading bot")
import research_f14_pat as V
MK = sys.argv[1]
A = pd.Timestamp(sys.argv[2], tz="UTC").value // 10**9
B = pd.Timestamp(sys.argv[3], tz="UTC").value // 10**9
P = V.prep(MK); M, T = P["M"], P["T"]
py = [r for r in V.run_market(MK, dict(model="A", tf="M15", sess="full", tp="zona", parity=True)) if A <= r[0] < B]
def cand(Tb, a, b):
    m = (M["t"][Tb["st"]] >= a) & (M["t"][Tb["st"]] < b)
    return [dict(time=int(M["t"][s]), open=float(o), high=float(h), low=float(l), close=float(c))
            for s, o, h, l, c in zip(Tb["st"][m], Tb["o"][m], Tb["h"][m], Tb["l"][m], Tb["c"][m])]
json.dump(dict(mk=MK, A=int(A), B=int(B), tick=float(M["tick"]), c15=cand(T["M15"], A - 40 * 86400, B),
               c1h=cand(T["H1"], A - 400 * 86400, B), py=py), open(os.path.join("scratch", f"f14_parita_{MK}.json"), "w"))
print(MK, "Python signalu", len(py))
