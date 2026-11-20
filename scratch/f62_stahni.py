"""F62: stazeni Yahoo GLD, IAU, SLV (denni, max) a GC=F (1h, poslednich 730 dni) do research_data/f62 (surovy JSON). Souhlas uzivatele 2026-11-20."""
import os
import sys
import time
import urllib.parse
import urllib.request

OUT = sys.argv[1]
JOBS = [(t, "period1=1072915200&period2=1795000000&interval=1d", f"{t}_1d") for t in ("GLD", "IAU", "SLV")]
JOBS.append(("GC=F", "range=730d&interval=1h", "GC_F_1h"))
for tk, q, name in JOBS:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(tk)}?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research script)"})
    raw = urllib.request.urlopen(req, timeout=60).read()
    open(os.path.join(OUT, f"{name}.json"), "wb").write(raw)
    print(tk, len(raw), "B")
    time.sleep(2)
