"""F11 - Srajer day trading v2: jako F10 (M15 zona v aktivni 4H zone, sweep M15 pivotu pred dotekem, discount/premium 4H swingu)
+ varianty vstupu: limit na proximal / potvrzeni (M5 svicka po doteku zavre zpet za proximal, vstup trhem); okna jeho / cely den 02-11 NY;
TP 2,5R / 3R. SL za distal M15 zony. Konec dne."""
import os, sys
import numpy as np, pandas as pd
os.chdir(r"D:\Trading bot"); sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L, research_f8 as F, research_f10 as X
D11 = os.path.join("research_data", "f11")
MARKETS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "XAUUSD"]
def run_market(M, T, var):
    Q, H4, D, Xb = T["M15"], T["H4"], T["D1"], T["M5"]
    n = len(M["c"])
    Zq = F.find_zones(Q, 1.5); Z4 = F.find_zones(H4, 2.0)
    sh4, sl4, _ = F.last_swing(H4["h"], H4["l"], 3)
    phq, plq = L.pivots(Q["h"], Q["l"], 3)
    dst, den = X.day_end_idx(M); dmap = np.searchsorted(dst, np.arange(n), side="right") - 1
    out = []
    for z in Zq:
        d = z["d"]; ia = Q["en"][z["act"]]; lo, hi = sorted((z["prox"], z["dist"]))
        par = None
        for w in Z4:
            if w["d"] != d: continue
            wa, wi = H4["en"][w["act"]], H4["en"][min(w["inv"], len(H4["en"]) - 1)]
            wlo, whi = sorted((w["prox"], w["dist"]))
            if wa <= ia < wi and lo <= whi and hi >= wlo: par = w; break
        if par is None: continue
        k4 = int(np.searchsorted(H4["st"], ia, side="right")) - 1
        rh, rl = sh4[k4], sl4[k4]
        if not (np.isfinite(rh) and np.isfinite(rl)) or rh <= rl: continue
        mid = 0.5 * (rh + rl)
        if (d == 1 and z["prox"] > mid) or (d == -1 and z["prox"] < mid): continue
        i_last = min(Q["en"][min(z["inv"], len(Q["en"]) - 1)], ia + 5 * 1440, n - 2)
        fi = X.m1_first(M, ia + 1, i_last, cond_low=z["prox"] if d == 1 else None, cond_high=z["prox"] if d == -1 else None)
        if fi < 0: continue
        hm = M["hm"][fi]
        if var["okna"] == "jeho":
            if not any(a <= hm < b for a, b in X.WIN_SR): continue
        elif not (9 <= hm < 18): continue
        qa, qf = z["act"], int(np.searchsorted(Q["st"], fi, side="right")) - 1
        swept = False
        for p in range(qa + 1, qf - 2):
            if d == 1 and plq[p] and Q["l"][p] > z["prox"] and M["l"][Q["en"][p + 3]:fi + 1].min() < Q["l"][p]: swept = True; break
            if d == -1 and phq[p] and Q["h"][p] < z["prox"] and M["h"][Q["en"][p + 3]:fi + 1].max() > Q["h"][p]: swept = True; break
        if not swept: continue
        SL = z["dist"] - d * 0.05 * Q["a"][z["act"]]
        atrD = D["a"][max(0, int(np.searchsorted(D["st"], fi, side="right")) - 2)]
        iex = den[dmap[fi]]
        if var["entry"] == "limit":
            E = z["prox"]; risk = (E - SL) * d
            s = X.sim(M, d, E, SL, E + d * var["R"] * risk, fi, fi, 0, iex)
        else:
            x0 = int(np.searchsorted(Xb["st"], fi, side="right")) - 1; xc = -1
            for q in range(x0, min(x0 + 12, len(Xb["c"]) - 1)):
                if (d == 1 and Xb["l"][q] <= SL) or (d == -1 and Xb["h"][q] >= SL): break
                if (Xb["c"][q] - z["prox"]) * d > 0: xc = q; break
            if xc < 0: continue
            i0 = Xb["en"][xc] + 1; E0 = M["o"][i0]; risk = (E0 - SL) * d
            if risk <= 0: continue
            s = X.sim(M, d, E0, SL, E0 + d * var["R"] * risk, i0, i0, 1, iex)
        if s: out.append(X.rec(M, "SRA", X.vn(var), d, s, var["R"], atrD, "den"))
    return out
if __name__ == "__main__":
    rows = []
    for mk in MARKETS:
        M = X.load1(mk); T = X.tfs(M)
        for entry in ("limit", "potvrz"):
            for okna in ("jeho", "den"):
                for R in (2.5, 3.0):
                    rows += run_market(M, T, dict(entry=entry, okna=okna, R=R))
        print(mk, len(rows), flush=True)
    pd.DataFrame(rows).to_pickle(os.path.join(D11, "f11_SRA.pkl"))
