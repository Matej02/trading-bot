"""
F7 - data pro test 6 strategii z dokumentu "Trading bot - 6 strategii (SMC + Volume Profile)" (2026-10-28).

Dokument chce M1 svicky za 3-4 roky s tick volume z MT5. Co jde ziskat zdarma:
  Krypto BTC/ETH/SOL: M1 z oficialnich verejnych dat Binance (data.binance.vision, mesicni zipy),
                      skutecny objem, od 2022-09.
  Forex/kovy/ropa:    MT5 terminal dava nejvys 100 000 svicek (nastaveni "Max bars in chart"),
                      takze M15 ~4 roky, M5 ~1,3 roku, M1 ~3 mesice; v historii jsou diry.
Vse se uklada do research_data/f7 jako pickle s casem v UTC (sekundy) a sloupci o,h,l,c,v.
Cas serveru brokera (GlobalDynamicMarkets) = Londyn (GMT/BST) - overeno podle otevreni tydne
(nedele 22:00 serveru = 17:00 NY v lete i v zime, 21:00 v tydnu, kdy Evropa uz ma zimni cas).
"""
import io
import os
import sys
import time
import zipfile

import numpy as np
import pandas as pd
import requests

sys.stdout.reconfigure(line_buffering=True)
OUT = os.path.join("research_data", "f7")
RAW = os.path.join(OUT, "raw")
os.makedirs(RAW, exist_ok=True)
START = pd.Timestamp("2022-09-01")
END = pd.Timestamp("2026-10-27")
CRYPTO = {"BTCUSD": "BTCUSDT", "ETHUSD": "ETHUSDT", "SOLUSD": "SOLUSDT",
          # rozsireni F7 pro vetsi vzorek tridy krypto (dokument chce BTC/ETH/SOL)
          "XRPUSD": "XRPUSDT", "BNBUSD": "BNBUSDT", "ADAUSD": "ADAUSDT", "DOGEUSD": "DOGEUSDT", "LTCUSD": "LTCUSDT",
          "LINKUSD": "LINKUSDT"}
MT5_MARKETS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "XAGUSD", "CRUDE_OIL"]


def binance_month(sym, y, m):
    path = os.path.join(RAW, f"{sym}-1m-{y}-{m:02d}.zip")
    if not os.path.exists(path):
        u = f"https://data.binance.vision/data/spot/monthly/klines/{sym}/1m/{sym}-1m-{y}-{m:02d}.zip"
        r = requests.get(u, timeout=120)
        if r.status_code != 200:
            return None
        open(path, "wb").write(r.content)
    z = zipfile.ZipFile(path)
    df = pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=range(6))
    return df


def binance_api(sym, start_ms, end_ms):
    rows, t = [], start_ms
    while t < end_ms:
        r = requests.get("https://data-api.binance.vision/api/v3/klines",
                         params={"symbol": sym, "interval": "1m", "startTime": t, "endTime": end_ms, "limit": 1000}, timeout=30).json()
        if not r:
            break
        rows += r
        t = r[-1][0] + 60_000
        time.sleep(0.1)
    return pd.DataFrame([x[:6] for x in rows])


