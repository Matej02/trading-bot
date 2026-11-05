"""
F7 knihovna - stavebni bloky z dokumentu "Trading bot - 6 strategii (SMC + Volume Profile)" a simulace obchodu.

Bloky (kazdy na jednom miste, strategie je jen skladaji):
  pivoty (N=3 vstupni TF / N=5 H1+), struktura a BOS, displacement (telo >= 1 ATR a >= 60 % rozsahu,
  cesta >= 2 ATR, efficiency ratio >= 0,6, nejvys 1 opacna svicka, RVOL > prah, FVG >= 0,25 ATR),
  MSS (close za swingem, ze ktereho vysel posledni pohyb do extremu), FVG, RVOL podle casu dne (20 dni),
  volume profil (bin = denni ATR / 40, VA 70 %, HVN/LVN z vyhlazeneho histogramu), session VWAP + sigma,
  rezim trhu (balance / trend), likvidita (PDH/PDL, PWH/PWL, Asie, Londyn, EQH/EQL) a S/D zony H4.
Cas: vse se pocita v NY case; obchodni den forex/komodity 17:00-17:00 NY, krypto 00:00-00:00 UTC.
Simulace na zakladnich svickach (krypto M1, MT5 M15): ceny jsou bid, long plati ask = bid + spread brokera
v dane hodine; limit se vyplni az pruchodem o 1 tick; SL a TP ve stejne svicce = SL; ve svicce vyplneni
se kontroluje jen SL; skluz 1 tick na market a stop; swapy brokera za kazdy rollover.
"""
import json
import os

import numpy as np
import pandas as pd
from numba import njit

D7 = os.path.join("research_data", "f7")
BROKER = json.load(open(os.path.join("simulator", "lib", "broker.json"), encoding="utf-8"))["markets"]

# rel = spread brokera se skaluje cenou (aktualni spread / aktualni cena); proxy = trh, jehoz naklady se pouziji
MK = {
    "EURUSD": dict(cls="FOREX", base="M15", tick=1e-5, rel=False),
    "GBPUSD": dict(cls="FOREX", base="M15", tick=1e-5, rel=False),
    "USDJPY": dict(cls="FOREX", base="M15", tick=1e-3, rel=False),
    "XAUUSD": dict(cls="KOMODITY", base="M15", tick=0.01, rel=True),
    "XAGUSD": dict(cls="KOMODITY", base="M15", tick=0.001, rel=True),
    "CRUDE_OIL": dict(cls="KOMODITY", base="M15", tick=0.01, rel=False),
    "BTCUSD": dict(cls="KRYPTO", base="M1", tick=0.01, rel=True),
    "ETHUSD": dict(cls="KRYPTO", base="M1", tick=0.01, rel=True),
    "SOLUSD": dict(cls="KRYPTO", base="M1", tick=0.01, rel=True, proxy="ETHUSD"),  # broker SOL nema
}
# rozsireni tridy krypto pro vetsi vzorek (naklady relativne jako ETH)
for _m, _t in (("XRPUSD", 0.0001), ("BNBUSD", 0.01), ("ADAUSD", 0.0001), ("DOGEUSD", 0.00001), ("LTCUSD", 0.01), ("LINKUSD", 0.001)):
    MK[_m] = dict(cls="KRYPTO", base="M1", tick=_t, rel=True, proxy="ETHUSD")
TFS = {"M1": 1, "M3": 3, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}

