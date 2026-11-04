import os, sys
sys.path.insert(0, r"D:\Trading bot"); os.chdir(r"D:\Trading bot")
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import run_fm_demo as R
R.mc.connect()
R.clear_caches()
for name, cfg in R.STRATS.items():
    for mk in cfg["markets"]:
        R.mt5.symbol_select(mk, True)
        last = R.fetch_m1(mk)
        if name == "F15_hve":
            R.fetch_h1(mk)
        R.clear_caches()
        c = R.CAND[name](mk)
        recent = [x for x in c if x[0] >= last - 30 * 86400]
        lastc = max(c, key=lambda x: x[0]) if c else None
        print(f"{name:10s} {mk:11s} kandidátů {len(c):4d}, za 30 dní {len(recent):3d}, poslední {pd.Timestamp(lastc[0], unit='s') if lastc else '-'}", flush=True)
