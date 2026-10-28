"""
F6 / ukoly 2-3 - rodiny strategii s dolozenou vyhodou na dennim timeframu, overeni ve trech obdobich (2026-10-28).

PLAN STANOVENY PREDEM (pravidla i prahy se podle vysledku nemeni):
  Data: denni svicky Yahoo (research_f6_data.py), od 1995 (u starsich indexu Yahoo nema skutecny open).
  Signal na zavreni dne, VSTUP NA OTEVRENI DALSIHO DNE (bot zavreni vidi az po nem), vystupy taky na otevreni.
  Naklady: median spreadu brokera prepocteny na cenu Yahoo (/ priceScale), pul spreadu pri vstupu i vystupu;
  swapy podle kalendarnich dni drzeni. Riziko (1 R) = pocatecni stop. Jedna pozice na strategii a trh.
  Stop se kontroluje behem dne (gap pres stop = ven za otevreni).

  MR1 RSI(2) pullback v trendu (Connors): long RSI2 < 10 a zavreni nad SMA200 / short RSI2 > 90 a pod SMA200;
      ven pri zavreni nad (pod) SMA5; stop 3 ATR(20); nejdele 10 dni.
  MR2 IBS: long IBS = (C-L)/(H-L) < 0,2 a nad SMA200 / short IBS > 0,8 a pod SMA200; ven pri IBS > 0,8 (< 0,2)
      nebo po 3 dnech; stop 3 ATR.
  MR3 double seven: long zavreni pod minimem zavreni 7 dni a nad SMA200 / short nad maximem a pod SMA200;
      ven pri zavreni nad maximem (pod minimem) 7 dni; stop 3 ATR; nejdele 15 dni.
  TF1 Donchian 55/20 (zelvy): long zavreni nad 55dennim maximem / short pod minimem; ven pri zavreni pod
      20dennim minimem (nad maximem); pocatecni stop 2 ATR; bez TP.
  TF2 pruraz F2 s trailing stopem: zavreni nad 20dennim maximem a tydenni trend nahoru (EMA50 tydnu + sklon) /
      short zrcadlove; pocatecni stop 2 ATR, pak chandelier 3 ATR od nejvyssiho (nejnizsiho) zavreni; bez TP.
  SE1 turn-of-month: long od otevreni posledniho obchodniho dne mesice do otevreni 4. dne noveho; stop 3 ATR.
      (Jen long - jde o sezonnost akciovych indexu, testuje se ale na vsech skupinach.)

  Skupiny trhu predem: INDEXY (8), FOREX (24), KOMODITY (zlato, stribro, platina, ropa, brent), KRYPTO (BTC, ETH).
  Obdobi: VYBER do 2018, KONTROLA 2019-2023, HOLDOUT od 2024.
  PROSLO (strategie x skupina) = vyber n >= 100, prumer > 0, t >= 2,0 A kontrola n >= 50, prumer > 0, t >= 2,0
  A holdout prumer > 0 a PF >= 1,10. (Tri nezavisla obdobi - nahodou to projde jen zridka.)
  Uvadi se uspesnost a pomer prumerne vyhry k prumerne ztrate (cil uzivatele), rozhoduje prumer R.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from numba import njit

sys.stdout.reconfigure(line_buffering=True)

DATA = "research_data"
START = pd.Timestamp("1995-01-01")
P1, P2 = pd.Timestamp("2019-01-01"), pd.Timestamp("2024-01-01")
broker = json.load(open(os.path.join("simulator", "lib", "broker.json"), encoding="utf-8"))["markets"]
GROUPS = {
    "INDEXY": ["SPX500mini", "US30mini", "NAS100mini", "GER_30mini", "GBR_100mini", "FRA_40mini", "EUR_50mini", "ESP_35mini"],
    "KOMODITY": ["XAUUSD", "XAGUSD", "XPTUSD", "CRUDE_OIL", "BRENT_OIL"],
    "KRYPTO": ["BTCUSD", "ETHUSD"],
}
GROUPS["FOREX"] = [m for m in broker if m != "GAUUSD" and not any(m in g for g in GROUPS.values())]
GROUP_OF = {m: g for g, ms in GROUPS.items() for m in ms}
NAMES = {"MR1": "RSI(2) pullback v trendu", "MR2": "IBS", "MR3": "double seven", "TF1": "Donchian 55/20",
         "TF2": "pruraz F2 + trailing", "SE1": "turn-of-month"}


def load(mk):
    df = pd.read_pickle(os.path.join(DATA, f"f6_{mk}_1d.pkl"))
    df = df[df.index >= START]
    df = df[~((df.open == df.high) & (df.high == df.low) & (df.low == df.close))]  # dny bez obchodu
    return df


# ---------------------------------------------------------- indikatory

def sma(x, n):
    return pd.Series(x).rolling(n).mean().values


def rsi(c, n):
    d = np.diff(c, prepend=c[0])
    up = pd.Series(np.maximum(d, 0)).ewm(alpha=1 / n, adjust=False).mean().values
    dn = pd.Series(np.maximum(-d, 0)).ewm(alpha=1 / n, adjust=False).mean().values
    return 100 - 100 / (1 + up / np.where(dn == 0, 1e-12, dn))


def atr(h, l, c, n=20):
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    return sma(tr, n)


def weekly_trend(df):
    """+1/-1/0 z uzavrenych tydnu (EMA50 tydennich zavreni + sklon 3 tydny), znamy na zavreni dne."""
    wk = df.close.resample("W-FRI").last().dropna()
    e = wk.ewm(span=50, adjust=False).mean()
    tr = np.where((wk > e) & (e > e.shift(3)), 1, np.where((wk < e) & (e < e.shift(3)), -1, 0))
    s = pd.Series(tr, index=wk.index)
    s.iloc[:53] = 0
    # tyden konci v patek - plati od patecniho zavreni dal
    return s.reindex(df.index, method="ffill").fillna(0).astype(int).values


# ---------------------------------------------------------- engine
# exit_mode: 0 = zavreni pres SMA5, 1 = IBS, 2 = kanal (zavreni pres extrem xlo/xhi), 3 = jen cas, 4 = chandelier

@njit(cache=True)
def engine(o, h, l, c, a, sig, exit_mode, xlo, xhi, sma5, ibs, stop_k, trail_k, max_days, spread, at_close=False):
    n = len(c)
    ent = np.full(n, -1, np.int64)
    ext = np.full(n, -1, np.int64)
    rr = np.zeros(n)
    dd = np.zeros(n, np.int64)
    eprice = np.zeros(n)
    k = 0
    i = 0
    hs = spread / 2
    while i < n - 2:
        d = sig[i]
        if d == 0 or np.isnan(a[i]) or a[i] <= 0:
            i += 1
            continue
        j = i + 1
        e = (c[i] if at_close else o[j]) + d * hs
        risk = stop_k * a[i]
        stop = e - d * risk
        best = c[j]
        m = j
        ex = -1.0
        while True:
            # stop behem dne
            if d == 1 and l[m] <= stop:
                ex = min(o[m], stop) if (m > j or at_close) else stop
                ex -= hs
                break
            if d == -1 and h[m] >= stop:
                ex = max(o[m], stop) if (m > j or at_close) else stop
                ex += hs
                break
            if m >= n - 2:
                ex = c[m] - d * hs
                break
            # vystup na zavreni -> otevreni dalsiho dne
            out = False
            if exit_mode == 0:
                out = (c[m] > sma5[m]) if d == 1 else (c[m] < sma5[m])
            elif exit_mode == 1:
                out = (ibs[m] > 0.8) if d == 1 else (ibs[m] < 0.2)
            elif exit_mode == 2:
                out = (c[m] < xlo[m]) if d == 1 else (c[m] > xhi[m])
            elif exit_mode == 4:
                best = max(best, c[m]) if d == 1 else min(best, c[m])
                if not np.isnan(a[m]):
                    ns = best - d * trail_k * a[m]
                    stop = max(stop, ns) if d == 1 else min(stop, ns)
            if max_days > 0 and m - j + 1 >= max_days:
                out = True
            if out:
                if at_close:  # vystup na zavreni (CFD po zavreni burzy)
                    ex = c[m] - d * hs
                else:
                    ex = o[m + 1] - d * hs
                    m += 1
                break
            m += 1
        ent[k] = j
        ext[k] = m
        rr[k] = (ex - e) * d / risk
        dd[k] = m - j
        eprice[k] = e
        k += 1
        i = m  # dalsi signal az po vystupu
    return ent[:k], ext[:k], rr[:k], dd[:k], eprice[:k]


def signals(sid, df):
    o, h, l, c = (df[x].values.astype(np.float64) for x in ("open", "high", "low", "close"))
    n = len(c)
    s200 = sma(c, 200)
    up, dn = c > s200, c < s200
    rng = np.where(h - l > 0, h - l, np.nan)
    ibs = np.nan_to_num((c - l) / rng, nan=0.5)
    sig = np.zeros(n, np.int64)
    xlo = np.full(n, np.nan)
    xhi = np.full(n, np.nan)
    p = dict(exit_mode=3, stop_k=3.0, trail_k=0.0, max_days=0)
    if sid == "MR1":
        r = rsi(c, 2)
        sig[(r < 10) & up] = 1
        sig[(r > 90) & dn] = -1
        p.update(exit_mode=0, max_days=10)
    elif sid == "MR2":
        sig[(ibs < 0.2) & up] = 1
        sig[(ibs > 0.8) & dn] = -1
        p.update(exit_mode=1, max_days=3)
    elif sid == "MR3":
        lo7 = pd.Series(c).rolling(7).min().shift(1).values
        hi7 = pd.Series(c).rolling(7).max().shift(1).values
        sig[(c < lo7) & up] = 1
        sig[(c > hi7) & dn] = -1
        p.update(max_days=15)  # vystup resi engine_mr3 (long ven nad hi7, short pod lo7)
    elif sid == "TF1":
        hi55 = pd.Series(h).rolling(55).max().shift(1).values
        lo55 = pd.Series(l).rolling(55).min().shift(1).values
        sig[c > hi55] = 1
        sig[c < lo55] = -1
        xlo = pd.Series(l).rolling(20).min().shift(1).values
        xhi = pd.Series(h).rolling(20).max().shift(1).values
        p.update(exit_mode=2, stop_k=2.0)
    elif sid == "TF2":
        hi20 = pd.Series(h).rolling(20).max().shift(1).values
        lo20 = pd.Series(l).rolling(20).min().shift(1).values
        wt = weekly_trend(df)
        sig[(c > hi20) & (wt == 1)] = 1
        sig[(c < lo20) & (wt == -1)] = -1
        p.update(exit_mode=4, stop_k=2.0, trail_k=3.0)
    elif sid == "SE1":
        mon = df.index.month.values
        # signal na zavreni dne pred poslednim obchodnim dnem mesice -> vstup na otevreni posledniho dne
        last = np.zeros(n, bool)
        last[:-1] = mon[1:] != mon[:-1]
        sig[:-1][last[1:]] = 1
        p.update(exit_mode=3, max_days=4)
    return o, h, l, c, sig, xlo, xhi, sma(c, 5), ibs, p


@njit(cache=True)
def engine_mr3(o, h, l, c, a, sig, lo7, hi7, stop_k, max_days, spread, at_close=False):
    """Double seven: long ven pri zavreni nad hi7, short pri zavreni pod lo7."""
    n = len(c)
    ent = np.full(n, -1, np.int64)
    ext = np.full(n, -1, np.int64)
    rr = np.zeros(n)
    dd = np.zeros(n, np.int64)
    eprice = np.zeros(n)
    k = 0
    i = 0
    hs = spread / 2
    while i < n - 2:
        d = sig[i]
        if d == 0 or np.isnan(a[i]) or a[i] <= 0:
            i += 1
            continue
        j = i + 1
        e = (c[i] if at_close else o[j]) + d * hs
        risk = stop_k * a[i]
        stop = e - d * risk
        m = j
        while True:
            if d == 1 and l[m] <= stop:
                ex = (min(o[m], stop) if (m > j or at_close) else stop) - hs
                break
            if d == -1 and h[m] >= stop:
                ex = (max(o[m], stop) if (m > j or at_close) else stop) + hs
                break
            if m >= n - 2:
                ex = c[m] - d * hs
                break
            out = (c[m] > hi7[m]) if d == 1 else (c[m] < lo7[m])
            if m - j + 1 >= max_days:
                out = True
            if out:
                if at_close:  # vystup na zavreni (CFD po zavreni burzy)
                    ex = c[m] - d * hs
                else:
                    ex = o[m + 1] - d * hs
                    m += 1
                break
            m += 1
        ent[k] = j
        ext[k] = m
        rr[k] = (ex - e) * d / risk
        dd[k] = m - j
        eprice[k] = e
        k += 1
        i = m
    return ent[:k], ext[:k], rr[:k], dd[:k], eprice[:k]


def spread_yahoo(mk):
    b = broker[mk]
    return float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0)


def run(sid, mk, df, cost_mult=1.0, at_close=False, side=0):
    o, h, l, c, sig, xlo, xhi, s5, ibs, p = signals(sid, df)
    a = atr(h, l, c, 20)
    if side:
        sig = np.where(sig == side, sig, 0)
    sp = spread_yahoo(mk) * cost_mult
    if sid == "MR3":
        lo7 = pd.Series(c).rolling(7).min().shift(1).values
        hi7 = pd.Series(c).rolling(7).max().shift(1).values
        ent, ext, r, days, e = engine_mr3(o, h, l, c, a, sig, lo7, hi7, p["stop_k"], p["max_days"], sp, at_close)
    else:
        ent, ext, r, days, e = engine(o, h, l, c, a, sig, p["exit_mode"], xlo, xhi, s5, ibs, p["stop_k"], p["trail_k"],
                                      p["max_days"], sp, at_close)
    if not len(ent):
        return pd.DataFrame()
    b = broker[mk]
    dirs = sig[ent - 1]
    cal = (df.index[ext] - df.index[ent]).days.values.astype(float)
    risk = p["stop_k"] * a[ent - 1]
    swap_r = np.where(dirs == 1, b["swapLong"], b["swapShort"]) * e * cal * cost_mult / risk
    return pd.DataFrame({"time": df.index[ent], "market": mk, "group": GROUP_OF[mk], "strat": sid, "dir": dirs,
                         "R": r + swap_r, "R_bez": r, "days": days, "cal": cal})


def stats(x):
    if len(x) < 2:
        return dict(n=len(x), win=0.0, meanR=0.0, t=0.0, pf=0.0, payoff=0.0, perYear=0.0, days=0.0)
    r = x["R"].values
    g = pd.Series(r).groupby(x["time"].dt.to_period("W").astype(str).to_numpy()).sum()  # shluky po tydnech
    t = g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 2 and g.std() > 0 else 0.0
    w, lo = r[r > 0], r[r <= 0]
    years = max((x["time"].max() - x["time"].min()).days / 365.25, 0.5)
    return dict(n=len(r), win=100 * (r > 0).mean(), meanR=r.mean(), t=t,
                pf=w.sum() / -lo.sum() if lo.sum() < 0 else np.inf,
                payoff=(w.mean() / -lo.mean()) if len(w) and len(lo) and lo.mean() < 0 else np.inf,
                perYear=len(r) / years, days=x["days"].mean())


def fmt(s):
    return (f"n={s['n']:>5} win {s['win']:5.1f}% prum {s['meanR']:+.3f}R t {s['t']:+5.2f} PF {s['pf']:4.2f} "
            f"vyhra/ztrata {s['payoff']:4.2f} drzi {s['days']:4.1f}d")


def all_trades(cost_mult=1.0):
    parts = []
    for mk in GROUP_OF:
        try:
            df = load(mk)
        except FileNotFoundError:
            continue
        for sid in NAMES:
            t = run(sid, mk, df, cost_mult)
            if len(t):
                parts.append(t)
    return pd.concat(parts, ignore_index=True)


def main():
    tr = all_trades()
    tr.to_csv(os.path.join(DATA, "f6_obchody.csv"), index=False)
    res = []
    for sid, name in NAMES.items():
        print(f"\n=== {sid} {name} ===")
        for grp in GROUPS:
            x = tr[(tr.strat == sid) & (tr.group == grp)]
            a, b, c_ = stats(x[x.time < P1]), stats(x[(x.time >= P1) & (x.time < P2)]), stats(x[x.time >= P2])
            ok = (a["n"] >= 100 and a["meanR"] > 0 and a["t"] >= 2.0 and b["n"] >= 50 and b["meanR"] > 0 and b["t"] >= 2.0
                  and c_["meanR"] > 0 and c_["pf"] >= 1.10)
            res.append({"strat": sid, "group": grp, "ok": ok, **{f"v_{k}": v for k, v in a.items()},
                        **{f"k_{k}": v for k, v in b.items()}, **{f"h_{k}": v for k, v in c_.items()}})
            print(f" {grp:<9} vyber   {fmt(a)}\n {'':<9} kontrola {fmt(b)}\n {'':<9} holdout {fmt(c_)}"
                  f"  {'<<< PROSLO' if ok else ''}")
    pd.DataFrame(res).to_csv(os.path.join(DATA, "f6_vysledky.csv"), index=False)
    ok = [f"{r['strat']} {r['group']}" for r in res if r["ok"]]
    print("\nPROSLO:", ", ".join(ok) if ok else "nic")


if __name__ == "__main__":
    main()
