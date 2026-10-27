"""
F2 - hledani setupu s VYSOKOU USPESNOSTI a kladnym vysledkem po nakladech, vic timeframu (2026-10-27).

Cil uzivatele: malo obchodu (klidne 1-2 denne), ale s co nejvyssi sanci na uspech; RRR idealne 1:2,
pri vysoke uspesnosti klidne 1:1. Meritkem je prumerny vysledek v R po nakladech (uspesnost sama
nestaci - pri 1:2 je zlom kolem 33 %, pri 1:1 kolem 50 %); mezi tim, co projde, se razi podle uspesnosti.

PLAN STANOVENY PREDEM (nemeni se podle vysledku):
  Trhy: BTCUSD, ETHUSD (Binance), XAUUSD, EURUSD, GBPUSD, USDJPY, SPX500mini, NAS100mini, GER_30mini (MT5).
  Vstupni timeframe 15m / 1h / 4h / 1d; filtr vyssiho timeframu (15m->4h, 1h->1d, 4h->1t, 1d->1t):
  trend = close nad/pod EMA50 a EMA50 roste/klesa; varianta "bez filtru".
  Rodiny vstupu (vzdy na uzavrene svicce, vstup na otevreni dalsi):
    pullback  - RSI(14) se vrati nad 40 (long) / pod 60 (short)
    bb_navrat - knot pres Bollingerovo pasmo (20, 2) a zavreni zpet uvnitr
    proraz    - zavreni nad maximem / pod minimem poslednich 20 svicek
    rsi2      - RSI(2) pod 10 (long) / nad 90 (short)
  Vystup: SL = k x ATR(14), k in {1, 1.5, 2}; TP = RRR x SL, RRR in {1, 1.5, 2}; nejdele 48 svicek.
  Naklady: zivy spread brokera v dane hodine (simulator/lib/broker.json) - long za ask, ven za bid.
  Jedna pozice na trh a setup najednou. Swapy se nepocitaji (drzeni vetsinou do 2 dnu) - poznamka u vysledku.

  Setup = rodina x timeframe x filtr x k x RRR, hodnoceny NAPRIC vsemi trhy (288 setupu).
  Vyber: obchody do 2023-12-31; n >= 200, prumer > 0; 5 nejlepsich podle t (shluky po dnech).
  Holdout: 2024-01-01 az dnes. PROSLO = n >= 100, prumer R > 0, t >= 2.33 (Bonferroni pro 5), PF >= 1.10.
  Mezi tim, co projde, se razi podle uspesnosti.
"""

import itertools
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import requests
from numba import njit

sys.stdout.reconfigure(line_buffering=True)

