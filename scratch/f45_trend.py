"""
F45 filtr trendu pro prop ucet - long indexu jen nad 10mesicnim prumerem (Faber), proti stalemu drzeni.
Plan predem ve vaultu: Vyzkum/F45 Filtr trendu pro prop ucet.md (2026-11-19).
Spusteni: python -I f45_trend.py -> D:\\Trading bot\\research_data\\f45\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f45")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
MK = ["SPX500mini", "NAS100mini", "US30mini", "GER_30mini"]
DEV0, SPLIT = pd.Timestamp("1990-01-01"), pd.Timestamp("2019-01-01")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def yahoo(mk):
    c = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))["close"].astype(float)
    c.index = pd.to_datetime(c.index).tz_localize(None).normalize()
    c = c[c > 0].dropna()
    return c[c.index.day_of_week < 5]


def broker(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))
    h.index = pd.to_datetime(h.index)
    c = h.close.groupby(h.index.normalize()).last().astype(float)
    return c[c.index.day_of_week < 5]


def daily(mk, c, mode):
    """Denni vynos strategie (podil uctu). mode 'filtr' | 'drzeni'."""
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(c.iloc[-1])
    ret = c.pct_change()
    if mode == "drzeni":
        pos = pd.Series(1.0, index=c.index)
    else:
        me = c.groupby([c.index.year, c.index.month]).tail(1)            # zavreni poslednich obchodnich dni mesicu
        sma10 = me.rolling(10).mean()
        sig = (me > sma10).astype(float).where(sma10.notna())
        pos = sig.reindex(c.index).shift(1).ffill()                    # od dalsiho dne az do konce dalsiho mesice
    pos = pos.fillna(0.0)
    held = pos.shift(1).fillna(0.0)                                     # pozice drzena pres noc do dne t
    n = np.where(c.index.day_of_week == 3, 3, 1)
    switch = (pos != held).astype(float)
    r = held * ret + held * b["swapLong"] * n - switch * rel / 2
    return r.fillna(0.0)


def metrics(r):
    r = r.dropna()
    eq = (1 + r).cumprod()
    yrs = len(r) / 252
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if yrs > 0 else np.nan
    dd = (eq / eq.cummax() - 1).min()
    sh = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else np.nan
    return dict(cagr=cagr, dd=dd, calmar=cagr / abs(dd) if dd < 0 else np.nan, sh=sh)


def fm(m):
    return f"CAGR {m['cagr'] * 100:+5.1f} % | max DD {m['dd'] * 100:6.1f} % | Calmar {m['calmar']:.2f} | Sharpe {m['sh']:.2f}"


def port(src, mode, a, b):
    cols = {mk: daily(mk, yahoo(mk) if src == "yahoo" else broker(mk), mode) for mk in MK}
    P = pd.DataFrame(cols)
    P = P[(P.index >= a) & ((P.index < b) if b is not None else True)]
    return P.mean(axis=1, skipna=True)


def main():
    say("F45 Filtr trendu – long indexů jen když měsíční zavření > SMA 10 měsíců, jinak mimo trh; portfolio SPX, NAS, US30, DAX (stejné váhy)")
    say("náklady: spread při vstupu/výstupu, swap long za noc v pozici; srovnání = stále long se stejnými náklady")
    say("=" * 100)
    M = {}
    for nm, src, a, b in (("vyvoj", "yahoo", DEV0, SPLIT), ("kontrola", "yahoo", SPLIT, None), ("broker", "broker", SPLIT, None)):
        for mode in ("filtr", "drzeni"):
            M[(nm, mode)] = metrics(port(src, mode, a, b))
        say(f"{nm:9s} filtr:  {fm(M[(nm, 'filtr')])}")
        say(f"{'':9s} držení: {fm(M[(nm, 'drzeni')])}")
    better = 0
    say("Po indexech (Yahoo 1990–2026):")
    for mk in MK:
        c = yahoo(mk)
        f = metrics(daily(mk, c, "filtr")[c.index >= DEV0])
        h = metrics(daily(mk, c, "drzeni")[c.index >= DEV0])
        better += f["calmar"] > h["calmar"]
        say(f"   {mk:11s} filtr {fm(f)}")
        say(f"   {'':11s} držení {fm(h)}")
    pf, ph = port("yahoo", "filtr", DEV0, None), port("yahoo", "drzeni", DEV0, None)
    say("Po letech (portfolio, výnos filtr / držení):")
    line = [f"{y}:{(1 + pf[pf.index.year == y]).prod() - 1:+.0%}/{(1 + ph[ph.index.year == y]).prod() - 1:+.0%}" for y in sorted(set(pf.index.year))]
    for i in range(0, len(line), 8):
        say("   " + "  ".join(line[i:i + 8]))
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    g = lambda nm, mode, k: M[(nm, mode)][k]  # noqa: E731
    c = [("1) max DD filtru menší (vývoj i kontrola)", g("vyvoj", "filtr", "dd") > g("vyvoj", "drzeni", "dd") and g("kontrola", "filtr", "dd") > g("kontrola", "drzeni", "dd"),
          f"{g('vyvoj', 'filtr', 'dd'):.1%} vs {g('vyvoj', 'drzeni', 'dd'):.1%}; {g('kontrola', 'filtr', 'dd'):.1%} vs {g('kontrola', 'drzeni', 'dd'):.1%}"),
         ("2) Calmar filtru vyšší (vývoj i kontrola)", g("vyvoj", "filtr", "calmar") > g("vyvoj", "drzeni", "calmar") and g("kontrola", "filtr", "calmar") > g("kontrola", "drzeni", "calmar"),
          f"{g('vyvoj', 'filtr', 'calmar'):.2f} vs {g('vyvoj', 'drzeni', 'calmar'):.2f}; {g('kontrola', 'filtr', 'calmar'):.2f} vs {g('kontrola', 'drzeni', 'calmar'):.2f}"),
         ("3) Sharpe filtru vyšší (vývoj i kontrola)", g("vyvoj", "filtr", "sh") > g("vyvoj", "drzeni", "sh") and g("kontrola", "filtr", "sh") > g("kontrola", "drzeni", "sh"),
          f"{g('vyvoj', 'filtr', 'sh'):.2f} vs {g('vyvoj', 'drzeni', 'sh'):.2f}; {g('kontrola', 'filtr', 'sh'):.2f} vs {g('kontrola', 'drzeni', 'sh'):.2f}"),
         ("4) Calmar lepší u >= 3 ze 4 indexů", better >= 3, f"{better} ze 4"),
         ("5) broker 2019+: Calmar filtru vyšší", g("broker", "filtr", "calmar") > g("broker", "drzeni", "calmar"),
          f"{g('broker', 'filtr', 'calmar'):.2f} vs {g('broker', 'drzeni', 'calmar'):.2f}")]
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
