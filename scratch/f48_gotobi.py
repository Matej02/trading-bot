"""
F48 gotobi efekt - long USDJPY 08:00 -> 09:55 JST (23:00 -> 00:55 UTC) v gotobi dny, proti stejnemu oknu v jine dny.
Plan predem ve vaultu: Vyzkum/F48 Gotobi efekt USDJPY.md (2026-11-19).
Spusteni: python -I f48_gotobi.py -> D:\\Trading bot\\research_data\\f48\\souhrn.txt
"""
import calendar
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f48")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    diff = a.mean() - b.mean()
    return diff, diff / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def gotobi_days(y0, y1):
    out = set()
    for y in range(y0, y1 + 1):
        for m in range(1, 13):
            last = calendar.monthrange(y, m)[1]
            cands = [d for d in (5, 10, 15, 20, 25, 30) if d <= last]
            for d in cands:
                x = date(y, m, d)
                while x.weekday() >= 5:
                    x -= timedelta(days=1)
                out.add(x)
            x = date(y, m, last)
            while x.weekday() >= 5:
                x -= timedelta(days=1)
            out.add(x)
    return out


GOTOBI = gotobi_days(2009, 2026)


def broker_h1_utc(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))[["open", "high", "low", "close"]].astype(float)
    u = pd.DatetimeIndex(h.index).tz_localize("UTC")
    # oprava 2026-11-21: surova H1 brokera = UTC cely rok (overeno proti GC=F), drivejsi posun +1 h v letnim case byl chybny
    dst = np.zeros(len(u), bool)
    h.index = u + pd.to_timedelta(dst.astype(np.int64) * 3600, unit="s")
    return h


def hd(sym):
    d = pd.read_pickle(os.path.join(RD, "histdata", "m1_fx", f"{sym}.pkl"))
    jump = np.log(d.close).diff().abs()
    bad = (jump > np.log(1.2))
    return d[~(bad | bad.shift(-1, fill_value=False))]


def atr_utc(d):
    g = d.groupby(d.index.date)
    D = pd.DataFrame({"H": g.high.max(), "L": g.low.min(), "C": g.close.last()})
    pc = D.C.shift(1)
    return np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs())).rolling(20).mean().shift(1)


def windows(mk, d, exit_min):
    """Okna 23:00 UTC (den D-1) -> 00:exit_min UTC (den D) pro vsedni dny D."""
    b = L.BROKER[mk]
    sbh = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    atr = atr_utc(d)
    idx = d.index
    rows = []
    days = sorted({x for x in idx.date if x.weekday() < 5})
    for D in days:
        t0 = pd.Timestamp(D, tz="UTC") - pd.Timedelta(hours=1)
        t1 = pd.Timestamp(D, tz="UTC") + pd.Timedelta(minutes=exit_min)
        i0 = idx.searchsorted(t0)
        i1 = idx.searchsorted(t1) - (0 if exit_min == 60 else 1)
        if i0 >= len(idx) or idx[i0] - t0 > pd.Timedelta(minutes=10) or i1 <= i0 or i1 >= len(idx):
            continue
        E = d.open.iloc[i0]
        X = d.open.iloc[i1] if exit_min == 60 else d.close.iloc[i1]
        if exit_min == 60 and idx[i1] != t1:
            continue
        if exit_min != 60 and t1 - idx[i1] > pd.Timedelta(minutes=10):
            continue
        a = atr.get(D, np.nan)
        if not a > 0:
            continue
        lon_h0 = t0.tz_convert("Europe/London").hour
        lon_h1 = t1.tz_convert("Europe/London").hour
        net = (X - E) - sbh[lon_h0] * E / 2 - sbh[lon_h1] * X / 2
        rows.append(dict(day=pd.Timestamp(D), ev=D in GOTOBI, R=net / a))
    return pd.DataFrame(rows)


def ex(T):
    e, o = T[T.ev].R, T[~T.ev].R
    diff, t = welch(e, o)
    return dict(ev=LB.st(e), base=LB.st(o), diff=diff, t=t)


def main():
    say("F48 Gotobi – long USDJPY 23:00 → 00:55 UTC (08:00 → 09:55 JST) v gotobi dny, převis nad stejným oknem v jiné dny")
    say("=" * 100)
    H = windows("USDJPY", hd("USDJPY"), 55)
    B = windows("USDJPY", broker_h1_utc("USDJPY"), 60)
    EJ = windows("EURJPY", broker_h1_utc("EURJPY"), 60)
    cut = pd.Timestamp("2019-01-01")
    R = {"vyvoj": ex(H[H.day < cut]), "kontrola": ex(B[B.day >= cut]), "zdroj2": ex(H[H.day >= cut]), "EURJPY": ex(EJ[EJ.day >= cut])}
    for k, v in R.items():
        say(f"{k:9s} gotobi: {LB.fmt(v['ev'])}")
        say(f"{'':9s} ostatní: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    say("Popis – broker 2010–2018 (stejný zdroj jako kontrola): " + (lambda v: f"převis {v['diff']:+.3f}, t {v['t']:+.2f}")(ex(B[B.day < cut])))
    allD = pd.concat([H[H.day < cut], B[B.day >= cut]])
    pos, line = [], []
    for y, g in allD.groupby(allD.day.dt.year):
        dy = g[g.ev].R.mean() - g[~g.ev].R.mean()
        pos.append(dy > 0)
        line.append(f"{y}:{dy:+.3f}")
    share = float(np.mean(pos))
    say("Po letech převis: " + "  ".join(line) + f" → kladný v {sum(pos)} z {len(pos)} ({share:.0%})")
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    v, k = R["vyvoj"], R["kontrola"]
    c = [("1) vývoj: gotobi > 0, převis > 0, t >= 2,0", v["ev"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['ev']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ("2) kontrola: gotobi > 0, převis > 0, t >= 1,5", k["ev"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['ev']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ("3) druhý zdroj převis > 0", R["zdroj2"]["diff"] > 0, f"{R['zdroj2']['diff']:+.3f}"),
         ("4) EURJPY převis > 0", R["EURJPY"]["diff"] > 0, f"{R['EURJPY']['diff']:+.3f}"),
         ("5) převis kladný v >= 60 % let", share >= 0.60, f"{share:.0%}")]
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
