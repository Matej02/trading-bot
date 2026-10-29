import sys, time
sys.path.insert(0, r"D:\Trading bot")
import numpy as np, pandas as pd
import research_f10 as X
t0 = time.time()
M = X.load1(sys.argv[1]); T = X.tfs(M); print("load", round(time.time()-t0,1))
for name in sys.argv[2:]:
    fn, mks, vars_ = X.STRATS[name]
    for v in vars_[:2]:
        t1 = time.time(); r = fn(M, T, v)
        R = np.array([x["R"] for x in r])
        print(name, X.vn(v), "n", len(r), "exp", round(R.mean(),3) if len(R) else None, "win", round((R>0).mean(),2) if len(R) else None, round(time.time()-t1,1), "s")
