"""
F28 - intradenni momentum (prvni pulhodina -> posledni pulhodina). Plan predem ve vaultu (Vyzkum/F28 ...).
Spusteni: python -I f28_momentum.py -> D:\\Trading bot\\research_data\\f28\\f28_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

OUT = os.path.join(LB.ROOT, "research_data", "f28")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
# tz, minuta svicky predchoziho zavreni, minuta mereni r1 (otevreni), vstup (otevreni), vystup (zavreni svicky)
SES = {"US": ("America/New_York", 959, 600, 930, 959), "EU": ("Europe/Berlin", 1049, 570, 1020, 1049)}
MS = {"SPX500mini": "US", "NAS100mini": "US", "US30mini": "US", "GER_30mini": "EU"}
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def prep(mk, src):
    d = LB.load_m1(mk, src)
    tick = LB.add_costs(mk, d, LB.broker_ref(mk))
    tz, pc, m1, en, ex = SES[MS[mk]]
    loc = d.u.dt.tz_convert(tz)
    d["date"] = loc.dt.date
    d["mod"] = loc.dt.hour * 60 + loc.dt.minute
    d = d[loc.dt.dayofweek < 5]
    atr = LB.daily_atr(d, tz)

    def pick(mn, first=True, col="o", tol=2):
        x = d[(d["mod"] >= mn - (0 if first else tol)) & (d["mod"] <= mn + (tol if first else 0))]
        g = x.groupby("date")
        return (g.first() if first else g.last())[[col, "spr", "u"]]
    C0 = pick(pc, first=False, col="c")
    R1 = pick(m1, col="o")
    EN = pick(en, col="o")
    EX = pick(ex, first=False, col="c")
    dates = sorted(set(R1.index) & set(EN.index) & set(EX.index))
    cd = np.array(sorted(C0.index))
    rows = []
    for dt in dates:
        k = np.searchsorted(cd, dt) - 1                    # predchozi den se zavrenim
        a = atr.get(dt, np.nan)
        if k < 0 or not a > 0:
            continue
        c0 = C0.loc[cd[k], "c"]
        r1 = R1.loc[dt, "o"] / c0 - 1
        if r1 == 0:
            continue
        dd = 1 if r1 > 0 else -1
        e, x = EN.loc[dt], EX.loc[dt]
        if dd == 1:
            pnl = (x.c - tick) - (e.o + e.spr + tick)
        else:
            pnl = (e.o - tick) - (x.c + x.spr + tick)
        rows.append(dict(mk=mk, date=dt, u=e.u, d=dd, r1=r1, R=pnl / a, Rg=dd * (x.c - e.o) / a,
                         base=(x.c - e.o) / a, cost=(e.spr + 2 * tick) / a))
    return pd.DataFrame(rows)


def rnd(T, reps=3, seed=9):
    """Nahoda: stejny smer, stejne okno, ale nahodny den stejneho obdobi a trhu."""
    rng = np.random.default_rng(seed)
    R = []
    for mk, g in T.groupby("mk"):
        base, cost = g.base.to_numpy(), g.cost.to_numpy()
        for d in g.d.to_numpy():
            for _ in range(reps):
                j = int(rng.integers(0, len(g)))
                R.append(d * base[j] - cost[j])
    return np.array(R)


say("F28 Intradenní momentum – směr od včerejšího zavření do 10:00 NY → obchod 15:30–16:00 NY (DAX 9:30 → 17:00–17:30)")
say("R = výsledek po nákladech / ATR20 denního rozpětí")
say("=" * 100)
P = {}
for mk in ("SPX500mini", "NAS100mini", "US30mini", "GER_30mini"):
    P[("broker", mk)] = prep(mk, "broker")
    if mk in ("SPX500mini", "NAS100mini"):
        P[("hd", mk)] = prep(mk, "hd")
sp = LB.SPLIT
parts = {"vyvoj": [P[("hd", m)][P[("hd", m)].u < sp] for m in ("SPX500mini", "NAS100mini")],
         "kontrola": [P[("broker", m)][P[("broker", m)].u >= sp] for m in ("SPX500mini", "NAS100mini")],
         "zdroj2": [P[("hd", m)][(P[("hd", m)].u >= sp) & (P[("hd", m)].u < LB.HD_END)] for m in ("SPX500mini", "NAS100mini")],
         "US30": [P[("broker", "US30mini")][P[("broker", "US30mini")].u >= sp]],
         "DAX": [P[("broker", "GER_30mini")][P[("broker", "GER_30mini")].u >= sp]]}
S = {}
for name, fr in parts.items():
    T = pd.concat(fr, ignore_index=True)
    T.to_pickle(os.path.join(OUT, f"f28_{name}.pkl"))
    S[name] = LB.st(T.R)
    say(f"\n{name.upper():9s}", LB.fmt(S[name]), f"| bez nákladů {LB.fmt(LB.st(T.Rg))}")
    say("   long / short:", LB.fmt(LB.st(T.R[T.d == 1])), "/", LB.fmt(LB.st(T.R[T.d == -1])))
    say(f"   průměrné náklady {T.cost.mean():.3f} R na obchod; průměrný pohyb poslední půlhodiny |base| {T.base.abs().mean():.3f} R")
    if name in ("vyvoj", "kontrola"):
        S[name + "_rnd"] = LB.st(rnd(T))
        say("   náhoda:", LB.fmt(S[name + "_rnd"]))
allT = pd.concat([pd.read_pickle(os.path.join(OUT, f"f28_{p}.pkl")) for p in ("vyvoj", "kontrola")])
say("\nPo letech:")
for y, g in allT.groupby(pd.to_datetime(allT.u, utc=True).dt.year):
    say(f"   {y}: n {len(g):4d}  {g.R.mean():+.4f} R  bez nákladů {g.Rg.mean():+.4f} R")
say("\nROZHODNUTÍ podle pravidel zapsaných předem")
LB.decide(say, S["vyvoj"], S["kontrola"], {"US30": S["US30"], "DAX": S["DAX"]}, S["vyvoj_rnd"], S["kontrola_rnd"], S["zdroj2"])
open(os.path.join(OUT, "f28_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
