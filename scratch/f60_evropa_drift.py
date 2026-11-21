"""
F60 nocni drift US indexu pri otevreni Evropy (long 02:00 -> 03:00 New York), srovnani = ostatni hodiny dne.
Plan predem ve vaultu: Vyzkum/F60 Nocni drift pri otevreni Evropy.md (2026-11-20).
Spusteni: python -I f60_evropa_drift.py -> D:\\Trading bot\\research_data\\f60\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402

LB, L = F.LB, F.L
RD = F.RD
OUT = os.path.join(RD, "f60")
os.makedirs(OUT, exist_ok=True)
HD = os.path.join(RD, "histdata", "m1", "m1_skutecne_utc")
FX = os.path.join(RD, "histdata", "m1_fx")
NY, LON = "America/New_York", "Europe/London"
SIG_H = 2
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def to_h1(m):
    r = m.resample("1h")
    return pd.DataFrame({"open": r.open.first(), "high": r.high.max(), "low": r.low.min(), "close": r.close.last()}).dropna()


def hd_index(mk):
    d = pd.read_pickle(os.path.join(HD, f"{mk}_M1.pkl"))
    m = pd.DataFrame({"open": d.o.to_numpy(), "high": d.h.to_numpy(), "low": d.l.to_numpy(), "close": d.c.to_numpy()},
                     index=pd.to_datetime(d.t, unit="s").dt.tz_localize("UTC"))
    return to_h1(m[~m.index.duplicated()].sort_index())


def hd_fx(sym):
    m = pd.read_pickle(os.path.join(FX, f"{sym}.pkl"))
    # chybne ticky HistData: skok > 20 % za minutu pryc
    j = (m.close / m.close.shift(1) - 1).abs()
    return to_h1(m[~(j > 0.2)])


def br_h1(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))[["open", "high", "low", "close"]].astype(float)
    u = pd.DatetimeIndex(h.index).tz_localize("UTC")
    dst = np.array([x.dst().seconds > 0 for x in (u + pd.Timedelta(hours=1)).tz_convert(LON)])
    h.index = u + pd.to_timedelta(dst.astype(np.int64) * 3600, unit="s")
    return h[~h.index.duplicated()].sort_index()


def trades(mk, h):
    """Kazda cela hodina NY: long open -> close H1 svicky. Vrati DataFrame (day, hr, R, prev)."""
    b = L.BROKER[mk]
    spr = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0) / float(h.close.iloc[-1])
    ny = h.index.tz_convert(NY)
    lon_h = h.index.tz_convert(LON).hour
    g = h.groupby(ny.date)
    D = pd.DataFrame({"H": g.high.max(), "L": g.low.min(), "C": g.close.last()})
    pc = D.C.shift(1)
    atr = np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs())).rolling(20).mean().shift(1)
    # predchozi US seance: zavreni svicky 15:00 NY vs. zavreni 15:00 NY o obchodni den driv
    c15 = pd.Series(h.close.to_numpy(), index=ny)[ny.hour == 15]
    c15.index = c15.index.date
    c15 = c15[~c15.index.duplicated()]
    prev_ret = (c15 - c15.shift(1)).shift(1)             # pro den D: navrat D-1 vs D-2
    day = pd.Index(ny.date)
    A = atr.reindex(day).to_numpy()
    O, C = h.open.to_numpy(), h.close.to_numpy()
    cost = (spr[lon_h] / 2 * O + spr[lon_h] / 2 * C)
    R = (C - O - cost) / A
    T = pd.DataFrame({"day": pd.to_datetime(day), "hr": ny.hour, "R": R, "wd": ny.dayofweek,
                      "prev": prev_ret.reindex(day).to_numpy()})
    T = T[(T.wd < 5) & np.isfinite(T.R)]
    return T


def ev(pairs, a=None, b=None, cond=None):
    Ts = [trades(mk, h) for mk, h in pairs]
    T = pd.concat(Ts)
    if a is not None:
        T = T[T.day >= a]
    if b is not None:
        T = T[T.day < b]
    sg = T[T.hr == SIG_H]
    if cond == "down":
        sg = sg[sg.prev < 0]
    elif cond == "up":
        sg = sg[sg.prev > 0]
    s = sg.groupby("day").R.mean()
    bb = T[T.hr != SIG_H].groupby(["day", "hr"]).R.mean()
    diff, t = F.welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb.groupby(level=0).mean(), T=T)


def main():
    say("F60 NOČNÍ DRIFT PŘI OTEVŘENÍ EVROPY – long 02:00 → 03:00 NY (08–09 Praha); srovnání = ostatní celé hodiny dne")
    say("=" * 100)
    SP = pd.Timestamp("2019-01-01")
    HDm = [(m, hd_index(m)) for m in ("SPX500mini", "NAS100mini")]
    BRm = [(m, br_h1(m)) for m in ("SPX500mini", "NAS100mini", "US30mini")]
    OT = [("GER_30mini", hd_fx("GRXEUR")), ("EUR_50mini", hd_fx("ETXEUR"))]
    R = {"vyvoj": ev(HDm, pd.Timestamp("2010-01-01"), SP), "kontrola": ev(HDm, SP, None), "broker": ev(BRm, SP, None)}
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    oth = ev(OT)
    say(f"jiné trhy DAX, EuroStoxx (HistData): signál {LB.fmt(oth['sig'])} | převis {oth['diff']:+.3f}, t {oth['t']:+.2f}")
    for mk, h in HDm + BRm + OT:
        v = ev([(mk, h)])
        say(f"   {mk:12s} {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    full = ev(HDm)
    prof = full["T"].groupby("hr").R.agg(["mean", "count"])
    say("popis – průměr R podle hodiny NY (HistData SPX+NAS 2010–2025): " + "  ".join(f"{hh:02d}:{m:+.3f}" for hh, (m, _) in prof.iterrows()))
    for cnd in ("down", "up"):
        for nm, a, b in (("vývoj", pd.Timestamp("2010-01-01"), SP), ("kontrola", SP, None)):
            v = ev(HDm, a, b, cond=cnd)
            say(f"popis – po {'poklesu' if cnd == 'down' else 'růstu'} předchozího dne, {nm}: {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    ys = sorted(set(full["s"].index.year))
    dif = {y: full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean() for y in ys}
    say("po letech převis: " + "  ".join(f"{y}:{v:+.3f}" for y, v in dif.items()))
    pos = [v > 0 for v in dif.values()]
    share = float(np.mean(pos))
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    c = [("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ("3) jiné trhy převis > 0", oth["diff"] > 0, f"{oth['diff']:+.3f}"),
         ("4) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
         ("5) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
