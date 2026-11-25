"""
F89 porovnani zkousek FTMO 1 krok a 2 kroky. Plan predem: Vyzkum/F89 Porovnani zkousek FTMO 1 krok a 2 kroky.md (commit 8c357de).
Bot ani runner se nemeni. Spusteni: python -I f89_typy_zkousek.py -> research_data/prop/f89_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import prop_meritko as PM  # noqa: E402
import f87_f33_stop as F87  # noqa: E402
import f86_riziko_zkousky as F86  # noqa: E402

LINES = []
GRID = F86.GRID
FEE = {"2": 540.0, "1": 499.0}


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def _day_step(P, day, open_, start_ok, r):
    rows = P.by_day[day]
    worst_d, close_open, closed, entered = 0.0, 0.0, 0.0, False
    for (j, lo, cl, first, last) in rows:
        if first and start_ok(day):
            open_.add(j)
            entered = True
        if j not in open_:
            continue
        worst_d += lo * r
        if last:
            closed += cl * r
            open_.discard(j)
        else:
            close_open += cl * r
    return worst_d, close_open, closed, entered


def two_step(P, r, start, months=36):
    """Jako meritko; vraci (vysledek, mesice, den_projiti)."""
    end = start + pd.DateOffset(months=months)
    i0 = int(np.searchsorted(P.day_arr, np.datetime64(start)))
    phase, bal, tdays, ps = 0, 100.0, 0, start
    open_ = set()
    for day in P.days[i0:]:
        if day >= end:
            break
        mid = bal
        w, co, cl, ent = _day_step(P, day, open_, lambda d: d >= ps, r)
        if bal + w < mid - 5.0 or bal + w < 90.0:
            return "propadl", (day - start).days / 30.44, day
        bal += cl
        tdays += ent
        if bal + co >= 100.0 + PM.TARGETS[phase] and tdays >= 4:
            if phase == 1:
                return "prosel", (day - start).days / 30.44, day
            phase, bal, tdays = 1, 100.0, 0
            open_ = set()
            ps = day + pd.Timedelta(days=1)
    return "vyprselo", np.nan, None


def one_step(P, r, start, months=36):
    end = start + pd.DateOffset(months=months)
    i0 = int(np.searchsorted(P.day_arr, np.datetime64(start)))
    bal, peak = 100.0, 100.0
    open_ = set()
    dprof = []
    for day in P.days[i0:]:
        if day >= end:
            break
        mid, lim = bal, peak - 10.0
        w, co, cl, ent = _day_step(P, day, open_, lambda d: d >= start, r)
        if bal + w < mid - 3.0 or bal + w < lim:
            return "propadl", (day - start).days / 30.44, day
        bal += cl
        eq = bal + co
        if eq >= 110.0:
            best = max(max(dprof, default=0.0), cl + co)
            if best <= 0.5 * (eq - 100.0):
                return "prosel", (day - start).days / 30.44, day
        dprof.append(cl)
        peak = max(peak, bal)
    return "vyprselo", np.nan, None


def funded(P, r, start, typ, months=12):
    """Financovany ucet bez cile a bez vyberu: (prezil, zustatek na konci)."""
    end = start + pd.DateOffset(months=months)
    i0 = int(np.searchsorted(P.day_arr, np.datetime64(start)))
    bal, peak = 100.0, 100.0
    open_ = set()
    for day in P.days[i0:]:
        if day >= end:
            break
        mid = bal
        w, co, cl, ent = _day_step(P, day, open_, lambda d: d >= start, r)
        if typ == "2":
            bad = bal + w < mid - 5.0 or bal + w < 90.0
        else:
            bad = bal + w < mid - 3.0 or bal + w < peak - 10.0
        if bad:
            return False, np.nan
        bal += cl
        peak = max(peak, bal)
    return True, bal - 100.0


def sim(P, r, typ):
    f = two_step if typ == "2" else one_step
    res = [(st,) + f(P, r, st) for st in PM.STARTS]
    return pd.DataFrame(res, columns=["st", "out", "months", "pday"]).assign(gap=False)


def line(s):
    return f"P12 {s['p12']:4.0%} P24 {s['p24']:4.0%} P36 {s['p36']:4.0%} propadlo {s['fail']:4.0%} medián {s['med']:5.1f}"


def main():
    _, f3s = F87.f33_trades_stop()
    rs = [t for mk in F.US for t in PM.rsi2_trades(mk) if t["t_in"] >= pd.Timestamp("2003-01-01")]
    P = PM.Portfolio(f3s + rs)
    say("F89 Porovnání zkoušek FTMO 1 krok a 2 kroky — F33 se stopem + RSI(2), starty 2003–2023, nejdéle 36 měsíců")
    chk = PM.summarize(sim(P, 1.25, "2"))
    say(f"Kontrola shody 2 kroků s F87 při 1,25 %: {line(chk)} (F87: P24 17 %, P36 65 %, propadlo 3 %, medián 27,2)")
    R = {}
    for typ, nm in (("2", "2 KROKY (+10 %, +5 %; denní 5 %; celkem 10 % statický; 4 dny)"),
                    ("1", "1 KROK (+10 %; denní 3 %; celkem 10 % posuvný; konzistence 50 %)")):
        say(f"\n=== {nm} ===")
        say("  r %  | celé                                              | vývoj 2003–14 | kontrola 2015–23")
        for r in GRID:
            S = sim(P, r, typ)
            a, e, lt = PM.summarize(S), PM.summarize(F86.EARLY(S)), PM.summarize(F86.LATE(S))
            R[(typ, r)] = (a, e, lt, S)
            say(f"  {r:4.2f} | {line(a)} | P24 {e['p24']:4.0%} prop. {e['fail']:4.0%} | P24 {lt['p24']:4.0%} prop. {lt['fail']:4.0%}")
    say("\nSROVNÁNÍ při bezpečném riziku (celé období, propadlo ≤ 10 %)")
    best = {}
    for typ, nm in (("2", "2 kroky"), ("1", "1 krok")):
        safe = [r for r in GRID if R[(typ, r)][0]["fail"] <= 0.10]
        if not safe:
            say(f"  {nm}: žádné bezpečné riziko")
            continue
        r0 = max(safe)
        a = R[(typ, r0)][0]
        rdev = max([r for r in GRID if R[(typ, r)][1]["fail"] <= 0.10] or [np.nan])
        lt = R[(typ, rdev)][2] if rdev == rdev else None
        cost = FEE[typ] / a["p36"] if a["p36"] > 0 else np.inf
        best[typ] = (r0, a, cost)
        say(f"  {nm}: bezpečné riziko {r0} % → {line(a)} | cena za projitou zkoušku ~{cost:,.0f} € (poplatek {FEE[typ]:.0f} € / P36)"
            + (" — u 2 kroků se poplatek vrací s první odměnou" if typ == "2" else " — nevratný"))
        if lt is not None:
            say(f"      kontrolně: r* z vývoje {rdev} % → kontrola {line(lt)}")
        # financovany ucet 12 mesicu po projiti (popis)
        S = R[(typ, r0)][3]
        fr = [funded(P, r0, d + pd.Timedelta(days=1), typ) for d in S[S.out == "prosel"].pday]
        if fr:
            surv = np.mean([x[0] for x in fr])
            gain = np.nanmedian([x[1] for x in fr if x[0]]) if any(x[0] for x in fr) else np.nan
            say(f"      financovaný účet 12 měsíců po projití: přežije {surv:.0%}, medián zisku {gain:+.1f} % (bez výběrů)")
    if len(best) == 2:
        p2, p1 = best["2"][1]["p24"], best["1"][1]["p24"]
        if abs(p2 - p1) > 0.05:
            win = "2 kroky" if p2 > p1 else "1 krok"
            why = f"vyšší P24 ({max(p2, p1):.0%} proti {min(p2, p1):.0%})"
        else:
            win = "2 kroky" if best["2"][2] <= best["1"][2] else "1 krok"
            why = f"P24 do 5 p. b. ({p2:.0%} / {p1:.0%}), rozhoduje nižší cena za projití"
        say(f"\n=> ROZHODNUTÍ podle pravidla zapsaného předem: {win} ({why})")
    open(os.path.join(PM.OUT, "f89_souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
