"""
F11 - Hakimi v2 (opraveny SL). Trend H4 (struktura) -> posledni noha pivot->pivot -> pullback do Fibo 0,5-0,75,
kde se kryje H4 nebo M15 S/D zona stejneho smeru nebo H4 FVG z nohy -> vstup: limit na golden pocket 0,618
(nebo proximal zony, pokud lezi v pasmu a je bliz) / varianta: M15 svicka po doteku zavre zpet nad 0,618 (vstup trhem)
-> SL pod zonou, nejmene pod Fibo 0,75 (- 0,1 ATR H4) -> TP high nohy, RR 2,5-8, bez BE, max 20 dni.
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

D11 = os.path.join("research_data", "f11")
MARKETS = ["XAUUSD", "XAGUSD", "NAS100mini", "SPX500mini", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]


def active(Z, T, i):
    """Zony aktivni v M1 indexu i (aktivovane pred i, nezrusene)."""
    out = []
    for z in Z:
        a = T["en"][z["act"]]
        v = T["en"][min(z["inv"], len(T["en"]) - 1)]
        if a < i <= v:
            out.append(z)
    return out


def run_market(mk, var, info=False):
    M = X.load1(mk)
    T = X.tfs(M)
    H4, Q, D = T["H4"], T["M15"], T["D1"]
    h, l = H4["h"], H4["l"]
    ph, pl = L.pivots(h, l, 3)
    _, _, tr = F.last_swing(h, l, 2)
    Z4 = F.find_zones(H4, 1.5)
    ZQ = F.find_zones(Q, 1.5)
    n = len(M["c"])
    out = []
    lastL = lastH = np.nan
    iL = iH = -1
    done = set()
    busy = -1
    for k in range(10, len(h) - 1):
        p = k - 3
        if pl[p]:
            lastL, iL = l[p], p
        if ph[p]:
            lastH, iH = h[p], p
        b = int(tr[k])
        if b == 0 or iL < 0 or iH < 0:
            continue
        if b == 1 and iH > iL:
            start, end, i_end_piv = lastL, lastH, iH
        elif b == -1 and iL > iH:
            start, end, i_end_piv = lastH, lastL, iL
        else:
            continue
        if (b, i_end_piv) in done:
            continue
        done.add((b, i_end_piv))
        leg = abs(end - start)
        a4 = H4["a"][k]
        if not leg > 0 or not a4 > 0 or leg < 1.5 * a4:
            continue
        fib = lambda x: end - b * x * leg
        f50, f618, f75 = fib(0.5), fib(0.618), fib(0.75)
        band_lo, band_hi = sorted((f50, f75))
        i_now = H4["en"][k]
        conf, zdist, zprox, src = False, np.nan, np.nan, ""
        for Zs, T_, nm in ((Z4, H4, "H4"), (ZQ, Q, "M15")):
            for z in active(Zs, T_, i_now):
                if z["d"] != b:
                    continue
                a_, b_ = sorted((z["prox"], z["dist"]))
                if a_ <= band_hi and b_ >= band_lo:
                    conf, zdist, zprox, src = True, z["dist"], z["prox"], nm
                    break
            if conf:
                break
        if not conf:
            s_leg = iL if b == 1 else iH
            for q in range(s_leg + 2, i_end_piv + 1):
                g0, g1 = (h[q - 2], l[q]) if b == 1 else (h[q], l[q - 2])
                if g1 > g0 and g0 <= band_hi and g1 >= band_lo:
                    conf, zdist, zprox, src = True, (g0 if b == 1 else g1), (g1 if b == 1 else g0), "FVG"
                    break
        if not conf:
            continue
        # vstup: golden pocket, nebo proximal zony, pokud je v pasmu a bliz cene
        E = f618
        if band_lo <= zprox <= band_hi and (zprox - f618) * b > 0:
            E = zprox
        SL = min(zdist, f75) - 0.1 * a4 if b == 1 else max(zdist, f75) + 0.1 * a4
        risk = (E - SL) * b
        if risk <= 0:
            continue
        Rt = (end - E) * b / risk
        if not (2.5 <= Rt <= 8):
            continue
        i_last = H4["en"][min(k + 30, len(h) - 1)]
        if i_now + 1 <= busy:
            continue
        fi = X.m1_first(M, i_now + 1, i_last, cond_low=E if b == 1 else None, cond_high=E if b == -1 else None)
        if fi < 0:
            continue
        seg = slice(i_now + 1, fi)
        if fi > i_now + 1 and ((b == 1 and M["h"][seg].max() >= end) or (b == -1 and M["l"][seg].min() <= end)):
            continue  # noha pokracovala - novy swing
        kd = max(int(np.searchsorted(D["st"], fi, side="right")) - 2, 0)
        if var["entry"] == "limit":
            s = X.sim(M, b, E, SL, end, fi, fi, 0, fi + 20 * 1440)
        else:
            # M15 potvrzeni: po doteku do 8 M15 svicek close zpet za E, SL nedotcen
            q0 = int(np.searchsorted(Q["st"], fi, side="right")) - 1
            qc = -1
            for q in range(q0, min(q0 + 8, len(Q["c"]) - 1)):
                if (b == 1 and Q["l"][q] <= SL) or (b == -1 and Q["h"][q] >= SL):
                    break
                if (Q["c"][q] - E) * b > 0:
                    qc = q
                    break
            if qc < 0:
                continue
            i0 = Q["en"][qc] + 1
            E0 = M["o"][i0]
            rk = (E0 - SL) * b
            if rk <= 0 or (end - E0) * b < 2 * rk:
                continue
            s = X.sim(M, b, E0, SL, end, i0, i0, 1, i0 + 20 * 1440)
        if s:
            r = X.rec(M, "HAK", X.vn(var), b, s, Rt, D["a"][kd], "20d")
            r["src"] = src
            out.append(r)
            busy = s["ex"]
    return out


if __name__ == "__main__":
    rows = []
    for mk in MARKETS:
        for v in (dict(entry="limit"), dict(entry="m15")):
            rows += run_market(mk, v)
        print(mk, len(rows), flush=True)
    pd.DataFrame(rows).to_pickle(os.path.join(D11, "f11_HAK.pkl"))
