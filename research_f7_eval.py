"""
F7 - vyhodnoceni obchodu z research_f7.py podle postupu dokumentu (2026-10-28).

Pro kazdou strategii a skupinu trhu (krypto M1, forex/komodity M15, forex/komodity M5):
  1) prehled vsech variant: vyvoj (do 2025-02) a OOS (od 2025-03),
  2) vyber varianty JEN na vyvoji (nejvyssi expectancy pri n >= 30), OOS jednou,
  3) metriky dokumentu na OOS: n >= 100, expectancy >= 0,15 R, PF >= 1,3, 95. percentil DD (Monte Carlo
     10 000 promichani) <= 15 R, ziskova ctvrtleti >= 60 %, o >= 0,1 R lepsi nez nahodne vstupy,
     plato (sousedni varianty na vyvoji take ziskove),
  4) walk-forward: 12 mesicu vyber varianty, 3 mesice test, posun 3 mesice.
Vystup: research_data/f7/f7_vyhodnoceni.txt
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

import f7_lib as L
import research_f7 as R

sys.stdout.reconfigure(line_buffering=True)
OUT = L.D7
NMIN_DEV = 30
VT_ORDER = ["M1", "M3", "M5", "M15", "-"]


def load():
    parts = [pd.read_pickle(p) for p in glob.glob(os.path.join(OUT, "f7_obchody_*.pkl"))]
    df = pd.concat([p for p in parts if len(p)], ignore_index=True)
    df["oos"] = df.t >= R.SPLIT_T
    df["dt"] = pd.to_datetime(df.t, unit="s")
    df["grp"] = df.cls
    doc3 = df.mk.isin(["BTCUSD", "ETHUSD", "SOLUSD"])
    return df, doc3


def st(r):
    r = np.asarray(r, float)
    n = len(r)
    if n == 0:
        return dict(n=0, mean=np.nan, win=np.nan, pf=np.nan, t=np.nan, aw=np.nan, al=np.nan)
    w, lo = r[r > 0], r[r <= 0]
    sd = r.std(ddof=1) if n > 1 else np.nan
    return dict(n=n, mean=r.mean(), win=(r > 0).mean() * 100, pf=w.sum() / -lo.sum() if lo.sum() < 0 else np.inf,
                t=r.mean() / sd * np.sqrt(n) if sd and sd > 0 else np.nan, aw=w.mean() if len(w) else 0.0, al=lo.mean() if len(lo) else 0.0)


def fmt(s):
    if s["n"] == 0:
        return "n 0"
    return f"n {s['n']:4d}  prum {s['mean']:+.3f} R  win {s['win']:4.1f} %  PF {s['pf']:.2f}  t {s['t']:+.2f}"


def mc_dd95(r, reps=10000, seed=7):
    r = np.asarray(r, float)
    if len(r) < 2:
        return np.nan
    rng = np.random.default_rng(seed)
    dd = np.empty(reps)
    for k in range(reps):
        eq = np.cumsum(rng.permutation(r))
        dd[k] = (np.maximum.accumulate(np.r_[0.0, eq])[1:] - eq).max()
    return float(np.percentile(dd, 95))


def quarters_pos(tr):
    q = tr.groupby(tr.dt.dt.to_period("Q").astype(str)).R.sum()
    return (q > 0).mean() * 100 if len(q) else np.nan, len(q)


def neighbors(var, allvars):
    cfg, vtf, en = var.split("|")
    out = []
    for v in allvars:
        c2, v2, e2 = v.split("|")
        if c2 != cfg or v == var:
            continue
        if v2 == vtf and e2 != en:
            out.append(v)
        elif e2 == en and vtf in VT_ORDER and v2 in VT_ORDER and abs(VT_ORDER.index(v2) - VT_ORDER.index(vtf)) == 1 and "-" not in (v2, vtf):
            out.append(v)
    return out


def walk_forward(g):
    """12 mesicu vyber (nejvyssi prumer, n >= 15), 3 mesice test, posun 3 mesice."""
    if not len(g):
        return pd.DataFrame()
    t0 = g.dt.min().to_period("M").to_timestamp()
    t_end = g.dt.max()
    res = []
    cur = t0
    while cur + pd.DateOffset(months=15) <= t_end + pd.DateOffset(days=1):
        tr = g[(g.dt >= cur) & (g.dt < cur + pd.DateOffset(months=12))]
        te = g[(g.dt >= cur + pd.DateOffset(months=12)) & (g.dt < cur + pd.DateOffset(months=15))]
        s = tr.groupby("var").R.agg(["count", "mean"])
        s = s[s["count"] >= 15]
        if len(s):
            best = s["mean"].idxmax()
            res.append(te[te["var"] == best])
        cur += pd.DateOffset(months=3)
    return pd.concat(res) if res else pd.DataFrame()


def random_means(sel_all):
    """Nahodne vstupy ke vsem vybranym OOS obchodum; kazdy trh se pripravi jen jednou. Vraci prumer na obchod."""
    res = {}
    for mk, g in sel_all.groupby("mk"):
        sym, base = (mk.split("@") + [None])[:2]
        B = L.prepare(sym, base)
        rb = R.random_baseline(B, g, reps=20)
        if len(rb):
            res.update(rb.groupby("key").R.mean().to_dict())
        del B
    return pd.Series(res)


RND = pd.Series(dtype=float)


def main():
    df, doc3 = load()
    lines = []

    def out(x=""):
        print(x)
        lines.append(x)

    # faze 1: vyber variant na vyvoji -> nahodne vstupy jen k jejich OOS obchodum
    picks = []
    for (grp, strat), g in df.groupby(["grp", "strat"]):
        t = g[~g.oos].groupby("var").R.agg(["count", "mean"])
        t = t[t["count"] >= NMIN_DEV]
        if len(t):
            picks.append(g[(g["var"] == t["mean"].idxmax()) & g.oos])
    global RND
    RND = random_means(pd.concat(picks)) if picks else pd.Series(dtype=float)
    out("F7 - vyhodnoceni 6 strategii z dokumentu (OOS od 2025-03-01, po nakladech brokera)")
    out(f"obchodu celkem {len(df)}, trhy: {', '.join(sorted(df.mk.unique()))}")
    summary = []
    for grp in ["KRYPTO", "FOREX", "KOMODITY", "FOREX@M1", "KOMODITY@M1", "FOREX@M5", "KOMODITY@M5"]:
        G = df[df.grp == grp]
        if not len(G):
            continue
        out("\n" + "=" * 110)
        out(f"SKUPINA {grp}: {len(G)} obchodu ze vsech variant, trhy {', '.join(sorted(G.mk.unique()))}")
        for strat in ["S1", "S2", "S3", "S4", "S5", "S6"]:
            g = G[G.strat == strat]
            out(f"\n--- {strat} ({len(g)} obchodu ze vsech variant)")
            if not len(g):
                out("   zadny obchod")
                summary.append(dict(grp=grp, strat=strat, var="-", verdikt="zadny obchod"))
                continue
            tab = g.groupby(["cfg", "var"]).apply(lambda x: pd.Series(dict(
                n_dev=(~x.oos).sum(), dev=x.R[~x.oos].mean(), win_dev=(x.R[~x.oos] > 0).mean() * 100,
                n_oos=x.oos.sum(), oos=x.R[x.oos].mean(), win_oos=(x.R[x.oos] > 0).mean() * 100)), include_groups=False)
            # verna verze dokumentu: vsechny jeji varianty VTF x vstup dohromady
            for cfg in sorted(g.cfg.unique()):
                x = g[g.cfg == cfg]
                out(f"   {cfg:12s} vse dohromady  vyvoj {fmt(st(x.R[~x.oos]))} | OOS {fmt(st(x.R[x.oos]))}")
            cand = tab[tab.n_dev >= NMIN_DEV]
            if not len(cand):
                out(f"   -> zadna varianta nema na vyvoji n >= {NMIN_DEV} (nejvic {int(tab.n_dev.max())}) - nelze vybrat ani overit")
                summary.append(dict(grp=grp, strat=strat, var="-", verdikt=f"malo obchodu (max n vyvoj {int(tab.n_dev.max())})",
                                    n_all=len(g), mean_all=g.R.mean()))
                continue
            best = cand.dev.idxmax()
            cfg, var = best
            sel = g[g["var"] == var]
            so, sd = st(sel.R[sel.oos]), st(sel.R[~sel.oos])
            nb = neighbors(var, tab.index.get_level_values(1))
            nbm = [tab.xs(v, level=1).dev.iloc[0] for v in nb if v in tab.index.get_level_values(1)]
            dd = mc_dd95(sel.R[sel.oos])
            qp, nq = quarters_pos(sel[sel.oos])
            ro = RND.reindex(sel[sel.oos].index).dropna()
            rnd = float(ro.mean()) if len(ro) else np.nan
            wf = walk_forward(g)
            sw = st(wf.R) if len(wf) else st([])
            checks = dict(n=so["n"] >= 100, exp=so["mean"] >= 0.15, pf=so["pf"] >= 1.3, dd=dd <= 15,
                          q=qp >= 60, rnd=(so["mean"] - rnd) >= 0.1 if not np.isnan(rnd) else False,
                          plato=bool(nbm) and all(m > 0 for m in nbm))
            ok = all(checks.values())
            out(f"   VYBRANO na vyvoji: {var}")
            out(f"      vyvoj {fmt(sd)}")
            out(f"      OOS   {fmt(so)}  prum. vyhra {so['aw']:+.2f} / ztrata {so['al']:+.2f} R")
            out(f"      MC 95% DD {dd:.1f} R | zisk. ctvrtleti {qp:.0f} % z {nq} | nahodne vstupy {rnd:+.3f} R | "
                f"sousede na vyvoji {', '.join(f'{m:+.2f}' for m in nbm) or '-'}")
            out(f"      walk-forward {fmt(sw)}")
            out(f"      prahy: " + ", ".join(f"{k} {'ANO' if v else 'ne'}" for k, v in checks.items()) + f"  => {'PROSLO' if ok else 'neproslo'}")
            summary.append(dict(grp=grp, strat=strat, var=var, n_dev=sd["n"], dev=sd["mean"], n_oos=so["n"], oos=so["mean"],
                                pf_oos=so["pf"], win_oos=so["win"], rnd=rnd, wf_n=sw["n"], wf=sw["mean"], dd95=dd, q=qp,
                                verdikt="PROSLO" if ok else "neproslo", n_all=len(g), mean_all=g.R.mean()))
    out("\n" + "=" * 110)
    out("SOUHRN")
    S = pd.DataFrame(summary)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        out(S.round(3).to_string(index=False))
    # verne verze dokumentu (cfg doc) - kolik obchodu by realne udelaly
    out("\nVERNA PRAVIDLA DOKUMENTU (cfg 'doc' / A-low / A-abs / B-80), obchodu za rok na trh (prumer variant VTF x vstup):")
    for grp in df.grp.unique():
        G = df[df.grp == grp]
        yrs = (G.dt.max() - G.dt.min()).days / 365.25
        nmk = G.mk.nunique()
        for strat, cfgs in [("S1", ["doc"]), ("S2", ["doc"]), ("S3", ["A-low", "A-abs", "B-80"]), ("S4", ["doc"]), ("S5", ["doc"]), ("S6", ["doc"])]:
            x = G[(G.strat == strat) & G.cfg.isin(cfgs)]
            nv = max(x["var"].nunique(), 1)
            out(f"   {grp:12s} {strat}: {len(x) / nv / max(yrs, 0.1) / nmk:.2f} obchodu/rok/trh, prumer {x.R.mean():+.3f} R (n {len(x)})")
    open(os.path.join(OUT, "f7_vyhodnoceni.txt"), "w", encoding="utf-8").write("\n".join(lines))
    S.to_csv(os.path.join(OUT, "f7_souhrn.csv"), index=False)


if __name__ == "__main__":
    main()
