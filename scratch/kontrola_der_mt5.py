# Kontrola der v historii MT5 (scratch/live_mt5/*_M1.pkl): ktere pracovni dny chybi.
import glob, os, datetime as dt
import pandas as pd, numpy as np
for f in sorted(glob.glob("scratch/live_mt5/*_M1.pkl")):
    df = pd.read_pickle(f)
    if "t" in getattr(df, "columns", []):
        ts = pd.to_datetime(df["t"], unit="s")
    elif "time" in getattr(df, "columns", []):
        ts = pd.to_datetime(df["time"], unit="s") if np.issubdtype(df["time"].dtype, np.number) else pd.to_datetime(df["time"])
    else:
        ts = pd.to_datetime(df.index)
    days = pd.DatetimeIndex(ts.dt.normalize().unique() if hasattr(ts, "dt") else ts.normalize().unique())
    allb = pd.bdate_range(days.min(), days.max())
    miss = allb.difference(days)
    by = pd.Series(1, index=miss).groupby(miss.strftime("%Y-%m")).sum()
    mt = dt.datetime.fromtimestamp(os.path.getmtime(f)).strftime("%H:%M")
    print(f"{os.path.basename(f)[:-7]:11s} ulozeno {mt} od {days.min().date()} do {days.max().date()} | radku {len(df)} | dnu {len(days)} z {len(allb)} | chybi: " + ", ".join(f"{k}:{v}" for k, v in by.items()))
