"""F11 vyhodnoceni jedne strategie: vsechny varianty DEV/OOS, vyber na vyvoji, po trzich, po letech, nahodne vstupy."""
import os, sys
import numpy as np, pandas as pd
os.chdir(r"D:\Trading bot"); sys.path.insert(0, r"D:\Trading bot")
import research_f10 as X
import research_f10_eval as E
OUT = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s); OUT.append(s)
def main(name):
    df = pd.read_pickle(os.path.join("research_data", "f11", f"f11_{name}.pkl"))
    df["oos"] = df.t >= X.OOS
    df["yr"] = pd.to_datetime(df.t, unit="s").dt.year
    p(f"=== {name}: {len(df)} obchodů, {df.mk.nunique()} trhů ===")
    rows = []
    for var, g in df.groupby("var"):
        sd, so = E.st(g[~g.oos].R), E.st(g[g.oos].R)
        rows.append((var, sd, so)); p(f"  {var:28s} DEV {E.fm(sd)} | OOS {E.fm(so)}")
    cand = [r for r in rows if r[1]["n"] >= 50] or rows
    var, sd, so = max(cand, key=lambda r: r[1]["exp"] if np.isfinite(r[1]["exp"]) else -9)
    g = df[df["var"] == var]
    p(f"  → vybraná na vývoji: {var}")
    for mk, gg in g.groupby("mk"):
        p(f"     {mk:11s} DEV {E.fm(E.st(gg[~gg.oos].R))} | OOS {E.fm(E.st(gg[gg.oos].R))}")
    p("     po letech: " + " ".join(f"{y}:{gg.R.mean():+.2f}({len(gg)})" for y, gg in g.groupby("yr")))
    p(f"     win {100*(g.R>0).mean():.0f} %, průměrné R cíle {g.Rt.median():.2f}, důvody výstupu {g.why.value_counts().to_dict()}")
    o = g[g.oos]
    if len(o) >= 20:
        rb = E.random_m1(o)
        p(f"     náhodné vstupy OOS: {E.fm(E.st(rb))}")
    open(os.path.join("research_data", "f11", f"f11_{name}_vyhodnoceni.txt"), "w", encoding="utf-8").write("\n".join(OUT))
if __name__ == "__main__":
    main(sys.argv[1])