# Vysoce dulezite zpravy USA (NY datum) - PRIBLIZNY kalendar z verejne znamych terminu (FXStreet historii
# bez hlavicky webu nevydava). FOMC 14:00 NY, NFP a CPI 08:30 NY.
FOMC = """2021-09-22 2021-11-03 2021-12-15 2022-01-26 2022-03-16 2022-05-04 2022-06-15 2022-07-27 2022-09-21
2022-11-02 2022-12-14 2023-02-01 2023-03-22 2023-05-03 2023-06-14 2023-07-26 2023-09-20 2023-11-01 2023-12-13
2024-01-31 2024-03-20 2024-05-01 2024-06-12 2024-07-31 2024-09-18 2024-11-07 2024-12-18 2025-01-29 2025-03-19
2025-05-07 2025-06-18 2025-07-30 2025-09-17 2025-10-29 2025-12-10 2026-01-28 2026-03-18 2026-04-29 2026-06-17
2026-07-29 2026-09-16 2026-10-28
2026-12-09 2027-01-27 2027-03-17 2027-04-28 2027-06-09 2027-07-28 2027-09-15 2027-10-27 2027-12-08""".split()
# Od 2026-11 doplneno z oficialnich rozpisu (federalreserve.gov fomccalendars; bls.gov schedule empsit a cpi),
# overeno 2026-11-05. FOMC 2027 je predbezne (Fed ho potvrzuje na predchozim zasedani).
NFP = """2021-09-03 2021-10-08 2021-11-05 2021-12-03 2022-01-07 2022-02-04 2022-03-04 2022-04-01 2022-05-06
2022-06-03 2022-07-08 2022-08-05 2022-09-02 2022-10-07 2022-11-04 2022-12-02 2023-01-06 2023-02-03 2023-03-10
2023-04-07 2023-05-05 2023-06-02 2023-07-07 2023-08-04 2023-09-01 2023-10-06 2023-11-03 2023-12-08 2024-01-05
2024-02-02 2024-03-08 2024-04-05 2024-05-03 2024-06-07 2024-07-05 2024-08-02 2024-09-06 2024-10-04 2024-11-01
2024-12-06 2025-01-10 2025-02-07 2025-03-07 2025-04-04 2025-05-02 2025-06-06 2025-07-03 2025-08-01 2025-09-05
2025-11-20 2025-12-16 2026-01-09 2026-02-11 2026-03-06 2026-04-03 2026-05-08 2026-06-05 2026-07-02 2026-08-07
2026-09-04 2026-10-02
2026-11-06 2026-12-04 2027-01-08 2027-02-05 2027-03-05 2027-04-02 2027-05-07 2027-06-04 2027-07-02 2027-08-06
2027-09-03 2027-10-08 2027-11-05 2027-12-03""".split()
CPI = """2021-09-14 2021-10-13 2021-11-10 2021-12-10 2022-01-12 2022-02-10 2022-03-10 2022-04-12 2022-05-11
2022-06-10 2022-07-13 2022-08-10 2022-09-13 2022-10-13 2022-11-10 2022-12-13 2023-01-12 2023-02-14 2023-03-14
2023-04-12 2023-05-10 2023-06-13 2023-07-12 2023-08-10 2023-09-13 2023-10-12 2023-11-14 2023-12-12 2024-01-11
2024-02-13 2024-03-12 2024-04-10 2024-05-15 2024-06-12 2024-07-11 2024-08-14 2024-09-11 2024-10-10 2024-11-13
2024-12-11 2025-01-15 2025-02-12 2025-03-12 2025-04-10 2025-05-13 2025-06-11 2025-07-15 2025-08-12 2025-09-11
2025-10-24 2025-12-18 2026-01-13 2026-02-13 2026-03-11 2026-04-10 2026-05-12 2026-06-10 2026-07-14 2026-08-12
2026-09-11 2026-10-14
2026-11-10 2026-12-10 2027-01-13 2027-02-11 2027-03-10 2027-04-13 2027-05-12 2027-06-10 2027-07-14 2027-08-11
2027-09-14 2027-10-14 2027-11-10 2027-12-10""".split()


def news_events():
    """Casy zprav v UTC sekundach a mnozina NY dat se zpravou (pro strategii 6)."""
    ev = [(d, "14:00") for d in FOMC] + [(d, "08:30") for d in NFP] + [(d, "08:30") for d in CPI]
    ts = pd.to_datetime([f"{d} {t}" for d, t in ev]).tz_localize("America/New_York").tz_convert("UTC")
    t = np.sort(ts.tz_localize(None).values.astype("datetime64[s]").astype(np.int64))
    days = set(pd.to_datetime(FOMC + NFP + CPI).date)
    return t, days


# ---------------------------------------------------------------- zakladni vypocty

def wilder_atr(h, l, c, n=14):
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    return pd.Series(tr).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()


def rvol(v, slot):
    """RVOL = objem / prumer objemu ve stejny cas dne za predchozich 20 dni (jen minula data)."""
    s = pd.Series(v)
    prev = s.groupby(slot).shift(1)
    m = prev.groupby(slot).rolling(20, min_periods=10).mean().reset_index(level=0, drop=True).sort_index()
    return (s / m.replace(0, np.nan)).to_numpy()


