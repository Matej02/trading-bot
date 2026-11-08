"""Stazeni dennich cen TLT, IEF, SPY z Yahoo Finance (chart API) do research_data/f33/yahoo (surovy JSON)."""
import json
import os
import sys
import time
import urllib.request

OUT = sys.argv[1]
for tk in ("TLT", "IEF", "SPY"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}?period1=1041379200&period2=1794000000&interval=1d&events=div"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research script)"})
    raw = urllib.request.urlopen(req, timeout=60).read()
    open(os.path.join(OUT, f"{tk}.json"), "wb").write(raw)
    print(tk, len(raw), "B")
    time.sleep(2)
