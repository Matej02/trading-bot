"""
F82 vikendovy pohyb bitcoinu (navrat k patku), F83 slaby mesic -> long dalsi mesic, F84 sude tydny cyklu FOMC.
Plan predem ve vaultu: Vyzkum/F82 az F84 Vikend bitcoinu, slaby mesic a cyklus FOMC.md (commit 6c95890).
Spusteni: python -I f82_f84.py -> D:\\Trading bot\\research_data\\f82\\souhrn.txt
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import f73_f78 as T  # noqa: E402

LB, L = F.LB, F.L
RD = F.RD
OUT = os.path.join(RD, "f82")
os.makedirs(OUT, exist_ok=True)
SPLIT = pd.Timestamp("2019-01-01")
US = ["SPX500mini", "NAS100mini", "US30mini"]
EU = ["GER_30mini", "GBR_100mini", "FRA_40mini"]
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def stat(x):
    x = np.asarray(x, float)
    n = len(x)
    if n < 2:
        return n, np.nan, np.nan
    return n, x.mean(), x.mean() / (x.std(ddof=1) / np.sqrt(n))


def fmt(nm, x):
    n, m, t = stat(x)
    return f"{nm:30s} n {n:5d} | prumer {m:+.3f} R | t {t:+.2f}"


# ------------------------------------------------------------------ F82
def crypto_cost(mk, price):
    b = L.BROKER.get(mk)
    if b is None:
        bb = L.BROKER["BTCUSD"]
        return 0.003 * price, bb["swapLong"], bb["swapShort"]
    return float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0), b["swapLong"], b["swapShort"]


def f82(h, mk):
    h = h[["open", "high", "low", "close"]].astype(float).copy()
    h.index = pd.DatetimeIndex(h.index)
    if h.index.tz is not None:
        h.index = h.index.tz_convert("UTC").tz_localize(None)
    g = h.groupby(h.index.normalize())
    dd = pd.DataFrame({"high": g.high.max(), "low": g.low.min(), "close": g.close.last()})
    pc = dd.close.shift(1)
    atr = np.maximum(dd.high - dd.low, np.maximum((dd.high - pc).abs(), (dd.low - pc).abs())).rolling(20).mean()
    t = h.index
    pos = pd.Series(np.arange(len(h)), index=t)
    fri = t[(t.dayofweek == 4) & (t.hour == 20)]
    hi, lo, cl, op = h.high.to_numpy(), h.low.to_numpy(), h.close.to_numpy(), h.open.to_numpy()
    sec = t.astype("datetime64[s]").astype(np.int64)
    rows = []
    for tf in fri:
        ts = tf + pd.Timedelta(hours=51)                       # nedele 23:00
        if ts not in pos.index or tf.normalize() not in atr.index or not np.isfinite(atr[tf.normalize()]):
            continue
        i, j = pos[tf], pos[ts]
        fc, E = cl[i], op[j]
        W = E - fc
        if abs(W) < 0.5 * atr[tf.normalize()] or W == 0:
            continue
        R = abs(W)
        dr = -1 if W > 0 else 1
        tp, sl = fc, E - dr * R
        j2 = np.searchsorted(sec, sec[j] + 120 * 3600, side="left")
        H, Lo = hi[j:j2], lo[j:j2]
        slh, tph = (Lo <= sl, H >= tp) if dr == 1 else (H >= sl, Lo <= tp)
        a, b = np.flatnonzero(slh), np.flatnonzero(tph)
        ia = a[0] if len(a) else 10**9
        ib = b[0] if len(b) else 10**9
        if ia == 10**9 and ib == 10**9:
            k, gr = j2 - 1, dr * (cl[j2 - 1] - E) / R
        elif ia <= ib:
            k, gr = j + ia, -1.0
        else:
            k, gr = j + ib, 1.0
        spread, swl, sws = crypto_cost(mk, E)
        nights = max(1, int(np.ceil((sec[k] - sec[j] + 3600) / 86400)))
        swap = (swl if dr == 1 else sws) * E * nights           # zaporne = naklad
        rows.append((ts, gr, gr + (-spread + swap) / R))
    return pd.DataFrame(rows, columns=["den", "hrube", "cista"]).set_index("den")


def run_f82():
    say("=" * 100)
    say("F82 vikendovy pohyb bitcoinu: |W| >= 0,5 ATR20 -> proti pohybu k patecni cene, stop 1:1, nejdele 120 h")
    btc = f82(pd.read_pickle(os.path.join(RD, "BTCUSD_H1.pkl")), "BTCUSD")
    dev, kon = btc[(btc.index >= "2012-01-01") & (btc.index < SPLIT)], btc[btc.index >= SPLIT]
    bn = f82(pd.read_pickle(os.path.join(RD, "binance_BTCUSDT_1h.pkl")), "BTCUSD")
    say(fmt("vyvoj broker 2012-18 hrube", dev.hrube))
    say(fmt("vyvoj broker 2012-18 ciste", dev.cista))
    say(fmt("kontrola broker 2019-26 hrube", kon.hrube))
    say(fmt("kontrola broker 2019-26 ciste", kon.cista))
    say(fmt("Binance 2019-26 ciste", bn.cista))
    pos = 0
    for mk in ("ETHUSD", "LTCUSD", "XRPUSD"):
        o = f82(pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl")), mk)
        say("  " + fmt(f"{mk} ciste", o.cista))
        pos += o.cista.mean() > 0
    full = btc[btc.index >= "2012-01-01"]
    yr = full.cista.groupby(full.index.year).mean()
    say("roky: " + ", ".join(f"{y}:{v:+.2f}" for y, v in yr.items()) + f" | kladnych {(yr > 0).mean():.0%}")
    n1, m1, t1 = stat(dev.cista)
    n2, m2, t2 = stat(kon.cista)
    c = [m1 > 0 and t1 >= 2.0, m2 > 0 and t2 >= 1.5, bn.cista.mean() > 0, pos >= 2, (yr > 0).mean() >= 0.55]
    say("BODY 1-5: " + " ".join("ANO" if x else "ne" for x in c) + f"  => {'VYHODA (proslo vse)' if all(c) else 'BEZ VYHODY'}")
    return "F82 vikend bitcoinu", sum(c), all(c)


# ------------------------------------------------------------------ F83 a F84 (indexy, standardnich 5 bodu)
def monthly_run(mk, d):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    pc = d.close.shift(1)
    atr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean()
    groups = [g for _, g in d.groupby(d.index.to_period("M"))]
    mret = [np.nan] + [groups[k].close.iloc[-1] / groups[k - 1].close.iloc[-1] - 1 for k in range(1, len(groups))]
    rs, rb = [], []
    for k in range(1, len(groups)):
        g = groups[k]
        e, x = g.index[0], g.index[-1]
        i = d.index.get_loc(e)
        if i < 21 or not atr.iloc[i - 1] > 0 or len(g) < 15:
            continue
        E, X = g.open.iloc[0], g.close.iloc[-1]
        risk = 3 * atr.iloc[i - 1]
        net = ((X - E) - rel * (E + X) / 2 + b["swapLong"] * E * F.nights(e, x)) / risk
        rb.append((e, net))
        hist = [v for v in mret[max(1, k - 1 - 120):k - 1] if np.isfinite(v)]
        prev = mret[k - 1]
        if len(hist) >= 60 and np.isfinite(prev) and prev <= np.quantile(hist, 0.2):
            rs.append((e, net))
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


K = json.load(open(os.path.join(RD, "kalendar_2010_2021.json")))
FOMC = sorted({pd.Timestamp(x) for x in K["FOMC"] + [x for x in L.FOMC if x >= "2021-09-01"]})


def fomc_flags(mk, d):
    """Signal na dni pred zacatkem okna (vstup na otevreni prvniho dne okna)."""
    idx = d.index
    j0s = [int(np.searchsorted(idx, f)) for f in FOMC]
    flags = np.zeros(len(idx), bool)
    for q, j0 in enumerate(j0s):
        if j0 >= len(idx):
            continue
        nxt = j0s[q + 1] - 1 if q + 1 < len(j0s) else len(idx)
        for a, b in ((-1, 3), (9, 13), (19, 23), (29, 33)):
            s, e = j0 + a, j0 + b
            if e < nxt and s - 1 >= 0 and e < len(idx):
                flags[s - 1] = True
    return flags


def evaluate_pairs(pairs, a, b):
    s = pd.concat([p[0] for p in pairs]).groupby("day").R.mean()
    bb = pd.concat([p[1] for p in pairs]).groupby("day").R.mean()
    sel = lambda x: x[(x.index >= pd.Timestamp(a)) & ((x.index < pd.Timestamp(b)) if b is not None else True)]  # noqa: E731
    s, bb = sel(s), sel(bb)
    diff, t = F.welch(s, bb) if len(s) > 1 else (np.nan, np.nan)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


def five_points(name, runner, dev0):
    say("=" * 100)
    say(name)
    Y = [runner(mk, F.yahoo(mk)) for mk in US]
    Bk = [runner(mk, F.broker(mk)) for mk in US]
    R = {"vyvoj": evaluate_pairs(Y, dev0, SPLIT), "kontrola": evaluate_pairs(Y, SPLIT, None), "broker": evaluate_pairs(Bk, SPLIT, None)}
    for k, v in R.items():
        say(f"{k:9s} signal:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnani: {LB.fmt(v['base'])}")
        say(f"{'':9s} previs {v['diff']:+.3f} R, t {v['t']:+.2f}")
    O = {mk: evaluate_pairs([runner(mk, F.yahoo(mk))], dev0, None) for mk in EU}
    for mk, v in O.items():
        say(f"{mk:11s}: signal {LB.fmt(v['sig'])} | previs {v['diff']:+.3f}, t {v['t']:+.2f}")
    full = evaluate_pairs(Y, dev0, None)
    pos, line = [], []
    for y in sorted(set(full["s"].index.year)):
        sy, by = full["s"][full["s"].index.year == y], full["b"][full["b"].index.year == y]
        if len(sy) and len(by):
            pos.append(sy.mean() - by.mean() > 0)
            line.append(f"{y}:{sy.mean() - by.mean():+.2f}")
    for i in range(0, len(line), 10):
        say("   " + "  ".join(line[i:i + 10]))
    share = float(np.mean(pos)) if pos else 0.0
    say(f"previs kladny v {sum(pos)} z {len(pos)} let ({share:.0%})")
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    c = [v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5,
         all(O[m]["diff"] > 0 for m in O), br["sig"]["m"] > 0 and br["diff"] > 0, share >= 0.55]
    say("BODY 1-5: " + " ".join("ANO" if x else "ne" for x in c) + f"  => {'VYHODA (proslo vse)' if all(c) else 'BEZ VYHODY'}")
    return name.split(":")[0], sum(c), all(c)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    res = [run_f82(),
           five_points("F83 slaby mesic: vynos mesice <= 20. percentil za 10 let -> long cely dalsi mesic", monthly_run, "1900-01-01"),
           five_points("F84 sude tydny cyklu FOMC: long v oknech -1..3, 9..13, 19..23, 29..33 dni od FOMC",
                       lambda mk, d: T.run(mk, d, fomc_flags(mk, d), 5), "2010-01-01")]
    say("=" * 100)
    for nm, k, ok in res:
        say(f"{nm:22s} {k}/5  {'PROSLO' if ok else 'neproslo'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES) + "\n")
