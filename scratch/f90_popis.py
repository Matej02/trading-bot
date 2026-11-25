"""F90 dodatecny popis PO vysledku (nerozhoduje): mirnejsi varianty pojistky a citlivost na skluz."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import f42_rsi2 as F, prop_meritko as PM, f87_f33_stop as F87, f90_pojistka as G
_, f3s = F87.f33_trades_stop()
rs = [t for mk in F.US for t in PM.rsi2_trades(mk) if t["t_in"] >= pd.Timestamp("2003-01-01")]
tr = f3s + rs; P = PM.Portfolio(tr); OP = G.open_map(tr)
out = ["F90 dodatečný popis po výsledku (nerozhoduje): skluz 0,1 / 0,25 / 0,4 R na pozici"]
for M in (1.5, 2.0):
    for r in (1.5, 1.75, 2.0):
        for sl in (0.1, 0.25, 0.4):
            trig = []
            S = G.sim(P, OP, r, M, slip=sl, trig=trig)
            a, e, l = PM.summarize(S), PM.summarize(G.EARLY(S)), PM.summarize(G.LATE(S))
            s = (f"M {M} r {r:4.2f} skluz {sl:4.2f} | celé {G.line(a)} | vývoj prop. {e['fail']:4.0%} medián {e['med']:5.1f} P12 {e['p12']:4.0%}"
                 f" | kontrola prop. {l['fail']:4.0%} medián {l['med']:5.1f} P12 {l['p12']:4.0%} | dnů se zásahem {len(set(trig))}")
            print(s, flush=True); out.append(s)
    S = G.sim(P, OP, 1.75, M)
    fr = [G.funded_g(P, OP, 1.75, d + pd.Timedelta(days=1), M) for d in S[S.out == "prosel"].pday]
    import numpy as np
    s = f"M {M} r 1.75 financovaný 12 m: přežije {np.mean([x[0] for x in fr]):.0%}, medián {np.nanmedian([x[1] for x in fr if x[0]]):+.1f} %"
    print(s); out.append(s)
open(os.path.join(PM.OUT, "f90_popis.txt"), "w", encoding="utf-8").write(chr(10).join(out))
