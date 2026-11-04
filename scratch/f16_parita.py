"""Parita F16: Python kandidati (research_f16_hak, parity=True) -> scratch/f16_parita_<trh>.json pro scripts/compare-f16.ts."""
import json, os, sys
import numpy as np, pandas as pd
os.chdir(r"D:\Trading bot"); sys.path.insert(0, r"D:\Trading bot")
import research_f16_hak as V
MK = sys.argv[1]
A = pd.Timestamp(sys.argv[2], tz="UTC").value // 10**9
B = pd.Timestamp(sys.argv[3], tz="UTC").value // 10**9
P = V.prep(MK); M, T = P["M"], P["T"]
py = [r for r in V.run_market(MK, dict(vlna=4, konf="fvg", entry="potvrz", sl="zona", tp="loc", parity=True)) if A <= r[0] < B]
def cand(Tb, a, b):
    m = (M["t"][Tb["st"]] >= a) & (M["t"][Tb["st"]] < b)
    return [dict(time=int(M["t"][s]), open=float(o), high=float(h), low=float(l), close=float(c))
            for s, o, h, l, c in zip(Tb["st"][m], Tb["o"][m], Tb["h"][m], Tb["l"][m], Tb["c"][m])]
json.dump(dict(mk=MK, A=int(A), B=int(B), c15=cand(T["M15"], A - 40 * 86400, B), c1h=cand(T["H1"], A - 400 * 86400, B), py=py),
          open(os.path.join("scratch", f"f16_parita_{MK}.json"), "w"))
print(MK, "Python signalu", len(py))
