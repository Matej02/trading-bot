"""
F66 relativni navrat mezi 8 indexy brokera (tydne long nejslabsiho), F67 RSI(2) na 10 svetovych indexech (overeni F42),
F68 noc po vyraznem poklesu na US indexech. Plan predem ve vaultu:
Vyzkum/F66 az F68 Navrat k prumeru (relativni, RSI(2) ve svete, noc po poklesu).md (2026-11-21).
Spusteni: python -I f66_f68.py -> D:\\Trading bot\\research_data\\f66\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import f58_f59 as T58  # noqa: E402
import f65 as T65  # noqa: E402

LB, L = F.LB, F.L
OUT = os.path.join(F.RD, "f66")
os.makedirs(OUT, exist_ok=True)
US = ["SPX500mini", "NAS100mini", "US30mini"]
EU = ["GER_30mini", "GBR_100mini", "FRA_40mini", "EUR_50mini", "ESP_35mini"]
IDX8 = US + EU
D0 = pd.Timestamp("1990-01-01")
NY = "America/New_York"
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def ok(nm, c, val):
    say(f"   {nm}: {'ANO' if c else 'NE'} ({val})")
    return c


def clean(d, need_open=False):
    d = d[~((d.open == d.high) & (d.high == d.low) & (d.low == d.close))]
    if need_open:
        bad = (d.open - d.close.shift(1)).abs() < 1e-9
        share = bad.groupby(d.index.year).mean()
        d = d[d.index.year.isin(share[share <= 0.5].index)]
    return d


def costs(mk, d):
    """(rel spread pro vzorec rel*(E+X)/2, swap za noc relativne)."""
    if mk in L.BROKER:
        b = L.BROKER[mk]
        return float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1]), b["swapLong"]
    return 2 * T65.SPR, T65.SWAP


def atr20(d):
    pc = d.close.shift(1)
    return np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean()


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 else np.nan


def years_share(ex):
    g = ex.groupby(ex.index.year).mean()
    return float((g > 0).mean()), g


# ------------------------------------------------------------------ F66
def weekly(mk, d):
    rel, sw = costs(mk, d)
    A = atr20(d)
    z = (d.close - d.close.shift(5)) / A
    wk = d.index.to_period("W-FRI")
    last = pd.Series(np.r_[wk[1:] != wk[:-1], True], index=d.index)
    e = d[last.to_numpy()]
    zz, aa = z[last.to_numpy()], A[last.to_numpy()]
    E, X = e.close.to_numpy()[:-1], e.close.to_numpy()[1:]
    nts = np.array([F.nights(a, b) for a, b in zip(e.index[:-1], e.index[1:])])
    gap = np.array([(b - a).days for a, b in zip(e.index[:-1], e.index[1:])])
    R = ((X - E) - rel * (E + X) / 2 + sw * E * nts) / aa.to_numpy()[:-1]
    per = e.index[:-1].to_period("W-FRI")
    df = pd.DataFrame({"z": zz.to_numpy()[:-1], "R": R}, index=per)
    df = df[(gap <= 10) & np.isfinite(df.z) & np.isfinite(df.R)]
    return df[~df.index.duplicated()]


def ev66(frames, a=None, b=None):
    Z = pd.concat({k: v.z for k, v in frames.items()}, axis=1)
    Rr = pd.concat({k: v.R for k, v in frames.items()}, axis=1)
    m = Z.notna() & Rr.notna()
    Z, Rr = Z.where(m), Rr.where(m)
    keep = m.sum(axis=1) >= 4
    Z, Rr = Z[keep], Rr[keep]
    pick = Z.idxmin(axis=1)
    sig = pd.Series([Rr.loc[i, c] for i, c in pick.items()], index=Rr.index)
    base = Rr.mean(axis=1)
    ex = sig - base
    idx = ex.index.to_timestamp(how="end").normalize()
    sig.index = base.index = ex.index = idx
    msk = np.ones(len(ex), bool)
    if a is not None:
        msk &= idx >= a
    if b is not None:
        msk &= idx < b
    sig, base, ex = sig[msk], base[msk], ex[msk]
    return dict(sig=LB.st(sig), base=LB.st(base), diff=ex.mean(), t=tstat(ex), ex=ex, pick=pick[msk])


def f66():
    say("=" * 100)
    say("F66 RELATIVNÍ NÁVRAT – týdně long index s nejnižším 5denním výnosem v ATR; srovnání = průměr všech indexů týž týden")
    say("=" * 100)
    Y = {mk: weekly(mk, clean(F.yahoo(mk))) for mk in IDX8}
    B = {mk: weekly(mk, clean(F.broker(mk))) for mk in IDX8}
    W = {}
    for tk in T65.TICK:
        d, _ = T65.load(tk)
        W[tk] = weekly(tk, d)
    R = {"vyvoj": ev66(Y, D0, F.SPLIT), "kontrola": ev66(Y, F.SPLIT, None), "broker": ev66(B, F.SPLIT, None)}
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    oth = ev66(W)
    say(f"jiné trhy (10 světových, celé období): signál {LB.fmt(oth['sig'])} | převis {oth['diff']:+.3f}, t {oth['t']:+.2f}")
    full = ev66(Y)
    cnt = full["pick"].value_counts()
    say("popis – jak často byl trh vybrán (Yahoo celé): " + ", ".join(f"{k} {v}" for k, v in cnt.items()))
    share, g = years_share(full["ex"])
    say("po letech převis: " + "  ".join(f"{y}:{v:+.2f}" for y, v in g.items()))
    say(f"převis kladný v {int((g > 0).sum())} z {len(g)} let ({share:.0%})")
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    c = [ok("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ok("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ok("3) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
         ok("4) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}"),
         ok("5) jiné trhy převis > 0", oth["diff"] > 0, f"{oth['diff']:+.3f}")]
    say(f"   => {'VÝHODA (prošlo vše)' if all(c) else 'BEZ VÝHODY'}")


# ------------------------------------------------------------------ F67
def f67():
    say("\n" + "=" * 100)
    say("F67 RSI(2) NA 10 SVĚTOVÝCH INDEXECH – pravidlo F42 beze změny; srovnání = stejné vstupy/výstupy ve všech dnech nad SMA200")
    say("=" * 100)
    Ss, Bs, per = [], [], {}
    for tk in T65.TICK:
        d, _ = T65.load(tk)
        L.BROKER[tk] = {"spreadByHour": [2 * T65.SPR * float(d.close.iloc[-1])] * 24, "priceScale": 1.0, "swapLong": T65.SWAP}
        s, b = F.run(tk, d)
        Ss.append(s)
        Bs.append(b)
        sd, bd = F.by_day(s), F.by_day(b)
        dif, t = F.welch(sd, bd)
        per[tk] = dif
        say(f"   {tk:7s} {LB.fmt(LB.st(sd))} | převis {dif:+.3f}, t {t:+.2f}")
    S, B = F.by_day(pd.concat(Ss)), F.by_day(pd.concat(Bs))
    full = F.welch(S, B)
    Sc, Bc = S[S.index >= F.SPLIT], B[B.index >= F.SPLIT]
    ctl = F.welch(Sc, Bc)
    Sp, Bp = S[S.index < F.SPLIT], B[B.index < F.SPLIT]
    pre = F.welch(Sp, Bp)
    say(f"celé období     signál {LB.fmt(LB.st(S))} | převis {full[0]:+.3f}, t {full[1]:+.2f}")
    say(f"do 2018 (popis) signál {LB.fmt(LB.st(Sp))} | převis {pre[0]:+.3f}, t {pre[1]:+.2f}")
    say(f"2019–2026       signál {LB.fmt(LB.st(Sc))} | převis {ctl[0]:+.3f}, t {ctl[1]:+.2f}")
    ys = sorted(set(S.index.year))
    g = pd.Series({y: S[S.index.year == y].mean() - B[B.index.year == y].mean() for y in ys}).dropna()
    share = float((g > 0).mean())
    say("po letech převis: " + "  ".join(f"{y}:{v:+.2f}" for y, v in g.items()))
    say(f"převis kladný v {int((g > 0).sum())} z {len(g)} let ({share:.0%})")
    npos = sum(v > 0 for v in per.values())
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    c = [ok("1) celé období: signál > 0, převis > 0, t >= 2,0", S.mean() > 0 and full[0] > 0 and full[1] >= 2.0, f"{S.mean():+.3f}, převis {full[0]:+.3f}, t {full[1]:+.2f}"),
         ok("2) 2019–2026: signál > 0 a převis > 0", Sc.mean() > 0 and ctl[0] > 0, f"{Sc.mean():+.3f}, převis {ctl[0]:+.3f}"),
         ok("3) převis > 0 aspoň na 7 z 10 trhů", npos >= 7, f"{npos} z 10"),
         ok("4) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
    say(f"   => {'RSI(2) NEZÁVISLE POTVRZENO (prošlo vše)' if all(c) else 'NEPOTVRZENO'}")


# ------------------------------------------------------------------ F68
def night_yahoo(mk, d):
    rel, sw = costs(mk, d)
    A = atr20(d).to_numpy()
    O, C, idx = d.open.to_numpy(), d.close.to_numpy(), d.index
    rsi = F.rsi_wilder(d.close).to_numpy()
    s200 = d.close.rolling(200).mean().to_numpy()
    rows = []
    for i in range(21, len(d) - 1):
        if not A[i - 1] > 0 or (idx[i + 1] - idx[i]).days > 5:
            continue
        E, X = C[i], O[i + 1]
        R = ((X - E) - rel * (E + X) / 2 + sw * E * F.nights(idx[i], idx[i + 1])) / A[i - 1]
        down = (C[i] - C[i - 1]) <= -A[i - 1]
        rows.append((idx[i], R, down, bool(C[i] > s200[i] and rsi[i] < 10)))
    return pd.DataFrame(rows, columns=["day", "R", "sig", "rsi2"])


def night_broker(mk):
    h = T58.br_h1(mk)
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(h.close.iloc[-1])
    ny = h.index.tz_convert(NY)
    loc = pd.DatetimeIndex(ny.tz_localize(None))
    cl = pd.Series(h.close.to_numpy(), index=loc)
    op = pd.Series(h.open.to_numpy(), index=loc)
    cl, op = cl[~cl.index.duplicated()], op[~op.index.duplicated()]
    c16 = cl[cl.index.hour == 15]
    c16.index = c16.index.normalize()
    o09 = op[op.index.hour == 9]
    o09.index = o09.index.normalize()
    g = h.groupby(ny.date)
    D = pd.DataFrame({"H": g.high.max(), "L": g.low.min(), "C": g.close.last()})
    D.index = pd.to_datetime(D.index)
    pc = D.C.shift(1)
    atr = np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs())).rolling(20).mean().shift(1)
    days = c16.index[c16.index.day_of_week < 5]
    rows = []
    for j in range(1, len(days)):
        d0 = days[j]
        nxt = o09.index[o09.index > d0]
        if not len(nxt) or (nxt[0] - d0).days > 5:
            continue
        a = atr.get(d0, np.nan)
        if not a > 0:
            continue
        E, X = c16[d0], o09[nxt[0]]
        R = ((X - E) - rel * (E + X) / 2 + b["swapLong"] * E * F.nights(d0, nxt[0])) / a
        rows.append((d0, R, (c16[d0] - c16[days[j - 1]]) <= -a, False))
    return pd.DataFrame(rows, columns=["day", "R", "sig", "rsi2"])


def ev68(T, a=None, b=None):
    T = pd.concat(T)
    if a is not None:
        T = T[T.day >= a]
    if b is not None:
        T = T[T.day < b]
    s = T[T.sig].groupby("day").R.mean()
    bb = T[~T.sig].groupby("day").R.mean()
    diff, t = F.welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb, T=T)


def f68():
    say("\n" + "=" * 100)
    say("F68 NOC PO VÝRAZNÉM POKLESU – den s poklesem >= 1 ATR → long zavření → otevření dalšího dne; srovnání = ostatní noci")
    say("=" * 100)
    Y = [night_yahoo(mk, clean(F.yahoo(mk), need_open=True)) for mk in US]
    Br = [night_broker(mk) for mk in US]
    R = {"vyvoj": ev68(Y, D0, F.SPLIT), "kontrola": ev68(Y, F.SPLIT, None), "broker": ev68(Br, F.SPLIT, None)}
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    oth = ev68([night_yahoo(mk, clean(F.yahoo(mk), need_open=True)) for mk in ("GER_30mini", "GBR_100mini", "FRA_40mini")])
    say(f"jiné trhy DAX, FTSE, CAC: signál {LB.fmt(oth['sig'])} | převis {oth['diff']:+.3f}, t {oth['t']:+.2f}")
    for mk, T in zip(US, Y):
        v = ev68([T])
        say(f"   {mk:12s} {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f} | data od {T.day.iloc[0].date()}")
    full = ev68(Y)
    TT = full["T"]
    say(f"popis – signálů {int(TT.sig.sum())}, z toho {int((TT.sig & TT.rsi2).sum())} ({(TT.sig & TT.rsi2).sum() / max(TT.sig.sum(), 1):.0%}) "
        "ve stejný den jako signál RSI(2)")
    ys = sorted(set(full["s"].index.year))
    g = pd.Series({y: full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean() for y in ys}).dropna()
    share = float((g > 0).mean())
    say("po letech převis: " + "  ".join(f"{y}:{v:+.2f}" for y, v in g.items()))
    say(f"převis kladný v {int((g > 0).sum())} z {len(g)} let ({share:.0%})")
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    c = [ok("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ok("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ok("3) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
         ok("4) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}"),
         ok("5) jiné trhy převis > 0", oth["diff"] > 0, f"{oth['diff']:+.3f}")]
    say(f"   => {'VÝHODA (prošlo vše)' if all(c) else 'BEZ VÝHODY'}")


if __name__ == "__main__":
    f66()
    f67()
    f68()
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
