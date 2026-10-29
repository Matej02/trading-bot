"""F7: parametry dokumentu a ablace pro S4 (povinnost SFP, FVG v pasmu, sklon), S5 a S6 (SFP i na VTF)."""
import os

os.chdir(r"D:\Trading bot")
p = "research_f7.py"
s = open(p, encoding="utf-8").read()


def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:80], s.count(a))
    s = s.replace(a, b)


rep('''            out.append(S(i, d, ext, i, 10, 10, L.exit_idx(B, i, 15, utc_hour=22), tp1=poc, f1=0.5,''',
    '''            out.append(S(i, d, ext, i, K, 10, L.exit_idx(B, i, 15, utc_hour=22), tp1=poc, f1=0.5,''')
# --- S4 numba: volitelne SFP, FVG, prah sklonu
rep('''                m15e, m15bos, m15below, m15above, m15day, fe, fd, flo, fhi, fday):
    """S4 spoustece na VTF: po killzone BOS M15 (displacement, RVOL >= 1,5) pullback do pasma VWAP..+1 sigma,
    v pasmu neotestovany FVG z impulzu, SFP pod posledni swing low VTF (RVOL >= 1,5). Short zrcadlove."""''',
    '''                m15e, m15bos, m15below, m15above, m15day, fe, fd, flo, fhi, fday, need_sfp, need_fvg, slope_thr):
    """S4 spoustece na VTF: po killzone BOS M15 (displacement, RVOL >= 1,5) pullback do pasma VWAP..+1 sigma,
    v pasmu neotestovany FVG z impulzu, SFP pod posledni swing low VTF (RVOL >= 1,5). Short zrcadlove.
    need_sfp=False: spoustec = prvni dotek pasma v pullbacku (parametr dokumentu "povinnost SFP"),
    need_fvg=False: bez podminky FVG v pasmu (ablace)."""''')
rep('''    nf = 0
    for k in range(1, nv):''', '''    nf = 0
    trL = -1
    trS = -1
    for k in range(1, nv):''')
rep('''            hod, hod_k, lod, lod_k = -1e18, -1, 1e18, -1
            nf = 0
        while p15''', '''            hod, hod_k, lod, lod_k = -1e18, -1, 1e18, -1
            nf = 0
            trL = trS = -1
        while p15''')
