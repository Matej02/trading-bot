"""
Kontrola shody prop runneru s testy na historii (lednova brana): rozhodovaci funkce runneru (f2x_live pres run_prop)
na historickych datech Yahoo proti obchodum z testu F33 (research_data/f33/f33_yahoo.pkl) a RSI(2) (prop_meritko.rsi2_trades).
Spusteni: python -I parita.py -> research_data/prop/parita_prop_runneru.txt
"""
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scratch"))
import pandas as pd  # noqa: E402

import run_prop as R  # noqa: E402
import f42_rsi2 as F  # noqa: E402
import prop_meritko as PM  # noqa: E402

FX = R.FX
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def etf(tk):
    j = json.load(open(os.path.join(F.RD, "f33", "yahoo", f"{tk}.json")))["chart"]["result"][0]
    t = pd.to_datetime(j["timestamp"], unit="s").normalize()
    s = pd.Series(j["indicators"]["adjclose"][0]["adjclose"], index=t, dtype=float).dropna()
    return {d.date(): float(v) for d, v in s.items()}


def f33_parity():
    spy, tlt = etf("SPY"), etf("TLT")
    T = pd.read_pickle(os.path.join(F.RD, "f33", "f33_yahoo.pkl"))
    test = {pd.Timestamp(r.t).date(): int(r.d) for r in T[T.mk == "SPX500mini"].itertuples()}
    run = {}
    days = sorted(spy)
    for d in days:
        if d.year < 2003 or d > days[-1] or not FX.is_trading_day(d) or FX.trading_days_left(d) != 2:
            continue
        now = datetime(d.year, d.month, d.day, 9, 35, tzinfo=FX.NY)
        r = FX.f33_entry(now, spy, tlt)
        if r and r[0] in (1, -1):
            run[d] = r[0]
    lo, hi = max(min(test), min(run)), min(max(test), max(run))
    a = {d: v for d, v in test.items() if lo <= d <= hi}
    b = {d: v for d, v in run.items() if lo <= d <= hi}
    same = [d for d in a if b.get(d) == a[d]]
    only_t = sorted(set(a) - set(b))
    only_r = sorted(set(b) - set(a))
    dirdiff = [d for d in a if d in b and a[d] != b[d]]
    say(f"F33 {lo}–{hi}: test {len(a)} vstupů, runner {len(b)}, shoda {len(same)} ({len(same) / max(len(a), 1):.1%})")
    say(f"   jen v testu: {[str(x) for x in only_t[:12]]}{' …' if len(only_t) > 12 else ''}")
    say(f"   jen v runneru: {[str(x) for x in only_r[:12]]}{' …' if len(only_r) > 12 else ''}")
    say(f"   opačný směr: {[str(x) for x in dirdiff]}")
    return len(same), len(a)


def rsi2_parity(mk):
    d = F.yahoo(mk)
    d = d[d.index >= "2001-01-01"]
    rows = [(i.date(), float(r.open), float(r.high), float(r.low), float(r.close)) for i, r in d.iterrows()]
    days, closes = [r[0] for r in rows], [r[4] for r in rows]
    test = sorted(t["t_in"].date() for t in PM.rsi2_trades(mk, d=d) if t["t_in"] >= pd.Timestamp("2003-01-01"))
    run, i, n = [], 250, len(rows)
    while i < n - 1:
        ok, _ = FX.rsi2_signal(days[:i + 1], closes[:i + 1])
        a = R.atr20(rows[:i + 1])
        if not ok or not a:
            i += 1
            continue
        e = i + 1
        entry_day, E = days[e], rows[e][1]
        stop = E - 3 * a
        j = e
        while j < n:
            if rows[j][3] <= stop or FX.rsi2_exit(days[:j + 1], closes[:j + 1], entry_day):
                break
            j += 1
        if entry_day >= pd.Timestamp("2003-01-01").date():
            run.append(entry_day)
        i = j + 1 if j > i else i + 1
    st, sr = set(test), set(run)
    same = len(st & sr)
    say(f"RSI(2) {mk}: test {len(st)} vstupů, runner {len(sr)}, shoda {same} ({same / max(len(st), 1):.1%})"
        f" | jen v testu {sorted(str(x) for x in st - sr)[:6]} | jen v runneru {sorted(str(x) for x in sr - st)[:6]}")
    return same, len(st)


def main():
    say("Kontrola shody prop runneru s testy na historii (Yahoo, stejná data jako testy)")
    s, t = f33_parity()
    tot_s, tot_t = s, t
    for mk in R.RSI2_MARKETS:
        s, t = rsi2_parity(mk)
        tot_s, tot_t = tot_s + s, tot_t + t
    say(f"CELKEM shoda {tot_s}/{tot_t} ({tot_s / tot_t:.1%})")
    open(os.path.join(F.RD, "prop", "parita_prop_runneru.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
