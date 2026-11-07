"""
F13 na delsi historii - vyhodnoceni podle pravidel zapsanych predem ve vaultu.
Spusteni: python -I f13_hist_eval.py  -> research_data\\histdata\\out\\f13_hist_souhrn.txt
"""
import os
import sys

ROOT = r"D:\Trading bot"
sys.path.insert(0, ROOT)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import research_f10 as X  # noqa: E402
import research_f12_eval as EV  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(ROOT, "research_data", "histdata", "out")
H = os.path.join(ROOT, "research_data", "histdata")
NEW_END = pd.Timestamp("2019-02-21").value // 10**9          # zacatek dat brokera
OVL_END = pd.Timestamp("2026-01-01").value // 10**9          # konec HistData
NEWS_START = pd.Timestamp("2021-09-01").value // 10**9       # zacatek rucniho kalendare zprav
MKS = ("NAS100mini", "SPX500mini")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def load(label):
    fr = [pd.read_pickle(os.path.join(OUT, f"{label}_{m}.pkl")) for m in MKS]
    d = pd.concat([f for f in fr if len(f)], ignore_index=True).sort_values("t").reset_index(drop=True)
    d["dt"] = pd.to_datetime(d.t, unit="s")
    return d


def stat(R):
    R = np.asarray(R, float)
    if len(R) < 2:
        return dict(n=len(R), exp=np.nan, sd=np.nan, tt=np.nan, pf=np.nan, win=np.nan)
    g, b = R[R > 0].sum(), -R[R < 0].sum()
    return dict(n=len(R), exp=R.mean(), sd=R.std(ddof=1), tt=R.mean() / R.std(ddof=1) * np.sqrt(len(R)),
                pf=g / b if b > 0 else np.inf, win=(R > 0).mean())


def fmt(s):
    return (f"n {s['n']:4d} | {s['exp']:+.3f} R | t {s['tt']:+.2f} | PF {s['pf']:.2f} | výhra {s['win']:.0%}"
            if s["n"] >= 2 else f"n {s['n']}")


def boot(R, reps=20000, seed=1):
    rng = np.random.default_rng(seed)
    R = np.asarray(R, float)
    return np.percentile([rng.choice(R, len(R)).mean() for _ in range(reps)], [5, 95])


def match(a, b, tol=120):
    """Podil obchodu z a, ktere maji v b obchod na stejnem trhu, ve stejnem smeru a do tol sekund."""
    hit, pairs = 0, []
    for mk in MKS:
        x, y = a[a.mk == mk], b[b.mk == mk]
        yt, yd, yr = y.t.to_numpy(), y.d.to_numpy(), y.R.to_numpy()
        for _, r in x.iterrows():
            j = np.where((np.abs(yt - r.t) <= tol) & (yd == r.d))[0]
            if len(j):
                hit += 1
                pairs.append((r.R, yr[j[0]]))
    return hit / max(len(a), 1), np.array(pairs)


A, B, C, D = load("A_broker"), load("B_broker_bezobjemu"), load("C_hist_jako_broker"), load("D_hist_skutecne_utc")
E, F = load("E_broker_bezzprav"), load("F_hist_jako_broker_bezzprav")

say("F13 Veselovský na indexech (NAS100 + SPX500), varianta z dema: tf=M1 lvl=liq entry=ob50 tp=tp2, s náklady")
say("=" * 100)
say("\n1) Kontrola: původní test na datech brokera")
say("   vývoj 2019-02..2021:", fmt(stat(A.R[A.t < X.OOS])))
say("   OOS 2022..2026-10:  ", fmt(stat(A.R[A.t >= X.OOS])))

say("\n2) Kalibrace na překryvu 2019-02-21 .. 2025-12-31 (HistData proti brokerovi)")
ov = lambda d: d[(d.t >= NEW_END) & (d.t < OVL_END)]
for name, d in (("broker s objemem (demo)", A), ("broker bez objemu", B), ("HistData, čas jako broker", C), ("HistData, skutečné UTC", D)):
    say(f"   {name:28s}", fmt(stat(ov(d).R)))
