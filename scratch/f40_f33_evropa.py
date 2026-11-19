"""
F40 - F33 (rebalancovani na konci mesice) na evropskych indexech FTSE, CAC, EuroStoxx, IBEX.
Plan predem ve vaultu: Vyzkum/F40 F33 na dalsich indexech.md (2026-11-19). Pravidlo F33 beze zmeny.
Spusteni: python -I f40_f33_evropa.py -> D:\Trading bot\research_data\f40\souhrn.txt
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f40")
os.makedirs(OUT, exist_ok=True)
YDIR = os.path.join(RD, "f33")
sys.stdout.reconfigure(encoding="utf-8")
SPLIT = pd.Timestamp("2019-01-01")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def etf(tk):
    j = json.load(open(os.path.join(YDIR, "yahoo", f"{tk}.json")))["chart"]["result"][0]
    t = pd.to_datetime(j["timestamp"], unit="s").normalize()
    return pd.Series(j["indicators"]["adjclose"][0]["adjclose"], index=t, dtype=float).dropna()


def yahoo(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))[["open", "high", "low", "close"]].astype(float)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    ok = (d.high >= d.low) & (d.low <= d.open) & (d.open <= d.high) & (d.low <= d.close) & (d.close <= d.high) & (d.close > 0)
    return d[ok].dropna()


def broker_daily(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))
    h.index = pd.to_datetime(h.index)
    g = h.groupby(h.index.normalize())
    d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()}).dropna()
    return d[d.index.dayofweek < 5]


def nights(d0, d1):
    days = pd.date_range(d0 + pd.Timedelta(days=1), d1, freq="D")
    wd = days.dayofweek
    return int(((wd < 5) & (wd != 3)).sum() + 3 * (wd == 3).sum())


SPY, TLT = etf("SPY"), etf("TLT")
cal = SPY.index
mend = cal[np.r_[cal.month[1:] != cal.month[:-1], True]]          # posledni obchodni den mesice (podle SPY)
SIG = {}
for k in range(1, len(mend)):
    L_ = mend[k]
    pos = cal.get_loc(L_)
    if pos < 4:
        continue
    d_sig = cal[pos - 3]                                            # L-3
    prev_end = mend[k - 1]
    rs = SPY[d_sig] / SPY[prev_end] - 1
    rb = TLT[d_sig] / TLT[prev_end] - 1
    diff = rs - rb
    if abs(diff) >= 0.02:
        SIG[(L_.year, L_.month)] = (-1 if diff > 0 else 1, d_sig, cal[pos - 2], L_, diff)


def trades(mk, d):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    pc = d.close.shift(1)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    atr = tr.rolling(20).mean().shift(1)
    rows = []
    for (y, m), (dd, d_sig, d_in, d_out, diff) in SIG.items():
        x = d[(d.index >= d_in) & (d.index <= d_out)]
        if len(x) < 2 or x.index[-1].month != m:
            continue
        a = atr.get(x.index[0], np.nan)
        if not a > 0:
            continue
        E, X = x.open.iloc[0], x.close.iloc[-1]
        n = nights(x.index[0], x.index[-1])
        cost = rel * (E + X) / 2
        net = dd * (X - E) - cost + (b["swapLong"] if dd == 1 else b["swapShort"]) * E * n
        net_l = (X - E) - cost + b["swapLong"] * E * n
        rows.append(dict(mk=mk, ym=(y, m), t=x.index[0], d=dd, diff=diff, R=net / a, R_long=net_l / a))
    return pd.DataFrame(rows)


def per_month(T):
    return T.groupby("ym").agg(R=("R", "mean"), R_long=("R_long", "mean"), t=("t", "first"), d=("d", "first"))



EU = ["GBR_100mini", "FRA_40mini", "EUR_50mini", "ESP_35mini"]
US = ["SPX500mini", "NAS100mini"]
say("F40 – pravidlo F33 beze změny na FTSE, CAC, EuroStoxx, IBEX; hodnoceno po měsících (průměr 4 trhů), R = výsledek / ATR20")
say("=" * 100)
say(f"signálních měsíců: {len(SIG)}")
Y = pd.concat([trades(m, yahoo(m)) for m in EU], ignore_index=True)
B = pd.concat([trades(m, broker_daily(m)) for m in EU], ignore_index=True)
Y = Y[Y.t >= pd.Timestamp("2003-01-01")]
S = {}
for name, T in (("vyvoj", Y[Y.t < SPLIT]), ("kontrola", Y[Y.t >= SPLIT]), ("zdroj2", B[B.t >= SPLIT])):
    M = per_month(T)
    S[name] = LB.st(M.R)
    S[name + "_long"] = LB.st(M.R_long)
    say("")
    say(f"{name.upper():9s} měsíců:", LB.fmt(S[name]))
    say("   stále long stejné dny:", LB.fmt(S[name + "_long"]))
    say("   short signály / long signály:", LB.fmt(LB.st(M.R[M.d == -1])), "/", LB.fmt(LB.st(M.R[M.d == 1])))
say("")
for m in EU:
    T = Y[Y.mk == m]
    S[m] = LB.st(T.R)
    say(f"{m:11s} (2003–2026): {LB.fmt(S[m])} | stále long: {LB.fmt(LB.st(T.R_long))}")
U = pd.concat([trades(m, yahoo(m)) for m in US], ignore_index=True)
mu, me = per_month(U).R, per_month(Y).R
j = pd.concat([mu.rename("us"), me.rename("eu")], axis=1).dropna()
say("")
say(f"Popis: korelace měsíčních R Evropa vs. SPX/NAS = {j.us.corr(j.eu):+.2f} (n {len(j)})")
both = (j.us + j.eu) / 2
say(f"Popis: kombinace US + Evropa po měsících: {LB.fmt(LB.st(both))} | jen US: {LB.fmt(LB.st(j.us))}")
allM = per_month(Y)
say("")
say("Po letech (Evropa, po měsících):")
say("   " + "  ".join(f"{y}:{g.R.mean():+.2f}" for y, g in allM.groupby(allM.t.dt.year)))
say("")
say("ROZHODNUTÍ podle pravidel zapsaných předem")
c = [("1) vývoj > 0 a t >= 2,0", S["vyvoj"]["m"] > 0 and S["vyvoj"]["t"] >= 2.0, f"{S['vyvoj']['m']:+.3f} R, t {S['vyvoj']['t']:+.2f}"),
     ("2) kontrola > 0 a t >= 1,5", S["kontrola"]["m"] > 0 and S["kontrola"]["t"] >= 1.5, f"{S['kontrola']['m']:+.3f} R, t {S['kontrola']['t']:+.2f}"),
     ("3) každý ze 4 trhů > 0", all(S[m]["m"] > 0 for m in EU), ", ".join(f"{m[:3]} {S[m]['m']:+.3f}" for m in EU)),
     ("4) lepší než stále long (vývoj i kontrola)", S["vyvoj"]["m"] > S["vyvoj_long"]["m"] and S["kontrola"]["m"] > S["kontrola_long"]["m"],
      f"{S['vyvoj']['m']:+.3f} vs {S['vyvoj_long']['m']:+.3f}; {S['kontrola']['m']:+.3f} vs {S['kontrola_long']['m']:+.3f}"),
     ("5) druhý zdroj > 0", S["zdroj2"]["m"] > 0, f"{S['zdroj2']['m']:+.3f} R")]
for name, ok, val in c:
    say(f"   {name}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
