"""
F70 RSI(2) pro maly ucet: A) popis v $ na 1 lot u brokera 2019-2026, B) varianty V0-V4 (MAR pri riziku 1 % u stopu).
Plan predem ve vaultu: Vyzkum/F70 RSI(2) pro maly ucet.md (2026-11-21).
Spusteni: python -I f70_rsi2_maly_ucet.py -> D:\\Trading bot\\research_data\\f70\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402

L = F.L
OUT = os.path.join(F.RD, "f70")
os.makedirs(OUT, exist_ok=True)
US = ["SPX500mini", "NAS100mini", "US30mini"]
UCET = 457.0
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def trades(mk, d, k=3.0, thr=10, maxd=10):
    """Obchody RSI(2) (pravidlo F42, stop k ATR). Vraci DataFrame: mk, entry, exit, pnl (cena na 1 lot), risk (k*ATR), R."""
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    c = d.close
    sma200, sma5 = c.rolling(200).mean(), c.rolling(5).mean()
    rsi = F.rsi_wilder(c)
    pc = c.shift(1)
    atr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean()
    O, Lo, C = d.open.to_numpy(), d.low.to_numpy(), c.to_numpy()
    S5, A = sma5.to_numpy(), atr.to_numpy()
    sig = ((c > sma200) & (rsi < thr)).to_numpy()
    idx, n = d.index, len(d)
    rows, busy = [], -1
    for i in range(200, n - 1):
        if not sig[i] or i <= busy or not A[i] > 0:
            continue
        e = i + 1
        E, risk = O[e], k * A[i]
        stop = E - risk
        X = kx = None
        for j in range(e, min(e + maxd, n)):
            if Lo[j] <= stop:
                X, kx = (min(stop, O[j]) if j > e else stop), j
                break
            if C[j] > S5[j] or j == e + maxd - 1:
                X, kx = C[j], j
                break
        if X is None:
            continue
        pnl = ((X - E) - rel * (E + X) / 2 + b["swapLong"] * E * F.nights(idx[e], idx[kx])) * b["moneyPerPrice"]
        rows.append((mk, idx[e], idx[kx], pnl, risk * b["moneyPerPrice"], pnl / (risk * b["moneyPerPrice"])))
        busy = kx
    return pd.DataFrame(rows, columns=["mk", "entry", "exit", "pnl", "risk", "R"])


def one_position(T):
    """V2: jedna pozice napric trhy, pri soubehu prednost SPX > NAS > US30."""
    pr = {m: i for i, m in enumerate(US)}
    T = T.assign(p=T.mk.map(pr)).sort_values(["entry", "p"])
    out, free = [], pd.Timestamp.min
    for _, r in T.iterrows():
        if r.entry > free:
            out.append(r)
            free = r.exit
    return pd.DataFrame(out)


def stats(T, a, b):
    T = T[(T.entry >= a) & (T.entry < b)]
    yrs = (b - a).days / 365.25
    if T.empty:
        return dict(n=0, ann=np.nan, dd=np.nan, mar=np.nan, m=np.nan, win=np.nan, npy=0)
    eq = T.sort_values("exit").R.cumsum()          # % uctu pri riziku 1 % (bez skladani)
    dd = float((eq.cummax().clip(lower=0) - eq).max())
    ann = float(T.R.sum() / yrs)
    return dict(n=len(T), ann=ann, dd=dd, mar=ann / dd if dd > 0 else np.inf, m=T.R.mean(), win=(T.R > 0).mean(), npy=len(T) / yrs)


def part_a():
    say("=" * 100)
    say("ČÁST A – popis: RSI(2) u brokera 2019–2026 na 1 lot (1 $/bod), stop 3 ATR")
    say("=" * 100)
    a = pd.Timestamp("2019-01-01")
    for mk in US:
        T = trades(mk, F.broker(mk))
        T = T[T.entry >= a]
        eq = T.sort_values("exit").pnl.cumsum()
        dd = float((eq.cummax().clip(lower=0) - eq).max())
        yr = T.groupby(T.exit.dt.year).pnl.sum()
        say(f"{mk:11s} obchodů {len(T)} | zisk celkem {T.pnl.sum():+,.0f} $ | největší propad {dd:,.0f} $ | nejhorší obchod {T.pnl.min():+,.0f} $ | "
            f"riziko u stopu medián {T.risk.median():,.0f} $, 90 % {T.risk.quantile(.9):,.0f} $")
        say(f"{'':11s} po letech: " + "  ".join(f"{y}:{v:+,.0f}" for y, v in yr.items()))
        need1, need2, needdd = T.risk.quantile(.9) / 0.01, T.risk.quantile(.9) / 0.02, dd / 0.20
        say(f"{'':11s} potřebný účet (1 lot): riziko ≤ 1 % → {need1:,.0f} $ | ≤ 2 % → {need2:,.0f} $ | propad ≤ 20 % → {needdd:,.0f} $"
            f" | mikro 0,01 lotu: {need1 / 100:,.0f} $ / {need2 / 100:,.0f} $ / {needdd / 100:,.0f} $")
        say(f"{'':11s} na účtu {UCET:.0f} $ by 1 lot riskoval u stopu medián {T.risk.median() / UCET:.0%}; mikro 0,01 lotu {T.risk.median() / 100 / UCET:.1%}")


def part_b():
    say("\n" + "=" * 100)
    say("ČÁST B – varianty při riziku 1 % u stopu na obchod (bez skládání): výnos % ročně, největší propad %, MAR")
    say("=" * 100)
    per = {"vývoj Yahoo 1990–2018": ("yahoo", pd.Timestamp("1990-01-01"), F.SPLIT),
           "kontrola Yahoo 2019–2026": ("yahoo", F.SPLIT, pd.Timestamp("2026-11-21")),
           "broker 2019–2026": ("broker", F.SPLIT, pd.Timestamp("2026-11-21"))}
    data = {src: {mk: (F.yahoo(mk) if src == "yahoo" else F.broker(mk)) for mk in US} for src in ("yahoo", "broker")}
    V = {"V0 3 trhy, stop 3 ATR": lambda s: pd.concat([trades(m, data[s][m]) for m in US]),
         "V1 jen SPX, stop 3 ATR": lambda s: trades("SPX500mini", data[s]["SPX500mini"]),
         "V2 jedna pozice napříč, 3 ATR": lambda s: one_position(pd.concat([trades(m, data[s][m]) for m in US])),
         "V3 jen SPX, stop 2 ATR": lambda s: trades("SPX500mini", data[s]["SPX500mini"], k=2.0),
         "V4 jen SPX, stop 1,5 ATR": lambda s: trades("SPX500mini", data[s]["SPX500mini"], k=1.5)}
    cache = {(v, s): f(s) for v, f in V.items() for s in ("yahoo", "broker")}
    res = {}
    for pn, (src, a, b) in per.items():
        say(f"\n{pn}:")
        for v in V:
            st = stats(cache[(v, src)], a, b)
            res[(pn, v)] = st
            say(f"   {v:32s} obchodů {st['n']:4d} ({st['npy']:.1f}/rok) | R {st['m']:+.3f} | výhra {st['win']:.0%} | "
                f"výnos {st['ann']:+.2f} %/rok | propad {st['dd']:.1f} % | MAR {st['mar']:.2f}")
    say("\nROZHODNUTÍ podle pravidel zapsaných předem")
    dev = "vývoj Yahoo 1990–2018"
    win = max(V, key=lambda v: res[(dev, v)]["mar"])
    say(f"   vítěz ve vývoji (nejvyšší MAR): {win} (MAR {res[(dev, win)]['mar']:.2f})")
    okc = True
    for pn in ("kontrola Yahoo 2019–2026", "broker 2019–2026"):
        best = max(res[(pn, v)]["mar"] for v in V)
        st = res[(pn, win)]
        c = st["ann"] > 0 and st["mar"] >= 0.8 * best
        okc &= c
        say(f"   {pn}: výnos {st['ann']:+.2f} %/rok, MAR {st['mar']:.2f} (nejlepší {best:.2f}, 80 % = {0.8 * best:.2f}) → {'ANO' if c else 'NE'}")
    say(f"   => {'POTVRZENO: pro malý účet ' + win if okc else 'NEPOTVRZENO: zůstává V0'}")


if __name__ == "__main__":
    part_a()
    part_b()
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
