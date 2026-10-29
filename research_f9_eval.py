"""F9 vyhodnoceni kombinaci: vyber 2010-17, validace 2018-21, holdout 2022+ (jednou), 1 obchod na trh a kombinaci,
nahodne vstupy, zpozdeny vstup. -> research_data/f9/f9_vyhodnoceni.txt, f9_vybrane.json"""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import research_f9 as G

OUT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def st(r):
    r = np.asarray(r, float)
    r = r[np.isfinite(r)]
    if len(r) < 2:
        return dict(n=len(r), exp=np.nan, t=np.nan, pf=np.nan, win=np.nan)
    g, b = r[r > 0].sum(), -r[r < 0].sum()
    return dict(n=len(r), exp=r.mean(), t=r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), pf=g / b if b > 0 else np.inf,
                win=(r > 0).mean() * 100)


def fm(s):
    return f"n={s['n']:5d} exp={s['exp']:+.3f}R t={s['t']:+.2f} PF={s['pf']:.2f} win={s['win']:.0f}%"


def nonoverlap(g, R):
    """1 otevreny obchod na trh: podle i, vstup az po vystupu predchoziho."""
    keep = np.zeros(len(g), bool)
    ex = g[f"ex{R}"].to_numpy()
    ii = g.i.to_numpy()
    mk = g.mk.to_numpy()
    last = {}
    for k in np.argsort(ii, kind="stable"):
        if ii[k] > last.get(mk[k], -1):
            keep[k] = True
            last[mk[k]] = ex[k]
    return g[keep]


def combos():
    subsets = [()] + [(a,) for a in G.FILT] + list(itertools.combinations(G.FILT, 2))
    for trig in G.TRIG:
        for sub in subsets:
            for R in G.RS:
                yield trig, sub, R


def name(trig, sub, R):
    return f"{trig} + {' + '.join(sub) if sub else '-'} | TP {R}R"


def main(base=""):
    df = pd.read_pickle(os.path.join(G.D9, f"f9_udalosti{base}.pkl")).sort_values(["mk", "i"]).reset_index(drop=True)
    df["per"] = np.where(df.t < G.SPLIT1, "dev", np.where(df.t < G.SPLIT2, "val", "hold"))
    p(f"Událostí celkem {len(df)}, trhů {df.mk.nunique()}")
    p("Spouštěče samotné (TP 2R, bez filtrů, s překryvem):")
    for trig, g in df.groupby("trig"):
        p(f"  {trig:12s} " + " | ".join(f"{per} {fm(st(g[g.per == per]['R2.0']))}" for per in ("dev", "val", "hold")))
    res = []
    by_trig = {t: g for t, g in df.groupby("trig")}
    for trig, sub, R in combos():
        g = by_trig[trig]
        m = np.ones(len(g), bool)
        for f in sub:
            m &= g[f].to_numpy()
        gg = nonoverlap(g[m], R)
        col = f"R{R}"
        sd = st(gg[gg.per == "dev"][col])
        sv = st(gg[gg.per == "val"][col])
        res.append(dict(trig=trig, sub=sub, R=R, dev=sd, val=sv))
    p(f"\nKombinací: {len(res)}")
    dev_ok = [r for r in res if r["dev"]["n"] >= 100 and r["dev"]["exp"] > 0 and r["dev"]["t"] > 2]
    p(f"Prošlo výběrem 2010–17 (n>=100, exp>0, t>2): {len(dev_ok)} (při náhodě by se čekalo ~2,3 % = {0.023 * len(res):.0f})")
    both = [r for r in dev_ok if r["val"]["n"] >= 50 and r["val"]["exp"] >= 0.10 and r["val"]["t"] > 2]
    p(f"Prošlo i validací 2018–21 (n>=50, exp>=0,10, t>2): {len(both)}")
    p("\nTOP 25 podle vývoje (s validací):")
    for r in sorted(dev_ok, key=lambda r: -r["dev"]["t"])[:25]:
        p(f"  {name(r['trig'], r['sub'], r['R']):55s} DEV {fm(r['dev'])} | VAL {fm(r['val'])}")
    p("\n=== HOLDOUT 2022–2026 (jednou, jen pro kombinace, které prošly vývojem i validací) ===")
    sel = []
    for r in sorted(both, key=lambda r: -(r["dev"]["t"] + r["val"]["t"])):
        g = by_trig[r["trig"]]
        m = np.ones(len(g), bool)
        for f in r["sub"]:
            m &= g[f].to_numpy()
        gg = nonoverlap(g[m], r["R"])
        sh = st(gg[gg.per == "hold"][f"R{r['R']}"])
        p(f"  {name(r['trig'], r['sub'], r['R']):55s} DEV {fm(r['dev'])} | VAL {fm(r['val'])} | HOLD {fm(sh)}")
        sel.append(dict(trig=r["trig"], filters=list(r["sub"]), R=r["R"], dev=r["dev"], val=r["val"], hold=sh))
    # zpozdeny vstup
    fd = os.path.join(G.D9, f"f9_udalosti{base}_d2.pkl")
    if os.path.exists(fd) and sel:
        d2 = pd.read_pickle(fd).sort_values(["mk", "i"]).reset_index(drop=True)
        d2["per"] = np.where(d2.t < G.SPLIT1, "dev", np.where(d2.t < G.SPLIT2, "val", "hold"))
        p("\nKontrola: vstup o 1 svíčku později (výhoda nesmí zmizet):")
        for s in sel:
            g = d2[d2.trig == s["trig"]]
            m = np.ones(len(g), bool)
            for f in s["filters"]:
                m &= g[f].to_numpy()
            gg = nonoverlap(g[m], s["R"])
            s["delay"] = {per: st(gg[gg.per == per][f"R{s['R']}"]) for per in ("dev", "val", "hold")}
            p(f"  {name(s['trig'], tuple(s['filters']), s['R']):55s} " + " | ".join(f"{k} {fm(v)}" for k, v in s["delay"].items()))
    json.dump(sel, open(os.path.join(G.D9, f"f9_vybrane{base}.json"), "w", encoding="utf-8"), indent=1, default=float)
    open(os.path.join(G.D9, f"f9_vyhodnoceni{base}.txt"), "w", encoding="utf-8").write("\n".join(OUT))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
