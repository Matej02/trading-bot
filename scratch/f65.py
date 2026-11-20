"""
F65 prelom mesice na 10 svetovych indexech (nezavisle overeni F61). Pravidlo F55: long otevreni posledniho obchodniho dne
mesice -> zavreni 3. dne dalsiho; srovnani = ostatni 4denni okna. Plan predem: Vyzkum/F65 Prelom mesice na svetovych indexech.md.
Spusteni: python -I f65.py -> D:\\Trading bot\\research_data\\f65\\souhrn.txt
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402

LB = F.LB
YD = os.path.join(F.RD, "f65")
TICK = ["N225", "AXJO", "SSMI", "AEX", "BFX", "HSI", "GSPTSE", "KS11", "TWII", "STI"]
SPR = 0.0002   # 2 bp na vstupu i na vystupu
SWAP = -0.0001  # za noc
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def load(tk):
    j = json.load(open(os.path.join(YD, f"{tk}_1d.json")))["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    tz = j["meta"].get("exchangeTimezoneName", "UTC")
    idx = pd.to_datetime(j["timestamp"], unit="s", utc=True).tz_convert(tz).tz_localize(None).normalize()
    d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=idx).astype(float).dropna()
    d = d[~d.index.duplicated(keep="last")].sort_index()
    d = d[d.index.day_of_week < 5]
    d = d[~((d.open == d.high) & (d.high == d.low) & (d.low == d.close))]
    d = d[(d.high >= d.low) & (d.close > 0) & (d.open > 0)]
    bad = (d.open - d.close.shift(1)).abs() < 1e-9
    share = bad.groupby(d.index.year).mean()
    keep = share[share <= 0.5].index
    return d[d.index.year.isin(keep)], sorted(set(share.index) - set(keep))


def tom(d):
    O, C, idx, n = d.open.to_numpy(), d.close.to_numpy(), d.index, len(d)
    pc = d.close.shift(1)
    A = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean().to_numpy()
    per = idx.to_period("M")
    last = np.r_[per[1:] != per[:-1], False]
    rs, rb = [], []
    for i in range(21, n - 3):
        if not A[i - 1] > 0:
            continue
        # mezera v datech (vyrazeny rok) -> okno nepocitat
        if (idx[i + 3] - idx[i]).days > 10:
            continue
        E, X = O[i], C[i + 3]
        R = ((X - E) - SPR * (E + X) + SWAP * E * F.nights(idx[i], idx[i + 3])) / A[i - 1]
        (rs if last[i] else rb).append((idx[i], R))
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def ev(data, a=None, b=None):
    S = pd.concat([x[0] for x in data]).groupby("day").R.mean()
    B = pd.concat([x[1] for x in data]).groupby("day").R.mean()
    if a is not None:
        S, B = S[S.index >= a], B[B.index >= a]
    if b is not None:
        S, B = S[S.index < b], B[B.index < b]
    diff, t = F.welch(S, B)
    return dict(sig=LB.st(S), diff=diff, t=t, s=S, b=B)


def main():
    say("F65 PŘELOM MĚSÍCE NA 10 SVĚTOVÝCH INDEXECH – pravidlo F55/F61, náklady 2 bp + swap −1 bp/noc")
    say("=" * 100)
    data, per_mk = [], {}
    for tk in TICK:
        d, dropped = load(tk)
        s, b = tom(d)
        data.append((s, b))
        v = ev([(s, b)])
        per_mk[tk] = v["diff"]
        say(f"   {tk:7s} {d.index[0].date()}–{d.index[-1].date()} | {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}"
            + (f" | vyřazené roky {dropped[0]}–{dropped[-1]} ({len(dropped)})" if dropped else ""))
    full = ev(data)
    ctl = ev(data, F.SPLIT, None)
    pre = ev(data, None, F.SPLIT)
    for nm, v in (("celé období", full), ("do 2018 (popis)", pre), ("2019–2026", ctl)):
        say(f"{nm:16s} signál {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    ys = sorted(set(full["s"].index.year))
    dif = {y: full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean() for y in ys}
    pos = [v > 0 for v in dif.values()]
    share = float(np.mean(pos))
    say("po letech převis: " + "  ".join(f"{y}:{v:+.2f}" for y, v in dif.items()))
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")
    npos = sum(v > 0 for v in per_mk.values())
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    c = []
    for nm, cond, val in (
            ("1) celé období: signál > 0, převis > 0, t >= 2,0", full["sig"]["m"] > 0 and full["diff"] > 0 and full["t"] >= 2.0,
             f"{full['sig']['m']:+.3f}, převis {full['diff']:+.3f}, t {full['t']:+.2f}"),
            ("2) 2019–2026: signál > 0 a převis > 0", ctl["sig"]["m"] > 0 and ctl["diff"] > 0, f"{ctl['sig']['m']:+.3f}, převis {ctl['diff']:+.3f}"),
            ("3) převis > 0 aspoň na 7 z 10 trhů", npos >= 7, f"{npos} z 10"),
            ("4) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")):
        say(f"   {nm}: {'ANO' if cond else 'NE'} ({val})")
        c.append(cond)
    say(f"   => {'NEZÁVISLÉ POTVRZENÍ F61 (prošlo vše)' if all(c) else 'NEPOTVRZENO'}")
    open(os.path.join(YD, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
