"""
Trendove momentum napric 40 trhy (F1, rodina A, varianta L=250).

STAV: NEOVERENO. Na holdoutu 2023+ po vsech nakladech PF 0.98, t +0.01
(neproslo). Hrube ma edge (t 3.3), polovina je urok za drzeni, zbytek sebere
swap brokera. Do bota je zapojene jen pro papirovy test dopredu (README, F1).

Pravidlo (stejne jako v research_f1.py):
  - pozice = znamenko vynosu za poslednich 250 obchodnich dni (long / short)
  - meni se jen pri zmene znamenka, jinak se drzi - zadny TP
  - velikost: stejne riziko na kazdem trhu (1 / denni volatilita za 60 dni)

Data pro signal: Yahoo Finance (zdarma). Historie u brokera ma diry (vsude
chybi 2025-10-06..2026-02-10 a 2026-06-15..2026-08-11, EURUSD skoro cely
rok), takze cena pred rokem tam neni. Obchoduje se dal pres MT5.

Odchylky od testu (vedome):
  - signal z posledni UZAVRENE denni svicky Yahoo (zpozdeni < 1 den), test
    bral cenu brokera v hodine rozhodnuti
  - pojistny SL 10 dennich sigma od vstupu - v testu zadny SL nebyl, ma jen
    chranit ucet pred katastrofou (gap, chyba dat)
"""

import numpy as np
import pandas as pd

SETUP = "momentum_d1_L250"
MAGIC = 20261027
LOOKBACK = 250
VOL_WINDOW = 60
DISASTER_SL_SIGMA = 10
PORTFOLIO_DAILY_VOL_PCT = 0.5     # cilova denni volatilita celeho portfolia v % uctu

# 40 trhu, ktere v research_f1.py prosly filtrem nakladu (spread <= 5 % denniho rozsahu)
YAHOO = {
    "SPX500mini": "^GSPC", "US30mini": "^DJI", "NAS100mini": "^NDX", "GER_30mini": "^GDAXI",
    "GBR_100mini": "^FTSE", "FRA_40mini": "^FCHI", "EUR_50mini": "^STOXX50E", "ESP_35mini": "^IBEX",
    **{fx: f"{fx}=X" for fx in (
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY",
        "CADJPY", "CHFJPY", "NZDJPY", "AUDJPY", "EURCAD", "GBPNZD", "USDTRY", "GBPTRY", "EURTRY",
        "USDNOK", "EURNOK", "GBPNOK", "USDSEK", "USDZAR", "EURZAR")},
    "XAUUSD": "GC=F", "GAUUSD": "GC=F", "XPTUSD": "PL=F", "XAGUSD": "SI=F",
    "CRUDE_OIL": "CL=F", "BRENT_OIL": "BZ=F", "BTCUSD": "BTC-USD", "ETHUSD": "ETH-USD",
}
UNIVERSE = list(YAHOO)
US_INDEX = {"SPX500mini", "US30mini", "NAS100mini"}
CRYPTO = {"BTCUSD", "ETHUSD"}       # Yahoo ma i vikendy -> jen pracovni dny, at 250 svicek = cca rok


def decision_hour(sym):
    """Hodina (UTC), kdy se obchoduje - likvidni, mimo rollover. Stejne jako v testu."""
    return 19 if sym in US_INDEX else 15


def fetch_daily(symbols, period="2y"):
    """Uzavrene denni close z Yahoo pro dane MT5 symboly -> {symbol: Series}.
    Dnesni (rozpracovana) svicka se zahodi. Kdyz Yahoo neodpovi, vraci {}."""
    import yfinance as yf

    tickers = sorted({YAHOO[s] for s in symbols})
    raw = yf.download(tickers, period=period, interval="1d", progress=False, auto_adjust=False)
    if raw is None or raw.empty:
        return {}
    close = raw["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    today = pd.Timestamp.now(tz="UTC").tz_localize(None).normalize()
    out = {}
    for s in symbols:
        c = close[YAHOO[s]].dropna()
        c.index = pd.to_datetime(c.index).tz_localize(None).normalize()
        c = c[c.index < today]
        if s in CRYPTO:
            c = c[c.index.weekday < 5]
        out[s] = c
    return out


def target(close):
    """+1 / -1 podle znamenka vynosu za LOOKBACK obchodnich dni, 0 = malo dat."""
    if len(close) < LOOKBACK + 1:
        return 0
    return int(np.sign(close.iloc[-1] / close.iloc[-1 - LOOKBACK] - 1))


def rel_vol(close):
    """Denni volatilita jako podil ceny (std dennich zmen za VOL_WINDOW dni)."""
    return float(close.pct_change().iloc[-VOL_WINDOW:].std())


def risk_pct(n_markets=len(UNIVERSE)):
    """Riziko na trh (v % uctu) pri pojistnem SL. Na kazdy trh pripada stejny dil
    cilove volatility portfolia: 1 denni sigma = PORTFOLIO_DAILY_VOL_PCT / sqrt(N)."""
    return PORTFOLIO_DAILY_VOL_PCT / np.sqrt(n_markets) * DISASTER_SL_SIGMA


def disaster_sl(price, direction, vol):
    d = DISASTER_SL_SIGMA * vol * price
    return price - d if direction == "long" else price + d