def crypto(mk):
    sym = CRYPTO[mk]
    parts = []
    m = START
    while m < END.replace(day=1):
        df = binance_month(sym, m.year, m.month)
        if df is not None:
            parts.append(df)
            print(f"  {sym} {m:%Y-%m} {len(df)}")
        m += pd.offsets.MonthBegin(1)
    last = int(pd.Timestamp(parts[-1].iloc[-1, 0] if parts[-1].iloc[-1, 0] < 1e14 else parts[-1].iloc[-1, 0] // 1000, unit="ms").timestamp() * 1000) + 60_000
    parts.append(binance_api(sym, last, int(END.timestamp() * 1000)))
    df = pd.concat(parts, ignore_index=True)
    df.columns = ["t", "o", "h", "l", "c", "v"]
    t = df.t.astype(np.int64).to_numpy()
    t = np.where(t > 1e14, t // 1000, t) // 1000  # od 2025 Binance dava mikrosekundy
    df["t"] = t
    df = df.drop_duplicates("t").sort_values("t").reset_index(drop=True).astype({"o": float, "h": float, "l": float, "c": float, "v": float})
    return df


def mt5_bars(mk, tf_name):
    import mt5_connector as mc
    if mc.mt5.terminal_info() is None:
        mc.connect()
    mt5 = mc.mt5
    tf = {"M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15}[tf_name]
    mt5.symbol_select(mk, True)
    r = None
    for _ in range(5):
        r = mt5.copy_rates_from_pos(mk, tf, 0, 99999)
        if r is not None and len(r):
            break
        time.sleep(2)
    df = pd.DataFrame(r)
    # cas serveru = Londyn -> UTC
    srv = pd.to_datetime(df.time, unit="s").dt.tz_localize("Europe/London", ambiguous="NaT", nonexistent="shift_forward")
    df = df[srv.notna()].copy()
    df["t"] = srv[srv.notna()].dt.tz_convert("UTC").dt.tz_localize(None).astype("datetime64[s]").astype(np.int64)
    df = df.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c", "tick_volume": "v"})[["t", "o", "h", "l", "c", "v"]]
    return df.iloc[:-1].astype({"v": float}).reset_index(drop=True)


def mt5_m1(mk, start="2020-01-01"):
    """M1 z MT5 po rocich (po nastaveni "Max. sloupcu v grafu" na neomezene, 2026-10-29)."""
    import datetime as dtm
    import mt5_connector as mc
    if mc.mt5.terminal_info() is None:
        mc.connect()
    mt5 = mc.mt5
    mt5.symbol_select(mk, True)
    parts = []
    y0 = pd.Timestamp(start).year
    for y in range(y0, 2027):
        r = None
        for _ in range(5):
            r = mt5.copy_rates_range(mk, mt5.TIMEFRAME_M1, dtm.datetime(y, 1, 1), dtm.datetime(y + 1, 1, 1))
            if r is not None:
                break
            time.sleep(2)
        if r is not None and len(r):
            parts.append(pd.DataFrame(r))
    df = pd.concat(parts, ignore_index=True).drop_duplicates("time").sort_values("time")
    srv = pd.to_datetime(df.time, unit="s").dt.tz_localize("Europe/London", ambiguous="NaT", nonexistent="shift_forward")
    df = df[srv.notna()].copy()
    df["t"] = srv[srv.notna()].dt.tz_convert("UTC").dt.tz_localize(None).astype("datetime64[s]").astype(np.int64)
    df = df.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c", "tick_volume": "v"})[["t", "o", "h", "l", "c", "v"]]
    return df.iloc[:-1].astype({"v": float}).reset_index(drop=True)


def main():
    for mk in CRYPTO:
        path = os.path.join(OUT, f"{mk}_M1.pkl")
        if not os.path.exists(path):
            df = crypto(mk)
            df.to_pickle(path)
            print(mk, len(df), pd.to_datetime(df.t.iloc[0], unit="s"), pd.to_datetime(df.t.iloc[-1], unit="s"))
    if "--jen-krypto" in sys.argv:
        return
    if "--mt5-m1" in sys.argv:
        for mk in MT5_MARKETS:
            df = mt5_m1(mk)
            df.to_pickle(os.path.join(OUT, f"{mk}_M1.pkl"))
            print(mk, "M1", len(df), pd.to_datetime(df.t.iloc[0], unit="s"), pd.to_datetime(df.t.iloc[-1], unit="s"))
        return
    for mk in MT5_MARKETS:
        for tf in ("M15", "M5"):
            df = mt5_bars(mk, tf)
            df.to_pickle(os.path.join(OUT, f"{mk}_{tf}.pkl"))
            print(mk, tf, len(df), pd.to_datetime(df.t.iloc[0], unit="s"), pd.to_datetime(df.t.iloc[-1], unit="s"))


if __name__ == "__main__":
    main()
