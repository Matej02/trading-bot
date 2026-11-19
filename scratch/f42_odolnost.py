"""F42 popisna kontrola odolnosti RSI(2): prah RSI 5/10/15 x max. dni 5/10/15 (pravidla rozhodnuti se nemeni)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import f42_rsi2 as F  # noqa: E402

out = []
for thr in (5, 10, 15):
    for maxd in (5, 10, 15):
        v = F.evaluate(F.US, "yahoo", F.DEV0, F.SPLIT, thr, maxd)
        k = F.evaluate(F.US, "yahoo", F.SPLIT, None, thr, maxd)
        s = (f"RSI<{thr:2d} max {maxd:2d} dní | vývoj {v['sig']['m']:+.3f} R převis {v['diff']:+.3f} t {v['t']:+.2f} (n {v['sig']['n']})"
             f" | kontrola {k['sig']['m']:+.3f} R převis {k['diff']:+.3f} t {k['t']:+.2f} (n {k['sig']['n']})")
        print(s, flush=True)
        out.append(s)
open(os.path.join(F.OUT, "odolnost.txt"), "w", encoding="utf-8").write(chr(10).join(out))
