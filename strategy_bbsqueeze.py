"""
Strategie: Bollinger Band squeeze breakout.

Logika:
- Po obdobi stazeneho rozpeti (nizka volatilita, Bollinger pasma blizko
  sebe - nejuzsich 25 % za poslednich 100 baru) casto nasleduje vyrazny
  pohyb. Obchodujeme smer prvniho prorazeni pasma po takovem squeeze.
- Session filter (13:00-17:00 UTC) a ATR-based SL/TP prevzate ze
  strategy.py - stejne osvedcene principy, jina vstupni logika.

Validace (viz README.md): walk-forward 5 nezavislych ~23mesicnich obdobi
na EURUSD - pozitivni profit factor ve 4 z 5. Na AUDJPY jeste
konzistentneji (4/5, nikdy pod 0.96). Na vetsine ostatnich testovanych
paru neprokazalo spolehlivou edge - nepouzivat mimo EURUSD/AUDJPY bez
dalsi validace.
"""

import pandas as pd
from strategy import in_session, compute_sl_tp

BB_PERIOD = 20
BB_STD = 2.0
SQUEEZE_LOOKBACK = 100
SQUEEZE_PERCENTILE = 0.25  # bandwidth musi byt v nejuzsich 25 % za posledních 100 baru


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    df["atr_median"] = df["atr"].rolling(100).median()

    mid = df["close"].rolling(BB_PERIOD).mean()
    std = df["close"].rolling(BB_PERIOD).std()
    df["bb_upper"] = mid + BB_STD * std
    df["bb_lower"] = mid - BB_STD * std
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / mid
    df["bb_width_rank"] = df["bb_width"].rolling(SQUEEZE_LOOKBACK).rank(pct=True)
    return df


def generate_signal(row, prev_row) -> str | None:
    if pd.isna(row["bb_width_rank"]) or pd.isna(row["atr_median"]):
        return None
    if not in_session(row.name):
        return None

    was_squeezed = prev_row["bb_width_rank"] <= SQUEEZE_PERCENTILE
    if not was_squeezed:
        return None

    if row["close"] > row["bb_upper"]:
        return "long"
    if row["close"] < row["bb_lower"]:
        return "short"
    return None
