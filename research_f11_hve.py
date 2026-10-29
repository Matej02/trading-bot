"""F11 - Hvezda v2 (plny trading plan): trend D1 (2 vyssi high + 2 vyssi low pivotu N=3) -> D1 zona (FM) volitelne uvnitr
aktivni W1 zony -> lokace: Fibo od low nejblizsi demand k high nejblizsi supply, long jen v dolni tretine (short horni)
-> vstup buy limit na proximal / potvrzovaci D1 svicka (hammer/engulfing) do 3 dnu -> SL pod zonou (+20 % varianta)
-> TP nejblizsi protejsi zona (min 2R, max 6R) / 2R -> BE pri 1R. H1 data MT5 2009-2026, 26 trhu."""
import os, sys
import numpy as np, pandas as pd
os.chdir(r"D:\Trading bot"); sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L, research_f8 as F
D11 = os.path.join("research_data", "f11")
OOS = pd.Timestamp("2022-01-01", tz="UTC").value // 10**9
def sim(H, d, E, SL, TP, i0, kind):
    sw = H["swl"] if d == 1 else H["sws"]
    tp1 = E + d * abs(E - SL)
    return L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], i0, i0, kind, d, E, SL, tp1, 1e-9, TP, 1 - 1e-9,
                       np.full(1, np.nan), 0, min(i0 + 30 * 24, len(H["c"]) - 1), np.nan, H["hend"], 0, 0.0, H["cum_sw"], sw)
def run(mk, H, T, var):
    Dd, W = T["D1"], T["W1"]
    o, h, l, c = Dd["o"], Dd["h"], Dd["l"], Dd["c"]
    ZD = F.find_zones(Dd, 1.5); ZW = F.find_zones(W, 1.5)
    out = []
    for z in ZD:
        d = z["d"]
        if z["tr"] != d: continue
        ia = Dd["en"][z["act"]]
        lo, hi = sorted((z["prox"], z["dist"]))
        if var["dvw"]:
            ok = False
            for w in ZW:
                if w["d"] != d: continue
                wa, wi = W["en"][w["act"]], W["en"][min(w["inv"], len(W["en"]) - 1)]
                wlo, whi = sorted((w["prox"], w["dist"]))
                if wa <= ia < wi and lo <= whi and hi >= wlo: ok = True; break
            if not ok: continue
        opp = [y for y in ZD if y["d"] == -d and y["act"] <= z["act"] < y["inv"] and (y["prox"] - z["prox"]) * d > 0]
        if var["tp"] == "zona" or var["lok"]:
            if not opp: continue
            yb = min(opp, key=lambda y: abs(y["prox"] - z["prox"]))
        if var["lok"]:
            a_, b_ = (z["dist"], yb["dist"]) if d == 1 else (yb["dist"], z["dist"])  # low demand .. high supply
            third = a_ + (b_ - a_) / 3 if d == 1 else b_ - (b_ - a_) / 3
            if (d == 1 and z["prox"] > third) or (d == -1 and z["prox"] < third): continue
        t0 = -1
        for k in range(z["act"] + 1, min(z["inv"], z["act"] + 120, len(c))):
            if (d == 1 and l[k] <= z["prox"]) or (d == -1 and h[k] >= z["prox"]): t0 = k; break
        if t0 < 0: continue
        hgt = abs(z["prox"] - z["dist"])
        SL = z["dist"] - d * (0.2 * hgt if var["sl20"] else 0.05 * z["atr"])
        if var["entry"] == "limit":
            E, i0, kind = z["prox"], Dd["st"][t0], 0
            # limit vyplnen v den t0 (dotek) - presny okamzik najde sim_trade na H1
        else:
            ck = -1
            for k in range(t0, min(t0 + 3, len(c) - 1)):
                if (c[k] - z["dist"]) * d < 0: break
                body = abs(c[k] - o[k]); lw = min(o[k], c[k]) - l[k]; uw = h[k] - max(o[k], c[k])
                if d == 1:
                    ok = (body > 0 and lw >= 2 * body and uw <= body) or (c[k] > o[k] and o[k-1] > c[k-1] and c[k] >= o[k-1] and o[k] <= c[k-1])
                else:
                    ok = (body > 0 and uw >= 2 * body and lw <= body) or (c[k] < o[k] and o[k-1] < c[k-1] and c[k] <= o[k-1] and o[k] >= c[k-1])
                if ok: ck = k; break
            if ck < 0: continue
            i0, kind = Dd["en"][ck] + 1, 1
            if i0 >= len(H["c"]) - 1: continue
            E = H["o"][i0] + (H["spr"][i0] if d == 1 else 0)
        risk = (E - SL) * d
        if risk <= 0: continue
        if var["tp"] == "zona":
            Rt = (yb["dist" if False else "prox"] - E) * d / risk
            if Rt < 2: continue
            Rt = min(Rt, 6.0)
        else:
            Rt = 2.0
        if kind == 0:
            r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], i0, Dd["en"][t0], 0, d, E, SL, E + d * risk, 1e-9,
                            E + d * Rt * risk, 1 - 1e-9, np.full(1, np.nan), 0, min(i0 + 30 * 24, len(H["c"]) - 1), np.nan, H["hend"],
                            0, 0.0, H["cum_sw"], H["swl"] if d == 1 else H["sws"])
        else:
            r = sim(H, d, E, SL, E + d * Rt * risk, i0, 1)
        if r[0]:
            out.append(dict(mk=mk, var=" ".join(f"{a}={b}" for a, b in var.items()), d=d, t=int(H["t"][r[2]]), R=r[1], Rt=Rt))
    return out
if __name__ == "__main__":
    rows = []
    vars_ = [dict(dvw=a, lok=b, entry=e, tp=t, sl20=s) for a in (True, False) for b in (True, False) for e in ("limit", "svicka") for t in ("zona", "2R") for s in (False, True)]
    for mk in F.MARKETS:
        H = F.load(mk); T = F.tfs(H)
        for v in vars_: rows += run(mk, H, T, v)
        print(mk, len(rows), flush=True)
    df = pd.DataFrame(rows); df["oos"] = df.t >= OOS
    df.to_pickle(os.path.join(D11, "f11_HVE.pkl"))
    res = []
    for var, g in df.groupby("var"):
        dv, ov = g[~g.oos].R, g[g.oos].R
        res.append((var, len(dv), dv.mean(), len(ov), ov.mean()))
    res.sort(key=lambda x: -x[2] if x[1] >= 50 else 9)
    for r in res: print(f"{r[0]:52s} DEV n={r[1]:4d} {r[2]:+.3f}R | OOS n={r[3]:4d} {r[4]:+.3f}R")
