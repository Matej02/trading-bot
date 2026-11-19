"""
F41 - F31 drift pred FOMC na HistData DAX a EuroStoxx 2010-2018 (+ DAX 2019-2025).
Plan predem ve vaultu: Vyzkum/F41 F31 na evropskych indexech 2010-2018.md (2026-11-19).
Spusteni: python -I f41_fomc_evropa.py -> D:\\Trading bot\\research_data\\f41\\souhrn.txt
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f41")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
K = json.load(open(os.path.join(RD, "kalendar_2010_2021.json")))
FOMC = {pd.Timestamp(x).date() for x in K["FOMC"] + [d for d in L.FOMC if d >= "2021-09-01"]}
TZ = "America/New_York"
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def load(sym):
    d = pd.read_pickle(os.path.join(RD, "histdata", "m1_fx", f"{sym}.pkl"))   # index UTC (z f35_f38.py, cas NY s letnim casem)
    jump = np.log(d.close).diff().abs()
    bad = jump > np.log(1.2)
    bad = bad | bad.shift(-1, fill_value=False)   # chybny tick: skok tam i zpet
    say(f"{sym}: vyřazeno chybných minut {int(bad.sum())}")
    return d[~bad]


def atr_daily(d):
    loc = d.index.tz_convert(TZ)
    g = d.groupby(loc.date)
    D = pd.DataFrame({"H": g.high.max(), "L": g.low.min(), "C": g.close.last()})
    pc = D.C.shift(1)
    tr = np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs()))
    return tr.rolling(20).mean().shift(1)


def px(d, t, side):
    i = d.index.searchsorted(t, "left")
    if side == "in":
        if i >= len(d) or d.index[i] - t > pd.Timedelta(minutes=30):
            return np.nan
        return d.open.iloc[i]
    i -= 1
    if i < 0 or t - d.index[i] > pd.Timedelta(minutes=30):
        return np.nan
    return d.close.iloc[i]


def nights(d0, d1):
    days = pd.date_range(pd.Timestamp(d0) + pd.Timedelta(days=1), pd.Timestamp(d1), freq="D")
    w = days.day_of_week
    return int(((w < 5) & (w != 3)).sum() + 3 * (w == 3).sum())


def windows(mk, d):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    atr = atr_daily(d)
    days = sorted({x for x in d.index.tz_convert(TZ).date if pd.Timestamp(x).day_of_week < 5})
    rows = []
    for P, T in zip(days[:-1], days[1:]):
        if (pd.Timestamp(T) - pd.Timestamp(P)).days > 4:
            continue
        t0 = pd.Timestamp(f"{P} 14:00", tz=TZ)
        t1 = pd.Timestamp(f"{T} 13:55", tz=TZ)
        E, X = px(d, t0, "in"), px(d, t1, "out")
        a = atr.get(P, np.nan)
        if not (E > 0 and X > 0 and a > 0):
            continue
        net = (X - E) - rel * (E + X) / 2 + b["swapLong"] * E * nights(P, T)
        rows.append(dict(day=pd.Timestamp(T), ev=T in FOMC, R=net / a))
    return pd.DataFrame(rows)


say("F41 – F31 drift před FOMC (long 14:00 NY den předem → 13:55 NY v den oznámení) na HistData DAX a EuroStoxx")
say("=" * 100)
DAX = windows("GER_30mini", load("GRXEUR"))
ES = windows("EUR_50mini", load("ETXEUR"))
cut = pd.Timestamp("2019-01-01")
D18, E18 = DAX[DAX.day < cut], ES[ES.day < cut]
ev = pd.concat([D18[D18.ev].set_index("day").R.rename("dax"), E18[E18.ev].set_index("day").R.rename("es")], axis=1)
ot = pd.concat([D18[~D18.ev].set_index("day").R.rename("dax"), E18[~E18.ev].set_index("day").R.rename("es")], axis=1)
e_avg, o_avg = ev.mean(axis=1).dropna(), ot.mean(axis=1).dropna()
s_ev, s_ot = LB.st(e_avg), LB.st(o_avg)
diff = s_ev["m"] - s_ot["m"]
tdiff = diff / np.sqrt(e_avg.var(ddof=1) / len(e_avg) + o_avg.var(ddof=1) / len(o_avg))
say(f"2010–2018 po událostech (DAX+ES): {LB.fmt(s_ev)}")
say(f"stejné okno ostatní dny:          {LB.fmt(s_ot)}")
say(f"převis nad driftem: {diff:+.3f} R, t {tdiff:+.2f}")
s_dax, s_es = LB.st(D18[D18.ev].R), LB.st(E18[E18.ev].R)
say(f"DAX 2010–2018:      {LB.fmt(s_dax)}")
say(f"EuroStoxx 2010–18:  {LB.fmt(s_es)}")
s_d19 = LB.st(DAX[(DAX.day >= cut) & DAX.ev].R)
say(f"DAX 2019–2025 (HistData): {LB.fmt(s_d19)}   (F31 broker DAX 2019–26: +0,228 R)")
say("Po letech (DAX+ES 2010–2018, po událostech): " + "  ".join(f"{y}:{g.mean():+.2f}" for y, g in e_avg.groupby(e_avg.index.year)))
say("Popis 2013–2018 (v F31 na US indexech ~0): " + LB.fmt(LB.st(e_avg[e_avg.index >= "2013-01-01"])))
say("ROZHODNUTÍ podle pravidel zapsaných předem")
c = [("1) 2010–2018 po událostech > 0 a t >= 1,5", s_ev["m"] > 0 and s_ev["t"] >= 1.5, f"{s_ev['m']:+.3f} R, t {s_ev['t']:+.2f}"),
     ("2) převis nad ostatními dny > 0", diff > 0, f"{diff:+.3f}"),
     ("3) DAX i EuroStoxx > 0", s_dax["m"] > 0 and s_es["m"] > 0, f"DAX {s_dax['m']:+.3f}, ES {s_es['m']:+.3f}"),
     ("4) HistData DAX 2019–2025 > 0", s_d19["m"] > 0, f"{s_d19['m']:+.3f}")]
for nm, ok, val in c:
    say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'PROŠLO (F31 posílena)' if all(x[1] for x in c) else 'NEPROŠLO (F31 zůstává kandidát)'}")
open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
