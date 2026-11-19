"""
F53 RSI(2) obousmerne na kovech a F54 na hlavnich menach. Plan predem ve vaultu: Vyzkum/F53 a F54 RSI(2) na kovech a menach.md.
Spusteni: python -I f53_f54.py -> D:\\Trading bot\\research_data\\f53\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402

LB, L = F.LB, F.L
OUT = os.path.join(F.RD, "f53")
os.makedirs(OUT, exist_ok=True)
LINES = []
DEV0 = pd.Timestamp("2000-01-01")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def run2(mk, d):
    """Obousmerne RSI(2): (signal, srovnani) jako DataFrame (day, R)."""
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    c = d.close
    s200, s5, rsi = c.rolling(200).mean().to_numpy(), c.rolling(5).mean().to_numpy(), F.rsi_wilder(c).to_numpy()
    pc = c.shift(1)
    A = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean().to_numpy()
    O, H, Lo, C = d.open.to_numpy(), d.high.to_numpy(), d.low.to_numpy(), c.to_numpy()
    idx, n = d.index, len(d)

    def one(i, dd):
        e = i + 1
        if e >= n or not A[i] > 0:
            return None
        E, risk = O[e], 3 * A[i]
        stop, X, k = E - dd * risk, None, None
        for k in range(e, min(e + 10, n)):
            hit = Lo[k] <= stop if dd == 1 else H[k] >= stop
            if hit:
                X = stop if k == e else (min(stop, O[k]) if dd == 1 else max(stop, O[k]))
                break
            if (dd == 1 and C[k] > s5[k]) or (dd == -1 and C[k] < s5[k]) or k == e + 9:
                X = C[k]
                break
        if X is None:
            return None
        sw = (b["swapLong"] if dd == 1 else b["swapShort"]) * E * F.nights(idx[e], idx[k])
        return k, (dd * (X - E) - rel * (E + X) / 2 + sw) / risk

    rs, rb, busy = [], [], -1
    for i in range(200, n - 1):
        if not np.isfinite(s200[i]):
            continue
        dd = 1 if C[i] > s200[i] else -1
        r = one(i, dd)
        if r is None:
            continue
        rb.append((idx[i + 1], r[1]))
        sig = (dd == 1 and rsi[i] < 10) or (dd == -1 and rsi[i] > 90)
        if sig and i > busy:
            rs.append((idx[i + 1], r[1]))
            busy = r[0]
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def evaluate(mks, src, a, b):
    S, B = [], []
    for mk in mks:
        d = F.yahoo(mk) if src == "yahoo" else F.broker(mk)
        s, bb = run2(mk, d)
        S.append(s)
        B.append(bb)
    s, bb = pd.concat(S).groupby("day").R.mean(), pd.concat(B).groupby("day").R.mean()
    sel = lambda x: x[(x.index >= a) & ((x.index < b) if b is not None else True)]  # noqa: E731
    s, bb = sel(s), sel(bb)
    diff, t = F.welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


def test(name, main_mks, other_mks):
    say("\n" + "=" * 100)
    say(name)
    say("=" * 100)
    R = {"vyvoj": evaluate(main_mks, "yahoo", DEV0, F.SPLIT), "kontrola": evaluate(main_mks, "yahoo", F.SPLIT, None),
         "broker": evaluate(main_mks, "broker", F.SPLIT, None)}
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    oth = evaluate(other_mks, "yahoo", DEV0, None)
    say(f"jiné trhy {', '.join(other_mks)}: signál {LB.fmt(oth['sig'])} | převis {oth['diff']:+.3f}, t {oth['t']:+.2f}")
    for mk in main_mks:
        v = evaluate([mk], "yahoo", DEV0, None)
        say(f"   {mk:8s} {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}")
    full = evaluate(main_mks, "yahoo", DEV0, None)
    pos = [full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean() > 0 for y in sorted(set(full["s"].index.year))]
    share = float(np.mean(pos))
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
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")


if __name__ == "__main__":
    test("F53 RSI(2) OBOUSMĚRNĚ NA KOVECH (XAU, XAG; jiný trh XPT)", ["XAUUSD", "XAGUSD"], ["XPTUSD"])
    test("F54 RSI(2) OBOUSMĚRNĚ NA HLAVNÍCH MĚNÁCH (7 párů; jiné trhy křížové páry)",
         ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"], ["EURJPY", "GBPJPY", "AUDJPY", "EURCAD", "GBPNZD"])
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
