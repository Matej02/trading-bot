"""
F14 - vyhodnoceni Patka: vyber varianty jen na vyvoji (NAS100, GBPUSD, XAUUSD), OOS, nahoda, bez nakladu, vrstvy,
trhy mimo test (SPX500, US30, DAX), grafy ukazek. Spusteni: py research_f14_eval.py -> research_data/f14/f14_souhrn.txt
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
import research_f14_pat as V

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def load(mks, suf=""):
    fr = [pd.read_pickle(os.path.join(V.D14, f"f14_{mk}{suf}.pkl")) for mk in mks
          if os.path.exists(os.path.join(V.D14, f"f14_{mk}{suf}.pkl"))]
    df = pd.concat([f for f in fr if len(f)], ignore_index=True)
    df["oos"] = df.t >= X.OOS
    return df


def parse(v):
    d = dict(kv.split("=") for kv in v.split(" "))
    for k in ("rej", "lhhl", "d1"):
        if k in d:
            d[k] = int(d[k])
    return d


def chart(mk, var, path, n=9):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    P = V.prep(mk)
    M, T = P["M"], P["T"]
    tr = [r for r in V.run_market(mk, var, info=True) if r["t"] >= X.OOS][:n]
    if not tr:
        return 0
    Xb = T["M5"]
    fig, axs = plt.subplots(3, 3, figsize=(22, 15))
    for ax, x in zip(axs.flat, tr):
        a = int(np.searchsorted(Xb["st"], x["ij"])) - 40
        e = int(np.searchsorted(Xb["st"], x["ex"])) + 12
        a, e = max(a, 0), min(e, len(Xb["c"]) - 1)
        for i in range(a, e):
            col = "#26a69a" if Xb["c"][i] >= Xb["o"][i] else "#ef5350"
            ax.plot([i, i], [Xb["l"][i], Xb["h"][i]], color=col, lw=0.6)
            ax.add_patch(plt.Rectangle((i - 0.3, min(Xb["o"][i], Xb["c"][i])), 0.6, abs(Xb["c"][i] - Xb["o"][i]) + 1e-12, color=col))
        k4 = int(P["c4"][x["fi"]])
        j1 = int(np.searchsorted(P["pj4"], k4, side="right"))
        j0 = int(np.searchsorted(P["pj4"], k4 - V.WIN4))
        lo, hi = Xb["l"][a:e].min(), Xb["h"][a:e].max()
        for pv in P["pp4"][j0:j1]:
            if lo - (hi - lo) <= pv <= hi + (hi - lo):
                ax.axhline(pv, color="gray", lw=0.5, ls=":")
        pos = lambda i1: int(np.searchsorted(Xb["st"], i1, side="right")) - 1
        for y, col, lab in ((x["E_"], "b", "vstup"), (x["SL_"], "r", "SL"), (x["TP_"], "g", "TP")):
            ax.axhline(y, color=col, lw=0.8)
            ax.text(a, y, lab, fontsize=7, color=col)
        for i1, col in ((x["fi"], "b"), (x["ex"], "k")):
            ax.axvline(pos(i1), color=col, lw=0.7)
        ax.set_ylim(lo - 0.1 * (hi - lo), hi + 0.1 * (hi - lo))
        ax.set_title(f"{mk} {pd.to_datetime(x['t'], unit='s', utc=True).tz_convert('Europe/Prague'):%Y-%m-%d %H:%M} "
                     f"{'LONG' if x['d'] == 1 else 'SHORT'} R={x['R']:+.2f} (cíl {x['Rt']:.1f} R)", fontsize=10)
    plt.suptitle(f"F14 Pátek – ukázky OOS, 5m svíčky, šedé tečkované = H4 pivoty (zóny = 2+ blízko sebe).  {X.vn(var)}", fontsize=11)
    plt.tight_layout()
    plt.savefig(path, dpi=65)
    plt.close()
    return len(tr)


if __name__ == "__main__":
    df = load(V.MARKETS)
    say("=== F14 Pátek – vyhodnocení", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
    say("obchodů", len(df), df.groupby("mk").size().to_dict())
    rows = []
    for v, g in df.groupby("var"):
        a, b = EV.st(g.R[~g.oos]), EV.st(g.R[g.oos])
        rows.append(dict(var=v, n_dev=a["n"], exp_dev=a["exp"], pf_dev=a["pf"], n_oos=b["n"], exp_oos=b["exp"], pf_oos=b["pf"]))
    tab = pd.DataFrame(rows).sort_values("exp_dev", ascending=False)
    say("\n--- varianty podle VÝVOJE a jejich OOS")
    say(tab.round(3).to_string(index=False))
    top = tab[tab.n_dev >= 40]
    best = top.iloc[0]["var"]
    g = df[df["var"] == best]
    say("\n--- VYBRANÁ:", best)
    say("vývoj:", EV.fmt(EV.st(g.R[~g.oos])), "| OOS:", EV.fmt(EV.st(g.R[g.oos])))
    for mk, h in g.groupby("mk"):
        say(f"   {mk:11s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    say("náhoda vývoj", EV.fmt(EV.st(EV.random_base(g[~g.oos]))), "| OOS", EV.fmt(EV.st(EV.random_base(g[g.oos]))))
    ho = load(V.HELD_OUT)
    gh = ho[ho["var"] == best]
    say("\n--- TRHY MIMO TEST (stejná varianta)")
    for mk, h in gh.groupby("mk"):
        say(f"   {mk:11s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    say("   náhoda mimo test", EV.fmt(EV.st(EV.random_base(gh, reps=2))))
    say("\n--- průměr přes varianty podle parametru (vývoj | OOS)")
    kv = df["var"].str.split(" ", expand=True)
    for col in range(kv.shape[1]):
        for val, h in df.groupby(kv[col]):
            say(f"   {val:12s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    if os.path.exists(os.path.join(V.D14, "f14_NAS100mini_nc.pkl")):
        dn = load(V.MARKETS, "_nc")
        gn = dn[dn["var"] == best]
        say("\n--- BEZ NÁKLADŮ: vybraná vývoj", EV.fmt(EV.st(gn.R[~gn.oos])), "| OOS", EV.fmt(EV.st(gn.R[gn.oos])),
            "| všechny varianty OOS", EV.fmt(EV.st(dn.R[dn.oos])))
    var = parse(best)
    say("\n--- vrstvy (vybraná varianta, testové trhy)")
    for nm, ch in (("vybraná", {}), ("bez odmítnutí v H4 zóně", dict(rej=0)), ("bez LH/HL", dict(lhhl=0)), ("+ shoda D1", dict(d1=1))):
        vv = {**var, **ch}
        rr = pd.DataFrame([r for mk in V.MARKETS for r in V.run_market(mk, vv)])
        rr["oos"] = rr.t >= X.OOS
        say(f"   {nm:26s} vývoj {EV.fmt(EV.st(rr.R[~rr.oos]))} | OOS {EV.fmt(EV.st(rr.R[rr.oos]))}")
    open(os.path.join(V.D14, "f14_souhrn.txt"), "w", encoding="utf-8").write("\n".join(OUT))
    say("grafy:", chart("NAS100mini", var, os.path.join(V.D14, "f14_ukazky_NAS100mini.png")))
