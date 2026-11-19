"""
F42 RSI(2) prisna proverka - signal vs. stejne vstupy/vystupy ve vsech dnech nad SMA200 (drift).
Plan predem ve vaultu: Vyzkum/F42 RSI(2) prisna proverka.md (2026-11-19).
Spusteni: python -I f42_rsi2.py -> D:\\Trading bot\\research_data\\f42\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f42")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
DEV0, SPLIT = pd.Timestamp("1990-01-01"), pd.Timestamp("2019-01-01")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def yahoo(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))[["open", "high", "low", "close"]].astype(float)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    ok = (d.high >= d.low) & (d.low <= d.close) & (d.close <= d.high) & (d.low <= d.open) & (d.open <= d.high) & (d.close > 0)
    d = d[ok].dropna()
    return d[d.index.day_of_week < 5]


def broker(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))
    h.index = pd.to_datetime(h.index)
    g = h.groupby(h.index.normalize())
    d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()}).dropna()
    return d[d.index.day_of_week < 5]


def rsi_wilder(c, n=2):
    d = c.diff()
    up, dn = d.clip(lower=0), (-d).clip(lower=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + au / ad.replace(0, np.nan))


def nights(d0, d1):
    days = pd.date_range(d0 + pd.Timedelta(days=1), d1, freq="D")
    w = days.day_of_week
    return int(((w < 5) & (w != 3)).sum() + 3 * (w == 3).sum())


def run(mk, d, thr=10, maxd=10):
    """Vrati (signal_trades, baseline_trades) jako DataFrame (entry_day, R)."""
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    c = d.close
    sma200, sma5 = c.rolling(200).mean(), c.rolling(5).mean()
    rsi = rsi_wilder(c)
    pc = c.shift(1)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    atr = tr.rolling(20).mean()
    O, H, Lo, C = d.open.to_numpy(), d.high.to_numpy(), d.low.to_numpy(), c.to_numpy()
    S5, A = sma5.to_numpy(), atr.to_numpy()
    up = (c > sma200).to_numpy()
    sig = (up & (rsi < thr).to_numpy())
    idx = d.index
    n = len(d)

    def one(i):
        """Signal na zavreni dne i -> vstup na otevreni i+1. Vrati (exit_index, R)."""
        e = i + 1
        if e >= n or not A[i] > 0:
            return None
        E = O[e]
        risk = 3 * A[i]
        stop = E - risk
        for k in range(e, min(e + maxd, n)):
            if Lo[k] <= stop:
                X = min(stop, O[k]) if k > e else stop
                break
            if C[k] > S5[k] or k == e + maxd - 1:
                X = C[k]
                break
        else:
            return None
        net = (X - E) - rel * (E + X) / 2 + b["swapLong"] * E * nights(idx[e], idx[k])
        return k, net / risk

    rows_s, rows_b = [], []
    busy = -1
    for i in range(200, n - 1):
        if up[i]:
            r = one(i)
            if r is not None:
                rows_b.append((idx[i + 1], r[1]))
        if sig[i] and i > busy:
            r = one(i)
            if r is not None:
                rows_s.append((idx[i + 1], r[1]))
                busy = r[0]
    S = pd.DataFrame(rows_s, columns=["day", "R"]).assign(mk=mk)
    B = pd.DataFrame(rows_b, columns=["day", "R"]).assign(mk=mk)
    return S, B


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    diff = a.mean() - b.mean()
    return diff, diff / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def by_day(T):
    return T.groupby("day").R.mean()


def evaluate(mks, src, a, b, thr=10, maxd=10):
    Ss, Bs = [], []
    for mk in mks:
        d = yahoo(mk) if src == "yahoo" else broker(mk)
        s, bb = run(mk, d, thr, maxd)
        Ss.append(s)
        Bs.append(bb)
    s, bb = by_day(pd.concat(Ss)), by_day(pd.concat(Bs))
    sel = lambda x: x[(x.index >= a) & ((x.index < b) if b is not None else True)]  # noqa: E731
    s, bb = sel(s), sel(bb)
    diff, t = welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


US = ["SPX500mini", "NAS100mini", "US30mini"]


def main():
    say("F42 RSI(2) – long nad SMA200 při RSI(2) < 10, vstup otevření dalšího dne, ven nad SMA5 / stop 3 ATR / 10 dní")
    say("srovnání = stejné vstupy a výstupy ve všech dnech nad SMA200 (drift); hodnoceno po dnech vstupu; R = výsledek / 3 ATR")
    say("=" * 100)
    R = {"vyvoj": evaluate(US, "yahoo", DEV0, SPLIT), "kontrola": evaluate(US, "yahoo", SPLIT, None),
         "broker": evaluate(US, "broker", SPLIT, None)}
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    O = {}
    for mk in ("GER_30mini", "GBR_100mini", "FRA_40mini"):
        O[mk] = evaluate([mk], "yahoo", DEV0, None)
        say(f"{mk:11s} (1990–2026): signál {LB.fmt(O[mk]['sig'])} | převis {O[mk]['diff']:+.3f}, t {O[mk]['t']:+.2f}")
    full = evaluate(US, "yahoo", DEV0, None)
    pos, line = [], []
    for y in sorted(set(full["s"].index.year)):
        dy = full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean()
        pos.append(dy > 0)
        line.append(f"{y}:{dy:+.2f}")
    share = float(np.mean(pos))
    for i in range(0, len(line), 10):
        say("   " + "  ".join(line[i:i + 10]))
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    c = [("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ("3) DAX, FTSE, CAC převis > 0", all(O[m]["diff"] > 0 for m in O), ", ".join(f"{m[:3]} {O[m]['diff']:+.3f}" for m in O)),
         ("4) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
         ("5) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
