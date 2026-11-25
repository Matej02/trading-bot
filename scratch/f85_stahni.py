"""
F85: stazeni dat (souhlas uzivatele 2026-11-25 „ano stahni to a spust test“).
1) historicke slozeni S&P 500 (GitHub fja05680/sp500) -> research_data/f85/raw/sp500_hist.csv
2) Yahoo denni (upraveno o splity a dividendy) pro vsechny cleny od 1996 + akcie FTMO -> research_data/f85/yahoo_us.pkl, yahoo_eu.pkl
Spusteni: python -I f85_stahni.py
"""
import os
import time
import urllib.request

import pandas as pd
import yfinance as yf

RD = r"D:\Trading bot\research_data\f85"
RAW = os.path.join(RD, "raw")
os.makedirs(RAW, exist_ok=True)
URL = "https://raw.githubusercontent.com/fja05680/sp500/master/S%26P%20500%20Historical%20Components%20%26%20Changes%20(Updated).csv"

FTMO_US = ["AAPL", "AMZN", "BA", "BABA", "BAC", "CSCO", "CVX", "DIS", "META", "FDX", "GE", "GM", "GOOG", "IBM", "INTC", "JNJ", "JPM",
           "KO", "MCD", "MSFT", "NFLX", "NVDA", "PFE", "QCOM", "RACE", "T", "TSLA", "V", "WMT", "XOM", "ZM", "RTX", "LMT", "PLTR", "AMD",
           "AVGO", "SBUX", "MSTR", "GME", "NKE", "ARM", "SNOW", "ASML", "AZN", "BRK-B"]
FTMO_EU = {"ADSGn": "ADS.DE", "AIRF": "AF.PA", "ALVG": "ALV.DE", "BAYGn": "BAYN.DE", "DBKGn": "DBK.DE", "IBE": "IBE.MC", "LVMH": "MC.PA",
           "SAN": "SAN.MC", "SIEGn": "SIE.DE", "VOWG_p": "VOW3.DE", "TTE": "TTE.PA", "BMW": "BMW.DE", "MBG": "MBG.DE"}


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(os.path.join(RD, "stahovani_log.txt"), "a", encoding="utf-8") as f:
        f.write(s + "\n")


def fetch(tickers, start="1995-01-01"):
    out, fail = {}, []
    for j in range(0, len(tickers), 50):
        part = tickers[j:j + 50]
        for attempt in range(3):
            try:
                df = yf.download(part, start=start, auto_adjust=True, actions=False, progress=False, threads=True, group_by="ticker")
                break
            except Exception as e:  # noqa: BLE001
                log("chyba davky", j, attempt, e)
                time.sleep(10)
        else:
            fail += part
            continue
        for t in part:
            try:
                d = df[t] if isinstance(df.columns, pd.MultiIndex) else df
                d = d.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna(subset=["open", "high", "low", "close"])
            except Exception:  # noqa: BLE001
                d = None
            if d is None or len(d) < 250:
                fail.append(t)
            else:
                out[t] = d.astype(float)
        log(f"davka {j}-{j + len(part)}: mame {len(out)}, chybi {len(fail)}")
        time.sleep(2)
    return out, fail


def main():
    p = os.path.join(RAW, "sp500_hist.csv")
    if not os.path.exists(p):
        urllib.request.urlretrieve(URL, p)
    h = pd.read_csv(p)
    log("slozeni:", p, os.path.getsize(p), "B,", len(h), "radku,", h.columns.tolist(), h.iloc[0, 0], "...", h.iloc[-1, 0])
    tick = set()
    for s in h.iloc[:, 1]:
        tick |= {x.strip() for x in str(s).split(",") if x.strip()}
    yt = sorted({t.replace(".", "-") for t in tick} | set(FTMO_US))
    log("tickeru celkem (cleni od 1996 + FTMO USA):", len(yt))
    us, fail = fetch(yt)
    pd.to_pickle(us, os.path.join(RD, "yahoo_us.pkl"))
    open(os.path.join(RD, "yahoo_chybi.txt"), "w", encoding="utf-8").write("\n".join(sorted(fail)))
    log("USA hotovo:", len(us), "tickeru, chybi", len(fail))
    eu, fail_eu = fetch(sorted(FTMO_EU.values()))
    pd.to_pickle(eu, os.path.join(RD, "yahoo_eu.pkl"))
    log("Evropa hotovo:", len(eu), "chybi", fail_eu)
    log("velikost:", round(sum(os.path.getsize(os.path.join(RD, f)) for f in os.listdir(RD) if f.endswith(".pkl")) / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
