"""F20 overeni na trzich mimo test: vybrana varianta a rodina zafixovane z puvodniho vyberu (bez zmeny parametru).
Predem: py research_f20_user.py AUDUSD USDCAD XAGUSD US30mini CRUDE_OIL BTCUSD ETHUSD"""
import itertools
import os
import sys

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

import research_f12_eval as EV
import research_f20_eval as E
import research_f20_user as U

U.MARKETS = ["AUDUSD", "USDCAD", "XAGUSD", "US30mini", "CRUDE_OIL", "BTCUSD", "ETHUSD"]
G = E.load()


def show(lab, d):
    print(f"{lab:44s} vse {EV.fmt(EV.st(d.R))} | do 2021 {EV.fmt(EV.st(d.R[~d.oos]))} | 2022+ {EV.fmt(EV.st(d.R[d.oos]))}")


best = E.variant(G, "4H15", "zona", "2", "0", "close", "poc")
show("VYBRANA (zafixovana)", best)
for mk, h in best.groupby("mk"):
    show("   " + mk, h)
fam = pd.concat([E.variant(G, b, p, v, "0", "close", "poc") for b in ("4H", "4H15") for p in ("zona", "zonapoc")
                 for v in ("0", "2")]).drop_duplicates(["mk", "fi"])
show("rodina 8 variant (unikatni obchody)", fam)
for b, p, v in itertools.product(("4H", "4H15"), ("zona", "zonapoc"), ("0", "2")):
    show(f"   {b} {p} vp={v}", E.variant(G, b, p, v, "0", "close", "poc"))
print("nahoda pro vybranou:", EV.fmt(EV.st(EV.random_base(best, reps=3))))
print("nahoda pro rodinu:", EV.fmt(EV.st(EV.random_base(fam, reps=2))))
show("jadro SFP bez filtru, close, 2R", E.variant(G, "zadny", "zadne", "0", "0", "close", "2R"))