rep('''        if bull and not invL and hod_k >= 0 and hod_k < k and h4st[k] == 1 and h1st[k] == 1 and vc[k] > vw[k] \\
                and vc[k] > DOv[k] and vc[k] > pdpoc[k] and slope[k] >= 0.1:
            s1 = vsl1[k - 1]
            if not np.isnan(s1) and vl[k] <= vw[k] + sg[k] and vl[k] <= s1 - 0.05 * A and vc[k] > s1 \\
                    and s1 - vl[k] <= 0.5 * A and vrv[k] >= 1.5:
                for q in range(nf):
                    if FD[q] == 1 and FF[q] <= ve[hod_k] and (FT[q] < 0 or FT[q] > hod_k) and FH[q] >= vw[k] and FL[q] <= vw[k] + sg[k]:
                        ok_k[cnt], ok_d[cnt] = k, 1
                        cnt += 1
                        break
        if bear and not invS and lod_k >= 0 and lod_k < k and h4st[k] == -1 and h1st[k] == -1 and vc[k] < vw[k] \\
                and vc[k] < DOv[k] and vc[k] < pdpoc[k] and slope[k] <= -0.1:
            s1 = vsh1[k - 1]
            if not np.isnan(s1) and vh[k] >= vw[k] - sg[k] and vh[k] >= s1 + 0.05 * A and vc[k] < s1 \\
                    and vh[k] - s1 <= 0.5 * A and vrv[k] >= 1.5:
                for q in range(nf):
                    if FD[q] == -1 and FF[q] <= ve[lod_k] and (FT[q] < 0 or FT[q] > lod_k) and FL[q] <= vw[k] and FH[q] >= vw[k] - sg[k]:
                        ok_k[cnt], ok_d[cnt] = k, -1
                        cnt += 1
                        break''',
    '''        if bull and not invL and hod_k >= 0 and hod_k < k and h4st[k] == 1 and h1st[k] == 1 and vc[k] > vw[k] \\
                and vc[k] > DOv[k] and vc[k] > pdpoc[k] and slope[k] >= slope_thr and vl[k] <= vw[k] + sg[k]:
            s1 = vsl1[k - 1]
            if need_sfp:
                trig = not np.isnan(s1) and vl[k] <= s1 - 0.05 * A and vc[k] > s1 and s1 - vl[k] <= 0.5 * A and vrv[k] >= 1.5
            else:
                trig = trL != hod_k  # prvni dotek pasma v tomto pullbacku
            if trig:
                fok = not need_fvg
                for q in range(nf):
                    if FD[q] == 1 and FF[q] <= ve[hod_k] and (FT[q] < 0 or FT[q] > hod_k) and FH[q] >= vw[k] and FL[q] <= vw[k] + sg[k]:
                        fok = True
                        break
                if fok:
                    ok_k[cnt], ok_d[cnt] = k, 1
                    cnt += 1
                    trL = hod_k
        if bear and not invS and lod_k >= 0 and lod_k < k and h4st[k] == -1 and h1st[k] == -1 and vc[k] < vw[k] \\
                and vc[k] < DOv[k] and vc[k] < pdpoc[k] and slope[k] <= -slope_thr and vh[k] >= vw[k] - sg[k]:
            s1 = vsh1[k - 1]
            if need_sfp:
                trig = not np.isnan(s1) and vh[k] >= s1 + 0.05 * A and vc[k] < s1 and vh[k] - s1 <= 0.5 * A and vrv[k] >= 1.5
            else:
                trig = trS != lod_k
            if trig:
                fok = not need_fvg
                for q in range(nf):
                    if FD[q] == -1 and FF[q] <= ve[lod_k] and (FT[q] < 0 or FT[q] > lod_k) and FL[q] <= vw[k] and FH[q] >= vw[k] - sg[k]:
                        fok = True
                        break
                if fok:
                    ok_k[cnt], ok_d[cnt] = k, -1
                    cnt += 1
                    trS = lod_k''')
rep('''def setups_s4(B, vtf):
    """S4 VWAP trend pullback."""''', '''def setups_s4(B, vtf, need_sfp=True, need_fvg=True, slope_thr=0.1, K=10):
    """S4 VWAP trend pullback."""''')
rep('''                         fe[fo], fd[fo], flo[fo], fhi[fo], fday[fo])''',
    '''                         fe[fo], fd[fo], flo[fo], fhi[fo], fday[fo], need_sfp, need_fvg, slope_thr)''')
rep('''        out.append(S(i, d, ext, ei, 10, 6, L.exit_idx(B, i, 15.5, utc_hour=22.5), sl_cap=1.0 * a15[i], tp1=tp1, min1R=1.5,''',
    '''        out.append(S(i, d, ext, ei, K, 6, L.exit_idx(B, i, 15.5, utc_hour=22.5), sl_cap=1.0 * a15[i], tp1=tp1, min1R=1.5,''')
# --- S5
rep('''def setups_s5(B, mode="mss"):''', '''def setups_s5(B, mode="mss", rv_bo=2.0, min_days=3, target="hvn", K=12):''')
rep('''        if not D["ok"][dd] or not (be[dd - 1] and be[dd - 2] and be[dd - 3]):
            continue
        r = 3''', '''        if not D["ok"][dd] or not all(be[dd - q] for q in range(1, min_days + 1)):
            continue
        r = min_days''')
