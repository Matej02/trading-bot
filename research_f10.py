"""
F10 - entry modely mentoru FM presne podle PDF (viz F10_PLAN.md), simulace na M1.
Spusteni: py research_f10.py [strategie ...]   (bez argumentu vse)  -> research_data/f10/f10_<strat>.pkl
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f8 as F

D10 = os.path.join("research_data", "f10")
OOS = pd.Timestamp("2022-01-01", tz="UTC").value // 10**9
FX = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
IDX = ["NAS100mini", "SPX500mini", "US30mini", "GER_30mini"]
NEWS_DAYS = None
NOCOST = os.environ.get("F10_NOCOST") == "1"
SUF = "_nc" if NOCOST else ""


# ---------------------------------------------------------------- data
def load1(mk):
    df = pd.read_pickle(os.path.join(D10, f"{mk}_M1.pkl"))
    t = df.t.to_numpy(np.int64)
    utc = pd.to_datetime(t, unit="s", utc=True)
    ny = utc.tz_convert("America/New_York").tz_localize(None).as_unit("s").asi8
    lon_h = utc.tz_convert("Europe/London").hour.to_numpy()
    lt = ny + 7 * 3600
    b = L.BROKER[mk]
    c = df.c.to_numpy(float)
    sbh = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0)
    if b["group"] == "FOREX":
        spr = sbh[lon_h]
    else:
        ref = float(np.median(c[-30 * 1440:]))
        spr = sbh[lon_h] / ref * c
    day = lt // 86400
    wd = (day + 3) % 7
    crypto = b["group"] == "CRYPTO" or mk in ("BTCUSD", "ETHUSD")
    new_day = np.r_[True, day[1:] != day[:-1]]
    cum_sw = np.cumsum(np.where(crypto, 1, np.where(wd == 3, 3, 1)) * new_day).astype(np.float64)
    M = dict(mk=mk, t=t, ny=ny, lt=lt, day=day, hm=(lt % 86400) / 3600.0,  # hm = hodina od 17:00 NY (0..24)
             o=df.o.to_numpy(float), h=df.h.to_numpy(float), l=df.l.to_numpy(float), c=c, v=df.v.to_numpy(float),
             spr=spr, tick=10.0 ** -b["digits"], cum_sw=cum_sw, swl=b["swapLong"], sws=b["swapShort"],
             pip=b.get("pip") or 10.0 ** -(b["digits"] - 1), fx=b["group"] == "FOREX")
    M["hend"] = np.zeros(len(c), np.bool_)
    if NOCOST:
        M["spr"] = np.zeros_like(spr)
        M["swl"] = M["sws"] = 0.0
    return M


def agg(M, key):
    chg = np.r_[True, key[1:] != key[:-1]]
    st = np.flatnonzero(chg)
    en = np.r_[st[1:] - 1, len(key) - 1]
    h = np.maximum.reduceat(M["h"], st)
    l = np.minimum.reduceat(M["l"], st)
    c = M["c"][en]
    T = dict(o=M["o"][st], h=h, l=l, c=c, st=st, en=en, a=L.wilder_atr(h, l, c, 14), hm=M["hm"][st],
             day=M["day"][st], v=np.add.reduceat(M["v"], st))
    return T


def tfs(M):
    ar = np.arange(len(M["c"]))
    m1 = dict(o=M["o"], h=M["h"], l=M["l"], c=M["c"], st=ar, en=ar, hm=M["hm"], day=M["day"], v=M["v"])
    return {"M1": m1, "M5": agg(M, M["t"] // 300), "M15": agg(M, M["t"] // 900), "H1": agg(M, M["lt"] // 3600),
            "H4": agg(M, M["lt"] // 14400), "D1": agg(M, M["day"])}


def day_end_idx(M):
    """Pro kazdou M1 svicku index posledni svicky jejiho dne."""
    st = np.flatnonzero(np.r_[True, M["day"][1:] != M["day"][:-1]])
    en = np.r_[st[1:] - 1, len(M["day"]) - 1]
    return st, en


def news_days():
    global NEWS_DAYS
    if NEWS_DAYS is None:
        s = set()
        for lst in (L.FOMC, L.NFP, L.CPI):
            for d in lst:
                s.add(pd.Timestamp(d).value // 10**9 // 86400)
        NEWS_DAYS = s
    return NEWS_DAYS


def bias_arrays(D):
    n = len(D["c"])
    bv = np.zeros(n, np.int8)
    bm = np.zeros(n, np.int8)
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
        if D["c"][k - 1] != D["o"][k - 1]:
            bm[k] = 1 if D["c"][k - 1] > D["o"][k - 1] else -1
    return bv, bm


def sim(M, d, E, SL, TP, i0, i_valid, kind, i_texit, tp1=np.nan, f1=0.0, be=False):
    n = len(M["c"])
    if i0 >= n - 1:
        return None
    if not np.isnan(tp1) and f1 > 0:
        a1, q1, a2, q2 = tp1, f1, TP, 1.0 - f1
    elif be:
        a1, q1, a2, q2 = E + d * abs(E - SL), 1e-9, TP, 1 - 1e-9
    else:
        a1, q1, a2, q2 = TP, 1.0, np.nan, np.nan
    sw = M["swl"] if d == 1 else M["sws"]
    r = L.sim_trade(M["o"], M["h"], M["l"], M["c"], M["spr"], M["tick"], i0, min(i_valid, n - 2), kind, d, E, SL,
                    a1, q1, a2, q2, np.full(1, np.nan), 0, min(i_texit, n - 1), np.nan, M["hend"], 0, 0.0,
                    M["cum_sw"], sw)
    if r[0] == 0:
        return None
    return dict(R=r[1], fi=r[2], ex=r[3], why=r[4], E=r[6], risk=r[7])


def rec(M, strat, var, d, s, Rt, atrD, kind_exit):
    return dict(mk=M["mk"], strat=strat, var=var, d=d, t=int(M["t"][s["fi"]]), fi=s["fi"], ex=s["ex"], R=s["R"],
                why=s["why"], Rt=Rt, risk_atrD=s["risk"] / atrD if atrD > 0 else np.nan, hm=float(M["hm"][s["fi"]]),
                exit_rule=kind_exit, hold=s["ex"] - s["fi"])


def closed_map(T, n):
    """Pro M1 index i: index posledni UZAVRENE svicky TF (-1 zadna)."""
    idx = np.searchsorted(T["st"], np.arange(n), side="right") - 1
    return np.where(np.arange(n) == T["en"][idx], idx, idx - 1)


def m1_first(M, i0, i1, cond_low=None, cond_high=None):
    """Prvni M1 index v [i0, i1] kde low <= cond_low nebo high >= cond_high."""
    if i0 > i1:
        return -1
    seg = slice(i0, i1 + 1)
    if cond_low is not None:
        k = np.flatnonzero(M["l"][seg] <= cond_low)
    else:
        k = np.flatnonzero(M["h"][seg] >= cond_high)
    return i0 + k[0] if len(k) else -1


# ---------------------------------------------------------------- 1 Veselovsky
def s_veselovsky(M, T, var):
    tfk = var["tf"]
    X = T[tfk]
    D = T["D1"]
    bv, _ = bias_arrays(D)
    nd = news_days()
    dst, den = day_end_idx(M)
    out = []
    W = 12 if tfk == "M5" else 30
    for k in range(2, len(D["c"])):
        b = int(bv[k])
        if b == 0:
            continue
        i_d0, i_d1 = D["st"][k], D["en"][k]
        if (M["ny"][i_d0] + 7 * 3600) // 86400 in nd or int(D["day"][k]) in nd:
            continue
        hm = M["hm"][i_d0:i_d1 + 1]
        asia = (hm >= 3) & (hm < 9)
        if asia.sum() < 60:
            continue
        aH = M["h"][i_d0:i_d1 + 1][asia].max()
        aL = M["l"][i_d0:i_d1 + 1][asia].min()
        o7 = np.flatnonzero(hm >= 7)
        if not len(o7):
            continue
        nydo = M["o"][i_d0 + o7[0]]
        pdh, pdl = D["h"][k - 1], D["l"][k - 1]
        atrD = D["a"][k - 1]
        tgt = pdh if b == 1 else pdl
        # svicky TF tohoto dne
        xs = np.searchsorted(X["st"], i_d0)
        xe = np.searchsorted(X["st"], i_d1, side="right") - 1
        for kz0, kz1 in ((9, 12), (15, 18)):
            liq = min(aL, pdl) if b == 1 else max(aH, pdh)
            liqs = [aL, pdl] if b == 1 else [aH, pdh]
            done = False
            for j in range(xs + W, xe):
                if not (kz0 <= X["hm"][j] < kz1):
                    continue
                if b == 1:
                    swept = any(X["l"][j] < q for q in liqs) and X["l"][j] < nydo
                else:
                    swept = any(X["h"][j] > q for q in liqs) and X["h"][j] > nydo
                if not swept:
                    continue
                # MSS
                lvl = X["h"][j - W:j + 1].max() if b == 1 else X["l"][j - W:j + 1].min()
                ext = X["l"][j] if b == 1 else X["h"][j]
                for m in range(j + 1, min(j + W + 1, xe)):
                    ext = min(ext, X["l"][m]) if b == 1 else max(ext, X["h"][m])
                    if (X["c"][m] - lvl) * b > 0:
                        # noha a FVG
                        lo = j + np.argmin(X["l"][j:m + 1]) if b == 1 else j + np.argmax(X["h"][j:m + 1])
                        legE = X["h"][lo:m + 1].max() if b == 1 else X["l"][lo:m + 1].min()
                        fv = []
                        for q in range(lo + 2, m + 1):
                            if b == 1 and X["l"][q] > X["h"][q - 2]:
                                fv.append((X["h"][q - 2], X["l"][q]))
                            if b == -1 and X["h"][q] < X["l"][q - 2]:
                                fv.append((X["h"][q], X["l"][q - 2]))
                        if not fv:
                            break
                        leg = abs(legE - ext)
                        if var["entry"] == "fib":
                            E = legE - b * 0.382 * leg
                        else:
                            E = fv[0][1] if b == 1 else fv[0][0]
                        buf = 2 * M["pip"] if M["fx"] else 0.03 * atrD
                        SL = ext - b * buf
                        risk = (E - SL) * b
                        if risk <= 0 or (tgt - E) * b < 2 * risk:
                            break
                        tp1 = aH if b == 1 else aL
                        f1 = 0.5 if (tp1 - E) * b >= 0.5 * risk and (tgt - tp1) * b > 0 else 0.0
                        i0 = X["en"][m] + 1
                        kzend = i_d0 + np.flatnonzero(hm < kz1)[-1]
                        s = sim(M, b, E, SL, tgt, i0, kzend, 0, i_d1, tp1 if f1 else np.nan, f1)
                        if s:
                            out.append(rec(M, "VES", vn(var), b, s, (tgt - E) * b / risk, atrD, "den"))
                        done = True
                        break
                break
            if done:
                continue
    return out


# ---------------------------------------------------------------- 2 Kimmel
def mss_after(X, j, b, W, xe):
    """MSS do W svicek po j: close za max/min W svicek pred j; vraci (m, ext) nebo (-1, nan)."""
    lvl = X["h"][max(0, j - W):j + 1].max() if b == 1 else X["l"][max(0, j - W):j + 1].min()
    ext = X["l"][j] if b == 1 else X["h"][j]
    for m in range(j + 1, min(j + W + 1, xe + 1)):
        ext = min(ext, X["l"][m]) if b == 1 else max(ext, X["h"][m])
        if (X["c"][m] - lvl) * b > 0:
            return m, ext
    return -1, np.nan


def s_kimmel(M, T, var):
    X, Q, D = T["M5"], T["M15"], T["D1"]
    bv, bm = bias_arrays(D)
    B = bv if var["bias"] == "V" else bm
    out = []
    zones = F.find_zones(Q, 2.0) if var["model"] == 2 else []
    zq = closed_map(Q, len(M["c"]))
    for k in range(2, len(D["c"])):
        b = int(B[k])
        if b == 0:
            continue
        i_d0, i_d1 = D["st"][k], D["en"][k]
        atrD = D["a"][k - 1]
        xs = np.searchsorted(X["st"], i_d0)
        xe = np.searchsorted(X["st"], i_d1, side="right") - 1
        win = [j for j in range(xs, xe + 1) if 16.5 <= X["hm"][j] < 19]  # 09:30-12:00 NY
        if not win:
            continue
        if var["model"] == 1:
            lvl = D["l"][k - 1] if b == 1 else D["h"][k - 1]
            for j in win:
                if (b == 1 and X["l"][j] <= lvl) or (b == -1 and X["h"][j] >= lvl):
                    m, ext = mss_after(X, j, b, 6, win[-1])
                    if m < 0:
                        break
                    i0 = X["en"][m] + 1
                    E0 = M["o"][i0] if i0 < len(M["o"]) else np.nan
                    risk = 1.25 * abs(E0 - ext)
                    SL = E0 - b * risk
                    TP = E0 + b * var["R"] * risk
                    s = sim(M, b, E0, SL, TP, i0, i0, 1, i_d1)
                    if s:
                        out.append(rec(M, "KIM", vn(var), b, s, var["R"], atrD, "den"))
                    break
        else:
            # aktivni M15 zony stejneho smeru, dotek v okne, pak 2 BOS na M5
            act = [z for z in zones if z["d"] == b and Q["en"][z["act"]] < X["st"][win[0]] and
                   Q["en"][min(z["inv"], len(Q["en"]) - 1)] > X["st"][win[0]] and
                   (X["c"][win[0] - 1] - z["prox"]) * b > 0]
            if not act:
                continue
            z = max(act, key=lambda z: z["prox"] * b)
            tj = -1
            for j in win:
                if (b == 1 and X["l"][j] <= z["prox"]) or (b == -1 and X["h"][j] >= z["prox"]):
                    tj = j
                    break
            if tj < 0:
                continue
            m1, ext = mss_after(X, tj, b, 6, win[-1])
            if m1 < 0:
                continue
            m2, _ = mss_after(X, m1 + 1, b, 6, win[-1])
            if m2 < 0:
                continue
            i0 = X["en"][m2] + 1
            if i0 >= len(M["o"]):
                continue
            E0 = M["o"][i0]
            SL = z["dist"] - b * 0.1 * Q["a"][z["act"]]
            risk = (E0 - SL) * b
            if risk <= 0:
                continue
            TP = E0 + b * var["R"] * risk
            s = sim(M, b, E0, SL, TP, i0, i0, 1, i_d1)
            if s:
                out.append(rec(M, "KIM", vn(var), b, s, var["R"], atrD, "den"))
    return out


# ---------------------------------------------------------------- 3 Patek
def s_patek(M, T, var):
    X, H4, D = T["M5"], T["H4"], T["D1"]
    n = len(M["c"])
    _, _, tr4 = F.last_swing(H4["h"], H4["l"], 2)
    c4 = closed_map(H4, n)
    ph, pl = L.pivots(X["h"], X["l"], 3)
    out = []
    lastH = lastL = prevL = prevH = np.nan
    busy = -1
    dst, den = day_end_idx(M)
    dmap = np.searchsorted(dst, np.arange(n), side="right") - 1
    for j in range(4, len(X["c"])):
        p = j - 3
        if ph[p]:
            prevH, lastH = lastH, X["h"][p]
        if pl[p]:
            prevL, lastL = lastL, X["l"][p]
        hm = X["hm"][j]
        if not ((10 <= hm < 13) or (16.5 <= hm < 19)):
            continue
        i_end = X["en"][j]
        if i_end <= busy or not np.isfinite(prevL) or not np.isfinite(prevH):
            continue
        k4 = c4[i_end]
        if k4 < 0:
            continue
        b = int(tr4[k4])
        if b == 0:
            continue
        if b == 1 and lastL > prevL and X["c"][j] > lastH and X["c"][j - 1] <= lastH:
            SL = lastL - M["tick"] * 10
        elif b == -1 and lastH < prevH and X["c"][j] < lastL and X["c"][j - 1] >= lastL:
            SL = lastH + M["tick"] * 10
        else:
            continue
        i0 = i_end + 1
        if i0 >= n:
            break
        E0 = M["o"][i0]
        risk = (E0 - SL) * b
        if risk <= 0:
            continue
        if var["tp"] == "2R":
            TP, Rt = E0 + b * 2 * risk, 2.0
        else:  # predchozi H4 high/low (leva strana)
            look = slice(max(0, k4 - 30), k4 + 1)
            cand = H4["h"][look].max() if b == 1 else H4["l"][look].min()
            Rt = (cand - E0) * b / risk
            if Rt < 1.5:
                continue
            Rt = min(Rt, 5.0)
            TP = E0 + b * Rt * risk
        atrD = D["a"][max(0, int(np.searchsorted(D["st"], i0, side="right")) - 2)]
        s = sim(M, b, E0, SL, TP, i0, i0, 1, den[dmap[i0]])
        if s:
            out.append(rec(M, "PAT", vn(var), b, s, Rt, atrD, "den"))
            busy = s["ex"]
    return out


# ---------------------------------------------------------------- 4 Srajer day trading
WIN_SR = ((9.5, 10.5), (11.5, 12.5), (14.5, 17.0))  # 02:30-03:30, 04:30-05:30, 07:30-10:00 NY


def s_srajer(M, T, var):
    Q, H4, D = T["M15"], T["H4"], T["D1"]
    n = len(M["c"])
    Zq = F.find_zones(Q, var["k"])
    Z4 = F.find_zones(H4, 2.0)
    sh4, sl4, _ = F.last_swing(H4["h"], H4["l"], 3)
    phq, plq = L.pivots(Q["h"], Q["l"], 3)
    dst, den = day_end_idx(M)
    dmap = np.searchsorted(dst, np.arange(n), side="right") - 1
    out = []
    for z in Zq:
        d = z["d"]
        ia = Q["en"][z["act"]]
        lo, hi = sorted((z["prox"], z["dist"]))
        par = None
        for w in Z4:
            if w["d"] != d:
                continue
            wa, wi = H4["en"][w["act"]], H4["en"][min(w["inv"], len(H4["en"]) - 1)]
            wlo, whi = sorted((w["prox"], w["dist"]))
            if wa <= ia < wi and lo <= whi and hi >= wlo:
                par = w
                break
        if par is None:
            continue
        # premium / discount: 4H swing range v dobe aktivace
        k4 = int(np.searchsorted(H4["st"], ia, side="right")) - 1
        rh, rl = sh4[k4], sl4[k4]
        if not (np.isfinite(rh) and np.isfinite(rl)) or rh <= rl:
            continue
        mid = 0.5 * (rh + rl)
        if (d == 1 and z["prox"] > mid) or (d == -1 and z["prox"] < mid):
            continue
        # prvni dotek do 5 dni
        i_last = min(Q["en"][min(z["inv"], len(Q["en"]) - 1)], ia + 5 * 1440, n - 2)
        fi = m1_first(M, ia + 1, i_last, cond_low=z["prox"] if d == 1 else None, cond_high=z["prox"] if d == -1 else None)
        if fi < 0:
            continue
        hm = M["hm"][fi]
        if not any(a <= hm < b for a, b in WIN_SR):
            continue
        # likvidita: mezi aktivaci a dotekem cena prorazila M15 pivot lezici mezi zonou a cenou
        qa, qf = z["act"], int(np.searchsorted(Q["st"], fi, side="right")) - 1
        swept = False
        for p in range(qa + 1, qf - 2):
            if d == 1 and plq[p] and Q["l"][p] > z["prox"] and M["l"][Q["en"][p + 3]:fi + 1].min() < Q["l"][p]:
                swept = True
                break
            if d == -1 and phq[p] and Q["h"][p] < z["prox"] and M["h"][Q["en"][p + 3]:fi + 1].max() > Q["h"][p]:
                swept = True
                break
        if not swept:
            continue
        E = z["prox"]
        SL = z["dist"] - d * 0.05 * Q["a"][z["act"]]
        risk = (E - SL) * d
        TP = E + d * var["R"] * risk
        atrD = D["a"][max(0, int(np.searchsorted(D["st"], fi, side="right")) - 2)]
        s = sim(M, d, E, SL, TP, fi, fi, 0, den[dmap[fi]])
        if s:
            out.append(rec(M, "SRA", vn(var), d, s, var["R"], atrD, "den"))
    return out


# ---------------------------------------------------------------- 5 Mucka
def s_mucka(M, T, var):
    X, D = T["M5"], T["D1"]
    _, bm = bias_arrays(D)
    out = []
    for k in range(2, len(D["c"])):
        i_d0, i_d1 = D["st"][k], D["en"][k]
        atrD = D["a"][k - 1]
        if not atrD > 0:
            continue
        hm = M["hm"][i_d0:i_d1 + 1]
        asia = (hm >= 3) & (hm < 7)  # 20:00-00:00 NY
        if asia.sum() < 60:
            continue
        aH = M["h"][i_d0:i_d1 + 1][asia].max()
        aL = M["l"][i_d0:i_d1 + 1][asia].min()
        cap = 35 * M["pip"] if M["mk"] == "EURUSD" else 0.47 * atrD
        if aH - aL > cap:
            continue
        mn = (6 * M["pip"]) if M["mk"] == "EURUSD" else 0.08 * atrD
        mx = (20 * M["pip"]) if M["mk"] == "EURUSD" else 0.27 * atrD
        xs = np.searchsorted(X["st"], i_d0)
        xe = np.searchsorted(X["st"], i_d1, side="right") - 1
        used = False
        for j in range(xs + 6, xe):
            hmj = X["hm"][j]
            if not ((10 <= hmj < 12) or (14.5 <= hmj < 18)):
                continue
            for d, sw in ((-1, X["h"][j] > aH), (1, X["l"][j] < aL)):
                if not sw or used:
                    continue
                if var["bias"] and bm[k] != d:
                    continue
                m, ext = mss_after(X, j, d, 6, xe)
                if m < 0:
                    continue
                used = True
                i0 = X["en"][m] + 1
                if i0 >= len(M["o"]) - 1:
                    break
                tgt = aH if d == 1 else aL
                if var["entry"] == "trh":
                    E, kind, iv = M["o"][i0], 1, i0
                else:
                    legE = X["h"][j:m + 1].max() if d == 1 else X["l"][j:m + 1].min()
                    E, kind, iv = legE - d * 0.618 * abs(legE - ext), 0, min(i0 + 24 * 5, i_d1)
                SL = ext
                risk = (E - SL) * d
                if risk < mn:
                    SL, risk = E - d * mn, mn
                if risk > mx:
                    break
                if var["tp"] == "asie":
                    Rt = (tgt - E) * d / risk
                    if Rt < 1.0:
                        break
                    TP = tgt
                else:
                    Rt, TP = 2.0, E + d * 2 * risk
                s = sim(M, d, E, SL, TP, i0, iv, kind, i_d1)
                if s:
                    out.append(rec(M, "MUC", vn(var), d, s, Rt, atrD, "den"))
                break
            if used:
                break
    return out


# ---------------------------------------------------------------- 6 Valchar
def s_valchar(M, T, var):
    H4, D = T["H4"], T["D1"]
    n = len(M["c"])
    o, h, l, c = H4["o"], H4["h"], H4["l"], H4["c"]
    sh, sl, _ = F.last_swing(h, l, 3)
    ph, pl = L.pivots(h, l, 3)
    _, _, trD = F.last_swing(D["h"], D["l"], 2)
    out = []
    used = set()
    for k in range(5, len(c) - 1):
        for d in (1, -1):
            lvl = sh[k] if d == 1 else sl[k]
            if not np.isfinite(lvl) or (c[k] - lvl) * d <= 0 or (c[k - 1] - lvl) * d > 0 or (d, lvl) in used:
                continue
            used.add((d, lvl))
            kd = int(np.searchsorted(D["st"], H4["st"][k], side="right")) - 2
            if kd < 0 or trD[kd] != d:
                continue
            ob = -1
            for j in range(k - 1, max(k - 11, 0), -1):
                if (c[j] - o[j]) * d < 0:
                    ob = j
                    break
            if ob < 0:
                continue
            top, bot = (h[ob], l[ob]) if d == 1 else (l[ob], h[ob])
            hgt = abs(top - bot)
            a4 = H4["a"][k]
            if not a4 > 0 or hgt <= 0:
                continue
            # POC impulzu z M1 tick volume
            s0, s1 = H4["st"][ob], H4["en"][k]
            bw = a4 / 20
            lo_p = M["l"][s0:s1 + 1].min()
            nb = int((M["h"][s0:s1 + 1].max() - lo_p) / bw) + 1
            hist = np.zeros(nb)
            mid = 0.5 * (M["h"][s0:s1 + 1] + M["l"][s0:s1 + 1])
            np.add.at(hist, ((mid - lo_p) / bw).astype(int).clip(0, nb - 1), M["v"][s0:s1 + 1])
            poc = lo_p + (hist.argmax() + 0.5) * bw
            if not (min(top, bot) - 0.25 * hgt <= poc <= max(top, bot) + 0.25 * hgt):
                continue
            E, SL = top, bot - d * 0.1 * a4
            risk = (E - SL) * d
            if risk <= 0:
                continue
            # dotek do 60 H4 svicek; cil = high/low od OB do doteku (predchozi high = protejsi likvidita)
            i_last = H4["en"][min(k + 60, len(c) - 1)]
            fi = m1_first(M, H4["en"][k] + 1, i_last, cond_low=E if d == 1 else None, cond_high=E if d == -1 else None)
            if fi < 0:
                continue
            imp = M["h"][s0:fi].max() if d == 1 else M["l"][s0:fi].min()
            Rt = (imp - E) * d / risk
            if not (1.8 <= Rt <= 6):
                continue
            kf = int(np.searchsorted(H4["st"], fi, side="right")) - 1
            if var["liq"]:
                ok = False
                for p in range(k + 1, kf - 2):
                    if d == 1 and pl[p] and l[p] > E and M["l"][H4["en"][p + 3]:fi + 1].min() < l[p]:
                        ok = True
                        break
                    if d == -1 and ph[p] and h[p] < E and M["h"][H4["en"][p + 3]:fi + 1].max() > h[p]:
                        ok = True
                        break
                if not ok:
                    continue
            atrD = D["a"][max(kd, 0)]
            s = sim(M, d, E, SL, imp, fi, fi, 0, fi + 30 * 1440)
            if s:
                out.append(rec(M, "VAL", vn(var), d, s, Rt, atrD, "30d"))
    return out


# ---------------------------------------------------------------- 7 Hakimi
def s_hakimi(M, T, var):
    H4, D = T["H4"], T["D1"]
    o, h, l, c = H4["o"], H4["h"], H4["l"], H4["c"]
    ph, pl = L.pivots(h, l, 3)
    _, _, tr = F.last_swing(h, l, 2)
    Z = F.find_zones(H4, 1.5)
    out = []
    lastL = lastH = np.nan
    iL = iH = -1
    done = set()
    for k in range(10, len(c) - 1):
        p = k - 3
        if pl[p]:
            lastL, iL = l[p], p
        if ph[p]:
            lastH, iH = h[p], p
        b = int(tr[k])
        if b == 0 or iL < 0 or iH < 0:
            continue
        if b == 1 and iH > iL:
            lo_, hi_, i_start = lastL, lastH, iH
        elif b == -1 and iL > iH:
            lo_, hi_, i_start = lastH, lastL, iL  # pro short: lo_ = high (start), hi_ = low (konec)
        else:
            continue
        key = (b, i_start)
        if key in done:
            continue
        done.add(key)
        leg = abs(hi_ - lo_)
        if leg <= 0:
            continue
        f50, f618, f75 = hi_ - b * 0.5 * leg, hi_ - b * 0.618 * leg, hi_ - b * 0.75 * leg
        zl, zh = sorted((f50, f75))
        conf, sl_cand = False, lo_
        for z in Z:
            if z["d"] != b or not (z["act"] <= k < z["inv"]):
                continue
            a_, b_ = sorted((z["prox"], z["dist"]))
            if a_ <= zh and b_ >= zl:
                conf, sl_cand = True, z["dist"]
                break
        if not conf and var["fvg"]:
            s_leg = iL if b == 1 else iH
            for q in range(s_leg + 2, i_start + 1):
                g0, g1 = (h[q - 2], l[q]) if b == 1 else (h[q], l[q - 2])
                if g1 > g0 and g0 <= zh and g1 >= zl:
                    conf, sl_cand = True, lo_
                    break
        if not conf:
            continue
        E = f618
        SL = sl_cand - b * 0.1 * H4["a"][k]
        risk = (E - SL) * b
        Rt = (hi_ - E) * b / risk if risk > 0 else 0
        if Rt < 2.5:
            continue
        i_last = H4["en"][min(k + 30, len(c) - 1)]
        fi = m1_first(M, H4["en"][k] + 1, i_last, cond_low=E if b == 1 else None, cond_high=E if b == -1 else None)
        if fi < 0:
            continue
        seg = slice(H4["en"][k] + 1, fi)
        if fi > H4["en"][k] + 1 and ((b == 1 and M["h"][seg].max() >= hi_) or (b == -1 and M["l"][seg].min() <= hi_)):
            continue
        kd = int(np.searchsorted(D["st"], fi, side="right")) - 2
        s = sim(M, b, E, SL, hi_, fi, fi, 0, fi + 20 * 1440)
        if s:
            out.append(rec(M, "HAK", vn(var), b, s, Rt, D["a"][max(kd, 0)], "20d"))
    return out


# ---------------------------------------------------------------- 8 Hvezda (D1 z H1, 26 trhu)
def hvezda_all(var):
    out = []
    for mk in F.MARKETS:
        H = F.load(mk)
        Dd = F.resample(H, H["day"])
        o, h, l, c = Dd["o"], Dd["h"], Dd["l"], Dd["c"]
        _, _, trd = F.last_swing(h, l, 3)
        Z = F.find_zones(Dd, 1.5)
        for z in Z:
            d = z["d"]
            if var["trend"] and z["tr"] != d:
                continue
            t0 = -1
            for k in range(z["act"] + 1, min(z["inv"], z["act"] + 120, len(c))):
                if (d == 1 and l[k] <= z["prox"]) or (d == -1 and h[k] >= z["prox"]):
                    t0 = k
                    break
            if t0 < 0:
                continue
            ck = -1
            for k in range(t0, min(t0 + 3, len(c) - 1)):
                if (c[k] - z["dist"]) * d < 0:
                    break
                body = abs(c[k] - o[k])
                lw = min(o[k], c[k]) - l[k]
                uw = h[k] - max(o[k], c[k])
                if d == 1:
                    hammer = body > 0 and lw >= 2 * body and uw <= body and c[k] > z["dist"]
                    engulf = c[k] > o[k] and o[k - 1] > c[k - 1] and c[k] >= o[k - 1] and o[k] <= c[k - 1]
                else:
                    hammer = body > 0 and uw >= 2 * body and lw <= body and c[k] < z["dist"]
                    engulf = c[k] < o[k] and o[k - 1] < c[k - 1] and c[k] <= o[k - 1] and o[k] >= c[k - 1]
                if hammer or engulf:
                    ck = k
                    break
            if ck < 0:
                continue
            i0 = Dd["en"][ck] + 1
            if i0 >= len(H["c"]) - 1:
                continue
            E0 = H["o"][i0] + (H["spr"][i0] if d == 1 else 0)
            hgt = abs(z["prox"] - z["dist"])
            SL = z["dist"] - d * (0.2 * hgt if var["sl20"] else 0) - d * 0.05 * z["atr"]
            risk = (E0 - SL) * d
            if risk <= 0:
                continue
            TP = E0 + d * var["R"] * risk
            sw = H["swl"] if d == 1 else H["sws"]
            tp1 = E0 + d * risk
            r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], i0, i0, 1, d, E0, SL, tp1, 1e-9, TP,
                            1 - 1e-9, np.full(1, np.nan), 0, min(i0 + 30 * 24, len(H["c"]) - 1), np.nan, H["hend"], 0,
                            0.0, H["cum_sw"], sw)
            if r[0]:
                out.append(dict(mk=mk, strat="HVE", var=vn(var), d=d, t=int(H["t"][r[2]]), R=r[1], why=r[4], Rt=var["R"],
                                risk_atrD=risk / z["atr"], fi=r[2], ex=r[3], hm=np.nan, exit_rule="30d", hold=r[3] - r[2]))
        print("HVE", mk, len(out), flush=True)
    return out


# ---------------------------------------------------------------- spousteni
def vn(var):
    return " ".join(f"{k}={v}" for k, v in var.items())


STRATS = {
    "VES": (s_veselovsky, FX + ["XAUUSD"], [dict(tf=t, entry=e) for t in ("M5", "M1") for e in ("fib", "fvg")]),
    "KIM": (s_kimmel, IDX, [dict(model=m, bias=b, R=r) for m in (1, 2) for b in ("V", "M") for r in (2, 3)]),
    "PAT": (s_patek, ["NAS100mini", "SPX500mini", "GBPUSD", "XAUUSD"], [dict(tp=t) for t in ("2R", "H4")]),
    "SRA": (s_srajer, FX + ["XAUUSD"], [dict(k=k, R=r) for k in (1.5, 2.0) for r in (2.5, 3.0)]),
    "MUC": (s_mucka, ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "XAUUSD", "NAS100mini"],
            [dict(entry=e, tp=t, bias=b) for e in ("trh", "gp") for t in ("asie", "2R") for b in (False, True)]),
    "VAL": (s_valchar, FX + ["XAUUSD", "XAGUSD"] + IDX, [dict(liq=q) for q in (True, False)]),
    "HAK": (s_hakimi, ["XAUUSD", "XAGUSD", "NAS100mini"] + FX, [dict(fvg=f) for f in (False, True)]),
}


def run(name):
    if name == "HVE":
        rows = []
        for v in [dict(trend=t, sl20=s, R=r) for t in (True, False) for s in (False, True) for r in (2, 3)]:
            rows += hvezda_all(v)
        pd.DataFrame(rows).to_pickle(os.path.join(D10, "f10_HVE.pkl"))
        return
    fn, mks, vars_ = STRATS[name]
    rows = []
    for mk in mks:
        M = load1(mk)
        T = tfs(M)
        for v in vars_:
            r = fn(M, T, v)
            rows += r
        print(name, mk, len(rows), flush=True)
    pd.DataFrame(rows).to_pickle(os.path.join(D10, f"f10_{name}{SUF}.pkl"))


if __name__ == "__main__":
    for nm in (sys.argv[1:] or list(STRATS) + ["HVE"]):
        run(nm)
