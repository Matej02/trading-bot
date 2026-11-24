# Diry v H1 historii runneru (scratch/live_mt5/research_data/*_H1.pkl)
import glob, os, datetime as dt
import pandas as pd
for f in sorted(glob.glob("scratch/live_mt5/research_data/*_H1.pkl")):
    df = pd.read_pickle(f)
    idx = pd.DatetimeIndex(df.index if not "time" in getattr(df,"columns",[]) else pd.to_datetime(df["time"]))
    days = idx.normalize().unique()
    allb = pd.bdate_range(days.min(), days.max())
    miss = allb.difference(days)
    by = pd.Series(1, index=miss).groupby(miss.strftime("%Y-%m")).sum()
    mt = dt.datetime.fromtimestamp(os.path.getmtime(f)).strftime("%d.%m %H:%M")
    print(f"{os.path.basename(f)[:-7]:11s} {mt} od {days.min().date()} | radku {len(df)} | dnu {len(days)} z {len(allb)} | chybi: " + ", ".join(f"{k}:{v}" for k, v in by.items() if v > 2))
