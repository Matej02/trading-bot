"""
F55 prelom mesice, F56 IBS, F57 den zprav CPI/NFP na US indexech.
Plan predem ve vaultu: Vyzkum/F55 az F57 Zacatek mesice, IBS a dny zprav.md (2026-11-19).
Spusteni: python -I f55_f57.py -> D:\\Trading bot\\research_data\\f55\\souhrn.txt
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import f7_lib as S7  # noqa: E402

LB, L = F.LB, F.L
OUT = os.path.join(F.RD, "f55")
os.makedirs(OUT, exist_ok=True)
LINES = []
US = ["SPX500mini", "NAS100mini", "US30mini"]
EU = ["GER_30mini", "GBR_100mini", "FRA_40mini"]
K = json.load(open(os.path.join(F.RD, "kalendar_2010_2021.json")))
_sp = lambda v: v.split() if isinstance(v, str) else list(v)  # noqa: E731
NEWS = {pd.Timestamp(x) for x in K["NFP"] + K["CPI"] + _sp(S7.NFP) + _sp(S7.CPI)}


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def prep(mk, d):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    pc = d.close.shift(1)
    A = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean().to_numpy()
    return b, rel, A


def net(b, rel, E, X, d0, d1):
    return (X - E) - rel * (E + X) / 2 + b["swapLong"] * E * F.nights(d0, d1)


# ---------- F55 prelom mesice ----------
def f55(mk, d):
    b, rel, A = prep(mk, d)
    O, C, idx, n = d.open.to_numpy(), d.close.to_numpy(), d.index, len(d)
    per = idx.to_period("M")
    last = np.r_[per[1:] != per[:-1], False]          # posledni obchodni den mesice
    rs, rb = [], []
    for i in range(21, n - 3):
        if not A[i - 1] > 0:
            continue
        R = net(b, rel, O[i], C[i + 3], idx[i], idx[i + 3]) / A[i - 1]
        (rs if last[i] else rb).append((idx[i], R))
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


# ---------- F56 IBS ----------
def f56(mk, d):
    b, rel, A = prep(mk, d)
    O, H, Lo, C = (x.to_numpy() for x in (d.open, d.high, d.low, d.close))
    s200 = d.close.rolling(200).mean().to_numpy()
    rng = H - Lo
    ibs = np.where(rng > 0, (C - Lo) / np.where(rng > 0, rng, 1), np.nan)
    idx, n = d.index, len(d)

    def one(i):
        e = i + 1
        if e >= n or not A[i] > 0:
            return None
        E, risk = O[e], 3 * A[i]
        stop = E - risk
        for k in range(e, min(e + 5, n)):
            if Lo[k] <= stop:
                X = stop if k == e else min(stop, O[k])
                break
            if C[k] > H[k - 1] or k == e + 4:
                X = C[k]
                break
        else:
            return None
        return k, net(b, rel, E, X, idx[e], idx[k]) / risk

    rs, rb, busy = [], [], -1
    for i in range(200, n - 1):
        if not (np.isfinite(s200[i]) and C[i] > s200[i]):
            continue
        r = one(i)
        if r is None:
            continue
        rb.append((idx[i + 1], r[1]))
        if ibs[i] < 0.2 and i > busy:
            rs.append((idx[i + 1], r[1]))
            busy = r[0]
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


# ---------- F57 den zprav ----------
def f57(mk, d):
    b, rel, A = prep(mk, d)
    C, idx, n = d.close.to_numpy(), d.index, len(d)
    rs, rb = [], []
    for i in range(21, n):
        if not A[i - 1] > 0:
            continue
        R = net(b, rel, C[i - 1], C[i], idx[i - 1], idx[i]) / A[i - 1]
        (rs if idx[i] in NEWS else rb).append((idx[i], R))
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def evaluate(fn, mks, src, a, b):
    Sx, Bx = [], []
    for mk in mks:
        d = F.yahoo(mk) if src == "yahoo" else F.broker(mk)
        s, bb = fn(mk, d)
        Sx.append(s)
        Bx.append(bb)
    s, bb = pd.concat(Sx).groupby("day").R.mean(), pd.concat(Bx).groupby("day").R.mean()
    sel = lambda x: x[(x.index >= a) & ((x.index < b) if b is not None else True)]  # noqa: E731
    s, bb = sel(s), sel(bb)
    diff, t = F.welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


def test(name, fn, dev0):
    say("\n" + "=" * 100)
    say(name)
    say("=" * 100)
    dev0 = pd.Timestamp(dev0)
    R = {"vyvoj": evaluate(fn, US, "yahoo", dev0, F.SPLIT), "kontrola": evaluate(fn, US, "yahoo", F.SPLIT, None),
         "broker": evaluate(fn, US, "broker", F.SPLIT, None)}
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    oth = evaluate(fn, EU, "yahoo", dev0, None)
    say(f"jiné trhy {', '.join(EU)}: signál {LB.fmt(oth['sig'])} | převis {oth['diff']:+.3f}, t {oth['t']:+.2f}")
    for mk in US + EU:
        v = evaluate(fn, [mk], "yahoo", dev0, None)
        say(f"   {mk:12s} {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    full = evaluate(fn, US, "yahoo", dev0, None)
    ys = sorted(set(full["s"].index.year))
    dif = {y: full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean() for y in ys}
    pos = [v > 0 for v in dif.values()]
    share = float(np.mean(pos))
    say("po letech převis: " + "  ".join(f"{y}:{v:+.2f}" for y, v in dif.items()))
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    c = [("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ("3) jiné trhy převis > 0", oth["diff"] > 0, f"{oth['diff']:+.3f}"),
         ("4) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
         ("5) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    ok = all(x[1] for x in c)
    say(f"   => {'VÝHODA (prošlo vše)' if ok else 'BEZ VÝHODY'}")
    return full


def ibs_overlap():
    """Popis: kolik vstupu IBS padne do otevreneho obchodu RSI(2) na stejnem trhu (Yahoo, cele obdobi)."""
    tot, hit = 0, 0
    for mk in US:
        d = F.yahoo(mk)
        s, _ = f56(mk, d)
        r, _ = F.run(mk, d)
        days = set(r.day)
        # otevreny RSI(2) obchod ~ vstup RSI(2) v poslednich 5 obchodnich dnech
        ix = d.index
        pos = {x: j for j, x in enumerate(ix)}
        rpos = sorted(pos[x] for x in days if x in pos)
        for x in s.day:
            j = pos.get(x)
            if j is None:
                continue
            tot += 1
            hit += any(0 <= j - p <= 4 for p in rpos)
    say(f"\nPopis F56: vstupů IBS {tot}, z toho {hit} ({hit / max(tot, 1):.0%}) do 5 dní po vstupu RSI(2) na stejném trhu")


if __name__ == "__main__":
    test("F55 PŘELOM MĚSÍCE – long otevření posledního dne měsíce → zavření 3. dne dalšího; srovnání = stejné 4denní okno v ostatní dny", f55, "1990-01-01")
    test("F56 IBS < 0,2 nad SMA200 – vstup otevření dalšího dne, ven zavření nad maximem předchozího dne / stop 3 ATR / 5 dní", f56, "1990-01-01")
    ibs_overlap()
    test("F57 DEN ZPRÁV CPI/NFP – long zavření předchozího dne → zavření dne zprávy; srovnání = ostatní dny", f57, "2010-01-01")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
