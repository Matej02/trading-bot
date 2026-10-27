"""
!!! POZOR - DULEZITE !!!
Tento skript generuje SYNTETICKA (nahodne vygenerovana) OHLC data,
ktera se POUZE POVAHOU podobaji EUR/USD H1. NEJSOU to skutecne
historicke ceny.

Duvod: tenhle sandbox nema pristup k financnim datovym API
(broker/data vendor domeny nejsou na whitelistu site).

Ucel techto dat je VYHRADNE overit, ze kod (strategie + risk
management + backtest engine) bezi spravne a nema bugy.

Vysledky backtestu na techto datech NEVYPOVIDAJI NIC o tom,
jestli ma strategie skutecnou edge na realnem trhu. Pred jakymkoli
demo/live nasazenim MUSIME tento soubor nahradit realnymi datu
(napr. export z MT5 "Historical Data Center", nebo CSV od data
vendora) - viz README.md, sekce "Dalsi kroky".
"""

import numpy as np
import pandas as pd


def generate_synthetic_eurusd_h1(n_bars: int = 8000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    start = pd.Timestamp("2023-01-02 00:00")
    timestamps = pd.date_range(start, periods=n_bars, freq="h")
    # jen pracovni dny/hodiny, aby to trochu pripominalo forex trh
    timestamps = timestamps[timestamps.dayofweek < 5]
    n_bars = len(timestamps)

    price = 1.0800
    closes = []
    # nekolik "rezimu" trendu, aby data nebyla cisty random walk
    regime_len = 300
    drift = 0.0
    for i in range(n_bars):
        if i % regime_len == 0:
            drift = rng.choice([-1, 0, 1]) * rng.uniform(0.00002, 0.00006)
        vol = rng.uniform(0.0003, 0.0009)
        price += drift + rng.normal(0, vol)
        price = max(price, 0.9)
        closes.append(price)

    closes = np.array(closes)
    opens = np.roll(closes, 1)
    opens[0] = closes[0]
    highs = np.maximum(opens, closes) + rng.uniform(0.0001, 0.0006, n_bars)
    lows = np.minimum(opens, closes) - rng.uniform(0.0001, 0.0006, n_bars)

    df = pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes},
        index=timestamps,
    )
    df.index.name = "time"
    return df


if __name__ == "__main__":
    df = generate_synthetic_eurusd_h1()
    df.to_csv("sample_data_SYNTHETIC.csv")
    print(f"Vygenerovano {len(df)} synteticky barů -> sample_data_SYNTHETIC.csv")
    print("PRIPOMINKA: tohle nejsou realna data, jen test mechaniky kodu.")
