"""F71 londynsky pruraz (asijske rozpeti) a F72 vikendovy gap na menach. Plan predem:
znalosti/Vyzkum/F71 a F72 Londynsky pruraz a vikendovy gap na menach.md (commit d72a628). Pravidla se po vysledku nemeni."""
import json
import os

import numpy as np
import pandas as pd

RD = r"D:\Trading bot\research_data"
OUT = os.path.join(RD, "f71")
os.makedirs(OUT, exist_ok=True)
COST = {k: v["naklad"] for k, v in json.load(open(os.path.join(RD, "naklady.json"))).items()}

MAIN71 = ["EURUSD", "GBPUSD"]
OTHER71 = ["USDJPY", "EURJPY", "GBPJPY", "AUDUSD", "EURGBP", "USDCHF", "USDCAD", "NZDUSD", "AUDJPY", "EURCHF"]
MAIN72 = ["EURUSD", "GBPUSD", "USDJPY", "EURJPY", "GBPJPY", "AUDUSD", "EURGBP", "USDCHF", "USDCAD", "NZDUSD", "AUDJPY", "EURCHF"]
OTHER72 = ["XAUUSD", "XAGUSD", "EURAUD", "EURCAD", "GBPAUD", "GBPCAD", "AUDCAD", "AUDNZD", "NZDJPY", "CADJPY"]
HD = ["EURUSD", "GBPUSD", "USDJPY"]


def broker(mk):
    d = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))[["open", "high", "low", "close"]].astype(float)
    d.index = pd.DatetimeIndex(d.index).tz_localize("UTC")
    d = d[d.index >= "2010-01-01"]
    return d


def histdata(mk):
    d = pd.read_pickle(os.path.join(RD, "histdata", "m1_fx", f"{mk}.pkl"))[["open", "high", "low", "close"]].astype(float)
    return d


def f71(d, cost, m1):
    lon = d.index.tz_convert("Europe/London")
    hr = lon.hour.to_numpy()
    day = lon.normalize().tz_localize(None).to_numpy()
    hi, lo, cl = d.high.to_numpy(), d.low.to_numpy(), d.close.to_numpy()
    res = []
    starts = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
    ends = np.r_[starts[1:], len(day)]
    for s, e in zip(starts, ends):
        dt = pd.Timestamp(day[s])
        if dt.day_of_week > 4:
            continue
        h = hr[s:e]
        asia = h <= 6
        if m1:
            if len(np.unique(h[asia])) < 7:
                continue
        elif asia.sum() != 7:
            continue
        rh, rl = hi[s:e][asia].max(), lo[s:e][asia].min()
        R = rh - rl
        if R < 5 * cost:
            continue
        man = (h >= 7) & (h <= 15)
        idx = np.flatnonzero(man)
        if len(idx) == 0:
            continue
        H, L, C, hh = hi[s:e][idx], lo[s:e][idx], cl[s:e][idx], h[idx]
        win = hh <= 11
        up = np.flatnonzero((H >= rh) & win)
        dn = np.flatnonzero((L <= rl) & win)
        if len(up) == 0 and len(dn) == 0:
            continue
        iu = up[0] if len(up) else 10**9
        idn = dn[0] if len(dn) else 10**9
        if iu == idn:
            g = -1.0
        else:
            k = min(iu, idn)
            if iu < idn:
                sl, tp, entry, dr = rl, rh + R, rh, 1
                slh, tph = L <= sl, H >= tp
            else:
                sl, tp, entry, dr = rh, rl - R, rl, -1
                slh, tph = H >= sl, L <= tp
            if slh[k]:
                g = -1.0
            else:
                a = np.flatnonzero(slh[k + 1:])
                b = np.flatnonzero(tph[k + 1:])
                ia = a[0] if len(a) else 10**9
                ib = b[0] if len(b) else 10**9
                if ia == 10**9 and ib == 10**9:
                    g = dr * (C[-1] - entry) / R
                elif ia <= ib:
                    g = -1.0
                else:
                    g = 1.0
        res.append((dt, g, g - cost / R))
    return pd.DataFrame(res, columns=["den", "hrube", "cista"]).set_index("den")