@njit(cache=True)
def pivots(h, l, N):
    n = len(h)
    ph = np.zeros(n, np.bool_)
    pl = np.zeros(n, np.bool_)
    for i in range(N, n - N):
        okh = True
        okl = True
        for j in range(i - N, i + N + 1):
            if j == i:
                continue
            if h[j] > h[i] or (j < i and h[j] == h[i]):
                okh = False
            if l[j] < l[i] or (j < i and l[j] == l[i]):
                okl = False
        ph[i] = okh
        pl[i] = okl
    return ph, pl


@njit(cache=True)
def structure(h, l, c, ph, pl, N):
    """Stav po uzavreni svicky k (pivot j je znamy az po svicce j+N): posledni a predposledni swing high/low,
    BOS (close za neprorazenym swingem), smer posledniho BOS a index svicky posledniho BOS."""
    n = len(c)
    sh1 = np.full(n, np.nan)
    sh1i = np.full(n, -1, np.int64)
    sh2 = np.full(n, np.nan)
    sl1 = np.full(n, np.nan)
    sl1i = np.full(n, -1, np.int64)
    sl2 = np.full(n, np.nan)
    st = np.zeros(n, np.int64)
    bk = np.full(n, -1, np.int64)
    a_sh, a_shi, p_sh, o_sh = np.nan, -1, np.nan, np.nan
    a_sl, a_sli, p_sl, o_sl = np.nan, -1, np.nan, np.nan
    cur, lastb = 0, -1
    for k in range(n):
        if not np.isnan(o_sh) and c[k] > o_sh:
            cur, lastb, o_sh = 1, k, np.nan
        if not np.isnan(o_sl) and c[k] < o_sl:
            cur, lastb, o_sl = -1, k, np.nan
        j = k - N
        if j >= 0:
            if ph[j]:
                p_sh, a_sh, a_shi, o_sh = a_sh, h[j], j, h[j]
            if pl[j]:
                p_sl, a_sl, a_sli, o_sl = a_sl, l[j], j, l[j]
        sh1[k], sh1i[k], sh2[k] = a_sh, a_shi, p_sh
        sl1[k], sl1i[k], sl2[k] = a_sl, a_sli, p_sl
        st[k], bk[k] = cur, lastb
    return sh1, sh1i, sh2, sl1, sl1i, sl2, st, bk


@njit(cache=True)
def displacement(o, h, l, c, a, rv, k, d, rv_thr):
    """Displacement 1-5 svicek koncici svickou k ve smeru d. Vraci (L, j) - L delka (0 = neplati),
    j = treti svicka FVG (muze byt k+1, pak je signal znamy az po jejim uzavreni)."""
    n = len(c)
    A = a[k]
    if not (A > 0):
        return 0, -1
    body = (c[k] - o[k]) * d
    rng = h[k] - l[k]
    if rng <= 0 or body < A or body < 0.6 * rng:
        return 0, -1
    for L in range(1, 6):
        s0 = k - L + 1
        if s0 < 2:
            break
        opp = 0
        rs = 0.0
        path = 0.0
        bad = False
        for j in range(s0, k + 1):
            if (c[j] - o[j]) * d < 0:
                opp += 1
            if np.isnan(rv[j]):
                bad = True
            else:
                rs += rv[j]
            path += abs(c[j] - c[j - 1])
        if opp > 1:
            break
        if bad:
            continue
        if (c[k] - o[s0]) * d < 2.0 * A:
            continue
        if path <= 0 or abs(c[k] - c[s0 - 1]) / path < 0.6:
            continue
        if rs / L <= rv_thr:
            continue
        fj = -1
        for j in range(min(k + 1, n - 1), s0, -1):
            gap = (l[j] - h[j - 2]) if d == 1 else (l[j - 2] - h[j])
            if gap >= 0.25 * A:
                fj = j
                break
        if fj == -1:
            continue
        return L, fj
    return 0, -1


