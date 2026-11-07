"""
F24 - filtr volatility pro zive strategie (RSI(2) pullback, Pruraz F2). Plan predem ve vaultu (Vyzkum/F24 ...).
Spusteni: python -I f24_vol.py -> D:\\Trading bot\\research_data\\f24\\f24_souhrn.txt
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = r"D:\Trading bot"
RD = os.path.join(ROOT, "research_data")
OUT = os.path.join(RD, "f24")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
SPLIT = pd.Timestamp("2019-01-01")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


_VOL = {}


def vol_pct(mk):
    """Percentil 20denni volatility proti 252 dnum; hodnota pro den D je z dat do D-1."""
    if mk not in _VOL:
        df = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))
        c = df["close"].astype(float)
        r = np.log(c).diff()
        v = r.rolling(20).std()
        p = v.rolling(252).apply(lambda x: (x[:-1] < x[-1]).mean() if np.isfinite(x[-1]) else np.nan, raw=True)
        s = p.shift(1)
        s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
        _VOL[mk] = s
    return _VOL[mk]


def attach(T):
    T = T.copy()
    T["time"] = pd.to_datetime(T.time).dt.tz_localize(None)
    T["day"] = T.time.dt.normalize()
    T["vp"] = np.nan
    for mk, g in T.groupby("market"):
        s = vol_pct(mk)
        T.loc[g.index, "vp"] = s.reindex(g.day, method="ffill").to_numpy()
    return T.dropna(subset=["vp"])


def st(R):
    R = np.asarray(R, float)
    return dict(n=len(R), m=R.mean() if len(R) else np.nan, sd=R.std(ddof=1) if len(R) > 1 else np.nan)


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def report(name, T, keep_high):
    say(f"\n{name} (filtr: ponechat percentil {'>= 50' if keep_high else '< 50'})")
    res = {}
    for per, g in (("vývoj do 2018", T[T.time < SPLIT]), ("kontrola 2019+", T[T.time >= SPLIT])):
        k = g[g.vp >= 0.5] if keep_high else g[g.vp < 0.5]
        x = g[g.vp < 0.5] if keep_high else g[g.vp >= 0.5]
        sa, sk, sx = st(g.R), st(k.R), st(x.R)
        t = welch(k.R, x.R) if len(k) > 1 and len(x) > 1 else np.nan
        res[per] = dict(diff=sk["m"] - sx["m"], t=t, excl=sx["m"])
        say(f"   {per:15s} vše n {sa['n']:4d} {sa['m']:+.3f} R | ponechané n {sk['n']:4d} {sk['m']:+.3f} R (součet {k.R.sum():+6.1f}) "
            f"| vyřazené n {sx['n']:4d} {sx['m']:+.3f} R (součet {x.R.sum():+6.1f}) | rozdíl {sk['m'] - sx['m']:+.3f}, t {t:+.2f}")
    # popisne: kvartily volatility
    q = pd.cut(T.vp, [0, 0.25, 0.5, 0.75, 1.0001], labels=["0–25", "25–50", "50–75", "75–100"], include_lowest=True)
    say("   popisně po čtvrtinách percentilu (celé období):",
        ", ".join(f"{k}: n {len(g)} {g.R.mean():+.3f} R" for k, g in T.groupby(q, observed=True)))
    d, kk = res["vývoj do 2018"], res["kontrola 2019+"]
    c1 = d["diff"] > 0 and d["t"] >= 2.0
    c2 = kk["diff"] > 0
    c3 = kk["excl"] <= 0
    say(f"   ROZHODNUTÍ: 1) vývoj rozdíl > 0 a t >= 2: {'ANO' if c1 else 'NE'} ({d['diff']:+.3f}, t {d['t']:+.2f}); "
        f"2) kontrola rozdíl > 0: {'ANO' if c2 else 'NE'} ({kk['diff']:+.3f}); 3) vyřazené v kontrole <= 0: {'ANO' if c3 else 'NE'} ({kk['excl']:+.3f})")
    say(f"   => {'FILTR PROŠEL' if c1 and c2 and c3 else 'FILTR NEPROŠEL'}")


say("F24 Filtr volatility pro živé strategie (percentil 20denní volatility proti 252 dnům, z dat do předchozího dne)")
say("=" * 100)
a = pd.read_csv(os.path.join(RD, "f6_obchody.csv"))
rsi = attach(a[(a.strat == "MR1") & (a.dir == 1) & a.market.isin(["SPX500mini", "NAS100mini", "US30mini"])])
report("RSI(2) pullback – US indexy (živě)", rsi, keep_high=True)
eu = attach(a[(a.strat == "MR1") & (a.dir == 1) & a.market.isin(["GER_30mini", "GBR_100mini", "FRA_40mini", "EUR_50mini", "ESP_35mini"])])
if len(eu):
    report("RSI(2) pullback – evropské indexy (popisně, živě neběží)", eu, keep_high=True)
b = pd.read_csv(os.path.join(RD, "f4_obchody.csv"))
pr = attach(b[b.varianta.str.startswith("A ")])
report("Průraz F2 – 9 živých trhů", pr, keep_high=False)
open(os.path.join(OUT, "f24_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
