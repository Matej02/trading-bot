"""
F39 Momentum L=250 bez men (indexy, kovy, ropa). Plan predem ve vaultu: Vyzkum/Fronta napadu F35-F39.md (2026-11-19).
Spusteni: python -I f39_mom.py -> D:\\Trading bot\\research_data\\f39\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f39")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
LINES = []
IDX = ["SPX500mini", "NAS100mini", "US30mini", "GER_30mini", "FRA_40mini", "ESP_35mini", "GBR_100mini", "EUR_50mini"]
COM = ["XAUUSD", "XAGUSD", "XPTUSD", "CRUDE_OIL", "BRENT_OIL"]
DEV0, SPLIT = pd.Timestamp("1990-01-01"), pd.Timestamp("2019-01-01")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def yahoo(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))["close"].astype(float)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    d = d[d > 0].dropna()
    return d[d.index.day_of_week < 5]


def broker(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))
    h.index = pd.to_datetime(h.index)
    c = h.close.groupby(h.index.normalize()).last().astype(float)
    return c[c.index.day_of_week < 5]


def daily_R(mk, c, mode):
    """Denni R v jednotkach sigma60. mode 'mom' = znamenko 250denniho vynosu, 'long' = stale long."""
    b = L.BROKER[mk]
    ret = c.pct_change()
    sig = ret.rolling(60).std().shift(1)
    if mode == "mom":
        pos = np.sign(c.shift(1) / c.shift(251) - 1)
    else:
        pos = pd.Series(1.0, index=c.index)
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(c.iloc[-1])
    flip = (pos != pos.shift(1)).astype(float) * pos.shift(1).notna()
    n = np.where(c.index.day_of_week == 3, 3, 1)  # noc ze stredy na ctvrtek 3x
    swap = np.where(pos > 0, b["swapLong"], np.where(pos < 0, b["swapShort"], 0.0)) * n
    net = pos * ret - flip * rel + swap
    R = (net / sig).replace([np.inf, -np.inf], np.nan)
    return R[pos != 0].dropna()


def portfolio(mks, src, mode):
    cols = {}
    for mk in mks:
        c = yahoo(mk) if src == "yahoo" else broker(mk)
        cols[mk] = daily_R(mk, c, mode)
    return pd.DataFrame(cols).mean(axis=1).dropna()


def stat(x):
    x = np.asarray(x, float)
    m, s = x.mean(), x.std(ddof=1)
    return dict(n=len(x), m=m, t=m / s * np.sqrt(len(x)), sh=m / s * np.sqrt(252))


def fm(s):
    return f"dní {s['n']:5d} | průměr {s['m']:+.4f} R/den | t {s['t']:+.2f} | Sharpe {s['sh']:+.2f}"


say("F39 Momentum L=250 bez měn – 8 indexů + 5 komodit, riziko na trh podle σ60, náklady brokera (spread při otočení, swap)")
say("=" * 100)
ALL = IDX + COM
P = {(src, mode): portfolio(ALL, src, mode) for src in ("yahoo", "broker") for mode in ("mom", "long")}
S = {}
for nm, src, a, b in (("vyvoj", "yahoo", DEV0, SPLIT), ("kontrola", "yahoo", SPLIT, None), ("zdroj2", "broker", SPLIT, None)):
    for mode in ("mom", "long"):
        x = P[(src, mode)]
        x = x[(x.index >= a) & ((x.index < b) if b is not None else True)]
        S[(nm, mode)] = stat(x)
    say(f"{nm:9s} momentum:   {fm(S[(nm, 'mom')])}")
    say(f"{'':9s} stále long: {fm(S[(nm, 'long')])}")
G = {}
for gname, mks in (("indexy", IDX), ("komodity", COM)):
    x = portfolio(mks, "yahoo", "mom")
    x = x[x.index >= DEV0]
    G[gname] = stat(x)
    say(f"{gname:9s} (Yahoo 1990–2026): {fm(G[gname])}")
x = P[("yahoo", "mom")]
x = x[x.index >= DEV0]
say("Po letech (Yahoo, Sharpe): " + "  ".join(f"{y}:{g.mean() / g.std() * np.sqrt(252):+.1f}" for y, g in x.groupby(x.index.year)))
say("ROZHODNUTÍ podle pravidel zapsaných předem")
v, k, z = S[("vyvoj", "mom")], S[("kontrola", "mom")], S[("zdroj2", "mom")]
c = [("1) vývoj > 0 a t >= 2,0", v["m"] > 0 and v["t"] >= 2.0, f"{v['m']:+.4f}, t {v['t']:+.2f}"),
     ("2) kontrola > 0 a t >= 1,5", k["m"] > 0 and k["t"] >= 1.5, f"{k['m']:+.4f}, t {k['t']:+.2f}"),
     ("3) broker 2019+ > 0", z["m"] > 0, f"{z['m']:+.4f}"),
     ("4) lepší než stále long (vývoj i kontrola)", v["m"] > S[("vyvoj", "long")]["m"] and k["m"] > S[("kontrola", "long")]["m"],
      f"{v['m']:+.4f} vs {S[('vyvoj', 'long')]['m']:+.4f}; {k['m']:+.4f} vs {S[('kontrola', 'long')]['m']:+.4f}"),
     ("5) indexy i komodity > 0", G["indexy"]["m"] > 0 and G["komodity"]["m"] > 0, f"{G['indexy']['m']:+.4f}, {G['komodity']['m']:+.4f}")]
for nm, ok, val in c:
    say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
