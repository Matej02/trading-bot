import sys, time
sys.path.insert(0, r"D:\Trading bot")
import numpy as np, research_f8 as F
t0 = time.time()
H = F.load("EURUSD"); T = F.tfs(H)
for tf in ("D1", "H4"):
    Z = F.find_zones(T[tf], 1.5); F.touch_info(H, T[tf], Z)
    print(tf, "zon", len(Z), "pivot", sum(z["piv"] for z in Z), "dotcenych", sum(z["fi"] >= 0 for z in Z))
    for piv in (True, False):
        v = dict(piv=piv, trend=False, sl20=False, tp="2", be=False)
        tr = F.one_per_dir(F.zone_trades(H, T[tf], Z, Z, v, tf))
        print("  piv" if piv else "  vse", "obchodu", len(tr), "prum R", round(np.mean([x["R"] for x in tr]), 3), "win", round(np.mean([x["R"] > 0 for x in tr]), 2))
print(round(time.time() - t0, 1), "s")
