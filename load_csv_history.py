"""
Nacte realna historicka H1 OHLC data ze souboru exportovaneho z MT5
(Nastroje -> Historical Data Center -> vyber symbol/timeframe -> Export)
nebo z bezneho CSV od jineho data vendora.

Vraci DataFrame ve stejnem tvaru jako generate_sample_data.generate_synthetic_eurusd_h1:
index = 'time' (pd.Timestamp), sloupce = open, high, low, close.
"""

import pandas as pd


def load_mt5_history_csv(path: str) -> pd.DataFrame:
    """Nativni MT5 export - sloupce <DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> ...,
    oddelovac bud tab nebo carka (lisi se podle verze terminalu)."""
    df = pd.read_csv(path, sep=None, engine="python")
    df.columns = [c.strip("<>").lower() for c in df.columns]

    if "date" in df.columns and "time" in df.columns:
        df["time"] = pd.to_datetime(df["date"].astype(str) + " " + df["time"].astype(str))
    elif "datetime" in df.columns:
        df["time"] = pd.to_datetime(df["datetime"])
    elif "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
    else:
        raise ValueError(
            f"Nerozpoznane sloupce data/casu v {path}: {list(df.columns)}. "
            "Ocekavam MT5 export (<DATE> <TIME> ...) nebo sloupec 'datetime'."
        )

    missing = {"open", "high", "low", "close"} - set(df.columns)
    if missing:
        raise ValueError(f"Chybi OHLC sloupce {missing} v {path}. Nalezeno: {list(df.columns)}")

    df = df.set_index("time")[["open", "high", "low", "close"]].astype(float)
    df = df.sort_index()
    df.index.name = "time"
    return df


def load_generic_csv(path: str, date_col: str = "Date", time_col: str | None = None,
                      ohlc_cols=("Open", "High", "Low", "Close")) -> pd.DataFrame:
    """Pro CSV z jineho data vendora (napr. Dukascopy, HistData) - rucne uved
    nazvy sloupcu, pokud se lisi od vychozich."""
    df = pd.read_csv(path)
    if time_col:
        df["time"] = pd.to_datetime(df[date_col].astype(str) + " " + df[time_col].astype(str))
    else:
        df["time"] = pd.to_datetime(df[date_col])
    o, h, l, c = ohlc_cols
    df = df.rename(columns={o: "open", h: "high", l: "low", c: "close"})
    df = df.set_index("time")[["open", "high", "low", "close"]].astype(float)
    df = df.sort_index()
    df.index.name = "time"
    return df
