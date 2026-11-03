"""
F12 - market structure podle doplnujicich pravidel uzivatele (A2) a Petrovych obrazku (MS teorie s5-s6, Trend s3-s4).
Jeden stroj pro libovolny TF (4H, 15m, 5m, 1m), pocita se jen ze zavrenych svicek:
- BOS = close TELEM za weak levelem o >= eps*ATR, momentum svicka (telo >= prumer 20 tel, <= 3 ATR, spravna barva)
  a dalsi svicka nezavre zpet + (objem nad MA50 nebo dalsi svicka stejne barvy). Udalost plati az po zavreni dalsi svicky.
- strong level = extrem mezi swingem, ze ktereho je BOS, a svickou pruraz (vcetne).
- weak level = extrem po pruraze; "zakresli se" az po pullbacku >= fib_tol nohy (kotva -> extrem) a noha >= kmin*ATR.
  Kotva = strong level, nebo "Fibo se presune na dalsi bod, kde cena zpomali nebo se otoci" (A2): posledni swing
  ZigZagu na ZAVIRACICH cenach (otocka kmin*ATR) pred extremem.
- close za strong levelem (stejna pravidla) = zmena trendu.
"""
import numpy as np
from numba import njit


@njit(cache=True)
def ms_machine(o, h, l, c, v, a, kmin, eps, fib_tol):
    n = len(c)
    tr_o = np.zeros(n, np.int8)
    strong_o = np.full(n, np.nan)
    strongi_o = np.full(n, -1, np.int64)
    weak_o = np.full(n, np.nan)
    bos_o = np.full(n, np.nan)
    bosi_o = np.full(n, -1, np.int64)
    # udalosti
    m = n // 2 + 10
    ev_i = np.full(m, -1, np.int64)
    ev_d = np.zeros(m, np.int8)
    ev_flip = np.zeros(m, np.int8)
    ev_lvl = np.full(m, np.nan)
    ev_orig = np.full(m, -1, np.int64)
    ev_brk = np.full(m, -1, np.int64)
    ev_st = np.full(m, np.nan)
    ev_sti = np.full(m, -1, np.int64)
    ne = 0
    body = np.abs(c - o)
    bavg = np.full(n, np.nan)
    s = 0.0
    for i in range(n):
        s += body[i]
        if i >= 20:
            s -= body[i - 20]
        if i >= 19:
            bavg[i] = s / 20.0
    vma = np.full(n, np.nan)
    s = 0.0
    for i in range(n):
        s += v[i]
        if i >= 50:
            s -= v[i - 50]
        if i >= 49:
            vma[i] = s / 50.0
    tr = 0
    strong = np.nan
    strong_i = -1
    weak = np.nan
    weak_i = -1
    ext = np.nan
    ext_i = -1
    bos = np.nan
    bos_i = -1
    cd = 0          # kandidat: smer
    cflip = 0
    clvl = np.nan
    corig = -1
    cbrk = -1
    # ZigZag na zaviracich cenach: potvrzene swingy (uroven = knot u pivotu, index pivotu)
    zdir = 0
    zext = c[0]
    zexti = 0
    zl_l = np.full(n // 2 + 10, np.nan)
    zl_i = np.full(n // 2 + 10, -1, np.int64)
    nzl = 0
    zh_l = np.full(n // 2 + 10, np.nan)
    zh_i = np.full(n // 2 + 10, -1, np.int64)
    nzh = 0
    for i in range(21, n):
        ai = a[i]
        if not ai > 0:
            continue
        # 0) ZigZag
        if zdir >= 0:
            if c[i] > zext or zdir == 0 and c[i] > zext:
                zext = c[i]
                zexti = i
            if c[i] < zext - kmin * ai:
                q0 = max(zexti - 1, 0)
                q1 = min(zexti + 1, n - 1)
                hv = h[q0]
                for q in range(q0, q1 + 1):
                    hv = max(hv, h[q])
                zh_l[nzh] = hv
                zh_i[nzh] = zexti
                nzh += 1
                zdir = -1
                zext = c[i]
                zexti = i
        if zdir == -1:
            if c[i] < zext:
                zext = c[i]
                zexti = i
            if c[i] > zext + kmin * ai:
                q0 = max(zexti - 1, 0)
                q1 = min(zexti + 1, n - 1)
                lv = l[q0]
                for q in range(q0, q1 + 1):
                    lv = min(lv, l[q])
                zl_l[nzl] = lv
                zl_i[nzl] = zexti
                nzl += 1
                zdir = 1
                zext = c[i]
                zexti = i
        # 1) potvrzeni kandidata z predchozi svicky
        if cd != 0 and cbrk == i - 1:
            ok_close = (c[i] - clvl) * cd > 0
            ok_mom = (v[i - 1] >= vma[i - 1]) or ((c[i] - o[i]) * cd > 0)
            if ok_close and ok_mom:
                # strong = extrem mezi swingem (corig) a svickou pruraz (cbrk)
                lo, hi = corig, cbrk
                if lo > hi:
                    lo = hi
                if cd == 1:
                    sv = l[lo]
                    si = lo
                    for q in range(lo, hi + 1):
                        if l[q] < sv:
                            sv = l[q]
                            si = q
                    ev = h[cbrk]
                    evi = cbrk
                    if h[i] > ev:
                        ev = h[i]
                        evi = i
                else:
                    sv = h[lo]
                    si = lo
                    for q in range(lo, hi + 1):
                        if h[q] > sv:
                            sv = h[q]
                            si = q
                    ev = l[cbrk]
                    evi = cbrk
                    if l[i] < ev:
                        ev = l[i]
                        evi = i
                tr = cd
                strong = sv
                strong_i = si
                weak = np.nan
                weak_i = -1
                ext = ev
                ext_i = evi
                bos = clvl
                bos_i = i
                if ne < m:
                    ev_i[ne] = i
                    ev_d[ne] = cd
                    ev_flip[ne] = cflip
                    ev_lvl[ne] = clvl
                    ev_orig[ne] = corig
                    ev_brk[ne] = cbrk
                    ev_st[ne] = sv
                    ev_sti[ne] = si
                    ne += 1
            cd = 0
        elif cd != 0:
            cd = 0
        # 2) extrem a potvrzeni weak levelu (jen dokud weak neni)
        if tr == 1 and np.isnan(weak) and bos_i != i:
            if h[i] > ext:
                ext = h[i]
                ext_i = i
            anc = strong
            for q in range(nzl - 1, max(nzl - 30, 0) - 1, -1):
                if zl_i[q] < ext_i:
                    if zl_i[q] > strong_i and zl_l[q] > anc:
                        anc = zl_l[q]
                    break
            leg = ext - anc
            if leg >= kmin * ai and l[i] <= ext - fib_tol * leg:
                weak = ext
                weak_i = ext_i
        elif tr == -1 and np.isnan(weak) and bos_i != i:
            if l[i] < ext:
                ext = l[i]
                ext_i = i
            anc = strong
            for q in range(nzh - 1, max(nzh - 30, 0) - 1, -1):
                if zh_i[q] < ext_i:
                    if zh_i[q] > strong_i and zh_l[q] < anc:
                        anc = zh_l[q]
                    break
            leg = anc - ext
            if leg >= kmin * ai and h[i] >= ext + fib_tol * leg:
                weak = ext
                weak_i = ext_i
        # 3) novy kandidat na teto svicce
        bd = c[i] - o[i]
        mom = abs(bd) >= bavg[i] and abs(bd) <= 3.0 * ai
        if tr == 0:
            hh = h[i - 20]
            hi_i = i - 20
            ll = l[i - 20]
            lo_i = i - 20
            for q in range(i - 20, i):
                if h[q] > hh:
                    hh = h[q]
                    hi_i = q
                if l[q] < ll:
                    ll = l[q]
                    lo_i = q
            if mom and bd > 0 and c[i] > hh + eps * ai:
                cd, cflip, clvl, corig, cbrk = 1, 1, hh, hi_i, i
            elif mom and bd < 0 and c[i] < ll - eps * ai:
                cd, cflip, clvl, corig, cbrk = -1, 1, ll, lo_i, i
        elif tr == 1:
            if mom and bd < 0 and c[i] < strong - eps * ai:
                cd, cflip, clvl, corig, cbrk = -1, 1, strong, strong_i, i
            elif (not np.isnan(weak)) and mom and bd > 0 and c[i] > weak + eps * ai:
                cd, cflip, clvl, corig, cbrk = 1, 0, weak, weak_i, i
        else:
            if mom and bd > 0 and c[i] > strong + eps * ai:
                cd, cflip, clvl, corig, cbrk = 1, 1, strong, strong_i, i
            elif (not np.isnan(weak)) and mom and bd < 0 and c[i] < weak - eps * ai:
                cd, cflip, clvl, corig, cbrk = -1, 0, weak, weak_i, i
        tr_o[i] = tr
        strong_o[i] = strong
        strongi_o[i] = strong_i
        weak_o[i] = weak
        bos_o[i] = bos
        bosi_o[i] = bos_i
    return (tr_o, strong_o, strongi_o, weak_o, bos_o, bosi_o,
            ev_i[:ne], ev_d[:ne], ev_flip[:ne], ev_lvl[:ne], ev_orig[:ne], ev_brk[:ne], ev_st[:ne], ev_sti[:ne])


def run(T, kmin, eps=0.1, fib_tol=0.35):
    r = ms_machine(T["o"], T["h"], T["l"], T["c"], T["v"].astype(np.float64), T["a"], float(kmin), float(eps), float(fib_tol))
    keys = ("tr", "strong", "strong_i", "weak", "bos", "bos_i")
    S = dict(zip(keys, r[:6]))
    S["ev"] = dict(i=r[6], d=r[7], flip=r[8], lvl=r[9], orig=r[10], brk=r[11], st=r[12], sti=r[13])
    return S


def chart(T, S, a, e, path, title, zones=None):
    """Svicky [a, e) s BOS (carkovane od swingu po pruraz), strong a weak levely; volitelne zony (i0, i1, lo, hi, d)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(20, 9))
    for i in range(a, e):
        col = "#2962ff" if T["c"][i] >= T["o"][i] else "#222222"
        ax.plot([i, i], [T["l"][i], T["h"][i]], color=col, lw=0.7)
        ax.add_patch(plt.Rectangle((i - 0.35, min(T["o"][i], T["c"][i])), 0.7, abs(T["c"][i] - T["o"][i]) + 1e-12, color=col))
    ev = S["ev"]
    for k in range(len(ev["i"])):
        i, d, fl = ev["i"][k], ev["d"][k], ev["flip"][k]
        if not (a <= ev["brk"][k] < e):
            continue
        col = "g" if d == 1 else "r"
        x0 = max(ev["orig"][k], a)
        ax.plot([x0, ev["brk"][k]], [ev["lvl"][k]] * 2, color=col, ls="--", lw=1.2)
        ax.text(x0, ev["lvl"][k], ("CH " if fl else "BOS ") + ("↑" if d == 1 else "↓"), color=col, fontsize=8,
                va="bottom" if d == 1 else "top")
        si = ev["sti"][k]
        if si >= a:
            ax.plot([si, min(e, si + 40)], [ev["st"][k]] * 2, color="orange", lw=1.0)
            ax.text(si, ev["st"][k], "S-" + ("Low" if d == 1 else "High"), color="orange", fontsize=7,
                    va="top" if d == 1 else "bottom")
    # weak levely: kreslit, kdyz se objevi
    w = S["weak"]
    for i in range(a + 1, e):
        if np.isfinite(w[i]) and (not np.isfinite(w[i - 1]) or w[i] != w[i - 1]):
            ax.plot([i, min(e, i + 30)], [w[i]] * 2, color="purple", lw=0.9, ls=":")
            ax.text(i, w[i], "W", color="purple", fontsize=7)
    if zones:
        for (i0, i1, lo, hi, d) in zones:
            if i1 < a or i0 > e:
                continue
            ax.add_patch(plt.Rectangle((max(i0, a), lo), min(i1, e) - max(i0, a), hi - lo,
                                       color="#26a69a" if d == 1 else "#ef5350", alpha=0.25))
    tr = S["tr"]
    ax.set_title(title + f"   (pozadí: trend struktury, zelená = up, červená = down)", fontsize=11)
    for i in range(a, e):
        if tr[i] != 0:
            ax.axvspan(i - 0.5, i + 0.5, color="#c8e6c9" if tr[i] == 1 else "#ffcdd2", alpha=0.25, lw=0)
    ax.set_xlim(a - 1, e + 1)
    plt.tight_layout()
    plt.savefig(path, dpi=80)
    plt.close()
