"""
F79 Halloween na indexech, F80 RSI(2) na kryptu, F81 RSI(2) na rope. Plan predem ve vaultu:
Vyzkum/F79 az F81 Halloween, RSI(2) na kryptu a na rope.md (commit 448cc3f).
Spusteni: python -I f79_f81.py -> D:\\Trading bot\\research_data\\f79\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402

LB, L = F.LB, F.L
RD = F.RD
OUT = os.path.join(RD, "f79")
os.makedirs(OUT, exist_ok=True)
SPLIT = pd.Timestamp("2019-01-01")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def costs(mk, d):
    b = L.BROKER.get(mk)
    if b is None:                                   # LTC, XRP, NATGAS: bez udaju brokera (plan)
        return 0.003, (L.BROKER["BTCUSD"]["swapLong"] if mk in ("LTCUSD", "XRPUSD") else 0.0)
    return float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1]), b["swapLong"]


def broker_all_days(mk):
    """Krypto: denni svicky ze vsech 7 dni (UTC)."""
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))
    h.index = pd.to_datetime(h.index)
    g = h.groupby(h.index.normalize())
    return pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()}).dropna()


def yahoo_all_days(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))[["open", "high", "low", "close"]].astype(float)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    ok = (d.high >= d.low) & (d.close > 0) & (d.low <= d.close) & (d.close <= d.high)
    return d[ok].dropna()


def cal_nights(d0, d1):
    return int((d1 - d0).days)


def atr20(d):
    pc = d.close.shift(1)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    return tr.rolling(20).mean()


def rsi2_run(mk, d, crypto):
    rel, swap = costs(mk, d)
    nights = cal_nights if crypto else F.nights
    c = d.close
    sma200, sma5 = c.rolling(200).mean(), c.rolling(5).mean()
    rsi = F.rsi_wilder(c)
    A = atr20(d).to_numpy()
    O, Lo, C, S5 = d.open.to_numpy(), d.low.to_numpy(), c.to_numpy(), sma5.to_numpy()
    up = (c > sma200).to_numpy()
    sig = up & (rsi < 10).to_numpy()
    idx, n = d.index, len(d)

    def one(i):
        e = i + 1
        if e >= n or not A[i] > 0:
            return None
        E = O[e]
        risk = 3 * A[i]
        stop = E - risk
        for k in range(e, min(e + 10, n)):
            if Lo[k] <= stop:
                X = min(stop, O[k]) if k > e else stop
                break
            if C[k] > S5[k] or k == e + 9:
                X = C[k]
                break
        else:
            return None
        net = (X - E) - rel * (E + X) / 2 + swap * E * nights(idx[e], idx[k])
        return k, net / risk

    rs, rb, busy = [], [], -1
    for i in range(200, n - 1):
        if up[i]:
            r = one(i)
            if r is not None:
                rb.append((idx[i + 1], r[1]))
        if sig[i] and i > busy:
            r = one(i)
            if r is not None:
                rs.append((idx[i + 1], r[1]))
                busy = r[0]
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def halloween_run(mk, d):
    rel, swap = costs(mk, d)
    A = atr20(d)
    ym = d.index.to_period("M")
    rs, rb = [], []
    for p, g in d.groupby(ym):
        e, k = g.index[0], g.index[-1]
        i = d.index.get_loc(e)
        if i < 21 or not A.iloc[i - 1] > 0 or len(g) < 15:
            continue
        E, X = g.open.iloc[0], g.close.iloc[-1]
        risk = 3 * A.iloc[i - 1]
        net = (X - E) - rel * (E + X) / 2 + swap * E * F.nights(e, k)
        rb.append((e, net / risk))
        if p.month in (11, 12, 1, 2, 3, 4):
            rs.append((e, net / risk))
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def ev(pairs, a, b):
    """pairs = [(S, B), ...] po trzich -> prumer po dnech vstupu, vyber obdobi, Welch."""
    s = pd.concat([p[0] for p in pairs]).groupby("day").R.mean()
    bb = pd.concat([p[1] for p in pairs]).groupby("day").R.mean()
    sel = lambda x: x[(x.index >= pd.Timestamp(a)) & ((x.index < pd.Timestamp(b)) if b is not None else True)]  # noqa: E731
    s, bb = sel(s), sel(bb)
    diff, t = F.welch(s, bb) if len(s) > 1 else (np.nan, np.nan)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


def show(nm, v):
    say(f"{nm:22s} signal:   {LB.fmt(v['sig'])}")
    say(f"{'':22s} srovnani: {LB.fmt(v['base'])}")
    say(f"{'':22s} previs {v['diff']:+.3f} R, t {v['t']:+.2f}")


def years(v):
    pos, line = [], []
    for y in sorted(set(v["s"].index.year)):
        sy, by = v["s"][v["s"].index.year == y], v["b"][v["b"].index.year == y]
        if len(sy) and len(by):
            dy = sy.mean() - by.mean()
            pos.append(dy > 0)
            line.append(f"{y}:{dy:+.2f}")
    for i in range(0, len(line), 10):
        say("   " + "  ".join(line[i:i + 10]))
    share = float(np.mean(pos)) if pos else 0.0
    say(f"previs kladny v {sum(pos)} z {len(pos)} let ({share:.0%})")
    return share


def verdict(nm, c):
    say("BODY 1-5: " + " ".join("ANO" if x else "ne" for x in c) + f"  => {'VYHODA (proslo vse)' if all(c) else 'BEZ VYHODY'}")
    return nm, sum(c), all(c)


def ok_sig(v, tmin):
    return v["sig"]["m"] > 0 and v["diff"] > 0 and (tmin is None or v["t"] >= tmin)


def f79():
    say("=" * 100)
    say("F79 Halloween: long cely mesic v listopadu az dubnu, srovnani vsechny mesice")
    US, EU = ["SPX500mini", "NAS100mini", "US30mini"], ["GER_30mini", "GBR_100mini", "FRA_40mini"]
    Y = [halloween_run(mk, F.yahoo(mk)) for mk in US]
    Bk = [halloween_run(mk, F.broker(mk)) for mk in US]
    dev, kon, br = ev(Y, "1900-01-01", SPLIT), ev(Y, SPLIT, None), ev(Bk, SPLIT, None)
    show("vyvoj (Yahoo do 2018)", dev)
    show("kontrola 2019-26", kon)
    show("broker 2019-26", br)
    O = {mk: ev([halloween_run(mk, F.yahoo(mk))], "1900-01-01", None) for mk in EU}
    for mk, v in O.items():
        say(f"{mk:11s}: signal {LB.fmt(v['sig'])} | previs {v['diff']:+.3f}, t {v['t']:+.2f}")
    share = years(ev(Y, "1900-01-01", None))
    return verdict("F79 Halloween", [ok_sig(dev, 2.0), ok_sig(kon, 1.5), all(v["diff"] > 0 for v in O.values()), ok_sig(br, None), share >= 0.55])


def f80():
    say("=" * 100)
    say("F80 RSI(2) na kryptu (vsech 7 dni): nad SMA200 a RSI(2) < 10, ven nad SMA5 / 10 dni / stop 3 ATR")
    btc = broker_all_days("BTCUSD")
    P = [rsi2_run("BTCUSD", btc, True)]
    dev, kon = ev(P, "2012-01-01", SPLIT), ev(P, SPLIT, None)
    yb = ev([rsi2_run("BTCUSD", yahoo_all_days("BTCUSD"), True)], "2015-01-01", None)
    show("vyvoj broker 2012-18", dev)
    show("kontrola broker 2019-26", kon)
    show("Yahoo BTC 2015-26", yb)
    O = {mk: ev([rsi2_run(mk, broker_all_days(mk), True)], "1900-01-01", None) for mk in ("ETHUSD", "LTCUSD", "XRPUSD")}
    for mk, v in O.items():
        say(f"{mk:11s}: signal {LB.fmt(v['sig'])} | previs {v['diff']:+.3f}, t {v['t']:+.2f}")
    share = years(ev(P, "2012-01-01", None))
    return verdict("F80 RSI(2) krypto", [ok_sig(dev, 2.0), ok_sig(kon, 1.5), all(v["diff"] > 0 for v in O.values()), ok_sig(yb, None), share >= 0.55])


def f81():
    say("=" * 100)
    say("F81 RSI(2) na rope (pracovni dny): nad SMA200 a RSI(2) < 10, ven nad SMA5 / 10 dni / stop 3 ATR")
    Y = [rsi2_run("CRUDE_OIL", F.yahoo("CRUDE_OIL"), False)]
    dev, kon = ev(Y, "1900-01-01", SPLIT), ev(Y, SPLIT, None)
    br = ev([rsi2_run("CRUDE_OIL", F.broker("CRUDE_OIL"), False)], SPLIT, None)
    show("vyvoj Yahoo do 2018", dev)
    show("kontrola Yahoo 2019-26", kon)
    show("broker 2019-26", br)
    O = {"BRENT_OIL": ev([rsi2_run("BRENT_OIL", F.yahoo("BRENT_OIL"), False)], "1900-01-01", None),
         "NATGAS": ev([rsi2_run("NATGAS", F.broker("NATGAS"), False)], "1900-01-01", None)}
    for mk, v in O.items():
        say(f"{mk:11s}: signal {LB.fmt(v['sig'])} | previs {v['diff']:+.3f}, t {v['t']:+.2f}")
    share = years(ev(Y, "1900-01-01", None))
    return verdict("F81 RSI(2) ropa", [ok_sig(dev, 2.0), ok_sig(kon, 1.5), all(v["diff"] > 0 for v in O.values()), ok_sig(br, None), share >= 0.55])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    res = [f79(), f80(), f81()]
    say("=" * 100)
    for nm, k, ok in res:
        say(f"{nm:22s} {k}/5  {'PROSLO' if ok else 'neproslo'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES) + "\n")
