"""
F20 - vyhodnoceni obecne strategie uzivatele: sklada varianty (bias, poi, vp, vol, entry, tp) z kandidatu SFP,
"jedna pozice naraz a max 2 obchody denne" na trh, vyber jen na vyvoji (n >= 30), OOS, nahoda, bez nakladu, vrstvy, trhy.
Spusteni: py research_f20_eval.py -> research_data/f20/f20_souhrn.txt
"""
import itertools
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
sys.stdout.reconfigure(encoding="utf-8")
import research_f10 as X
import research_f12_eval as EV
import research_f20_user as U

OUT = []
BIAS = {"4H": lambda g: g.b4, "4H15": lambda g: g.b4 & g.b15, "zadny": lambda g: np.ones(len(g), bool)}
POI = {"zona": lambda g: g.pz, "zonapoc": lambda g: g.pz | g.pp, "zadne": lambda g: np.ones(len(g), bool)}
VP = {"2": lambda g: g.vp >= 2, "3": lambda g: g.vp == 3, "0": lambda g: np.ones(len(g), bool)}
VOL = {"1": lambda g: g.vol, "0": lambda g: np.ones(len(g), bool)}


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def load(suf=""):
    fr = [pd.read_pickle(os.path.join(U.D20, f"f20_{mk}{suf}.pkl")) for mk in U.MARKETS]
    return {(mk, e, t): g.sort_values("fi") for f in fr if len(f) for (mk, e, t), g in f.groupby(["mk", "entry", "tp"])}


def sequential(g):
    """Jedna pozice naraz, max 2 obchody za prazsky den."""
    fi, ex, day = g.fi.to_numpy(), g.ex.to_numpy(), g.day.to_numpy()
    keep = np.zeros(len(g), bool)
    last, cnt = -1, {}
    for k in range(len(g)):
        if fi[k] <= last or cnt.get(day[k], 0) >= 2:
            continue
        keep[k] = True
        last = ex[k]
        cnt[day[k]] = cnt.get(day[k], 0) + 1
    return g[keep]


def variant(G, b, p, v, vo, e, t):
    parts = []
    for mk in U.MARKETS:
        g = G.get((mk, e, t))
        if g is None:
            continue
        m = BIAS[b](g) & POI[p](g) & VP[v](g) & VOL[vo](g)
        parts.append(sequential(g[np.asarray(m)]))
    return pd.concat(parts) if parts else pd.DataFrame()


def name(b, p, v, vo, e, t):
    return f"bias={b} poi={p} vp={v} vol={vo} entry={e} tp={t}"


if __name__ == "__main__":
    G = load()
    say("=== F20 obecná strategie uživatele – vyhodnocení", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
    rows, ALL = [], {}
    for combo in itertools.product(BIAS, POI, VP, VOL, U.ENTRIES, U.TPS):
        df = variant(G, *combo)
        if not len(df):
            continue
        nm = name(*combo)
        ALL[nm] = df
        a, b = EV.st(df.R[~df.oos]), EV.st(df.R[df.oos])
        rows.append(dict(var=nm, n_dev=a["n"], exp_dev=a["exp"], pf_dev=a["pf"], n_oos=b["n"], exp_oos=b["exp"], pf_oos=b["pf"]))
    tab = pd.DataFrame(rows).sort_values("exp_dev", ascending=False)
    top = tab[tab.n_dev >= 30]
    say("\n--- 15 nejlepších variant na VÝVOJI (n_dev >= 30) a jejich OOS")
    say(top.head(15).round(3).to_string(index=False))
    say("\nvariant celkem", len(tab), "| kladných na vývoji", int((top.exp_dev > 0).sum()), "| kladných na OOS", int((tab.exp_oos > 0).sum()),
        "| kladných v obou", int(((top.exp_dev > 0) & (top.exp_oos > 0)).sum()))
    best = top.iloc[0]["var"]
    g = ALL[best]
    say("\n--- VYBRANÁ:", best)
    say("vývoj:", EV.fmt(EV.st(g.R[~g.oos])), "| OOS:", EV.fmt(EV.st(g.R[g.oos])))
    for mk, h in g.groupby("mk"):
        say(f"   {mk:11s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    say("náhoda vývoj", EV.fmt(EV.st(EV.random_base(g[~g.oos], reps=3))), "| OOS", EV.fmt(EV.st(EV.random_base(g[g.oos], reps=3))))
    say("\n--- průměr přes varianty podle parametru (všechny obchody variant dohromady; vývoj | OOS)")
    kv = tab["var"].str.split(" ", expand=True)
    for col in range(kv.shape[1]):
        for val in sorted(kv[col].unique()):
            sel = tab["var"][kv[col] == val]
            R = pd.concat([ALL[s][["R", "oos"]] for s in sel])
            say(f"   {val:14s} vývoj {EV.fmt(EV.st(R.R[~R.oos]))} | OOS {EV.fmt(EV.st(R.R[R.oos]))}")
    say("\n--- trhy (průměr přes všechny varianty; vývoj | OOS)")
    R = pd.concat([ALL[s][["R", "oos", "mk"]] for s in tab["var"]])
    for mk, h in R.groupby("mk"):
        say(f"   {mk:11s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    if os.path.exists(os.path.join(U.D20, "f20_EURUSD_nc.pkl")):
        Gn = load("_nc")
        gn = variant(Gn, *[x.split("=")[1] for x in best.split(" ")])
        say("\n--- BEZ NÁKLADŮ: vybraná vývoj", EV.fmt(EV.st(gn.R[~gn.oos])), "| OOS", EV.fmt(EV.st(gn.R[gn.oos])))
        Rn = []
        for combo in itertools.product(BIAS, POI, VP, VOL, U.ENTRIES, U.TPS):
            d = variant(Gn, *combo)
            if len(d):
                Rn.append(d[["R", "oos"]])
        Rn = pd.concat(Rn)
        say("    všechny varianty bez nákladů: vývoj", EV.fmt(EV.st(Rn.R[~Rn.oos])), "| OOS", EV.fmt(EV.st(Rn.R[Rn.oos])))
        say("    jen SFP + FRVP 3/3 bez dalších filtrů, vstup close, 2R, bez nákladů:",
            EV.fmt(EV.st(variant(Gn, "zadny", "zadne", "3", "0", "close", "2R").R)))
    open(os.path.join(U.D20, "f20_souhrn.txt"), "w", encoding="utf-8").write("\n".join(OUT))
