import sys, os, time
sys.path.insert(0, r"D:\Trading bot")
import research_f7_data as R
for mk in ["NAS100mini", "SPX500mini", "US30mini", "GER_30mini"]:
    p = os.path.join(r"D:\Trading bot\research_data\f7", f"{mk}_M1.pkl")
    if os.path.exists(p): print(mk, "uz je"); continue
    t0 = time.time()
    try:
        df = R.mt5_m1(mk, "2019-01-01")
        df.to_pickle(p)
        print(mk, len(df), df.t.iloc[0], df.t.iloc[-1], round(time.time()-t0), "s", flush=True)
    except Exception as e:
        print(mk, "chyba", e, flush=True)
