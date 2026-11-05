"""F20 shoda: kandidati SFP a jejich filtry ze zivych MT5 dat (75 dni) vs z testovacich pickle ve spolecnem obdobi."""
import os
import sys

sys.path.insert(0, r"D:\Trading bot")
os.chdir(r"D:\Trading bot")
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

import run_fm_demo as R
import research_f20_user as U

R.mc.connect()
for mk in sys.argv[1:] or ["EURUSD", "SPX500mini", "GER_30mini", "XAUUSD"]:
    R.X.D10 = R.LIVE_DIR
    R.clear_caches()
    R.mt5.symbol_select(mk, True)
    R.fetch_m1(mk, R.M1_DAYS_F20)
    P, C = U.candidates(mk)
    t = P["M"]["t"]
    live = {(int(t[r["ic"]]), r["d"]): (r["b4"], r["b15"], r["pz"], r["vp"]) for r in C}
    first = int(t[0])
    R.X.D10 = os.path.join("research_data", "f10")
    R.clear_caches()
    P2, C2 = U.candidates(mk)
    t2 = P2["M"]["t"]
    hist = {(int(t2[r["ic"]]), r["d"]): (r["b4"], r["b15"], r["pz"], r["vp"]) for r in C2}
    end = int(t2[-1])
    a = first + 40 * 86400                     # zahrivaci doba zivych dat (H4 struktura, zony)
    Lk = {k for k in live if a <= k[0] <= end}
    Hk = {k for k in hist if a <= k[0] <= end}
    both = Lk & Hk
    same = sum(live[k] == hist[k] for k in both)
    sel_l = {k for k in Lk if live[k][0] and live[k][1] and live[k][2] and live[k][3] >= 2}
    sel_h = {k for k in Hk if hist[k][0] and hist[k][1] and hist[k][2] and hist[k][3] >= 2}
    print(f"{mk}: {pd.Timestamp(a, unit='s'):%Y-%m-%d}..{pd.Timestamp(end, unit='s'):%Y-%m-%d} | SFP live {len(Lk)} hist {len(Hk)} "
          f"spolecne {len(both)} | stejne filtry {same}/{len(both)} | vybrana varianta live {len(sel_l)} hist {len(sel_h)} "
          f"shoda {len(sel_l & sel_h)}", flush=True)
R.X.D10 = R.LIVE_DIR
