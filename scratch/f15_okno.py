"""Overeni: chybejici TS signaly F15 jsou dane kratkou historii (okno 6500 1h svicek jako zive)? Python na stejnem okne."""
import os, sys, json, numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
os.chdir(r"D:\Trading bot"); sys.path.insert(0, r"D:\Trading bot")
import research_f8 as F, research_f15_hve as V, research_f15_cot as C
VAR = dict(tf="den", base=3, dvw=1, lnl=1, entry="limit", cot="0", parity=True)
for mk in sys.argv[1:]:
    D = json.load(open(f"scratch/f15_parita_{mk}.json"))
    H0, T0, Z0, S0 = V.prep(mk)
    full = {(r[0], r[1]) for r in V.run_market(mk, VAR)}
    hits = 0; tot = 0
    for t, d, sl in D["py"]:
        i = int(np.searchsorted(H0["t"], t))
        a = max(0, i - 6499)
        H = {k: (v[a:i + 1] if isinstance(v, np.ndarray) and len(v) == len(H0["t"]) else v) for k, v in H0.items()}
        H["cum_sw"] = H0["cum_sw"][a:i + 1]
        T = F.tfs(H)
        Z = {(tf, bm): F.find_zones(T[tf], 1.5, bmax=bm) for tf in ("W1", "D1", "H4") for bm in (3, 6)}
        V._C.clear(); V._C["okno"] = (H, T, Z, S0)
        res = {(r[0], r[1]) for r in V.run_market("okno", VAR)}
        tot += 1; hits += (t, d) in res
    print(mk, f"Python s oknem 6500 h najde {hits} z {tot} plných signálů")
