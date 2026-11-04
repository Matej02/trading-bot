"""
F16 - Hakimi: PDF + obrazky jako zdroj, B5 jako dodatek (F16_PLAN.md). M1 data MT5, simulace na M1 s naklady.
Trend H4 -> vlny ZigZagem na 15m (zavirani, otocka 2 ATR 15m): vlna 1 = noha ve smeru H4 s BOS, vlna 2 nesmi za zacatek vlny 1
(varianta vlna 4) -> zona vstupu = Fibo vlny 0,618-0,75 (+ 15m S/D zona / FVG) -> limit nebo potvrzeni zavrenim nad 0,618 ->
SL pod zonou/0,75 nebo pod zacatkem vlny -> TP high vlny 1 (LOC) nebo extenze 1,618; RR >= 2,5, bez BE, konec dne 22:00.
Spusteni: py research_f16_hak.py [trh ...] -> research_data/f16/f16_<trh>.pkl (F10_NOCOST=1 -> _nc)
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

D16 = os.path.join("research_data", "f16")
os.makedirs(D16, exist_ok=True)
MAIN = ["XAUUSD", "XAGUSD"]
OTHER = ["EURUSD", "GBPUSD", "NAS100mini"]
KZZ = 2.0
_C = {}


def zigzag(c, a, k):
    """Potvrzene swingy na zaviracich cenach: list (index swingu, index potvrzeni, typ +1 high / -1 low)."""
    out = []
    d, ext, ei = 0, c[0], 0
    for i in range(1, len(c)):
        if not a[i] > 0:
            continue
        if d >= 0:
            if c[i] > ext:
                ext, ei = c[i], i
            if c[i] < ext - k * a[i]:
                out.append((ei, i, 1))
                d, ext, ei = -1, c[i], i
                continue
        if d <= 0:
            if c[i] < ext:
                ext, ei = c[i], i
            if c[i] > ext + k * a[i]:
                out.append((ei, i, -1))
                d, ext, ei = 1, c[i], i
    return out


def prep(mk):
    if mk in _C:
        return _C[mk]
    M = X.load1(mk)
    T = X.tfs(M)
    cz, czday = F12.prague_hours(M["t"])
    M15, H4 = T["M15"], T["H4"]
    _, _, tr4 = F.last_swing(H4["h"], H4["l"], 2)
    zz = zigzag(M15["c"], M15["a"], KZZ)
    Z = F.find_zones(M15, 1.5)
    P = dict(M=M, T=T, cz=cz, czday=czday, tr4=tr4, c4=X.closed_map(H4, len(M["c"])), zz=zz, Z=Z, news=X.news_days())
    _C.clear()
    _C[mk] = P
    return P


def wave_price(X15, i, typ):
    """Uroven swingu = knot svicky swingu (+-1 svicka)."""
    s = slice(max(0, i - 1), i + 2)
    return X15["h"][s].max() if typ == 1 else X15["l"][s].min()


def run_market(mk, var):
    P = prep(mk)
    M, T, cz, czday = P["M"], P["T"], P["cz"], P["czday"]
    X15 = T["M15"]
    zz = P["zz"]
    n = len(M["c"])
    out = []
    busy = -1
    for q in range(3, len(zz)):
        # konec vlny (1 nebo 3) = posledni potvrzeny swing ve smeru d; zacatek = predchozi swing
        i_end, conf, typ = zz[q]
        d = typ                                    # swing high (+1) ukoncuje vzhuru vlnu -> long pullback
        i_st = zz[q - 1][0]
        p_end, p_st = wave_price(X15, i_end, typ), wave_price(X15, i_st, -typ)
        prev_ext = wave_price(X15, zz[q - 2][0], typ)
        i_conf = int(X15["en"][conf])
        k4 = int(P["c4"][i_conf])
        if k4 < 2 or P["tr4"][k4] != d:
            continue
        if (p_end - prev_ext) * d <= 0:            # vlna ve smeru s BOS (prorazila predchozi swing)
            continue
        if var["vlna"] == 4:
            # predchozi noha ve smeru (vlna 1) musi byt kratsi a pullback (vlna 4) nesmi do vlny 1
            if q < 5:
                continue
            w1_st, w1_end = wave_price(X15, zz[q - 3][0], -typ), wave_price(X15, zz[q - 2][0], typ)
            if abs(p_end - p_st) <= abs(w1_end - w1_st):
                continue
            floor = w1_end
        else:
            floor = p_st
        leg = abs(p_end - p_st)
        f618, f75 = p_end - d * 0.618 * leg, p_end - d * 0.75 * leg
        top, bot = (f618, f75) if d == 1 else (f75, f618)   # pasmo [bot, top]
        if var["konf"] == "zona":
            zs = [z for z in P["Z"] if z["d"] == d and z["act"] <= conf and z["inv"] > conf and
                  min(z["prox"], z["dist"]) <= top and max(z["prox"], z["dist"]) >= bot]
            if not zs:
                continue
            z = max(zs, key=lambda z: z["act"])
            zl, zh = min(z["prox"], z["dist"]), max(z["prox"], z["dist"])
            top, bot = min(top, zh), max(bot, zl)
            if top <= bot:
                continue
        elif var["konf"] == "fvg":
            fv = None
            for r in range(min(i_st, i_end) + 2, max(i_st, i_end) + 1):
                if d == 1 and X15["l"][r] > X15["h"][r - 2]:
                    g = (X15["h"][r - 2], X15["l"][r])
                elif d == -1 and X15["h"][r] < X15["l"][r - 2]:
                    g = (X15["h"][r], X15["l"][r - 2])
                else:
                    continue
                if g[0] <= top and g[1] >= bot:
                    fv = g
            if fv is None:
                continue
            top, bot = min(top, fv[1]), max(bot, fv[0])
            if top <= bot:
                continue
        E_lim = top if d == 1 else bot
        a15 = X15["a"][conf]
        SL = (min(bot, f75) - 0.1 * a15) if d == 1 else (max(top, f75) + 0.1 * a15)
        if var["sl"] == "vlna":
            SL = floor - d * 0.1 * a15
        TPx = p_end if var["tp"] == "loc" else p_st + d * 1.618 * leg
        # hledani vstupu po potvrzeni swingu, do konce dne a dokud cena neprojde za floor nebo cil
        i0 = i_conf + 1
        if (i0 <= busy and not var.get("parity")) or i0 >= n - 2:
            continue
        day = czday[i0]
        if (M["t"][i0] // 86400) in P["news"] and not var.get("parity"):
            continue
        i_x = i0
        while i_x + 1 < n and czday[i_x + 1] == day and cz[i_x + 1] < 22.0:
            i_x += 1
        if i_x - i0 < 30:
            continue
        if var["entry"] == "limit":
            E, kind, iv, fill0 = E_lim, 0, i_x, i0
        else:
            # dotek pasma a 15m zavreni zpet za 0,618
            k0 = int(np.searchsorted(X15["st"], i0))
            k1 = int(np.searchsorted(X15["st"], i_x))
            touched, ck = False, -1
            for k in range(k0, k1):
                if (d == 1 and X15["l"][k] <= SL) or (d == -1 and X15["h"][k] >= SL):
                    break
                if (d == 1 and X15["h"][k] >= TPx) or (d == -1 and X15["l"][k] <= TPx):
                    break
                if (d == 1 and X15["l"][k] <= top) or (d == -1 and X15["h"][k] >= bot):
                    touched = True
                if touched and (X15["c"][k] - f618) * d > 0 and (X15["c"][k] - X15["o"][k]) * d > 0:
                    ck = k
                    break
            if ck < 0:
                continue
            fill0 = int(X15["en"][ck]) + 1
            if fill0 >= i_x:
                continue
            if var.get("parity"):                 # kontrola shody s TS: signal na svicce ck (vstup = jeji close), bez stavu
                Ec = X15["c"][ck]
                rk = (Ec - SL) * d
                if rk > 0 and (TPx - Ec) * d / rk >= 2.5:
                    out.append([int(M["t"][int(X15["st"][ck])]), d, float(SL), float(Ec + d * min((TPx - Ec) * d / rk, 8.0) * rk)])
                continue
            E, kind, iv = M["o"][fill0] + (M["spr"][fill0] if d == 1 else 0), 1, fill0
        risk = (E - SL) * d
        if risk <= 0 or risk < 3 * M["spr"][i0]:
            continue
        Rt = (TPx - E) * d / risk
        if Rt < 2.5:
            continue
        Rt = min(Rt, 8.0)
        TP = E + d * Rt * risk
        s = X.sim(M, d, E, SL, TP, fill0, iv, kind, i_x)
        if not s:
            continue
        atrD = T["D1"]["a"][max(0, int(np.searchsorted(T["D1"]["st"], fill0, side="right")) - 2)]
        r = X.rec(M, "F16", X.vn(var), d, s, Rt, atrD, "den")
        r.update(sl_dist=risk, tp_dist=Rt * risk, cz=float(cz[s["fi"]]))
        out.append(r)
        busy = s["ex"]
    return out


GRID = [dict(vlna=w, konf=k, entry=e, sl=s, tp=t) for w in (2, 4) for k in ("fibo", "zona", "fvg") for e in ("limit", "potvrz")
        for s in ("zona", "vlna") for t in ("loc", "ext")]

if __name__ == "__main__":
    for mk in sys.argv[1:] or MAIN + OTHER:
        rows = []
        for var in GRID:
            rows += run_market(mk, var)
        pd.DataFrame(rows).to_pickle(os.path.join(D16, f"f16_{mk}{X.SUF}.pkl"))
        print(mk, len(rows), flush=True)
