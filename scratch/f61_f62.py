"""
F61 prelom mesice v Evrope (overeni kandidata z F55) a F62 druhy zdroj pro F46 zlato v Asii (Yahoo GLD/IAU/SLV, GC=F 1h).
Plan predem ve vaultu: Vyzkum/F61 a F62 Overeni kandidatu (prelom mesice v Evrope, zlato v Asii).md (2026-11-20).
Spusteni: python -I f61_f62.py -> D:\\Trading bot\\research_data\\f61\\souhrn.txt
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import f55_f57 as T55  # noqa: E402

LB, L = F.LB, F.L
RD = F.RD
OUT = os.path.join(RD, "f61")
os.makedirs(OUT, exist_ok=True)
YD = os.path.join(RD, "f62")
LON = "Europe/London"
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def ok(nm, c, val):
    say(f"   {nm}: {'ANO' if c else 'NE'} ({val})")
    return c


# ------------------------------------------------------------------ F61
def f61():
    say("=" * 100)
    say("F61 PŘELOM MĚSÍCE V EVROPĚ – pravidlo F55; nové trhy EuroStoxx + IBEX, broker 2019+")
    say("=" * 100)
    NEW = ["EUR_50mini", "ESP_35mini"]
    BRK = ["GER_30mini", "GBR_100mini", "FRA_40mini", "EUR_50mini", "ESP_35mini"]
    D0 = pd.Timestamp("1990-01-01")
    new_all = T55.evaluate(T55.f55, NEW, "yahoo", D0, None)
    new_ctl = T55.evaluate(T55.f55, NEW, "yahoo", F.SPLIT, None)
    brk = T55.evaluate(T55.f55, BRK, "broker", F.SPLIT, None)
    for nm, v in (("EuroStoxx+IBEX celé", new_all), ("EuroStoxx+IBEX 2019+", new_ctl), ("broker 2019+ (5 trhů)", brk)):
        say(f"{nm:22s} signál {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    for mk in NEW:
        v = T55.evaluate(T55.f55, [mk], "yahoo", D0, None)
        say(f"   {mk:12s} {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    for mk in BRK:
        v = T55.evaluate(T55.f55, [mk], "broker", F.SPLIT, None)
        say(f"   broker {mk:12s} {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}")
    for nm, a, b in (("do 2018", D0, F.SPLIT), ("od 2019", F.SPLIT, None)):
        v = T55.evaluate(T55.f55, ["GER_30mini", "GBR_100mini"], "yahoo", a, b)
        say(f"popis DAX+FTSE {nm}: signál {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    full = T55.evaluate(T55.f55, ["GER_30mini", "GBR_100mini"] + NEW, "yahoo", D0, None)
    ys = sorted(set(full["s"].index.year))
    dif = {y: full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean() for y in ys}
    pos = [v > 0 for v in dif.values()]
    share = float(np.mean(pos))
    say("po letech převis: " + "  ".join(f"{y}:{v:+.2f}" for y, v in dif.items()))
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    c = [ok("1) EuroStoxx+IBEX celé: signál > 0, převis > 0, t >= 2,0", new_all["sig"]["m"] > 0 and new_all["diff"] > 0 and new_all["t"] >= 2.0,
            f"{new_all['sig']['m']:+.3f}, převis {new_all['diff']:+.3f}, t {new_all['t']:+.2f}"),
         ok("2) EuroStoxx+IBEX 2019+: signál > 0 a převis > 0", new_ctl["sig"]["m"] > 0 and new_ctl["diff"] > 0, f"{new_ctl['sig']['m']:+.3f}, převis {new_ctl['diff']:+.3f}"),
         ok("3) broker 2019+: signál > 0 a převis > 0", brk["sig"]["m"] > 0 and brk["diff"] > 0, f"{brk['sig']['m']:+.3f}, převis {brk['diff']:+.3f}"),
         ok("4) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
    say(f"   => {'KANDIDÁT NA SLEDOVÁNÍ (prošlo vše)' if all(c) else 'NEPROŠLO'}")


# ------------------------------------------------------------------ F62
def yjson(name):
    j = json.load(open(os.path.join(YD, f"{name}.json")))["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=pd.to_datetime(j["timestamp"], unit="s", utc=True)).astype(float)
    return d.dropna()


def night_day(name):
    d = yjson(name)
    d.index = d.index.tz_convert("America/New_York").tz_localize(None).normalize()
    d = d[~d.index.duplicated()]
    pc = d.close.shift(1)
    A = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean().shift(1)
    T = pd.DataFrame({"night": (d.open - pc) / A, "day": (d.close - d.open) / A}).dropna()
    return T


def nd_eval(T, a=None, b=None):
    if a is not None:
        T = T[T.index >= a]
    if b is not None:
        T = T[T.index < b]
    diff, t = F.welch(T.night, T.day)
    return dict(n=len(T), night=T.night.mean(), day=T.day.mean(), diff=diff, t=t, T=T)


def h1_windows(h, spr, start=23, ln=8):
    """Kazde 8h okno long (zacatek v cele hodine Londyn): (signal, srovnani) po dnech."""
    loc = h.index.tz_convert(LON).tz_localize(None)
    op = pd.Series(h.open.to_numpy(), index=loc)
    cl = pd.Series(h.close.to_numpy(), index=loc)
    op, cl = op[~op.index.duplicated()], cl[~cl.index.duplicated()]
    g = h.groupby(loc.date)
    D = pd.DataFrame({"H": g.high.max(), "L": g.low.min(), "C": g.close.last()})
    pc = D.C.shift(1)
    atr = np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs())).rolling(20).mean().shift(1)
    atr.index = pd.to_datetime(atr.index)
    days = pd.DatetimeIndex(atr.index)
    S, B = [], []
    for hr in range(23 + 1):
        t0 = days + pd.Timedelta(hours=hr)
        E = op.reindex(t0).to_numpy()
        X = cl.reindex(t0 + pd.Timedelta(hours=ln - 1)).to_numpy()
        A = atr.reindex(days).to_numpy()
        R = (X - E - spr[hr] / 2 * E - spr[(hr + ln) % 24] / 2 * X) / A
        m = np.isfinite(R)
        s = pd.Series(R[m], index=days[m])
        (S if hr == start else B).append(s)
    s = pd.concat(S)
    b = pd.concat(B).groupby(level=0).mean()
    return s, b


def f62():
    say("\n" + "=" * 100)
    say("F62 DRUHÝ ZDROJ PRO F46 ZLATO V ASII – B1 GLD noc vs. den (Yahoo), B2 GC=F 1h přesně pravidlo F46")
    say("=" * 100)
    G, I, Sv = night_day("GLD_1d"), night_day("IAU_1d"), night_day("SLV_1d")
    SP = pd.Timestamp("2019-01-01")
    dv, ct, ia, sl = nd_eval(G, None, SP), nd_eval(G, SP, None), nd_eval(I), nd_eval(Sv)
    for nm, v in (("GLD 2004–2018", dv), ("GLD 2019–2026", ct), ("IAU celé", ia), ("SLV celé (popis)", sl)):
        say(f"{nm:18s} n {v['n']:5d} | noc {v['night']:+.4f} | den {v['day']:+.4f} | převis noc−den {v['diff']:+.4f}, t {v['t']:+.2f}")
    full = nd_eval(G)
    ys = sorted(set(full["T"].index.year))
    dif = {y: full["T"][full["T"].index.year == y].night.mean() - full["T"][full["T"].index.year == y].day.mean() for y in ys}
    pos = [v > 0 for v in dif.values()]
    share = float(np.mean(pos))
    say("po letech převis GLD: " + "  ".join(f"{y}:{v:+.3f}" for y, v in dif.items()))
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")

    b = L.BROKER["XAUUSD"]
    gc = yjson("GC_F_1h")
    spr = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0) / float(gc.close.iloc[-1])
    s_gc, b_gc = h1_windows(gc, spr)
    import f58_f59 as T58  # noqa: E402
    br = T58.br_h1("XAUUSD")
    br = br[br.index >= gc.index[0] - pd.Timedelta(days=40)]
    spr_b = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0) / float(br.close.iloc[-1])
    s_br, b_br = h1_windows(br, spr_b)
    a0 = max(s_gc.index[0], s_br.index[0]) + pd.Timedelta(days=30)
    s_gc, b_gc, s_br, b_br = (x[x.index >= a0] for x in (s_gc, b_gc, s_br, b_br))
    d_gc, t_gc = F.welch(s_gc, b_gc)
    d_br, t_br = F.welch(s_br, b_br)
    say(f"B2 GC=F 1h {a0.date()}–: signál {LB.fmt(LB.st(s_gc))} | převis {d_gc:+.3f}, t {t_gc:+.2f}")
    say(f"   broker XAU stejné období: signál {LB.fmt(LB.st(s_br))} | převis {d_br:+.3f}, t {t_br:+.2f}")
    j = pd.concat([s_gc.rename("gc"), s_br.rename("br")], axis=1).dropna()
    say(f"   shoda denních R GC=F vs broker: korelace {j.gc.corr(j.br):+.2f} (n {len(j)})")
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    c = [ok("1) GLD 2004–2018: noc > 0, převis > 0, t >= 2,0", dv["night"] > 0 and dv["diff"] > 0 and dv["t"] >= 2.0, f"noc {dv['night']:+.4f}, převis {dv['diff']:+.4f}, t {dv['t']:+.2f}"),
         ok("2) GLD 2019–2026: noc > 0, převis > 0, t >= 1,5", ct["night"] > 0 and ct["diff"] > 0 and ct["t"] >= 1.5, f"noc {ct['night']:+.4f}, převis {ct['diff']:+.4f}, t {ct['t']:+.2f}"),
         ok("3) IAU převis > 0", ia["diff"] > 0, f"{ia['diff']:+.4f}"),
         ok("4) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}"),
         ok("5) GC=F 1h pravidlo F46: signál > 0 a převis > 0", LB.st(s_gc)["m"] > 0 and d_gc > 0, f"{LB.st(s_gc)['m']:+.3f}, převis {d_gc:+.3f}")]
    say(f"   => {'DRUHÝ ZDROJ POTVRZUJE F46 (prošlo vše)' if all(c) else 'DRUHÝ ZDROJ F46 NEPOTVRDIL'}")


if __name__ == "__main__":
    f61()
    f62()
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
