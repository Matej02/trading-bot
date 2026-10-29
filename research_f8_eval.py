"""F8 vyhodnoceni: vyber varianty jen na vyvoji (do 2019), OOS od 2020 jednou, nahodne vstupy, kvartaly. -> research_data/f8/f8_vyhodnoceni.txt"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f8 as F

OUT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def stats(r):
    r = np.asarray(r, float)
    if len(r) == 0:
        return dict(n=0, exp=np.nan, pf=np.nan, win=np.nan, t=np.nan)
    g, b = r[r > 0].sum(), -r[r < 0].sum()
    return dict(n=len(r), exp=r.mean(), pf=g / b if b > 0 else np.inf, win=(r > 0).mean() * 100,
                t=r.mean() / (r.std(ddof=1) / np.sqrt(len(r))) if len(r) > 1 and r.std() > 0 else np.nan)


def fmt(s):
    return f"n={s['n']:4d} exp={s['exp']:+.3f}R PF={s['pf']:.2f} win={s['win']:.0f}% t={s['t']:+.2f}" if s["n"] else "n=0"


def quarters(df):
    q = pd.to_datetime(df.t, unit="s").dt.to_period("Q")
    s = df.groupby(q).R.sum()
    return (s > 0).mean() * 100, len(s)


def random_baseline(tr, reps=5, seed=1):
    """Pro kazdy obchod: nahodna H1 svicka ve stejnem roce a trhu, stejny smer, SL = stejny nasobek ATR D1, stejne R cile a doba."""
    rng = np.random.default_rng(seed)
    res = []
    for mk, g in tr.groupby("mk"):
        H = F.load(mk)
        D = F.resample(H, H["day"])
        # ATR D1 platny pro kazdou H1 svicku = ATR posledni uzavrene D1
        dix = np.searchsorted(D["en"], np.arange(len(H["c"])), side="left") - 1
        atr = np.where(dix >= 0, D["a"][np.clip(dix, 0, None)], np.nan)
        yr = pd.to_datetime(H["t"], unit="s").year.to_numpy()
        for x in g.itertuples():
            pool = np.flatnonzero((yr == pd.Timestamp(x.t, unit="s").year) & np.isfinite(atr))
            pool = pool[pool < len(H["c"]) - 2]
            for _ in range(reps):
                i = int(rng.choice(pool))
                E = H["o"][i]
                risk = x.risk_atr * atr[i]
                if not risk > 0:
                    continue
                SL = E - x.d * risk
                TP = E + x.d * x.Rt * risk
                sw = H["swl"] if x.d == 1 else H["sws"]
                r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], i, i, 1, x.d, E, SL, TP, 1.0,
                                np.nan, np.nan, np.full(1, np.nan), 0, min(i + x.hold, len(H["c"]) - 1), np.nan,
                                H["hend"], 0, 0.0, H["cum_sw"], sw)
                if r[0]:
                    res.append(r[1])
    return np.array(res)


def eval_a():
    df = pd.read_pickle(os.path.join(F.D8, "f8_A_obchody.pkl"))
    df["oos"] = df.t >= F.OOS
    df["grp"] = np.where(df.mk.isin(F.FOREX), "FOREX", "OSTATNI")
    p("=" * 100)
    p("TEST A – S/D zóny FM (vývoj do 2019, OOS od 2020)")
    for test, g in df.groupby("test"):
        p("-" * 100)
        p(test)
        rows = []
        for var, gv in g.groupby("var"):
            dv, ov = gv[~gv.oos], gv[gv.oos]
            sd, so = stats(dv.R), stats(ov.R)
            rows.append((var, sd, so))
        rows.sort(key=lambda x: -x[1]["exp"] if x[1]["n"] >= 100 else 1e9)
        p("  TOP 8 podle vývoje (n_dev >= 100):")
        for var, sd, so in rows[:8]:
            p(f"   {var:38s} DEV {fmt(sd)} | OOS {fmt(so)}")
        best = [r for r in rows if r[1]["n"] >= 100]
        if not best:
            p("  žádná varianta nemá n_dev >= 100")
            continue
        var, sd, so = best[0]
        sel = g[g["var"] == var]
        o = sel[sel.oos]
        qp, nq = quarters(o) if len(o) else (np.nan, 0)
        p(f"  VYBRANÁ: {var}")
        p(f"   DEV {fmt(sd)}")
        p(f"   OOS {fmt(so)} | ziskové kvartály {qp:.0f}% z {nq}")
        for grp, gg in o.groupby("grp"):
            p(f"   OOS {grp:8s} {fmt(stats(gg.R))}")
        if len(o) >= 20:
            rb = random_baseline(o)
            p(f"   náhodné vstupy (stejný směr/SL v ATR/R/doba, 5×): {fmt(stats(rb))}")
            ok = (so["n"] >= 100 and so["exp"] >= 0.15 and so["pf"] >= 1.3 and qp >= 60 and so["exp"] - rb.mean() >= 0.1)
            p(f"   PRAHY F7 (n>=100, exp>=0,15, PF>=1,3, kvartály>=60 %, o 0,1R nad náhodou): {'PROŠLO' if ok else 'neprošlo'}")
        # plato: OOS vsech variant s n_dev>=100
        oo = [r[2]["exp"] for r in best if r[2]["n"] >= 30]
        p(f"   plato: OOS exp všech variant s n_dev>=100 (n_oos>=30): medián {np.median(oo):+.3f}R, kladných {np.mean(np.array(oo) > 0) * 100:.0f}% z {len(oo)}")


def eval_b():
    df = pd.read_pickle(os.path.join(F.D8, "f8_B_obchody.pkl"))
    df["oos"] = df.t >= F.OOS
    p("=" * 100)
    p("TEST B – Daily bias (V = Veselovský, M = Můčka); obchod: open dne → TP cíl (PDH/PDL), SL opačný PD extrém, konec dne")
    allhit = pd.concat([df.drop_duplicates(["mk", "t"]).hit_up, df.drop_duplicates(["mk", "t"]).hit_dn]).mean() * 100
    p(f"  nepodmíněná míra zásahu PDH nebo PDL v daný den: {allhit:.1f}%")
    for (rule, side), g in df.groupby(["rule", "side"]):
        for per, gg in (("DEV", g[~g.oos]), ("OOS", g[g.oos])):
            p(f"  {rule} {side:4s} {per}: zásah cíle {gg.hit.mean() * 100:5.1f}%  obchod {fmt(stats(gg.R))}  (průměrné R cíle {gg.Rt.median():.2f})")


if __name__ == "__main__":
    if os.path.exists(os.path.join(F.D8, "f8_B_obchody.pkl")):
        eval_b()
    if os.path.exists(os.path.join(F.D8, "f8_A_obchody.pkl")):
        eval_a()
    open(os.path.join(F.D8, "f8_vyhodnoceni.txt"), "w", encoding="utf-8").write("\n".join(OUT))
