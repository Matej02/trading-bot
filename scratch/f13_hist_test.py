"""
F13 na delsi historii - beh presne demo varianty F13 (tf=M1 lvl=liq entry=ob50 tp=tp2) nad zvolenou slozkou M1 dat.
Spusteni: python -I f13_hist_test.py <slozka M1 dat> <stitek> <trh> [--bez-zprav]
Vysledek: D:\\Trading bot\\research_data\\histdata\\out\\<stitek>_<trh>.pkl
Kod runneru ani vyzkumu se nemeni: jen se v tomto procesu presmeruje cteni M1 (X.D10) na jinou slozku.
"""
import os
import sys
import time

ROOT = r"D:\Trading bot"
sys.path.insert(0, ROOT)
import pandas as pd  # noqa: E402

import research_f10 as X  # noqa: E402
import research_f13_ves as V  # noqa: E402

data_dir, label, mk = sys.argv[1:4]
X.D10 = data_dir
if "--bez-zprav" in sys.argv:
    X.NEWS_DAYS = set()                  # vypnout vynechani dnu FOMC/NFP/CPI (jen pro mereni vlivu)
VAR = dict(tf="M1", lvl="liq", entry="ob50", tp="tp2")
t0 = time.time()
rows = V.run_market(mk, VAR)
out = os.path.join(ROOT, "research_data", "histdata", "out")
os.makedirs(out, exist_ok=True)
pd.DataFrame(rows).to_pickle(os.path.join(out, f"{label}_{mk}.pkl"))
print(f"{label} {mk}: {len(rows)} obchodu za {time.time() - t0:.0f} s", flush=True)
