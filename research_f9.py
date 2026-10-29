"""
F9 - kombinace FM konceptu (viz F9_PLAN.md). Spoustece (T) x filtry (F) x TP; signal na zavreni H1 svicky,
vstup trhem na open dalsi, SL podle konceptu, TP v R, max 48 H1 svicek. Vyber 2010-17, validace 2018-21, holdout 2022+.
Vystup: research_data/f9/f9_udalosti.pkl (kazdy spoustec 1x s vysledky pro R 1,5/2/3 a priznaky filtru).
"""
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f8 as F

D9 = os.path.join("research_data", "f9")
os.makedirs(D9, exist_ok=True)
MARKETS = F.MARKETS + ["BTCUSD", "ETHUSD"]
TRIG = ["sweepPD", "sweepAsia", "mss", "fvg", "ob", "zona", "prurazPivot", "balance"]
FILT = ["trendD1", "trendH4", "emaD1", "biasV", "biasM", "discount", "kz", "nyDO", "zonaH4"]
RS = (1.5, 2.0, 3.0)
HOLD = 48
SPLIT1 = pd.Timestamp("2018-01-01", tz="UTC").value // 10**9
SPLIT2 = pd.Timestamp("2022-01-01", tz="UTC").value // 10**9


@njit(cache=True)
def _ai(x):
    a = np.empty(len(x), np.int64)
    for k in range(len(x)):
        a[k] = x[k]
    return a


@njit(cache=True)
def _af(x):
    a = np.empty(len(x), np.float64)
    for k in range(len(x)):
        a[k] = x[k]
    return a


# ---------------------------------------------------------------- spoustece (numba)
@njit(cache=True)
def trig_sweeps(h, l, c, day, hl, pdh, pdl, a1):
    """sweepPD (typ 0) a sweepAsia (typ 1). Vraci pole (i, d, sl, typ)."""
    n = len(c)
    out_i = [0]; out_i.pop(); out_d = [0]; out_d.pop(); out_sl = [0.0]; out_sl.pop(); out_t = [0]; out_t.pop()
    asH, asL = np.nan, np.nan
    swPDl = swPDh = swAl = swAh = False
    lowday, highday = np.inf, -np.inf
    lowpost, highpost = np.inf, -np.inf
    for i in range(1, n):
        if day[i] != day[i - 1]:
            asH, asL = -np.inf, np.inf
            swPDl = swPDh = swAl = swAh = False
            lowday, highday = np.inf, -np.inf
            lowpost, highpost = np.inf, -np.inf
        if 3 <= hl[i] < 9:
            asH = max(asH, h[i])
            asL = min(asL, l[i])
        # PD sweep (cely den)
        if np.isfinite(pdl[i]):
            if not swPDl and l[i] < pdl[i]:
                swPDl = True
                if c[i] > pdl[i]:
                    out_i.append(i); out_d.append(1); out_sl.append(min(lowday, l[i]) - 0.1 * a1[i]); out_t.append(0)
            if not swPDh and h[i] > pdh[i]:
                swPDh = True
                if c[i] < pdh[i]:
                    out_i.append(i); out_d.append(-1); out_sl.append(max(highday, h[i]) + 0.1 * a1[i]); out_t.append(0)
        lowday = min(lowday, l[i])
        highday = max(highday, h[i])
        # Asie sweep 02-12 NY (hl 9..18)
        if 9 <= hl[i] < 19 and np.isfinite(asL) and asH > -np.inf:
            lowpost = min(lowpost, l[i])
            highpost = max(highpost, h[i])
            if not swAl and l[i] < asL:
                swAl = True
                if c[i] > asL:
                    out_i.append(i); out_d.append(1); out_sl.append(lowpost - 0.1 * a1[i]); out_t.append(1)
            if not swAh and h[i] > asH:
                swAh = True
                if c[i] < asH:
                    out_i.append(i); out_d.append(-1); out_sl.append(highpost + 0.1 * a1[i]); out_t.append(1)
    return _ai(out_i), _ai(out_d), _af(out_sl), _ai(out_t)


