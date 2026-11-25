"""
F86 riziko prizpusobene prop zkousce. Plan predem ve vaultu: Vyzkum/F86 Riziko prizpusobene prop zkousce.md (commit 7f6096b).
Spusteni: python -I f86_riziko_zkousky.py -> research_data/prop/f86_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import prop_meritko as PM  # noqa: E402

LINES = []
GRID = [round(x, 2) for x in np.arange(0.5, 3.01, 0.25)]
CAP = 3.0
NAMES = {0: "V0 pevné riziko", 1: "V1 riziko klesá s propadem", 2: "V2 strop otevřeného rizika 3 %", 3: "V3 = V1 + V2"}
EARLY = lambda S: S[S.st < "2015-01-01"]  # noqa: E731
LATE = lambda S: S[S.st >= "2015-01-01"]  # noqa: E731


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def one_dyn(P, r, start, mode):
    end = start + pd.DateOffset(months=PM.CAP_MONTHS)
    i0 = int(np.searchsorted(P.day_arr, np.datetime64(start)))
    phase, bal, tdays, phase_start, eq_prev = 0, 100.0, 0, start, 100.0
    open_ = {}
    last_entry, gap = start, False
    for day in P.days[i0:]:
        if day >= end:
            break
        rows = P.by_day[day]
        mid = bal
        open_risk = sum(open_.values())
        entered = False
        for (j, lo, cl, first, last) in rows:
            if not (first and day >= phase_start):
                continue
            rj = r
            if mode in (1, 3):
                rj = r * min(1.0, max(0.0, (eq_prev - 90.0) / 10.0))
            if mode in (2, 3):
                rj = min(rj, CAP - open_risk)
                if rj < 0.25 * r:
                    continue
            if rj <= 0:
                continue
            open_[j] = rj
            open_risk += rj
            entered = True
        worst, close_open, closed = bal, 0.0, 0.0
        for (j, lo, cl, first, last) in rows:
            rj = open_.get(j)
            if rj is None:
                continue
            worst += lo * rj
            if last:
                closed += cl * rj
                del open_[j]
            else:
                close_open += cl * rj
        if worst < mid - PM.DAY_LIMIT or worst < 100.0 - PM.MAX_LIMIT:
            return "propadl", (day - start).days / 30.44, gap
        bal += closed
        if entered:
            tdays += 1
            if (day - last_entry).days > PM.INACTIVE_DAYS:
                gap = True
            last_entry = day
        eq = bal + sum(0.0 for _ in ()) + close_open
        eq_prev = eq
        if eq >= 100.0 + PM.TARGETS[phase] and tdays >= PM.MIN_DAYS:
            if phase == 1:
                return "prosel", (day - start).days / 30.44, gap
            phase, bal, tdays, eq_prev = 1, 100.0, 0, 100.0
            open_ = {}
            phase_start = day + pd.Timedelta(days=1)
    return "vyprselo", np.nan, gap


def sim(P, r, mode):
    res = [(st,) + one_dyn(P, r, st, mode) for st in PM.STARTS]
    return pd.DataFrame(res, columns=["st", "out", "months", "gap"])


def line(s):
    return f"P12 {s['p12']:4.0%} P24 {s['p24']:4.0%} P36 {s['p36']:4.0%} propadlo {s['fail']:4.0%} medián {s['med']:5.1f}"


def main():
    f3 = PM.f33_trades()
    rs = {mk: [t for t in PM.rsi2_trades(mk) if t["t_in"] >= pd.Timestamp("2003-01-01")] for mk in F.US}
    trades = f3 + rs["SPX500mini"] + rs["NAS100mini"] + rs["US30mini"]   # poradi = prednost pri vstupu ve stejny den
    P = PM.Portfolio(trades)
    say("F86 Riziko přizpůsobené prop zkoušce FTMO 2 kroky — F33 + RSI(2), pravidla a simulace jako v měřítku")
    say(f"Vývoj = starty 2003–2014 ({(PM.STARTS < '2015-01-01').sum()}), kontrola = starty 2015–2023 ({(PM.STARTS >= '2015-01-01').sum()})")
    # kontrola shody V0 s meritkem
    ref = PM.summarize(PM.simulate(P, 1.0))
    v0 = PM.summarize(sim(P, 1.0, 0))
    say(f"Shoda V0 s měřítkem při 1 %: měřítko {line(ref)} | V0 {line(v0)}")
    R = {}
    for mode in range(4):
        say(f"\n=== {NAMES[mode]} ===")
        say("  r %  | vývoj (2003–14)                                   | kontrola (2015–23)                                | celé")
        for r in GRID:
            S = sim(P, r, mode)
            a, e, lt = PM.summarize(S), PM.summarize(EARLY(S)), PM.summarize(LATE(S))
            R[(mode, r)] = (a, e, lt)
            say(f"  {r:4.2f} | {line(e)} | {line(lt)} | propadlo {a['fail']:4.0%}")
    base = R[(0, 1.0)]
    say(f"\nSrovnávací bod V0 při 1,0 %: vývoj P24 {base[1]['p24']:.0%}, kontrola P24 {base[2]['p24']:.0%}")
    say("\nROZHODNUTÍ podle pravidel zapsaných předem (r* = nejvyšší r s propadlo ≤ 10 % na vývoji)")
    best = None
    for mode in range(4):
        ok_r = [r for r in GRID if R[(mode, r)][1]["fail"] <= 0.10]
        if not ok_r:
            say(f"  {NAMES[mode]}: žádné r s propady ≤ 10 % na vývoji")
            continue
        rs_ = max(ok_r)
        a, e, lt = R[(mode, rs_)]
        c1 = lt["fail"] <= 0.10
        c2 = a["fail"] <= 0.10
        c3 = e["p24"] >= base[1]["p24"] + 0.10 and lt["p24"] >= base[2]["p24"] + 0.10
        say(f"  {NAMES[mode]}: r* = {rs_} %")
        say(f"     vývoj    {line(e)}")
        say(f"     kontrola {line(lt)}")
        say(f"     celé     {line(a)}")
        if mode == 0:
            say("     (V0 je srovnání; jen popis, jak by dopadlo pevné riziko vybrané na starších letech)")
            continue
        say(f"     1) kontrola propadlo ≤ 10 %: {'ANO' if c1 else 'NE'} | 2) celé propadlo ≤ 10 %: {'ANO' if c2 else 'NE'} | "
            f"3) P24 +10 p. b. ve vývoji i kontrole: {'ANO' if c3 else 'NE'} → {'POMÁHÁ' if c1 and c2 and c3 else 'NEPOMÁHÁ'}")
        if c1 and c2 and c3 and (best is None or lt["p24"] > best[2]):
            best = (mode, rs_, lt["p24"])
    if best:
        say(f"\n=> DOPORUČENÍ: {NAMES[best[0]]} se základním rizikem {best[1]} % (kontrola P24 {best[2]:.0%})")
    else:
        say("\n=> Žádná varianta podle pravidel nepomáhá; zůstává V0 při 1,0 %.")
    open(os.path.join(PM.OUT, "f86_souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
