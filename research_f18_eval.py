"""
F18 - vyhodnoceni Valchare: vyber jen na vyvoji, OOS, nahoda (stejny trh, smer, SL/TP, max 30 dni, nahodna minuta stejneho
obdobi), bez nakladu, prumery parametru (hlavne filtr skore). Spusteni: py research_f18_eval.py -> research_data/f18/f18_souhrn.txt
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
sys.stdout.reconfigure(encoding="utf-8")
import research_f10 as X
import research_f12_eval as EV
import research_f18_val as V

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def load(suf=""):
    fr = [pd.read_pickle(os.path.join(V.D11, f"f18_{mk}{suf}.pkl")) for mk in V.MARKETS if os.path.exists(os.path.join(V.D11, f"f18_{mk}{suf}.pkl"))]
    df = pd.concat([f for f in fr if len(f)], ignore_index=True)
    df["oos"] = df.t >= X.OOS
    return df


def random_swing(df, reps=3, seed=5):
    rng = np.random.default_rng(seed)
    R = []
    for mk, g in df.groupby("mk"):
        M = X.load1(mk)
        n = len(M["c"])
        pool_d = np.flatnonzero(M["t"] < X.OOS)
        pool_o = np.flatnonzero(M["t"] >= X.OOS)
        for x in g.itertuples():
            pool = pool_o if x.oos else pool_d
            pool = pool[pool < n - 30 * 1440 - 2]
            for _ in range(reps):
                i0 = int(rng.choice(pool))
                d = int(x.d)
                E = M["o"][i0] + (M["spr"][i0] if d == 1 else 0)
                s = X.sim(M, d, E, E - d * x.sl_dist, E + d * x.tp_dist, i0, i0, 1, i0 + 30 * 1440)
                if s:
                    R.append(s["R"])
    return np.array(R)


if __name__ == "__main__":
    df = load()
    say("=== F18 Valchář – vyhodnocení", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
    rows = []
    for v, g in df.groupby("var"):
        a, b = EV.st(g.R[~g.oos]), EV.st(g.R[g.oos])
        rows.append(dict(var=v, n_dev=a["n"], exp_dev=a["exp"], pf_dev=a["pf"], n_oos=b["n"], exp_oos=b["exp"], pf_oos=b["pf"]))
    tab = pd.DataFrame(rows).sort_values("exp_dev", ascending=False)
    say("\n--- 15 nejlepších variant na VÝVOJI (n_dev >= 40) a jejich OOS")
    top = tab[tab.n_dev >= 40]
    say(top.head(15).round(3).to_string(index=False))
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
            say(f"   {val:14s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    say("\n--- skóre jen na párech se skóre (OOS do 2024-10): stejné ostatní parametry")
    sc = df[df.mk.isin(V.SCORED) & (df.t < pd.Timestamp("2024-10-04", tz="UTC").value // 10**9)]
    for val, h in sc.groupby(sc["var"].str.extract(r"score=(\w+)")[0]):
        say(f"   score={val:6s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    if os.path.exists(os.path.join(V.D11, "f18_EURUSD_nc.pkl")):
        dn = load("_nc")
        gn = dn[dn["var"] == best]
        say("\n--- BEZ NÁKLADŮ: vybraná vývoj", EV.fmt(EV.st(gn.R[~gn.oos])), "| OOS", EV.fmt(EV.st(gn.R[gn.oos])),
            "| všechny OOS", EV.fmt(EV.st(dn.R[dn.oos])))
    open(os.path.join(V.D11, "f18_souhrn.txt"), "w", encoding="utf-8").write("\n".join(OUT))
