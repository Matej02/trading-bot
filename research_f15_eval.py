"""
F15 - vyhodnoceni Hvezdy: vyber jen na vyvoji (do 2021), OOS 2022-26, nahodne swing vstupy (stejny trh, smer, SL a TP
v cene, BE pri 1R, stejne drzeni, nahodna H1 svicka stejneho obdobi), bez nakladu, vrstvy (COT, lokace, SL +20 %).
Spusteni: py research_f15_eval.py -> research_data/f15/f15_souhrn.txt
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
sys.stdout.reconfigure(encoding="utf-8")
import f7_lib as L
import research_f12_eval as EV
import research_f15_hve as V

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def random_swing(df, reps=5, seed=7):
    rng = np.random.default_rng(seed)
    R = []
    for mk, g in df.groupby("mk"):
        H = V.prep(mk)[0]
        n = len(H["c"])
        t = H["t"]
        for x in g.itertuples():
            pool = np.flatnonzero((t >= V.OOS) if x.t >= V.OOS else (t < V.OOS))
            pool = pool[pool < n - x.hold - 2]
            if not len(pool):
                continue
            for _ in range(reps):
                i0 = int(rng.choice(pool))
                d = int(x.d)
                E = H["o"][i0] + (H["spr"][i0] if d == 1 else 0)
                SL, TP = E - d * x.sl_dist, E + d * x.tp_dist
                sw = H["swl"] if d == 1 else H["sws"]
                r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], i0, i0, 1, d, E, SL, E + d * x.sl_dist, 1e-9,
                                TP, 1 - 1e-9, np.full(1, np.nan), 0, min(i0 + int(x.hold), n - 1), np.nan, H["hend"], 0, 0.0,
                                H["cum_sw"], sw)
                if r[0]:
                    R.append(r[1])
    return np.array(R)


def parse(v):
    d = dict(kv.split("=") for kv in v.split(" "))
    for k in ("base", "dvw", "lnl"):
        d[k] = int(d[k])
    return d


if __name__ == "__main__":
    df = pd.read_pickle(os.path.join(V.D15, "f15.pkl"))
    df["oos"] = df.t >= V.OOS
    say("=== F15 Hvězda – vyhodnocení", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
    say("obchodů", len(df), "| podle trhu", df[df["var"] == df["var"].iloc[0]].groupby("mk").size().to_dict())
    rows = []
    for v, g in df.groupby("var"):
        a, b = EV.st(g.R[~g.oos]), EV.st(g.R[g.oos])
        rows.append(dict(var=v, n_dev=a["n"], exp_dev=a["exp"], pf_dev=a["pf"], n_oos=b["n"], exp_oos=b["exp"], pf_oos=b["pf"]))
    tab = pd.DataFrame(rows).sort_values("exp_dev", ascending=False)
    say("\n--- 20 nejlepších variant na VÝVOJI (n_dev >= 30) a jejich OOS")
    top = tab[tab.n_dev >= 30]
    say(top.head(20).round(3).to_string(index=False))
    best = top.iloc[0]["var"]
    g = df[df["var"] == best]
    say("\n--- VYBRANÁ:", best)
    say("vývoj:", EV.fmt(EV.st(g.R[~g.oos])), "| OOS:", EV.fmt(EV.st(g.R[g.oos])))
    for mk, h in g.groupby("mk"):
        say(f"   {mk:11s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    say("náhoda vývoj", EV.fmt(EV.st(random_swing(g[~g.oos]))), "| OOS", EV.fmt(EV.st(random_swing(g[g.oos]))))
    say("\n--- průměr přes varianty podle parametru (vývoj | OOS)")
    kv = df["var"].str.split(" ", expand=True)
    for col in range(kv.shape[1]):
        for val, h in df.groupby(kv[col]):
            say(f"   {val:12s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    say("\n--- COT jako filtr: stejné ostatní parametry, porovnání cot=0 vs smer vs ext (všechny kombinace dohromady)")
    for c, h in df.groupby(kv[5]):
        say(f"   {c:10s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    nc = os.path.join(V.D15, "f15_nc.pkl")
    if os.path.exists(nc):
        dn = pd.read_pickle(nc)
        dn["oos"] = dn.t >= V.OOS
        gn = dn[dn["var"] == best]
        say("\n--- BEZ NÁKLADŮ: vybraná vývoj", EV.fmt(EV.st(gn.R[~gn.oos])), "| OOS", EV.fmt(EV.st(gn.R[gn.oos])),
            "| všechny OOS", EV.fmt(EV.st(dn.R[dn.oos])))
    var = parse(best)
    say("\n--- vrstvy (vybraná varianta)")
    for nm, ch in (("vybraná", {}), ("+ lokace (dolní třetina)", dict(lok=1)), ("+ SL +20 %", dict(sl20=1)),
                   ("COT vypnutý", dict(cot="0")), ("COT směr", dict(cot="smer")), ("COT extrém", dict(cot="ext"))):
        vv = {**var, **ch}
        rr = pd.DataFrame([r for mk in V.MARKETS for r in V.run_market(mk, vv)])
        if not len(rr):
            say(f"   {nm:26s} n 0")
            continue
        rr["oos"] = rr.t >= V.OOS
        say(f"   {nm:26s} vývoj {EV.fmt(EV.st(rr.R[~rr.oos]))} | OOS {EV.fmt(EV.st(rr.R[rr.oos]))}")
    open(os.path.join(V.D15, "f15_souhrn.txt"), "w", encoding="utf-8").write("\n".join(OUT))
