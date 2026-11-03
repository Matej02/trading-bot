"""
F12 - vyhodnoceni: varianta se vybira jen na vyvoji (do 2021), pak OOS 2022-2026, nahodne vstupy, bez nakladu, grafy.
Spusteni: py research_f12_eval.py  -> research_data/f12/f12_souhrn.txt (+ f12_ukazky_<trh>.png)
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
sys.stdout.reconfigure(encoding="utf-8")
import research_f10 as X
import research_f12 as F

D12 = F.D12
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def st(R):
    R = np.asarray(R, float)
    if len(R) == 0:
        return dict(n=0, exp=np.nan, pf=np.nan, win=np.nan)
    g, b = R[R > 0].sum(), -R[R < 0].sum()
    return dict(n=len(R), exp=R.mean(), pf=g / b if b > 0 else np.inf, win=(R > 0).mean())


def fmt(s):
    return f"n {s['n']:4d}  exp {s['exp']:+.3f} R  PF {s['pf']:.2f}  win {s['win']:.0%}" if s["n"] else "n    0"


def load(suf=""):
    fr = [pd.read_pickle(os.path.join(D12, f"f12_{mk}{suf}.pkl")) for mk in F.MARKETS
          if os.path.exists(os.path.join(D12, f"f12_{mk}{suf}.pkl"))]
    df = pd.concat([f for f in fr if len(f)], ignore_index=True)
    df["oos"] = df.t >= X.OOS
    return df


def random_base(df, reps=3, seed=1):
    """Stejny trh, smer, prazsky cas, vzdalenost SL a TP, vstup trhem v nahodny den stejneho obdobi; konec 22:00."""
    rng = np.random.default_rng(seed)
    R = []
    for mk, g in df.groupby("mk"):
        M = X.load1(mk)
        cz, czday = F.prague_hours(M["t"])
        days = np.unique(czday)
        oos_day = X.OOS // 86400
        for _, r in g.iterrows():
            pool = days[(days >= oos_day)] if r.oos else days[(days < oos_day)]
            for _ in range(reps):
                dd = rng.choice(pool)
                s0, s1 = np.searchsorted(czday, dd), np.searchsorted(czday, dd, side="right")
                if s1 - s0 < 600:
                    continue
                i = s0 + int(np.searchsorted(cz[s0:s1], r.cz))
                if i >= s1 - 1:
                    continue
                E = M["o"][i]
                d = int(r.d)
                e = i
                while e < s1 - 1 and cz[e] < 22.0:
                    e += 1
                s = X.sim(M, d, E, E - d * r.sl_dist, E + d * r.tp_dist, i, i, 1, e)
                if s:
                    R.append(s["R"])
    return np.array(R)


def chart(mk, var, path, n=9):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    P = F.prep(mk)
    M, T = P["M"], P["T"]
    tr = [r for r in F.run_market(mk, var, info=True) if r["t"] >= X.OOS][:n]
    if not tr:
        return 0
    M5 = T["M5"]
    Z = P["S"][var["k"]]["Z"]
    B = P["S"][var["k"]]["B"]
    fig, axs = plt.subplots(3, 3, figsize=(22, 15))
    for ax, x in zip(axs.flat, tr):
        a = int(np.searchsorted(M5["st"], x["si"])) - 50
        e = int(np.searchsorted(M5["st"], x["ex"])) + 15
        a, e = max(a, 0), min(e, len(M5["c"]) - 1)
        for i in range(a, e):
            col = "#2962ff" if M5["c"][i] >= M5["o"][i] else "#222222"
            ax.plot([i, i], [M5["l"][i], M5["h"][i]], color=col, lw=0.6)
            ax.add_patch(plt.Rectangle((i - 0.3, min(M5["o"][i], M5["c"][i])), 0.6, abs(M5["c"][i] - M5["o"][i]) + 1e-12, color=col))
        pos = lambda i1: int(np.searchsorted(M5["st"], i1, side="right")) - 1
        d = x["d"]
        for z in Z:
            if z[0] == d and z[3] <= x["si"] <= z[4] and z[1] - (z[2] - z[1]) <= x["sv"] <= z[2] + (z[2] - z[1]):
                ax.add_patch(plt.Rectangle((a, z[1]), e - a, z[2] - z[1], color="#26a69a" if d == 1 else "#ef5350", alpha=0.2))
        for b in B:
            if b[0] == d and b[2] <= x["si"] <= b[3]:
                ax.axhline(b[1], color="gray", ls="-.", lw=0.8)
        for y, col, lab in ((x["E_"], "b", "vstup"), (x["SL_"], "r", "SL"), (x["TP_"], "g", "TP"), (x["sv"], "orange", "sweep")):
            ax.axhline(y, color=col, lw=0.8)
            ax.text(a, y, lab, fontsize=7, color=col)
        for i1, col in ((x["si"], "orange"), (x["ic"], "m"), (x["fi"], "b"), (x["ex"], "k")):
            ax.axvline(pos(i1), color=col, lw=0.7)
        ax.set_title(f"{mk} {pd.to_datetime(x['t'], unit='s', utc=True).tz_convert('Europe/Prague'):%Y-%m-%d %H:%M} "
                     f"{'LONG' if d == 1 else 'SHORT'} R={x['R']:+.2f} (cíl {x['Rt']:.1f} R)", fontsize=10)
    plt.suptitle(f"F12 Můčka – ukázky OOS, 5m svíčky. Zóna = podbarvení, balanční level = šedá čerchovaná, "
                 f"oranžová = sweep, fialová = MSS, modrá = vstup, černá = výstup.  {X.vn(var)}", fontsize=11)
    plt.tight_layout()
    plt.savefig(path, dpi=65)
    plt.close()
    return len(tr)


if __name__ == "__main__":
    df = load()
    say("=== F12 Můčka podle doplňujících pravidel – vyhodnocení", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
    say("obchodů celkem", len(df), "| trhy", df.groupby("mk").size().to_dict())
    rows = []
    for v, g in df.groupby("var"):
        a, b = st(g.R[~g.oos]), st(g.R[g.oos])
        rows.append(dict(var=v, n_dev=a["n"], exp_dev=a["exp"], pf_dev=a["pf"], n_oos=b["n"], exp_oos=b["exp"], pf_oos=b["pf"],
                         win_oos=b["win"]))
    tab = pd.DataFrame(rows).sort_values("exp_dev", ascending=False)
    say("\n--- 15 nejlepších variant na VÝVOJI (n_dev >= 40) a jejich OOS")
    top = tab[tab.n_dev >= 40].head(15)
    say(top.round(3).to_string(index=False))
    best = top.iloc[0]["var"] if len(top) else tab.iloc[0]["var"]
    g = df[df["var"] == best]
    say("\n--- VYBRANÁ varianta:", best)
    say("vývoj:", fmt(st(g.R[~g.oos])))
    say("OOS:  ", fmt(st(g.R[g.oos])))
    for mk, h in g.groupby("mk"):
        say(f"   {mk:11s} vývoj {fmt(st(h.R[~h.oos]))} | OOS {fmt(st(h.R[h.oos]))}")
    rb = random_base(g[g.oos])
    say("náhodné vstupy OOS (stejné SL/TP, čas, směr):", fmt(st(rb)))
    rbd = random_base(g[~g.oos])
    say("náhodné vstupy vývoj:", fmt(st(rbd)))
    say("\n--- průměr přes všechny varianty podle parametru (vývoj | OOS)")
    kv = df["var"].str.split(" ", expand=True)
    for col in range(kv.shape[1]):
        key = kv[col].str.split("=").str[0].iloc[0]
        for val, h in df.groupby(kv[col]):
            say(f"   {val:12s} vývoj {fmt(st(h.R[~h.oos]))} | OOS {fmt(st(h.R[h.oos]))}")
    say("\n--- všechny varianty dohromady: vývoj", fmt(st(df.R[~df.oos])), "| OOS", fmt(st(df.R[df.oos])))
    if os.path.exists(os.path.join(D12, "f12_EURUSD_nc.pkl")):
        dn = load("_nc")
        gn = dn[dn["var"] == best]
        say("\n--- BEZ NÁKLADŮ: vybraná varianta vývoj", fmt(st(gn.R[~gn.oos])), "| OOS", fmt(st(gn.R[gn.oos])))
        say("    všechny varianty bez nákladů: vývoj", fmt(st(dn.R[~dn.oos])), "| OOS", fmt(st(dn.R[dn.oos])))
        say("    náhodné bez nákladů OOS:", fmt(st(random_base(gn[gn.oos]))))
    open(os.path.join(D12, "f12_souhrn.txt"), "w", encoding="utf-8").write("\n".join(OUT))
    var = dict(kv.split("=") for kv in best.split(" "))
    var["k"] = float(var["k"])
    mk_most = g[g.oos].mk.value_counts().index[0] if g.oos.any() else "EURUSD"
    say("grafy ukázek:", chart(mk_most, var, os.path.join(D12, f"f12_ukazky_{mk_most}.png")))
