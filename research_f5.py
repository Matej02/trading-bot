"""
F5 - sest strategii z konceptu S/R, SMC a volume profile na vsech trzich brokera (2026-10-28).

Prani uzivatele: misto trend-followingu zkusit S/R zony, breakouty, fakeouty, SMC (order blocky, FVG,
supply/demand), volume profile (FRVP, HVN/LVN, VAH/VAL/POC), denni open a likviditu - vymyslet ~6 strategii,
otestovat je na ruznych parech a obchodovat tam, kde funguji.

PLAN STANOVENY PREDEM (pravidla i prahy se podle vysledku nemeni):
  Data: hodinove svicky MT5 s tick volume (forex/kovy/indexy/ropa), BTC/ETH z Binance se skutecnym objemem.
  Cas = cas brokera (den zacina o pulnoci brokera); Binance se posune o +2 h, at session sedi.
  Spolecne: ATR(14) z 1h, denni ATR(14) a denni trend z UZAVRENYCH dni (EMA50 dennich zavreni a jeji sklon
  za 3 dny: nahoru / dolu / nic). Spread brokera v dane hodine (long za ask, ven za bid), swapy podle dni drzeni.
  SL ma prednost pred TP ve stejne svicce; pri vstupu limitem se v teze svicce kontroluje jen SL.
  Jedna pozice na strategii a trh; nejdele 120 svicek 1h (5 dni), pak ven za trzni cenu.

  S1 S/R breakout + retest: urovne = denni swingy (fraktal 2 dny) z poslednich 60 dni, ktere se aspon 2x
     potkaly do 0,25 denniho ATR. 1h zavreni pres uroven s objemem >= 1,5x prumer 20 svicek a ne proti
     dennimu trendu -> limit na uroven (retest) platny 24 svicek, SL 0,5 denniho ATR za urovni, TP 2R.
  S2 Fakeout / sweep likvidity: 1h svicka prorazi vcerejsi high (low), zavre zpet pod (nad) nim, knot >= 50 %
     svicky a objem >= 1,2x prumer -> obchod opacnym smerem na otevreni dalsi svicky, SL za extremem knotu
     + 0,1 ATR, TP 2R. Nejvys 1x denne na stranu.
  S3 SMC - BOS + FVG + order block v dennim trendu: displacement svicka (telo >= 1,2 ATR) prorazi maximum
     (minimum) 20 svicek a za ni vznikne FVG; order block = posledni opacna svicka pred displacementem
     (az 5 zpet). Limit na okraj OB platny 48 svicek, SL za OB + 0,1 ATR, TP 2R.
  S4 Supply/demand 4h zpresnena volume profilem: zakladna 4h (rozpeti <= 0,6 ATR 4h) a odchod (telo >= 1,5 ATR 4h,
     zavreni za zakladnou) v dennim trendu. Zona plati jen kdyz se kryje s HVN (kos profilu >= 80. percentil)
     z FRVP poslednich 120 svicek 1h. Limit na okraj zony platny 60 svicek, SL za zonou + 0,1 ATR 4h, TP 2R.
  S5 Range - value area (VAH/VAL -> POC): profil vcerejsiho dne (objem rozlozeny po rozpeti svicek, 40 kosu,
     value area 70 %). Jen kdyz se vcerejsi value area prekryva s predvcerejsi (trh v rovnovaze). Svicka sahne
     pod VAL (nad VAH) a zavre zpet dovnitr -> obchod k POC, SL za extremem svicky + 0,2 ATR, TP = POC
     (jen kdyz to dava aspon 1:1). Nejvys 1x denne na stranu.
  S6 Denni open + asijska likvidita (Judas swing): asijske rozpeti = svicky 01-08 h brokera. V 09-16 h svicka
     smete asijske minimum (maximum) a zavre zpet do rozpeti, je pod (nad) dennim openem a denni trend
     souhlasi -> obchod ve smeru trendu, SL za extremem + 0,1 ATR, TP 2R. Nejvys 1x denne.

  Trhy: vsech 40 trhu brokera (simulator/lib/broker.json) bez GAUUSD (kopie zlata); trhy s mene nez 2 roky
  hodinovych dat do 2023 se vynechaji.
  Vyber: obchody do 2023-12-31, holdout od 2024-01-01.
  A) Strategie na vsech trzich dohromady: PROSLO = holdout n >= 100, prumer R > 0, t >= 2,64 (Bonferroni pro 6),
     PF >= 1,10 a zaroven prumer > 0 i ve vyberu.
  B) Strategie x trh (prani uzivatele "obchodovat tam, kde to funguje"): z vyberu se vezmou dvojice s n >= 40,
     prumerem >= +0,05 R a t >= 2,0. Ty se v holdoutu hodnoti JAKO SKUPINA (test samotneho vybirani):
     PROSLO = n >= 60, prumer R > 0, t >= 2,33. Jednotlive dvojice se jen vypisi (malo obchodu = sum).
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from numba import njit

sys.stdout.reconfigure(line_buffering=True)

DATA = "research_data"
SPLIT = pd.Timestamp("2024-01-01")
broker = json.load(open(os.path.join("simulator", "lib", "broker.json"), encoding="utf-8"))["markets"]
MARKETS = [m for m in broker if m != "GAUUSD"]
BINANCE = {"BTCUSD": "BTCUSDT", "ETHUSD": "ETHUSDT"}
MAX_HOLD = 120
NAMES = {1: "S1 S/R breakout + retest", 2: "S2 fakeout / sweep likvidity", 3: "S3 SMC BOS+FVG+OB",
         4: "S4 S/D 4h + FRVP HVN", 5: "S5 range VAL/VAH -> POC", 6: "S6 denni open + asijska likvidita"}


# ---------------------------------------------------------- data (1h s objemem)

def load_1h(mk):
    path = os.path.join(DATA, f"f5_{mk.replace('&', 'and')}_1h.pkl")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 7 * 86400:
        return pd.read_pickle(path)
    if mk in BINANCE:
        import requests
        rows, t = [], int(pd.Timestamp("2019-01-01", tz="UTC").timestamp() * 1000)
        while True:
            r = requests.get("https://data-api.binance.vision/api/v3/klines",
                             params={"symbol": BINANCE[mk], "interval": "1h", "startTime": t, "limit": 1000}, timeout=30).json()
            if not r:
                break
            rows += r
            t = r[-1][0] + 1
            if len(r) < 1000:
                break
        df = pd.DataFrame([[x[0], *map(float, x[1:6])] for x in rows], columns=["time", "open", "high", "low", "close", "volume"])
        df["time"] = pd.to_datetime(df["time"], unit="ms") + pd.Timedelta(hours=2)  # priblizne cas brokera
    else:
        import mt5_connector as mc
        if mc.mt5.terminal_info() is None:
            mc.connect()
        mc.mt5.symbol_select(mk, True)
        r = None
        for _ in range(5):
            r = mc.mt5.copy_rates_from_pos(mk, mc.mt5.TIMEFRAME_H1, 0, 99000)
            if r is not None and len(r):
                break
            time.sleep(2)
        if r is None or not len(r):
            raise RuntimeError("MT5 nevratil data")
        df = pd.DataFrame(r)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df = df.rename(columns={"tick_volume": "volume"})[["time", "open", "high", "low", "close", "volume"]]
    df = df.set_index("time").astype(float).iloc[:-1]
    df.to_pickle(path)
    return df


def secs(idx):
    return idx.as_unit("s").asi8.astype(np.int64)


def sma(x, n):
    return pd.Series(x).rolling(n).mean().values


def atr(h, l, c, n=14):
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    return sma(tr, n)


def prepare(df):
    """Pole pro strategie: 1h + denni (z uzavrenych dni) + 4h."""
    o, h, l, c, v = (df[k].values.astype(np.float64) for k in ("open", "high", "low", "close", "volume"))
    day = df.index.normalize()
    dd = df.groupby(day).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
    d_atr = atr(dd.high.values, dd.low.values, dd.close.values)
    e50 = pd.Series(dd.close.values).ewm(span=50, adjust=False).mean().values
    tr = np.where((dd.close.values > e50) & (e50 > np.roll(e50, 3)), 1, np.where((dd.close.values < e50) & (e50 < np.roll(e50, 3)), -1, 0))
    tr[:53] = 0
    k = np.searchsorted(dd.index.values, day.values)  # index dne pro kazdou hodinu
    # 4h svicky (cas brokera) a index posledni 1h svicky v kazde
    g4 = df.index.floor("4h")
    h4 = df.groupby(g4).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
    end4 = (np.searchsorted(g4.values, h4.index.values, side="right") - 1).astype(np.int64)
    a4 = atr(h4.high.values, h4.low.values, h4.close.values)
    return dict(
        t=secs(df.index), o=o, h=h, l=l, c=c, v=v, hour=df.index.hour.values.astype(np.int64),
        a1=atr(h, l, c), vavg=sma(v, 20), k=k.astype(np.int64),
        d_open=dd.open.values, d_high=dd.high.values, d_low=dd.low.values, d_atr=d_atr, d_tr=tr.astype(np.int64),
        d_start=np.searchsorted(k, np.arange(len(dd))).astype(np.int64),
        h4o=h4.open.values, h4h=h4.high.values, h4l=h4.low.values, h4c=h4.close.values, a4=a4, end4=end4,
        h4day=k[end4],
    )


# ---------------------------------------------------------- strategie -> prikazy
# prikaz: (index signalni svicky i, smer, druh 0 = trh na otevreni i+1 / 1 = limit, cena limitu, SL,
#          TP (0 = 2R z vstupu), platnost limitu ve svickach)

@njit(cache=True)
def s1_orders(c, v, vavg, a1, k, d_high, d_low, d_atr, d_tr):
    n = len(c)
    nd = len(d_high)
    # silne urovne pro kazdy den z swingu potvrzenych do predchoziho dne
    R = np.full((nd, 10), np.nan)
    S = np.full((nd, 10), np.nan)
    for day in range(65, nd):
        ad = d_atr[day - 1]
        if np.isnan(ad):
            continue
        nr = 0
        ns = 0
        for j in range(day - 62, day - 2):
            if j < 2 or j + 2 > day - 1:
                continue
            if d_high[j] > d_high[j - 1] and d_high[j] > d_high[j - 2] and d_high[j] > d_high[j + 1] and d_high[j] > d_high[j + 2]:
                cnt = 0
                for q in range(day - 62, day - 2):
                    if q != j and q >= 2 and abs(d_high[q] - d_high[j]) <= 0.25 * ad:
                        cnt += 1
                if cnt >= 1 and nr < 10:
                    R[day, nr] = d_high[j]
                    nr += 1
            if d_low[j] < d_low[j - 1] and d_low[j] < d_low[j - 2] and d_low[j] < d_low[j + 1] and d_low[j] < d_low[j + 2]:
                cnt = 0
                for q in range(day - 62, day - 2):
                    if q != j and q >= 2 and abs(d_low[q] - d_low[j]) <= 0.25 * ad:
                        cnt += 1
                if cnt >= 1 and ns < 10:
                    S[day, ns] = d_low[j]
                    ns += 1
    out = []
    for i in range(21, n - 1):
        day = k[i]
        if day < 65 or np.isnan(vavg[i - 1]) or v[i] < 1.5 * vavg[i - 1] or np.isnan(d_atr[day - 1]):
            continue
        ad = d_atr[day - 1]
        tr = d_tr[day - 1]
        for q in range(10):
            L = R[day, q]
            if not np.isnan(L) and tr >= 0 and c[i - 1] <= L < c[i]:
                out.append((i, 1, 1, L, L - 0.5 * ad, 0.0, 24))
                break
            L = S[day, q]
            if not np.isnan(L) and tr <= 0 and c[i - 1] >= L > c[i]:
                out.append((i, -1, 1, L, L + 0.5 * ad, 0.0, 24))
                break
    return out


@njit(cache=True)
def s2_orders(o, h, l, c, v, vavg, a1, k, d_high, d_low):
    out = []
    last_long = -1
    last_short = -1
    for i in range(21, len(c) - 1):
        day = k[i]
        if day < 2 or np.isnan(vavg[i - 1]) or np.isnan(a1[i]) or v[i] < 1.2 * vavg[i - 1]:
            continue
        rng = h[i] - l[i]
        if rng <= 0:
            continue
        pdh = d_high[day - 1]
        pdl = d_low[day - 1]
        if h[i] > pdh and c[i] < pdh and (h[i] - max(o[i], c[i])) >= 0.5 * rng and last_short != day:
            out.append((i, -1, 0, 0.0, h[i] + 0.1 * a1[i], 0.0, 0))
            last_short = day
        if l[i] < pdl and c[i] > pdl and (min(o[i], c[i]) - l[i]) >= 0.5 * rng and last_long != day:
            out.append((i, 1, 0, 0.0, l[i] - 0.1 * a1[i], 0.0, 0))
            last_long = day
    return out


@njit(cache=True)
def s3_orders(o, h, l, c, a1, k, d_tr):
    out = []
    for i in range(25, len(c) - 1):
        day = k[i]
        if day < 1 or np.isnan(a1[i]):
            continue
        tr = d_tr[day - 1]
        b = i - 1  # displacement
        body = abs(c[b] - o[b])
        if body < 1.2 * a1[i]:
            continue
        if tr == 1 and c[b] > o[b] and l[i] > h[i - 2] and c[b] > np.max(h[b - 20:b]):
            for j in range(b - 1, b - 6, -1):
                if c[j] < o[j]:
                    sl = l[j] - 0.1 * a1[i]
                    if h[j] - sl >= 0.3 * a1[i]:
                        out.append((i, 1, 1, h[j], sl, 0.0, 48))
                    break
        if tr == -1 and c[b] < o[b] and h[i] < l[i - 2] and c[b] < np.min(l[b - 20:b]):
            for j in range(b - 1, b - 6, -1):
                if c[j] > o[j]:
                    sl = h[j] + 0.1 * a1[i]
                    if sl - l[j] >= 0.3 * a1[i]:
                        out.append((i, -1, 1, l[j], sl, 0.0, 48))
                    break
    return out


@njit(cache=True)
def hvn_overlap(h, l, v, e, zl, zh):
    """FRVP poslednich 120 svicek 1h do indexu e: kryje se zona [zl, zh] s HVN (kos >= 80. percentil)?"""
    s = e - 119
    if s < 0:
        return False
    lo = np.min(l[s:e + 1])
    hi = np.max(h[s:e + 1])
    if hi <= lo:
        return False
    nb = 50
    w = (hi - lo) / nb
    prof = np.zeros(nb)
    for m in range(s, e + 1):
        b0 = min(nb - 1, int((l[m] - lo) / w))
        b1 = min(nb - 1, int((h[m] - lo) / w))
        share = v[m] / (b1 - b0 + 1)
        for b in range(b0, b1 + 1):
            prof[b] += share
    thr = np.sort(prof)[int(0.8 * nb)]
    for b in range(nb):
        if prof[b] >= thr:
            bl = lo + b * w
            bh = bl + w
            if bh >= zl and bl <= zh:
                return True
    return False


@njit(cache=True)
def s4_orders(h, l, v, h4o, h4h, h4l, h4c, a4, end4, h4day, d_tr):
    out = []
    for b in range(15, len(h4c) - 1):
        a = a4[b - 1]
        if np.isnan(a) or a <= 0:
            continue
        g = b + 1  # odchod ze zakladny
        day = h4day[g]
        if day < 1:
            continue
        tr = d_tr[day - 1]
        if h4h[b] - h4l[b] > 0.6 * a or abs(h4c[g] - h4o[g]) < 1.5 * a:
            continue
        e = end4[g]
        if tr == 1 and h4c[g] > h4h[b] and h4c[g] > h4o[g]:
            if hvn_overlap(h, l, v, e, h4l[b], h4h[b]):
                out.append((e, 1, 1, h4h[b], h4l[b] - 0.1 * a, 0.0, 60))
        if tr == -1 and h4c[g] < h4l[b] and h4c[g] < h4o[g]:
            if hvn_overlap(h, l, v, e, h4l[b], h4h[b]):
                out.append((e, -1, 1, h4l[b], h4h[b] + 0.1 * a, 0.0, 60))
    return out


@njit(cache=True)
def day_profile(h, l, v, s, e):
    """POC, VAH, VAL z 1h svicek s..e (vcetne), 40 kosu, value area 70 %."""
    lo = np.min(l[s:e + 1])
    hi = np.max(h[s:e + 1])
    nb = 40
    if hi <= lo:
        return np.nan, np.nan, np.nan
    w = (hi - lo) / nb
    prof = np.zeros(nb)
    for m in range(s, e + 1):
        b0 = min(nb - 1, int((l[m] - lo) / w))
        b1 = min(nb - 1, int((h[m] - lo) / w))
        share = v[m] / (b1 - b0 + 1)
        for b in range(b0, b1 + 1):
            prof[b] += share
    poc = int(np.argmax(prof))
    tot = prof.sum()
    acc = prof[poc]
    a, z = poc, poc
    while acc < 0.7 * tot and (a > 0 or z < nb - 1):
        up = prof[z + 1] if z < nb - 1 else -1.0
        dn = prof[a - 1] if a > 0 else -1.0
        if up >= dn:
            z += 1
            acc += up
        else:
            a -= 1
            acc += dn
    return lo + (poc + 0.5) * w, lo + (z + 1) * w, lo + a * w


@njit(cache=True)
def s5_orders(h, l, c, v, a1, k, d_start):
    nd = len(d_start)
    POC = np.full(nd, np.nan)
    VAH = np.full(nd, np.nan)
    VAL = np.full(nd, np.nan)
    for day in range(nd - 1):
        s = d_start[day]
        e = d_start[day + 1] - 1
        if e - s >= 5:
            POC[day], VAH[day], VAL[day] = day_profile(h, l, v, s, e)
    out = []
    last_long = -1
    last_short = -1
    for i in range(20, len(c) - 1):
        day = k[i]
        if day < 2 or np.isnan(a1[i]) or np.isnan(POC[day - 1]) or np.isnan(POC[day - 2]):
            continue
        vah, val, poc = VAH[day - 1], VAL[day - 1], POC[day - 1]
        if not (val <= VAH[day - 2] and vah >= VAL[day - 2]):  # vcerejsi value area se nekryje s predvcerejsi
            continue
        if l[i] < val and c[i] > val and last_long != day:
            sl = l[i] - 0.2 * a1[i]
            if poc - c[i] >= c[i] - sl > 0:
                out.append((i, 1, 0, 0.0, sl, poc, 0))
                last_long = day
        if h[i] > vah and c[i] < vah and last_short != day:
            sl = h[i] + 0.2 * a1[i]
            if c[i] - poc >= sl - c[i] > 0:
                out.append((i, -1, 0, 0.0, sl, poc, 0))
                last_short = day
    return out


@njit(cache=True)
def s6_orders(h, l, c, a1, hour, k, d_open, d_tr):
    out = []
    asia_day = -1
    ah = -1e18
    al = 1e18
    traded = -1
    for i in range(1, len(c) - 1):
        day = k[i]
        if day != asia_day:
            asia_day = day
            ah = -1e18
            al = 1e18
        if 1 <= hour[i] <= 8:
            ah = max(ah, h[i])
            al = min(al, l[i])
            continue
        if not (9 <= hour[i] <= 16) or ah < -1e17 or day < 1 or traded == day or np.isnan(a1[i]):
            continue
        tr = d_tr[day - 1]
        if tr == 1 and l[i] < al and c[i] > al and c[i] < d_open[day]:
            out.append((i, 1, 0, 0.0, l[i] - 0.1 * a1[i], 0.0, 0))
            traded = day
        elif tr == -1 and h[i] > ah and c[i] < ah and c[i] > d_open[day]:
            out.append((i, -1, 0, 0.0, h[i] + 0.1 * a1[i], 0.0, 0))
            traded = day
    return out


# ---------------------------------------------------------- simulace prikazu

@njit(cache=True)
def simulate(t, o, h, l, c, spread, sig, dirs, kind, price, sl0, tp0, valid, max_hold):
    n = len(c)
    m_ = len(sig)
    ent = np.full(m_, -1, np.int64)
    rs = np.zeros(m_)
    held = np.zeros(m_, np.int64)
    entry_px = np.zeros(m_)
    dist_out = np.zeros(m_)
    busy = -1
    for q in range(m_):
        i = sig[q]
        if i <= busy or i + 1 >= n:
            continue
        d = dirs[q]
        sl = sl0[q]
        j = i + 1
        intrabar = False
        e = 0.0
        ex = 0.0
        if kind[q] == 0:
            e = o[j] + d * spread[j] / 2
        else:
            j = -1
            for m in range(i + 1, min(n, i + 1 + valid[q])):
                hs = spread[m] / 2
                if d == 1 and l[m] + hs <= price[q]:
                    e = min(price[q], o[m] + hs)
                    j = m
                    intrabar = o[m] + hs > price[q]
                    break
                if d == -1 and h[m] - hs >= price[q]:
                    e = max(price[q], o[m] - hs)
                    j = m
                    intrabar = o[m] - hs < price[q]
                    break
            if j < 0:
                continue
        dist = (e - sl) * d
        if dist <= 2 * spread[j]:  # SL tesne u vstupu (nebo uz za nim) - nesmysl
            continue
        tp = tp0[q] if tp0[q] != 0 else e + d * 2.0 * dist
        if (tp - e) * d <= 0:
            continue
        m = j
        first = True
        while True:
            hs = spread[m] / 2
            if m > j and t[m] - t[m - 1] > 4 * 86400:
                ex = c[m - 1] - d * spread[m - 1] / 2
                m -= 1
                break
            if d == 1:
                if not first and o[m] - hs <= sl:
                    ex = o[m] - hs
                    break
                if l[m] - hs <= sl:
                    ex = sl
                    break
                if not (first and intrabar) and h[m] - hs >= tp:
                    ex = tp
                    break
            else:
                if not first and o[m] + hs >= sl:
                    ex = o[m] + hs
                    break
                if h[m] + hs >= sl:
                    ex = sl
                    break
                if not (first and intrabar) and l[m] + hs <= tp:
                    ex = tp
                    break
            if m - j >= max_hold or m == n - 1:
                ex = c[m] - d * hs
                break
            first = False
            m += 1
        ent[q] = j
        rs[q] = (ex - e) * d / dist
        held[q] = m - j
        entry_px[q] = e
        dist_out[q] = dist
        busy = m
    return ent, rs, held, entry_px, dist_out


def orders_for(sid, p):
    if sid == 1:
        return s1_orders(p["c"], p["v"], p["vavg"], p["a1"], p["k"], p["d_high"], p["d_low"], p["d_atr"], p["d_tr"])
    if sid == 2:
        return s2_orders(p["o"], p["h"], p["l"], p["c"], p["v"], p["vavg"], p["a1"], p["k"], p["d_high"], p["d_low"])
    if sid == 3:
        return s3_orders(p["o"], p["h"], p["l"], p["c"], p["a1"], p["k"], p["d_tr"])
    if sid == 4:
        return s4_orders(p["h"], p["l"], p["v"], p["h4o"], p["h4h"], p["h4l"], p["h4c"], p["a4"], p["end4"], p["h4day"], p["d_tr"])
    if sid == 5:
        return s5_orders(p["h"], p["l"], p["c"], p["v"], p["a1"], p["k"], p["d_start"])
    return s6_orders(p["h"], p["l"], p["c"], p["a1"], p["hour"], p["k"], p["d_open"], p["d_tr"])


def run_market(mk, df):
    p = prepare(df)
    b = broker[mk]
    spread = np.array(b["spreadByHour"], dtype=np.float64)[p["hour"]]
    out = []
    for sid in NAMES:
        od = orders_for(sid, p)
        if not len(od):
            continue
        a = np.array(od, dtype=np.float64)
        a = a[np.argsort(a[:, 0], kind="stable")]
        ent, rs, held, e, dist = simulate(p["t"], p["o"], p["h"], p["l"], p["c"], spread, a[:, 0].astype(np.int64),
                                          a[:, 1].astype(np.int64), a[:, 2].astype(np.int64), a[:, 3], a[:, 4], a[:, 5],
                                          a[:, 6].astype(np.int64), MAX_HOLD)
        ok = ent >= 0
        if not ok.any():
            continue
        d = a[ok, 1]
        days = held[ok] / 24.0
        swap_r = np.where(d == 1, b["swapLong"], b["swapShort"]) * e[ok] * days / dist[ok]
        out.append(pd.DataFrame({"time": df.index[ent[ok]], "market": mk, "strat": sid, "dir": d.astype(int),
                                 "R": rs[ok] + swap_r, "R_bez": rs[ok], "bars": held[ok]}))
    return out


def stats(tr):
    if len(tr) < 2:
        return dict(n=len(tr), win=0.0, meanR=0.0, t=0.0, pf=0.0, perDay=0.0)
    r = tr["R"].values
    g = pd.Series(r).groupby(tr["time"].dt.floor("D").values).sum()
    t = g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 2 and g.std() > 0 else 0.0
    w, lo = r[r > 0].sum(), -r[r < 0].sum()
    span = max((tr["time"].max() - tr["time"].min()).days, 1)
    return dict(n=len(r), win=100 * (r > 0).mean(), meanR=r.mean(), t=t, pf=w / lo if lo else np.inf, perDay=len(r) / span)


def fmt(s):
    return f"n={s['n']:>5}  win {s['win']:5.1f} %  prumer {s['meanR']:+.3f} R  t {s['t']:+.2f}  PF {s['pf']:.2f}"


def main():
    parts = []
    for mk in MARKETS:
        try:
            df = load_1h(mk)
        except Exception as e:
            print(f"   {mk:<12} data nejsou ({e})")
            continue
        if (df.index < SPLIT).sum() < 2 * 252 * 20:
            print(f"   {mk:<12} malo historie do 2023 ({df.index[0].date()}) - vynechan")
            continue
        print(f"   {mk:<12} {len(df):>6} svicek 1h od {df.index[0].date()}")
        parts += run_market(mk, df)
    tr = pd.concat(parts, ignore_index=True)
    tr.to_csv(os.path.join(DATA, "f5_obchody.csv"), index=False)
    sel, hold = tr[tr.time < SPLIT], tr[tr.time >= SPLIT]

    print("\n=== A) STRATEGIE NA VSECH TRZICH (se swapy) ===")
    verdicts = {}
    for sid, name in NAMES.items():
        a, h = stats(sel[sel.strat == sid]), stats(hold[hold.strat == sid])
        ok = h["n"] >= 100 and h["meanR"] > 0 and h["t"] >= 2.64 and h["pf"] >= 1.10 and a["meanR"] > 0
        verdicts[sid] = ok
        print(f" {name}\n    vyber   {fmt(a)}  obchodu/den {a['perDay']:.1f}\n    holdout {fmt(h)}  -> {'PROSLO' if ok else 'neproslo'}")

    print("\n=== B) STRATEGIE x TRH: vyber do 2023 -> holdout skupiny ===")
    rows = []
    for (sid, mk), x in sel.groupby(["strat", "market"]):
        s = stats(x)
        if s["n"] >= 40 and s["meanR"] >= 0.05 and s["t"] >= 2.0:
            hs = stats(hold[(hold.strat == sid) & (hold.market == mk)])
            rows.append({"strategie": NAMES[sid], "trh": mk, "v_n": s["n"], "v_win": s["win"], "v_R": s["meanR"], "v_t": s["t"],
                         "h_n": hs["n"], "h_win": hs["win"], "h_R": hs["meanR"], "h_t": hs["t"]})
    if rows:
        pick = pd.DataFrame(rows).sort_values("v_t", ascending=False)
        print(pick.round(2).to_string(index=False))
        keys = set(zip(pick.strategie, pick.trh))
        grp = hold[[(NAMES[s], m) in keys for s, m in zip(hold.strat, hold.market)]]
        g = stats(grp)
        okb = g["n"] >= 60 and g["meanR"] > 0 and g["t"] >= 2.33
        print(f"\n Vybrane dvojice v holdoutu dohromady: {fmt(g)} -> {'PROSLO' if okb else 'NEPROSLO'}")
        pick.to_csv(os.path.join(DATA, "f5_vybrane_dvojice.csv"), index=False)
    else:
        okb = False
        print(" Zadna dvojice strategie x trh nesplnila podminky vyberu.")

    print("\n=== Po trzich (holdout, se swapy) - jen pro predstavu ===")
    piv = hold.groupby(["market", "strat"]).R.agg(["count", "mean"]).unstack("strat")
    print(piv.round(2).to_string())
    json.dump({"A": {NAMES[k]: bool(v) for k, v in verdicts.items()}, "B": bool(okb)},
              open(os.path.join(DATA, "f5_verdikt.json"), "w"), ensure_ascii=False, indent=1)
    print("\nVERDIKT A:", ", ".join(f"{NAMES[k]}: {'PROSLO' if v else 'ne'}" for k, v in verdicts.items()))
    print("VERDIKT B:", "PROSLO" if okb else "NEPROSLO")


if __name__ == "__main__":
    main()
