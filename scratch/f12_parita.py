"""Parita F12: Python kandidati signalu (bez busy/2 denne/news, objem = 1 jako z Yahoo) -> scratch/f12_parita.json pro
simulator/scripts/compare-f12.ts. Signal = 1m svicka, ktera po MSS zasahne 0,618 (vstup = close te svicky)."""
import json
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import research_f10 as X

_load = X.load1


def load_v1(mk):
    M = _load(mk)
    M["v"] = np.ones_like(M["v"])
    return M


X.load1 = load_v1
import research_f12 as F

MK = sys.argv[1] if len(sys.argv) > 1 else "EURUSD"
A = pd.Timestamp("2023-03-01", tz="UTC").value // 10**9
B = pd.Timestamp(sys.argv[2] if len(sys.argv) > 2 else "2023-05-01", tz="UTC").value // 10**9
P = F.prep(MK)
M, T, cz, czday, D = P["M"], P["T"], P["cz"], P["czday"], P["D"]
k = 1.5
Xb = T["M1"]
ev = P["S"][k]["M1"]["ev"]
S4 = P["S"][k]["H4"]
t = M["t"]
n = len(t)
out = []
for q in range(1, len(ev["i"])):
    if not ev["flip"][q]:
        continue
    d = int(ev["d"][q])
    if ev["d"][q - 1] != -d:
        continue
    sti, bp = int(ev["sti"][q]), int(ev["brk"][q - 1])
    if not (bp <= sti <= bp + 60):
        continue
    ic = int(Xb["en"][ev["i"][q]])
    if not (A <= t[ic] < B):
        continue
    kz = [w for w in F.KZ if w[0] <= cz[ic] < w[1]]
    if not kz:
        continue
    kD = int(P["dmap"][ic])
    if kD < 2 or P["bm"][kD] != d:
        continue
    k4 = int(P["c4"][ic])
    if k4 < 1 or S4["tr"][k4] != d:
        continue
    b4 = int(S4["bos_i"][k4])
    if b4 < 0 or t[ic] - t[int(T["H4"]["en"][b4])] > 30 * 86400:
        continue
    sv = float(ev["st"][q])
    si = int(Xb["en"][sti])
    if not F.in_poi(P, k, "obe", d, sv, si):
        continue
    ext = M["h"][sti:ic + 1].max() if d == 1 else M["l"][sti:ic + 1].min()
    touch = -1
    for i in range(ic + 1, n):
        if not (kz[0][0] <= cz[i] < kz[0][1]):
            break
        lvl = ext - d * 0.618 * abs(ext - sv)
        if (d == 1 and M["l"][i] <= lvl) or (d == -1 and M["h"][i] >= lvl):
            touch = i
            break
        if (d == 1 and M["l"][i] < sv) or (d == -1 and M["h"][i] > sv):
            break
        ext = max(ext, M["h"][i]) if d == 1 else min(ext, M["l"][i])
    if touch < 0:
        continue
    aD = D["a"][kD - 1]
    px = M["c"][touch]
    mn, mx = (6 * M["pip"], 15 * M["pip"]) if MK in ("EURUSD", "GBPUSD") else (0.086 * aD, 0.21 * aD)
    sl, risk = sv, (px - sv) * d
    if risk <= 0:
        continue
    if risk < mn:
        sl, risk = px - d * mn, mn
    if risk > mx:
        continue
    out.append([int(t[touch]), d, float(sl)])


def cand(Tb, a, b):
    m = (M["t"][Tb["st"]] >= a) & (M["t"][Tb["st"]] < b)
    return [dict(time=int(M["t"][s]), open=float(o), high=float(h), low=float(l), close=float(c))
            for s, o, h, l, c in zip(Tb["st"][m], Tb["o"][m], Tb["h"][m], Tb["l"][m], Tb["c"][m])]


H1 = T["H1"]
data = dict(mk=MK, A=int(A), B=int(B), pip=float(M["pip"]), fx=MK in ("EURUSD", "GBPUSD"),
            c1=cand(T["M1"], A - 6 * 86400, B), c15=cand(T["M15"], A - 40 * 86400, B), c1h=cand(H1, A - 400 * 86400, B), py=out)
json.dump(data, open(os.path.join("scratch", f"f12_parita_{MK}.json"), "w"))
print(MK, "Python signalu", len(out), "| svicek 1m", len(data["c1"]), "15m", len(data["c15"]), "1h", len(data["c1h"]))
