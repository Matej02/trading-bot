"""Parita F13: Python kandidati (research_f13_ves, parity=True) -> scratch/f13_parita_<trh>.json pro scripts/compare-f13.ts."""
import json, os, sys
import numpy as np, pandas as pd
os.chdir(r"D:\Trading bot"); sys.path.insert(0, r"D:\Trading bot")
import research_f10 as X
_load = X.load1
def _v1(mk):
    M = _load(mk); M['v'] = np.ones_like(M['v']); return M
X.load1 = _v1   # zive (Yahoo) objem neni -> podminka objemu v MSS vzdy projde, stejne jako v TS
import research_f13_ves as V
MK = sys.argv[1]
A = pd.Timestamp(sys.argv[2], tz="UTC").value // 10**9
B = pd.Timestamp(sys.argv[3], tz="UTC").value // 10**9
P = V.prep(MK); M, T = P["M"], P["T"]
py = [r for r in V.run_market(MK, dict(tf="M1", lvl="liq", entry="ob50", tp="tp2", parity=True)) if A <= r[0] < B]
def cand(Tb, a, b):
    m = (M["t"][Tb["st"]] >= a) & (M["t"][Tb["st"]] < b)
    return [dict(time=int(M["t"][s]), open=float(o), high=float(h), low=float(l), close=float(c))
            for s, o, h, l, c in zip(Tb["st"][m], Tb["o"][m], Tb["h"][m], Tb["l"][m], Tb["c"][m])]
data = dict(mk=MK, A=int(A), B=int(B), pip=float(M["pip"]), fx=MK in ("EURUSD", "GBPUSD"),
            c1=cand(T["M1"], A - 6 * 86400, B), c15=cand(T["M15"], A - 40 * 86400, B), c1h=cand(T["H1"], A - 400 * 86400, B), py=py)
json.dump(data, open(os.path.join("scratch", f"f13_parita_{MK}.json"), "w"))
print(MK, "Python signalu", len(py))