@njit(cache=True)
def find_mss(o, h, l, c, a, rv, ph, pl, N, k0, K, d, ext, ext_k, cancel, rv_thr):
    """Sdileny vstupni model: MSS ve smeru d s displacementem a FVG, nejpozdeji K svicek VTF po spoustaci.
    k0 = prvni svicka VTF po uzavreni spoustace; MSS se hleda uz od svicky po extremu (ext_k + 1), protoze
    na nizsim TF se struktura casto zlomi jeste uvnitr svicky spoustace (SFP na M15). Signal je znamy az po
    uzavreni MSS/FVG i spoustace. ext/ext_k = extrem pohybu pred MSS (aktualizuje se), cancel = close za touto
    cenou setup rusi. Vraci (k_mss, dec, fj, L, ext, ob); k_mss = -1 nic."""
    n = len(c)
    for k in range(min(ext_k + 1, k0), min(k0 + K, n - 1)):
        if d == 1:
            if l[k] < ext:
                ext, ext_k = l[k], k
            if c[k] < cancel:
                return -1, -1, -1, 0, ext, -1
        else:
            if h[k] > ext:
                ext, ext_k = h[k], k
            if c[k] > cancel:
                return -1, -1, -1, 0, ext, -1
        A = a[k]
        if not (A > 0):
            continue
        lvl = np.nan
        j = ext_k - 1
        lim = max(ext_k - 300, 1)
        while j >= lim:
            if j + N <= k - 1 and ((d == 1 and ph[j]) or (d == -1 and pl[j])):
                cand = h[j] if d == 1 else l[j]
                if (cand - ext) * d >= 0.5 * A:
                    lvl = cand
                    break
            j -= 1
        if np.isnan(lvl):
            continue
        if (c[k] - lvl) * d > 0 and (c[k - 1] - lvl) * d <= 0:
            L, fj = displacement(o, h, l, c, a, rv, k, d, rv_thr)
            if L > 0:
                ob = -1
                for q in range(k - L, max(k - L - 10, 0), -1):
                    if (c[q] - o[q]) * d < 0:
                        ob = q
                        break
                return k, max(k, fj, k0 - 1), fj, L, ext, ob
    return -1, -1, -1, 0, ext, -1


# ---------------------------------------------------------------- volume profil

@njit(cache=True)
def profile_hist(h, l, v, s, e, bw):
    lo = np.min(l[s:e + 1])
    hi = np.max(h[s:e + 1])
    b0 = int(np.floor(lo / bw))
    b1 = int(np.floor(hi / bw))
    hist = np.zeros(b1 - b0 + 1)
    for i in range(s, e + 1):
        x0 = int(np.floor(l[i] / bw)) - b0
        x1 = int(np.floor(h[i] / bw)) - b0
        w = v[i] / (x1 - x0 + 1)
        for x in range(x0, x1 + 1):
            hist[x] += w
    return hist, b0


@njit(cache=True)
def value_area(hist, pct):
    nb = len(hist)
    poc = int(np.argmax(hist))
    tot = hist.sum()
    a = poc
    z = poc
    acc = hist[poc]
    while acc < pct * tot and (a > 0 or z < nb - 1):
        up = -1.0
        if z + 1 < nb:
            up = hist[z + 1] + (hist[z + 2] if z + 2 < nb else 0.0)
        dn = -1.0
        if a - 1 >= 0:
            dn = hist[a - 1] + (hist[a - 2] if a - 2 >= 0 else 0.0)
        if up >= dn:
            z = min(z + 2, nb - 1)
        else:
            a = max(a - 2, 0)
        acc = hist[a:z + 1].sum()
    return poc, a, z


@njit(cache=True)
def range_profiles(h, l, v, rs, re, bws, tick, pct):
    """POC/VAH/VAL pro kazdy rozsah zakladnich svicek rs[i]..re[i] s binem bws[i]."""
    m = len(rs)
    poc = np.full(m, np.nan)
    vah = np.full(m, np.nan)
    val = np.full(m, np.nan)
    for i in range(m):
        bw = bws[i]
        if not (bw > 0) or rs[i] < 0 or re[i] < rs[i]:
            continue
        bw = max(tick, np.round(bw / tick) * tick)
        hist, b0 = profile_hist(h, l, v, rs[i], re[i], bw)
        if hist.sum() <= 0:
            continue
        p, a, z = value_area(hist, pct)
        poc[i] = (b0 + p + 0.5) * bw
        val[i] = (b0 + a) * bw
        vah[i] = (b0 + z + 1) * bw
    return poc, vah, val


