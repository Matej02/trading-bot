"""F93 dodatecny popis PO vysledku (nerozhoduje): meritko s mensim rizikem na akciove obchody F93."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import f42_rsi2 as F, prop_meritko as PM, f87_f33_stop as F87, f86_riziko_zkousky as F86, f88_pead as F88, f92_vysledky_den as G
E = F88.events(); us = pd.read_pickle(os.path.join(F.RD, "f85", "yahoo_us.pkl"))
_, cand = G.build(E, us, "F93", with_paths=True)
ch = G.per_day(cand)
rs = [t for mk in F.US for t in PM.rsi2_trades(mk) if t["t_in"] >= pd.Timestamp("2003-01-01")]
_, f3s = F87.f33_trades_stop()
out = ["F93 dodatečný popis po výsledku (nerozhoduje): indexy 1,25 %, akciové obchody F93 menším rizikem"]
for f in (0.2, 0.4, 0.6):
    sc = [dict(c, R=c["R"] * f, path=[(d, lo * f, cl * f) for d, lo, cl in c["path"]]) for c in ch]
    S = F86.sim(PM.Portfolio(f3s + rs + sc), 1.25, 0)
    a, e, l = PM.summarize(S), PM.summarize(F86.EARLY(S)), PM.summarize(F86.LATE(S))
    s = f"F93 riziko {1.25 * f:.2f} %: celé {F86.line(a)} | vývoj {F86.line(e)} | kontrola {F86.line(l)}"
    print(s); out.append(s)
open(os.path.join(F.RD, "f88", "f93_popis.txt"), "w", encoding="utf-8").write(chr(10).join(out))