for (na, a), (nb, b) in ((("broker bez objemu", B), ("HistData jako broker", C)), (("broker s objemem", A), ("HistData jako broker", C))):
    m1, p1 = match(ov(a), ov(b))
    m2, _ = match(ov(b), ov(a))
    cr = np.corrcoef(p1[:, 0], p1[:, 1])[0, 1] if len(p1) > 2 else np.nan
    say(f"   shoda obchodů {na} -> {nb}: {m1:.0%} (opačně {m2:.0%}), korelace R u shodných {cr:.2f}")

say("\n3) NOVÝ VZOREK 2010-11 .. 2019-02-20 (data, na kterých se nikdy nic neladilo)")
nw = C[C.t < NEW_END].copy()
s_new = stat(nw.R)
say("   HistData, čas jako broker (= jak to počítá demo):", fmt(s_new))
lo, hi = boot(nw.R)
say(f"   90% bootstrap interval průměru: {lo:+.3f} .. {hi:+.3f} R")
for mk in MKS:
    say(f"     {mk:11s}", fmt(stat(nw.R[nw.mk == mk])))
nwd = D[D.t < NEW_END]
say("   HistData, skutečné UTC (kontrola):              ", fmt(stat(nwd.R)))
# nahoda: stejne SL/TP/smer/prazsky cas, vstup v nahodny den noveho vzorku
X.D10 = os.path.join(H, "m1", "m1_jako_broker")
X.OOS = NEW_END
nw["oos"] = False
rb = EV.random_base(nw)
say("   náhodné vstupy (stejný SL/TP, směr, čas, nový vzorek):", fmt(stat(rb)))

say("\n   po letech (HistData jako broker do 2019-02, pak broker s objemem):")
both = pd.concat([nw.assign(src="H"), A[A.t >= NEW_END].assign(src="B")], ignore_index=True)
for y, g in both.groupby(both.dt.dt.year):
    s = stat(g.R)
    say(f"     {y}: n {s['n']:3d}  {s['exp']:+.2f} R  součet {g.R.sum():+6.1f} R  ({'HistData' if (g.src == 'H').all() else 'broker' if (g.src == 'B').all() else 'oba'})")

say("\n4) CELEK: nový vzorek + data brokera 2019-02..2026-10")
s_all = stat(np.r_[nw.R, A.R])
say("   s brokerem s objemem (demo):", fmt(s_all))
say("   s brokerem bez objemu:      ", fmt(stat(np.r_[nw.R, B.R])))
c = np.cumsum(np.r_[nw.R, A.R])
say(f"   max. propad {np.max(np.maximum.accumulate(c) - c):.1f} R, součet {c[-1]:+.1f} R")

say("\n5) Vliv filtru zpráv (od 2021-09, kde je kalendář)")
nf = lambda d: d[d.t >= NEWS_START]
say("   broker s filtrem:", fmt(stat(nf(A).R)), "| bez filtru:", fmt(stat(nf(E).R)))
say("   HistData s filtrem:", fmt(stat(nf(C[C.t < OVL_END]).R)), "| bez filtru:", fmt(stat(nf(F[F.t < OVL_END]).R)))

say("\n6) ROZHODNUTÍ podle pravidel zapsaných předem")
ok1 = s_new["exp"] >= 0.10
ok2 = s_all["tt"] >= 2.0
say(f"   nový vzorek >= +0,10 R: {'ANO' if ok1 else 'NE'} ({s_new['exp']:+.3f} R)")
say(f"   celek t >= 2,0:         {'ANO' if ok2 else 'NE'} (t {s_all['tt']:+.2f})")
say(f"   => {'OVĚŘENÁ VÝHODA' if ok1 and ok2 else 'BEZ OVĚŘENÉ VÝHODY'}")
open(os.path.join(OUT, "f13_hist_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
