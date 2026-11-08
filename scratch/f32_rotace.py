"""
F32 - rotace podle relativni sily (mesicne long 3 nejsilnejsi z 15 podle 126d vynosu / vol). Plan predem ve vaultu (Vyzkum/F32 ...).
Spusteni: python -I f32_rotace.py -> D:\\Trading bot\\research_data\\f32\\f32_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f32")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
UA = ["SPX500mini", "NAS100mini", "US30mini", "GER_30mini", "GBR_100mini", "FRA_40mini", "XAUUSD", "XAGUSD", "CRUDE_OIL",
      "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"]
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def yahoo(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))[["open", "high", "low", "close"]].astype(float)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    ok = (d.high >= d.low) & (d.low <= d.open) & (d.open <= d.high) & (d.low <= d.close) & (d.close <= d.high) & (d.close > 0)
    return d[ok].dropna()[["open", "close"]]


def broker_daily(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))
    h.index = pd.to_datetime(h.index)
    g = h.groupby(h.index.normalize())
    d = pd.DataFrame({"open": g.open.first(), "close": g.close.last()}).dropna()
    return d[d.index.dayofweek < 5]


def nights(d0, d1):
    days = pd.date_range(d0 + pd.Timedelta(days=1), d1, freq="D")
    wd = days.dayofweek
    return int(((wd < 5) & (wd != 3)).sum() + 3 * (wd == 3).sum())


def run(data, k=3, ls=False, start=None, end=None):
    """Mesicni vynosy portfolia (rebalance prvni obchodni den mesice, open -> open dalsiho rebalancu)."""
    cal = sorted(set().union(*[set(d.index) for d in data.values()]))
    cal = pd.DatetimeIndex(cal)
    reb = cal[np.r_[True, cal.month[1:] != cal.month[:-1]]]
    if start is not None:
        reb = reb[reb >= start]
    if end is not None:
        reb = reb[reb < end]
    cost = {}
    for mk, d in data.items():
        b = L.BROKER[mk]
        cost[mk] = (float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1]), b["swapLong"], b["swapShort"])
    rows, prev_pos, prev_bh = [], {}, set()
    for i in range(len(reb) - 1):
        t0, t1 = reb[i], reb[i + 1]
        sc, rets = {}, {}
        for mk, d in data.items():
            past = d[d.index < t0]
            if len(past) < 130:
                continue
            c = past.close.to_numpy()
            lr = np.diff(np.log(c[-127:]))
            sd = lr.std()
            a0 = d[d.index >= t0]
            a1 = d[d.index >= t1]
            if not sd > 0 or len(a0) == 0 or len(a1) == 0 or a0.index[0] >= t1:
                continue
            sc[mk] = (c[-1] / c[-127] - 1) / sd
            rets[mk] = (a1.open.iloc[0] / a0.open.iloc[0] - 1, a0.index[0], a1.index[0])
        if len(sc) < 2 * k + 1:
            prev_pos, prev_bh = {}, set()
            continue
        order = sorted(sc, key=sc.get, reverse=True)
        pos = {m: 1 for m in order[:k]}
        if ls:
            pos.update({m: -1 for m in order[-k:]})
        w = 1.0 / len(pos)
        r = 0.0
        for m, dd in pos.items():
            rel, swl, sws = cost[m]
            ret, d0, d1 = rets[m]
            r += w * (dd * ret + (swl if dd == 1 else sws) * nights(d0, d1))
            if prev_pos.get(m) != dd:
                r -= w * rel / 2 * (2 if m in prev_pos else 1)
        for m, dd in prev_pos.items():
            if m not in pos:
                r -= w * cost[m][0] / 2
        # srovnani: stejne vazeny long vsech dostupnych trhu (buy & hold, naklady jen pri vstupu trhu)
        wb = 1.0 / len(rets)
        rb = 0.0
        for m, (ret, d0, d1) in rets.items():
            rb += wb * (ret + cost[m][1] * nights(d0, d1))
            if m not in prev_bh:
                rb -= wb * cost[m][0] / 2
        rows.append(dict(t=t0, r=r, bh=rb, top=",".join(order[:k])))
        prev_pos, prev_bh = pos, set(rets)
    return pd.DataFrame(rows).set_index("t")


def stm(x):
    x = np.asarray(x, float)
    n, m, sd = len(x), x.mean(), x.std(ddof=1)
    return dict(n=n, m=m, t=m / sd * np.sqrt(n), sh=m / sd * np.sqrt(12), tot=np.prod(1 + x) - 1, dd=dd(x))


def dd(x):
    eq = np.cumprod(1 + np.asarray(x))
    return float((1 - eq / np.maximum.accumulate(eq)).max())


def f(s):
    return f"měsíců {s['n']:3d} | {s['m'] * 100:+.3f} %/měs | t {s['t']:+.2f} | Sharpe {s['sh']:+.2f} | celkem {s['tot'] * 100:+.0f} % | max propad {s['dd'] * 100:.0f} %"


say("F32 Rotace – měsíčně long 3 nejsilnější z 15 trhů (126d výnos / volatilita), náklady + swap")
say("=" * 100)
YA = {m: yahoo(m) for m in UA}
allm = sorted(p[3:-7] for p in os.listdir(RD) if p.startswith("f6_") and p.endswith("_1d.pkl"))
UB = [m for m in allm if m not in UA and m not in ("BTCUSD", "ETHUSD") and m in L.BROKER]
YB = {m: yahoo(m) for m in UB}
S = {}
for name, data, k_ls, lo, hi in (("VÝVOJ Yahoo 2007–2018 (vesmír A)", YA, False, pd.Timestamp("2007-01-01"), pd.Timestamp("2019-01-01")),
                                 ("KONTROLA Yahoo 2019+ (vesmír A)", YA, False, pd.Timestamp("2019-01-01"), None),
                                 ("VESMÍR B Yahoo 2019+", YB, False, pd.Timestamp("2019-01-01"), None)):
    P = run(data, ls=k_ls, start=lo - pd.Timedelta(days=1) if lo is not None else None, end=hi)
    P = P[(P.index >= lo) & ((P.index < hi) if hi is not None else True)]
    P.to_pickle(os.path.join(OUT, f"f32_{name.split()[0]}_{name.split()[-1].strip(')')}.pkl"))
    s, b = stm(P.r), stm(P.bh)
    S[name] = (s, b)
    say(f"\n{name}")
    say("   rotace:     ", f(s))
    say("   všechny long:", f(b))
    say("   nejčastěji v top 3:", pd.Series(",".join(P.top).split(",")).value_counts().head(5).to_dict())
BR = {}
for m in UA:
    try:
        BR[m] = broker_daily(m)
    except Exception as e:
        say(f"   {m}: chybí H1 brokera ({e})")
P2 = run(BR)
P2.to_pickle(os.path.join(OUT, "f32_broker.pkl"))
s2, b2 = stm(P2.r), stm(P2.bh)
say("\nDRUHÝ ZDROJ broker H1 → denní (vesmír A)")
say("   rotace:     ", f(s2))
say("   všechny long:", f(b2))
for name, lo, hi in (("vývoj", pd.Timestamp("2007-01-01"), pd.Timestamp("2019-01-01")), ("kontrola", pd.Timestamp("2019-01-01"), None)):
    P = run(YA, ls=True, start=lo - pd.Timedelta(days=1), end=hi)
    P = P[P.index >= lo]
    say(f"\nPopisně long/short 3+3 ({name}):", f(stm(P.r)))
say("\nROZHODNUTÍ podle pravidel zapsaných předem")
dv, dvb = S["VÝVOJ Yahoo 2007–2018 (vesmír A)"]
kt, ktb = S["KONTROLA Yahoo 2019+ (vesmír A)"]
ub = S["VESMÍR B Yahoo 2019+"][0]
c = [("1) vývoj > 0 a t >= 2,0", dv["m"] > 0 and dv["t"] >= 2.0, f"t {dv['t']:+.2f}"),
     ("2) kontrola > 0 a t >= 1,5", kt["m"] > 0 and kt["t"] >= 1.5, f"t {kt['t']:+.2f}"),
     ("3) vesmír B v kontrole > 0", ub["m"] > 0, f"{ub['m'] * 100:+.3f} %/měs"),
     ("4) Sharpe vyšší než všechny long (vývoj i kontrola)", dv["sh"] > dvb["sh"] and kt["sh"] > ktb["sh"],
      f"{dv['sh']:+.2f} vs {dvb['sh']:+.2f}; {kt['sh']:+.2f} vs {ktb['sh']:+.2f}"),
     ("5) druhý zdroj > 0", s2["m"] > 0, f"{s2['m'] * 100:+.3f} %/měs")]
for name, ok, val in c:
    say(f"   {name}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
open(os.path.join(OUT, "f32_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
