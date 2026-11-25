"""
Export pro kontrolu shody F93 v simulatoru (simulator/scripts/f93-parity.ts): stejna data jako test F93
(yahoo_us.pkl, S&P 500 z f6, udalosti EDGAR) + obchody z testu. Spusteni: python -I f93_export.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import f85_rsi2_akcie as F85  # noqa: E402
import f92_vysledky_den as F92  # noqa: E402

us = pd.read_pickle(os.path.join(F.RD, "f85", "yahoo_us.pkl"))
E = pd.read_pickle(os.path.join(F.RD, "f88", "udalosti.pkl"))
E = E[E.form == "8-K"]
ix = F.yahoo("SPX500mini")
out = {"spx": [[str(d.date()), float(c)] for d, c in ix.close.items()], "stocks": {}, "events": {}}
for t, g in E.groupby("ticker"):
    if t not in us:
        continue
    d = F85.clean(us[t])
    out["stocks"][t] = [[str(i.date()), float(r.open), float(r.high), float(r.low), float(r.close)] for i, r in d.iterrows()]
    out["events"][t] = list(g.acceptance)
T, _ = F92.build(F88E := __import__("f88_pead").events(), us, "F93")
out["trades"] = [dict(t=r.t, day=str(r.day.date()), z=float(r.z), s=int(r.s), norm=float(r.norm), pess=float(r.pess), gross=float(r.gross))
                 for r in T.itertuples()]
p = os.path.join(F.RD, "f88", "f93_parita_vstup.json")
json.dump(out, open(p, "w"))
print("obchodu z testu", len(out["trades"]), "akcii", len(out["stocks"]), "->", p)