def smooth_nodes(hist, b0, bw):
    """HVN = lokalni maximum vyhlazeneho histogramu (5 binu) >= 50 % POC, LVN = lokalni minimum <= 25 % POC
    mezi dvema HVN. Vraci ceny stredu binu (hvn, lvn)."""
    sm = np.convolve(hist, np.ones(5) / 5, mode="same")
    if len(sm) < 3 or sm.max() <= 0:
        return np.array([]), np.array([])
    pk = sm.max()
    loc_max = np.flatnonzero((sm[1:-1] >= sm[:-2]) & (sm[1:-1] > sm[2:])) + 1
    loc_min = np.flatnonzero((sm[1:-1] <= sm[:-2]) & (sm[1:-1] < sm[2:])) + 1
    hv = loc_max[sm[loc_max] >= 0.5 * pk]
    lv = loc_min[sm[loc_min] <= 0.25 * pk]
    if len(hv) >= 2:
        lv = lv[(lv > hv.min()) & (lv < hv.max())]
    else:
        lv = lv[:0]
    return (b0 + hv + 0.5) * bw, (b0 + lv + 0.5) * bw


@njit(cache=True)
def session_vwap(h, l, c, v, day):
    n = len(c)
    vw = np.empty(n)
    sg = np.empty(n)
    cv = cpv = cp2v = 0.0
    for i in range(n):
        if i == 0 or day[i] != day[i - 1]:
            cv = cpv = cp2v = 0.0
        p = (h[i] + l[i] + c[i]) / 3.0
        w = v[i] if v[i] > 0 else 1e-9
        cv += w
        cpv += p * w
        cp2v += p * p * w
        m = cpv / cv
        vw[i] = m
        sg[i] = np.sqrt(max(cp2v / cv - m * m, 0.0))
    return vw, sg


# ---------------------------------------------------------------- simulace obchodu

