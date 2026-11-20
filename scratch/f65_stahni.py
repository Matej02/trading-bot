"""F65: stazeni Yahoo dennich dat 10 svetovych indexu (max historie) do research_data/f65 (surovy JSON). Souhlas uzivatele 2026-11-20."""
import os
import sys
import time
import urllib.parse
import urllib.request

OUT = sys.argv[1]
TICKERS = ["^N225", "^AXJO", "^SSMI", "^AEX", "^BFX", "^HSI", "^GSPTSE", "^KS11", "^TWII", "^STI"]
for tk in TICKERS:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(tk)}?period1=0&period2=1795000000&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research script)"})
    raw = urllib.request.urlopen(req, timeout=60).read()
    open(os.path.join(OUT, tk.strip("^") + "_1d.json"), "wb").write(raw)
    print(tk, len(raw), "B", flush=True)
    time.sleep(2)
