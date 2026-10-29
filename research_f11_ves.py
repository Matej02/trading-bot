"""
F11 - Veselovsky v plne verzi (podle PDF i grafu), s ulozenim detailu obchodu a grafy ukazek.
Daily bias (jeho pravidla, range = neobchodovat) -> Asie 20-02 NY -> v killzone (Londyn 02-05:30, NY 07-11 NY)
sweep likvidity (Asia low/high, PDL/PDH nebo lokalni M15 swing) pod/nad NY open -> MSS na M5/M1: close za POSLEDNIM
swing high/low pred sweepem (pivot N=2) s displacementem (FVG v noze) -> limit do zony: OB 50 % (posledni opacna svicka
pred impulzem), prvni FVG nebo 0,382 / golden pocket -> SL za extrem sweepu +2 pipy -> TP1 opacna strana Asie (50 %, BE),
TP2 = PDH/PDL. Max 2 SL denne. Bez FOMC/NFP/CPI. Konec dne zavrit.
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f10 as X

D11 = os.path.join("research_data", "f11")
os.makedirs(D11, exist_ok=True)
MARKETS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "XAUUSD"]
KZ = ((9.0, 12.5), (14.0, 18.0))  # hm (hodiny od 17:00 NY): Londyn 02:00-05:30, NY 07:00-11:00


def pivots_last(h, l, N):
    """Pro kazdou svicku index posledniho POTVRZENEHO pivot high/low (potvrzeni N svicek po pivotu)."""
    ph, pl = L.pivots(h, l, N)
    n = len(h)
    lh = np.full(n, -1)
    ll = np.full(n, -1)
    a = b = -1
    for i in range(n):
        p = i - N
        if p >= 0:
            if ph[p]:
                a = p
            if pl[p]:
                b = p
        lh[i], ll[i] = a, b
    return lh, ll


def bias_ves(D):
    n = len(D["c"])
    bv = np.zeros(n, np.int8)
    for k in range(2, n):
        cp, hp, lp, hpp, lpp = D["c"][k - 1], D["h"][k - 1], D["l"][k - 1], D["h"][k - 2], D["l"][k - 2]
        if cp > hpp:
            bv[k] = 1
        elif hp > hpp and cp < hpp:
            bv[k] = -1
        elif cp < lpp:
            bv[k] = -1
        elif lp < lpp and cp > lpp:
            bv[k] = 1
    return bv


def run_market(mk, var, info=False):
    M = X.load1(mk)
    T = X.tfs(M)
    Xb = T[var["tf"]]
    Q = T["M15"]
    D = T["D1"]
    bv = bias_ves(D)
    nd = X.news_days()
    lhX, llX = pivots_last(Xb["h"], Xb["l"], 2)
    lhQ, llQ = pivots_last(Q["h"], Q["l"], 2)
    W = 24 if var["tf"] == "M5" else 90  # kolik svicek po sweepu se ceka na MSS (2 h / 1,5 h)
    buf = 2 * M["pip"] if M["fx"] else None
    out, funnel = [], dict(dni=0, bias=0, sweep=0, mss=0, disp=0, rr=0, fill=0)
    for k in range(2, len(D["c"])):
        funnel["dni"] += 1
        b = int(bv[k])
        if b == 0 or int(D["day"][k]) in nd:
            continue
        funnel["bias"] += 1
        i_d0, i_d1 = D["st"][k], D["en"][k]
        hm = M["hm"][i_d0:i_d1 + 1]
        asia = (hm >= 3) & (hm < 9)
        if asia.sum() < 60:
            continue
        aH, aL = M["h"][i_d0:i_d1 + 1][asia].max(), M["l"][i_d0:i_d1 + 1][asia].min()
        o7 = np.flatnonzero(hm >= 7)
        if not len(o7):
            continue
        nydo = M["o"][i_d0 + o7[0]]
        pdh, pdl = D["h"][k - 1], D["l"][k - 1]
        atrD = D["a"][k - 1]
        bf = buf if buf is not None else 0.03 * atrD
        tgt = pdh if b == 1 else pdl
        xs = np.searchsorted(Xb["st"], i_d0)
        xe = np.searchsorted(Xb["st"], i_d1, side="right") - 1
        losses = 0
        busy = -1
        for kz0, kz1 in KZ:
            if losses >= 2:
                break
            j = xs + 3
            while j < xe:
                hmj = Xb["hm"][j]
                if not (kz0 <= hmj < kz1) or Xb["en"][j] <= busy:
                    j += 1
                    continue
                # likvidita: PRVNI vybrani Asia low/high nebo PDL/PDH v danem dni (manipulace), pod/nad NY open
                pools = [aL, pdl] if b == 1 else [aH, pdh]
                if var.get("loc"):
                    qk = int(np.searchsorted(Q["st"], Xb["st"][j], side="right")) - 2
                    if qk >= 0:
                        pq = llQ[qk] if b == 1 else lhQ[qk]
                        if pq >= 0:
                            pools.append(Q["l"][pq] if b == 1 else Q["h"][pq])
                seg_l = M["l"][i_d0:Xb["st"][j]] if Xb["st"][j] > i_d0 else np.array([np.inf])
                seg_h = M["h"][i_d0:Xb["st"][j]] if Xb["st"][j] > i_d0 else np.array([-np.inf])
                if b == 1:
                    prev_low = seg_l[(hm[:len(seg_l)] >= 9)].min(initial=np.inf)  # low po Asii pred touto svickou
                    hit = [q for q in pools if Xb["l"][j] < q and prev_low >= q] and Xb["l"][j] < nydo
                else:
                    prev_high = seg_h[(hm[:len(seg_h)] >= 9)].max(initial=-np.inf)
                    hit = [q for q in pools if Xb["h"][j] > q and prev_high <= q] and Xb["h"][j] > nydo
                if not hit:
                    j += 1
                    continue
                funnel["sweep"] += 1
                # MSS: close za poslednim potvrzenym swingem PRED sweepem
                p = lhX[j] if b == 1 else llX[j]
                if p < 0:
                    j += 1
                    continue
                lvl = Xb["h"][p] if b == 1 else Xb["l"][p]
                if (lvl - Xb["c"][j]) * b <= 0:
                    j += 1
                    continue
                m, ext = -1, Xb["l"][j] if b == 1 else Xb["h"][j]
                for q in range(j + 1, min(j + W + 1, xe)):
                    if not (Xb["hm"][q] < kz1 + 0.5):
                        break
                    if (b == 1 and Xb["l"][q] < ext) or (b == -1 and Xb["h"][q] > ext):
                        ext = Xb["l"][q] if b == 1 else Xb["h"][q]
                    if (Xb["c"][q] - lvl) * b > 0:
                        m = q
                        break
                if m < 0:
                    j += 1
                    continue
                funnel["mss"] += 1
                lo = j + (np.argmin(Xb["l"][j:m + 1]) if b == 1 else np.argmax(Xb["h"][j:m + 1]))
                legE = Xb["h"][lo:m + 1].max() if b == 1 else Xb["l"][lo:m + 1].min()
                # displacement = FVG v noze od extremu po MSS
                fv = []
                for q in range(lo + 2, m + 1):
                    if b == 1 and Xb["l"][q] > Xb["h"][q - 2]:
                        fv.append((Xb["h"][q - 2], Xb["l"][q]))
                    if b == -1 and Xb["h"][q] < Xb["l"][q - 2]:
                        fv.append((Xb["h"][q], Xb["l"][q - 2]))
                if not fv:
                    j = m + 1
                    continue
                funnel["disp"] += 1
                leg = abs(legE - ext)
                if var["entry"] == "ob":
                    # OB = posledni opacna svicka pred impulzem (od extremu zpet), vstup na 50 % tela
                    ob = -1
                    for q in range(lo, max(lo - 6, j - 3) - 1, -1):
                        if (Xb["c"][q] - Xb["o"][q]) * b < 0:
                            ob = q
                            break
                    if ob < 0:
                        ob = lo
                    E = 0.5 * (Xb["o"][ob] + Xb["c"][ob])
                elif var["entry"] == "fvg":
                    E = fv[0][1] if b == 1 else fv[0][0]
                elif var["entry"] == "gp":
                    E = legE - b * 0.618 * leg
                else:
                    E = legE - b * 0.382 * leg
                SL = ext - b * bf
                risk = (E - SL) * b
                if risk <= 0 or (tgt - E) * b < 2 * risk:
                    funnel["rr"] += 0
                    j = m + 1
                    continue
                funnel["rr"] += 1
                tp1 = aH if b == 1 else aL
                f1 = 0.5 if (tp1 - E) * b >= 0.5 * risk and (tgt - tp1) * b > 0 else 0.0
                i0 = Xb["en"][m] + 1
                kzend = i_d0 + np.flatnonzero(hm < kz1 + 0.5)[-1]
                s = X.sim(M, b, E, SL, tgt, i0, kzend, 0, i_d1, tp1 if f1 else np.nan, f1)
                if s:
                    funnel["fill"] += 1
                    r = X.rec(M, "VES", X.vn(var), b, s, (tgt - E) * b / risk, atrD, "den")
                    if info:
                        r.update(E_=E, SL_=SL, TP2=tgt, TP1=tp1 if f1 else np.nan, aH=aH, aL=aL, pdh=pdh, pdl=pdl, nydo=nydo,
                                 i_sweep=int(Xb["st"][j]), i_mss=int(Xb["en"][m]), lvl=lvl, day0=int(i_d0))
                    out.append(r)
                    busy = s["ex"]
                    if s["R"] < 0:
                        losses += 1
                    j = int(np.searchsorted(Xb["st"], s["ex"], side="right"))
                    if losses >= 2:
                        break
                    continue
                j = m + 1
    return out, funnel, M


def chart(M, tr, path, n=12):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(4, 3, figsize=(21, 20))
    for ax, x in zip(axs.flat, tr[:n]):
        a = x["day0"] + 60 * 7  # od 00:00 NY... zobraz od Asie
        a = x["day0"] + 3 * 60
        e = min(x["ex"] + 90, len(M["c"]) - 1)
        key = (M["t"][a:e + 1] // 300)
        st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]]) + a
        en = np.r_[st[1:] - 1, e]
        o, h, l, c = M["o"][st], np.maximum.reduceat(M["h"][a:e + 1], st - a), np.minimum.reduceat(M["l"][a:e + 1], st - a), M["c"][en]
        for i in range(len(o)):
            col = "#26a69a" if c[i] >= o[i] else "#ef5350"
            ax.plot([i, i], [l[i], h[i]], color=col, lw=0.7)
            ax.add_patch(plt.Rectangle((i - 0.3, min(o[i], c[i])), 0.6, abs(c[i] - o[i]) + 1e-12, color=col))
        pos = lambda i1: int(np.searchsorted(st, i1, side="right")) - 1
        for y, col, lab in ((x["aH"], "#7e57c2", "Asia H"), (x["aL"], "#7e57c2", "Asia L"), (x["pdh"], "k", "PDH"),
                            (x["pdl"], "k", "PDL"), (x["nydo"], "orange", "NY DO"), (x["E_"], "b", "vstup"),
                            (x["SL_"], "r", "SL"), (x["TP2"], "g", "TP2"), (x["TP1"], "#66bb6a", "TP1"), (x["lvl"], "gray", "MSS lvl")):
            if np.isfinite(y):
                ax.axhline(y, color=col, lw=0.8, ls="--" if lab in ("PDH", "PDL", "NY DO", "MSS lvl") else "-")
                ax.text(0, y, lab, fontsize=7, color=col, va="bottom")
        for i1, col in ((x["i_sweep"], "m"), (x["i_mss"], "gray"), (x["fi"], "b"), (x["ex"], "k")):
            ax.axvline(pos(i1), color=col, lw=0.8)
        lo_, hi_ = min(x["SL_"], x["pdl"], x["aL"]), max(x["TP2"], x["pdh"], x["aH"])
        ax.set_ylim(lo_ - 0.1 * (hi_ - lo_), hi_ + 0.1 * (hi_ - lo_))
        ax.set_title(f"{M['mk']} {pd.to_datetime(x['t'], unit='s'):%Y-%m-%d %H:%M} UTC {'LONG' if x['d'] == 1 else 'SHORT'} R={x['R']:+.2f}", fontsize=10)
    plt.tight_layout()
    plt.savefig(path, dpi=70)
    plt.close()


VARS = [dict(tf=t, entry=e) for t in ("M5", "M1") for e in ("ob", "fvg", "382", "gp")]

if __name__ == "__main__":
    if sys.argv[1:2] == ["ukazka"]:
        tr, fun, M = run_market("EURUSD", dict(tf="M5", entry="ob"), info=True)
        print(fun, len(tr))
        tr = [x for x in tr if x["t"] >= X.OOS]
        chart(M, tr, os.path.join(D11, "ves_ukazky.png"))
        sys.exit()
    rows, funs = [], []
    for mk in MARKETS:
        for v in VARS:
            tr, fun, _ = run_market(mk, v)
            rows += tr
            funs.append(dict(mk=mk, var=X.vn(v), **fun))
        print(mk, len(rows), flush=True)
    pd.DataFrame(rows).to_pickle(os.path.join(D11, "f11_VES.pkl"))
    pd.DataFrame(funs).to_csv(os.path.join(D11, "f11_VES_trychtyr.csv"), index=False)
