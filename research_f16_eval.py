"""
F16 - vyhodnoceni Hakimi: vyber jen na vyvoji na XAU+XAG, OOS, nahoda (stejne SL/TP, cas, smer), trhy mimo vyber
(EURUSD, GBPUSD, NAS100), bez nakladu, prumery parametru. Spusteni: py research_f16_eval.py -> research_data/f16/f16_souhrn.txt
"""
import os
import sys

import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
sys.stdout.reconfigure(encoding="utf-8")
import research_f10 as X
import research_f12_eval as EV
import research_f16_hak as V

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def load(mks, suf=""):
    fr = [pd.read_pickle(os.path.join(V.D16, f"f16_{mk}{suf}.pkl")) for mk in mks if os.path.exists(os.path.join(V.D16, f"f16_{mk}{suf}.pkl"))]
    df = pd.concat([f for f in fr if len(f)], ignore_index=True)
    df["oos"] = df.t >= X.OOS
    return df


if __name__ == "__main__":
    df = load(V.MAIN)
    say("=== F16 Hakimi – vyhodnocení", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
    rows = []
    for v, g in df.groupby("var"):
        a, b = EV.st(g.R[~g.oos]), EV.st(g.R[g.oos])
        rows.append(dict(var=v, n_dev=a["n"], exp_dev=a["exp"], pf_dev=a["pf"], n_oos=b["n"], exp_oos=b["exp"], pf_oos=b["pf"]))
    tab = pd.DataFrame(rows).sort_values("exp_dev", ascending=False)
    say("\n--- 15 nejlepších variant na VÝVOJI (XAU+XAG, n_dev >= 40) a jejich OOS")
    top = tab[tab.n_dev >= 40]
    say(top.head(15).round(3).to_string(index=False))
    best = top.iloc[0]["var"]
    g = df[df["var"] == best]
    say("\n--- VYBRANÁ:", best)
    say("vývoj:", EV.fmt(EV.st(g.R[~g.oos])), "| OOS:", EV.fmt(EV.st(g.R[g.oos])))
    for mk, h in g.groupby("mk"):
        say(f"   {mk:11s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    say("náhoda vývoj", EV.fmt(EV.st(EV.random_base(g[~g.oos], reps=2))), "| OOS", EV.fmt(EV.st(EV.random_base(g[g.oos], reps=2))))
    ho = load(V.OTHER)
    gh = ho[ho["var"] == best]
    say("\n--- OSTATNÍ TRHY (stejná varianta, nebyly ve výběru)")
    for mk, h in gh.groupby("mk"):
        say(f"   {mk:11s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    if len(gh):
        say("   náhoda ostatní", EV.fmt(EV.st(EV.random_base(gh, reps=2))))
    say("\n--- průměr přes varianty podle parametru, XAU+XAG (vývoj | OOS)")
    kv = df["var"].str.split(" ", expand=True)
    for col in range(kv.shape[1]):
        for val, h in df.groupby(kv[col]):
            say(f"   {val:12s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    if os.path.exists(os.path.join(V.D16, "f16_XAUUSD_nc.pkl")):
        dn = load(V.MAIN, "_nc")
        gn = dn[dn["var"] == best]
        say("\n--- BEZ NÁKLADŮ: vybraná vývoj", EV.fmt(EV.st(gn.R[~gn.oos])), "| OOS", EV.fmt(EV.st(gn.R[gn.oos])),
            "| všechny varianty OOS", EV.fmt(EV.st(dn.R[dn.oos])))
    open(os.path.join(V.D16, "f16_souhrn.txt"), "w", encoding="utf-8").write("\n".join(OUT))
