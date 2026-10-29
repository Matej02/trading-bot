import sys, os, time, shutil
sys.path.insert(0, r"D:\Trading bot")
import research_f7_data as R
D = r"D:\Trading bot\research_data\f10"
for mk in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "XAUUSD", "XAGUSD", "CRUDE_OIL"]:
    p = os.path.join(D, f"{mk}_M1.pkl")
    if os.path.exists(p): continue
    df = R.mt5_m1(mk, "2017-01-01"); df.to_pickle(p)
    print(mk, len(df), df.t.iloc[0], df.t.iloc[-1], flush=True)
for mk in ["NAS100mini", "SPX500mini", "US30mini", "GER_30mini"]:
    shutil.copy(os.path.join(r"D:\Trading bot\research_data\f7", f"{mk}_M1.pkl"), os.path.join(D, f"{mk}_M1.pkl"))
for mk in ["BTCUSD", "ETHUSD"]:
    shutil.copy(os.path.join(r"D:\Trading bot\research_data\f7", f"{mk}_M1.pkl"), os.path.join(D, f"{mk}_M1.pkl"))
