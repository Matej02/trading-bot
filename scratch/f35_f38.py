"""
F35 mesicni fixing v FX a F38 drift pred ECB. Plan predem ve vaultu: Vyzkum/Fronta napadu F35-F39.md (2026-11-19).
Spusteni: python -I f35_f38.py -> D:\\Trading bot\\research_data\\f38\\souhrn.txt
Bota ani vyzkumny kod nemeni.
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
ZIP = os.path.join(RD, "histdata", "zip_fx")
OUT = os.path.join(RD, "f38")
CACHE = os.path.join(RD, "histdata", "m1_fx")
os.makedirs(CACHE, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
SPLIT = pd.Timestamp("2019-01-01", tz="UTC")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


# ------------------------------------------------------------------ data
def histdata(sym):
    """HistData M1 -> DataFrame s indexem UTC (cas HistData = New York vcetne letniho casu)."""
    p = os.path.join(CACHE, f"{sym}.pkl")
    if os.path.exists(p):
        return pd.read_pickle(p)
    fr = []
    for f in sorted(os.listdir(ZIP)):
        if f"_{sym}_M1" not in f:
            continue
        z = zipfile.ZipFile(os.path.join(ZIP, f))
        csv = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        with z.open(csv) as fh:
            fr.append(pd.read_csv(fh, sep=";", header=None, names=["ts", "open", "high", "low", "close", "v"], dtype={"ts": str}))
    d = pd.concat(fr, ignore_index=True)
    loc = pd.DatetimeIndex(pd.to_datetime(d.ts, format="%Y%m%d %H%M%S"))
    # cas HistData FX/indexu = New York vcetne letniho casu (overeno: posledni paterni svicka 16:59 NY v zime i v lete)
    idx = loc.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC")
    d = d[["open", "high", "low", "close"]].astype(float)
    d.index = idx
    d = d[d.index.notna()]
    d = d[~d.index.duplicated()].sort_index()
    d.to_pickle(p)
    return d


def broker_h1(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))[["open", "high", "low", "close"]].astype(float)
    u = pd.DatetimeIndex(h.index).tz_localize("UTC")
    # cas serveru = UTC, data ctena jako Londyn -> v britskem letnim case +1 h (stejne jako f2x_lib.load_m1)
    dst = np.array([x.dst().seconds > 0 for x in (u + pd.Timedelta(hours=1)).tz_convert("Europe/London")])
    h.index = u + pd.to_timedelta(dst.astype(np.int64) * 3600, unit="s")
    return h


def yahoo_close(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))["close"].astype(float)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return d[d > 0].dropna()


def atr_daily(d, tz):
    loc = d.index.tz_convert(tz)
    g = d.groupby(loc.date)
    D = pd.DataFrame({"H": g.high.max(), "L": g.low.min(), "C": g.close.last()})
    pc = D.C.shift(1)
    tr = np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs()))
    a = tr.rolling(20).mean().shift(1)
    a.index = pd.to_datetime(a.index)
    return a


def price_at(d, t, side):
    """side 'in' = open prvni svicky v case >= t; 'out' = close posledni svicky pred t."""
    if side == "in":
        i = d.index.searchsorted(t, "left")
        if i >= len(d) or d.index[i] - t > pd.Timedelta(minutes=90):
            return np.nan, None
        return d.open.iloc[i], d.index[i]
    i = d.index.searchsorted(t, "left") - 1
    if i < 0 or t - d.index[i] > pd.Timedelta(minutes=90):
        return np.nan, None
    return d.close.iloc[i], d.index[i]


def spread_rel(mk, d):
    b = L.BROKER[mk]
    s = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0)
    return s / float(d.close.iloc[-1])


def nights(d0, d1):
    days = pd.date_range(d0.normalize() + pd.Timedelta(days=1), d1.normalize(), freq="D")
    w = days.day_of_week
    return int(((w < 5) & (w != 3)).sum() + 3 * (w == 3).sum())


def trade(mk, d, t0, t1, direction, atr, tz_atr="Europe/London"):
    E, ti = price_at(d, t0, "in")
    X, to = price_at(d, t1, "out")
    if not (E > 0 and X > 0) or ti is None or to is None or to <= ti:
        return None
    a = atr.get(pd.Timestamp(t0.tz_convert(tz_atr).date()), np.nan)
    if not a > 0:
        return None
    rel = spread_rel(mk, d)
    hi = t0.tz_convert("Europe/London").hour
    ho = t1.tz_convert("Europe/London").hour % 24
    cost = rel[hi] * E / 2 + rel[ho] * X / 2
    b = L.BROKER[mk]
    sw = (b["swapLong"] if direction == 1 else b["swapShort"]) * E * nights(t0, t1)
    return (direction * (X - E) - cost + sw) / a


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or len(b) < 3:
        return np.nan, np.nan
    diff = a.mean() - b.mean()
    return diff, diff / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


# ------------------------------------------------------------------ kontrola casu HistData
say("Kontrola času HistData (New York s letním časem): poslední páteční svíčka EURUSD v UTC má být v zimě 21:59 a v létě 20:59")
eu = histdata("EURUSD")
fri = eu[eu.index.day_of_week == 4]
last = fri.groupby(fri.index.date).apply(lambda x: x.index[-1].strftime("%H:%M"))
for dt_ in ("2015-01-16", "2015-07-17", "2018-01-12", "2018-07-13"):
    k = pd.Timestamp(dt_).date()
    say(f"   {dt_}: {last.get(k, '-')}")

# ================================================================== F35
say("\n" + "=" * 100)
say("F35 MĚSÍČNÍ FIXING V FX – poslední pracovní den, 10:00 → 16:00 Londýn, signál S&P 500 − EuroStoxx 50 (|rozdíl| >= 1 p. b.)")
say("=" * 100)
SPXc, EUc = yahoo_close("SPX500mini"), yahoo_close("EUR_50mini")
days = pd.bdate_range("2010-01-01", "2026-10-31")
SIG = []
for (y, m), g in pd.Series(days, index=days).groupby([days.year, days.month]):
    T = g.iloc[-1]
    prev_end = pd.Timestamp(y, m, 1) - pd.Timedelta(days=1)
    tm1 = g.iloc[-2] if len(g) > 1 else None
    if tm1 is None:
        continue
    try:
        rs = SPXc[:tm1].iloc[-1] / SPXc[:prev_end].iloc[-1] - 1
        re = EUc[:tm1].iloc[-1] / EUc[:prev_end].iloc[-1] - 1
    except IndexError:
        continue
    diff = rs - re
    if abs(diff) >= 0.01:
        SIG.append((T, 1 if diff > 0 else -1, diff))
say(f"signálních měsíců: {len(SIG)} (US vedly {sum(1 for s in SIG if s[1] == 1)}, Evropa vedla {sum(1 for s in SIG if s[1] == -1)})")
USD_SIDE = {"EURUSD": 1, "GBPUSD": 1, "USDJPY": -1}   # US vedly -> slabsi USD -> long EURUSD, GBPUSD, short USDJPY


def f35_rows(mk, d):
    atr = atr_daily(d, "Europe/London")
    rows = []
    for T, sgn, diff in SIG:
        t0 = pd.Timestamp(f"{T.date()} 10:00", tz="Europe/London").tz_convert("UTC")
        t1 = pd.Timestamp(f"{T.date()} 16:00", tz="Europe/London").tz_convert("UTC")
        dd = sgn * USD_SIDE[mk]
        r = trade(mk, d, t0, t1, dd, atr)
        rl = trade(mk, d, t0, t1, 1, atr)
        if r is not None:
            rows.append(dict(mk=mk, t=t0, R=r, R_long=rl))
    return pd.DataFrame(rows)


S = {}
HD = {mk: f35_rows(mk, histdata(mk)) for mk in USD_SIDE}
BR = {mk: f35_rows(mk, broker_h1(mk)) for mk in USD_SIDE}
for name, T in (("vyvoj", HD["EURUSD"][HD["EURUSD"].t < SPLIT]), ("kontrola", BR["EURUSD"][BR["EURUSD"].t >= SPLIT]),
                ("zdroj2", HD["EURUSD"][HD["EURUSD"].t >= SPLIT])):
    S[name] = LB.st(T.R)
    S[name + "_long"] = LB.st(T.R_long)
    say(f"{name:9s} EURUSD: {LB.fmt(S[name])} | stále long: {LB.fmt(S[name + '_long'])}")
for mk in ("GBPUSD", "USDJPY"):
    T = pd.concat([HD[mk][HD[mk].t < SPLIT], BR[mk][BR[mk].t >= SPLIT]])
    S[mk] = LB.st(T.R)
    say(f"{mk} (HistData do 2018 + broker 2019+): {LB.fmt(S[mk])}")
allE = pd.concat([HD["EURUSD"][HD["EURUSD"].t < SPLIT], BR["EURUSD"][BR["EURUSD"].t >= SPLIT]])
say("Po letech EURUSD: " + "  ".join(f"{y}:{g.R.mean():+.2f}" for y, g in allE.groupby(allE.t.dt.year)))
say("ROZHODNUTÍ podle pravidel zapsaných předem")
c = [("1) vývoj EURUSD > 0 a t >= 2,0", S["vyvoj"]["m"] > 0 and S["vyvoj"]["t"] >= 2.0, f"{S['vyvoj']['m']:+.3f} R, t {S['vyvoj']['t']:+.2f}"),
     ("2) kontrola EURUSD > 0 a t >= 1,5", S["kontrola"]["m"] > 0 and S["kontrola"]["t"] >= 1.5, f"{S['kontrola']['m']:+.3f} R, t {S['kontrola']['t']:+.2f}"),
     ("3) GBPUSD i USDJPY > 0", S["GBPUSD"]["m"] > 0 and S["USDJPY"]["m"] > 0, f"GBPUSD {S['GBPUSD']['m']:+.3f}, USDJPY {S['USDJPY']['m']:+.3f}"),
     ("4) druhý zdroj > 0", S["zdroj2"]["m"] > 0, f"{S['zdroj2']['m']:+.3f}"),
     ("5) lepší než stále long (vývoj i kontrola)", S["vyvoj"]["m"] > S["vyvoj_long"]["m"] and S["kontrola"]["m"] > S["kontrola_long"]["m"],
      f"{S['vyvoj']['m']:+.3f} vs {S['vyvoj_long']['m']:+.3f}; {S['kontrola']['m']:+.3f} vs {S['kontrola_long']['m']:+.3f}")]
for nm, ok, val in c:
    say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")

# ================================================================== F38
say("\n" + "=" * 100)
say("F38 DRIFT PŘED ECB – long 24 h před rozhodnutím (HistData 13:30 → 13:30 Praha, broker H1 13:00 → 13:00), převis nad ostatními dny")
say("=" * 100)
ECB = pd.to_datetime(open(os.path.join(OUT, "ecb_terminy.txt")).read().split())
ECB = ECB[~ECB.isin(pd.to_datetime(["2014-10-26", "2021-07-08"])) & (ECB.day_of_week < 5)]
ecb_set = set(ECB.date)


def f38_rows(mk, d, hhmm):
    atr = atr_daily(d, "Europe/Prague")
    have = set(pd.DatetimeIndex(d.index.tz_convert("Europe/Prague").date).unique().date)
    alld = sorted(x for x in have if pd.Timestamp(x).day_of_week < 5)
    rows = []
    for i in range(1, len(alld)):
        T, P = alld[i], alld[i - 1]
        if (pd.Timestamp(T) - pd.Timestamp(P)).days > 4:
            continue
        t0 = pd.Timestamp(f"{P} {hhmm}", tz="Europe/Prague").tz_convert("UTC")
        t1 = pd.Timestamp(f"{T} {hhmm}", tz="Europe/Prague").tz_convert("UTC")
        r = trade(mk, d, t0, t1, 1, atr, "Europe/Prague")
        if r is not None:
            rows.append(dict(day=pd.Timestamp(T), ev=T in ecb_set, R=r))
    return pd.DataFrame(rows)


def ex(T):
    e, o = T[T.ev].R, T[~T.ev].R
    diff, t = welch(e, o)
    return dict(ev=LB.st(e), base=LB.st(o), diff=diff, t=t)


hdD, brD = f38_rows("GER_30mini", histdata("GRXEUR"), "13:30"), f38_rows("GER_30mini", broker_h1("GER_30mini"), "13:00")
cut = pd.Timestamp("2019-01-01")
R38 = {"vyvoj": ex(hdD[hdD.day < cut]), "kontrola": ex(brD[brD.day >= cut]), "zdroj2": ex(hdD[hdD.day >= cut])}
for k, v in R38.items():
    say(f"{k:9s} DAX událost: {LB.fmt(v['ev'])}")
    say(f"{'':9s} ostatní:     {LB.fmt(v['base'])}")
    say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
es = f38_rows("EUR_50mini", histdata("ETXEUR"), "13:30")
cac = f38_rows("FRA_40mini", broker_h1("FRA_40mini"), "13:00")
R38["ES"] = ex(es[es.day < cut])
R38["CAC"] = ex(cac[cac.day >= cut])
say(f"EuroStoxx (HistData do 2018): událost {LB.fmt(R38['ES']['ev'])} | převis {R38['ES']['diff']:+.3f}, t {R38['ES']['t']:+.2f}")
say(f"CAC (broker 2019+):           událost {LB.fmt(R38['CAC']['ev'])} | převis {R38['CAC']['diff']:+.3f}, t {R38['CAC']['t']:+.2f}")
allD = pd.concat([hdD[hdD.day < cut], brD[brD.day >= cut]])
pos, line = [], []
for y, g in allD.groupby(allD.day.dt.year):
    if g.ev.sum() == 0:
        continue
    dy = g[g.ev].R.mean() - g[~g.ev].R.mean()
    pos.append(dy > 0)
    line.append(f"{y}:{dy:+.2f}")
share = float(np.mean(pos))
say("Po letech DAX převis: " + "  ".join(line) + f"  → kladný v {sum(pos)} z {len(pos)} ({share:.0%})")
say("ROZHODNUTÍ podle pravidel zapsaných předem")
v, k = R38["vyvoj"], R38["kontrola"]
c = [("1) vývoj: událost > 0, převis > 0, t >= 2,0", v["ev"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['ev']['m']:+.3f} R, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
     ("2) kontrola: událost > 0, převis > 0, t >= 1,5", k["ev"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['ev']['m']:+.3f} R, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
     ("3) EuroStoxx i CAC převis > 0", R38["ES"]["diff"] > 0 and R38["CAC"]["diff"] > 0, f"ES {R38['ES']['diff']:+.3f}, CAC {R38['CAC']['diff']:+.3f}"),
     ("4) druhý zdroj převis > 0", R38["zdroj2"]["diff"] > 0, f"{R38['zdroj2']['diff']:+.3f}"),
     ("5) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
for nm, ok, val in c:
    say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
