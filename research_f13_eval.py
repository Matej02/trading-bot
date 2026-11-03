"""
F13 - vyhodnoceni Veselovskeho: vyber varianty jen na vyvoji, OOS, nahoda, bez nakladu, vrstvy, grafy ukazek.
Spusteni: py research_f13_eval.py -> research_data/f13/f13_souhrn.txt
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
import research_f13_ves as V

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def load(suf=""):
    fr = [pd.read_pickle(os.path.join(V.D13, f"f13_{mk}{suf}.pkl")) for mk in V.MARKETS
          if os.path.exists(os.path.join(V.D13, f"f13_{mk}{suf}.pkl"))]
    df = pd.concat([f for f in fr if len(f)], ignore_index=True)
    df["oos"] = df.t >= X.OOS
    return df


def chart(mk, var, path, n=9):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    P = V.prep(mk)
    M, T = P["M"], P["T"]
    tr = [r for r in V.run_market(mk, var, info=True) if r["t"] >= X.OOS][:n]
    if not tr:
        return 0
    M5 = T["M5"]
    fig, axs = plt.subplots(3, 3, figsize=(22, 15))
    for ax, x in zip(axs.flat, tr):
        a = int(np.searchsorted(M5["st"], x["i_sw"])) - 60
        e = int(np.searchsorted(M5["st"], x["ex"])) + 12
        a, e = max(a, 0), min(e, len(M5["c"]) - 1)
        for i in range(a, e):
            col = "#2962ff" if M5["c"][i] >= M5["o"][i] else "#222222"
            ax.plot([i, i], [M5["l"][i], M5["h"][i]], color=col, lw=0.6)
            ax.add_patch(plt.Rectangle((i - 0.3, min(M5["o"][i], M5["c"][i])), 0.6, abs(M5["c"][i] - M5["o"][i]) + 1e-12, color=col))
        pos = lambda i1: int(np.searchsorted(M5["st"], i1, side="right")) - 1
        day = int(P["czday"][x["ic"]])
        asia = P["asia"].get(day)
        lines = [(x["E_"], "b", "vstup"), (x["SL_"], "r", "SL"), (x["TP_"], "g", "TP2 cíl biasu"), (x["sv"], "orange", "sweep"),
                 (P["nydo"][x["i_sw"]], "gray", "NY DO")]
        if np.isfinite(x["TP1_"]):
            lines.append((x["TP1_"], "limegreen", "TP1 Asie"))
        if asia:
            ax.axhspan(asia[1], asia[0], color="#b3c7ff", alpha=0.15)
        for y, col, lab in lines:
            ax.axhline(y, color=col, lw=0.8, ls="--" if lab == "NY DO" else "-")
            ax.text(a, y, lab, fontsize=7, color=col)
        for i1, col in ((x["i_sw"], "orange"), (x["ic"], "m"), (x["fi"], "b"), (x["ex"], "k")):
            ax.axvline(pos(i1), color=col, lw=0.7)
        ax.set_title(f"{mk} {pd.to_datetime(x['t'], unit='s', utc=True).tz_convert('Europe/Prague'):%Y-%m-%d %H:%M} "
                     f"{'LONG' if x['d'] == 1 else 'SHORT'} R={x['R']:+.2f} (cíl {x['Rt']:.1f} R)", fontsize=10)
    plt.suptitle("F13 Veselovský – ukázky OOS, 5m svíčky. Modrý pás = Asie, oranžová = sweep, fialová = MSS, modrá = vstup, "
                 f"černá = výstup.  {X.vn(var)}", fontsize=11)
    plt.tight_layout()
    plt.savefig(path, dpi=65)
    plt.close()
    return len(tr)


if __name__ == "__main__":
    df = load()
    say("=== F13 Veselovský – vyhodnocení", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
    say("obchodů celkem", len(df), "| trhy", df.groupby("mk").size().to_dict())
    rows = []
    for v, g in df.groupby("var"):
        a, b = EV.st(g.R[~g.oos]), EV.st(g.R[g.oos])
        rows.append(dict(var=v, n_dev=a["n"], exp_dev=a["exp"], pf_dev=a["pf"], n_oos=b["n"], exp_oos=b["exp"], pf_oos=b["pf"]))
    tab = pd.DataFrame(rows).sort_values("exp_dev", ascending=False)
    say("\n--- varianty podle VÝVOJE (n_dev >= 40) a jejich OOS")
    top = tab[tab.n_dev >= 40]
    say(top.round(3).to_string(index=False))
    best = top.iloc[0]["var"] if len(top) else tab.iloc[0]["var"]
    g = df[df["var"] == best]
    say("\n--- VYBRANÁ varianta:", best)
    say("vývoj:", EV.fmt(EV.st(g.R[~g.oos])))
    say("OOS:  ", EV.fmt(EV.st(g.R[g.oos])))
    for mk, h in g.groupby("mk"):
        say(f"   {mk:11s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    say("náhodné vstupy OOS:", EV.fmt(EV.st(EV.random_base(g[g.oos]))))
    say("náhodné vstupy vývoj:", EV.fmt(EV.st(EV.random_base(g[~g.oos]))))
    say("\n--- průměr přes varianty podle parametru (vývoj | OOS)")
    kv = df["var"].str.split(" ", expand=True)
    for col in range(kv.shape[1]):
        for val, h in df.groupby(kv[col]):
            say(f"   {val:12s} vývoj {EV.fmt(EV.st(h.R[~h.oos]))} | OOS {EV.fmt(EV.st(h.R[h.oos]))}")
    say("\n--- všechny varianty: vývoj", EV.fmt(EV.st(df.R[~df.oos])), "| OOS", EV.fmt(EV.st(df.R[df.oos])))
    if os.path.exists(os.path.join(V.D13, "f13_EURUSD_nc.pkl")):
        dn = load("_nc")
        gn = dn[dn["var"] == best]
        say("\n--- BEZ NÁKLADŮ: vybraná vývoj", EV.fmt(EV.st(gn.R[~gn.oos])), "| OOS", EV.fmt(EV.st(gn.R[gn.oos])))
        say("    všechny varianty bez nákladů: vývoj", EV.fmt(EV.st(dn.R[~dn.oos])), "| OOS", EV.fmt(EV.st(dn.R[dn.oos])))
        say("    náhoda bez nákladů OOS:", EV.fmt(EV.st(EV.random_base(gn[gn.oos]))))
    # vrstvy: vybrana varianta bez biasu / bez NY DO / s liq misto zony
    var = dict(kv_.split("=") for kv_ in best.split(" "))
    say("\n--- vrstvy (vybraná varianta, všechny trhy, s náklady)")
    for nm, ch in (("vybraná", {}), ("bez daily biasu", dict(bias=0)), ("bez NY DO", dict(nydo=0)),
                   ("úroveň = jen sweep LQ", dict(lvl="liq")), ("bez biasu i NY DO", dict(bias=0, nydo=0))):
        vv = {**var, **ch}
        rr = pd.DataFrame([r for mk in V.MARKETS for r in V.run_market(mk, vv)])
        if not len(rr):
            say(f"   {nm:24s} n 0")
            continue
        rr["oos"] = rr.t >= X.OOS
        say(f"   {nm:24s} vývoj {EV.fmt(EV.st(rr.R[~rr.oos]))} | OOS {EV.fmt(EV.st(rr.R[rr.oos]))}")
    open(os.path.join(V.D13, "f13_souhrn.txt"), "w", encoding="utf-8").write("\n".join(OUT))
    mk_most = g[g.oos].mk.value_counts().index[0] if g.oos.any() else "EURUSD"
    say("grafy:", chart(mk_most, var, os.path.join(V.D13, f"f13_ukazky_{mk_most}.png")))
    if mk_most != "EURUSD":
        say("grafy EURUSD:", chart("EURUSD", var, os.path.join(V.D13, "f13_ukazky_EURUSD.png")))