@njit(cache=True)
def sim_trade(o, h, l, c, spr, tick, i0, i_valid, kind, d, E, SL, tp1, f1, tp2, f2,
              trail, trail_mode, i_texit, soft_lvl, hend, chk_bars, chk_R, cum_sw, sw_frac):
    """Jeden obchod na zakladnich svickach (bid). Long: vstup za ask, SL/TP podle bid. Short: vstup za bid,
    SL/TP podle ask (SL zadany v bid cene se prevede +spread v case vstupu).
    kind 0 = limit E platny i0..i_valid (zrusi se pri dosazeni TP1 nebo SL pred vyplnenim), 1 = trh na open i0.
    Nohy: f1 na tp1 (pak SL na vstup), f2 na tp2 (nan = pripadne k runneru), zbytek runner (trailing/cas).
    trail_mode 0 nic, 1 trailing po TP1. Vraci (stav, R, i_fill, i_exit, duvod, mfe, E, risk)
    stav 0 = nevyplneno; duvod 1 SL, 2 TP, 3 cas, 4 BE/trailing, 5 mekky vystup, 6 kontrola +1R, 7 konec dat."""
    n = len(c)
    fi = -1
    if kind == 1:
        if i0 >= n:
            return 0, 0.0, -1, -1, 0, 0.0, E, 0.0
        fi = i0
        E = o[i0] + spr[i0] + tick if d == 1 else o[i0] - tick
    else:
        for i in range(i0, min(i_valid, n - 1) + 1):
            if d == 1:
                if l[i] + spr[i] <= E - tick:
                    fi = i
                    break
                if h[i] >= tp1 or l[i] <= SL:
                    return 0, 0.0, -1, i, 0, 0.0, E, 0.0
            else:
                if h[i] >= E + tick:
                    fi = i
                    break
                if l[i] + spr[i] <= tp1 or h[i] >= SL:
                    return 0, 0.0, -1, i, 0, 0.0, E, 0.0
        if fi < 0:
            return 0, 0.0, -1, -1, 0, 0.0, E, 0.0
    if d == 1:
        stop = SL
        risk = E - SL
    else:
        stop = SL + spr[fi]
        risk = stop - E
    if risk <= 0:
        return 0, 0.0, -1, -1, 0, 0.0, E, 0.0
    q1 = f1
    q2 = f2 if not np.isnan(tp2) else 0.0
    openq = 1.0
    pnl = 0.0
    mfe = 0.0
    hit1 = q1 <= 0
    reason = 7
    ex = n - 1
    for i in range(fi, n):
        first = i == fi
        sp = spr[i]
        if i >= i_texit and not first:
            px = o[i] if d == 1 else o[i] + sp
            pnl += openq * (px - E) * d
            openq = 0.0
            reason, ex = 3, i
            break
        if d == 1:
            if l[i] <= stop:
                px = (min(o[i], stop) if not first else stop) - tick
                pnl += openq * (px - E)
                openq = 0.0
                reason, ex = (1 if stop == SL else 4), i
                break
        else:
            if h[i] + sp >= stop:
                px = (max(o[i] + sp, stop) if not first else stop) + tick
                pnl += openq * (E - px)
                openq = 0.0
                reason, ex = (1 if stop == SL + spr[fi] else 4), i
                break
        if not first:
            if not hit1:
                if (d == 1 and h[i] >= tp1) or (d == -1 and l[i] + sp <= tp1):
                    pnl += q1 * (tp1 - E) * d
                    openq -= q1
                    hit1 = True
            if hit1 and q2 > 0:
                if (d == 1 and h[i] >= tp2) or (d == -1 and l[i] + sp <= tp2):
                    pnl += q2 * (tp2 - E) * d
                    openq -= q2
                    q2 = 0.0
            if openq <= 1e-9:
                openq = 0.0
                reason, ex = 2, i
                break
            if hend[i] and not np.isnan(soft_lvl) and (c[i] - soft_lvl) * d < 0:
                px = c[i] if d == 1 else c[i] + sp
                pnl += openq * (px - E) * d
                openq = 0.0
                reason, ex = 5, i
                break
        fav = ((h[i] - E) if d == 1 else (E - l[i] - sp)) / risk
        if fav > mfe:
            mfe = fav
        if chk_bars > 0 and i - fi == chk_bars and mfe < chk_R:
            px = c[i] if d == 1 else c[i] + sp
            pnl += openq * (px - E) * d
            openq = 0.0
            reason, ex = 6, i
            break
        if hit1 and q1 > 0:
            if d == 1 and stop < E:
                stop = E
            if d == -1 and stop > E:
                stop = E
        if trail_mode == 1 and hit1:
            tl = trail[i]
            if not np.isnan(tl):
                if d == 1 and tl > stop and tl < c[i]:
                    stop = tl
                if d == -1 and tl + sp < stop and tl > c[i]:
                    stop = tl + sp
    if openq > 0:
        px = c[n - 1] if d == 1 else c[n - 1] + spr[n - 1]
        pnl += openq * (px - E) * d
    sw = sw_frac * E * (cum_sw[ex] - cum_sw[fi])
    return 1, (pnl + sw) / risk, fi, ex, reason, mfe, E, risk


# ---------------------------------------------------------------- priprava trhu

def group(B, key):
    n = len(key)
    s = np.flatnonzero(np.r_[True, key[1:] != key[:-1]]).astype(np.int64)
    e = np.r_[s[1:] - 1, n - 1].astype(np.int64)
    T = dict(s=s, e=e, o=B["o"][s], c=B["c"][e], h=np.maximum.reduceat(B["h"], s), l=np.minimum.reduceat(B["l"], s),
             v=np.add.reduceat(B["v"], s), key=key[s])
    T["ix"] = np.repeat(np.arange(len(s)), e - s + 1)
    T["cl"] = T["ix"] - (T["e"][T["ix"]] != np.arange(n)).astype(np.int64)  # posledni UZAVRENA svicka
    return T


