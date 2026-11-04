"""Shoda: kandidati z zivych MT5 dat (75 dni) vs z testovacich pickle (cela historie) ve spolecnem obdobi."""
import os, sys
sys.path.insert(0, r"D:\Trading bot"); os.chdir(r"D:\Trading bot")
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import run_fm_demo as R
import research_f10 as X
R.mc.connect()
pairs = [("F13_ves", "GBPUSD"), ("F13_ves", "XAUUSD"), ("F12_mucka", "XAUUSD"), ("F12_mucka", "XAGUSD"), ("F14_pat", "XAUUSD"), ("F13_ves", "NAS100mini")]
for name, mk in pairs:
    R.X.D10 = R.LIVE_DIR; R.clear_caches()
    last = R.fetch_m1(mk)
    live = {(x[0], x[1]) for x in R.CAND[name](mk)}
    first = pd.read_pickle(os.path.join(R.LIVE_DIR, f"{mk}_M1.pkl")).t.iloc[0]
    R.X.D10 = os.path.join("research_data", "f10"); R.clear_caches()
    hist_df = pd.read_pickle(os.path.join(R.X.D10, f"{mk}_M1.pkl"))
    end = hist_df.t.iloc[-1]
    hist = {(x[0], x[1]) for x in R.CAND[name](mk)}
    a = first + 40 * 86400                     # zahrivaci doba zivych dat (zony, H4 struktura)
    L = {x for x in live if a <= x[0] <= end}; H = {x for x in hist if a <= x[0] <= end}
    print(f"{name} {mk}: obdobi {pd.Timestamp(a, unit='s'):%Y-%m-%d}..{pd.Timestamp(end, unit='s'):%Y-%m-%d} | live {len(L)} hist {len(H)} shoda {len(L & H)}", flush=True)
R.X.D10 = R.LIVE_DIR
