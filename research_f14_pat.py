"""
F14 - Patek: PDF + obrazky jako zdroj, B3 jako dodatek (F14_PLAN.md).
Model A (ve smeru H4): odmitnuti v H4 S/R zone -> nizsi high / vyssi low (pivoty M5/M15) -> close za poslednim pivotem ->
vstup trhem, SL za LH/HL, TP 2R / H1 pivot / protejsi H4 zona (RR >= 2).
Model B (proti H4, pullback): HL/LH + prurazu pivotu proti H4 trendu, TP = H4 zona zleva, SL za svickou pred prurazem.
Spusteni: py research_f14_pat.py [trh ...] -> research_data/f14/f14_<trh>.pkl (F10_NOCOST=1 -> _nc)
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

D14 = os.path.join("research_data", "f14")
os.makedirs(D14, exist_ok=True)
MARKETS = ["NAS100mini", "GBPUSD", "XAUUSD"]
HELD_OUT = ["SPX500mini", "US30mini", "GER_30mini"]
SESS = {"open": ((9.0, 12.0), (15.5, 18.0)), "full": ((9.0, 17.0), (15.5, 22.0))}
TOL = 0.25
WIN4 = 300

_C = {}


def prep(mk):
    if mk in _C:
        return _C[mk]
    M = X.load1(mk)
    T = X.tfs(M)
    n = len(M["c"])
    cz, czday = F12.prague_hours(M["t"])
    H4, H1, D = T["H4"], T["H1"], T["D1"]
    _, _, tr4 = F.last_swing(H4["h"], H4["l"], 2)
    _, _, trD = F.last_swing(D["h"], D["l"], 2)
    ph4, pl4 = L.pivots(H4["h"], H4["l"], 2)
    # H4 pivoty (index potvrzeni = j+2, cena): high i low dohromady (role reversal)
    pj = np.r_[np.flatnonzero(ph4), np.flatnonzero(pl4)]
    pp = np.r_[H4["h"][ph4], H4["l"][pl4]]
    o = np.argsort(pj, kind="stable")
    ph1, pl1 = L.pivots(H1["h"], H1["l"], 2)
    P = dict(M=M, T=T, cz=cz, czday=czday, tr4=tr4, trD=trD, c4=X.closed_map(H4, n), cD=X.closed_map(D, n),
             c1h=X.closed_map(H1, n), pj4=pj[o] + 2, pp4=pp[o],
             h1h_j=np.flatnonzero(ph1) + 2, h1h_p=H1["h"][ph1], h1l_j=np.flatnonzero(pl1) + 2, h1l_p=H1["l"][pl1])
    P["piv"] = {}
    for tf in ("M5", "M15"):
        Xb = T[tf]
        ph, pl = L.pivots(Xb["h"], Xb["l"], 3)
        P["piv"][tf] = (ph, pl)
    _C.clear()
    _C[mk] = P
    return P


def zone_near(P, k4, x, a4):
    """H4 S/R zona (>= 2 pivoty do tolerance) kolem ceny x: vraci (lo, hi, pocet) nebo None."""
    j1 = int(np.searchsorted(P["pj4"], k4, side="right"))
    j0 = int(np.searchsorted(P["pj4"], k4 - WIN4))
    p = P["pp4"][j0:j1]
    m = np.abs(p - x) <= TOL * a4
    if m.sum() >= 2:
        return p[m].min(), p[m].max(), int(m.sum())
    return None


def next_zone(P, k4, E, d, a4):
    """Nejblizsi H4 zona (>= 2 dotyky) ve smeru d od ceny E: vraci blizsi hranu zony nebo nan."""
    j1 = int(np.searchsorted(P["pj4"], k4, side="right"))
    j0 = int(np.searchsorted(P["pj4"], k4 - WIN4))
    p = np.sort(P["pp4"][j0:j1])
    cand = p[p > E] if d == 1 else p[p < E][::-1]
    for x in cand:
        m = np.abs(p - x) <= TOL * a4
        if m.sum() >= 2:
            return p[m].min() if d == 1 else p[m].max()
    return np.nan


def next_h1_pivot(P, i, E, d):
    k1 = int(P["c1h"][i])
    if d == 1:
        j, pr = P["h1h_j"], P["h1h_p"]
    else:
        j, pr = P["h1l_j"], P["h1l_p"]
    m = (j <= k1) & (j > k1 - 24 * 20)
    pr = pr[m]
    pr = pr[pr > E] if d == 1 else pr[pr < E]
    if not len(pr):
        return np.nan
    return pr.min() if d == 1 else pr.max()


def run_market(mk, var, info=False):
    P = prep(mk)
    M, T, cz, czday = P["M"], P["T"], P["cz"], P["czday"]
    tf = var["tf"]
    Xb = T[tf]
    H4 = T["H4"]
    ph, pl = P["piv"][tf]
    n = len(M["c"])
    sess = SESS[var["sess"]]
    out = []
    piv_h, piv_l = [], []
    busy = -1
    for j in range(4, len(Xb["c"])):
        p = j - 3
        if ph[p]:
            piv_h.append((p, Xb["h"][p]))
        if pl[p]:
            piv_l.append((p, Xb["l"][p]))
        if len(piv_h) < 2 or len(piv_l) < 2:
            continue
        i_end = int(Xb["en"][j])
        h_ = cz[i_end]
        if not any(a <= h_ < b for a, b in sess):
            continue
        if (i_end <= busy and not var.get("parity")) or i_end + 2 >= n:
            continue
        k4 = int(P["c4"][i_end])
        if k4 < 5:
            continue
        t4 = int(P["tr4"][k4])
        if t4 == 0:
            continue
        a4 = H4["a"][k4]
        if not a4 > 0:
            continue
        if var.get("d1", 0):
            kd = int(P["cD"][i_end])
            if kd < 3 or int(P["trD"][kd]) != t4:
                continue
        d = t4 if var["model"] == "A" else -t4
        # LH/HL + close za poslednim pivotem (prave ted, ne drive)
        if d == -1:
            (ip1, h1), (ip0, h0) = piv_h[-1], piv_h[-2]
            lastL = piv_l[-1][1]
            if var.get("lhhl", 1) and not h1 < h0:
                continue
            if not (Xb["c"][j] < lastL and Xb["c"][j - 1] >= lastL):
                continue
            ext = h1
        else:
            (ip1, l1), (ip0, l0) = piv_l[-1], piv_l[-2]
            lastH = piv_h[-1][1]
            if var.get("lhhl", 1) and not l1 > l0:
                continue
            if not (Xb["c"][j] > lastH and Xb["c"][j - 1] <= lastH):
                continue
            ext = l1
        i0 = i_end + 1
        E0 = M["o"][i0]
        if var["model"] == "A":
            # 1) odmitnuti: pullback (extrem za poslednich 24 svicek) v H4 zone proti smeru
            if var.get("rej", 1):
                pull = Xb["h"][max(0, j - 24):j + 1].max() if d == -1 else Xb["l"][max(0, j - 24):j + 1].min()
                z = zone_near(P, k4, pull, a4)
                if z is None or (d == -1 and z[1] < E0) or (d == 1 and z[0] > E0):
                    continue
            SL = ext - d * 10 * M["tick"]
        else:
            SL = (Xb["l"][j - 1] if d == 1 else Xb["h"][j - 1]) - d * 10 * M["tick"]
        risk = (E0 - SL) * d
        if risk <= 0 or (risk < 3 * M["spr"][i0] and not var.get("parity")):
            continue
        if var["tp"] == "2R":
            Rt = 2.0
        elif var["tp"] == "pivot":
            x = next_h1_pivot(P, i_end, E0, d)
            if not np.isfinite(x):
                continue
            Rt = (x - E0) * d / risk
        else:
            x = next_zone(P, k4, E0, d, a4)
            if not np.isfinite(x):
                continue
            Rt = (x - E0) * d / risk
        if Rt < 2.0:
            continue
        Rt = min(Rt, 5.0)
        TP = E0 + d * Rt * risk
        if var.get("parity"):                     # kontrola shody s TS: signal bez stavu (busy) a bez simulace
            out.append([int(M["t"][int(Xb["st"][j])]), d, float(SL), float(TP)])
            continue
        day = czday[i0]
        i_x = i0
        while i_x + 1 < n and czday[i_x + 1] == day and cz[i_x + 1] < 22.0:
            i_x += 1
        s = X.sim(M, d, E0, SL, TP, i0, i0, 1, i_x)
        if not s:
            continue
        r = X.rec(M, "F14", X.vn({k: v for k, v in var.items()}), d, s, Rt, H4["a"][k4], "den")
        r.update(sl_dist=risk, tp_dist=Rt * risk, cz=float(cz[i0]))
        if info:
            r.update(E_=s["E"], SL_=SL, TP_=TP, ij=int(Xb["st"][max(0, j - 24)]))
        out.append(r)
        busy = s["ex"]
    return out


GRID = [dict(model="A", tf=tf, sess=se, tp=tp) for tf in ("M5", "M15") for se in ("open", "full") for tp in ("2R", "pivot", "zona")] + \
       [dict(model="B", tf=tf, sess=se, tp="zona") for tf in ("M5", "M15") for se in ("open", "full")]

if __name__ == "__main__":
    for mk in sys.argv[1:] or MARKETS:
        rows = []
        for var in GRID:
            rows += run_market(mk, var)
        pd.DataFrame(rows).to_pickle(os.path.join(D14, f"f14_{mk}{X.SUF}.pkl"))
        print(mk, len(rows), flush=True)
