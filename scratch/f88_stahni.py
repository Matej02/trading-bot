"""
F88: data zverejneni vysledku z EDGAR (SEC) pro americke akcie FTMO (souhlas uzivatele 2026-11-25 „pokracuj 1 a pak 2“).
- https://www.sec.gov/files/company_tickers.json  (ticker -> CIK)
- https://data.sec.gov/submissions/CIK##########.json (+ starsi soubory z 'files')
Vystup: research_data/f88/raw/*.json, research_data/f88/udalosti.pkl (ticker, form, items, filingDate, acceptanceDateTime)
Spusteni: python -I f88_stahni.py
"""
import json
import os
import time
import urllib.request

import pandas as pd

RD = r"D:\Trading bot\research_data\f88"
RAW = os.path.join(RD, "raw")
os.makedirs(RAW, exist_ok=True)
# SEC vyzaduje kontakt v User-Agent. Zadava se jen pri spusteni (promenna SEC_UA), do repozitare se neuklada (repo je verejne).
UA = {"User-Agent": os.environ.get("SEC_UA", "TradingResearch research-script"), "Accept-Encoding": "identity"}
FTMO_US = ["AAPL", "AMZN", "BA", "BABA", "BAC", "CSCO", "CVX", "DIS", "META", "FDX", "GE", "GM", "GOOG", "IBM", "INTC", "JNJ", "JPM",
           "KO", "MCD", "MSFT", "NFLX", "NVDA", "PFE", "QCOM", "RACE", "T", "TSLA", "V", "WMT", "XOM", "ZM", "RTX", "LMT", "PLTR", "AMD",
           "AVGO", "SBUX", "MSTR", "GME", "NKE", "ARM", "SNOW", "ASML", "AZN", "BRK-B"]


def get(url, path):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    open(path, "wb").write(data)
    time.sleep(0.2)
    return json.loads(data)


def main():
    tick = get("https://www.sec.gov/files/company_tickers.json", os.path.join(RAW, "company_tickers.json"))
    cik = {v["ticker"].upper().replace(".", "-"): int(v["cik_str"]) for v in tick.values()}
    rows, miss = [], []
    for t in FTMO_US:
        c = cik.get(t)
        if c is None:
            miss.append(t)
            continue
        main_ = get(f"https://data.sec.gov/submissions/CIK{c:010d}.json", os.path.join(RAW, f"CIK{c:010d}.json"))
        parts = [main_["filings"]["recent"]]
        for f in main_["filings"].get("files", []):
            parts.append(get(f"https://data.sec.gov/submissions/{f['name']}", os.path.join(RAW, f["name"])))
        n0 = len(rows)
        for p in parts:
            for form, items, fd, acc in zip(p["form"], p["items"], p["filingDate"], p["acceptanceDateTime"]):
                if form in ("8-K", "6-K") and "2.02" in str(items):
                    rows.append(dict(ticker=t, cik=c, form=form, items=items, filingDate=fd, acceptance=acc))
        print(t, c, "souboru", len(parts), "udalosti 2.02:", len(rows) - n0, flush=True)
    E = pd.DataFrame(rows)
    E.to_pickle(os.path.join(RD, "udalosti.pkl"))
    size = sum(os.path.getsize(os.path.join(RAW, f)) for f in os.listdir(RAW)) / 1e6
    print("hotovo: udalosti", len(E), "tickeru s udalostmi", E.ticker.nunique() if len(E) else 0, "bez CIK", miss, f"velikost {size:.1f} MB")


if __name__ == "__main__":
    main()
