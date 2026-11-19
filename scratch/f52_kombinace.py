"""
F52 kombinace F33 a RSI(2) pro prop ucet (pravidla obou beze zmeny). Plan predem ve vaultu: Vyzkum/F52 Kombinace F33 a RSI(2) pro prop ucet.md.
Spusteni: python -I f52_kombinace.py -> D:\\Trading bot\\research_data\\f52\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402

LB, L = F.LB, F.L
OUT = os.path.join(F.RD, "f52")
os.makedirs(OUT, exist_ok=True)
LINES = []
START = pd.Timestamp("2003-01-01")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def rsi2_trades(mk):
    """Obchody RSI(2) podle F42 (Yahoo) s datem vstupu a vystupu; R v jednotkach 3 ATR."""
    d = F.yahoo(mk)
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    c = d.close
    s200, s5, rsi = c.rolling(200).mean(), c.rolling(5).mean(), F.rsi_wilder(c)
    pc = c.shift(1)
    A = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean().to_numpy()
    O, Lo, C, S5 = d.open.to_numpy(), d.low.to_numpy(), c.to_numpy(), s5.to_numpy()
    sig = ((c > s200) & (rsi < 10)).to_numpy()
    idx, n = d.index, len(d)
    rows, busy = [], -1
    for i in range(200, n - 1):
        if not sig[i] or i <= busy or not A[i] > 0:
            continue
        e = i + 1
        E, risk = O[e], 3 * A[i]
        stop, X, k = E - risk, None, None
        for k in range(e, min(e + 10, n)):
            if Lo[k] <= stop:
                X = min(stop, O[k]) if k > e else stop
                break
            if C[k] > S5[k] or k == e + 9:
                X = C[k]
                break
        if X is None:
            continue
        net = (X - E) - rel * (E + X) / 2 + b["swapLong"] * E * F.nights(idx[e], idx[k])
        rows.append(dict(s="RSI2", mk=mk, t_in=idx[e], t_out=idx[k], R=net / risk))
        busy = k
    return pd.DataFrame(rows)


def f33_trades():
    T = pd.read_pickle(os.path.join(F.RD, "f33", "f33_yahoo.pkl"))
    out = T.t + pd.offsets.BMonthEnd(0)
    return pd.DataFrame(dict(s="F33", mk=T.mk, t_in=T.t, t_out=out, R=T.R / 3.0))   # R z ATR -> jednotky 3 ATR


END = pd.Timestamp("2026-10-31")


def monthly(T):
    m = T.groupby(T.t_out.dt.to_period("M")).R.sum()
    return m.reindex(pd.period_range(START, END, freq="M"), fill_value=0.0)


def maxdd(r):
    eq = np.cumsum(np.asarray(r))
    return float((eq - np.maximum.accumulate(np.r_[0, eq])[1:]).min())


def sharpe(m):
    return m.mean() / m.std() * np.sqrt(12) if m.std() > 0 else np.nan


def prop_sim(T, risk_pct):
    """Start kazdy mesic: +10 % pred -10 % celkem nebo -5 % za den, limit 12 mesicu. Ucet se meni pri uzavreni obchodu."""
    T = T.sort_values("t_out")
    daily = T.groupby(T.t_out.dt.normalize()).R.sum()
    res = []
    for st in pd.date_range("2003-03-01", "2025-10-01", freq="MS"):
        end = st + pd.DateOffset(months=12)
        eq, out, when = 0.0, "vyprselo", None
        for day, r in daily[(daily.index >= st) & (daily.index < end)].items():
            pnl = r * risk_pct
            if pnl <= -5.0:
                out, when = "propadl (den)", day
                break
            eq += pnl
            if eq <= -10.0:
                out, when = "propadl", day
                break
            if eq >= 10.0:
                out, when = "prosel", day
                break
        res.append(dict(st=st, out=out, months=(when - st).days / 30.4 if when is not None else np.nan))
    return pd.DataFrame(res)


def main():
    R2 = pd.concat([rsi2_trades(m) for m in F.US], ignore_index=True)
    R2 = R2[R2.t_in >= START]
    F3 = f33_trades()
    ALL = pd.concat([R2, F3], ignore_index=True)
    say("F52 Kombinace F33 (SPX, NAS) a RSI(2) (SPX, NAS, US30), Yahoo 2003–2026, R = jednotka rizika 3 ATR")
    say("=" * 100)
    say(f"obchodů: RSI(2) {len(R2)} ({len(R2) / 23.8:.1f}/rok), F33 {len(F3)} ({len(F3) / 23.8:.1f}/rok)")
    mR, mF, mA = monthly(R2), monthly(F3), monthly(ALL)
    corr = float(np.corrcoef(mR, mF)[0, 1])
    say(f"korelace měsíčních výsledků F33 vs RSI(2): {corr:+.2f}")
    S = {}
    for nm, a, b in (("vyvoj", "2003-01", "2018-12"), ("kontrola", "2019-01", None)):
        sl = lambda m: m[(m.index >= pd.Period(a)) & ((m.index <= pd.Period(b)) if b else True)]  # noqa: E731
        S[nm] = {k: dict(sh=sharpe(sl(m)), sum=sl(m).sum() / (len(sl(m)) / 12), dd=maxdd(sl(m))) for k, m in (("RSI2", mR), ("F33", mF), ("obe", mA))}
        for k, v in S[nm].items():
            say(f"{nm:9s} {k:5s}: Sharpe {v['sh']:.2f} | R za rok {v['sum']:+.2f} | největší propad {v['dd']:+.2f} R")
    tot = {k: maxdd(m) for k, m in (("RSI2", mR), ("F33", mF), ("obe", mA))}
    say(f"celé období největší propad: RSI(2) {tot['RSI2']:+.2f} R, F33 {tot['F33']:+.2f} R, obě {tot['obe']:+.2f} R")
    say("Po letech (R za rok: RSI2 / F33 / obě): " + "  ".join(
        f"{y}:{mR[mR.index.year == y].sum():+.1f}/{mF[mF.index.year == y].sum():+.1f}/{mA[mA.index.year == y].sum():+.1f}" for y in range(2003, 2027)))
    say("\nSimulace prop zkoušky (start každý měsíc 2003–2025; +10 % před −10 % / −5 % za den; max 12 měsíců):")
    for rp in (0.25, 0.5, 1.0, 2.0):
        P = prop_sim(ALL, rp)
        cnt = P.out.value_counts(normalize=True)
        med = P[P.out == "prosel"].months.median()
        say(f"   riziko {rp:4.2f} %/obchod: prošel {cnt.get('prosel', 0):.0%} | propadl {cnt.get('propadl', 0) + cnt.get('propadl (den)', 0):.0%} "
            f"| vypršelo {cnt.get('vyprselo', 0):.0%} | medián do úspěchu {med:.1f} měs.")
        for nm, a, b in (("  2003–18", "2003-01-01", "2018-12-31"), ("  2019–25", "2019-01-01", "2026-01-01")):
            Q = P[(P.st >= a) & (P.st <= b)]
            c2 = Q.out.value_counts(normalize=True)
            say(f"      {nm}: prošel {c2.get('prosel', 0):.0%}, propadl {c2.get('propadl', 0) + c2.get('propadl (den)', 0):.0%}, vypršelo {c2.get('vyprselo', 0):.0%}")
    say("\nROZHODNUTÍ podle pravidel zapsaných předem")
    v, k = S["vyvoj"], S["kontrola"]
    c = [("1) korelace < 0,5", corr < 0.5, f"{corr:+.2f}"),
         ("2) Sharpe obou > každá zvlášť (vývoj i kontrola)", all(S[p]["obe"]["sh"] > max(S[p]["RSI2"]["sh"], S[p]["F33"]["sh"]) for p in ("vyvoj", "kontrola")),
          f"vývoj {v['obe']['sh']:.2f} vs {v['RSI2']['sh']:.2f}/{v['F33']['sh']:.2f}; kontrola {k['obe']['sh']:.2f} vs {k['RSI2']['sh']:.2f}/{k['F33']['sh']:.2f}"),
         ("3) propad obou < součet propadů", tot["obe"] > tot["RSI2"] + tot["F33"], f"{tot['obe']:+.2f} vs {tot['RSI2'] + tot['F33']:+.2f}")]
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'KOMBINACE POMÁHÁ (prošlo vše)' if all(x[1] for x in c) else 'KOMBINACE NEPOMÁHÁ'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