DATA = "research_data"
SPLIT = pd.Timestamp("2024-01-01")
BINANCE = {"BTCUSD": "BTCUSDT", "ETHUSD": "ETHUSDT"}
MT5_MARKETS = ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "SPX500mini", "NAS100mini", "GER_30mini"]
TFS = {"15m": ("15min", "4h"), "1h": ("1h", "1D"), "4h": ("4h", "1W"), "1d": ("1D", "1W")}
TF_SEC = {"15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}
FAMILIES = ["pullback", "bb_navrat", "proraz", "rsi2"]
KS, RRRS, MAX_HOLD = (1.0, 1.5, 2.0), (1.0, 1.5, 2.0), 48
T_HOLD, N_SEL, N_HOLD, PF_HOLD, TOP = 2.33, 200, 100, 1.10, 5

broker = json.load(open(os.path.join("simulator", "lib", "broker.json"), encoding="utf-8"))["markets"]


# ---------------------------------------------------------- data

def binance(sym, tf, start="2019-01-01"):
    path = os.path.join(DATA, f"binance_{sym}_{tf}.pkl")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 86400:
        return pd.read_pickle(path)
    rows, t = [], int(pd.Timestamp(start, tz="UTC").timestamp() * 1000)
    while True:
        r = requests.get("https://data-api.binance.vision/api/v3/klines",
                         params={"symbol": sym, "interval": tf, "startTime": t, "limit": 1000}, timeout=30).json()
        if not r:
            break
        rows += r
        t = r[-1][0] + 1
        if len(r) < 1000:
            break
    df = pd.DataFrame([[x[0], *map(float, x[1:5])] for x in rows], columns=["time", "open", "high", "low", "close"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df = df.set_index("time").iloc[:-1]  # bez tvorici se svicky
    df.to_pickle(path)
    return df


def mt5(sym, tf):
    path = os.path.join(DATA, f"mt5_{sym.replace('&', 'and')}_{tf}.pkl")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 86400:
        return pd.read_pickle(path)
    import mt5_connector as mc
    if mc.mt5.terminal_info() is None:
        mc.connect()
    code = {"15m": mc.mt5.TIMEFRAME_M15, "1h": mc.mt5.TIMEFRAME_H1, "4h": mc.mt5.TIMEFRAME_H4, "1d": mc.mt5.TIMEFRAME_D1}[tf]
    mc.mt5.symbol_select(sym, True)
    r = mc.mt5.copy_rates_from_pos(sym, code, 0, 99000)
    df = pd.DataFrame(r)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("time")[["open", "high", "low", "close"]].astype(float).iloc[:-1]
    df.to_pickle(path)
    return df


def load(market, tf):
    return binance(BINANCE[market], tf) if market in BINANCE else mt5(market, tf)


# ---------------------------------------------------------- indikatory

def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().values


def rsi(close, n):
    d = np.diff(close, prepend=close[0])
    up = pd.Series(np.maximum(d, 0)).ewm(alpha=1 / n, adjust=False).mean().values
    dn = pd.Series(np.maximum(-d, 0)).ewm(alpha=1 / n, adjust=False).mean().values
    return 100 - 100 / (1 + up / np.where(dn == 0, 1e-12, dn))


def atr(h, l, c, n=14):
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    return pd.Series(tr).rolling(n).mean().values


def htf_trend(df, ltf_rule, htf_rule, ltf_sec):
    """+1 / -1 / 0 trend vyssiho timeframu, znamy az po UZAVRENI vyssi svicky (bez pohledu do budoucna)."""
    hh = df["close"].resample(htf_rule, label="left", closed="left").last().dropna()
    e = pd.Series(ema(hh.values, 50), index=hh.index)
    tr = np.where((hh > e) & (e > e.shift(3)), 1, np.where((hh < e) & (e < e.shift(3)), -1, 0))
    step = pd.Timedelta(htf_rule) if htf_rule != "1W" else pd.Timedelta(days=7)
    avail = pd.DataFrame({"t": hh.index + step, "tr": tr}).sort_values("t")
    dec = pd.DataFrame({"t": df.index + pd.Timedelta(seconds=ltf_sec)})  # rozhodnuti na konci LTF svicky
    m = pd.merge_asof(dec, avail, on="t", direction="backward")
    return m["tr"].fillna(0).astype(int).values


def signals(df, family):
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    sig = np.zeros(len(c), np.int8)
    if family == "pullback":
        r = rsi(c, 14)
        sig[1:][(r[:-1] < 40) & (r[1:] >= 40)] = 1
        sig[1:][(r[:-1] > 60) & (r[1:] <= 60)] = -1
    elif family == "bb_navrat":
        mid = pd.Series(c).rolling(20).mean().values
        sd = pd.Series(c).rolling(20).std().values
        sig[(l < mid - 2 * sd) & (c > mid - 2 * sd)] = 1
        sig[(h > mid + 2 * sd) & (c < mid + 2 * sd)] = -1
    elif family == "proraz":
        hi = pd.Series(h).rolling(20).max().shift(1).values
        lo = pd.Series(l).rolling(20).min().shift(1).values
        sig[c > hi] = 1
        sig[c < lo] = -1
    elif family == "rsi2":
        r = rsi(c, 2)
        sig[r < 10] = 1
        sig[r > 90] = -1
    return sig


# ---------------------------------------------------------- simulace (numba)

@njit(cache=True)
def simulate(t, o, h, l, c, spread, sig, a, k, rrr, max_hold, gap):
    n = len(c)
    ent = np.empty(n, np.int64)
    dirs = np.empty(n, np.int8)
    rs = np.empty(n)
    held = np.empty(n, np.int64)
    m_ = 0
    i = 0
    while i < n - 1:
        d = sig[i]
        if d == 0 or np.isnan(a[i]) or a[i] <= 0 or t[i + 1] - t[i] > gap:
            i += 1
            continue
        j = i + 1
        entry = o[j] + d * spread[j] / 2
        dist = k * a[i]
        sl = entry - d * dist
        tp = entry + d * rrr * dist
        m = j
        bars = 0
        ex = np.nan
        while True:
            hs = spread[m] / 2
            if m > j and t[m] - t[m - 1] > gap:  # dira v datech -> ven za posledni zname cene
                ex = c[m - 1] - d * spread[m - 1] / 2
                m -= 1
                break
            if d == 1:
                if m > j and o[m] - hs <= sl:
                    ex = o[m] - hs
                    break
                if l[m] - hs <= sl:
                    ex = sl
                    break
                if h[m] - hs >= tp:
                    ex = tp
                    break
            else:
                if m > j and o[m] + hs >= sl:
                    ex = o[m] + hs
                    break
                if h[m] + hs >= sl:
                    ex = sl
                    break
                if l[m] + hs <= tp:
                    ex = tp
                    break
            bars += 1
            if bars >= max_hold or m == n - 1:
                ex = c[m] - d * hs
                break
            m += 1
        ent[m_] = j
        dirs[m_] = d
        rs[m_] = (ex - entry) * d / dist
        held[m_] = bars
        m_ += 1
        i = max(m, i + 1)
    return ent[:m_], dirs[:m_], rs[:m_], held[:m_]


# ---------------------------------------------------------- hodnoceni

def stats(tr):
    if len(tr) < 2:
        return dict(n=len(tr), win=0.0, meanR=0.0, t=0.0, pf=0.0, perDay=0.0, bars=0.0)
    r = tr["R"].values
    day = tr["time"].dt.floor("D")
    g = pd.Series(r).groupby(day.values).sum()  # shluky po dnech (trhy se hybou spolu)
    t = g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 2 and g.std() > 0 else 0.0
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    span = max((tr["time"].max() - tr["time"].min()).days, 1)
    return dict(n=len(r), win=100 * (r > 0).mean(), meanR=r.mean(), t=t, pf=wins / losses if losses else np.inf,
                perDay=len(r) / span, bars=tr["bars"].mean())


def main():
    markets = list(BINANCE) + MT5_MARKETS
    trades = {}  # setup -> list of DataFrames
    for tf, (ltf_rule, htf_rule) in TFS.items():
        for mk in markets:
            try:
                df = load(mk, tf)
            except Exception as e:
                print(f"   {mk} {tf}: data nejsou ({e})")
                continue
            if len(df) < 500:
                continue
            spread = np.array(broker[mk]["spreadByHour"])[df.index.hour]  # zivy spread brokera v dane hodine
            t = (df.index.astype("int64") // 10**9).values.astype(np.int64)
            o, h, l, c = (df[x].values for x in ("open", "high", "low", "close"))
            a = atr(h, l, c)
            trend = htf_trend(df, ltf_rule, htf_rule, TF_SEC[tf])
            gap = TF_SEC[tf] * 4 + 3 * 86400  # vikend/svatek projde, dira v historii ne
            print(f"   {mk:<11} {tf:>3}: {len(df):>7} svicek od {df.index[0].date()}")
            for fam in FAMILIES:
                raw = signals(df, fam)
                for filt in ("trend", "bez"):
                    sig = raw if filt == "bez" else np.where(raw == trend, raw, 0).astype(np.int8)
                    for k, rrr in itertools.product(KS, RRRS):
                        e, d, r, b = simulate(t, o, h, l, c, spread, sig, a, k, rrr, MAX_HOLD, gap)
                        if len(e):
                            key = (fam, tf, filt, k, rrr)
                            trades.setdefault(key, []).append(pd.DataFrame(
                                {"time": df.index[e], "market": mk, "dir": d, "R": r, "bars": b}))

    rows = []
    for key, parts in trades.items():
        tr = pd.concat(parts, ignore_index=True)
        sel, hold = tr[tr["time"] < SPLIT], tr[tr["time"] >= SPLIT]
        rows.append({"rodina": key[0], "tf": key[1], "filtr": key[2], "k": key[3], "rrr": key[4],
                     **{f"v_{a}": b for a, b in stats(sel).items()}, **{f"h_{a}": b for a, b in stats(hold).items()}})
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(DATA, "f2_vysledky.csv"), index=False)

    print(f"\nSetupu otestovano: {len(res)}  (vsechny vysledky: {DATA}/f2_vysledky.csv)")
    show = ["rodina", "tf", "filtr", "k", "rrr", "v_n", "v_win", "v_meanR", "v_t", "v_pf", "v_perDay"]
    cand = res[(res["v_n"] >= N_SEL) & (res["v_meanR"] > 0)].sort_values("v_t", ascending=False)
    print(f"Ve vyberu kladnych s n >= {N_SEL}: {len(cand)} z {len(res)}")
    print("\nNEJVYSSI USPESNOST VE VYBERU (jen pro predstavu, n >= 200):")
    print(res[res["v_n"] >= N_SEL].sort_values("v_win", ascending=False)[show].head(8).round(3).to_string(index=False))
    print("\nTOP 5 PODLE t -> HOLDOUT 2024+:")
    top = cand.head(TOP).copy()
    top["PROSLO"] = (top["h_n"] >= N_HOLD) & (top["h_meanR"] > 0) & (top["h_t"] >= T_HOLD) & (top["h_pf"] >= PF_HOLD)
    cols = show + ["h_n", "h_win", "h_meanR", "h_t", "h_pf", "h_perDay", "h_bars", "PROSLO"]
    print(top[cols].round(3).to_string(index=False))
    ok = top[top["PROSLO"]].sort_values("h_win", ascending=False)
    print("\nVERDIKT:", f"{len(ok)} setup(u) proslo - serazeno podle uspesnosti" if len(ok) else "zadny setup neprosel holdoutem")
    if len(ok):
        print(ok[cols].round(3).to_string(index=False))
    top.to_csv(os.path.join(DATA, "f2_holdout.csv"), index=False)


if __name__ == "__main__":
    main()