@njit(cache=True)
def trig_mss(h, l, c, sw_i, sw_d, a1):
    """Do 12 svicek po sweepu close za max/min 6 svicek pred sweepem -> vstup; SL za extrem od sweepu."""
    n = len(c)
    oi = [0]; oi.pop(); od = [0]; od.pop(); osl = [0.0]; osl.pop()
    for k in range(len(sw_i)):
        s, d = sw_i[k], sw_d[k]
        if s < 7:
            continue
        if d == 1:
            lvl = h[s - 6:s + 1].max()
            ext = l[s]
            for i in range(s + 1, min(s + 13, n)):
                ext = min(ext, l[i])
                if c[i] > lvl:
                    oi.append(i); od.append(1); osl.append(ext - 0.1 * a1[i])
                    break
        else:
            lvl = l[s - 6:s + 1].min()
            ext = h[s]
            for i in range(s + 1, min(s + 13, n)):
                ext = max(ext, h[i])
                if c[i] < lvl:
                    oi.append(i); od.append(-1); osl.append(ext + 0.1 * a1[i])
                    break
    return _ai(oi), _ai(od), _af(osl)


@njit(cache=True)
def trig_fvg(o, h, l, c, a1):
    n = len(c)
    oi = [0]; oi.pop(); od = [0]; od.pop(); osl = [0.0]; osl.pop()
    for j in range(2, n - 1):
        a = a1[j]
        if not a > 0:
            continue
        for d in (1, -1):
            if d == 1:
                gap = l[j] - h[j - 2]
                ok = gap >= 0.3 * a and c[j - 1] > o[j - 1]
                lo, hi = h[j - 2], l[j]
                sl = min(l[j - 2], l[j - 1]) - 0.1 * a
            else:
                gap = l[j - 2] - h[j]
                ok = gap >= 0.3 * a and c[j - 1] < o[j - 1]
                lo, hi = h[j], l[j - 2]
                sl = max(h[j - 2], h[j - 1]) + 0.1 * a
            if not ok:
                continue
            mid = 0.5 * (lo + hi)
            for i in range(j + 1, min(j + 25, n)):
                if d == 1:
                    if c[i] < lo:
                        break
                    if l[i] <= mid:
                        if c[i] > mid:
                            oi.append(i); od.append(1); osl.append(sl)
                        break
                else:
                    if c[i] > hi:
                        break
                    if h[i] >= mid:
                        if c[i] < mid:
                            oi.append(i); od.append(-1); osl.append(sl)
                        break
    return _ai(oi), _ai(od), _af(osl)


@njit(cache=True)
def trig_ob(o, h, l, c, sh, sl_, a1):
    """BOS = close za poslednim potvrzenym pivotem (N=3); OB = posledni opacna svicka do 10 svicek zpet; retest do 48 svicek."""
    n = len(c)
    oi = [0]; oi.pop(); od = [0]; od.pop(); osl = [0.0]; osl.pop()
    used_h, used_l = np.nan, np.nan
    for k in range(1, n - 1):
        for d in (1, -1):
            lvl = sh[k] if d == 1 else sl_[k]
            if not np.isfinite(lvl):
                continue
            if d == 1 and (c[k] <= lvl or c[k - 1] > lvl or lvl == used_h):
                continue
            if d == -1 and (c[k] >= lvl or c[k - 1] < lvl or lvl == used_l):
                continue
            if d == 1:
                used_h = lvl
            else:
                used_l = lvl
            ob = -1
            for j in range(k - 1, max(k - 11, 0), -1):
                if (c[j] - o[j]) * d < 0:
                    ob = j
                    break
            if ob < 0:
                continue
            top, bot = (h[ob], l[ob]) if d == 1 else (l[ob], h[ob])
            for i in range(k + 1, min(k + 49, n)):
                if (c[i] - bot) * d < 0:
                    break
                touch = l[i] <= top if d == 1 else h[i] >= top
                if touch:
                    if (c[i] - top) * d > 0:
                        oi.append(i); od.append(d); osl.append(bot - d * 0.1 * a1[i])
                    break
    return _ai(oi), _ai(od), _af(osl)


@njit(cache=True)
def trig_pivot_break(c, sh, sl_, a1):
    n = len(c)
    oi = [0]; oi.pop(); od = [0]; od.pop(); osl = [0.0]; osl.pop()
    for i in range(1, n):
        if np.isfinite(sh[i]) and c[i] > sh[i] and c[i - 1] <= sh[i] and np.isfinite(sl_[i]):
            oi.append(i); od.append(1); osl.append(sl_[i] - 0.1 * a1[i])
        if np.isfinite(sl_[i]) and c[i] < sl_[i] and c[i - 1] >= sl_[i] and np.isfinite(sh[i]):
            oi.append(i); od.append(-1); osl.append(sh[i] + 0.1 * a1[i])
    return _ai(oi), _ai(od), _af(osl)


# ---------------------------------------------------------------- priprava trhu
def map_closed(st, en, n):
    """Pro kazdou H1 svicku index posledni UZAVRENE svicky vyssiho TF (-1 = zadna)."""
    idx = np.searchsorted(st, np.arange(n), side="right") - 1
    closed = np.where(np.arange(n) == en[idx], idx, idx - 1)
    return idx, closed


