"""
F36 tyden expirace opci (OPEX) a F37 den pred svatkem - long indexu, hodnoceno jako previs nad driftem.
Plan predem ve vaultu: Vyzkum/Fronta napadu F35-F39.md (2026-11-19).
Spusteni: python -I f36_f37.py -> D:\\Trading bot\\research_data\\f36_f37\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f36_f37")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
DEV0, SPLIT = pd.Timestamp("1990-01-01"), pd.Timestamp("2019-01-01")
LINES = []
UNPLANNED = pd.to_datetime(["2001-09-11", "2001-09-12", "2001-09-13", "2001-09-14", "2004-06-11", "2007-01-02",
                            "2012-10-29", "2012-10-30", "2018-12-05", "2025-01-09"])


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def yahoo(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))[["open", "high", "low", "close"]].astype(float)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    ok = (d.high >= d.low) & (d.low <= d.close) & (d.close <= d.high) & (d.close > 0)
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


# ---------------------------------------------------------------- kalendar NYSE podle S&P 500 (Yahoo)
SPX = yahoo("SPX500mini")
cal = SPX.index[SPX.index >= "1985-01-01"]
wd = pd.bdate_range(cal[0], cal[-1])
closed = wd.difference(cal).difference(UNPLANNED)
# F37: posledni obchodni den pred kazdym (planovanym) zavrenim
PRE = sorted({cal[cal < h][-1] for h in closed if (cal < h).any()})
# F36: patek expirace = 3. patek v mesici (pri svatku posledni obchodni den pred nim)
OPEX = []
for y in range(cal[0].year, cal[-1].year + 1):
    for m in range(1, 13):
        f3 = pd.date_range(f"{y}-{m:02d}-01", periods=21, freq="D")
        f3 = f3[f3.dayofweek == 4][2]
        if f3 > cal[-1] or f3 < cal[0]:
            continue
        ex = cal[cal <= f3][-1]
        mon = f3 - pd.Timedelta(days=4)
        if not (cal < mon).any():
            continue
        OPEX.append((cal[cal < mon][-1], ex))
WEEKEND = cal[np.r_[cal.dayofweek[1:] <= cal.dayofweek[:-1], True]]  # posledni obchodni den kazdeho tydne
WEEKS = list(zip(WEEKEND[:-1], WEEKEND[1:]))


def windows_trades(mk, d, wins):
    """Long od zavreni d0 do zavreni d1 pro kazde okno (d0, d1); R = cisty vysledek / ATR20."""
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    pc = d.close.shift(1)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    atr = tr.rolling(20).mean()
    idx = d.index
    rows = []
    for d0, d1 in wins:
        if d0 not in idx or d1 not in idx or d1 <= d0:
            continue
        a = atr.get(d0, np.nan)
        if not a > 0:
            continue
        E, X = d.close[d0], d.close[d1]
        net = (X - E) - rel * (E + X) / 2 + b["swapLong"] * E * nights(d0, d1)
        rows.append(dict(mk=mk, d0=d0, d1=d1, R=net / a))
    return pd.DataFrame(rows)


def daily_wins(d):
    i = d.index
    return list(zip(i[:-1], i[1:]))


def per_event(T):
    return T.groupby("d1").R.mean()


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or len(b) < 3:
        return np.nan, np.nan
    diff = a.mean() - b.mean()
    return diff, diff / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def evaluate(name, ev_wins, base_wins_fn, key_fn):
    say("\n" + "=" * 100)
    say(name)
    say("=" * 100)
    S = {}
    srcs = {"yahoo": {m: yahoo(m) for m in ("SPX500mini", "NAS100mini")},
            "broker": {m: broker_daily(m) for m in ("SPX500mini", "NAS100mini")}}

    def both(src, wins_fn):
        return pd.concat([windows_trades(m, d, wins_fn(d)) for m, d in srcs[src].items()], ignore_index=True)

    EV = {s: both(s, lambda d: ev_wins) for s in srcs}
    BA = {s: both(s, base_wins_fn) for s in srcs}
    evset = set(key_fn(ev_wins))
    for s in BA:
        BA[s] = BA[s][~BA[s].d1.isin(evset)]
    parts = (("vyvoj", "yahoo", DEV0, SPLIT), ("kontrola", "yahoo", SPLIT, None), ("zdroj2", "broker", SPLIT, None))
    for p, s, a, b in parts:
        e, o = per_event(EV[s]), per_event(BA[s])
        sel = lambda x: x[(x.index >= a) & ((x.index < b) if b is not None else True)]  # noqa: E731
        e, o = sel(e), sel(o)
        diff, t = welch(e, o)
        S[p] = dict(ev=LB.st(e), base=LB.st(o), diff=diff, t=t)
        say(f"{p:9s} událost: {LB.fmt(S[p]['ev'])}")
        say(f"{'':9s} ostatní: {LB.fmt(S[p]['base'])}")
        say(f"{'':9s} převis nad driftem {diff:+.3f} R, t {t:+.2f}")
    for m in ("US30mini", "GER_30mini"):
        d = yahoo(m)
        e = windows_trades(m, d, ev_wins).set_index("d1").R
        o = windows_trades(m, d, base_wins_fn(d))
        o = o[~o.d1.isin(evset)].set_index("d1").R
        diff, t = welch(e, o)
        S[m] = dict(diff=diff, t=t)
        say(f"{m:11s} (celé období): událost {LB.fmt(LB.st(e))} | převis {diff:+.3f} R, t {t:+.2f}")
    e, o = per_event(EV["yahoo"]), per_event(BA["yahoo"])
    e, o = e[e.index >= DEV0], o[o.index >= DEV0]
    yrs = sorted(set(e.index.year))
    pos = []
    say("Po letech (Yahoo SPX+NAS): převis")
    line = []
    for y in yrs:
        dy = e[e.index.year == y].mean() - o[o.index.year == y].mean()
        pos.append(dy > 0)
        line.append(f"{y}:{dy:+.2f}")
    for i in range(0, len(line), 10):
        say("   " + "  ".join(line[i:i + 10]))
    share = float(np.mean(pos))
    say(f"   kladný převis v {sum(pos)} z {len(pos)} let ({share:.0%})")
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    v, k = S["vyvoj"], S["kontrola"]
    c = [("1) vývoj: událost > 0, převis > 0, t >= 2,0", v["ev"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0,
          f"{v['ev']['m']:+.3f} R, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ("2) kontrola: událost > 0, převis > 0, t >= 1,5", k["ev"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5,
          f"{k['ev']['m']:+.3f} R, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ("3) US30 i DAX převis > 0", S["US30mini"]["diff"] > 0 and S["GER_30mini"]["diff"] > 0,
          f"US30 {S['US30mini']['diff']:+.3f}, DAX {S['GER_30mini']['diff']:+.3f}"),
         ("4) druhý zdroj převis > 0", S["zdroj2"]["diff"] > 0, f"{S['zdroj2']['diff']:+.3f}"),
         ("5) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
    return S


say("F36 OPEX a F37 den před svátkem – long indexů, převis nad driftem; R = výsledek / ATR20, náklady brokera")
say(f"kalendář NYSE z Yahoo S&P 500: {len(closed)} zavřených pracovních dní, dnů před svátkem {len(PRE)}, týdnů OPEX {len(OPEX)}")
pre_wins = [(cal[cal < t][-1], t) for t in PRE if (cal < t).any()]
evaluate("F37 DEN PŘED SVÁTKEM (zavření T−1 → zavření T)", pre_wins, daily_wins, lambda w: [x[1] for x in w])
evaluate("F36 TÝDEN EXPIRACE OPCÍ (zavření před pondělím → zavření pátku expirace)", OPEX,
         lambda d: WEEKS, lambda w: [x[1] for x in w])
open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
