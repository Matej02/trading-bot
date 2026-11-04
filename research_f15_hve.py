"""
F15 - Hvezda: PDF + obrazky jako zdroj, B4 jako dodatek, COT z CFTC (F15_PLAN.md). H1 data MT5 2009-2026, 13 trhu s COT.
Strategie `tyden`: W1 zona (vstup na D1), `den`: D1 zona (vstup na H4). Zona FM (research_f8.find_zones: pohyb ven >= 1,5 ATR,
base male svicky max 3 / 6, proximal = tela base, distal = knot, aktivace po BOS), jen ve smeru trendu (2 vyssi high + low).
Varianty:
- dvw: zona nizsiho TF uvnitr aktivni zony vyssiho TF ("denni level v tydennim");
- lnl: level nad levelem (SL pod 2. zonou);
- entry: limit na proximal / svickova formace (hammer, engulfing);
- cot: 0 / smer (commercials index > 50 ve smeru) / ext (commercials extrem >= 80 / <= 20 v poslednich 4 reportech).
SL pod distal, TP nejblizsi protejsi zona (2-6 R), BE pri 1R, max drzeni 30 / 10 dni.
Spusteni: py research_f15_hve.py -> research_data/f15/f15.pkl (F15_NOCOST=1 -> _nc)
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f8 as F
import research_f15_cot as C

D15 = os.path.join("research_data", "f15")
os.makedirs(D15, exist_ok=True)
OOS = pd.Timestamp("2022-01-01", tz="UTC").value // 10**9
MARKETS = list(C.CODES)
NOCOST = os.environ.get("F15_NOCOST") == "1"
SUF = "_nc" if NOCOST else ""
_C = {}


def prep(mk):
    if mk in _C:
        return _C[mk]
    H = F.load(mk)
    if NOCOST:
        H["spr"] = np.zeros_like(H["spr"])
        H["swl"] = H["sws"] = 0.0
    T = F.tfs(H)
    Z = {}
    for tf in ("W1", "D1", "H4"):
        for bm in (3, 6):
            Z[(tf, bm)] = F.find_zones(T[tf], 1.5, bmax=bm)
    _C.clear()
    _C[mk] = (H, T, Z, C.series(mk))
    return _C[mk]


def zt(T, z):
    """(aktivace, zneplatneni) zony jako H1 indexy."""
    return T["en"][z["act"]], T["en"][min(z["inv"], len(T["en"]) - 1)]


def candle_ok(T, k, d):
    o, h, l, c = T["o"], T["h"], T["l"], T["c"]
    body = abs(c[k] - o[k])
    lw, uw = min(o[k], c[k]) - l[k], h[k] - max(o[k], c[k])
    if d == 1:
        return (body > 0 and lw >= 2 * body and uw <= body) or (c[k] > o[k] and o[k - 1] > c[k - 1] and c[k] >= o[k - 1] and o[k] <= c[k - 1])
    return (body > 0 and uw >= 2 * body and lw <= body) or (c[k] < o[k] and o[k - 1] < c[k - 1] and c[k] <= o[k - 1] and o[k] >= c[k - 1])


DBG = {}


def _c(k):
    DBG[k] = DBG.get(k, 0) + 1


def run_market(mk, var):
    H, T, Z, S = prep(mk)
    hi_tf, lo_tf = ("W1", "D1") if var["tf"] == "tyden" else ("D1", "H4")
    Th, Tl = T[hi_tf], T[lo_tf]
    hold = (30 if var["tf"] == "tyden" else 10) * 24
    ZH, ZL = Z[(hi_tf, var["base"])], Z[(lo_tf, var["base"])]
    n = len(H["c"])
    # kandidati: (zona pro vstup, TF zony vstupu, zony pro TP/lnl, trend ok)
    cands = []
    if var["dvw"]:
        for zl in ZL:
            a_l, i_l = zt(Tl, zl)
            lo1, hi1 = sorted((zl["prox"], zl["dist"]))
            for zh in ZH:
                if zh["d"] != zl["d"] or zh["tr"] != zh["d"]:
                    continue
                a_h, i_h = zt(Th, zh)
                lo2, hi2 = sorted((zh["prox"], zh["dist"]))
                if a_h <= a_l < i_h and lo1 <= hi2 and hi1 >= lo2:
                    cands.append((zl, Tl, ZL))
                    break
    else:
        cands = [(z, Th, ZH) for z in ZH if z["tr"] == z["d"]]
    out = []
    busy = -1
    for z, Tz, Zs in sorted(cands, key=lambda x: zt(x[1], x[0])[0]):
        d = z["d"]
        a0, i_inv = zt(Tz, z)
        # prvni dotek proximal na TF vstupu (Tl), do zneplatneni zony a nejdyl 120 svicek
        k0 = int(np.searchsorted(Tl["st"], a0 + 1))
        t0 = -1
        for k in range(k0, min(len(Tl["c"]), k0 + 120)):
            if Tl["st"][k] > i_inv:
                break
            if (d == 1 and Tl["l"][k] <= z["prox"]) or (d == -1 and Tl["h"][k] >= z["prox"]):
                t0 = k
                break
        if t0 < 0 or (Tl["st"][t0] <= busy and not var.get("parity")):
            _c("bez doteku")
            continue
        _c("dotek")
        i_touch = Tl["st"][t0]
        hgt = abs(z["prox"] - z["dist"])
        SL = z["dist"] - d * (0.2 * hgt if var.get("sl20") else 0.05 * z["atr"])
        if var["lnl"]:
            z2s = [y for y in Zs if y is not z and y["d"] == d and zt(Tz, y)[0] <= i_touch < zt(Tz, y)[1]
                   and (z["dist"] - y["prox"]) * d >= 0 and (z["dist"] - y["prox"]) * d <= 2 * z["atr"]]
            if not z2s:
                continue
            z2 = min(z2s, key=lambda y: abs(z["dist"] - y["prox"]))
            SL = z2["dist"] - d * 0.05 * z["atr"]
        # TP: nejblizsi protejsi zona vyssiho TF aktivni pri doteku
        # tyden: nejblizsi supply/demand na W1 nebo D1 ("nejblizsi supply zona nebo klicova uroven"), den: D1
        pool = [(y, Th) for y in ZH] + ([(y, Tl) for y in ZL] if var["tf"] == "tyden" else [])
        opp = [y for y, Ty in pool if y["d"] == -d and zt(Ty, y)[0] <= i_touch < zt(Ty, y)[1] and (y["prox"] - z["prox"]) * d > 0]
        if not opp:
            _c("bez protizony")
            continue
        yb = min(opp, key=lambda y: abs(y["prox"] - z["prox"]))
        if var.get("lok"):
            a_, b_ = (z["dist"], yb["dist"]) if d == 1 else (yb["dist"], z["dist"])
            third = a_ + (b_ - a_) / 3 if d == 1 else b_ - (b_ - a_) / 3
            if (d == 1 and z["prox"] > third) or (d == -1 and z["prox"] < third):
                continue
        # COT filtr k casu doteku
        if var["cot"] != "0":
            k = C.at(S, int(H["t"][i_touch]))
            if k < 3:
                continue
            last = S.comm.to_numpy()[k - 3:k + 1]
            if np.isnan(last[-1]):
                continue
            if var["cot"] == "smer" and not ((d == 1 and last[-1] > 50) or (d == -1 and last[-1] < 50)):
                continue
            if var["cot"] == "ext" and not ((d == 1 and np.nanmax(last) >= 80) or (d == -1 and np.nanmin(last) <= 20)):
                continue
        if var.get("parity"):                     # kontrola shody s TS: prvni H1 svicka v H4 bloku doteku, ktera proximal zasahne
            risk = (z["prox"] - SL) * d
            Rt = (yb["prox"] - z["prox"]) * d / risk if risk > 0 else 0
            if risk > 0 and Rt >= 2:
                for i in range(i_touch, Tl["en"][t0] + 1):
                    if (d == 1 and H["l"][i] <= z["prox"]) or (d == -1 and H["h"][i] >= z["prox"]):
                        out.append([int(H["t"][i]), d, float(SL), float(z["prox"] + d * min(Rt, 6.0) * risk)])
                        break
            continue
        if var["entry"] == "limit":
            E, i0, iv, kind = z["prox"], i_touch, Tl["en"][t0], 0
        else:
            ck = -1
            for k in range(t0, min(t0 + 3, len(Tl["c"]) - 1)):
                if (Tl["c"][k] - z["dist"]) * d < 0:
                    break
                if candle_ok(Tl, k, d):
                    ck = k
                    break
            if ck < 0:
                continue
            i0 = Tl["en"][ck] + 1
            if i0 >= n - 1:
                continue
            E, iv, kind = H["o"][i0] + (H["spr"][i0] if d == 1 else 0), i0, 1
        risk = (E - SL) * d
        if risk <= 0:
            continue
        Rt = (yb["prox"] - E) * d / risk
        if Rt < 2:
            _c("RR<2")
            continue
        Rt = min(Rt, 6.0)
        TP = E + d * Rt * risk
        sw = H["swl"] if d == 1 else H["sws"]
        r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], i0, min(iv, n - 2), kind, d, E, SL, E + d * risk, 1e-9,
                        TP, 1 - 1e-9, np.full(1, np.nan), 0, min(i0 + hold, n - 1), np.nan, H["hend"], 0, 0.0, H["cum_sw"], sw)
        if not r[0]:
            _c("sim nevyplnil")
            continue
        out.append(dict(mk=mk, var=" ".join(f"{a}={b}" for a, b in var.items()), d=d, t=int(H["t"][r[2]]), fi=int(r[2]),
                        ex=int(r[3]), R=r[1], Rt=Rt, sl_dist=risk, tp_dist=Rt * risk, hold=hold))
        busy = r[3]
    return out


GRID = [dict(tf=tf, base=b, dvw=dv, lnl=ln, entry=e, cot=c) for tf in ("tyden", "den") for b in (3, 6) for dv in (0, 1)
        for ln in (0, 1) for e in ("limit", "svicka") for c in ("0", "smer", "ext")]

if __name__ == "__main__":
    rows = []
    for mk in MARKETS:
        for var in GRID:
            rows += run_market(mk, var)
        print(mk, len(rows), flush=True)
    df = pd.DataFrame(rows)
    df.to_pickle(os.path.join(D15, f"f15{SUF}.pkl"))
