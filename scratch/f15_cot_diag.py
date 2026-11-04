"""Diagnostika: predpovida COT extrem (commercials >= 80 / <= 20, retail opacne) vynos za 4 a 13 tydnu? Tydenni closy z H1."""
import os, sys, numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"D:\Trading bot"); sys.path.insert(0, r"D:\Trading bot")
import research_f8 as F, research_f15_cot as C
OOS = pd.Timestamp("2022-01-01").value // 10**9
rows = []
for mk in C.CODES:
    H = F.load(mk); W = F.resample(H, (H["day"] + 3) // 7)
    tw = H["t"][W["en"]]; cw = W["c"]
    S = C.series(mk)
    for i in range(len(cw) - 14):
        k = C.at(S, H["t"][W["st"][i]])          # report dostupny na zacatku tydne i
        if k < 0 or np.isnan(S.comm[k]): continue
        r4 = np.log(cw[i + 3] / W["o"][i]); r13 = np.log(cw[i + 12] / W["o"][i])
        rows.append(dict(mk=mk, t=int(tw[i]), comm=S.comm[k], nc=S.nc[k], nr=S.nr[k], r4=r4, r13=r13))
df = pd.DataFrame(rows); df["oos"] = df.t >= OOS
# normalizace vynosu volatilitou trhu (std tydennich 4t vynosu)
for c in ("r4", "r13"):
    df[c + "z"] = df.groupby("mk")[c].transform(lambda x: x / x.std())
def rep(mask, nm):
    for per, g in (("vývoj", df[mask & ~df.oos]), ("OOS", df[mask & df.oos])):
        print(f"  {nm:34s} {per:5s} n {len(g):5d}  4t {g.r4z.mean():+.3f} σ  13t {g.r13z.mean():+.3f} σ")
print("směr = 100 býčí pro pár; výnos v σ (kladné = cena šla ve směru signálu)")
rep(df.comm >= 0, "všechny týdny (drift, long)")
for nm, col, hi in (("commercials", "comm", True), ("non-comm (fondy)", "nc", True), ("retail", "nr", False)):
    lo_m = df[col] <= 20; hi_m = df[col] >= 80
    sig = np.where(hi_m, 1, np.where(lo_m, -1, 0)) * (1 if hi else -1)
    df["s"] = sig
    for per in (False, True):
        g = df[(df.s != 0) & (df.oos == per)]
        print(f"  {nm:16s} extrém {'OOS ' if per else 'vývoj'} n {len(g):5d}  4t {(g.s*g.r4z).mean():+.3f} σ  13t {(g.s*g.r13z).mean():+.3f} σ  (long {int((g.s>0).sum())}, short {int((g.s<0).sum())})")
