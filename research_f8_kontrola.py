"""F8 kontrola vitezne varianty A3 (H4 zony): rozpad po trzich/letech/smeru, 2x naklady, zpozdeny vstup, graf ukazek.
-> research_data/f8/f8_kontrola.txt a f8_ukazky_A3.png"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import research_f8 as F
import research_f8_eval as EV

OUT = []
V = dict(piv=False, trend=True, sl20=False, tp="2", be=True)
K = 2.0


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def run(cost_mult=1.0, delay_h=0):
    rows, ex = [], []
    for mk in F.MARKETS:
        H = F.load(mk)
        H["spr"] = H["spr"] * cost_mult
        T = F.tfs(H)
        Z = F.find_zones(T["H4"], K)
        if delay_h:
            for z in Z:
                pass
        F.touch_info(H, T["H4"], Z)
        if delay_h:  # vstup az o delay_h hodin pozdeji: dotek se hleda od aktivace + delay
            for z in Z:
                if z["fi"] >= 0 and z["fi"] < T["H4"]["en"][z["act"]] + 1 + delay_h:
                    z["fi"] = -1
        tr = F.one_per_dir(F.zone_trades(H, T["H4"], Z, Z, V, "H4"))
        rows += tr
        if mk in ("EURUSD", "XAUUSD", "GBPJPY") and cost_mult == 1.0 and not delay_h:
            ex.append((H, T, Z, tr))
    return pd.DataFrame(rows), ex


def main():
    df, ex = run()
    df["oos"] = df.t >= F.OOS
    df["yr"] = pd.to_datetime(df.t, unit="s").dt.year
    p("A3 H4 vybraná varianta:", V, "k", K)
    p("celkem", EV.fmt(EV.stats(df.R)), "| DEV", EV.fmt(EV.stats(df[~df.oos].R)), "| OOS", EV.fmt(EV.stats(df[df.oos].R)))
    p("\nPo letech:")
    for y, g in df.groupby("yr"):
        p(f"  {y} {EV.fmt(EV.stats(g.R))}")
    p("\nPo trzích (celé období):")
    for mk, g in df.groupby("mk"):
        s = EV.stats(g.R)
        p(f"  {mk:12s} {EV.fmt(s)}")
    p("\nSměr:", {d: round(g.R.mean(), 3) for d, g in df.groupby("d")}, "| důvod výstupu:", df.why.value_counts().to_dict())
    p("Obchodů za rok (všechny trhy):", round(len(df) / df.yr.nunique(), 1))
    d2, _ = run(cost_mult=2.0)
    d2["oos"] = d2.t >= F.OOS
    p("\n2× náklady: DEV", EV.fmt(EV.stats(d2[~d2.oos].R)), "| OOS", EV.fmt(EV.stats(d2[d2.oos].R)))
    d3, _ = run(delay_h=4)
    d3["oos"] = d3.t >= F.OOS
    p("Dotek až 4 h po aktivaci (bez hned prvních doteků): DEV", EV.fmt(EV.stats(d3[~d3.oos].R)), "| OOS", EV.fmt(EV.stats(d3[d3.oos].R)))
    # graf ukazek
    fig, axs = plt.subplots(3, 2, figsize=(16, 13))
    k = 0
    for H, T, Z, tr in ex:
        X = T["H4"]
        tro = [x for x in tr if x["t"] >= F.OOS][:2]
        for x in tro:
            ax = axs.flat[k]
            k += 1
            i_h4 = int(np.searchsorted(X["en"], x["fi"]))
            a, b = max(0, i_h4 - 60), min(len(X["c"]), i_h4 + 40)
            for i in range(a, b):
                col = "#26a69a" if X["c"][i] >= X["o"][i] else "#ef5350"
                ax.plot([i, i], [X["l"][i], X["h"][i]], color=col, lw=0.8)
                ax.add_patch(plt.Rectangle((i - 0.35, min(X["o"][i], X["c"][i])), 0.7, abs(X["c"][i] - X["o"][i]) + 1e-12, color=col))
            z = min((z for z in Z if z["fi"] == x["fi"]), key=lambda z: 0, default=None)
            if z:
                ax.add_patch(plt.Rectangle((z["b0"] - 0.5, min(z["prox"], z["dist"])), i_h4 - z["b0"] + 8, abs(z["prox"] - z["dist"]),
                                           color="#2962ff" if z["d"] == 1 else "#ff6d00", alpha=0.25))
                ax.axvline(z["act"], color="gray", ls=":", lw=0.8)
            ax.axvline(i_h4, color="k", lw=0.6)
            ax.set_title(f"{H['mk']} {pd.to_datetime(x['t'], unit='s'):%Y-%m-%d %H:%M} {'long' if x['d'] == 1 else 'short'} R={x['R']:+.2f}")
            if k >= 6:
                break
        if k >= 6:
            break
    plt.tight_layout()
    plt.savefig(os.path.join(F.D8, "f8_ukazky_A3.png"), dpi=80)
    open(os.path.join(F.D8, "f8_kontrola.txt"), "w", encoding="utf-8").write("\n".join(OUT))


main()
