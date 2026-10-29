"""
F11 - Patek v2 podle grafu entry modelu: H4 trend (struktura) -> 1) odmitnuti: cena v poslednich 24 M5 svickach dosahla
H4 rezistence/supportu (aktivni H4 zona proti smeru pullbacku, nebo posledni H4 swing) 2) na M5 vznikne nizsi high (short)
/ vyssi low (long) 3) close za poslednim M5 pivotem = vstup trhem. SL nad nizsi high (pod vyssi low). TP: 2R / dalsi pivot
low (predchozi M5/M15 low ve smeru, min 1,5R) / H4 extrem vlevo. Session 03-06 a 09:30-12 NY, konec dne zavrit.
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
MARKETS = ["NAS100mini", "SPX500mini", "US30mini", "GER_30mini", "GBPUSD", "XAUUSD"]


def run_market(mk, var):
    M = X.load1(mk)
    T = X.tfs(M)
    Xb, H4, D = T["M5"], T["H4"], T["D1"]
    n = len(M["c"])
    _, _, tr4 = F.last_swing(H4["h"], H4["l"], 2)
    sh4, sl4, _ = F.last_swing(H4["h"], H4["l"], 3)
    c4 = X.closed_map(H4, n)
    Z4 = F.find_zones(H4, 1.5)
    # pro kazdou H1.. zjednodusene: seznam aktivnich H4 zon jako intervaly (i_act, i_inv, d, lo, hi)
    zi = [(H4["en"][z["act"]], H4["en"][min(z["inv"], len(H4["en"]) - 1)], z["d"], *sorted((z["prox"], z["dist"]))) for z in Z4]
    ph, pl = L.pivots(Xb["h"], Xb["l"], 3)
    dst, den = X.day_end_idx(M)
    dmap = np.searchsorted(dst, np.arange(n), side="right") - 1
    out = []
    piv_h, piv_l = [], []  # (index, cena)
    busy = -1
    for j in range(4, len(Xb["c"])):
        p = j - 3
        if ph[p]:
            piv_h.append((p, Xb["h"][p]))
        if pl[p]:
            piv_l.append((p, Xb["l"][p]))
        hm = Xb["hm"][j]
        if not ((10 <= hm < 13) or (16.5 <= hm < 19)) or len(piv_h) < 2 or len(piv_l) < 2:
            continue
        i_end = Xb["en"][j]
        if i_end <= busy:
            continue
        k4 = c4[i_end]
        if k4 < 2:
            continue
        b = int(tr4[k4])
        if b == 0:
            continue
        if b == -1:
            (ip1, h1), (ip0, h0) = piv_h[-1], piv_h[-2]
            lastL = piv_l[-1][1]
            if not (h1 < h0 and Xb["c"][j] < lastL and Xb["c"][j - 1] >= lastL and ip1 > piv_l[-1][0] - 50):
                continue
            ext, SL = h0, h1 + 10 * M["tick"]
        else:
            (ip1, l1), (ip0, l0) = piv_l[-1], piv_l[-2]
            lastH = piv_h[-1][1]
            if not (l1 > l0 and Xb["c"][j] > lastH and Xb["c"][j - 1] <= lastH and ip1 > piv_h[-1][0] - 50):
                continue
            ext, SL = l0, l1 - 10 * M["tick"]
        # 1) odmitnuti na H4 urovni: extrem pullbacku (h0 / l0) v blizkosti H4 zony proti smeru nebo H4 swingu
        if var["rej"]:
            a4 = H4["a"][k4]
            lvl4 = sh4[k4] if b == -1 else sl4[k4]
            near = np.isfinite(lvl4) and abs(ext - lvl4) <= 0.3 * a4
            if not near:
                for ia, iv, zd, lo, hi in zi:
                    if zd == -b and ia < i_end <= iv and lo - 0.1 * a4 <= ext <= hi + 0.1 * a4:
                        near = True
                        break
            if not near:
                continue
        i0 = i_end + 1
        if i0 >= n:
            break
        E0 = M["o"][i0]
        risk = (E0 - SL) * b
        if risk <= 0:
            continue
        if var["tp"] == "2R":
            Rt = 2.0
        elif var["tp"] == "pivot":
            cands = [pr for _, pr in (piv_l if b == -1 else piv_h)[-12:] if (pr - E0) * b > 1.5 * risk]
            if not cands:
                continue
            Rt = min(((pr - E0) * b / risk for pr in cands))
            Rt = min(Rt, 5.0)
        else:
            look = slice(max(0, k4 - 30), k4 + 1)
            cand = H4["h"][look].max() if b == 1 else H4["l"][look].min()
            Rt = (cand - E0) * b / risk
            if Rt < 1.5:
                continue
            Rt = min(Rt, 5.0)
        TP = E0 + b * Rt * risk
        atrD = D["a"][max(0, int(np.searchsorted(D["st"], i0, side="right")) - 2)]
        s = X.sim(M, b, E0, SL, TP, i0, i0, 1, den[dmap[i0]])
        if s:
            out.append(X.rec(M, "PAT", X.vn(var), b, s, Rt, atrD, "den"))
            busy = s["ex"]
    return out


if __name__ == "__main__":
    rows = []
    for mk in MARKETS:
        for rej in (True, False):
            for tp in ("2R", "pivot", "H4"):
                rows += run_market(mk, dict(rej=rej, tp=tp))
        print(mk, len(rows), flush=True)
    pd.DataFrame(rows).to_pickle(os.path.join(D11, "f11_PAT.pkl"))
