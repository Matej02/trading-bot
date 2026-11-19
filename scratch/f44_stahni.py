"""F44: stazeni dennich hodnot ^VIX a ^VIX3M z Yahoo (chart API) do research_data/f44 (surovy JSON). Souhlas uzivatele 2026-11-19."""
import os
import sys
import time
import urllib.parse
import urllib.request

OUT = sys.argv[1]
for tk in ("^VIX", "^VIX3M"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(tk)}?period1=631152000&period2=1795000000&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research script)"})
    raw = urllib.request.urlopen(req, timeout=60).read()
    open(os.path.join(OUT, f"{tk.strip('^')}.json"), "wb").write(raw)
    print(tk, len(raw), "B")
    time.sleep(2)
