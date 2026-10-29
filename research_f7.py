"""
F7 - test 6 strategii z dokumentu uzivatele "Trading bot - 6 strategii (SMC + Volume Profile)" (2026-10-28).

PLAN STANOVENY PREDEM (pred prvnim spustenim; pravidla podle dokumentu, odchylky vypsane nize):
  Data: krypto BTC/ETH/SOL - M1 z Binance 2022-09 az 2026-10, VTF M1 / M3 / M5 / M15.
        forex EURUSD/GBPUSD/USDJPY, komodity XAUUSD/XAGUSD/CRUDE_OIL - MT5 jen M15 (terminal da max
        100 000 svicek), 2021/22 az 2025-10 -> VTF jen M15, profily z M15 svicek.
  Naklady: spread brokera podle hodiny (kovy a krypto skalovane cenou), swapy, skluz 1 tick; SOL bez brokera
        -> naklady jako ETH (relativne k cene).
  Rozdeleni: vyvoj = prvnich ~60 % (do 2025-02-28), out-of-sample = od 2025-03-01, vyhodnoceno jednou.
  Vyber na vyvoji: pro kazdou strategii a tridu aktiv varianta s nejvyssi expectancy pri n >= 30
        (mrizka: VTF x typ vstupu CE / market x 1 parametr strategie).
  Prah pro postup (dokument, OOS po nakladech, vsechny trhy tridy dohromady): n >= 100, expectancy >= 0,15 R,
        PF >= 1,3, 95. percentil DD z Monte Carla <= 15 R, ziskova ctvrtleti >= 60 %, o >= 0,1 R lepsi nez
        nahodne vstupy (stejny smer, SL v ATR, TP v R, delka drzeni a denni doba, nahodny den).
  Navic: walk-forward (12 mesicu vyber varianty, 3 mesice test, posun 3 mesice) a ablace filtru u nejlepsich.
  Odchylky od dokumentu: kalendar zprav pribliznny (FOMC/NFP/CPI); po TP1 se zbytek (vcetne runneru S2)
        trailuje spolecne; SFP vzdy na M15 (S4 na VTF); S/D zona plati nejvys 120 svicek H4 a "cerstva" =
        do zpresnene zony cena dojde do 12 svicek H4 od prvniho doteku puvodni zony; limit S2B, S3 a S5
        plati 10 svicek VTF, okno MSS S5 12 svicek; pro M1 jen pesimisticke filly z M1 svicek (bez ticku).
"""
import os
import sys
import time

import numpy as np
import pandas as pd
from numba import njit

import f7_lib as L
from f7_lib import displacement, find_mss, profile_hist, sim_trade, smooth_nodes, value_area

