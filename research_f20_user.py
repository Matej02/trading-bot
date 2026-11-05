"""
F20 - obecna strategie uzivatele (cast A Doplnujicich pravidel) podle F20_PLAN.md:
4H bias (stroj F12) -> 15m SFP (knot za nevybranym 15m swingem, zavreni zpet) v S/D zone 4H/15m nebo na POC predchoziho dne
-> FRVP do svicky SFP (250 radku, VA 70 %; POC/VAH/VAL v knotu 2 ze 3 / 3 ze 3) + objem nad SMA50 -> vstup trhem / po 1m MSS /
limitem na POC svicky -> SL za knot +0,1 ATR15 -> TP 2R / opacny 15m swing / nahy denni POC; konec 22:00 Praha.
Kazdy kandidat SFP se simuluje pro vsechny kombinace vstupu a TP; filtry (bias, poi, vp, vol) a "jedna pozice naraz" se
skladaji az ve vyhodnoceni (research_f20_eval.py).
Spusteni: py research_f20_user.py [trh ...] -> research_data/f20/f20_<trh>.pkl ; F10_NOCOST=1 -> _nc
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f10 as X
import research_f12 as F12

F12.KS = (1.5,)
K = 1.5
D20 = os.path.join("research_data", "f20")
os.makedirs(D20, exist_ok=True)
MARKETS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "NAS100mini", "SPX500mini", "GER_30mini"]
PIV_N = 5            # 15m swing = pivot +-5 svicek ("jasne viditelny swing" [A2])
PIV_AGE = 192        # swing nejvys 2 dny stary
ROWS = 250           # FRVP row size [A7]
ENTRIES = ("close", "mss", "poc")
TPS = ("2R", "liq", "poc")
DAY = 86400


def real_spread(mk):
    if not X.NOCOST:
        return None
    X.NOCOST = False
    try:
        return X.load1(mk)["spr"].copy()
    finally:
        X.NOCOST = True


def end22_index(cz, czday):
    """Pro kazdy M1 index posledni index stejneho prazskeho dne pred 22:00 (-1 kdyz uz je po 22:00)."""
    n = len(cz)
    out = np.full(n, -1, np.int64)
    ok = cz < 22.0
    df = pd.DataFrame({"d": czday, "i": np.arange(n), "ok": ok})
    last = df[df.ok].groupby("d").i.max()
    lm = last.reindex(czday).to_numpy()
    lm = np.where(np.isnan(lm), -1, lm).astype(np.int64)
    out[:] = np.where(ok, lm, -1)
    return out


def candidates(mk):
    P = F12.prep(mk)
    M, T, cz, czday, D = P["M"], P["T"], P["cz"], P["czday"], P["D"]
    Q = T["M15"]
    S = P["S"][K]
    S4, S15 = S["H4"], S["M15"]
    n, nq = len(M["c"]), len(Q["c"])
    t = M["t"]
    ph, pl = L.pivots(Q["h"], Q["l"], PIV_N)
    vma = pd.Series(Q["v"]).rolling(50).mean().shift(1).to_numpy()
    lows, highs = [], []           # aktivni nevybrane swingy: (level, index)
    out = []
    for q in range(PIV_N + 1, nq):
        p = q - 1 - PIV_N
        if pl[p]:
            lows.append((Q["l"][p], p))
        if ph[p]:
            highs.append((Q["h"][p], p))
        lows = [x for x in lows if q - x[1] <= PIV_AGE]
        highs = [x for x in highs if q - x[1] <= PIV_AGE]
        a = Q["a"][q - 1]
        o_, h_, l_, c_ = Q["o"][q], Q["h"][q], Q["l"][q], Q["c"][q]
        bl, bh = min(o_, c_), max(o_, c_)
        found = []
        sw_l = [lv for lv, _ in lows if l_ < lv - 0.05 * a]
        if sw_l and bl > max(sw_l):
            found.append((1, max(sw_l)))
        sw_h = [lv for lv, _ in highs if h_ > lv + 0.05 * a]
        if sw_h and bh < min(sw_h):
            found.append((-1, min(sw_h)))
        # vybrane swingy (i bez SFP) uz neplati
        lows = [x for x in lows if not l_ < x[0]]
        highs = [x for x in highs if not h_ > x[0]]
        if len(found) != 1 or not a > 0:
            continue
        d, lvl = found[0]
        ic = int(Q["en"][q])
        if ic + 2 >= n:
            continue
        hc = cz[ic] + 1.0 / 60
        if not (9.0 <= hc < 20.0):
            continue
        day = int(czday[ic])
        if day in P["news"] and (12.5 <= hc < 15.5 or 18.0 <= hc < 21.0):
            continue
        a15 = Q["a"][q]
        s0, e0 = int(Q["st"][q]), int(Q["en"][q])
        seg = slice(s0, e0 + 1)
        si = s0 + int(np.argmin(M["l"][seg]) if d == 1 else np.argmax(M["h"][seg]))
        sv = l_ if d == 1 else h_
        # bias
        k4 = int(P["c4"][ic])
        b4 = k4 >= 1 and S4["tr"][k4] == d and S4["bos_i"][k4] >= 0 and \
            t[ic] - t[int(T["H4"]["en"][int(S4["bos_i"][k4])])] <= 30 * DAY
        b15 = S15["tr"][q] == d and S15["bos_i"][q] >= 0 and t[ic] - t[int(Q["en"][int(S15["bos_i"][q])])] <= 5 * DAY
        # POI
        pz = F12.in_poi(P, K, "zona", d, sv, si)
        kD = int(P["dmap"][ic])
        pp = False
        if kD >= 1 and np.isfinite(P["poc"][kD - 1]):
            x = P["poc"][kD - 1]
            pp = (sv - 0.1 * a15 <= x <= bl) if d == 1 else (bh <= x <= sv + 0.1 * a15)
        out.append(dict(q=q, d=d, lvl=lvl, ic=ic, si=si, sv=sv, a15=a15, day=day, hc=hc, kD=kD, b4=bool(b4), b15=bool(b15),
                        pz=bool(pz), pp=bool(pp), vol=bool(Q["v"][q] > vma[q]) if np.isfinite(vma[q]) else False,
                        bl=bl, bh=bh, opp=[lv for lv, _ in (highs if d == 1 else lows)]))
    if not out:
        return P, out
    # FRVP do svicky SFP
    qs = np.array([r["q"] for r in out])
    rs, re_ = Q["st"][qs].astype(np.int64), Q["en"][qs].astype(np.int64)
    bws = (Q["h"][qs] - Q["l"][qs]) / ROWS
    poc, vah, val = L.range_profiles(M["h"], M["l"], M["v"], rs, re_, bws, M["tick"], 0.70)
    for r, p_, h_, v_ in zip(out, poc, vah, val):
        lv3 = np.array([p_, h_, v_])
        r["vp"] = int(np.sum(lv3 < r["bl"])) if r["d"] == 1 else int(np.sum(lv3 > r["bh"]))
        r["vpoc"] = float(p_)
    return P, out


def naked_poc_R(P, kD, ic, E, risk, d):
    """TP = nejblizsi neotestovany denni POC za 5 dni ve smeru, >= 1,5 R, strop 6 R [A4, Volume nPOC s7]; None = zadny."""
    M, D = P["M"], P["D"]
    cand = []
    for k in range(max(0, kD - 5), kD):
        x = P["poc"][k]
        if not np.isfinite(x) or (x - E) * d < 1.5 * risk:
            continue
        s1, s2 = int(D["en"][k]) + 1, ic + 1
        if s2 > s1 and ((d == 1 and M["h"][s1:s2].max() >= x) or (d == -1 and M["l"][s1:s2].min() <= x)):
            continue
        cand.append((x - E) * d / risk)
    return min(min(cand), 6.0) if cand else None


def live_signals(mk):
    """Vybrana varianta (vyber jen na vyvoji): bias=4H15 poi=zona vp=2 vol=0 entry=close tp=poc.
    Vraci [(konec svicky SFP v UTC, d, SL, TP)]; stejna pravidla jako run_market, E = close svicky SFP (+spread u longu).
    Kontrolu SL >= 3x spread dela az runner s zivym spreadem."""
    P, C = candidates(mk)
    M = P["M"]
    out = []
    for r in C:
        if not (r["b4"] and r["b15"] and r["pz"] and r["vp"] >= 2):
            continue
        d, ic, a15 = r["d"], r["ic"], r["a15"]
        SL = r["sv"] - d * 0.1 * a15
        E = M["c"][ic] + (M["spr"][ic] if d == 1 else 0.0)
        risk = (E - SL) if d == 1 else (SL + M["spr"][ic] - E)
        if not risk > 0 or risk > 4 * a15:
            continue
        Rt = naked_poc_R(P, r["kD"], ic, E, risk, d)
        if Rt is None:
            continue
        out.append((int(M["t"][ic]) + 60, d, float(SL), float(E + d * Rt * risk)))
    return out


def run_market(mk):
    P, C = candidates(mk)
    M, T, cz, czday, D = P["M"], P["T"], P["cz"], P["czday"], P["D"]
    n = len(M["c"])
    spr_chk = real_spread(mk)
    spr_chk = M["spr"] if spr_chk is None else spr_chk
    e22 = end22_index(cz, czday)
    ev = P["S"][K]["M1"]["ev"]
    ev_i, ev_d = ev["i"], ev["d"]
    rows = []
    for r in C:
        d, ic, a15 = r["d"], r["ic"], r["a15"]
        SL = r["sv"] - d * 0.1 * a15
        for entry in ENTRIES:
            i0 = ic + 1
            if entry == "close":
                kind, iv = 1, i0
                E = M["o"][i0] + M["spr"][i0] + M["tick"] if d == 1 else M["o"][i0] - M["tick"]
            elif entry == "mss":
                q0 = int(np.searchsorted(ev_i, ic + 1))
                j = -1
                for qq in range(q0, len(ev_i)):
                    if ev_i[qq] > ic + 60:
                        break
                    if ev_d[qq] == d:
                        j = int(ev_i[qq])
                        break
                if j < 0 or j + 1 >= n:
                    continue
                seg = slice(ic + 1, j + 1)
                if (d == 1 and M["l"][seg].min() <= SL) or (d == -1 and M["h"][seg].max() >= SL):
                    continue
                i0 = j + 1
                kind, iv = 1, i0
                E = M["o"][i0] + M["spr"][i0] + M["tick"] if d == 1 else M["o"][i0] - M["tick"]
            else:
                E = r["vpoc"]
                if not np.isfinite(E) or (d == 1 and not (SL < E < M["c"][ic])) or (d == -1 and not (M["c"][ic] < E < SL)):
                    continue
                kind, iv = 0, ic + 60
            if i0 >= n - 1:
                continue
            i_x = int(e22[i0])
            if i_x < i0:
                continue
            risk = (E - SL) * d if d == 1 else (SL + M["spr"][i0] - E)
            if not (risk > 0) or risk < 3 * spr_chk[i0] or risk > 4 * a15:
                continue
            for tp in TPS:
                if tp == "2R":
                    Rt = 2.0
                elif tp == "liq":
                    cand = [(lv - E) * d / risk for lv in r["opp"] if (lv - E) * d >= 1.5 * risk]
                    if not cand:
                        continue
                    Rt = min(min(cand), 6.0)
                else:
                    Rt = naked_poc_R(P, r["kD"], ic, E, risk, d)
                    if Rt is None:
                        continue
                TP = E + d * Rt * risk
                s = X.sim(M, d, E, SL, TP, i0, iv, kind, i_x)
                if not s:
                    continue
                rows.append(dict(mk=mk, d=d, t=int(M["t"][s["fi"]]), fi=s["fi"], ex=s["ex"], R=s["R"], why=s["why"], Rt=Rt,
                                 entry=entry, tp=tp, b4=r["b4"], b15=r["b15"], pz=r["pz"], pp=r["pp"], vp=r["vp"],
                                 vol=r["vol"], day=r["day"], cz=float(cz[s["fi"]]), sl_dist=risk, tp_dist=Rt * risk,
                                 q=r["q"], oos=bool(M["t"][s["fi"]] >= X.OOS)))
    return pd.DataFrame(rows), len(C)


if __name__ == "__main__":
    for mk in sys.argv[1:] or MARKETS:
        df, nc = run_market(mk)
        df.to_pickle(os.path.join(D20, f"f20_{mk}{X.SUF}.pkl"))
        print(mk, "kandidatu SFP", nc, "| simulaci", len(df), flush=True)
