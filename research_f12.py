"""
F12 - Mucka podle doplnujicich pravidel uzivatele (F12_PLAN.md). Struktura z research_f12_ms (stejny stroj na 4H/15m/5m/1m).
Spusteni: py research_f12.py [trh ...]  -> research_data/f12/f12_<trh>.pkl ; s F10_NOCOST=1 bez nakladu (_nc).
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f10 as X
import research_f12_ms as MS

D12 = os.path.join("research_data", "f12")
MARKETS = ["EURUSD", "GBPUSD", "XAUUSD", "XAGUSD", "NAS100mini"]
KS = (1.5, 2.5, 4.0)
DAY = 86400
KZ = ((9.0, 11.0), (13.5, 17.0))   # killzones mistniho casu (Praha) [PDF Killzones]


def prague_hours(t):
    cz = pd.to_datetime(t, unit="s", utc=True).tz_convert("Europe/Prague")
    return (cz.hour + cz.minute / 60.0).to_numpy(float), (cz.normalize().tz_localize(None).as_unit("s").asi8 // DAY)


# ---------------------------------------------------------------- POI: zony a balancni levely
def zones_from(Tb, S, T15, M, age_days, k_tf):
    """Zona pred impulzem, ktery udelal BOS [PDF S/D]: base kolem strong levelu (male svicky, max 6), hranice pres tela [A4].
    Plati od potvrzeni BOS do stari; prvni dotek plati, po doteku hloubeji nez 25 % plati jen ten dotek [obr S/D s4-2]."""
    ev = S["ev"]
    o, h, l, c, a = Tb["o"], Tb["h"], Tb["l"], Tb["c"], Tb["a"]
    body = np.abs(c - o)
    out = []
    t = M["t"]
    for k in range(len(ev["i"])):
        d, si, brk, ci = int(ev["d"][k]), int(ev["sti"][k]), int(ev["brk"][k]), int(ev["i"][k])
        if si < 1 or not a[si] > 0:
            continue
        small = lambda q: body[q] <= 0.6 * a[q]
        s = e = si
        while e + 1 < brk and small(e + 1) and e - s + 1 < 6:
            e += 1
        while s - 1 >= 0 and small(s - 1) and e - s + 1 < 6:
            s -= 1
        top = max(max(o[q], c[q]) for q in range(s, e + 1))
        bot = min(min(o[q], c[q]) for q in range(s, e + 1))
        if top - bot < 0.1 * a[si]:
            if d == 1:
                bot = l[s:e + 1].min()
            else:
                top = h[s:e + 1].max()
        a0 = int(Tb["en"][ci]) + 1
        if a0 >= len(t):
            continue
        t_exp = t[a0] + age_days * DAY
        hz = top - bot
        # dotyky na 15m
        k0 = int(np.searchsorted(T15["st"], a0))
        k1 = int(np.searchsorted(T15["st"], np.searchsorted(t, t_exp)))
        end = int(np.searchsorted(t, t_exp)) - 1
        deep = False
        for q in range(k0, min(k1, len(T15["c"]))):
            if d == 1:
                if T15["c"][q] < bot:
                    end = int(T15["en"][q]); break
                if T15["l"][q] < top - 0.25 * hz:
                    deep = True
                elif deep and T15["l"][q] > top:
                    end = int(T15["st"][q]); break
            else:
                if T15["c"][q] > top:
                    end = int(T15["en"][q]); break
                if T15["h"][q] > bot + 0.25 * hz:
                    deep = True
                elif deep and T15["h"][q] < bot:
                    end = int(T15["st"][q]); break
        out.append((d, bot, top, a0, end, k_tf))
    return out


def balance_from(Tb, S, T15, M, age_days, k_tf):
    """Balancni level = protazeny BOS [PDF Balancni levely]; plati jen prvni navrat [A2 'po prvnim navratu mitigovany']."""
    ev = S["ev"]
    t = M["t"]
    out = []
    for k in range(len(ev["i"])):
        d, lvl, ci = int(ev["d"][k]), float(ev["lvl"][k]), int(ev["i"][k])
        a0 = int(Tb["en"][ci]) + 1
        if a0 >= len(t):
            continue
        t_exp = t[a0] + age_days * DAY
        k0 = int(np.searchsorted(T15["st"], a0))
        k1 = min(int(np.searchsorted(T15["st"], np.searchsorted(t, t_exp))), len(T15["c"]))
        f = -1
        for q in range(k0, k1):
            a15 = T15["a"][q]
            if (d == 1 and T15["l"][q] <= lvl + 0.1 * a15) or (d == -1 and T15["h"][q] >= lvl - 0.1 * a15):
                f = q
                break
        if f < 0:
            continue
        g = min(f + 96, k1 - 1)  # navrat nejdyl 1 den
        for q in range(f + 1, min(f + 96, k1)):
            a15 = T15["a"][q]
            if (d == 1 and T15["l"][q] > lvl + 0.5 * a15) or (d == -1 and T15["h"][q] < lvl - 0.5 * a15):
                g = q
                break
        out.append((d, lvl, int(T15["st"][f]), int(T15["en"][g]), k_tf))
    return out


# ---------------------------------------------------------------- denni levely pro TP [obr 178, PDF Statistiky]
def day_levels(M, D, cz, czday):
    n = len(D["c"])
    vw = np.full(n, np.nan)
    poc = np.full(n, np.nan)
    hlc = (M["h"] + M["l"] + M["c"]) / 3.0
    for k in range(n):
        s, e = D["st"][k], D["en"][k] + 1
        vv = M["v"][s:e]
        if vv.sum() > 0:
            vw[k] = float((hlc[s:e] * vv).sum() / vv.sum())
            aD = D["a"][k] if D["a"][k] > 0 else (D["h"][k] - D["l"][k])
            bw = max(aD / 50.0, 1e-9)
            lo = M["l"][s:e].min()
            idx = ((hlc[s:e] - lo) / bw).astype(int)
            hist = np.bincount(idx, weights=vv)
            poc[k] = lo + (hist.argmax() + 0.5) * bw
    return vw, poc


def asia_hl(M, cz, czday):
    """Asia 2:00-6:00 Praha pro kazdy prazsky den: (high, low) slovnik den -> (h, l)."""
    m = (cz >= 2.0) & (cz < 6.0)
    df = pd.DataFrame({"d": czday[m], "h": M["h"][m], "l": M["l"][m]})
    g = df.groupby("d").agg(h=("h", "max"), l=("l", "min"))
    return {int(k): (r.h, r.l) for k, r in g.iterrows()}


# ---------------------------------------------------------------- priprava trhu
_CACHE = {}


def prep(mk):
    if mk in _CACHE:
        return _CACHE[mk]
    M = X.load1(mk)
    T = X.tfs(M)
    T["M1"]["a"] = L.wilder_atr(M["h"], M["l"], M["c"], 14)
    cz, czday = prague_hours(M["t"])
    D = T["D1"]
    _, bm = X.bias_arrays(D)
    vw, poc = day_levels(M, D, cz, czday)
    P = dict(M=M, T=T, cz=cz, czday=czday, D=D, bm=bm, vw=vw, poc=poc, asia=asia_hl(M, cz, czday),
             dmap=np.searchsorted(D["st"], np.arange(len(M["c"])), side="right") - 1,
             c4=X.closed_map(T["H4"], len(M["c"])), news=X.news_days())
    P["S"] = {}
    for k in KS:
        S4, S15 = MS.run(T["H4"], k), MS.run(T["M15"], k)
        P["S"][k] = dict(H4=S4, M15=S15, M5=MS.run(T["M5"], k), M1=MS.run(T["M1"], k))
        z = zones_from(T["H4"], S4, T["M15"], M, 30, "4H") + zones_from(T["M15"], S15, T["M15"], M, 5, "15m")
        b = balance_from(T["H4"], S4, T["M15"], M, 30, "4H") + balance_from(T["M15"], S15, T["M15"], M, 5, "15m")
        P["S"][k]["Z"] = np.array([r[:5] for r in z], float).reshape(-1, 5)
        P["S"][k]["B"] = np.array([r[:4] for r in b], float).reshape(-1, 4)
    _CACHE.clear()
    _CACHE[mk] = P
    return P


def in_poi(P, k, poi, d, sv, si):
    a15 = P["T"]["M15"]["a"][max(0, int(np.searchsorted(P["T"]["M15"]["st"], si, side="right")) - 1)]
    if poi in ("zona", "obe"):
        Z = P["S"][k]["Z"]
        if len(Z):
            m = (Z[:, 0] == d) & (Z[:, 3] <= si) & (si <= Z[:, 4])
            hz = Z[:, 2] - Z[:, 1]
            if d == 1:
                m &= (sv <= Z[:, 2]) & (sv >= Z[:, 1] - 0.5 * hz)
            else:
                m &= (sv >= Z[:, 1]) & (sv <= Z[:, 2] + 0.5 * hz)
            if m.any():
                return True
    if poi in ("balanc", "obe"):
        B = P["S"][k]["B"]
        if len(B):
            m = (B[:, 0] == d) & (B[:, 2] <= si) & (si <= B[:, 3])
            if d == 1:
                m &= (sv <= B[:, 1] + 0.2 * a15) & (sv >= B[:, 1] - 0.5 * a15)
            else:
                m &= (sv >= B[:, 1] - 0.2 * a15) & (sv <= B[:, 1] + 0.5 * a15)
            if m.any():
                return True
    return False


# ---------------------------------------------------------------- strategie
def run_market(mk, var, info=False):
    P = prep(mk)
    M, T, cz, czday, D = P["M"], P["T"], P["cz"], P["czday"], P["D"]
    k, tf = var["k"], var["tf"]
    Xb = T[tf]
    SX = P["S"][k][tf]
    S4 = P["S"][k]["H4"]
    ev = SX["ev"]
    n = len(M["c"])
    t = M["t"]
    out = []
    busy = -1
    per_day = {}
    for q in range(1, len(ev["i"])):
        if not ev["flip"][q]:
            continue
        d = int(ev["d"][q])
        if ev["d"][q - 1] != -d:
            continue
        sti, brk_prev = int(ev["sti"][q]), int(ev["brk"][q - 1])
        if not (brk_prev <= sti <= brk_prev + 60):   # sweep = low po BOS dolu, ktery vybral likviditu
            continue
        ic = int(Xb["en"][ev["i"][q]])
        if ic + 2 >= n or ic <= busy:
            continue
        h_ = cz[ic]
        kz = [w for w in KZ if w[0] <= h_ < w[1]]
        if not kz:
            continue
        day = int(czday[ic])
        if per_day.get(day, 0) >= 2:
            continue
        if day in P["news"] and 14.0 <= h_ < 15.0:
            continue
        kD = int(P["dmap"][ic])
        if kD < 2 or (var.get("bias", 1) and P["bm"][kD] != d):   # daily bias ze svicky [PDF Daily bias]
            continue
        k4 = int(P["c4"][ic])
        if var.get("h4", 1):
            if k4 < 1 or S4["tr"][k4] != d:                 # 4H struktura ve smeru [PDF Trend]
                continue
            b4 = int(S4["bos_i"][k4])
            if b4 < 0 or t[ic] - t[int(T["H4"]["en"][b4])] > 30 * DAY:
                continue
        sv = float(ev["st"][q])
        si = int(Xb["en"][sti])
        if var["poi"] != "zadne" and not in_poi(P, k, var["poi"], d, sv, si):
            continue
        # konec killzone
        j = ic
        lim = min(n - 2, ic + 600)
        while j < lim and kz[0][0] <= cz[j] < kz[0][1]:
            j += 1
        i_kz_end = j
        # vstup
        spr = M["spr"]
        fill, E = -1, np.nan
        if var["entry"] == "gp":
            s0 = int(Xb["st"][sti])
            ext = M["h"][s0:ic + 1].max() if d == 1 else M["l"][s0:ic + 1].min()
            for i in range(ic + 1, i_kz_end + 1):
                lvl = ext - d * 0.618 * abs(ext - sv)
                Ei = lvl + d * spr[i]
                if (d == 1 and M["l"][i] <= lvl) or (d == -1 and M["h"][i] >= lvl):
                    fill, E = i, Ei
                    break
                if (d == 1 and M["l"][i] < sv) or (d == -1 and M["h"][i] > sv):
                    break
                ext = max(ext, M["h"][i]) if d == 1 else min(ext, M["l"][i])
        else:
            fv = None
            i_ev = int(ev["i"][q])
            for r in range(sti + 2, i_ev + 1):
                if d == 1 and Xb["l"][r] > Xb["h"][r - 2]:
                    fv = (Xb["h"][r - 2], Xb["l"][r])
                if d == -1 and Xb["h"][r] < Xb["l"][r - 2]:
                    fv = (Xb["h"][r], Xb["l"][r - 2])
            if fv is None:
                continue
            lvl = 0.5 * (fv[0] + fv[1])
            for i in range(ic + 1, i_kz_end + 1):
                if (d == 1 and M["l"][i] <= lvl) or (d == -1 and M["h"][i] >= lvl):
                    fill, E = i, lvl + d * spr[i]
                    break
                if (d == 1 and M["l"][i] < sv) or (d == -1 and M["h"][i] > sv):
                    break
        if fill < 0:
            continue
        atrD = D["a"][kD - 1]
        if not atrD > 0:
            continue
        fx = mk in ("EURUSD", "GBPUSD")
        mn = 6 * M["pip"] if fx else 0.086 * atrD
        mx = 15 * M["pip"] if fx else 0.21 * atrD
        SL = sv
        risk = (E - SL) * d
        if risk <= 0:
            continue
        if risk < mn:
            SL, risk = E - d * mn, mn
        if risk > mx:
            continue
        # TP
        if var["tp"] == "2.5R":
            Rt = 2.5
        else:
            cands = []
            s_day = int(D["st"][kD])
            hi_t, lo_t = M["h"][s_day:fill].max(initial=-np.inf), M["l"][s_day:fill].min(initial=np.inf)
            lv = [D["h"][kD - 1] if d == 1 else D["l"][kD - 1], P["vw"][kD - 1], P["poc"][kD - 1]]
            ah = P["asia"].get(day)
            if ah is not None and h_ >= 6:
                lv.append(ah[0] if d == 1 else ah[1])
            for x in lv:
                if not np.isfinite(x):
                    continue
                untouched = (x > hi_t) if d == 1 else (x < lo_t)
                if untouched and (x - E) * d >= 2.0 * risk:
                    cands.append((x - E) * d / risk)
            if not cands:
                continue
            Rt = min(min(cands), 5.0)
        TP = E + d * Rt * risk
        # konec dne 22:00 Praha
        e_day = fill
        lim = min(n - 1, fill + 1440)
        while e_day < lim and czday[e_day] == day and cz[e_day] < 22.0:
            e_day += 1
        s = X.sim(M, d, E, SL, TP, fill, fill, 0, e_day)
        if not s:
            continue
        r = X.rec(M, "F12", X.vn(var), d, s, Rt, atrD, "den")
        r.update(sl_dist=risk, tp_dist=Rt * risk, cz=float(cz[fill]))
        if info:
            r.update(E_=s["E"], SL_=SL, TP_=TP, sv=sv, si=si, ic=ic)
        out.append(r)
        busy = s["ex"]
        per_day[day] = per_day.get(day, 0) + 1
    return out


GRID = [dict(k=k, poi=p, tf=tf, entry=e, tp=tp) for k in KS for p in ("zona", "balanc", "obe")
        for tf in ("M5", "M1") for e in ("gp", "fvg") for tp in ("prob", "2.5R")]

if __name__ == "__main__":
    mks = sys.argv[1:] or MARKETS
    for mk in mks:
        rows = []
        for var in GRID:
            rows += run_market(mk, var)
        df = pd.DataFrame(rows)
        df.to_pickle(os.path.join(D12, f"f12_{mk}{X.SUF}.pkl"))
        print(mk, len(df), flush=True)
