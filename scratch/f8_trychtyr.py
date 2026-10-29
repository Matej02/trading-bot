import sys
sys.path.insert(0, r"D:\Trading bot")
import numpy as np
import research_f8 as F, f7_lib as L
H = F.load("EURUSD"); T = F.tfs(H)
for tf in ("D1", "H4"):
    X = T[tf]; o, h, l, c, a = X["o"], X["h"], X["l"], X["c"], X["a"]; body = c - o; n = len(c)
    sh, sl, tr = F.last_swing(h, l)
    cnt = dict(leg=0, base=0, bos5=0, bos10=0, bosmin=0)
    for j in range(20, n - 1):
        aj = a[j-1]
        for d in (1, -1):
            if d*body[j] < 0.5*aj: continue
            s = 0
            for k in range(j, min(j+3, n)):
                if d*body[k] <= 0: break
                s += d*body[k]
                if s >= 1.5*aj: break
            if s < 1.5*aj: continue
            cnt["leg"] += 1
            b0 = j
            while b0-1 >= 0 and j-(b0-1) <= 6 and abs(body[b0-1]) <= 0.5*aj: b0 -= 1
            if b0 == j: continue
            cnt["base"] += 1
            lvl = sh[b0] if d == 1 else sl[b0]
            if any((c[k]-lvl)*d > 0 for k in range(j, min(j+5, n))): cnt["bos5"] += 1
            if any((c[k]-lvl)*d > 0 for k in range(j, min(j+10, n))): cnt["bos10"] += 1
            # minor: nejblizsi lokalni high v poslednich 10 svickach pred bazi
            lvl2 = h[max(0,b0-10):b0].max() if d == 1 else l[max(0,b0-10):b0].min()
            if any((c[k]-lvl2)*d > 0 for k in range(j, min(j+5, n))): cnt["bosmin"] += 1
    print(tf, cnt)
