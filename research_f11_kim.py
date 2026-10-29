"""
F11 - Kimmel v2 podle diagramu entry modelu 1 a pravidel z PDF.
Okno 09:30-12:00 NY. Bias: V (Veselovsky), M (barva vcerejsi svicky) nebo 'pair' (best pair: obchoduje se ten z NQ/ES,
ktery je od 09:30 silnejsi ve smeru biasu M). Setup: sweep pod PDL / pod low M15 zony z predchoziho dne (15m PDA) -> MSS na M5
(close tela za poslednim swing high pred sweepem, pivot N=2) -> vstup trhem na close MSS nebo limit do LTF FVG (M5) ->
SL o 25 % za extrem sweepu -> TP 'range' = high od 09:30 do sweepu (nad range, min 1,5R) nebo 2R. Konec okna +2 h zavrit.
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import research_f8 as F
import research_f10 as X
from research_f11_ves import bias_ves, pivots_last

D11 = os.path.join("research_data", "f11")
MARKETS = ["NAS100mini", "SPX500mini", "US30mini", "GER_30mini"]


def run_market(mk, var, other=None):
    M = X.load1(mk)
    T = X.tfs(M)
    Xb, Q, D = T["M5"], T["M15"], T["D1"]
    bv = bias_ves(D)
    _, bm = X.bias_arrays(D)
    lh, ll = pivots_last(Xb["h"], Xb["l"], 2)
    ZQ = F.find_zones(Q, 1.5)
    # M15 zony z predchoziho dne (15m PDA): aktivovane v predchozim dni
    zday = {}
    for z in ZQ:
        dd = int(Q["day"][z["act"]])
        zday.setdefault(dd, []).append(z)
    out = []
    days = D["day"]
    for k in range(2, len(D["c"])):
        b = int(bv[k] if var["bias"] == "V" else bm[k])
        if var["bias"] == "pair":
            b = int(bm[k])
        if b == 0:
            continue
        i_d0, i_d1 = D["st"][k], D["en"][k]
        xs = np.searchsorted(Xb["st"], i_d0)
        xe = np.searchsorted(Xb["st"], i_d1, side="right") - 1
        win = [j for j in range(xs, xe + 1) if 16.5 <= Xb["hm"][j] < 19]
        if len(win) < 10:
            continue
        if var["bias"] == "pair" and other is not None:
            # silnejsi index ve smeru biasu od 09:30 do 10:00 NY
            t0, t1 = M["t"][Xb["st"][win[0]]], M["t"][Xb["en"][win[5]]]
            r_me = (Xb["c"][win[5]] - Xb["o"][win[0]]) / Xb["o"][win[0]]
            r_ot = other(t0, t1)
            if r_ot is None or (r_me - r_ot) * b <= 0:
                continue
            win = win[6:]
        pdl, pdh = D["l"][k - 1], D["h"][k - 1]
        pools = [pdl if b == 1 else pdh]
        for z in zday.get(int(days[k - 1]), []):
            if z["d"] == b:
                pools.append(min(z["prox"], z["dist"]) if b == 1 else max(z["prox"], z["dist"]))
        atrD = D["a"][k - 1]
        for j in win:
            hit = [q for q in pools if (b == 1 and Xb["l"][j] < q < Xb["h"][j]) or (b == -1 and Xb["h"][j] > q > Xb["l"][j])]
            if not hit:
                continue
            p = lh[j] if b == 1 else ll[j]
            if p < 0:
                break
            lvl = Xb["h"][p] if b == 1 else Xb["l"][p]
            ext = Xb["l"][j] if b == 1 else Xb["h"][j]
            m = -1
            for q in range(j + 1, min(j + 13, win[-1] + 1)):
                ext = min(ext, Xb["l"][q]) if b == 1 else max(ext, Xb["h"][q])
                if (Xb["c"][q] - lvl) * b > 0:
                    m = q
                    break
            if m < 0:
                break
            rng_hi = Xb["h"][win[0]:j + 1].max() if b == 1 else Xb["l"][win[0]:j + 1].min()
            i0 = Xb["en"][m] + 1
            if var["entry"] == "trh":
                E, kind, iv = M["o"][i0], 1, i0
            else:
                fv = None
                for q in range(j + 2, m + 1):
                    if b == 1 and Xb["l"][q] > Xb["h"][q - 2]:
                        fv = (Xb["h"][q - 2], Xb["l"][q])
                    if b == -1 and Xb["h"][q] < Xb["l"][q - 2]:
                        fv = (Xb["h"][q], Xb["l"][q - 2])
                if fv is None:
                    break
                E, kind, iv = (fv[1] if b == 1 else fv[0]), 0, min(i0 + 24, i_d1)
            dist = abs(E - ext)
            SL = E - b * 1.25 * dist
            risk = 1.25 * dist
            if risk <= 0:
                break
            if var["tp"] == "range":
                Rt = (rng_hi - E) * b / risk
                if Rt < 1.5:
                    break
                Rt = min(Rt, 5.0)
            else:
                Rt = 2.0
            TP = E + b * Rt * risk
            iex = min(i_d0 + np.flatnonzero(M["hm"][i_d0:i_d1 + 1] < 21)[-1], i_d1)
            s = X.sim(M, b, E, SL, TP, i0, iv, kind, iex)
            if s:
                out.append(X.rec(M, "KIM", X.vn(var), b, s, Rt, atrD, "den"))
            break
    return out


def make_other(mk):
    M = X.load1(mk)
    t = M["t"]

    def f(t0, t1):
        i0, i1 = np.searchsorted(t, t0), np.searchsorted(t, t1)
        if i1 >= len(t) or i0 >= i1 or abs(int(t[i0]) - int(t0)) > 300:
            return None
        return (M["c"][i1] - M["o"][i0]) / M["o"][i0]
    return f


if __name__ == "__main__":
    rows = []
    pair = {"NAS100mini": "SPX500mini", "SPX500mini": "NAS100mini", "US30mini": "SPX500mini", "GER_30mini": None}
    for mk in MARKETS:
        oth = make_other(pair[mk]) if pair[mk] else None
        for bias in ("V", "M", "pair"):
            if bias == "pair" and oth is None:
                continue
            for entry in ("trh", "fvg"):
                for tp in ("range", "2R"):
                    rows += run_market(mk, dict(bias=bias, entry=entry, tp=tp), oth)
        print(mk, len(rows), flush=True)
    pd.DataFrame(rows).to_pickle(os.path.join(D11, "f11_KIM.pkl"))