def make_tf(B, minutes):
    T = group(B, B["lt"] // (minutes * 60))
    T["min"] = minutes
    T["lt0"] = T["key"] * minutes * 60
    T["day"] = B["day"][T["s"]]
    T["a"] = wilder_atr(T["h"], T["l"], T["c"])
    T["rv"] = rvol(T["v"], (T["lt0"] % 86400) // (minutes * 60)) if minutes < 1440 else np.ones(len(T["s"]))
    N = 3 if minutes <= 30 else 5
    T["N"] = N
    T["ph"], T["pl"] = pivots(T["h"], T["l"], N)
    for k, x in zip(["sh1", "sh1i", "sh2", "sl1", "sl1i", "sl2", "st", "bk"], structure(T["h"], T["l"], T["c"], T["ph"], T["pl"], N)):
        T[k] = x
    return T


def at_closed(T, arr, default=np.nan):
    """Hodnota pole TF na zakladnich svickach podle posledni UZAVRENE svicky TF."""
    cl = T["cl"]
    out = np.where(cl >= 0, arr[np.maximum(cl, 0)], default)
    return out


def load_market(mk, base=None):
    info = MK[mk]
    base = base or info["base"]
    df = pd.read_pickle(os.path.join(D7, f"{mk}_{base}.pkl"))
    t = df.t.to_numpy(np.int64)
    utc = pd.to_datetime(t, unit="s", utc=True)
    ny = utc.tz_convert("America/New_York").tz_localize(None).values.astype("datetime64[s]").astype(np.int64)
    lon_h = utc.tz_convert("Europe/London").hour.to_numpy()
    crypto = info["cls"] == "KRYPTO"
    lt = t.copy() if crypto else ny + 7 * 3600
    B = dict(mk=mk, cls=info["cls"], crypto=crypto, base=base, bmin=TFS[base], tick=info["tick"],
             t=t, ny=ny, lt=lt, day=lt // 86400, nyh=(ny % 86400) / 3600.0,
             o=df.o.to_numpy(float), h=df.h.to_numpy(float), l=df.l.to_numpy(float), c=df.c.to_numpy(float),
             v=df.v.to_numpy(float))
    # naklady brokera
    src = info.get("proxy", mk)
    b = BROKER[src]
    sbh = np.array(b["spreadByHour"], float)
    if info["rel"]:
        if src == mk:
            ref = float(np.median(B["c"][-30 * 1440 // B["bmin"]:]))
        else:
            p = pd.read_pickle(os.path.join(D7, f"{src}_M1.pkl"))
            ref = float(np.median(p.c.to_numpy()[-30 * 1440:]))
        B["spr"] = sbh[lon_h] / ref * B["c"]
    else:
        B["spr"] = sbh[lon_h]
    wd = (B["day"] + 3) % 7  # 0 = pondeli
    new_day = np.r_[True, B["day"][1:] != B["day"][:-1]]
    mult = np.where(crypto, 1, np.where(wd == 3, 3, 1)) * new_day
    B["cum_sw"] = np.cumsum(mult).astype(np.float64)
    B["swl"], B["sws"] = b["swapLong"], b["swapShort"]
    B["news_t"], B["news_days"] = news_events()
    return B


def prepare(mk, base=None):
    """Vsechny stavebni bloky pro jeden trh (TF svicky, profily, VWAP, rezim, likvidita)."""
    B = load_market(mk, base)
    n = len(B["t"])
    T = {}
    for nm, m in TFS.items():
        if m >= B["bmin"] and (m % B["bmin"] == 0):
            T[nm] = make_tf(B, m)
    D = T["D1"]
    B["T"] = T
    nd = len(D["s"])
    # dny po dire v datech (MT5) - 25 obchodnich dni se nepouziji, nez se naplni ATR, RVOL a kompozit
    gap = np.r_[99, np.diff(D["key"])] > 4
    last_gap = np.maximum.accumulate(np.where(gap, np.arange(nd), 0))
    D["ok"] = (np.arange(nd) - last_gap) >= 25
    datr = D["a"]
    datr_prev = np.r_[np.nan, datr[:-1]]
    # profil kazdeho dne (bin = denni ATR predchoziho dne / 40)
    D["poc"], D["vah"], D["val"] = range_profiles(B["h"], B["l"], B["v"], D["s"], D["e"], datr_prev / 40, B["tick"], 0.70)
    # kompozit 20 dni pro den d = dny d-20..d-1
    rs = np.full(nd, -1, np.int64)
    re = np.full(nd, -1, np.int64)
    rs[20:] = D["s"][:-20]
    re[20:] = D["e"][19:-1]
    D["cpoc"], D["cvah"], D["cval"] = range_profiles(B["h"], B["l"], B["v"], rs, re, datr_prev / 40, B["tick"], 0.70)
    # VA prekryv
    def ov(a, b):
        w = np.minimum(D["vah"][a] - D["val"][a], D["vah"][b] - D["val"][b])
        x = np.minimum(D["vah"][a], D["vah"][b]) - np.maximum(D["val"][a], D["val"][b])
        return np.where(w > 0, x / w, 0.0) >= 0.5
    idx = np.arange(nd)
    va3 = np.zeros(nd, bool)  # VA dnu d-3, d-2, d-1 se navzajem prekryvaji
    m3 = idx >= 3
    a, b2, c2 = idx[m3] - 3, idx[m3] - 2, idx[m3] - 1
    va3[m3] = ov(a, b2) & ov(b2, c2) & ov(a, c2)
    D["va3"] = va3
    # balance na konci dne d: VA d-2..d prekryte a close dne d uvnitr kompozitu d-19..d
    cv_next_l = np.r_[D["cval"][1:], np.nan]
    cv_next_h = np.r_[D["cvah"][1:], np.nan]
    bal_end = np.zeros(nd, bool)
    bal_end[:-1] = va3[1:]
    bal_end &= (D["c"] >= cv_next_l) & (D["c"] <= cv_next_h)
    D["bal_end"] = bal_end
    di = D["ix"]  # index dne pro kazdou zakladni svicku
    B["di"] = di
    B["dok"] = D["ok"][di]
    # VWAP a jeho sklon
    B["vw"], B["sg"] = session_vwap(B["h"], B["l"], B["c"], B["v"], B["day"])
    lag = 60 // B["bmin"]
    a5 = at_closed(T["M5"], T["M5"]["a"]) if "M5" in T else at_closed(T["M15"], T["M15"]["a"]) * 0.58
    vw_lag = np.r_[np.full(lag, np.nan), B["vw"][:-lag]]
    same = np.r_[np.zeros(lag, bool), B["day"][lag:] == B["day"][:-lag]]
    B["slope"] = np.where(same, (B["vw"] - vw_lag) / a5, np.nan)
    # rezim na kazde zakladni svicce
    inside = (B["c"] >= D["cval"][di]) & (B["c"] <= D["cvah"][di])
    H4 = T["H4"]
    h4cl = H4["cl"]
    h4bk = np.where(h4cl >= 0, H4["bk"][np.maximum(h4cl, 0)], -1)
    h4st = np.where(h4cl >= 0, H4["st"][np.maximum(h4cl, 0)], 0)
    bos_day = np.where(h4bk >= 0, H4["day"][np.maximum(h4bk, 0)], -10**9)
    recent = (B["day"] - bos_day) <= 5
    has = ~np.isnan(D["cval"][di])
    B["regime"] = np.where(has & D["va3"][di] & inside, 1, np.where(has & recent & ~inside & (h4st != 0), 2, 0))
    B["h4st"] = h4st
    # kdy je konec H1 svicky (mekky vystup) a trailing urovne
    H1 = T["H1"]
    hend = np.zeros(n, np.bool_)
    hend[H1["e"]] = True
    B["hend"] = hend
    B["trail"] = {}
    for nm in ("M5", "M15", "H1"):
        if nm in T:
            B["trail"][nm] = (at_closed(T[nm], T[nm]["sl1"]), at_closed(T[nm], T[nm]["sh1"]))
    return B


def idx_ge(B, t_utc):
    return int(np.searchsorted(B["t"], t_utc))


def exit_idx(B, i, ny_hour, utc_hour=None):
    """Index prvni zakladni svicky v hodine vystupu tehoz obchodniho dne (forex: NY cas; krypto: UTC)."""
    if B["crypto"] and utc_hour is not None:
        target = (B["t"][i] // 86400) * 86400 + int(utc_hour * 3600)
        return int(np.searchsorted(B["t"], target))
    target_ny = (B["ny"][i] // 86400) * 86400 + int(ny_hour * 3600)
    target = target_ny - (B["ny"][i] - B["t"][i])
    return int(np.searchsorted(B["t"], target))


def in_news(B, i, minutes=30):
    t = B["t"][i]
    nt = B["news_t"]
    k = np.searchsorted(nt, t)
    for q in (k - 1, k):
        if 0 <= q < len(nt) and abs(nt[q] - t) <= minutes * 60:
            return True
    return False
