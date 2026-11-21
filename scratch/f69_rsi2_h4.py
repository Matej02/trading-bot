"""
F69 RSI(2) na H4 US indexu (pravidlo F42 prenesene na H4). Plan predem ve vaultu: Vyzkum/F69 RSI(2) na H4 US indexu.md (2026-11-21).
Spusteni: python -I f69_rsi2_h4.py -> D:\\Trading bot\\research_data\\f69\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import f58_f59 as T58  # noqa: E402
import f60_evropa_drift as T60  # noqa: E402

LB, L = F.LB, F.L
OUT = os.path.join(F.RD, "f69")
os.makedirs(OUT, exist_ok=True)
LINES = []
S19, S10 = pd.Timestamp("2019-01-01"), pd.Timestamp("2010-11-01")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def ok(nm, c, val):
    say(f"   {nm}: {'ANO' if c else 'NE'} ({val})")
    return c


def to_h4(h):
    h = h.copy()
    h.index = pd.DatetimeIndex(h.index).tz_convert("UTC").tz_localize(None) if pd.DatetimeIndex(h.index).tz is not None else h.index
    r = h.resample("4h")
    d = pd.DataFrame({"open": r.open.first(), "high": r.high.max(), "low": r.low.min(), "close": r.close.last()}).dropna()
    return d[d.index.day_of_week < 5]


def run_h4(mk, d, maxd=10, thr=10):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    c = d.close
    sma200, sma5 = c.rolling(200).mean(), c.rolling(5).mean()
    rsi = F.rsi_wilder(c)
    pc = c.shift(1)
    atr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean()
    O, Lo, C = d.open.to_numpy(), d.low.to_numpy(), c.to_numpy()
    S5, A = sma5.to_numpy(), atr.to_numpy()
    up = (c > sma200).to_numpy()
    sig = up & (rsi < thr).to_numpy()
    idx, n = d.index, len(d)

    def one(i):
        e = i + 1
        if e >= n or not A[i] > 0 or (idx[e] - idx[i]).days > 4:
            return None
        E, risk = O[e], 3 * A[i]
        stop = E - risk
        for k in range(e, min(e + maxd, n)):
            if Lo[k] <= stop:
                X = min(stop, O[k]) if k > e else stop
                break
            if C[k] > S5[k] or k == e + maxd - 1:
                X = C[k]
                break
        else:
            return None
        net = (X - E) - rel * (E + X) / 2 + b["swapLong"] * E * F.nights(idx[e].normalize(), idx[k].normalize())
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
    return pd.DataFrame(rs, columns=["day", "R"]).assign(mk=mk), pd.DataFrame(rb, columns=["day", "R"]).assign(mk=mk)


def daily_rsi2_days(mk):
    """Dny (data) do 5 obchodnich dni po dennim signalu RSI(2) (Yahoo)."""
    d = F.yahoo(mk)
    s = (d.close > d.close.rolling(200).mean()) & (F.rsi_wilder(d.close) < 10)
    pos = np.flatnonzero(s.to_numpy())
    out = set()
    for p in pos:
        for k in range(0, 6):
            if p + k < len(d):
                out.add(d.index[p + k])
    return out


def ev(pairs, a=None, b=None, excl=None):
    Ss, Bs = [], []
    for mk, d in pairs:
        s, bb = run_h4(mk, d)
        if excl is not None:
            s = s[~s.day.dt.normalize().isin(excl[mk])]
        Ss.append(s)
        Bs.append(bb)
    s, bb = pd.concat(Ss), pd.concat(Bs)
    for x in (s, bb):
        pass
    if a is not None:
        s, bb = s[s.day >= a], bb[bb.day >= a]
    if b is not None:
        s, bb = s[s.day < b], bb[bb.day < b]
    sd, bd = s.groupby("day").R.mean(), bb.groupby("day").R.mean()
    diff, t = F.welch(sd, bd)
    return dict(sig=LB.st(sd), base=LB.st(bd), diff=diff, t=t, s=sd, b=bd)


def main():
    say("F69 RSI(2) NA H4 – zavření H4 nad SMA200 a RSI(2) < 10 → long otevření další H4, ven nad SMA5 / stop 3 ATR / 10 svíček")
    say("srovnání = stejné vstupy/výstupy na všech H4 nad SMA200; R = výsledek / 3 ATR(H4)")
    say("=" * 100)
    HD = [(mk, to_h4(T60.hd_index(mk))) for mk in ("SPX500mini", "NAS100mini")]
    BR = [(mk, to_h4(T58.br_h1(mk))) for mk in ("SPX500mini", "NAS100mini", "US30mini")]
    R = {"vyvoj": ev(HD, S10, S19), "kontrola": ev(HD, S19, None), "broker": ev(BR, S19, None)}
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    for mk, d in HD + BR[2:]:
        v = ev([(mk, d)])
        say(f"   {mk:12s} {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    excl = {mk: daily_rsi2_days(mk) for mk in ("SPX500mini", "NAS100mini")}
    ind = ev(HD, excl=excl)
    say(f"bez dnů po denním signálu RSI(2): signál {LB.fmt(ind['sig'])} | převis {ind['diff']:+.3f}, t {ind['t']:+.2f}")
    full = ev(HD)
    ys = sorted(set(full["s"].index.year))
    g = pd.Series({y: full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean() for y in ys})
    share = float((g > 0).mean())
    say("po letech převis: " + "  ".join(f"{y}:{v:+.3f}" for y, v in g.items()))
    say(f"převis kladný v {int((g > 0).sum())} z {len(g)} let ({share:.0%})")
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    c = [ok("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ok("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ok("3) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
         ok("4) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}"),
         ok("5) bez dnů po denním RSI(2) převis > 0", ind["diff"] > 0, f"{ind['diff']:+.3f}")]
    say(f"   => {'VÝHODA (prošlo vše)' if all(c) else 'BEZ VÝHODY'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