def f72(d, cost, m1):
    t = d.index
    sec = (t.tz_convert("UTC").tz_localize(None).astype("datetime64[s]").astype(np.int64)).to_numpy()
    gap_at = np.flatnonzero(np.diff(sec) > 24 * 3600)
    o, hi, lo, cl = d.open.to_numpy(), d.high.to_numpy(), d.low.to_numpy(), d.close.to_numpy()
    # ATR20 z dennich svicek UTC
    dd = d.groupby(t.tz_convert("UTC").normalize()).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    dd = dd[dd.index.dayofweek < 5]
    pc = dd.close.shift(1)
    tr = np.maximum(dd.high - dd.low, np.maximum((dd.high - pc).abs(), (dd.low - pc).abs()))
    atr = tr.rolling(20).mean()
    res = []
    for i in gap_at:
        tf, tn = t[i], t[i + 1]
        if tf.dayofweek != 4 or tn.dayofweek not in (6, 0):
            continue
        fday = tf.normalize()
        if fday not in atr.index or not np.isfinite(atr[fday]):
            continue
        fc, op = cl[i], o[i + 1]
        gap = op - fc
        if abs(gap) < 0.25 * atr[fday]:
            continue
        R = abs(gap)
        dr = -1 if gap > 0 else 1                 # proti gapu
        tp, sl = fc, op - dr * R
        j1 = i + 1
        j2 = np.searchsorted(sec, sec[j1] + 24 * 3600, side="left")   # svicky do 24 h od otevreni
        H, L = hi[j1:j2], lo[j1:j2]
        if dr == 1:
            slh, tph = L <= sl, H >= tp
        else:
            slh, tph = H >= sl, L <= tp
        a = np.flatnonzero(slh)
        b = np.flatnonzero(tph)
        ia = a[0] if len(a) else 10**9
        ib = b[0] if len(b) else 10**9
        if ia == 10**9 and ib == 10**9:
            g = dr * (cl[j2 - 1] - op) / R
        elif ia <= ib:
            g = -1.0
        else:
            g = 1.0
        res.append((tn.tz_convert("UTC").tz_localize(None), g, g - 3 * cost / R))
    return pd.DataFrame(res, columns=["den", "hrube", "cista"]).set_index("den")


def stat(x):
    x = np.asarray(x, float)
    n = len(x)
    if n < 2:
        return n, np.nan, np.nan
    return n, x.mean(), x.mean() / (x.std(ddof=1) / np.sqrt(n))


def fmt(nm, x):
    n, m, tt = stat(x)
    return f"{nm:32s} n {n:5d} | prumer {m:+.3f} R | t {tt:+.2f}"


def report(name, fn, main, other, hd):
    lines = [f"===== {name} ====="]
    per = {mk: fn(broker(mk), COST[mk], False) for mk in main + other}
    M = pd.concat([per[mk] for mk in main])
    dev = M[M.index < "2019-01-01"]
    ctl = M[M.index >= "2019-01-01"]
    lines += [fmt("vyvoj 2010-18 hrube", dev.hrube), fmt("vyvoj 2010-18 ciste", dev.cista),
              fmt("kontrola 2019-26 hrube", ctl.hrube), fmt("kontrola 2019-26 ciste", ctl.cista)]
    for mk in main:
        lines.append("  " + fmt(f"{mk} cele ciste", per[mk].cista))
    hdr = {mk: fn(histdata(mk), COST[mk], True) for mk in hd}
    H = pd.concat(hdr.values())
    lines.append(fmt("HistData M1 2010-25 ciste", H.cista))
    for mk in hd:
        lines.append("  " + fmt(f"HistData {mk} ciste", hdr[mk].cista))
    pos = 0
    O = []
    for mk in other:
        lines.append("  " + fmt(f"jiny trh {mk} ciste", per[mk].cista))
        pos += per[mk].cista.mean() > 0
        O.append(per[mk].cista)
    O = pd.concat(O)
    lines.append(fmt("jine trhy dohromady ciste", O) + f" | kladnych {pos}/{len(other)}")
    yr = M.cista.groupby(M.index.year).mean()
    lines.append("roky (hlavni, ciste): " + ", ".join(f"{y}:{v:+.3f}" for y, v in yr.items()) + f" | kladnych {(yr > 0).mean():.0%}")
    n1, m1_, t1 = stat(dev.cista)
    n2, m2, t2 = stat(ctl.cista)
    return lines, dict(dev=(m1_, t1), ctl=(m2, t2), hd=H.cista.mean(), other=(O.mean(), pos, len(other)), years=(yr > 0).mean())


if __name__ == "__main__":
    out = []
    l71, r71 = report("F71 londynsky pruraz", f71, MAIN71, OTHER71, ["EURUSD", "GBPUSD"])
    v71 = [r71["dev"][0] > 0 and r71["dev"][1] >= 2.0, r71["ctl"][0] > 0 and r71["ctl"][1] >= 1.5, r71["hd"] > 0,
           r71["other"][0] > 0 and r71["other"][1] >= 6, r71["years"] >= 0.55]
    l71.append("BODY 1-5: " + " ".join("ANO" if v else "ne" for v in v71) + f" -> VERDIKT {'ANO' if all(v71) else 'NE'}")
    out += l71
    l72, r72 = report("F72 vikendovy gap", f72, MAIN72, OTHER72, HD)
    v72 = [r72["dev"][0] > 0 and r72["dev"][1] >= 2.0, r72["ctl"][0] > 0 and r72["ctl"][1] >= 1.5, r72["hd"] > 0,
           r72["other"][0] > 0 and r72["other"][1] >= 0.55 * r72["other"][2], r72["years"] >= 0.55]
    l72.append("BODY 1-5: " + " ".join("ANO" if v else "ne" for v in v72) + f" -> VERDIKT {'ANO' if all(v72) else 'NE'}")
    out += l72
    txt = "\n".join(out)
    print(txt)
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(txt + "\n")