sys.stdout.reconfigure(line_buffering=True)
OUT = L.D7
SPLIT_T = int(pd.Timestamp("2025-03-01").timestamp())
# (trh, zakladni TF): dokument BTC/ETH/SOL + rozsireni krypta pro vetsi vzorek; forex/komodity z MT5 na M15
# (VTF M15, ~4 roky) a navic na M5 (VTF M5/M15, jen ~1,5 roku - jen orientacne)
MARKETS = [(m, None) for m in ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "BNBUSD", "ADAUSD", "DOGEUSD", "LTCUSD", "LINKUSD",
                                "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "XAGUSD", "CRUDE_OIL"]] +           [(m, "M5") for m in ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "XAGUSD", "CRUDE_OIL"]] +           [(m, "M1") for m in ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "XAGUSD", "CRUDE_OIL"]]  # MT5 M1 od 2020 (2026-10-29)


def in_kz(h):
    return 2.0 <= h < 5.0 or 7.0 <= h < 10.0


def base_ext(B, s, e, d):
    """Index zakladni svicky s extremem (long: nejnizsi low, short: nejvyssi high) v rozsahu s..e."""
    return s + int(np.argmin(B["l"][s:e + 1])) if d == 1 else s + int(np.argmax(B["h"][s:e + 1]))


def friday_close(B, i):
    """Forex a komodity: vikend - zavrit v patek do 15:00 NY. Krypto bez omezeni (vraci velke cislo)."""
    if B["crypto"]:
        return 10 ** 12
    ny = B["ny"][i]
    day = ny // 86400
    target = (day + (4 - (day + 3) % 7) % 7) * 86400 + 15 * 3600
    if target <= ny:
        target += 7 * 86400
    return L.idx_ge(B, target - (ny - B["t"][i]))


def S(i, d, ext, ext_i, K, P, texit, **kw):
    x = dict(i=int(i), d=int(d), ext=float(ext), ext_i=int(ext_i), K=int(K), P=int(P), texit=int(texit))
    x.update(kw)
    return x


# ---------------------------------------------------------------- likvidita a zony

@njit(cache=True)
def pool_sweeps(level, side, created, until, s15, e15, h15, l15, c15, a15, ix15, sfp2):
    """Pro kazdy pool prvni svicka M15, ktera ho vybere (za uroven aspon o 0,05 ATR), a svicka SFP
    (close zpet a hloubka <= 0,5 ATR; sfp2 = navrat do 2 svicek). Vybrany pool prestava platit."""
    m = len(level)
    nb = len(s15)
    sweep = np.full(m, -1, np.int64)
    trig = np.full(m, -1, np.int64)
    for p in range(m):
        if created[p] >= len(ix15):
            continue
        b = ix15[created[p]]
        if s15[b] < created[p]:
            b += 1
        found = -1
        while b < nb and e15[b] <= until[p]:
            A = a15[b]
            if A > 0 and ((side[p] == 1 and h15[b] >= level[p] + 0.05 * A) or (side[p] == -1 and l15[b] <= level[p] - 0.05 * A)):
                found = b
                break
            b += 1
        if found < 0:
            continue
        sweep[p] = found
        A = a15[found]
        if side[p] == 1:
            if c15[found] < level[p] and h15[found] - level[p] <= 0.5 * A:
                trig[p] = found
            elif sfp2 and found + 1 < nb and c15[found + 1] < level[p] and max(h15[found], h15[found + 1]) - level[p] <= 0.5 * A:
                trig[p] = found + 1
        else:
            if c15[found] > level[p] and level[p] - l15[found] <= 0.5 * A:
                trig[p] = found
            elif sfp2 and found + 1 < nb and c15[found + 1] > level[p] and level[p] - min(l15[found], l15[found + 1]) <= 0.5 * A:
                trig[p] = found + 1
    return sweep, trig


def build_pools(B):
    """Pooly likvidity: (uroven, strana +1 nad / -1 pod, vaha, vznik, platnost do, druh).
    Druh 1 PDH/PDL (2), 2 PWH/PWL (3), 3 EQH/EQL (2), 4 Asie (1), 5 Londyn (1), 6 pdVAH/pdVAL, 7 kompozit VAH/VAL."""
    T = B["T"]
    D = T["D1"]
    nd = len(D["s"])
    n = len(B["t"])
    rows = []
    for d in range(1, nd):
        rows += [(D["h"][d - 1], 1, 2, D["s"][d], D["e"][d], 1), (D["l"][d - 1], -1, 2, D["s"][d], D["e"][d], 1)]
        if not np.isnan(D["vah"][d - 1]):
            rows += [(D["vah"][d - 1], 1, 0, D["s"][d], D["e"][d], 6), (D["val"][d - 1], -1, 0, D["s"][d], D["e"][d], 6)]
        if not np.isnan(D["cvah"][d]):
            rows += [(D["cvah"][d], 1, 0, D["s"][d], D["e"][d], 7), (D["cval"][d], -1, 0, D["s"][d], D["e"][d], 7)]
    wk = (D["key"] + 3) // 7
    st = np.flatnonzero(np.r_[True, wk[1:] != wk[:-1]])
    en = np.r_[st[1:] - 1, nd - 1]
    for q in range(1, len(st)):
        a, b = st[q - 1], en[q - 1]
        cs, ce = D["s"][st[q]], D["e"][en[q]]
        rows += [(D["h"][a:b + 1].max(), 1, 3, cs, ce, 2), (D["l"][a:b + 1].min(), -1, 3, cs, ce, 2)]
    asia = {}
    for kind, (h0, h1) in ((4, (20, 24)), (5, (2, 5))):
        idx = np.flatnonzero((B["nyh"] >= h0) & (B["nyh"] < h1))
        dd = B["di"][idx]
        brk = np.flatnonzero(np.r_[True, dd[1:] != dd[:-1]])
        bend = np.r_[brk[1:] - 1, len(idx) - 1]
        for a, b in zip(brk, bend):
            i0, i1, d = idx[a], idx[b], dd[a]
            if i1 + 1 > D["e"][d]:
                continue
            hi, lo = B["h"][i0:i1 + 1].max(), B["l"][i0:i1 + 1].min()
            rows += [(hi, 1, 1, i1 + 1, D["e"][d], kind), (lo, -1, 1, i1 + 1, D["e"][d], kind)]
            if kind == 4:
                asia[d] = (hi, lo, i1 + 1)
    H1 = T["H1"]
    N = H1["N"]
    for side, piv, arr in ((1, H1["ph"], H1["h"]), (-1, H1["pl"], H1["l"])):
        P = np.flatnonzero(piv)
        for ai, j in enumerate(P):
            conf = j + N
            if conf >= len(H1["e"]) - 1:
                break
            A = H1["a"][j]
            if not A > 0:
                continue
            for q in P[max(0, ai - 40):ai][::-1]:
                if j - q > 120:
                    break
                if j - q < 5 or abs(arr[j] - arr[q]) > 0.1 * A:
                    continue
                lvl = max(arr[j], arr[q]) if side == 1 else min(arr[j], arr[q])
                if side == 1 and H1["h"][q + 1:j].max() > lvl:
                    continue
                if side == -1 and H1["l"][q + 1:j].min() < lvl:
                    continue
                c0 = H1["e"][conf] + 1
                rows.append((lvl, side, 2, c0, min(L.idx_ge(B, B["t"][c0] + 5 * 86400), n - 1), 3))
                break
    a = np.array(rows, dtype=float)
    PL = dict(lev=a[:, 0], side=a[:, 1].astype(np.int64), w=a[:, 2].astype(np.int64), cr=a[:, 3].astype(np.int64),
              un=a[:, 4].astype(np.int64), kind=a[:, 5].astype(np.int64))
    M = T["M15"]
    PL["sw"], PL["trig"] = pool_sweeps(PL["lev"], PL["side"], PL["cr"], PL["un"], M["s"], M["e"], M["h"], M["l"], M["c"], M["a"], M["ix"], False)
    PL["swt"] = np.where(PL["sw"] >= 0, M["s"][np.maximum(PL["sw"], 0)], 10 ** 12)
    B["asia"] = asia
    return PL


def nearest_pool(PL, i, d, price, kinds, wmin=0):
    """Nejblizsi aktivni nevybrany pool ve smeru d od ceny (cil TP)."""
    m = ((PL["side"] == d) & (PL["cr"] <= i) & (PL["un"] >= i) & (PL["swt"] > i) & np.isin(PL["kind"], kinds)
         & (PL["w"] >= wmin) & ((PL["lev"] - price) * d > 0))
    if not m.any():
        return np.nan
    x = PL["lev"][m]
    return float(x.min() if d == 1 else x.max())


@njit(cache=True)
def disp_fixed(o, h, l, c, a, rv, s0, k, d, rv_thr):
    """Displacement s pevnym zacatkem s0 a koncem k (odchod ze zakladny S/D)."""
    n = len(c)
    A = a[k]
    if not (A > 0) or s0 < 2:
        return -1
    body = (c[k] - o[k]) * d
    rng = h[k] - l[k]
    if rng <= 0 or body < A or body < 0.6 * rng:
        return -1
    opp = 0
    rs = 0.0
    path = 0.0
    for j in range(s0, k + 1):
        if (c[j] - o[j]) * d < 0:
            opp += 1
        if np.isnan(rv[j]):
            return -1
        rs += rv[j]
        path += abs(c[j] - c[j - 1])
    if opp > 1 or (c[k] - o[s0]) * d < 2.0 * A or path <= 0 or abs(c[k] - c[s0 - 1]) / path < 0.6 or rs / (k - s0 + 1) <= rv_thr:
        return -1
    for j in range(min(k + 1, n - 1), s0, -1):
        gap = (l[j] - h[j - 2]) if d == 1 else (l[j - 2] - h[j])
        if gap >= 0.25 * A:
            return j
    return -1


@njit(cache=True)
def sd_zones(o, h, l, c, a, rv, sh1, sl1):
    """S/D zony H4: zakladna 1-4 svicky (rozsah <= 0,7 ATR, telo <= 50 %), odchod = displacement hned za ni,
    cena se vzdali >= 3x vysku zakladny. Vraci pole (smer, proximal, distal, vznik, skore, zac. zakladny, konec odchodu)."""
    n = len(c)
    zd = np.zeros(n, np.int64)
    zp = np.zeros(n)
    zq = np.zeros(n)
    zc = np.zeros(n, np.int64)
    zs = np.zeros(n, np.int64)
    zb = np.zeros(n, np.int64)
    zk = np.zeros(n, np.int64)
    ze = np.zeros(n, np.int64)
    cnt = 0
    for b in range(20, n - 2):
        A = a[b]
        if not A > 0:
            continue
        nb = 0
        for q in range(b, b - 4, -1):
            rng = h[q] - l[q]
            if rng <= 0.7 * A and abs(c[q] - o[q]) <= 0.5 * rng:
                nb += 1
            else:
                break
        if nb == 0:
            continue
        bs = b - nb + 1
        top = -1e18
        bot = 1e18
        bhi = -1e18
        blo = 1e18
        for q in range(bs, b + 1):
            top = max(top, max(o[q], c[q]))
            bot = min(bot, min(o[q], c[q]))
            bhi = max(bhi, h[q])
            blo = min(blo, l[q])
        height = bhi - blo
        for d in (1, -1):
            for k in range(b + 1, min(b + 6, n - 1)):
                fj = disp_fixed(o, h, l, c, a, rv, b + 1, k, d, 1.0)
                if fj < 0:
                    continue
                if d == 1:
                    away = np.max(h[b + 1:k + 1]) - top
                else:
                    away = bot - np.min(l[b + 1:k + 1])
                if away < 3 * height:
                    continue
                sc = 2 + (1 if nb <= 2 else 0)
                if d == 1:
                    if not np.isnan(sh1[b]) and c[k] > sh1[b]:
                        sc += 1
                    zp[cnt], zq[cnt] = top, min(blo, l[b + 1])
                else:
                    if not np.isnan(sl1[b]) and c[k] < sl1[b]:
                        sc += 1
                    zp[cnt], zq[cnt] = bot, max(bhi, h[b + 1])
                zd[cnt], zc[cnt], zs[cnt], zb[cnt], zk[cnt], ze[cnt] = d, max(k, fj), sc, bs, k, b
                cnt += 1
                break
    return zd[:cnt], zp[:cnt], zq[:cnt], zc[:cnt], zs[:cnt], zb[:cnt], zk[:cnt], ze[:cnt]


def build_zones(B):
    H4 = B["T"]["H4"]
    zd, zp, zq, zc, zs, zb, zk, ze = sd_zones(H4["o"], H4["h"], H4["l"], H4["c"], H4["a"], H4["rv"], H4["sh1"], H4["sl1"])
    n = len(B["t"])
    nh = len(H4["e"])
    cb = H4["e"][zc] + 1
    ub = H4["e"][np.minimum(zc + 120, nh - 1)]
    inval = np.full(len(zd), n, np.int64)
    for z in range(len(zd)):
        seg = H4["c"][zc[z] + 1:min(zc[z] + 121, nh)]
        bad = np.flatnonzero(seg < zq[z]) if zd[z] == 1 else np.flatnonzero(seg > zq[z])
        if len(bad):
            inval[z] = H4["e"][zc[z] + 1 + bad[0]] + 1
    Z = dict(d=zd, prox=zp, dist=zq, ch4=zc, score=zs, bs=zb, k=zk, be=ze, cb=cb, ub=np.minimum(ub, inval - 1), inval=inval)
    return Z


def zone_near(Z, i, d, price, datr):
    """Je cena v aktivni zone smeru d nebo pred ni do 0,5 denniho ATR (S6: supply nad cenou pro long)?"""
    m = (Z["d"] == d) & (Z["cb"] <= i) & (Z["ub"] >= i)
    if not m.any():
        return False
    p, q = Z["prox"][m], Z["dist"][m]
    if d == -1:  # supply nad cenou
        return bool(np.any((price >= p - 0.5 * datr) & (price <= q)))
    return bool(np.any((price <= p + 0.5 * datr) & (price >= q)))


# ---------------------------------------------------------------- spolecne provedeni (vstupni model + simulace)

REJ = {}


def rej(why):
    REJ[why] = REJ.get(why, 0) + 1


def execute(B, setups, vtf, entry, rv_thr=1.0):
    """Sdileny vstupni model a simulace. setups: seznam slovniku z generatoru strategii.
    Duvody zamitnuti se pocitaji v REJ (diagnostika trychtyre)."""
    T = B["T"][vtf]
    n = len(B["t"])
    o, h, l, c, spr, tick = B["o"], B["h"], B["l"], B["c"], B["spr"], B["tick"]
    nan_trail = np.full(n, np.nan)
    trades = []
    busy = -1
    per_day = {}
    for s in sorted(setups, key=lambda x: x["i"]):
        i = s["i"]
        if i <= busy or i >= n - 2 or not B["dok"][i]:
            continue
        dk = (B["day"][i], s["d"]) if s.get("max_side") else B["day"][i]
        if per_day.get(dk, 0) >= s.get("max_day", 99):
            continue
        d = s["d"]
        A = np.nan
        if s.get("direct") and s.get("mkt"):  # koncepty: vstup trhem na otevreni dalsi svicky
            act, kind, SL, valid = i + 1, 1, s["SL"], i + 1
            E = o[act] + spr[act] + tick if d == 1 else o[act] - tick
        elif s.get("direct"):
            E, SL, act, valid, kind = s["E"], s["SL"], i + 1, s["valid"], 0
        else:
            k0 = T["ix"][i] + (1 if T["e"][T["ix"][i]] == i else 0)
            if k0 >= len(T["c"]) - 2:
                continue
            ext_k = T["ix"][s["ext_i"]]
            cancel = s.get("cancel", -np.inf if d == 1 else np.inf)
            k, dec, fj, Ld, ext, ob = find_mss(T["o"], T["h"], T["l"], T["c"], T["a"], T["rv"], T["ph"], T["pl"], T["N"],
                                               k0, s["K"], d, s["ext"], ext_k, cancel, rv_thr)
            if k < 0:
                rej("bez MSS")
                continue
            A = T["a"][dec]
            lo, hi = (T["h"][fj - 2], T["l"][fj]) if d == 1 else (T["h"][fj], T["l"][fj - 2])
            act = T["e"][dec] + 1
            if act >= n - 1:
                continue
            valid = T["e"][min(dec + s["P"], len(T["e"]) - 1)]
            SL = ext - 0.1 * A if d == 1 else ext + 0.1 * A
            kind = 0
            if entry == "ce":
                E = (lo + hi) / 2
            elif entry == "prox":
                E = hi if d == 1 else lo
            elif entry == "ob":
                if ob < 0:
                    continue
                E = T["o"][ob]
            else:
                kind = 1
                E = o[act] + spr[act] + tick if d == 1 else o[act] - tick
        if "sl_beyond" in s:
            SL = min(SL, s["sl_beyond"]) if d == 1 else max(SL, s["sl_beyond"])
        if "sl_cap_lvl" in s:
            SL = max(SL, s["sl_cap_lvl"]) if d == 1 else min(SL, s["sl_cap_lvl"])
        sp = spr[act]
        risk = (E - SL) if d == 1 else (SL + sp - E)
        if risk <= 0:
            rej("SL za vstupem")
            continue
        if risk < 5 * sp:
            rej("SL < 5x spread")
            continue
        if risk > s.get("sl_cap", np.inf):
            rej("SL > strop")
            continue
        if "e_lim" in s and (E - s["e_lim"]) * d > 0:
            rej("vstup ne v discount/premium")
            continue
        if "tp1R" in s:
            tp1 = E + d * s["tp1R"] * risk
        elif "tp1c" in s:
            cands = [x for x in s["tp1c"] if not np.isnan(x) and (x - E) * d > 0]
            if not cands:
                continue
            tp1 = min(cands) if d == 1 else max(cands)
        else:
            tp1 = s["tp1"]
        if np.isnan(tp1) or (tp1 - E) * d < s.get("min1R", 0.0) * risk or (tp1 - E) * d <= 0:
            rej("TP1 moc blizko")
            continue
        tp2 = s.get("tp2", np.nan)
        if "tp2R" in s:
            tp2 = E + d * s["tp2R"] * risk
        if not np.isnan(tp2) and (tp2 - E) * d < s.get("min2R", 0.0) * risk:
            rej("TP2 moc blizko")
            continue
        if not np.isnan(tp2) and (tp2 - tp1) * d <= 0:
            tp2 = np.nan
        if "filt" in s and not np.isnan(s["filt"]) and abs(s["filt"] - E) < s["filtR"] * risk:
            rej("POC moc blizko")
            continue
        texit = s["texit"]
        if texit <= act:
            rej("po casovem vystupu")
            continue
        if s.get("news", True) and L.in_news(B, act):
            rej("zpravy")
            continue
        ttf = s.get("trail_tf")
        trail = B["trail"][ttf][0 if d == 1 else 1] if ttf else nan_trail
        f1 = s.get("f1", 1.0)
        f2 = s.get("f2", 0.0)
        sw = B["swl"] if d == 1 else B["sws"]
        r = sim_trade(o, h, l, c, spr, tick, act, valid, kind, d, E, SL, tp1, f1, tp2, f2, trail, 1 if ttf else 0,
                      texit, s.get("soft", np.nan), B["hend"], s.get("chk", 0), s.get("chkR", 0.0), B["cum_sw"], sw)
        if r[0] == 0:
            rej("limit nevyplnen")
            continue
        rej("OBCHOD")
        _, R, fi, ex, why, mfe, Ef, rk = r
        if np.isnan(A):
            A = B["T"][vtf]["a"][max(B["T"][vtf]["cl"][act], 0)]
        trades.append(dict(t=int(B["t"][fi]), d=d, R=R, why=int(why), mfe=mfe, risk_atr=rk / A if A > 0 else np.nan,
                           tp1R=(tp1 - Ef) * d / rk, tp2R=(tp2 - Ef) * d / rk if not np.isnan(tp2) else np.nan,
                           f1=f1, f2=f2 if not np.isnan(tp2) else 0.0, ttf=ttf or "", hold=int(B["t"][ex] - B["t"][fi]),
                           tag=s.get("tag", "")))
        busy = ex
        per_day[dk] = per_day.get(dk, 0) + 1
    return trades


# ---------------------------------------------------------------- strategie

def setups_s1(B, PL, rv_sfp=1.5, killzone=True, prem=True, K=12):
    """S1 Sweep & Shift: SFP na poolu s vahou >= 2 v killzone, H4 premium/discount, proti H4 jen PWH/PWL."""
    M, H4 = B["T"]["M15"], B["T"]["H4"]
    out = []
    for p in np.flatnonzero((PL["trig"] >= 0) & (PL["w"] >= 2) & np.isin(PL["kind"], (1, 2, 3))):
        m, bsw = PL["trig"][p], PL["sw"][p]
        i = M["e"][m]
        h0 = B["nyh"][M["s"][m]]
        if killzone and not in_kz(h0):
            continue
        if not M["rv"][bsw] >= rv_sfp:
            continue
        d = -PL["side"][p]
        hc = H4["cl"][i]
        if hc < 0 or np.isnan(H4["sh1"][hc]) or np.isnan(H4["sl1"][hc]):
            continue
        mid = (H4["sh1"][hc] + H4["sl1"][hc]) / 2
        if prem and (M["c"][m] - mid) * d > 0:  # short jen v premium, long jen v discount
            continue
        if prem and H4["st"][hc] == -d and PL["w"][p] < 3:
            continue
        if L.in_news(B, i):
            continue
        ei = base_ext(B, M["s"][bsw], i, d)
        ext = B["l"][ei] if d == 1 else B["h"][ei]
        tp2 = nearest_pool(PL, i, d, M["c"][m], (1, 2, 3, 4))
        if np.isnan(tp2):
            continue
        out.append(S(i, d, ext, ei, K, 10, L.exit_idx(B, i, 16, utc_hour=23), cancel=ext, sl_cap=1.5 * M["a"][m],
                     tp1R=2.0, f1=0.5, tp2=tp2, f2=0.5, min2R=2.5, tag="L" if h0 < 6 else "N"))
    return out


def setups_s2(B, PL, Z, variant="B", min_score=3, K=12):
    """S2 zpresnena S/D zona: H4 zona ve smeru D1 struktury, v discount/premium, zpresneni HVN profilu zakladny."""
    H4, D, H1 = B["T"]["H4"], B["T"]["D1"], B["T"]["H1"]
    out = []
    n = len(B["t"])
    for z in np.flatnonzero(Z["score"] >= min_score):
        d = int(Z["d"][z])
        prox, dist = Z["prox"][z], Z["dist"][z]
        cb, ub = Z["cb"][z], Z["ub"][z]
        if cb >= n - 2 or ub <= cb or not B["dok"][cb]:
            continue
        di = B["di"][cb]
        datr = D["a"][di - 1]
        if not datr > 0:
            continue
        bw = max(B["tick"], np.round(datr / 40 / B["tick"]) * B["tick"])
        s0, e0 = H4["s"][Z["bs"][z]], H4["e"][Z["k"][z]]
        hist, b0 = profile_hist(B["h"], B["l"], B["v"], s0, e0, bw)
        sm = np.convolve(hist, np.ones(5) / 5, mode="same")
        lo_z, hi_z = min(prox, dist), max(prox, dist)
        centers = (b0 + np.arange(len(sm)) + 0.5) * bw
        pk = sm.max() if len(sm) else 0
        lm = np.r_[False, (sm[1:-1] >= sm[:-2]) & (sm[1:-1] > sm[2:]), False] if len(sm) >= 3 else np.zeros(len(sm), bool)
        cand = np.flatnonzero(lm & (sm >= 0.5 * pk) & (centers >= lo_z) & (centers <= hi_z))
        if len(cand):
            ctr = centers[cand[np.argmax(sm[cand])]]
        else:
            hb, bb = profile_hist(B["h"], B["l"], B["v"], s0, H4["e"][Z["be"][z]], bw)  # jen svicky zakladny
            ctr = (bb + int(np.argmax(hb)) + 0.5) * bw
        r_lo, r_hi = ctr - 1.5 * bw, ctr + 1.5 * bw
        if (r_hi - r_lo) > 0.6 * (hi_z - lo_z):
            continue
        r_lo, r_hi = max(r_lo, lo_z), min(r_hi, hi_z)
        edge = r_hi if d == 1 else r_lo
        # prvni dotek puvodni a zpresnene zony
        seg_l, seg_h = B["l"][cb:ub + 1], B["h"][cb:ub + 1]
        t_orig = np.flatnonzero(seg_l <= prox) if d == 1 else np.flatnonzero(seg_h >= prox)
        t_ref = np.flatnonzero(seg_l <= edge) if d == 1 else np.flatnonzero(seg_h >= edge)
        if variant == "A":
            i = cb - 1
            if (D["st"][di - 1] != d) or not D["ok"][di]:
                continue
        else:
            if not len(t_ref) or not len(t_orig):
                continue
            i0 = cb + t_orig[0]
            i = cb + t_ref[0]
            if H4["ix"][i] - H4["ix"][i0] > 12:
                continue
            di = B["di"][i]
            if D["st"][di - 1] != d:
                continue
        sh, sl_ = D["sh1"][di - 1], D["sl1"][di - 1]
        if np.isnan(sh) or np.isnan(sl_) or (prox - (sh + sl_) / 2) * d > 0:  # demand v discount / supply v premium
            continue
        price = B["c"][i]
        tp2a = nearest_pool(PL, i, d, price, (1, 2, 3), wmin=2)
        mz = (Z["d"] == -d) & (Z["cb"] <= i) & (Z["ub"] >= i) & ((Z["prox"] - price) * d > 0)
        tp2b = (Z["prox"][mz].min() if d == 1 else Z["prox"][mz].max()) if mz.any() else np.nan
        tp2 = np.nanmin([tp2a, tp2b]) if d == 1 else np.nanmax([tp2a, tp2b])
        texit = min(friday_close(B, i), L.idx_ge(B, B["t"][i] + 20 * 86400))
        chk = 30 * 60 // B["bmin"]
        common = dict(tp1R=2.0, f1=0.4, tp2=tp2, f2=0.4, trail_tf="H1", chk=chk, chkR=1.0, tag=variant)
        if variant == "A":
            if i + 1 >= n:
                continue
            SL = dist - 0.1 * H4["a"][Z["ch4"][z]] * d
            valid = H4["e"][min(Z["ch4"][z] + 20, len(H4["e"]) - 1)]
            out.append(S(i, d, np.nan, i, 0, 0, texit, direct=True, E=edge, SL=SL, valid=min(valid, ub), **common))
        else:
            ei = i
            ext = B["l"][i] if d == 1 else B["h"][i]
            out.append(S(i, d, ext, ei, K, 10, texit, sl_beyond=(r_lo - B["tick"]) if d == 1 else (r_hi + B["tick"]), **common))
    return out


def setups_s3(B, PL, setup="A", vol="low", flat=True, regime=True, K=10):
    """S3 rotace ve Value Area: jen rezim balance, plochy VWAP, London+NY session; A = fade okraje VA po SFP,
    B = pravidlo 80 %. Kill switch: 2 svicky M30 mimo pdVA s RVOL >= 2."""
    M, M30, D = B["T"]["M15"], B["T"]["M30"], B["T"]["D1"]
    out = []
    nd = len(D["s"])
    kill = np.full(nd, 10 ** 12, np.int64)
    m30d = B["di"][M30["s"]]
    vah30, val30 = D["vah"][np.maximum(m30d - 1, 0)], D["val"][np.maximum(m30d - 1, 0)]
    outside = ((M30["c"] > vah30) | (M30["c"] < val30)) & (M30["rv"] >= 2)
    two = outside & np.r_[False, outside[:-1]] & (m30d == np.r_[-1, m30d[:-1]])
    for j in np.flatnonzero(two):
        kill[m30d[j]] = min(kill[m30d[j]], M30["e"][j] + 1)
    if setup == "A":
        for p in np.flatnonzero((PL["trig"] >= 0) & np.isin(PL["kind"], (6, 7))):
            m, bsw = PL["trig"][p], PL["sw"][p]
            i = M["e"][m]
            h0 = B["nyh"][M["s"][m]]
            if not (2 <= h0 < 14) or i >= kill[B["di"][i]]:
                continue
            if (regime and B["regime"][i] != 1) or (flat and not abs(B["slope"][i]) < 0.1):
                continue
            side = PL["side"][p]
            rng = M["h"][bsw] - M["l"][bsw]
            wick = (M["h"][bsw] - max(M["o"][bsw], M["c"][bsw])) if side == 1 else (min(M["o"][bsw], M["c"][bsw]) - M["l"][bsw])
            rv = M["rv"][bsw]
            if vol == "low" and not rv < 1.0:
                continue
            if vol == "abs" and not (rv >= 2.0 and rng > 0 and wick >= 0.5 * rng):
                continue
            if L.in_news(B, i):
                continue
            d = -side
            dd = B["di"][i]
            poc, vah, val = D["poc"][dd - 1], D["vah"][dd - 1], D["val"][dd - 1]
            ei = base_ext(B, M["s"][bsw], i, d)
            ext = B["l"][ei] if d == 1 else B["h"][ei]
            tp2 = (val + 0.1 * M["a"][m]) if d == -1 else (vah - 0.1 * M["a"][m])
            out.append(S(i, d, ext, ei, K, 10, L.exit_idx(B, i, 15, utc_hour=22), filt=poc, filtR=1.2,
                         tp1c=(poc, B["vw"][i]), f1=0.5, tp2=tp2, f2=0.5, tag=f"A{PL['kind'][p]}"))
    else:
        for dd in range(21, nd):
            if not D["ok"][dd]:
                continue
            vah, val, poc = D["vah"][dd - 1], D["val"][dd - 1], D["poc"][dd - 1]
            if np.isnan(vah):
                continue
            DO = D["o"][dd]
            if DO > vah:
                d, edge = -1, vah
            elif DO < val:
                d, edge = 1, val
            else:
                continue
            js = np.flatnonzero(m30d == dd)
            if len(js) < 3:
                continue
            ins = (M30["c"][js] <= vah) & (M30["c"][js] >= val)
            two_in = np.flatnonzero(ins[1:] & ins[:-1])
            if not len(two_in):
                continue
            j2 = js[two_in[0] + 1]
            jend = min(j2 + 6, js[-1])
            a30 = M30["a"][j2]
            s0, e0 = M30["e"][j2] + 1, M30["e"][jend]
            if e0 <= s0:
                continue
            hit = np.flatnonzero(B["h"][s0:e0 + 1] >= edge - 0.1 * a30) if d == -1 else np.flatnonzero(B["l"][s0:e0 + 1] <= edge + 0.1 * a30)
            if not len(hit):
                continue
            i = s0 + hit[0]
            if not (2 <= B["nyh"][i] < 14) or i >= kill[dd] or L.in_news(B, i):
                continue
            ext = B["l"][i] if d == 1 else B["h"][i]
            out.append(S(i, d, ext, i, K, 10, L.exit_idx(B, i, 15, utc_hour=22), tp1=poc, f1=0.5,
                         tp2=(val if d == -1 else vah), f2=0.5, tag="B"))
    return out


@njit(cache=True)
def s4_triggers(vs, ve, vo, vh, vl, vc, va, vrv, vday, vnyh, vsl1, vsh1, vw, sg, slope, regime, h4st, h1st, DOv, pdpoc,
                m15e, m15bos, m15below, m15above, m15day, fe, fd, flo, fhi, fday, need_sfp, need_fvg, slope_thr):
    """S4 spoustece na VTF: po killzone BOS M15 (displacement, RVOL >= 1,5) pullback do pasma VWAP..+1 sigma,
    v pasmu neotestovany FVG z impulzu, SFP pod posledni swing low VTF (RVOL >= 1,5). Short zrcadlove.
    need_sfp=False: spoustec = prvni dotek pasma v pullbacku (parametr dokumentu "povinnost SFP"),
    need_fvg=False: bez podminky FVG v pasmu (ablace)."""
    nv = len(vc)
    ok_k = np.zeros(nv, np.int64)
    ok_d = np.zeros(nv, np.int64)
    cnt = 0
    cur = -1
    p15 = 0
    pf = 0
    bull = bear = invL = invS = False
    bull_t = bear_t = -1
    hod = -1e18
    hod_k = -1
    lod = 1e18
    lod_k = -1
    FL = np.zeros(128)
    FH = np.zeros(128)
    FD = np.zeros(128, np.int64)
    FF = np.zeros(128, np.int64)
    FT = np.full(128, -1, np.int64)
    nf = 0
    trL = -1
    trS = -1
    for k in range(1, nv):
        e = ve[k]
        if vday[k] != cur:
            cur = vday[k]
            bull = bear = invL = invS = False
            bull_t = bear_t = -1
            hod, hod_k, lod, lod_k = -1e18, -1, 1e18, -1
            nf = 0
            trL = trS = -1
        while p15 < len(m15e) and m15e[p15] <= e:
            if m15day[p15] == cur:
                if m15bos[p15] == 1 and not bull:
                    bull, bull_t, hod, hod_k = True, m15e[p15], -1e18, -1
                if m15bos[p15] == -1 and not bear:
                    bear, bear_t, lod, lod_k = True, m15e[p15], 1e18, -1
                if m15below[p15]:
                    invL = True
                if m15above[p15]:
                    invS = True
            p15 += 1
        while pf < len(fe) and fe[pf] <= e:
            if fday[pf] == cur and nf < 128:
                FL[nf], FH[nf], FD[nf], FF[nf], FT[nf] = flo[pf], fhi[pf], fd[pf], fe[pf], -1
                nf += 1
            pf += 1
        for q in range(nf):
            if FT[q] < 0 and vs[k] > FF[q]:
                if (FD[q] == 1 and vl[k] <= FH[q]) or (FD[q] == -1 and vh[k] >= FL[q]):
                    FT[q] = k
        if bull and vs[k] > bull_t and vh[k] > hod:
            hod, hod_k = vh[k], k
        if bear and vs[k] > bear_t and vl[k] < lod:
            lod, lod_k = vl[k], k
        A = va[k]
        if not (A > 0) or vnyh[k] >= 14.0 or regime[k] != 2:
            continue
        if bull and not invL and hod_k >= 0 and hod_k < k and h4st[k] == 1 and h1st[k] == 1 and vc[k] > vw[k] \
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
        if bear and not invS and lod_k >= 0 and lod_k < k and h4st[k] == -1 and h1st[k] == -1 and vc[k] < vw[k] \
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
                    trS = lod_k
    return ok_k[:cnt], ok_d[:cnt]


def setups_s4(B, vtf, need_sfp=True, need_fvg=True, slope_thr=0.1, K=10):
    """S4 VWAP trend pullback."""
    T = B["T"]
    V, M, H1, D = T[vtf], T["M15"], T["H1"], T["D1"]
    e = V["e"]
    h1cl = H1["cl"][e]
    h1st = np.where(h1cl >= 0, H1["st"][np.maximum(h1cl, 0)], 0)
    di = B["di"][e]
    DOv = D["o"][di]
    pdpoc = np.where(di >= 1, D["poc"][np.maximum(di - 1, 0)], np.nan)
    vsl1 = V["sl1"]
    vsh1 = V["sh1"]
    # killzone BOS M15 s displacementem a RVOL >= 1,5
    nm = len(M["c"])
    bos = np.zeros(nm, np.int64)
    bos_e = M["e"].copy()
    for m in np.flatnonzero(M["bk"] == np.arange(nm)):
        if not in_kz(B["nyh"][M["s"][m]]) or not M["rv"][m] >= 1.5:
            continue
        dd = int(M["st"][m])
        Ld, fj = displacement(M["o"], M["h"], M["l"], M["c"], M["a"], M["rv"], m, dd, 1.0)
        if Ld > 0:
            bos[m] = dd
            bos_e[m] = M["e"][max(m, fj)]
    order = np.argsort(bos_e, kind="stable")
    vwe, sge = B["vw"][M["e"]], B["sg"][M["e"]]
    below = M["c"] < vwe - sge
    above = M["c"] > vwe + sge
    m15day = M["day"]
    F = T["M5"] if "M5" in T else M
    j = np.arange(2, len(F["c"]))
    gb = F["l"][j] - F["h"][j - 2]
    gs = F["l"][j - 2] - F["h"][j]
    okb = gb >= 0.25 * F["a"][j]
    oks = gs >= 0.25 * F["a"][j]
    fe = np.r_[F["e"][j[okb]], F["e"][j[oks]]]
    fd = np.r_[np.ones(okb.sum(), np.int64), -np.ones(oks.sum(), np.int64)]
    flo = np.r_[F["h"][j[okb] - 2], F["h"][j[oks]]]
    fhi = np.r_[F["l"][j[okb]], F["l"][j[oks] - 2]]
    fday = np.r_[F["day"][j[okb]], F["day"][j[oks]]]
    fo = np.argsort(fe, kind="stable")
    ks, ds = s4_triggers(V["s"], e, V["o"], V["h"], V["l"], V["c"], V["a"], V["rv"], V["day"], B["nyh"][e], vsl1, vsh1,
                         B["vw"][e], B["sg"][e], B["slope"][e], B["regime"][e], B["h4st"][e], h1st, DOv, pdpoc,
                         bos_e[order], bos[order], below[order], above[order], m15day[order],
                         fe[fo], fd[fo], flo[fo], fhi[fo], fday[fo], need_sfp, need_fvg, slope_thr)
    out = []
    ttf = "M5" if "M5" in T else "M15"
    a15 = L.at_closed(M, M["a"])
    for k, d in zip(ks, ds):
        i = e[k]
        if L.in_news(B, i):
            continue
        dd = B["di"][i]
        ds0 = D["s"][dd]
        if d == 1:
            tp1 = B["h"][ds0:i + 1].max()
            c2 = [x for x in (B["vw"][i] + 2 * B["sg"][i], D["h"][dd - 1]) if x > tp1]
            tp2 = min(c2) if c2 else np.nan
            ext = V["l"][k]
        else:
            tp1 = B["l"][ds0:i + 1].min()
            c2 = [x for x in (B["vw"][i] - 2 * B["sg"][i], D["l"][dd - 1]) if x < tp1]
            tp2 = max(c2) if c2 else np.nan
            ext = V["h"][k]
        ei = base_ext(B, V["s"][k], i, d)
        out.append(S(i, d, ext, ei, K, 6, L.exit_idx(B, i, 15.5, utc_hour=22.5), sl_cap=1.0 * a15[i], tp1=tp1, min1R=1.5,
                     f1=0.5, tp2=tp2, f2=0.5, trail_tf=ttf, max_day=2, tag=""))
    return out


def setups_s5(B, mode="mss", rv_bo=2.0, min_days=3, target="hvn", K=12):
    """S5 breakout z balance pres LVN: balance >= 3 dny, H1 close za okraj s displacementem a RVOL >= 2, BOS,
    akceptace, retest pasma VAH..CE FVG, cil HVN za LVN kompozitu 20 dni."""
    D, H1 = B["T"]["D1"], B["T"]["H1"]
    out = []
    nd = len(D["s"])
    n = len(B["t"])
    be = D["bal_end"]
    for dd in range(25, nd):
        if not D["ok"][dd] or not all(be[dd - q] for q in range(1, min_days + 1)):
            continue
        r = min_days
        while r < 10 and dd - r - 1 >= 0 and be[dd - r - 1]:
            r += 1
        datr = D["a"][dd - 1]
        if not datr > 0:
            continue
        bw = max(B["tick"], np.round(datr / 40 / B["tick"]) * B["tick"])
        hist, b0 = profile_hist(B["h"], B["l"], B["v"], D["s"][dd - r], D["e"][dd - 1], bw)
        if hist.sum() <= 0:
            continue
        p, a, z = value_area(hist, 0.70)
        bvah, bval = (b0 + z + 1) * bw, (b0 + a) * bw
        bhi, blo = D["h"][dd - r:dd].max(), D["l"][dd - r:dd].min()
        hist2, b02 = profile_hist(B["h"], B["l"], B["v"], D["s"][dd - 20], D["e"][dd - 1], bw)
        hv, lv = smooth_nodes(hist2, b02, bw)
        js = np.flatnonzero(H1["day"] == D["key"][dd])
        done = set()
        for j in js:
            if j < 2 or j + 1 >= len(H1["c"]):
                continue
            for d, edge, va_edge in ((1, bhi, bvah), (-1, blo, bval)):
                if d in done or not ((H1["c"][j] - edge) * d > 0 and (H1["c"][j - 1] - edge) * d <= 0):
                    continue
                done.add(d)
                Ld, fj = displacement(H1["o"], H1["h"], H1["l"], H1["c"], H1["a"], H1["rv"], j, d, 1.0)
                if Ld == 0 or not H1["rv"][j] >= rv_bo:
                    continue
                ref = H1["sh1"][j - 1] if d == 1 else H1["sl1"][j - 1]
                if np.isnan(ref) or (H1["c"][j] - ref) * d <= 0 or (H1["c"][j + 1] - va_edge) * d <= 0:
                    continue
                tgt = np.nan
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
                    continue
                acc_end = H1["e"][max(j + 1, fj)]
                lim_end = H1["e"][min(j + 11, len(H1["e"]) - 1)]
                if acc_end + 1 >= n or lim_end <= acc_end:
                    continue
                cap = va_edge - d * 0.5 * H1["a"][j]
                tp2 = va_edge + d * (bhi - blo)
                i_ref = acc_end
                texit = min(friday_close(B, i_ref), int(np.searchsorted(B["day"], B["day"][i_ref] + 3)))  # 3 obchodni dny
                common = dict(tp1=tgt, min1R=1.5, f1=0.5, tp2=tp2, f2=0.5, trail_tf="H1", soft=va_edge, tag=mode)
                if target != "hvn":  # ablace: pevny TP1 2R misto HVN
                    common.pop("tp1")
                    common.update(tp1R=2.0)
                if mode == "direct":
                    out.append(S(acc_end, d, np.nan, acc_end, 0, 0, texit, direct=True, E=band, SL=cap, valid=lim_end, **common))
                else:
                    seg = B["l"][acc_end + 1:lim_end + 1] if d == 1 else B["h"][acc_end + 1:lim_end + 1]
                    hit = np.flatnonzero(seg <= band) if d == 1 else np.flatnonzero(seg >= band)
                    if not len(hit):
                        continue
                    i = acc_end + 1 + hit[0]
                    ext = B["l"][i] if d == 1 else B["h"][i]
                    out.append(S(i, d, ext, i, K, 10, texit, sl_cap_lvl=cap, **common))
    return out


def vtf_sweeps(B, PL, vtf):
    """Sweep a SFP poolu na VTF (S6: "na M15 nebo VTF vznikne SFP")."""
    V = B["T"][vtf]
    sw, tr = pool_sweeps(PL["lev"], PL["side"], PL["cr"], PL["un"], V["s"], V["e"], V["h"], V["l"], V["c"], V["a"], V["ix"], False)
    return V, sw, tr


def setups_s6(B, PL, Z, do_mode="day", rv_sfp=1.5, killzone=True, asia_max=0.4, vsw=None, K=10):
    """S6 Daily Open manipulace (Power of 3): bias D1 + vcerejsi close vs POC, uzka Asie, sweep low Asie / PDL
    se SFP pod DO v killzone, CE FVG pod DO, TP1 high Asie, TP2 PDH."""
    M15, D = B["T"]["M15"], B["T"]["D1"]
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
        h0 = B["nyh"][M["s"][m]]
        if killzone and not in_kz(h0):
            continue
        if not M["rv"][bsw] >= rv_sfp:
            continue
        dd = B["di"][i]
        if dd < 21 or dd not in B["asia"] or not D["ok"][dd]:
            continue
        ah, al, i00 = B["asia"][dd]
        if i00 > i:
            continue
        d = -PL["side"][p]
        key = (dd, d)
        if key not in cache:
            datr = D["a"][dd - 1]
            ok = datr > 0 and D["st"][dd - 1] == d and (D["c"][dd - 1] - D["poc"][dd - 1]) * d > 0 \
                and (ah - al) <= asia_max * datr \
                and pd.Timestamp(int(B["ny"][i00]), unit="s").date() not in B["news_days"] \
                and not zone_near(Z, i00, -d, B["c"][i00], datr)
            cache[key] = ok
        if not cache[key]:
            continue
        DO = D["o"][dd] if do_mode == "day" else B["o"][i00]
        if (M["c"][m] - DO) * d >= 0:
            continue
        ei = base_ext(B, M["s"][bsw], i, d)
        ext = B["l"][ei] if d == 1 else B["h"][ei]
        tp1 = ah if d == 1 else al
        pdx = D["h"][dd - 1] if d == 1 else D["l"][dd - 1]
        tp2 = pdx if (pdx - tp1) * d > 0 else np.nan
        london = h0 < 6
        used.add(p)
        out.append(S(i, d, ext, ei, K, 8, L.exit_idx(B, i, 12 if london else 16), e_lim=DO, tp1=tp1, min1R=1.5, f1=0.5,
                     tp2=tp2, f2=0.5, trail_tf=None if not np.isnan(tp2) else "M15", max_day=1, tag="L" if london else "N"))
    return out


# ---------------------------------------------------------------- beh

# konfigurace (strategie, nazev, parametry generatoru): "doc" = presne podle dokumentu, dalsi = parametry
# z jeho rozsahu k optimalizaci a ablace (vypnuti jednoho filtru, "jadro" = jen spoustec + vstupni model)
CONFIGS = [
    ("S1", "doc", {}), ("S1", "okno20", dict(K=20)), ("S1", "bezRVOL", dict(rv=0.0)), ("S1", "bezKZ", dict(kz=False)),
    ("S1", "bezPrem", dict(prem=False)), ("S1", "jadro", dict(rv=0.0, kz=False, prem=False, K=20)),
    ("S2", "doc", dict(variant="B")), ("S2", "skore2", dict(variant="B", score=2)), ("S2", "okno20", dict(variant="B", K=20)),
    ("S2", "A-limit", dict(variant="A", novtf=True)),
    ("S3", "A-low", dict(setup="A", vol="low")), ("S3", "A-abs", dict(setup="A", vol="abs")), ("S3", "B-80", dict(setup="B")),
    ("S3", "A-bezVWAP", dict(setup="A", vol="any", flat=False)),
    ("S3", "A-jadro", dict(setup="A", vol="any", flat=False, regime=False)), ("S3", "B-okno20", dict(setup="B", K=20)),
    ("S4", "doc", {}), ("S4", "bezSFP", dict(need_sfp=False)), ("S4", "bezFVG", dict(need_fvg=False)),
    ("S4", "sklon005", dict(slope=0.05)), ("S4", "jadro", dict(need_sfp=False, need_fvg=False, slope=0.05)),
    ("S5", "doc", dict(mode="mss")), ("S5", "primo", dict(mode="direct", novtf=True)), ("S5", "RVOL15", dict(mode="mss", rv_bo=1.5)),
    ("S5", "jadro", dict(mode="mss", rv_bo=1.5, min_days=2, target="2R")),
    ("S5", "jadro-primo", dict(mode="direct", rv_bo=1.5, min_days=2, target="2R", novtf=True)),
    ("S6", "doc", dict(do_mode="day")), ("S6", "DO-ny0", dict(do_mode="ny0")), ("S6", "sfpVTF", dict(do_mode="day", sfp_vtf=True)),
    ("S6", "bezRVOL", dict(do_mode="day", rv=0.0)), ("S6", "Asie06", dict(do_mode="day", asia=0.6)),
    ("S6", "jadro", dict(do_mode="day", sfp_vtf=True, rv=0.0, asia=0.6, K=20)),
]


def gen_setups(B, PL, Z, strat, p, vtf, vcache):
    if strat == "S1":
        return setups_s1(B, PL, p.get("rv", 1.5), p.get("kz", True), p.get("prem", True), p.get("K", 12))
    if strat == "S2":
        return setups_s2(B, PL, Z, p["variant"], p.get("score", 3), p.get("K", 12))
    if strat == "S3":
        return setups_s3(B, PL, p["setup"], p.get("vol", "low"), p.get("flat", True), p.get("regime", True), p.get("K", 10))
    if strat == "S4":
        return setups_s4(B, vtf, p.get("need_sfp", True), p.get("need_fvg", True), p.get("slope", 0.1), p.get("K", 10))
    if strat == "S5":
        return setups_s5(B, p["mode"], p.get("rv_bo", 2.0), p.get("min_days", 3), p.get("target", "hvn"), p.get("K", 12))
    vsw = None
    if p.get("sfp_vtf") and vtf != "M15":
        if vtf not in vcache:
            vcache[vtf] = vtf_sweeps(B, PL, vtf)
        vsw = vcache[vtf]
    return setups_s6(B, PL, Z, p["do_mode"], p.get("rv", 1.5), p.get("kz", True), p.get("asia", 0.4), vsw, p.get("K", 10))


def run_market(mk, configs=None, entries=("ce", "mkt"), base=None):
    t0 = time.time()
    B = L.prepare(mk, base)
    label = mk if base is None else f"{mk}@{base}"
    grp = B["cls"] if base is None else f"{B['cls']}@{base}"
    PL = build_pools(B)
    Z = build_zones(B)
    vts = [v for v in ("M1", "M3", "M5", "M15") if v in B["T"]]
    rows = []
    vcache = {}
    nset = {}
    for strat, cfg, p in (configs or CONFIGS):
        dep_vtf = strat == "S4" or (strat == "S6" and p.get("sfp_vtf"))
        su_cache = None
        for vtf in ([vts[-1]] if p.get("novtf") else vts):
            if dep_vtf or su_cache is None:
                su_cache = gen_setups(B, PL, Z, strat, p, vtf, vcache)
                nset[(strat, cfg, vtf if dep_vtf else "")] = len(su_cache)
            su = su_cache
            if "fixR" in p:  # ablace: pevny cil misto strukturalniho
                su = [{k: v for k, v in x.items() if k not in ("tp1", "tp1c", "min1R", "min2R")} for x in su]
                su = [dict(x, tp1R=p["fixR"], f1=1.0, f2=0.0, tp2=np.nan, trail_tf=None) for x in su]
            for en in (["ce"] if p.get("novtf") else entries):
                tr = execute(B, su, vtf, en, rv_thr=p.get("rv_mss", 1.0))
                for x in tr:
                    x.update(strat=strat, cfg=cfg, var=f"{cfg}|{'-' if p.get('novtf') else vtf}|{en}", mk=label, cls=grp,
                             vtf=vtf, entry=en)
                rows += tr
    print(f"  {label}: {len(rows)} obchodu ({time.time() - t0:.0f} s); setupy: " +
          ", ".join(f"{k[0]}-{k[1]}{('@' + k[2]) if k[2] else ''}={v}" for k, v in nset.items()))
    return rows, B


def main():
    allr = []
    only = [a for a in sys.argv[1:] if not a.startswith("-")]
    bases = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--base=")]
    for mk, base in MARKETS:
        if only and mk not in only:
            continue
        if bases and (base or L.MK[mk]["base"]) not in bases:
            continue
        if not os.path.exists(os.path.join(OUT, f"{mk}_{base or L.MK[mk]['base']}.pkl")):
            print("  chybi data", mk, base)
            continue
        rows, _ = run_market(mk, base=base)
        allr += rows
        pd.DataFrame(rows).to_pickle(os.path.join(OUT, f"f7_obchody_{mk}_{base or 'zakl'}.pkl"))
    df = pd.DataFrame(allr)
    print("obchodu celkem", len(df))


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------- nahodne vstupy (test dokumentu, krok 6)

def random_baseline(B, tr, reps=20, seed=1):
    """Ke kazdemu obchodu nahodny vstup: stejny smer, stejny SL v ATR(VTF), TP1/TP2 v R, podily, trailing a
    nejdelsi drzeni; nahodny den ze stejneho obdobi (vyvoj / OOS) a stejna denni doba (+-60 min), vstup trhem."""
    rng = np.random.default_rng(seed)
    n = len(B["t"])
    days = np.unique(B["day"][B["dok"]])
    out = []
    nan_trail = np.full(n, np.nan)
    for _, x in tr.iterrows():
        T = B["T"][x.vtf]
        oos = x.t >= SPLIT_T
        pool = days[(days * 86400 >= SPLIT_T) == oos] if B["crypto"] else days[((days * 86400 - 7 * 3600) >= SPLIT_T) == oos]
        tod = (x.t - (x.t // 86400) * 86400)
        for _ in range(reps):
            dd = rng.choice(pool)
            i = None
            for _try in range(5):
                tt = int(B["t"][int(np.searchsorted(B["day"], dd))] // 86400 * 86400 + tod + rng.integers(-3600, 3601))
                i = int(np.searchsorted(B["t"], tt))
                if 0 < i < n - 2 and B["dok"][i]:
                    break
                dd = rng.choice(pool)
            if i is None or not (0 < i < n - 2):
                continue
            A = T["a"][max(T["cl"][i], 0)]
            if not A > 0 or np.isnan(x.risk_atr):
                continue
            d = int(x.d)
            E = B["o"][i] + B["spr"][i] + B["tick"] if d == 1 else B["o"][i] - B["tick"]
            risk = x.risk_atr * A
            SL = E - risk if d == 1 else E + risk - B["spr"][i]
            tp1 = E + d * x.tp1R * risk
            tp2 = E + d * x.tp2R * risk if not np.isnan(x.tp2R) else np.nan
            texit = int(np.searchsorted(B["t"], B["t"][i] + max(int(x.hold), 60) + 1))
            trail = B["trail"][x.ttf][0 if d == 1 else 1] if x.ttf else nan_trail
            sw = B["swl"] if d == 1 else B["sws"]
            r = sim_trade(B["o"], B["h"], B["l"], B["c"], B["spr"], B["tick"], i, i, 1, d, E, SL, tp1, x.f1, tp2, x.f2,
                          trail, 1 if x.ttf else 0, min(texit, n - 1), np.nan, B["hend"], 0, 0.0, B["cum_sw"], sw)
            if r[0]:
                out.append(dict(key=x.name, R=r[1]))
    return pd.DataFrame(out)
