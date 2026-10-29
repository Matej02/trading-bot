"""F10 vyhodnoceni: varianta vybrana na vyvoji (do 2021), OOS 2022+, nahodne vstupy, rozpad po trzich. -> f10_vyhodnoceni.txt"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f10 as X
import research_f8 as F

OUT = []
NAMES = {"VES": "Veselovský (ICT intraday)", "KIM": "Kimmel (indexy)", "PAT": "Pátek (průraz pivotu M5 v trendu H4)",
         "SRA": "Šrajer day trading (M15 zóna ve 4H zóně)", "MUC": "Můčka (sweep Asie ≤ 35 pipů)",
         "VAL": "Valchář (H4 OB + POC + likvidita)", "HAK": "Hakimi (Fibo 0,5–0,75 + zóna)", "HVE": "Hvězda (D1 zóna + svíčka)"}


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def st(r):
    r = np.asarray(r, float)
    if len(r) < 2:
        return dict(n=len(r), exp=np.nan, pf=np.nan, win=np.nan, t=np.nan)
    g, b = r[r > 0].sum(), -r[r < 0].sum()
    return dict(n=len(r), exp=r.mean(), pf=g / b if b > 0 else np.inf, win=(r > 0).mean() * 100,
                t=r.mean() / (r.std(ddof=1) / np.sqrt(len(r))))


def fm(s):
    return f"n={s['n']:5d} exp={s['exp']:+.3f}R PF={s['pf']:.2f} win={s['win']:.0f}% t={s['t']:+.2f}" if s["n"] > 1 else f"n={s['n']}"


def random_m1(tr, reps=3, seed=7):
    """Nahodny vstup: stejny trh a rok, stejna hodina dne, smer, SL = stejny nasobek ATR D1, stejne R cile a vystup."""
    rng = np.random.default_rng(seed)
    res = []
    for mk, g in tr.groupby("mk"):
        M = X.load1(mk)
        T = X.agg(M, M["day"])
        dst, den = X.day_end_idx(M)
        yr = pd.to_datetime(M["t"][dst], unit="s").year.to_numpy()
        for x in g.itertuples():
            y = pd.Timestamp(x.t, unit="s").year
            days = np.flatnonzero(yr == y)
            days = days[days > 0]
            for _ in range(reps):
                k = int(rng.choice(days))
                a = T["a"][k - 1]
                if not a > 0 or not np.isfinite(x.risk_atrD):
                    continue
                seg = M["hm"][dst[k]:den[k] + 1]
                j = np.searchsorted(seg, x.hm) if np.isfinite(x.hm) else int(rng.integers(0, len(seg)))
                i0 = dst[k] + min(j, len(seg) - 2)
                risk = x.risk_atrD * a
                E = M["o"][i0]
                SL, TP = E - x.d * risk, E + x.d * x.Rt * risk
                if x.exit_rule == "den":
                    iex = den[k]
                else:  # pevna maximalni doba drzeni (ne skutecna doba obchodu - ta zavisi na vysledku)
                    iex = i0 + int(str(x.exit_rule).rstrip("d")) * 1440
                s = X.sim(M, x.d, E, SL, TP, i0, i0, 1, iex)
                if s:
                    res.append(s["R"])
    return np.array(res)


def main(names):
    for nm in names:
        f = os.path.join(X.D10, f"f10_{nm}{X.SUF}.pkl")
        if not os.path.exists(f):
            continue
        df = pd.read_pickle(f)
        if df.empty:
            p(f"\n{NAMES[nm]}: žádné obchody")
            continue
        df["oos"] = df.t >= X.OOS
        p("\n" + "=" * 110)
        p(f"{NAMES[nm]}  ({df.mk.nunique()} trhů)")
        rows = []
        for var, g in df.groupby("var"):
            sd, so = st(g[~g.oos].R), st(g[g.oos].R)
            rows.append((var, sd, so))
            p(f"  {var:36s} DEV {fm(sd)} | OOS {fm(so)}")
        cand = [r for r in rows if r[1]["n"] >= 50] or rows
        var, sd, so = max(cand, key=lambda r: r[1]["exp"] if np.isfinite(r[1]["exp"]) else -9)
        g = df[df["var"] == var]
        o = g[g.oos]
        p(f"  → VYBRANÁ na vývoji: {var}")
        p(f"    OOS {fm(so)}")
        for mk, gg in g.groupby("mk"):
            p(f"     {mk:12s} DEV {fm(st(gg[~gg.oos].R))} | OOS {fm(st(gg[gg.oos].R))}")
        if len(o) >= 20:
            rb = random_m1(o) if nm != "HVE" else None
            if rb is not None and len(rb):
                p(f"    náhodné vstupy OOS: {fm(st(rb))}")
                ok = so["n"] >= 100 and so["exp"] >= 0.15 and so["pf"] >= 1.3 and so["exp"] - rb.mean() >= 0.1
            else:
                ok = so["n"] >= 100 and so["exp"] >= 0.15 and so["pf"] >= 1.3
            p(f"    PRAHY: {'PROŠLO' if ok else 'neprošlo'}")
    open(os.path.join(X.D10, f"f10_vyhodnoceni{X.SUF}.txt"), "w", encoding="utf-8").write("\n".join(OUT))


if __name__ == "__main__":
    main(sys.argv[1:] or list(NAMES))