def to_h4(H):
    """Zakladni svicky H4 z H1 (bloky po 4 h od 17:00 NY) se stejnou strukturou jako H1 slovnik."""
    key = H["lt"] // 14400
    st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    en = np.r_[st[1:] - 1, len(key) - 1]
    G4 = dict(H)
    G4.update(o=H["o"][st], h=np.maximum.reduceat(H["h"], st), l=np.minimum.reduceat(H["l"], st), c=H["c"][en],
              t=H["t"][st], lt=H["lt"][st], day=H["day"][st], spr=H["spr"][st], cum_sw=H["cum_sw"][st])
    G4["hend"] = np.zeros(len(st), np.bool_)
    return G4


def prepare(mk, base="H1"):
    H = F.load(mk)
    if base == "H4":
        H = to_h4(H)
    o, h, l, c = H["o"], H["h"], H["l"], H["c"]
    n = len(c)
    hl = ((H["lt"] % 86400) // 3600).astype(np.int64)
    a1 = L.wilder_atr(h, l, c, 14)
    D = F.resample(H, H["day"])
    T4 = F.resample(H, H["lt"] // 14400)
    di, _ = map_closed(D["st"], D["en"], n)  # di = dnesni den; vcera = di-1
    _, c4 = map_closed(T4["st"], T4["en"], n)
    pdh = np.where(di >= 1, D["h"][np.clip(di - 1, 0, None)], np.nan)
    pdl = np.where(di >= 1, D["l"][np.clip(di - 1, 0, None)], np.nan)
    # D1 filtry podle vcerejska
    _, _, trD = F.last_swing(D["h"], D["l"], 2)
    emaD = pd.Series(D["c"]).ewm(span=20, adjust=False).mean().to_numpy()
    nd = len(D["c"])
    biasV = np.zeros(nd, np.int8)
    biasM = np.zeros(nd, np.int8)
    for k in range(2, nd):
        cp, hp, lp, hpp, lpp = D["c"][k - 1], D["h"][k - 1], D["l"][k - 1], D["h"][k - 2], D["l"][k - 2]
        if cp > hpp:
            biasV[k] = 1
        elif hp > hpp and cp < hpp:
            biasV[k] = -1
        elif cp < lpp:
            biasV[k] = -1
        elif lp < lpp and cp > lpp:
            biasV[k] = 1
        if D["c"][k - 1] != D["o"][k - 1]:
            biasM[k] = 1 if D["c"][k - 1] > D["o"][k - 1] else -1
    hi10 = pd.Series(D["h"]).rolling(10).max().shift(1).to_numpy()
    lo10 = pd.Series(D["l"]).rolling(10).min().shift(1).to_numpy()
    dcl = np.clip(di - 1, 0, None)
    f = {}
    f["trendD1"] = np.where(di >= 1, trD[dcl], 0)
    f["emaD1"] = np.where(di >= 1, np.sign(D["c"][dcl] - emaD[dcl]), 0)
    f["biasV"] = biasV[di]
    f["biasM"] = biasM[di]
    mid10 = 0.5 * (hi10[di] + lo10[di])
    f["discount"] = np.where(np.isfinite(mid10), np.where(c < mid10, 1, -1), 0)
    _, _, tr4 = F.last_swing(T4["h"], T4["l"], 2)
    f["trendH4"] = np.where(c4 >= 0, tr4[np.clip(c4, 0, None)], 0)
    f["kz"] = ((hl >= 9) & (hl < 12)) | ((hl >= 15) & (hl < 18))
    # NY open 00:00 = hl 7
    nydo = np.full(n, np.nan)
    cur = np.nan
    for i in range(n):
        if i and H["day"][i] != H["day"][i - 1]:
            cur = np.nan
        if hl[i] == 7 and (i == 0 or hl[i - 1] != 7):
            cur = o[i]
        nydo[i] = cur
    f["nyDO"] = np.where(np.isfinite(nydo), np.where(c < nydo, 1, -1), 0)  # 1 = pod open (pro long)
    # H4 zony (F8, k=2) - aktivni od uzavreni aktivacni H4 svicky do prvniho close za distal
    Z = F.find_zones(T4, 2.0)
    zin = np.zeros(n, np.int8)
    zone_ev = []
    for z in Z:
        i0 = T4["en"][z["act"]] + 1
        i1 = min(T4["en"][min(z["inv"], len(T4["en"]) - 1)], n - 1)
        if i0 >= n:
            continue
        seg = slice(i0, i1 + 1)
        d, E, dist = z["d"], z["prox"], z["dist"]
        inside = (l[seg] <= E) if d == 1 else (h[seg] >= E)
        zin[seg] = np.where(inside, d, zin[seg])
        hit = np.flatnonzero(inside)
        if len(hit):
            t0 = i0 + hit[0]
            for i in range(t0, min(t0 + 7, i1 + 1)):  # potvrzovaci svicka: close zpet za proximal
                if (c[i] - E) * d > 0:
                    zone_ev.append((i, d, dist - d * 0.1 * a1[i]))
                    break
    f["zonaH4"] = zin
    # H1 pivoty
    sh, sl_, _ = F.last_swing(h, l, 3)
    # balance: H4 pivot (N=2) proraz closem, retest do 48 H1 svicek
    sh4, sl4, _ = F.last_swing(T4["h"], T4["l"], 2)
    bal = []
    for b in range(1, len(T4["c"])):
        for d, lvl in ((1, sh4[b]), (-1, sl4[b])):
            if not np.isfinite(lvl):
                continue
            if (T4["c"][b] - lvl) * d > 0 and (T4["c"][b - 1] - lvl) * d <= 0:
                a4 = T4["a"][b]
                if not a4 > 0:
                    continue
                for i in range(T4["en"][b] + 1, min(T4["en"][b] + 49, n)):
                    if (c[i] - (lvl - d * 0.5 * a4)) * d < 0:
                        break
                    touch = l[i] <= lvl if d == 1 else h[i] >= lvl
                    if touch:
                        if (c[i] - lvl) * d > 0:
                            bal.append((i, d, lvl - d * 0.5 * a4))
                        break
    ev = {}
    si, sd, ssl, st = trig_sweeps(h, l, c, H["day"], hl, pdh, pdl, a1)
    ev["sweepPD"] = (si[st == 0], sd[st == 0], ssl[st == 0])
    ev["sweepAsia"] = (si[st == 1], sd[st == 1], ssl[st == 1])
    ev["mss"] = trig_mss(h, l, c, si, sd, a1)
    ev["fvg"] = trig_fvg(o, h, l, c, a1)
    ev["ob"] = trig_ob(o, h, l, c, sh, sl_, a1)
    ev["prurazPivot"] = trig_pivot_break(c, sh, sl_, a1)
    ev["zona"] = tuple(np.array(x) for x in zip(*zone_ev)) if zone_ev else (np.array([]),) * 3
    ev["balance"] = tuple(np.array(x) for x in zip(*bal)) if bal else (np.array([]),) * 3
    return H, a1, f, ev


def simulate_events(H, a1, f, ev, delay=1):
    rows = []
    n = len(H["c"])
    for name, (I, Dd, SL) in ev.items():
        for i, d, sl in zip(I.astype(int), Dd.astype(int), SL.astype(float)):
            i0 = i + delay
            if i0 + 1 >= n or not a1[i] > 0:
                continue
            E0 = H["o"][i0] + (H["spr"][i0] if d == 1 else 0.0)
            risk = (E0 - sl) * d
            if risk < 0.2 * a1[i] or risk > 4 * a1[i] or risk < 3 * H["spr"][i]:
                continue
            row = dict(mk=H["mk"], trig=name, i=i, d=d, t=int(H["t"][i]), risk_atr=risk / a1[i])
            for k in FILT:
                v = f[k][i]
                row[k] = bool(v) if k == "kz" else (int(v) == d)
            sw = H["swl"] if d == 1 else H["sws"]
            for R in RS:
                tp = E0 + d * R * risk
                r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], i0, i0, 1, d, E0, sl, tp, 1.0,
                                np.nan, np.nan, np.full(1, np.nan), 0, min(i0 + HOLD, n - 1), np.nan, H["hend"], 0, 0.0,
                                H["cum_sw"], sw)
                row[f"R{R}"] = r[1] if r[0] else np.nan
                row[f"ex{R}"] = r[3]
            rows.append(row)
    return rows


def main(delay=1, base="H1"):
    rows = []
    for mk in MARKETS:
        H, a1, f, ev = prepare(mk, base)
        rows += simulate_events(H, a1, f, ev, delay)
        print(mk, {k: len(v[0]) for k, v in ev.items()}, flush=True)
    df = pd.DataFrame(rows)
    df.to_pickle(os.path.join(D9, f"f9_udalosti{'' if base == 'H1' else '_' + base}{'' if delay == 1 else '_d' + str(delay)}.pkl"))
    return df


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1, sys.argv[2] if len(sys.argv) > 2 else "H1")
