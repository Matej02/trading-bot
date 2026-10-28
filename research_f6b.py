"""
F6b - druhe kolo: kandidati vybrani JEN z dat do 2018 (research_f6.py, diagnostika long/short a vstup na zavreni).

PLAN STANOVENY PREDEM (rozhodnuto pred pohledem na 2019+):
  Ve vyberu do 2018 mela mean reversion vyhodu jen na indexech a jen u longu; vstup na zavreni (CFD na indexy
  se obchoduji i po zavreni burzy, bot vstoupi ~15 min po nem) byl stejny nebo lepsi nez na otevreni.
  Kandidati (vse INDEXY, vstup i vystup na zavreni, pravidla jinak beze zmeny z research_f6.py):
    K1 = MR1 RSI(2) < 10 nad SMA200, jen long, ven nad SMA5, stop 3 ATR, max 10 dni
    K2 = MR3 double seven, jen long, ven nad 7dennim maximem zavreni, stop 3 ATR, max 15 dni
    K3 = SE1 turn-of-month, long od zavreni predposledniho dne mesice 4 dny
  PROSLO = kontrola 2019-2023: n >= 50, prumer > 0, t >= 2,13 (Bonferroni pro 3) A holdout 2024+: prumer > 0, PF >= 1,10.
  Navic (jen informace): naklady x1,5, vysledky po letech, po trzich.
"""
import numpy as np
import pandas as pd

import research_f6 as f

CANDS = {"K1 MR1 RSI(2) long": ("MR1", 1), "K2 MR3 double seven long": ("MR3", 1), "K3 SE1 turn-of-month": ("SE1", 1)}


def trades(sid, side, cost=1.0):
    parts = [f.run(sid, mk, f.load(mk), cost_mult=cost, at_close=True, side=side) for mk in f.GROUPS["INDEXY"]]
    return pd.concat([p for p in parts if len(p)], ignore_index=True)


def main():
    out = {}
    for name, (sid, side) in CANDS.items():
        tr = trades(sid, side)
        out[name] = tr
        v, k, h = tr[tr.time < f.P1], tr[(tr.time >= f.P1) & (tr.time < f.P2)], tr[tr.time >= f.P2]
        sk, sh = f.stats(k), f.stats(h)
        ok = sk["n"] >= 50 and sk["meanR"] > 0 and sk["t"] >= 2.13 and sh["meanR"] > 0 and sh["pf"] >= 1.10
        print(f"\n=== {name} ===")
        print(f"  vyber    {f.fmt(f.stats(v))}")
        print(f"  kontrola {f.fmt(sk)}")
        print(f"  holdout  {f.fmt(sh)}   -> {'PROSLO' if ok else 'neproslo'}")
        t15 = trades(sid, side, 1.5)
        print(f"  naklady x1,5 (2019+): {f.fmt(f.stats(t15[t15.time >= f.P1]))}")
        yr = tr.groupby(tr.time.dt.year).R.agg(["count", "mean", lambda r: (r > 0).mean() * 100])
        yr.columns = ["n", "prumR", "win%"]
        print("  po letech (od 2015):", " | ".join(f"{y}: {r.n:.0f} {r['win%']:.0f}% {r.prumR:+.2f}" for y, r in yr[yr.index >= 2015].iterrows()))
        mk = tr[tr.time >= f.P1].groupby("market").R.agg(["count", "mean"])
        print("  po trzich 2019+:", " | ".join(f"{m}: {r['count']:.0f} {r['mean']:+.2f}" for m, r in mk.iterrows()))
    pd.concat([x.assign(kandidat=k) for k, x in out.items()]).to_csv("research_data/f6b_obchody.csv", index=False)


if __name__ == "__main__":
    main()
