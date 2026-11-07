"""
F13 na delsi historii - prevod HistData M1 (zip) do formatu testu (t UTC s, o h l c v) + kontrola casoveho pasma.
Spusteni: python -I f13_hist_prevod.py <slozka se zipy> <vystupni slozka> <slozka M1 brokera>
Nic v runneru ani ve vyzkumnem kodu nemeni.
"""
import os
import sys
import zipfile

import numpy as np
import pandas as pd

ZIP, OUT, BRK = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
PAIRS = {"SPXUSD": "SPX500mini", "NSXUSD": "NAS100mini"}


def read_pair(p):
    fr = []
    for f in sorted(os.listdir(ZIP)):
        if f"_{p}_M1" not in f or not f.endswith(".zip"):
            continue
        z = zipfile.ZipFile(os.path.join(ZIP, f))
        csv = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        with z.open(csv) as fh:
            d = pd.read_csv(fh, sep=";", header=None, names=["ts", "o", "h", "l", "c", "v"], dtype={"ts": str})
        fr.append(d)
    d = pd.concat(fr, ignore_index=True)
    d["local"] = pd.to_datetime(d.ts, format="%Y%m%d %H%M%S")
    return d.drop(columns="ts")


def to_utc(d, how):
    if how == "EST pevne (UTC-5)":
        u = d.local + pd.Timedelta(hours=5)
    else:
        u = d.local.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC").dt.tz_localize(None)
    return u


for p, mk in PAIRS.items():
    d = read_pair(p)
    b = pd.read_pickle(os.path.join(BRK, f"{mk}_M1.pkl"))
    b["u"] = pd.to_datetime(b.t, unit="s")
    print(f"{mk}: HistData {len(d):,} svicek {d.local.min()} -> {d.local.max()} | objem nenulovy: {(d.v != 0).sum()}")
    best = None
    for how in ("EST pevne (UTC-5)", "New York s letnim casem"):
        u = to_utc(d, how)
        h = pd.DataFrame({"u": u, "c": d.c}).dropna().drop_duplicates("u")
        for per in (("2023-01-09", "2023-02-10"), ("2023-07-10", "2023-08-11")):   # zima a leto
            x = h[(h.u >= per[0]) & (h.u < per[1])].set_index("u").c
            y = b[(b.u >= per[0]) & (b.u < per[1])].set_index("u").c
            j = pd.concat([x.rename("h"), y.rename("b")], axis=1).dropna()
            r = j.pct_change().dropna()
            corr = r.h.corr(r.b)
            print(f"   {how:24s} {per[0][:7]}: spolecnych minut {len(j):6d}, korelace 1m vynosu {corr:.3f}, "
                  f"pomer cen brokera/HistData median {np.median(j.b / j.h):.4f}")
            if per[0].startswith("2023-07"):
                if best is None or corr > best[1]:
                    best = (how, corr)
    # HistData = newyorsky cas vcetne letniho (otevreni burzy 9:30 v obou obdobich). Skutecne UTC = NY -> UTC.
    # Data brokera v testu i v runneru: cas serveru (= UTC i v lete) se cte jako Londyn -> v britskem letnim case o 1 h driv.
    u = to_utc(d, "New York s letnim casem")
    ok = u.notna().values
    true_t = u[ok].values.astype("datetime64[s]").astype(np.int64)
    lon_dst = (pd.to_datetime(true_t, unit="s").tz_localize("UTC").tz_convert("Europe/London").map(lambda x: x.dst().seconds) > 0)
    base = pd.DataFrame({"o": d.o[ok].values, "h": d.h[ok].values, "l": d.l[ok].values, "c": d.c[ok].values}).astype(float)
    base["v"] = 1.0                               # HistData nema objem -> konstanta (podminka objemu v MSS nikdy neplati)
    for sub, t in (("m1_jako_broker", true_t - 3600 * np.asarray(lon_dst, dtype=np.int64)), ("m1_skutecne_utc", true_t)):
        o = base.assign(t=t)[["t", "o", "h", "l", "c", "v"]].drop_duplicates("t").sort_values("t").reset_index(drop=True)
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
        o.to_pickle(os.path.join(OUT, sub, f"{mk}_M1.pkl"))
        print(f"   -> {sub}: {len(o):,} svicek {pd.Timestamp(o.t.iloc[0], unit='s')} -> {pd.Timestamp(o.t.iloc[-1], unit='s')}")
