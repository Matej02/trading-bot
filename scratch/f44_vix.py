"""
F44 struktura VIX - VIX/VIX3M >= 1 -> long indexu na 5 dni (stop 3 ATR), proti stejnym vstupum ve vsech dnech.
Plan predem ve vaultu: Vyzkum/F44 Struktura VIX.md (2026-11-19).
Spusteni: python -I f44_vix.py -> D:\\Trading bot\\research_data\\f44\\souhrn.txt
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402  (nacitani dat, noci, welch)

LB, L = F.LB, F.L
OUT = os.path.join(F.RD, "f44")
DEV0, SPLIT = pd.Timestamp("2006-07-17"), pd.Timestamp("2019-01-01")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def vix(tk):
    j = json.load(open(os.path.join(OUT, f"{tk}.json")))["chart"]["result"][0]
    t = pd.to_datetime(j["timestamp"], unit="s").normalize()
    return pd.Series(j["indicators"]["quote"][0]["close"], index=t, dtype=float).dropna().groupby(level=0).last()


RATIO = (vix("VIX") / vix("VIX3M")).dropna()


def run(mk, d):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    c = d.close
    pc = c.shift(1)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    A = tr.rolling(20).mean().to_numpy()
    O, Lo, C = d.open.to_numpy(), d.low.to_numpy(), c.to_numpy()
    sig = (RATIO.reindex(d.index) >= 1.0).to_numpy()
    idx, n = d.index, len(d)

    def one(i):
        e = i + 1
        if e + 4 >= n or not A[i] > 0:
            return None
        E = O[e]
        risk = 3 * A[i]
        stop = E - risk
        X, k = None, None
        for k in range(e, e + 5):
            if Lo[k] <= stop:
                X = min(stop, O[k]) if k > e else stop
                break
        if X is None:
            k = e + 4
            X = C[k]
        net = (X - E) - rel * (E + X) / 2 + b["swapLong"] * E * F.nights(idx[e], idx[k])
        return k, net / risk

    rs, rb, busy = [], [], -1
    for i in range(20, n - 5):
        if idx[i] < DEV0:
            continue
        r = one(i)
        if r is None:
            continue
        rb.append((idx[i + 1], r[1]))
        if sig[i] and i > busy:
            rs.append((idx[i + 1], r[1]))
            busy = r[0]
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def evaluate(mks, src, a, b):
    S, B = [], []
    for mk in mks:
        d = F.yahoo(mk) if src == "yahoo" else F.broker(mk)
        s, bb = run(mk, d)
        S.append(s)
        B.append(bb)
    s, bb = pd.concat(S).groupby("day").R.mean(), pd.concat(B).groupby("day").R.mean()
    sel = lambda x: x[(x.index >= a) & ((x.index < b) if b is not None else True)]  # noqa: E731
    s, bb = sel(s), sel(bb)
    diff, t = F.welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


def main():
    US = ["SPX500mini", "NAS100mini"]
    say("F44 Struktura VIX – VIX/VIX3M >= 1 na zavření → long od otevření dalšího dne na 5 dní (stop 3 ATR)")
    say(f"dní s backwardation od 2006-07: {int((RATIO >= 1).sum())} z {len(RATIO)}")
    say("=" * 100)
    R = {"vyvoj": evaluate(US, "yahoo", DEV0, SPLIT), "kontrola": evaluate(US, "yahoo", SPLIT, None),
         "broker": evaluate(US, "broker", SPLIT, None)}
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    O = {}
    for mk in ("US30mini", "GER_30mini", "GBR_100mini"):
        O[mk] = evaluate([mk], "yahoo", DEV0, None)
        say(f"{mk:11s} (2006–2026): signál {LB.fmt(O[mk]['sig'])} | převis {O[mk]['diff']:+.3f}, t {O[mk]['t']:+.2f}")
    full = evaluate(US, "yahoo", DEV0, None)
    pos, line = [], []
    for y in sorted(set(full["s"].index.year)):
        dy = full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean()
        pos.append(dy > 0)
        line.append(f"{y}:{dy:+.2f}(n{int((full['s'].index.year == y).sum())})")
    share = float(np.mean(pos))
    for i in range(0, len(line), 7):
        say("   " + "  ".join(line[i:i + 7]))
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    c = [("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ("3) US30, DAX, FTSE převis > 0", all(O[m]["diff"] > 0 for m in O), ", ".join(f"{m[:3]} {O[m]['diff']:+.3f}" for m in O)),
         ("4) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
         ("5) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