rep('''                if Ld == 0 or not H1["rv"][j] >= 2.0:''', '''                if Ld == 0 or not H1["rv"][j] >= rv_bo:''')
rep('''                if d == 1:
                    lvx = lv[lv > bhi]
                    if not len(lvx):
                        continue
                    hvx = hv[hv > lvx.min()]
                    if not len(hvx):
                        continue
                    target = hvx.min()
                    ce = (H1["h"][fj - 2] + H1["l"][fj]) / 2
                    band = max(va_edge, ce)
                else:
                    lvx = lv[lv < blo]
                    if not len(lvx):
                        continue
                    hvx = hv[hv < lvx.max()]
                    if not len(hvx):
                        continue
                    target = hvx.max()
                    ce = (H1["h"][fj] + H1["l"][fj - 2]) / 2
                    band = min(va_edge, ce)''', '''                tgt = np.nan
                if d == 1:
                    lvx = lv[lv > bhi]
                    hvx = hv[hv > lvx.min()] if len(lvx) else hv[:0]
                    if len(hvx):
                        tgt = hvx.min()
                    ce = (H1["h"][fj - 2] + H1["l"][fj]) / 2
                    band = max(va_edge, ce)
                else:
                    lvx = lv[lv < blo]
                    hvx = hv[hv < lvx.max()] if len(lvx) else hv[:0]
                    if len(hvx):
                        tgt = hvx.max()
                    ce = (H1["h"][fj] + H1["l"][fj - 2]) / 2
                    band = min(va_edge, ce)
                if target == "hvn" and np.isnan(tgt):
                    continue''')
rep('''                common = dict(tp1=target, min1R=1.5, f1=0.5, tp2=tp2, f2=0.5, trail_tf="H1", soft=va_edge, tag=mode)''',
    '''                common = dict(tp1=tgt, min1R=1.5, f1=0.5, tp2=tp2, f2=0.5, trail_tf="H1", soft=va_edge, tag=mode)
                if target != "hvn":  # ablace: pevny TP1 2R misto HVN
                    common.pop("tp1")
                    common.update(tp1R=2.0)''')
rep('''                    out.append(S(i, d, ext, i, 12, 10, texit, sl_cap_lvl=cap, **common))''',
    '''                    out.append(S(i, d, ext, i, K, 10, texit, sl_cap_lvl=cap, **common))''')
# --- S6: SFP i na VTF, prah Asie
rep('''def setups_s6(B, PL, Z, do_mode="day", rv_sfp=1.5, killzone=True):''',
    '''def vtf_sweeps(B, PL, vtf):
    """Sweep a SFP poolu na VTF (S6: "na M15 nebo VTF vznikne SFP")."""
    V = B["T"][vtf]
    sw, tr = pool_sweeps(PL["lev"], PL["side"], PL["cr"], PL["un"], V["s"], V["e"], V["h"], V["l"], V["c"], V["a"], V["ix"], False)
    return V, sw, tr


def setups_s6(B, PL, Z, do_mode="day", rv_sfp=1.5, killzone=True, asia_max=0.4, vsw=None, K=10):''')
rep('''    M, D = B["T"]["M15"], B["T"]["D1"]
    out = []
    cache = {}
    for p in np.flatnonzero((PL["trig"] >= 0) & np.isin(PL["kind"], (1, 4))):
        m, bsw = PL["trig"][p], PL["sw"][p]
        i = M["e"][m]
        h0 = B["nyh"][M["s"][m]]''', '''    M15, D = B["T"]["M15"], B["T"]["D1"]
    out = []
    cache = {}
    cands = [(p, M15, PL["trig"][p], PL["sw"][p]) for p in np.flatnonzero((PL["trig"] >= 0) & np.isin(PL["kind"], (1, 4)))]
    if vsw is not None:
        V, vs_, vt_ = vsw
        cands += [(p, V, vt_[p], vs_[p]) for p in np.flatnonzero((vt_ >= 0) & np.isin(PL["kind"], (1, 4)))]
        cands.sort(key=lambda x: x[1]["e"][x[2]])
    used = set()
    for p, M, m, bsw in cands:
        if p in used:
            continue
        i = M["e"][m]
        h0 = B["nyh"][M["s"][m]]''')
rep('''            ok = datr > 0 and D["st"][dd - 1] == d and (D["c"][dd - 1] - D["poc"][dd - 1]) * d > 0 \\
                and (ah - al) <= 0.4 * datr \\''', '''            ok = datr > 0 and D["st"][dd - 1] == d and (D["c"][dd - 1] - D["poc"][dd - 1]) * d > 0 \\
                and (ah - al) <= asia_max * datr \\''')
rep('''        london = h0 < 6
        out.append(S(i, d, ext, ei, 10, 8, L.exit_idx''', '''        london = h0 < 6
        used.add(p)
        out.append(S(i, d, ext, ei, K, 8, L.exit_idx''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
