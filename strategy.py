"""
Strategie: trend-following pullback na H1.

Logika (vedoma volba, ne nahodna):
- Trend filter: EMA50 vs EMA200 - obchodujeme jen ve smeru dlouhodobeho trendu.
  Duvod: snizuje pocet falesnych signalu v protitrendovych whipsaws.
- Trigger vstupu: cena se stahne k EMA20 (pullback) a pak zavre svicku
  zpet ve smeru trendu -> potvrzeni, ze pullback skoncil.
- Volatility filter: ATR musi byt nad minimem (jinak trh "spi" a spready
  relativne k pohybu jsou moc velke).
- Session filter: obchodujeme jen London/NY prekryv (13:00-17:00 UTC),
  kdy je nejvyssi likvidita a nejuzsi spready.
- SL: 1.5x ATR od vstupu (dava strategii prostor na normalni sum trhu).
- TP: 2.5x ATR od vstupu (risk:reward cca 1:1.67 - nemusime mit
  vysoky winrate, aby to bylo dlouhodobe ziskove).

Tohle NENI zaruceny edge. Je to rozumne, vysvetlitelne pravidlo,
jehoz skutecnou vykonnost overime backtestem na realnych datech.
"""

import pandas as pd
import numpy as np


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()

    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    df["atr_median"] = df["atr"].rolling(100).median()
    return df


def in_session(ts) -> bool:
    return 13 <= ts.hour < 17


def generate_signal(row, prev_row) -> str | None:
    """Vraci 'long', 'short' nebo None pro danou svicku."""
    if pd.isna(row["ema200"]) or pd.isna(row["atr_median"]):
        return None
    if row["atr"] < 0.6 * row["atr_median"]:
        return None  # trh moc klidny, preskocit
    if not in_session(row.name):
        return None

    uptrend = row["ema50"] > row["ema200"]
    downtrend = row["ema50"] < row["ema200"]

    # pullback k ema20 a zavreni zpet ve smeru trendu
    pulled_back_up = prev_row["low"] <= prev_row["ema20"] and row["close"] > row["ema20"]
    pulled_back_down = prev_row["high"] >= prev_row["ema20"] and row["close"] < row["ema20"]

    if uptrend and pulled_back_up and row["close"] > row["open"]:
        return "long"
    if downtrend and pulled_back_down and row["close"] < row["open"]:
        return "short"
    return None


def compute_sl_tp(entry_price: float, atr: float, direction: str):
    sl_dist = 1.5 * atr
    tp_dist = 2.5 * atr
    if direction == "long":
        return entry_price - sl_dist, entry_price + tp_dist
    else:
        return entry_price + sl_dist, entry_price - tp_dist
