"""
F29 - krypto momentum 28 dni, tydenni prepocet (long/flat). Plan predem ve vaultu (Vyzkum/F29 ...).
Spusteni: python -I f29_krypto.py -> D:\\Trading bot\\research_data\\f29\\f29_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f29")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
SPLIT = pd.Timestamp("2022-01-01")
OTHERS = ["XRPUSD", "LTCUSD", "ADAUSD", "BNBUSD", "DOGEUSD", "LINKUSD", "SOLUSD"]
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def yahoo(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))[["open", "close"]].astype(float)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return d[(d.open > 0) & (d.close > 0)]


def binance(mk):
    d = pd.read_pickle(os.path.join(RD, "f7", f"{mk}_M1.pkl"))
    t = pd.to_datetime(d.t, unit="s") if np.issubdtype(d.t.dtype, np.integer) else pd.to_datetime(d.t)
    g = d.groupby(t.dt.normalize().to_numpy())
    return pd.DataFrame({"open": g.o.first(), "close": g.c.last()}).astype(float)


def costs(mk):
    b = L.BROKER.get(mk) or L.BROKER["BTCUSD"]
    src = mk if mk in L.BROKER else "BTCUSD"
    ref = float(np.median(yahoo(src).close.iloc[-30:]))
    rel = float(np.median(L.BROKER[src]["spreadByHour"])) / L.BROKER[src].get("priceScale", 1.0) / ref
    return rel, b["swapLong"]


def weekly(d, rel, swl, lookback=28, mode="long"):
    """Tydenni vynosy strategie (pondeli otevreni -> dalsi pondeli otevreni) a stale-long."""
    mon = d.index[d.index.dayofweek == 0]
    rows = []
    prev = 0
    prev_bh = 0
    for i in range(len(mon) - 1):
        m0, m1 = mon[i], mon[i + 1]
        if (m1 - m0).days != 7 or m0 not in d.index or m1 not in d.index:
            prev = 0
            prev_bh = 0
            continue
        past = m0 - pd.Timedelta(days=lookback + 1)
        sun = m0 - pd.Timedelta(days=1)
        if past not in d.index or sun not in d.index:
            continue
        mom = d.close[sun] / d.close[past] - 1
        pos = (1 if mom > 0 else 0) if mode == "long" else (1 if mom > 0 else -1)
        ret = d.open[m1] / d.open[m0] - 1
        sw = swl * 7 if pos == 1 else (swl * 7 if pos == -1 else 0.0)   # short: swap BTC je symetricky, pro jednoduchost stejny
        r = pos * ret - rel / 2 * abs(pos - prev) + (sw if pos != 0 else 0.0)
        rb = ret - rel / 2 * abs(1 - prev_bh) + swl * 7
        rows.append(dict(week=m0, pos=pos, ret=ret, r=r, bh=rb))
        prev, prev_bh = pos, 1
    return pd.DataFrame(rows).set_index("week")


def ew(frames, col):
    return pd.concat([f[col].rename(i) for i, f in enumerate(frames)], axis=1).mean(axis=1)


def stw(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    m, sd = x.mean(), x.std(ddof=1)
    return dict(n=n, m=m, t=m / sd * np.sqrt(n), sh=m / sd * np.sqrt(52), tot=np.prod(1 + x) - 1)


def f(s):
    return f"týdnů {s['n']:4d} | {s['m'] * 100:+.3f} %/týden | t {s['t']:+.2f} | Sharpe {s['sh']:+.2f} | celkem {s['tot'] * 100:+.0f} %"


say("F29 Krypto momentum – long na týden, když výnos za 28 dní > 0 (jinak mimo trh), náklady + swap brokera")
say("=" * 100)
W = {}
for mk in ("BTCUSD", "ETHUSD"):
    rel, swl = costs(mk)
    say(f"   {mk}: spread {rel * 100:.3f} % ceny, swap long {swl * 100:+.4f} %/den ({swl * 7 * 100:+.3f} %/týden)")
    W[("y", mk)] = weekly(yahoo(mk), rel, swl)
    W[("y_ls", mk)] = weekly(yahoo(mk), rel, swl, mode="ls")
    W[("b", mk)] = weekly(binance(mk), rel, swl)
relb, swlb = costs("BTCUSD")
for mk in OTHERS:
    W[("b", mk)] = weekly(binance(mk), relb, swlb)
res = {}
for name, keys, lo, hi in (("VÝVOJ Yahoo do 2021", [("y", "BTCUSD"), ("y", "ETHUSD")], None, SPLIT),
                           ("KONTROLA Yahoo 2022+", [("y", "BTCUSD"), ("y", "ETHUSD")], SPLIT, None),
                           ("DRUHÝ ZDROJ Binance 2022-09+", [("b", "BTCUSD"), ("b", "ETHUSD")], None, None),
                           ("JINÉ MINCE Binance 2022-09+", [("b", m) for m in OTHERS], None, None)):
    fr = []
    for k in keys:
        x = W[k]
        if lo is not None:
            x = x[x.index >= lo]
        if hi is not None:
            x = x[x.index < hi]
        fr.append(x)
    s, b = stw(ew(fr, "r")), stw(ew(fr, "bh"))
    res[name] = (s, b)
    say(f"\n{name}")
    say("   momentum: ", f(s), f"| v trhu {np.mean([x.pos.mean() for x in fr]):.0%} týdnů")
    say("   stále long:", f(b))
    for k, x in zip(keys, fr):
        say(f"     {k[1]:8s} momentum {stw(x.r)['m'] * 100:+.3f} %/t (Sharpe {stw(x.r)['sh']:+.2f}) | stále long {stw(x.bh)['m'] * 100:+.3f} %/t (Sharpe {stw(x.bh)['sh']:+.2f})")
ls = [W[("y_ls", m)] for m in ("BTCUSD", "ETHUSD")]
say("\nPopisně long/short (Yahoo): vývoj", f(stw(ew([x[x.index < SPLIT] for x in ls], "r"))),
    "| kontrola", f(stw(ew([x[x.index >= SPLIT] for x in ls], "r"))))
say("\nROZHODNUTÍ podle pravidel zapsaných předem")
dv, kt, z2, ot = (res[k][0] for k in ("VÝVOJ Yahoo do 2021", "KONTROLA Yahoo 2022+", "DRUHÝ ZDROJ Binance 2022-09+", "JINÉ MINCE Binance 2022-09+"))
dvb, ktb = res["VÝVOJ Yahoo do 2021"][1], res["KONTROLA Yahoo 2022+"][1]
c = [("1) vývoj > 0 a t >= 2,0", dv["m"] > 0 and dv["t"] >= 2.0, f"t {dv['t']:+.2f}"),
     ("2) kontrola > 0 a t >= 1,5", kt["m"] > 0 and kt["t"] >= 1.5, f"t {kt['t']:+.2f}"),
     ("3) jiné mince > 0", ot["m"] > 0, f"{ot['m'] * 100:+.3f} %/týden"),
     ("4) Sharpe lepší než stále long (vývoj i kontrola)", dv["sh"] > dvb["sh"] and kt["sh"] > ktb["sh"],
      f"{dv['sh']:+.2f} vs {dvb['sh']:+.2f}; {kt['sh']:+.2f} vs {ktb['sh']:+.2f}"),
     ("5) druhý zdroj > 0", z2["m"] > 0, f"{z2['m'] * 100:+.3f} %/týden")]
for name, ok, val in c:
    say(f"   {name}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
open(os.path.join(OUT, "f29_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
