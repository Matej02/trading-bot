"""F7: maji koncepty/strategie vyhodu aspon PRED naklady? Stejne obchody se spreadem a swapy = 0
(filtr SL >= 5x spread pak nic nevyradi, takze vzorek je o neco vetsi)."""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f7 as R
import research_f7_koncepty as K

rows = []
for mk in sys.argv[1:] or ["BTCUSD", "ETHUSD", "SOLUSD"]:
    B = L.prepare(mk)
    PL = R.build_pools(B)
    Z = R.build_zones(B)
    for nul in (False, True):
        if nul:
            B["spr"] = np.zeros_like(B["spr"])
            B["swl"] = B["sws"] = 0.0
        tests = [("K1 SFP vsechny pooly", K.k1(B, PL, False), "M15", "mkt"), ("K2 VWAP pullback", K.k2(B), "M15", "mkt")]
        for cfg_name, p in [("S1 jadro", dict(rv=0.0, kz=False, prem=False, K=20)), ]:
            tests.append((cfg_name, R.setups_s1(B, PL, 0.0, False, False, 20), "M1", "ce"))
        tests.append(("S3 A-jadro", R.setups_s3(B, PL, "A", "any", False, False), "M1", "ce"))
        tests.append(("S6 jadro", R.setups_s6(B, PL, Z, "day", 0.0, True, 0.6, R.vtf_sweeps(B, PL, "M1"), 20), "M1", "ce"))
        tests.append(("S4 jadro", R.setups_s4(B, "M1", False, False, 0.05), "M1", "ce"))
        for name, su, vtf, en in tests:
            tr = R.execute(B, su, vtf, en)
            for x in tr:
                rows.append(dict(mk=mk, test=name, naklady="bez" if nul else "s", R=x["R"]))
    print(mk, "hotovo")
df = pd.DataFrame(rows)
t = df.groupby(["test", "naklady"]).R.agg(["count", "mean", lambda r: (r > 0).mean() * 100]).round(3)
t.columns = ["n", "prum R", "win %"]
print(t.to_string())
t.to_csv(os.path.join(L.D7, "f7_bez_nakladu.csv"))
