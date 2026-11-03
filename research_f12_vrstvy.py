"""
F12 - vrstveny test propojeni konceptu: MSS na 5m/1m v killzone (vstup GP 0,618, SL na sweepu, TP 2,5 R)
 -> + 4H struktura -> + daily bias -> + POI (zona / balancni level). Kazda vrstva se porovna s predchozi a s nahodou.
Spusteni: py research_f12_vrstvy.py -> research_data/f12/f12_vrstvy.txt
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
import research_f12_eval as EV

LAYERS = [
    ("0 jen MSS v killzone", dict(h4=0, bias=0, poi="zadne")),
    ("1 + 4H struktura", dict(h4=1, bias=0, poi="zadne")),
    ("2 + daily bias", dict(h4=1, bias=1, poi="zadne")),
    ("3 + POI zóna", dict(h4=1, bias=1, poi="zona")),
    ("3b + POI balanc", dict(h4=1, bias=1, poi="balanc")),
    ("3c + POI obojí", dict(h4=1, bias=1, poi="obe")),
    ("x  4H + POI bez biasu", dict(h4=0, bias=0, poi="obe")),
]

if __name__ == "__main__":
    out = []
    rows = []
    for mk in F.MARKETS:
        for k in (1.5, 2.5):
            for tf in ("M5", "M1"):
                for name, lay in LAYERS:
                    var = dict(k=k, poi=lay["poi"], tf=tf, entry="gp", tp="2.5R", bias=lay["bias"], h4=lay["h4"])
                    for r in F.run_market(mk, var):
                        r["layer"] = name
                        r["kt"] = f"k={k} {tf}"
                        rows.append(r)
        print(mk, len(rows), flush=True)
    df = pd.DataFrame(rows)
    df["oos"] = df.t >= X.OOS
    df.to_pickle(os.path.join(F.D12, f"f12_vrstvy{X.SUF}.pkl"))
    for kt, g0 in df.groupby("kt"):
        out.append(f"\n=== {kt}  (všech 5 trhů, s náklady)" if not X.NOCOST else f"\n=== {kt} BEZ NÁKLADŮ")
        for name, _ in LAYERS:
            g = g0[g0.layer == name]
            a, b = EV.st(g.R[~g.oos]), EV.st(g.R[g.oos])
            rb = EV.random_base(g[g.oos], reps=2) if len(g[g.oos]) else np.array([])
            out.append(f"{name:24s} vývoj {EV.fmt(a)} | OOS {EV.fmt(b)} | náhoda OOS {EV.fmt(EV.st(rb))}")
        print("\n".join(out[-len(LAYERS) - 1:]), flush=True)
    open(os.path.join(F.D12, f"f12_vrstvy{X.SUF}.txt"), "w", encoding="utf-8").write("\n".join(out))
