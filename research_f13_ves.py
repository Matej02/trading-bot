"""
F13 - Veselovsky: PDF + obrazky jako zdroj, doplnujici pravidla B2 jako dodatek (F13_PLAN.md).
Daily bias (jeho pravidla) -> killzone (Praha) -> sweep Asie (2-8) / PDL / 15m swingu pod NY daily open -> MSS na 1m/5m
(stroj F12, close za strong levelem s momentem + FVG v noze) v dulezite urovni -> limit FVG/0,618/OB 50 % ->
SL 2 pipy za sweep -> TP1 opacna strana Asie (50 % + BE) a TP2 cil biasu. Max 2 SL denne, po trefeni cile konec.
Spusteni: py research_f13_ves.py [trh ...] -> research_data/f13/f13_<trh>.pkl (F10_NOCOST=1 -> _nc)
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f10 as X
import research_f12 as F12
import research_f12_ms as MS

D13 = os.path.join("research_data", "f13")
os.makedirs(D13, exist_ok=True)
MARKETS = ["EURUSD", "GBPUSD", "XAUUSD", "NAS100mini", "SPX500mini"]
K = 1.5
DAY = 86400


# ---------------------------------------------------------------- daily bias [PDF Daily bias]
def michal_bias(D):
    n = len(D["c"])
    b = np.zeros(n, np.int8)
    o, h, l, c = D["o"], D["h"], D["l"], D["c"]
    for k in range(2, n):
        p, q = k - 1, k - 2                      # vcerejsi svicka p vs predvcerejsi q
        if c[p] > h[q]:
            b[k] = 1
        elif c[p] < l[q]:
            b[k] = -1
        elif h[p] > h[q] and c[p] < h[q]:
            b[k] = -1                            # sweep PDH a close pod
        elif l[p] < l[q] and c[p] > l[q]:
            b[k] = 1
        else:
            bt, bb = max(o[q], c[q]), min(o[q], c[q])
            if c[p] > bt:                        # close v hornim wicku
                b[k] = 1 if c[p] >= bt + 0.5 * (h[q] - bt) else -1
            elif c[p] < bb:
                b[k] = -1 if c[p] <= bb - 0.5 * (bb - l[q]) else 1
            else:
                b[k] = 0                         # uvnitr tela = range -> neobchodovat
    return b


# ---------------------------------------------------------------- dulezite zony na H1 / 15m
def build_zones(Tb, M, age_days, bpd):
    """FVG, iFVG, BPR a OB (B2: rada svicek opacne barvy jen tely, plati po close za zonou, FVG v impulzu).
    Vystup: pole (d, lo, hi, t0, t1, kind, hvn, imp) s t0/t1 jako M1 indexy."""
    o, h, l, c, st, en = Tb["o"], Tb["h"], Tb["l"], Tb["c"], Tb["st"], Tb["en"]
    n = len(c)
    nM = len(M["c"])
    age = int(age_days * 1440)
    rows = []
    act = []   # aktivni FVG: [d, lo, hi, j]
    lowmin = pd.Series(l).rolling(20).min().shift(1).to_numpy()
    highmax = pd.Series(h).rolling(20).max().shift(1).to_numpy()

    def close_beyond(j0, d, lo, hi):
        """prvni svicka TF po j0, ktera zavre za zonou proti smeru (d=1: pod lo); vraci M1 index konce nebo limit stari."""
        lim = min(n - 1, j0 + 1 + int(age_days * bpd))
        for j in range(j0 + 1, lim + 1):
            if (d == 1 and c[j] < lo) or (d == -1 and c[j] > hi):
                return j
        return -1

    for j in range(2, n):
        for d in (1, -1):
            if d == 1 and l[j] > h[j - 2]:
                lo, hi = h[j - 2], l[j]
            elif d == -1 and h[j] < l[j - 2]:
                lo, hi = h[j], l[j - 2]
            else:
                continue
            t0 = en[j] + 1
            if t0 >= nM:
                continue
            jb = close_beyond(j, d, lo, hi)
            t1 = min(en[jb] if jb >= 0 else t0 + age, t0 + age, nM - 1)
            rows.append((d, lo, hi, t0, t1, 0, 0, 0))                     # FVG
            if jb >= 0 and en[jb] < t0 + age:                              # iFVG = proletene FVG v opacnem smeru
                ti = en[jb] + 1
                jb2 = close_beyond(jb, -d, lo, hi)
                rows.append((-d, lo, hi, ti, min(en[jb2] if jb2 >= 0 else ti + age, ti + age, nM - 1), 1, 0, 0))
            # BPR: prekryv s aktivnim FVG opacneho smeru
            for a in act:
                if a[0] == -d and t0 <= a[4]:
                    blo, bhi = max(lo, a[1]), min(hi, a[2])
                    if bhi > blo:
                        rows.append((d, blo, bhi, t0, t1, 2, 0, 0))
            act.append([d, lo, hi, j, t1])
            act = [a for a in act if a[4] >= t0]
            # OB: posledni rada svicek opacne barvy pred impulzivni svickou j-1
            e = j - 2
            while e >= 0 and (c[e] - o[e]) * d >= 0 and e > j - 6:
                e -= 1
            if e < 0 or (c[e] - o[e]) * d >= 0:
                continue
            s = e
            while s - 1 >= 0 and (c[s - 1] - o[s - 1]) * d < 0 and e - s < 4:
                s -= 1
            blo = min(min(o[q], c[q]) for q in range(s, e + 1))
            bhi = max(max(o[q], c[q]) for q in range(s, e + 1))
            if bhi <= blo:
                continue
            # plati po close za zonou (d=1: close nad bhi)
            jv = -1
            for q in range(e + 1, min(n, e + 8)):
                if (d == 1 and c[q] > bhi) or (d == -1 and c[q] < blo):
                    jv = q
                    break
            if jv < 0:
                continue
            ta = en[jv] + 1
            if ta >= nM:
                continue
            # dulezita uroven: rada vybrala likviditu (low pod minimem 20 svicek) nebo lezi ve FVG
            imp = (d == 1 and l[s:e + 1].min() < lowmin[s]) or (d == -1 and h[s:e + 1].max() > highmax[s])
            if not imp:
                for a in act[:-1]:
                    if a[0] == d and a[1] <= bhi and a[2] >= blo:
                        imp = True
                        break
            # HVN: tick volume profil za 24 h pred aktivaci, 40 kosu
            s0 = max(0, ta - 1440)
            lo_p, hi_p = M["l"][s0:ta].min(), M["h"][s0:ta].max()
            hvn = 0
            if hi_p > lo_p:
                bw = (hi_p - lo_p) / 40
                mid = 0.5 * (M["h"][s0:ta] + M["l"][s0:ta])
                hist = np.bincount(np.clip(((mid - lo_p) / bw).astype(int), 0, 39), weights=M["v"][s0:ta], minlength=40)
                b0, b1 = int((blo - lo_p) / bw), int((bhi - lo_p) / bw)
                b0, b1 = max(0, b0), min(39, b1)
                med = np.median(hist[hist > 0]) if (hist > 0).any() else 0
                if b1 >= b0 and med > 0 and hist[b0:b1 + 1].max() >= 1.5 * med:
                    hvn = 1
            jb = close_beyond(jv, d, blo, bhi)
            t1o = min(en[jb] if jb >= 0 else ta + age, ta + age, nM - 1)
            rows.append((d, blo, bhi, ta, t1o, 3, hvn, int(imp)))
    Z = np.array(rows, float).reshape(-1, 8)
    return Z


# ---------------------------------------------------------------- priprava trhu
_C = {}


def prep(mk):
    if mk in _C:
        return _C[mk]
    M = X.load1(mk)
    T = X.tfs(M)
    T["M1"]["a"] = L.wilder_atr(M["h"], M["l"], M["c"], 14)
    cz, czday = F12.prague_hours(M["t"])
    D = T["D1"]
    n = len(M["c"])
    nyday = M["ny"] // DAY
    chg = np.r_[True, nyday[1:] != nyday[:-1]]
    nydo = M["o"][np.maximum.accumulate(np.where(chg, np.arange(n), 0))]
    # Asie 2-8 Praha
    m = (cz >= 2.0) & (cz < 8.0)
    g = pd.DataFrame({"d": czday[m], "h": M["h"][m], "l": M["l"][m]}).groupby("d").agg(h=("h", "max"), l=("l", "min"))
    asia = {int(k): (r.h, r.l) for k, r in g.iterrows()}
    # 15m swingy (pivot N=2, potvrzene)
    M15 = T["M15"]
    ph, pl = L.pivots(M15["h"], M15["l"], 2)
    piv_h = [(int(M15["en"][j + 2]), M15["h"][j]) for j in np.flatnonzero(ph) if j + 2 < len(M15["c"])]
    piv_l = [(int(M15["en"][j + 2]), M15["l"][j]) for j in np.flatnonzero(pl) if j + 2 < len(M15["c"])]
    P = dict(M=M, T=T, cz=cz, czday=czday, D=D, bias=michal_bias(D), nydo=nydo, asia=asia,
             dmap=np.searchsorted(D["st"], np.arange(n), side="right") - 1, news=X.news_days(),
             ph_t=np.array([p[0] for p in piv_h]), ph_v=np.array([p[1] for p in piv_h]),
             pl_t=np.array([p[0] for p in piv_l]), pl_v=np.array([p[1] for p in piv_l]))
    P["Z"] = np.vstack([build_zones(T["H1"], M, 20, 24), build_zones(M15, M, 5, 96)])
    P["S"] = {tf: MS.run(T[tf], K) for tf in ("M1", "M5")}
    _C.clear()
    _C[mk] = P
    return P


def kz_end(cz, i, d):
    """M1 index konce killzone, ve ktere lezi i (Londyn 8-11, long do 11:30; NY 14-17), jinak -1."""
    h = cz[i]
    if 8.0 <= h < (11.5 if d == 1 else 11.0):
        end = 11.5 if d == 1 else 11.0
    elif 14.0 <= h < 17.0:
        end = 17.0
    else:
        return -1
    j = i
    while j + 1 < len(cz) and cz[j + 1] < end and cz[j + 1] >= h:
        j += 1
    return j


def run_market(mk, var, info=False):
    P = prep(mk)
    M, T, cz, czday, D, Z = P["M"], P["T"], P["cz"], P["czday"], P["D"], P["Z"]
    tf = var["tf"]
    Xb = T[tf]
    ev = P["S"][tf]["ev"]
    n = len(M["c"])
    t = M["t"]
    out = []
    busy = -1
    losses, done_day = {}, set()
    fx = mk in ("EURUSD", "GBPUSD")
    for q in range(1, len(ev["i"])):
        if not ev["flip"][q] or ev["d"][q - 1] != -ev["d"][q]:
            continue
        d = int(ev["d"][q])
        ic = int(Xb["en"][ev["i"][q]])            # MSS potvrzena (zavrena svicka po pruraze)
        if ic + 2 >= n or ic <= busy:
            continue
        ke = kz_end(cz, ic, d)
        if ke < 0 or ke <= ic:
            continue
        day = int(czday[ic])
        par = var.get("parity", False)            # kontrola shody s TS: bez stavu (zpravy, busy, 2 SL) a bez simulace
        if not par and (day in done_day or losses.get(day, 0) >= 2 or (t[ic] // DAY) in P["news"]):
            continue
        kD = int(P["dmap"][ic])
        if kD < 2:
            continue
        if var.get("bias", 1) and P["bias"][kD] != d:
            continue
        tgt = D["h"][kD - 1] if d == 1 else D["l"][kD - 1]
        s_day = int(D["st"][kD])
        if var.get("bias", 1):
            seg_h, seg_l = M["h"][s_day:ic + 1].max(), M["l"][s_day:ic + 1].min()
            if (d == 1 and seg_h >= tgt) or (d == -1 and seg_l <= tgt):
                done_day.add(day)                 # cil biasu (externi LQ) uz trefen -> den hotovy
                continue
        sti = int(ev["sti"][q])
        sv = float(ev["st"][q])
        i_sw = int(Xb["st"][sti])                 # zacatek svicky sweepu (M1)
        if ic - i_sw > 180:
            continue
        # likvidita vybrana timto sweepem poprve (od 8:00 Praha): Asie, PDL/PDH, posledni 15m swing
        a = P["asia"].get(day)
        if a is None or cz[i_sw] < 8.0:
            continue
        i8 = max(i_sw - int(round((cz[i_sw] - 8.0) * 60)), s_day)
        # (uroven, odkud se hlida, ze ji drive nikdo nevybral): Asie a PDL od 8:00, 15m swing od jeho potvrzeni
        levels = [(a[1] if d == 1 else a[0], i8), (D["l"][kD - 1] if d == 1 else D["h"][kD - 1], i8)]
        pt, pv = (P["pl_t"], P["pl_v"]) if d == 1 else (P["ph_t"], P["ph_v"])
        kp = int(np.searchsorted(pt, i_sw)) - 1
        if kp >= 0:
            levels.append((pv[kp], max(int(pt[kp]), i8)))
        took = False
        for lv, f0 in levels:
            if (sv - lv) * d >= 0:
                continue
            seg = M["l"][f0:i_sw + 1] if d == 1 else M["h"][f0:i_sw + 1]
            k1 = np.flatnonzero(seg < lv) if d == 1 else np.flatnonzero(seg > lv)
            # sweep = prvni vybrani urovne patri k teto noze (nejdyl 60 min pred extremem)
            if len(k1) and f0 + k1[0] >= i_sw - 60:
                took = True
                break
        if not took:
            continue
        if var.get("nydo", 1) and ((d == 1 and not sv < P["nydo"][i_sw]) or (d == -1 and not sv > P["nydo"][i_sw])):
            continue
        # displacement: FVG v noze MSS (na tf)
        i_ev = int(ev["i"][q])
        fvgs = []
        for r in range(sti + 2, i_ev + 1):
            if d == 1 and Xb["l"][r] > Xb["h"][r - 2]:
                fvgs.append((Xb["h"][r - 2], Xb["l"][r]))
            if d == -1 and Xb["h"][r] < Xb["l"][r - 2]:
                fvgs.append((Xb["h"][r], Xb["l"][r - 2]))
        if not fvgs:
            continue
        # dulezita uroven
        if var["lvl"] != "liq":
            m = (Z[:, 0] == d) & (Z[:, 3] <= i_sw) & (i_sw <= Z[:, 4])
            hz = Z[:, 2] - Z[:, 1]
            m &= (sv <= Z[:, 2] + 0.25 * hz) & (sv >= Z[:, 1] - 0.5 * hz) if d == 1 else \
                (sv >= Z[:, 1] - 0.25 * hz) & (sv <= Z[:, 2] + 0.5 * hz)
            if var["lvl"] == "obhvn":
                m &= (Z[:, 5] == 3) & (Z[:, 6] == 1) & (Z[:, 7] == 1)
            if not m.any():
                continue
        # vstup
        ext = M["h"][i_sw:ic + 1].max() if d == 1 else M["l"][i_sw:ic + 1].min()
        leg = abs(ext - sv)
        if var["entry"] == "gp":
            E = ext - d * 0.618 * leg
        elif var["entry"] == "fvg":
            l382 = ext - d * 0.382 * leg
            lo, hi = fvgs[-1]
            best = min(fvgs, key=lambda z: 0 if z[0] <= l382 <= z[1] else min(abs(l382 - z[0]), abs(l382 - z[1])))
            lo, hi = best
            E = min(max(l382, lo), hi)
        else:
            e = int(ev["brk"][q]) - 1
            while e > sti and (Xb["c"][e] - Xb["o"][e]) * d >= 0:
                e -= 1
            if (Xb["c"][e] - Xb["o"][e]) * d >= 0:
                continue
            s = e
            while s - 1 >= sti and (Xb["c"][s - 1] - Xb["o"][s - 1]) * d < 0 and e - s < 4:
                s -= 1
            blo = min(min(Xb["o"][r], Xb["c"][r]) for r in range(s, e + 1))
            bhi = max(max(Xb["o"][r], Xb["c"][r]) for r in range(s, e + 1))
            E = 0.5 * (blo + bhi)
        if (d == 1 and E >= M["c"][ic]) or (d == -1 and E <= M["c"][ic]):
            continue                              # limit musi byt v pullbacku
        atrD = D["a"][kD - 1]
        if not atrD > 0:
            continue
        SL = sv - d * 2 * M["pip"]
        risk = (E - SL) * d
        mx = 15 * M["pip"] if fx else 0.21 * atrD
        if risk <= 0 or risk > mx or (not par and risk < 3 * M["spr"][ic]):
            continue
        Rt = (tgt - E) * d / risk
        if Rt < 2.0:
            continue
        Rt = min(Rt, 10.0)
        TP = E + d * Rt * risk
        if par:
            for r in range(ic + 1, ke + 1):
                if (d == 1 and M["l"][r] <= E) or (d == -1 and M["h"][r] >= E):
                    out.append([int(t[r]), d, float(SL), float(TP)])
                    break
            continue
        i_x = ic
        while i_x + 1 < n and czday[i_x + 1] == day and cz[i_x + 1] < 22.0:
            i_x += 1
        tp1 = np.nan
        if var["tp"] == "tp12":
            a1 = a[0] if d == 1 else a[1]
            if (a1 - E) * d >= 1.0 * risk and (TP - a1) * d > 0:
                tp1 = a1
        s = X.sim(M, d, E, SL, TP, ic + 1, ke, 0, i_x, tp1=tp1, f1=0.5 if np.isfinite(tp1) else 0.0,
                  be=bool(np.isfinite(tp1)))
        if not s:
            continue
        r = X.rec(M, "F13", X.vn(var), d, s, Rt, atrD, "den")
        r.update(sl_dist=risk, tp_dist=Rt * risk, cz=float(cz[s["fi"]]))
        if info:
            r.update(E_=s["E"], SL_=SL, TP_=TP, TP1_=tp1, sv=sv, i_sw=i_sw, ic=ic)
        out.append(r)
        busy = s["ex"]
        if s["R"] < 0:
            losses[day] = losses.get(day, 0) + 1
    return out


GRID = [dict(tf=tf, lvl=lv, entry=e, tp=tp) for tf in ("M1", "M5") for lv in ("liq", "zona", "obhvn")
        for e in ("fvg", "gp", "ob50") for tp in ("tp12", "tp2")]

if __name__ == "__main__":
    for mk in sys.argv[1:] or MARKETS:
        rows = []
        for var in GRID:
            rows += run_market(mk, var)
        pd.DataFrame(rows).to_pickle(os.path.join(D13, f"f13_{mk}{X.SUF}.pkl"))
        print(mk, len(rows), flush=True)
