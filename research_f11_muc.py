"""
F11 - Mucka v2. Asie 20:00-00:00 NY s range <= 35 pipu (EURUSD; jinde <= 0,47 ATR D1). Bias = barva vcerejsi D1 svicky
(medvedi -> cil PDL). V jeho oknech (03-05 a 07:30-11 NY) sweep Asia high (short) / low (long) proti... ve smeru biasu
(sweep high a pak short pri medvedim biasu). Structure shift na M5 nebo M1: close za poslednim swingem pred sweepem
(pivot N=2), s momentem (telo >= prumer tel). Vstup trhem / limit FVG (M5) / limit golden pocket 0,618 (M1).
SL primo na high/low sweepu, min 6 pipu (0,08 ATR D1), max 20 pipu (0,27 ATR D1). TP: opacna strana Asie / PDH-PDL. Konec dne.
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import research_f10 as X
from research_f11_ves import pivots_last

D11 = os.path.join("research_data", "f11")
MARKETS = ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "XAUUSD", "NAS100mini"]


def run_market(mk, var, cache={}):
    if mk not in cache:
        cache.clear()
        M = X.load1(mk)
        cache[mk] = (M, X.tfs(M))
    M, T = cache[mk]
    Xb, D = T[var["tf"]], T["D1"]
    _, bm = X.bias_arrays(D)
    lh, ll = pivots_last(Xb["h"], Xb["l"], 2)
    W = 24 if var["tf"] == "M5" else 60
    body = np.abs(Xb["c"] - Xb["o"])
    bavg = pd.Series(body).rolling(20).mean().to_numpy()
    out = []
    for k in range(2, len(D["c"])):
        b = int(bm[k])
        if b == 0:
            continue
        i_d0, i_d1 = D["st"][k], D["en"][k]
        atrD = D["a"][k - 1]
        if not atrD > 0:
            continue
        hm = M["hm"][i_d0:i_d1 + 1]
        asia = (hm >= 3) & (hm < 7)
        if asia.sum() < 60:
            continue
        aH, aL = M["h"][i_d0:i_d1 + 1][asia].max(), M["l"][i_d0:i_d1 + 1][asia].min()
        if aH - aL > (35 * M["pip"] if mk == "EURUSD" else 0.47 * atrD):
            continue
        mn = 6 * M["pip"] if mk == "EURUSD" else 0.08 * atrD
        mx = 20 * M["pip"] if mk == "EURUSD" else 0.27 * atrD
        xs = np.searchsorted(Xb["st"], i_d0)
        xe = np.searchsorted(Xb["st"], i_d1, side="right") - 1
        # sweep proti smeru obchodu: pri bias -1 sweep Asia high, pri +1 sweep Asia low
        lvl_sw = aL if b == 1 else aH
        swept_before = False
        for j in range(xs + 3, xe):
            hmj = Xb["hm"][j]
            if hmj >= 7 and ((b == 1 and Xb["l"][j] < lvl_sw) or (b == -1 and Xb["h"][j] > lvl_sw)):
                if not ((10 <= hmj < 12) or (14.5 <= hmj < 18)) or swept_before:
                    swept_before = True
                    break
                swept_before = True
                p = lh[j] if b == 1 else ll[j]
                if p < 0:
                    break
                lvl = Xb["h"][p] if b == 1 else Xb["l"][p]
                ext = Xb["l"][j] if b == 1 else Xb["h"][j]
                m = -1
                for q in range(j + 1, min(j + W + 1, xe)):
                    ext = min(ext, Xb["l"][q]) if b == 1 else max(ext, Xb["h"][q])
                    if (Xb["c"][q] - lvl) * b > 0:
                        m = q
                        break
                if m < 0 or not body[m] >= bavg[m]:
                    break
                i0 = Xb["en"][m] + 1
                if i0 >= len(M["o"]) - 1:
                    break
                legE = Xb["h"][j:m + 1].max() if b == 1 else Xb["l"][j:m + 1].min()
                if var["entry"] == "trh":
                    E, kind, iv = M["o"][i0], 1, i0
                elif var["entry"] == "gp":
                    E, kind, iv = legE - b * 0.618 * abs(legE - ext), 0, min(i0 + 120, i_d1)
                else:
                    fv = None
                    for q in range(j + 2, m + 1):
                        if b == 1 and Xb["l"][q] > Xb["h"][q - 2]:
                            fv = (Xb["h"][q - 2], Xb["l"][q])
                        if b == -1 and Xb["h"][q] < Xb["l"][q - 2]:
                            fv = (Xb["h"][q], Xb["l"][q - 2])
                    if fv is None:
                        break
                    E, kind, iv = (fv[1] if b == 1 else fv[0]) + b * M["spr"][i0], 0, min(i0 + 120, i_d1)
                SL = ext
                risk = (E - SL) * b
                if risk < mn:
                    SL, risk = E - b * mn, mn
                if risk > mx:
                    break
                tgt = (aH if b == 1 else aL) if var["tp"] == "asie" else (D["h"][k - 1] if b == 1 else D["l"][k - 1])
                Rt = (tgt - E) * b / risk
                if Rt < 1.0:
                    break
                s = X.sim(M, b, E, SL, tgt, i0, iv, kind, i_d1)
                if s:
                    out.append(X.rec(M, "MUC", X.vn(var), b, s, Rt, atrD, "den"))
                break
    return out


if __name__ == "__main__":
    rows = []
    for mk in MARKETS:
        for tf in ("M5", "M1"):
            for entry in ("trh", "fvg", "gp"):
                for tp in ("asie", "pd"):
                    rows += run_market(mk, dict(tf=tf, entry=entry, tp=tp))
        print(mk, len(rows), flush=True)
    pd.DataFrame(rows).to_pickle(os.path.join(D11, "f11_MUC.pkl"))
