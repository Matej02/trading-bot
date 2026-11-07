"""
Spolecne funkce pro testy F22+ (jen vyzkum, bot se nemeni).
- M1 data brokera (cas posunuty na skutecne UTC) a HistData (skutecne UTC)
- naklady brokera (spread podle hodiny, tick, swap), statistika, pravidla rozhodnuti
"""
import os
import sys

ROOT = r"D:\Trading bot"
sys.path.insert(0, ROOT)
os.chdir(ROOT)                       # f7_lib cte simulator/lib/broker.json relativne
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f7_lib as L  # noqa: E402

BRK = os.path.join(ROOT, "research_data", "f10")
HD = os.path.join(ROOT, "research_data", "histdata", "m1", "m1_skutecne_utc")
SPLIT = pd.Timestamp("2019-02-21", tz="UTC")
HD_END = pd.Timestamp("2026-01-01", tz="UTC")


def load_m1(mk, src):
    """src = 'broker' | 'hd'. Vraci DataFrame u (UTC tz-aware), o h l c."""
    path = os.path.join(BRK if src == "broker" else HD, f"{mk}_M1.pkl")
    d = pd.read_pickle(path)[["t", "o", "h", "l", "c"]].copy()
    u = pd.to_datetime(d.t, unit="s").dt.tz_localize("UTC")
    if src == "broker":   # cas serveru = UTC, data ctena jako Londyn -> v britskem letnim case +1 h
        dst = (u + pd.Timedelta(hours=1)).dt.tz_convert("Europe/London").map(lambda x: x.dst().seconds > 0).to_numpy()
        u = u + pd.to_timedelta(dst.astype(np.int64) * 3600, unit="s")
    d["u"] = u
    return d.drop(columns="t").reset_index(drop=True)


def broker_ref(mk):
    d = pd.read_pickle(os.path.join(BRK, f"{mk}_M1.pkl"))
    return float(np.median(d.c.to_numpy()[-30 * 1440:]))


def add_costs(mk, d, ref):
    """Spread (cenove jednotky) podle londynske hodiny, relativne k cene jako v testech."""
    b = L.BROKER[mk]
    sbh = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0)
    lon_h = d.u.dt.tz_convert("Europe/London").dt.hour.to_numpy()
    d["spr"] = sbh[lon_h] / ref * d.c.to_numpy()
    return 10.0 ** -b["digits"]


def daily_atr(d, tz, n=20):
    """ATR20 denniho rozpeti podle mistniho data (z predchozich n dni)."""
    loc = d.u.dt.tz_convert(tz)
    g = d.groupby(loc.dt.date)
    D = pd.DataFrame({"H": g.h.max(), "L": g.l.min(), "C": g.c.last()})
    pc = D.C.shift(1)
    tr = np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs()))
    return tr.rolling(n).mean().shift(1)


def sim(o, h, l, c, spr, tick, i, k, d, sl, tp=np.nan):
    """Obchod od otevreni svicky i do otevreni svicky k (casovy vystup). d=+1 long / -1 short.
    Data jsou bid; long kupuje za ask, short prodava za bid. SL pred TP ve stejne svicce. Vraci (R, duvod)."""
    if d == 1:
        E = o[i] + spr[i] + tick
        risk = E - sl
    else:
        E = o[i] - tick
        risk = sl - E
    if not risk > 0:
        return None
    for j in range(i, k):
        if d == 1:
            if l[j] <= sl:
                x = min(o[j], sl) - tick if j > i else sl - tick
                return (x - E) / risk, "SL"
            if tp == tp and h[j] >= tp:
                return (max(tp, o[j]) - E) / risk if j > i else (tp - E) / risk, "TP"
        else:
            if h[j] + spr[j] >= sl:
                x = max(o[j] + spr[j], sl) + tick if j > i else sl + tick
                return (E - x) / risk, "SL"
            if tp == tp and l[j] + spr[j] <= tp:
                return (E - min(tp, o[j] + spr[j])) / risk if j > i else (E - tp) / risk, "TP"
    x = o[k] - tick if d == 1 else o[k] + spr[k] + tick
    return ((x - E) if d == 1 else (E - x)) / risk, "cas"


def st(R):
    R = np.asarray(R, float)
    n = len(R)
    if n < 2:
        return dict(n=n, m=np.nan, t=np.nan, win=np.nan, pf=np.nan)
    g, b = R[R > 0].sum(), -R[R < 0].sum()
    return dict(n=n, m=R.mean(), t=R.mean() / R.std(ddof=1) * np.sqrt(n), win=(R > 0).mean(), pf=g / b if b > 0 else np.inf)


def fmt(s):
    return (f"n {s['n']:5d} | {s['m']:+.3f} R | t {s['t']:+.2f} | PF {s['pf']:.2f} | výhra {s['win']:.0%}"
            if s["n"] >= 2 else f"n {s['n']}")


def decide(say, dev, kon, others, dev_rnd, kon_rnd, second):
    c = [("1) vývoj > 0 a t >= 2,0", dev["m"] > 0 and dev["t"] >= 2.0, f"{dev['m']:+.3f} R, t {dev['t']:+.2f}"),
         ("2) kontrola > 0 a t >= 1,5", kon["m"] > 0 and kon["t"] >= 1.5, f"{kon['m']:+.3f} R, t {kon['t']:+.2f}"),
         ("3) jiné trhy vše > 0", all(v["m"] > 0 for v in others.values()),
          ", ".join(f"{k} {v['m']:+.3f}" for k, v in others.items())),
         ("4) lepší než náhoda (vývoj i kontrola)", dev["m"] > dev_rnd["m"] and kon["m"] > kon_rnd["m"],
          f"{dev['m']:+.3f} vs {dev_rnd['m']:+.3f}; {kon['m']:+.3f} vs {kon_rnd['m']:+.3f}"),
         ("5) druhý zdroj > 0", second["m"] > 0, f"{second['m']:+.3f} R")]
    for name, ok, val in c:
        say(f"   {name}: {'ANO' if ok else 'NE'} ({val})")
    ok = all(x[1] for x in c)
    say(f"   => {'VÝHODA (prošlo vše)' if ok else 'BEZ VÝHODY'}")
    return ok
