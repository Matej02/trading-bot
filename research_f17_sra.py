"""
F17 - Srajer: PDF + obrazky jako zdroj, B6 jako dodatek (F17_PLAN.md).
A) day trading (M1 data): 4H zona ve smeru 4H trendu v discountu/premiu 4H swingu -> v ni 15m zona -> pred dotekem vybrana likvidita
   (equal lows/highs nebo pivot) -> vstup limit na proximal / lokalni zmena trendu na 5m -> SL za distal (ci sweep) -> TP 2,7 R / protejsi
   15m zona; okna 8:30-9:30, 10:30-11:30, 13:30-16:00 Praha; konec dne 22:00.
B) swing (H1 data): D1 zona v top discountu/premiu mezi nejblizsi unmitigated D1 supply a demand -> limit na proximal (D1 nebo 4H uvnitr)
   -> SL za distal, TP 2R / 0,5 rovnovaha; filtr skore Trading Analyzer (bias / zmena za 5 dni). Max 20 dni.
Spusteni: py research_f17_sra.py dt|swing [trh ...] -> research_data/f17/ (F10_NOCOST=1 -> _nc)
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f8 as F
import research_f10 as X
import research_f12 as F12

D17 = os.path.join("research_data", "f17")
os.makedirs(D17, exist_ok=True)
DT_MARKETS = ["EURUSD", "XAUUSD", "GBPUSD", "AUDUSD", "USDJPY", "USDCAD"]
SW_MARKETS = [m for m in (f[:-4].replace("_", "") for f in sorted(os.listdir(os.path.join("research_data", "fm_score")))) if m in L.BROKER]
KZ = ((8.5, 9.5), (10.5, 11.5), (13.5, 16.0))
NOCOST = os.environ.get("F10_NOCOST") == "1"


# ---------------------------------------------------------------- A) day trading
_CA = {}


def prep_dt(mk):
    if mk in _CA:
        return _CA[mk]
    M = X.load1(mk)
    T = X.tfs(M)
    cz, czday = F12.prague_hours(M["t"])
    Q, H4 = T["M15"], T["H4"]
    sh4, sl4, tr4 = F.last_swing(H4["h"], H4["l"], 3)
    phq, plq = L.pivots(Q["h"], Q["l"], 3)
    ph5, pl5 = L.pivots(T["M5"]["h"], T["M5"]["l"], 2)
    P = dict(M=M, T=T, cz=cz, czday=czday, Zq=F.find_zones(Q, 1.5), Z4=F.find_zones(H4, 1.5), sh4=sh4, sl4=sl4, tr4=tr4,
             phq=np.flatnonzero(phq), plq=np.flatnonzero(plq), ph5=np.flatnonzero(ph5), pl5=np.flatnonzero(pl5))
    _CA.clear()
    _CA[mk] = P
    return P


def run_dt(mk, var):
    P = prep_dt(mk)
    M, T, cz, czday = P["M"], P["T"], P["cz"], P["czday"]
    Q, H4, X5 = T["M15"], T["H4"], T["M5"]
    n = len(M["c"])
    out = []
    busy = -1
    for z in P["Zq"]:
        d = z["d"]
        ia = int(Q["en"][z["act"]])
        lo, hi = sorted((z["prox"], z["dist"]))
        par = None
        for w in P["Z4"]:
            if w["d"] != d:
                continue
            wa, wi = H4["en"][w["act"]], H4["en"][min(w["inv"], len(H4["en"]) - 1)]
            wlo, whi = sorted((w["prox"], w["dist"]))
            if wa <= ia < wi and lo <= whi and hi >= wlo:
                par = w
                break
        if par is None:
            continue
        k4 = int(np.searchsorted(H4["st"], ia, side="right")) - 1
        if var.get("tr", 1) and P["tr4"][k4] != d:
            continue
        rh, rl = P["sh4"][k4], P["sl4"][k4]
        if not (np.isfinite(rh) and np.isfinite(rl)) or rh <= rl:
            continue
        mid = 0.5 * (rh + rl)
        if (d == 1 and z["prox"] > mid) or (d == -1 and z["prox"] < mid):
            continue
        hz = hi - lo
        i_last = min(int(Q["en"][min(z["inv"], len(Q["en"]) - 1)]), ia + 5 * 1440, n - 2)
        fi = X.m1_first(M, ia + 1, i_last, cond_low=z["prox"] if d == 1 else None, cond_high=z["prox"] if d == -1 else None)
        if fi < 0 or fi <= busy:
            continue
        # mitigace <= 25 %: pred timto dotekem se zona nedotkla (fi je prvni dotek proximal) - ok
        if not any(a <= cz[fi] < b for a, b in KZ):
            continue
        # likvidita vybrana v poslednich 8 h pred dotekem / v zone: equal lows nebo pivot low nad distal
        qf = int(np.searchsorted(Q["st"], fi, side="right")) - 1
        a15 = Q["a"][qf]
        piv = P["plq"] if d == 1 else P["phq"]
        piv = piv[(piv >= z["act"]) & (piv <= qf - 3) & (piv >= qf - 96)]
        pr = Q["l"][piv] if d == 1 else Q["h"][piv]
        sweep_ext = M["l"][fi:min(fi + 120, n)].min() if d == 1 else M["h"][fi:min(fi + 120, n)].max()
        took = False
        if var["lq"] == "eq":
            for a_ in range(len(pr)):
                for b_ in range(a_ + 1, len(pr)):
                    if abs(pr[a_] - pr[b_]) <= 0.1 * a15:
                        lvl = min(pr[a_], pr[b_]) if d == 1 else max(pr[a_], pr[b_])
                        seg = M["l"][int(Q["en"][piv[b_] + 3]):fi + 120] if d == 1 else M["h"][int(Q["en"][piv[b_] + 3]):fi + 120]
                        if len(seg) and ((d == 1 and seg.min() < lvl) or (d == -1 and seg.max() > lvl)):
                            took = True
                            break
                if took:
                    break
        else:
            for p_, v_ in zip(piv, pr):
                seg = M["l"][int(Q["en"][p_ + 3]):fi + 120] if d == 1 else M["h"][int(Q["en"][p_ + 3]):fi + 120]
                if len(seg) and ((d == 1 and seg.min() < v_) or (d == -1 and seg.max() > v_)):
                    took = True
                    break
        if not took:
            continue
        day = czday[fi]
        iex = fi
        while iex + 1 < n and czday[iex + 1] == day and cz[iex + 1] < 22.0:
            iex += 1
        SL0 = z["dist"] - d * 0.05 * a15
        if var["entry"] == "limit":
            E, i0, iv, kind = z["prox"], fi, fi, 0
            SL = SL0
        else:
            # lokalni zmena trendu na 5m: po doteku close za poslednim 5m pivotem proti pullbacku (do 3 h, SL nezasazen)
            x0 = int(np.searchsorted(X5["st"], fi, side="right")) - 1
            pv = P["ph5"] if d == 1 else P["pl5"]
            xc = -1
            for q in range(x0, min(x0 + 36, len(X5["c"]) - 1)):
                if (d == 1 and X5["l"][q] <= SL0) or (d == -1 and X5["h"][q] >= SL0):
                    break
                k = int(np.searchsorted(pv, q - 2)) - 1
                if k < 0:
                    continue
                lvl = X5["h"][pv[k]] if d == 1 else X5["l"][pv[k]]
                if pv[k] >= x0 - 12 and (X5["c"][q] - lvl) * d > 0 and (X5["c"][q - 1] - lvl) * d <= 0:
                    xc = q
                    break
            if xc < 0:
                continue
            i0 = int(X5["en"][xc]) + 1
            if i0 >= iex:
                continue
            ext = M["l"][fi:i0].min() if d == 1 else M["h"][fi:i0].max()
            SL = min(SL0, ext - 0.05 * a15) if d == 1 else max(SL0, ext + 0.05 * a15)
            E, iv, kind = M["o"][i0] + (M["spr"][i0] if d == 1 else 0), i0, 1
        risk = (E - SL) * d
        if risk <= 0 or risk < 3 * M["spr"][fi]:
            continue
        if var["tp"] == "2.7R":
            Rt = 2.7
        else:
            opp = [y for y in P["Zq"] if y["d"] == -d and Q["en"][y["act"]] <= fi < Q["en"][min(y["inv"], len(Q["en"]) - 1)]
                   and (y["prox"] - E) * d > 0]
            if not opp:
                continue
            yb = min(opp, key=lambda y: abs(y["prox"] - E))
            Rt = (yb["prox"] - E) * d / risk
            if Rt < 2.0:
                continue
            Rt = min(Rt, 3.5)
        s = X.sim(M, d, E, SL, E + d * Rt * risk, i0, iv, kind, iex)
        if not s:
            continue
        atrD = T["D1"]["a"][max(0, int(np.searchsorted(T["D1"]["st"], fi, side="right")) - 2)]
        r = X.rec(M, "F17dt", X.vn(var), d, s, Rt, atrD, "den")
        r.update(sl_dist=risk, tp_dist=Rt * risk, cz=float(cz[s["fi"]]))
        out.append(r)
        busy = s["ex"]
    return out


DT_GRID = [dict(tr=r, lq=q, entry=e, tp=t) for r in (1, 0) for q in ("eq", "piv") for e in ("limit", "shift") for t in ("2.7R", "zona")]


# ---------------------------------------------------------------- B) swing
_CB = {}


def score_series(mk):
    p = os.path.join("research_data", "fm_score", f"{mk[:3]}_{mk[3:]}.csv")
    s = pd.read_csv(p)
    s["t"] = pd.to_datetime(s.timestamp).astype("datetime64[s]").astype("int64") + 86400   # pouzitelne od dalsiho dne
    return s.sort_values("t").reset_index(drop=True)


def prep_sw(mk):
    if mk in _CB:
        return _CB[mk]
    H = F.load(mk)
    if NOCOST:
        H["spr"] = np.zeros_like(H["spr"])
        H["swl"] = H["sws"] = 0.0
    T = F.tfs(H)
    P = dict(H=H, T=T, ZD=F.find_zones(T["D1"], 1.5), Z4=F.find_zones(T["H4"], 1.5), S=score_series(mk))
    _CB.clear()
    _CB[mk] = P
    return P


def run_sw(mk, var):
    P = prep_sw(mk)
    H, T, ZD, Z4, S = P["H"], P["T"], P["ZD"], P["Z4"], P["S"]
    Dd, H4 = T["D1"], T["H4"]
    n = len(H["c"])
    st_t, st_v = S.t.to_numpy(), S.score.to_numpy(float)
    zt = lambda TT, z: (TT["en"][z["act"]], TT["en"][min(z["inv"], len(TT["en"]) - 1)])
    out = []
    busy = -1
    for z in ZD:
        d = z["d"]
        a0, inv = zt(Dd, z)
        # prvni dotek proximal po aktivaci (H1), do 60 dni a pred zneplatnenim
        lim = min(inv, a0 + 60 * 24, n - 2)
        seg = H["l"][a0 + 1:lim + 1] if d == 1 else H["h"][a0 + 1:lim + 1]
        k = np.flatnonzero(seg <= z["prox"]) if d == 1 else np.flatnonzero(seg >= z["prox"])
        if not len(k):
            continue
        it = a0 + 1 + int(k[0])
        if it <= busy:
            continue
        # protejsi nejblizsi unmitigated D1 zona aktivni pri doteku -> lokace (top discount = pod 0,333)
        opp = [y for y in ZD if y["d"] == -d and zt(Dd, y)[0] <= it < zt(Dd, y)[1] and (y["prox"] - z["prox"]) * d > 0]
        if not opp:
            continue
        yb = min(opp, key=lambda y: abs(y["prox"] - z["prox"]))
        a_, b_ = (z["prox"], yb["prox"])                       # vrch demand .. spodek supply (pro long)
        third = a_ + (b_ - a_) / 3                            # 0,333
        half = a_ + (b_ - a_) / 2
        # entry: proximal D1 zony je uz v top discountu (pod 0,333) z definice; volitelne 4H zona uvnitr D1 zony
        E = z["prox"]
        if var["ltf"] == "4h":
            lo, hi = sorted((z["prox"], z["dist"]))
            cand = [w for w in Z4 if w["d"] == d and zt(H4, w)[0] <= it and zt(H4, w)[1] > it and lo <= max(w["prox"], w["dist"])
                    and hi >= min(w["prox"], w["dist"])]
            if not cand:
                continue
            w = max(cand, key=lambda w: w["act"])
            E = w["prox"] if (w["prox"] - z["prox"]) * d <= 0 else z["prox"]
        SL = z["dist"] - d * 0.05 * z["atr"]
        risk = (E - SL) * d
        if risk <= 0:
            continue
        if var["tp"] == "2R":
            Rt = 2.0
        else:
            Rt = (half - E) * d / risk
            if Rt < 2.0:
                continue
            Rt = min(Rt, 6.0)
        # skore k casu doteku
        j = int(np.searchsorted(st_t, H["t"][it], side="right")) - 1
        if var["score"] != "0":
            if j < 5 or H["t"][it] - st_t[j] > 5 * 86400:
                continue
            sc, dsc = st_v[j], st_v[j] - st_v[j - 5]
            if var["score"] == "bias" and not ((d == 1 and sc >= 5) or (d == -1 and sc <= -5)):
                continue
            if var["score"] == "zmena" and not ((d == 1 and dsc >= 2) or (d == -1 and dsc <= -2)):
                continue
        # limit E vyplnen od doteku proximal (it) do konce 20 dni
        sw = H["swl"] if d == 1 else H["sws"]
        TP = E + d * Rt * risk
        r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], it, min(it + 5 * 24, n - 2), 0, d, E, SL, TP, 1.0,
                        np.nan, np.nan, np.full(1, np.nan), 0, min(it + 20 * 24, n - 1), np.nan, H["hend"], 0, 0.0, H["cum_sw"], sw)
        if not r[0]:
            continue
        out.append(dict(mk=mk, var=" ".join(f"{a}={b}" for a, b in var.items()), d=d, t=int(H["t"][r[2]]), fi=int(r[2]),
                        ex=int(r[3]), R=r[1], Rt=Rt, sl_dist=risk, tp_dist=Rt * risk, hold=20 * 24, score_ok=j >= 0))
        busy = r[3]
    return out


SW_GRID = [dict(ltf=l, tp=t, score=s) for l in ("d1", "4h") for t in ("2R", "half") for s in ("0", "bias", "zmena")]

if __name__ == "__main__":
    part = sys.argv[1]
    mks = sys.argv[2:] or (DT_MARKETS if part == "dt" else SW_MARKETS)
    rows = []
    for mk in mks:
        for var in (DT_GRID if part == "dt" else SW_GRID):
            rows += run_dt(mk, var) if part == "dt" else run_sw(mk, var)
        print(part, mk, len(rows), flush=True)
    pd.DataFrame(rows).to_pickle(os.path.join(D17, f"f17_{part}{X.SUF}.pkl"))
