"""
F91 pravidla prop firem v meritku. Plan predem: Vyzkum/F91 Pravidla prop firem v meritku.md (commit 617bf8a).
Bot ani runner se nemeni. Spusteni: python -I f91_firmy.py -> research_data/prop/f91_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import prop_meritko as PM  # noqa: E402
import f87_f33_stop as F87  # noqa: E402

LINES = []
GRID = [round(x, 2) for x in np.arange(0.5, 3.01, 0.25)]
EARLY = lambda S: S[S.st < "2015-01-01"]  # noqa: E731
LATE = lambda S: S[S.st >= "2015-01-01"]  # noqa: E731
# ref: ftmo = pulnocni zustatek - pct % pocatecniho; maxbe = vyssi z (zustatek, equity) na konci predchoziho dne x (1 - pct);
#      eq = equity na konci predchoziho dne x (1 - pct); bal = zustatek na konci predchoziho dne x (1 - pct)
# dtype: entry = den se vstupem; profit = zisk dne >= 0,5 %; open = den s otevrenou pozici
RULES = {
    "FTMO 2 kroky": dict(T=(10.0, 5.0), ref="ftmo", pct=5.0, mind=4, dtype="entry", fee="540 €"),
    "The5ers Classic, denní 5 %": dict(T=(8.0, 5.0), ref="maxbe", pct=5.0, mind=3, dtype="profit", fee="179 $"),
    "The5ers Classic, denní 3 %": dict(T=(8.0, 5.0), ref="maxbe", pct=3.0, mind=3, dtype="profit", fee="179 $"),
    "Fintokei ProTrader": dict(T=(8.0, 6.0), ref="eq", pct=5.0, mind=3, dtype="open", warn=True, fee="549 $"),
    "Fintokei Swing": dict(T=(8.0, 6.0), ref="bal", pct=5.0, mind=3, dtype="open", warn=True, fee="679 $"),
}


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def run(P, r, start, R, months=36):
    end = start + pd.DateOffset(months=months)
    i0 = int(np.searchsorted(P.day_arr, np.datetime64(start)))
    phase, bal, eqp, days, ps = 0, 100.0, 100.0, 0, start
    open_ = set()
    warns, last_entry, gap = 0, start, False
    k = 1.0 - R["pct"] / 100.0
    for day in P.days[i0:]:
        if day >= end:
            break
        rows = P.by_day[day]
        mid = bal
        if R["ref"] == "ftmo":
            floor = mid - R["pct"]
        elif R["ref"] == "maxbe":
            floor = max(mid, eqp) * k
        elif R["ref"] == "eq":
            floor = eqp * k
        else:
            floor = mid * k
        floor = max(floor, 90.0)
        entered, act = False, []
        for (j, lo, cl, first, last) in rows:
            if first and day >= ps:
                open_.add(j)
                entered = True
            if j in open_:
                act.append((j, lo, cl, last))
        w = r * sum(a[1] for a in act)
        if R.get("warn") and w <= -3.0:
            warns += 1
        if bal + w < floor:
            return "propadl", (day - start).days / 30.44, gap, warns
        bal += r * sum(a[2] for a in act if a[3])
        co = r * sum(a[2] for a in act if not a[3])
        open_ -= {a[0] for a in act if a[3]}
        eq = bal + co
        if entered:
            if (day - last_entry).days > PM.INACTIVE_DAYS:
                gap = True
            last_entry = day
        if R["dtype"] == "entry":
            cnt = entered
        elif R["dtype"] == "open":
            cnt = bool(act)
        else:
            cnt = min(bal, eq) - mid >= 0.5
        if eq >= 100.0 + R["T"][phase]:
            cnt_pass = (eq - mid >= 0.5) if R["dtype"] == "profit" else cnt
            if days + cnt_pass >= R["mind"]:
                if phase == 1:
                    return "prosel", (day - start).days / 30.44, gap, warns
                phase, bal, eqp, days = 1, 100.0, 100.0, 0
                open_ = set()
                ps = day + pd.Timedelta(days=1)
                continue
        days += cnt
        eqp = eq
    return "vyprselo", np.nan, gap, warns


def sim(P, r, R):
    res = [(st,) + run(P, r, st, R) for st in PM.STARTS]
    return pd.DataFrame(res, columns=["st", "out", "months", "gap", "warns"])


def line(s):
    return f"P12 {s['p12']:4.0%} P24 {s['p24']:4.0%} P36 {s['p36']:4.0%} propadlo {s['fail']:4.0%} medián {s['med']:5.1f}"


def main():
    _, f3s = F87.f33_trades_stop()
    rs = [t for mk in F.US for t in PM.rsi2_trades(mk) if t["t_in"] >= pd.Timestamp("2003-01-01")]
    P = PM.Portfolio(f3s + rs)
    say("F91 Pravidla prop firem v měřítku — F33 se stopem + RSI(2), starty 2003–2023, nejdéle 36 měsíců, účet 100k")
    say("FundedNext Stellar vyřazen předem: EA na účtech od 50 000 nepovolené.")
    RES = {}
    for nm, R in RULES.items():
        say(f"\n=== {nm}: cíl {R['T'][0]:g} % + {R['T'][1]:g} %, denní {R['pct']:g} % ({R['ref']}), min. {R['mind']} dny ({R['dtype']}) ===")
        say("  r %  | celé                                               | vývoj 2003–14 | kontrola 2015–23 | mezera>30 d"
            + (" | zkoušek s varováním" if R.get("warn") else ""))
        for r in GRID:
            S = sim(P, r, R)
            a, e, lt = PM.summarize(S), PM.summarize(EARLY(S)), PM.summarize(LATE(S))
            wsh = (S.warns > 0).mean()
            RES[(nm, r)] = (a, e, lt, wsh)
            say(f"  {r:4.2f} | {line(a)} | P24 {e['p24']:4.0%} prop. {e['fail']:4.0%} | P24 {lt['p24']:4.0%} prop. {lt['fail']:4.0%} | {a['gap']:4.0%}"
                + (f" | {wsh:4.0%}" if R.get("warn") else ""))

    say("\nPROVOZNÍ RIZIKO (propadlo ≤ 10 % na celém období; u Fintokei i varování ≤ 10 % zkoušek):")
    op = {}
    for nm, R in RULES.items():
        ok = [r for r in GRID if RES[(nm, r)][0]["fail"] <= 0.10 and (not R.get("warn") or RES[(nm, r)][3] <= 0.10)]
        if not ok:
            say(f"  {nm}: žádné")
            continue
        r0 = max(ok)
        a, e, lt, wsh = RES[(nm, r0)]
        op[nm] = (r0, a, e, lt)
        cost = f"{R['fee']} / P36 = {float(R['fee'].split()[0]) / a['p36']:,.0f} {R['fee'].split()[1]}" if a["p36"] > 0 else "–"
        rdev = max([r for r in GRID if RES[(nm, r)][1]["fail"] <= 0.10] or [np.nan])
        ctl = RES[(nm, rdev)][2] if rdev == rdev else None
        say(f"  {nm}: {r0} % → {line(a)} | vývoj prop. {e['fail']:.0%}, kontrola prop. {lt['fail']:.0%}"
            + (f" | varování {wsh:.0%}" if R.get("warn") else "") + f" | poplatek za projití {cost}")
        if R.get("warn"):
            ok_f = [r for r in GRID if RES[(nm, r)][0]["fail"] <= 0.10]
            if ok_f and max(ok_f) != r0:
                say(f"      (bez podmínky varování by bylo {max(ok_f)} %: {line(RES[(nm, max(ok_f))][0])}, varování {RES[(nm, max(ok_f))][3]:.0%})")
        if ctl is not None:
            say(f"      kontrolně r* z vývoje {rdev} % → kontrola {line(ctl)}")

    base = op["FTMO 2 kroky"][1]["p24"]
    say(f"\nShoda FTMO se F89: {line(op['FTMO 2 kroky'][1])} při {op['FTMO 2 kroky'][0]} % (F89: P24 17 %, P36 65 %, propadlo 3 %, medián 27,2)")
    say("\nROZHODNUTÍ (změna první volby jen když P24 ≥ FTMO + 10 p. b. a propadlo ≤ 10 % ve vývoji i kontrole; u The5ers pro 5 % i 3 %):")

    def ok_firm(nm):
        if nm not in op:
            return False
        _, a, e, lt = op[nm]
        return a["p24"] >= base + 0.10 and e["fail"] <= 0.10 and lt["fail"] <= 0.10
    cands = []
    for nm in RULES:
        if nm.startswith("FTMO"):
            continue
        good = ok_firm(nm)
        say(f"  {nm}: {'splňuje' if good else 'nesplňuje'}" + (f" (P24 {op[nm][1]['p24']:.0%} proti {base:.0%})" if nm in op else ""))
    t5 = ok_firm("The5ers Classic, denní 5 %") and ok_firm("The5ers Classic, denní 3 %")
    if t5:
        cands.append(("The5ers High Stakes Classic", min(op["The5ers Classic, denní 5 %"][1]["p24"], op["The5ers Classic, denní 3 %"][1]["p24"])))
    for nm in ("Fintokei ProTrader", "Fintokei Swing"):
        if ok_firm(nm):
            cands.append((nm, op[nm][1]["p24"]))
    if cands:
        win = max(cands, key=lambda x: x[1])
        say(f"\n=> ROZHODNUTÍ podle pravidla zapsaného předem: nová první volba {win[0]} (P24 {win[1]:.0%} proti FTMO {base:.0%})")
    else:
        say("\n=> ROZHODNUTÍ podle pravidla zapsaného předem: FTMO 2 kroky zůstává první volbou")
    open(os.path.join(PM.OUT, "f91_souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
