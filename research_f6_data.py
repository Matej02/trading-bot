"""
F6 / ukol 1 - denni historie co nejdelsi (Yahoo, period1=0, denni interval) pro vsechny trhy brokera.
Ceny jsou v jednotkach Yahoo; spread brokera se prepocita pres priceScale (cena Yahoo x priceScale = cena brokera).
Vystup: research_data/f6_<trh>_1d.pkl (open, high, low, close).
"""
import json
import os
import time

import pandas as pd
import requests

DATA = "research_data"
broker = json.load(open(os.path.join("simulator", "lib", "broker.json"), encoding="utf-8"))["markets"]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}


def yahoo_daily(ticker):
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(ticker)}"
    r = requests.get(url, params={"period1": 0, "period2": int(time.time()), "interval": "1d", "includeAdjustedClose": "false"}, headers=UA, timeout=30)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame({"open": q["open"], "high": q["high"], "low": q["low"], "close": q["close"]},
                      index=pd.to_datetime(res["timestamp"], unit="s").normalize())
    df = df.dropna()
    df = df[(df.high >= df.low) & (df.close > 0)]
    df = df[~df.index.duplicated(keep="last")]
    # Yahoo u forexu nekdy vraci open = predchozi close a high/low nesedi - oprava na rozpeti
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df.iloc[:-1]  # bez dnesni tvorici se svicky


def main():
    rows = []
    for mk, b in broker.items():
        if mk == "GAUUSD":
            continue
        path = os.path.join(DATA, f"f6_{mk}_1d.pkl")
        try:
            df = yahoo_daily(b["yahoo"])
            df.to_pickle(path)
            rows.append((mk, b["yahoo"], len(df), df.index[0].date(), df.index[-1].date()))
            print(f"   {mk:<12} {b['yahoo']:<10} {len(df):>6} dni  {df.index[0].date()} -> {df.index[-1].date()}")
        except Exception as e:
            print(f"   {mk:<12} {b['yahoo']:<10} CHYBA {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
