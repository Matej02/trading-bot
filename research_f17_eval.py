"""
F17 + F19 - vyhodnoceni Srajera (day trading + swing) a Kimmela modelu 2: vyber jen na vyvoji, OOS, nahoda, bez nakladu, parametry.
Spusteni: py research_f17_eval.py dt|swing|kim
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
sys.stdout.reconfigure(encoding="utf-8")
import f7_lib as L
import research_f10 as X
import research_f12_eval as EV
import research_f17_sra as V

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def random_swing_h1(df, reps=5, seed=11):
    rng = np.random.default_rng(seed)
    R = []
    for mk, g in df.groupby("mk"):
        H = V.prep_sw(mk)["H"]
        n, t = len(H["c"]), H["t"]
        for x in g.itertuples():
            pool = np.flatnonzero((t >= X.OOS) if x.t >= X.OOS else (t < X.OOS))
            pool = pool[pool < n - x.hold - 2]
            for _ in range(reps):
                i0 = int(rng.choice(pool))
                d = int(x.d)
                E = H["o"][i0] + (H["spr"][i0] if d == 1 else 0)
                r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], i0, i0, 1, d, E, E - d * x.sl_dist,
                                E + d * x.tp_dist, 1.0, np.nan, np.nan, np.full(1, np.nan), 0, min(i0 + int(x.hold), n - 1), np.nan,
                                H["hend"], 0, 0.0, H["cum_sw"], H["swl"] if d == 1 else H["sws"])
                if r[0]:
                    R.append(r[1])
    return np.array(R)


if __name__ == "__main__":
    part = sys.argv[1]
    path = {"dt": os.path.join(V.D17, "f17_dt"), "swing": os.path.join(V.D17, "f17_swing"),
            "kim": os.path.join("research_data", "f19", "f19")}[part]
    df = pd.read_pickle(path + ".pkl")
    df["oos"] = df.t >= X.OOS
    if part == "swing":
        df = df[df.t < pd.Timestamp("2024-10-04", tz="UTC").value // 10**9].copy()   # skore konci 2024-10-03
    say(f"=== {part} – vyhodnocení", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"), "| obchodů", len(df))
    rows = []
    for v, g in df.groupby("var"):
        a, b = EV.st(g.R[~g.oos]), EV.st(g.R[g.oos])
        rows.append(dict(var=v, n_dev=a["n"], exp_dev=a["exp"], pf_dev=a["pf"], n_oos=b["n"], exp_oos=b["exp"], pf_oos=b["pf"]))
    tab = pd.DataFrame(rows).sort_values("exp_dev", ascending=False)
    say(tab.head(15).round(3).to_string(index=False))
    top = tab[tab.n_dev >= 30]
    best = (top if len(top) else tab).iloc[0]["var"]
    g = df[df["var"] == best]
    say("\n--- VYBRANÁ:", best)
    say("vývoj:", EV.fmt(EV.st(g.R[~g.oos])), "| OOS:", EV.fmt(EV.st(g.R[g.oos])))
    for mk, h in g.groupby("mk"):
        say(f"   {mk:11s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    if part == "swing":
        say("náhoda vývoj", EV.fmt(EV.st(random_swing_h1(g[~g.oos]))), "| OOS", EV.fmt(EV.st(random_swing_h1(g[g.oos]))))
    else:
        say("náhoda vývoj", EV.fmt(EV.st(EV.random_base(g[~g.oos], reps=3))), "| OOS", EV.fmt(EV.st(EV.random_base(g[g.oos], reps=3))))
    say("\n--- průměr přes varianty podle parametru (vývoj | OOS)")
    kv = df["var"].str.split(" ", expand=True)
    for col in range(kv.shape[1]):
        for val, h in df.groupby(kv[col]):
            say(f"   {val:12s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    if os.path.exists(path + "_nc.pkl"):
        dn = pd.read_pickle(path + "_nc.pkl")
        dn["oos"] = dn.t >= X.OOS
        gn = dn[dn["var"] == best]
        say("\n--- BEZ NÁKLADŮ: vybraná vývoj", EV.fmt(EV.st(gn.R[~gn.oos])), "| OOS", EV.fmt(EV.st(gn.R[gn.oos])),
            "| všechny OOS", EV.fmt(EV.st(dn.R[dn.oos])))
    open(path + "_souhrn.txt", "w", encoding="utf-8").write("\n".join(OUT))
