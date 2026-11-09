"""
F34 - limit rizika pro korelovane trhy (veto 1 pozice ve skupine a smeru / strop 1,5 R). Plan predem ve vaultu.
Spusteni: python -I f34_korelace.py -> D:\\Trading bot\\research_data\\f34\\f34_souhrn.txt
"""
import os
import sys

import numpy as np
import pandas as pd

RD = r"D:\Trading bot\research_data"
OUT = os.path.join(RD, "f34")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
GROUP = {**{m: "US" for m in ("SPX500mini", "NAS100mini", "US30mini", "SPX500fut", "NAS100fut")},
         **{m: "EU" for m in ("GER_30mini", "GBR_100mini", "FRA_40mini", "EUR_50mini", "ESP_35mini")},
         "XAUUSD": "KOVY", "XAGUSD": "KOVY", "BTCUSD": "KRYPTO", "ETHUSD": "KRYPTO"}
ORDER = {m: i for i, m in enumerate(["SPX500mini", "NAS100mini", "US30mini", "GER_30mini", "XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD"])}
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def load():
    a = pd.read_csv(os.path.join(RD, "f6_obchody.csv"))
    rsi = a[(a.strat == "MR1") & (a.dir == 1) & a.market.isin(["SPX500mini", "NAS100mini", "US30mini"])].copy()
    rsi["t0"] = pd.to_datetime(rsi.time)
    rsi["t1"] = rsi.t0 + pd.to_timedelta(rsi.cal, unit="D")
    rsi["sys"] = "RSI2"
    b = pd.read_csv(os.path.join(RD, "f4_obchody.csv"))
    pr = b[b.varianta.str.startswith("A ")].copy()
    pr["t0"] = pd.to_datetime(pr.time)
    pr["t1"] = pr.t0 + pd.to_timedelta(pr.bars, unit="D")
    pr["sys"] = "PRURAZ"
    f = pd.read_pickle(os.path.join(RD, "f33", "f33_yahoo.pkl"))
    f33 = pd.DataFrame({"market": f.mk, "dir": f.d, "R": f.R, "t0": pd.to_datetime(f.t)})
    f33["t1"] = f33.t0 + pd.Timedelta(days=4)
    f33["sys"] = "F33"
    cols = ["sys", "market", "dir", "R", "t0", "t1"]
    return rsi[cols], pr[cols], f33[cols]


def simulate(T, rule):
    """Vrati obchody s vahou (0 = nebran) podle pravidla: None / 'A' veto / 'B' strop 1,5."""
    T = T.assign(o=T.market.map(ORDER).fillna(99)).sort_values(["t0", "o"]).reset_index(drop=True)
    w = np.ones(len(T))
    open_ = []                                   # (t1, group, dir, weight)
    for i, r in T.iterrows():
        open_ = [x for x in open_ if x[0] > r.t0]
        g = GROUP.get(r.market)
        if rule and g:
            same = [x for x in open_ if x[1] == g and x[2] == r.dir]
            if rule == "A" and same:
                w[i] = 0
            elif rule == "B":
                left = 1.5 - sum(x[3] for x in same)
                w[i] = min(1.0, left) if left >= 0.25 else 0
        if w[i] > 0:
            open_.append((r.t1, g, r.dir, w[i]))
    return T.assign(w=w)


def metrics(T):
    x = T[T.w > 0].sort_values("t1")
    pnl = (x.R * x.w).to_numpy()
    eq = np.cumsum(pnl)
    dd = float(np.max(np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq])) if len(eq) else 0.0
    m = (x.R * x.w).groupby(x.t1.dt.to_period("M")).sum()
    tot = float(pnl.sum())
    return dict(n=len(x), tot=tot, dd=dd, mar=tot / dd if dd > 0 else np.inf, worst_m=float(m.min()) if len(m) else 0.0)


def fmt(s):
    return f"obchodů {s['n']:5d} | součet {s['tot']:+8.1f} R | max propad {s['dd']:6.1f} R | MAR {s['mar']:5.2f} | nejhorší měsíc {s['worst_m']:+6.1f} R"


say("F34 Limit rizika pro korelované trhy – bez limitu / A (1 pozice ve skupině a směru) / B (strop 1,5 R)")
say("=" * 110)
rsi, pr, f33 = load()
sets = {"RSI(2) US indexy": rsi, "Průraz F2 (9 trhů)": pr, "Portfolio RSI(2) + Průraz + F33": pd.concat([rsi, pr, f33], ignore_index=True)}
res = {}
for name, T in sets.items():
    say(f"\n{name}")
    for per, lo, hi in (("do 2018", "1900-01-01", "2019-01-01"), ("od 2019", "2019-01-01", "2100-01-01")):
        P = T[(T.t0 >= lo) & (T.t0 < hi)]
        for rule in (None, "A", "B"):
            s = metrics(simulate(P, rule))
            res[(name, per, rule)] = s
            say(f"   {per:8s} {('bez limitu' if rule is None else 'pravidlo ' + rule):11s} {fmt(s)}")
say("\nROZHODNUTÍ podle pravidel zapsaných předem (MAR vyšší v obou obdobích a součet R nejvýš −25 %)")
for name in sets:
    ok = {}
    for rule in ("A", "B"):
        c = []
        for per in ("do 2018", "od 2019"):
            b, r = res[(name, per, None)], res[(name, per, rule)]
            c.append(r["mar"] > b["mar"] and r["tot"] >= 0.75 * b["tot"])
        ok[rule] = all(c)
    best = [r for r in ("A", "B") if ok[r]]
    pick = max(best, key=lambda r: res[(name, "od 2019", r)]["mar"]) if best else None
    say(f"   {name}: A {'ANO' if ok['A'] else 'NE'}, B {'ANO' if ok['B'] else 'NE'} → {('zavést pravidlo ' + pick) if pick else 'nezavádět'}")
open(os.path.join(OUT, "f34_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
