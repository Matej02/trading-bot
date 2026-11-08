"""
F33 - rebalancovani na konci mesice (SPY vs TLT od zacatku mesice -> obchod proti vitezi poslední 3 dny). Plan predem ve vaultu.
Spusteni: python -I f33_rebal.py -> D:\\Trading bot\\research_data\\f33\\f33_souhrn.txt
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
OUT = os.path.join(RD, "f33")
sys.stdout.reconfigure(encoding="utf-8")
SPLIT = pd.Timestamp("2019-01-01")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def etf(tk):
    j = json.load(open(os.path.join(OUT, "yahoo", f"{tk}.json")))["chart"]["result"][0]
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


say("F33 Rebalancování na konci měsíce – SPY vs TLT od začátku měsíce do L−3; |rozdíl| >= 2 p. b. → obchod proti vítězi L−2 … L")
say("hodnoceno po měsících (průměr SPX500 a NAS100), R = výsledek / ATR20")
say("=" * 100)
say(f"signálních měsíců: {len(SIG)} z {len(mend) - 1}; short (akcie vedly) {sum(1 for v in SIG.values() if v[0] == -1)}, long {sum(1 for v in SIG.values() if v[0] == 1)}")
Y = pd.concat([trades(m, yahoo(m)) for m in ("SPX500mini", "NAS100mini")], ignore_index=True)
B = pd.concat([trades(m, broker_daily(m)) for m in ("SPX500mini", "NAS100mini")], ignore_index=True)
O = {m: trades(m, yahoo(m)) for m in ("US30mini", "GER_30mini")}
Y.to_pickle(os.path.join(OUT, "f33_yahoo.pkl"))
S = {}
for name, T in (("vyvoj", Y[Y.t < SPLIT]), ("kontrola", Y[Y.t >= SPLIT]), ("zdroj2", B[B.t >= SPLIT])):
    M = per_month(T)
    S[name] = LB.st(M.R)
    S[name + "_long"] = LB.st(M.R_long)
    say(f"\n{name.upper():9s} měsíců:", LB.fmt(S[name]))
    say("   stále long stejné dny:", LB.fmt(S[name + "_long"]))
    say("   short signály / long signály:", LB.fmt(LB.st(M.R[M.d == -1])), "/", LB.fmt(LB.st(M.R[M.d == 1])))
for m, T in O.items():
    S[m] = LB.st(T.R)
    say(f"\n{m:11s} (celé období):", LB.fmt(S[m]), "| stále long:", LB.fmt(LB.st(T.R_long)))
allM = per_month(Y)
say("\nPo letech (Yahoo, po měsících):")
for y, g in allM.groupby(allM.t.dt.year):
    say(f"   {y}: n {len(g):2d}  {g.R.mean():+.3f} R  součet {g.R.sum():+5.2f} R")
say("\nROZHODNUTÍ podle pravidel zapsaných předem")
c = [("1) vývoj > 0 a t >= 2,0", S["vyvoj"]["m"] > 0 and S["vyvoj"]["t"] >= 2.0, f"{S['vyvoj']['m']:+.3f} R, t {S['vyvoj']['t']:+.2f}"),
     ("2) kontrola > 0 a t >= 1,5", S["kontrola"]["m"] > 0 and S["kontrola"]["t"] >= 1.5, f"{S['kontrola']['m']:+.3f} R, t {S['kontrola']['t']:+.2f}"),
     ("3) US30 i DAX > 0", S["US30mini"]["m"] > 0 and S["GER_30mini"]["m"] > 0, f"US30 {S['US30mini']['m']:+.3f}, DAX {S['GER_30mini']['m']:+.3f}"),
     ("4) lepší než stále long (vývoj i kontrola)", S["vyvoj"]["m"] > S["vyvoj_long"]["m"] and S["kontrola"]["m"] > S["kontrola_long"]["m"],
      f"{S['vyvoj']['m']:+.3f} vs {S['vyvoj_long']['m']:+.3f}; {S['kontrola']['m']:+.3f} vs {S['kontrola_long']['m']:+.3f}"),
     ("5) druhý zdroj > 0", S["zdroj2"]["m"] > 0, f"{S['zdroj2']['m']:+.3f} R")]
for name, ok, val in c:
    say(f"   {name}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
open(os.path.join(OUT, "f33_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
