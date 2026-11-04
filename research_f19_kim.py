"""
F19 - Kimmel entry model 2 (pokracovaci) podle PDF a obrazku 27-30 (model 1 byl v F10/F11):
bias dne (Veselovskeho pravidla jako F13 / barva vcerejsi svicky) -> v okne 15:30-18:00 Praha dotek 15m S/D zony ve smeru biasu
-> 2 po sobe jdouci zmeny struktury (stroj F12 na 1m, close telem s momentem) ve smeru biasu -> vstup: limit do nejblizsi zony
(FVG z nohy 2. MSS) / trhem na close 2. MSS -> SL za 3. (konzervativne 4.) predchozim bodem zajmu: 3 = strong level 1. MSS
(sweep low), 4 = distal 15m zony -> TP interni likvidita (nejblizsi neprobrany 5m pivot high, min 1,5 R) / 2R / externi (PDH).
Best pair: pro NQ/ES se obchoduje jen trh silnejsi ve smeru biasu od 15:30. Konec dne 22:00.
Spusteni: py research_f19_kim.py -> research_data/f19/f19.pkl (F10_NOCOST=1 -> _nc)
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
import research_f12_ms as MS
import research_f13_ves as V13

D19 = os.path.join("research_data", "f19")
os.makedirs(D19, exist_ok=True)
MARKETS = ["NAS100mini", "SPX500mini", "US30mini"]
PAIR = {"NAS100mini": "SPX500mini", "SPX500mini": "NAS100mini"}
_C = {}


def prep(mk):
    if mk in _C:
        return _C[mk]
    M = X.load1(mk)
    T = X.tfs(M)
    T["M1"]["a"] = L.wilder_atr(M["h"], M["l"], M["c"], 14)
    cz, czday = F12.prague_hours(M["t"])
    D = T["D1"]
    _, bm = X.bias_arrays(D)
    ph5, _ = L.pivots(T["M5"]["h"], T["M5"]["l"], 2)
    _, pl5 = L.pivots(T["M5"]["h"], T["M5"]["l"], 2)
    P = dict(M=M, T=T, cz=cz, czday=czday, D=D, bv=V13.michal_bias(D), bm=bm, Zq=F.find_zones(T["M15"], 1.5),
             S1=MS.run(T["M1"], 1.5), dmap=np.searchsorted(D["st"], np.arange(len(M["c"])), side="right") - 1,
             ph5=np.flatnonzero(ph5), pl5=np.flatnonzero(pl5))
    if len(_C) > 2:
        _C.clear()
    _C[mk] = P
    return P


def day_open_strength(P, day, d):
    """Pohyb od 15:30 Praha do ted (posledni minuty okna) ve smeru d v jednotkach ATR D1 - pro best pair."""
    M, cz, czday = P["M"], P["cz"], P["czday"]
    idx = np.flatnonzero((czday == day) & (cz >= 15.5) & (cz < 18.0))
    if len(idx) < 30:
        return None, None
    return idx, (M["c"][idx] - M["o"][idx[0]]) * d


def run_market(mk, var):
    P = prep(mk)
    M, T, cz, czday, D = P["M"], P["T"], P["cz"], P["czday"], P["D"]
    Q, X1, X5 = T["M15"], T["M1"], T["M5"]
    ev = P["S1"]["ev"]
    n = len(M["c"])
    out = []
    busy = -1
    used = set()
    Pp = prep(PAIR[mk]) if var["pair"] and mk in PAIR else None
    ev_i = ev["i"]
    for z in P["Zq"]:
        d = z["d"]
        ia = int(Q["en"][z["act"]])
        i_last = min(int(Q["en"][min(z["inv"], len(Q["en"]) - 1)]), ia + 5 * 1440, n - 2)
        fi = X.m1_first(M, ia + 1, i_last, cond_low=z["prox"] if d == 1 else None, cond_high=z["prox"] if d == -1 else None)
        if fi < 0 or fi <= busy or not (15.5 <= cz[fi] < 18.0):
            continue
        day = int(czday[fi])
        if (day, d) in used:
            continue
        kD = int(P["dmap"][fi])
        b = int(P["bv"][kD] if var["bias"] == "V" else P["bm"][kD])
        if b != d:
            continue
        # 2 po sobe jdouci MSS ve smeru d po doteku (do 18:00), mezi nimi zadna opacna udalost
        q0 = int(np.searchsorted(ev_i, int(np.searchsorted(X1["st"], fi))))
        got = []
        for q in range(q0, len(ev_i)):
            iq = int(X1["en"][ev_i[q]])
            if cz[iq] >= 18.0 or czday[iq] != day:
                break
            if ev["d"][q] != d:
                got = []
                continue
            got.append(q)
            if len(got) == 2:
                break
        if len(got) < 2:
            continue
        q1, q2 = got
        ic = int(X1["en"][ev_i[q2]])
        if ic + 2 >= n:
            continue
        # best pair: druhy trh musi byt od 15:30 slabsi ve smeru biasu
        if Pp is not None:
            j = int(np.searchsorted(Pp["M"]["t"], M["t"][ic]))
            sd = int(Pp["czday"][min(j, len(Pp["czday"]) - 1)])
            idx_o, mv_o = day_open_strength(Pp, sd, d)
            idx_s, mv_s = day_open_strength(P, day, d)
            if idx_o is None or idx_s is None:
                continue
            k_o = int(np.searchsorted(Pp["M"]["t"][idx_o], M["t"][ic], side="right")) - 1
            k_s = int(np.searchsorted(M["t"][idx_s], M["t"][ic], side="right")) - 1
            if k_o < 0 or k_s < 0:
                continue
            aD_o = Pp["D"]["a"][max(0, int(Pp["dmap"][idx_o[0]]) - 1)]
            aD_s = D["a"][max(0, kD - 1)]
            if not (aD_o > 0 and aD_s > 0) or mv_s[k_s] / aD_s <= mv_o[k_o] / aD_o:
                continue
        # SL: 3. POI = strong level 1. MSS, 4. POI = distal 15m zony
        a1 = X1["a"][ev_i[q2]] if "a" in X1 else T["M15"]["a"][int(np.searchsorted(Q["st"], ic, side="right")) - 1]
        SL3 = float(ev["st"][q1])
        SL = SL3 if var["sl"] == "poi3" else (min(SL3, z["dist"]) if d == 1 else max(SL3, z["dist"]))
        SL -= d * 0.1 * T["M15"]["a"][int(np.searchsorted(Q["st"], ic, side="right")) - 1]
        # vstup
        sti2 = int(ev["sti"][q2])
        if var["entry"] == "trh":
            i0 = ic + 1
            E, iv, kind = M["o"][i0] + (M["spr"][i0] if d == 1 else 0), i0, 1
        else:
            fv = None
            for r in range(sti2 + 2, int(ev_i[q2]) + 1):
                if d == 1 and X1["l"][r] > X1["h"][r - 2]:
                    fv = (X1["h"][r - 2], X1["l"][r])
                elif d == -1 and X1["h"][r] < X1["l"][r - 2]:
                    fv = (X1["h"][r], X1["l"][r - 2])
            if fv is None:
                continue
            E = fv[1] if d == 1 else fv[0]
            if (d == 1 and E >= M["c"][ic]) or (d == -1 and E <= M["c"][ic]):
                continue
            i0 = ic + 1
            j18 = i0
            while j18 + 1 < n and czday[j18 + 1] == day and cz[j18 + 1] < 18.0:
                j18 += 1
            iv, kind = j18, 0
        risk = (E - SL) * d
        if risk <= 0 or risk < 3 * M["spr"][ic]:
            continue
        if var["tp"] == "2R":
            Rt = 2.0
        elif var["tp"] == "ext":
            tgt = D["h"][kD - 1] if d == 1 else D["l"][kD - 1]
            Rt = (tgt - E) * d / risk
            if Rt < 1.5:
                continue
            Rt = min(Rt, 6.0)
        else:
            piv = P["ph5"] if d == 1 else P["pl5"]
            k5 = int(np.searchsorted(X5["st"], ic, side="right")) - 1
            piv = piv[(piv <= k5 - 2) & (piv >= k5 - 288)]
            pr = X5["h"][piv] if d == 1 else X5["l"][piv]
            seg_hi = M["h"][int(X5["st"][max(0, k5 - 288)]):ic + 1].max()
            seg_lo = M["l"][int(X5["st"][max(0, k5 - 288)]):ic + 1].min()
            cand = []
            for p_, v_ in zip(piv, pr):
                after = M["h"][int(X5["en"][p_]) + 1:ic + 1] if d == 1 else M["l"][int(X5["en"][p_]) + 1:ic + 1]
                taken = len(after) and ((d == 1 and after.max() > v_) or (d == -1 and after.min() < v_))
                if not taken and (v_ - E) * d >= 1.5 * risk:
                    cand.append((v_ - E) * d / risk)
            if not cand:
                continue
            Rt = min(min(cand), 6.0)
        i_x = i0
        while i_x + 1 < n and czday[i_x + 1] == day and cz[i_x + 1] < 22.0:
            i_x += 1
        s = X.sim(M, d, E, SL, E + d * Rt * risk, i0, iv, kind, i_x)
        if not s:
            continue
        r = X.rec(M, "F19", X.vn(var), d, s, Rt, D["a"][max(0, kD - 1)], "den")
        r.update(sl_dist=risk, tp_dist=Rt * risk, cz=float(cz[s["fi"]]))
        out.append(r)
        busy = s["ex"]
        used.add((day, d))
    return out


GRID = [dict(bias=b, pair=p, entry=e, sl=s, tp=t) for b in ("V", "M") for p in (1, 0) for e in ("fvg", "trh")
        for s in ("poi3", "poi4") for t in ("int", "2R", "ext")]

if __name__ == "__main__":
    rows = []
    for mk in MARKETS:
        for var in GRID:
            if var["pair"] and mk not in PAIR:
                continue
            rows += run_market(mk, var)
        print(mk, len(rows), flush=True)
    pd.DataFrame(rows).to_pickle(os.path.join(D19, f"f19{X.SUF}.pkl"))
