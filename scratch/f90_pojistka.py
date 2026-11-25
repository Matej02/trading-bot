"""
F90 denni pojistka na cely ucet. Plan predem: Vyzkum/F90 Denni pojistka na cely ucet.md (commit fda73e9).
Bot ani runner se nemeni. Spusteni: python -I f90_pojistka.py -> research_data/prop/f90_souhrn.txt
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import prop_meritko as PM  # noqa: E402
import f87_f33_stop as F87  # noqa: E402

LINES = []
GRID = [round(x, 2) for x in np.arange(0.5, 4.01, 0.25)]
MARGINS = (0.5, 1.0, 1.5, 2.0)
SLIP, SLIP_HI = 0.1, 0.25
EARLY = lambda S: S[S.st < "2015-01-01"]  # noqa: E731
LATE = lambda S: S[S.st >= "2015-01-01"]  # noqa: E731


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


# ---------------------------------------------------------------- otevirací cena v R pro kazdy den obchodu
def open_map(trades):
    """{(j, den): open_R}. RSI(2): long, E = open vstupu, jednotka 3 ATR(20) den pred vstupem. F33: smer z f33_yahoo.pkl."""
    T = pd.read_pickle(os.path.join(F.RD, "f33", "f33_yahoo.pkl"))
    sgn33 = {(t.mk, pd.Timestamp(t.t)): float(t.d) for _, t in T.iterrows()}
    cache, OP = {}, {}
    for j, t in enumerate(trades):
        mk = t["mk"]
        if mk not in cache:
            d = F.yahoo(mk)
            cache[mk] = (d, PM._atr20(d))
        d, A = cache[mk]
        i = d.index.get_loc(t["t_in"])
        unit, E = 3 * A.iloc[i - 1], d.open.iloc[i]
        sg = sgn33[(mk, t["t_in"])] if t["s"] == "F33" else 1.0
        for (day, lo, cl) in t["path"]:
            OP[(j, pd.Timestamp(day))] = sg * (d.open.loc[day] - E) / unit
    return OP


# ---------------------------------------------------------------- zkouska 2 kroky s pojistkou
def two_step_g(P, OP, r, start, M=None, slip=SLIP, months=36, trig=None):
    """M=None = bez pojistky (shodne s F89.two_step). Vraci (vysledek, mesice, den_projiti)."""
    end = start + pd.DateOffset(months=months)
    i0 = int(np.searchsorted(P.day_arr, np.datetime64(start)))
    phase, bal, tdays, ps = 0, 100.0, 0, start
    open_ = set()
    for day in P.days[i0:]:
        if day >= end:
            break
        rows = P.by_day[day]
        L = max(bal - 5.0, 90.0)
        held = [(j, lo, cl, last) for (j, lo, cl, first, last) in rows if j in open_ and not first]
        new = [(j, lo, cl, last) for (j, lo, cl, first, last) in rows if first and day >= ps]
        if M is not None and held:
            eq_open = bal + r * sum(OP[(j, day)] for (j, _, _, _) in held)
            if eq_open <= L + M:                       # gap pres pojistku na otevreni
                eq_x = eq_open - slip * r * len(held)
                if eq_open < L or eq_x < L:
                    return "propadl", (day - start).days / 30.44, day
                bal = eq_x
                open_ -= {j for (j, _, _, _) in held}
                if trig is not None:
                    trig.append(day)
                continue                               # nove vstupy ten den se neotviraji
        for (j, _, _, _) in new:
            open_.add(j)
        act = held + new
        worst = bal + r * sum(lo for (_, lo, _, _) in act)
        if M is not None and act and worst <= L + M:   # pojistka behem dne
            eq_x = L + M - slip * r * len(act)
            if eq_x < L:
                return "propadl", (day - start).days / 30.44, day
            bal = eq_x
            open_ -= {j for (j, _, _, _) in act}
            tdays += bool(new)
            if trig is not None:
                trig.append(day)
            continue
        if worst < L:
            return "propadl", (day - start).days / 30.44, day
        closed = r * sum(cl for (j, _, cl, last) in act if last)
        co = r * sum(cl for (j, _, cl, last) in act if not last)
        open_ -= {j for (j, _, _, last) in act if last}
        bal += closed
        tdays += bool(new)
        if bal + co >= 100.0 + PM.TARGETS[phase] and tdays >= PM.MIN_DAYS:
            if phase == 1:
                return "prosel", (day - start).days / 30.44, day
            phase, bal, tdays = 1, 100.0, 0
            open_ = set()
            ps = day + pd.Timedelta(days=1)
    return "vyprselo", np.nan, None


def funded_g(P, OP, r, start, M, months=12):
    """Financovany ucet 2 kroky (denni 5 %, celkem 10 % staticky) s pojistkou, bez cile a vyberu."""
    end = start + pd.DateOffset(months=months)
    i0 = int(np.searchsorted(P.day_arr, np.datetime64(start)))
    bal, open_ = 100.0, set()
    for day in P.days[i0:]:
        if day >= end:
            break
        rows = P.by_day[day]
        L = max(bal - 5.0, 90.0)
        held = [(j, lo, cl, last) for (j, lo, cl, first, last) in rows if j in open_ and not first]
        new = [(j, lo, cl, last) for (j, lo, cl, first, last) in rows if first and day >= start]
        if M is not None and held:
            eq_open = bal + r * sum(OP[(j, day)] for (j, _, _, _) in held)
            if eq_open <= L + M:
                eq_x = eq_open - SLIP * r * len(held)
                if eq_open < L or eq_x < L:
                    return False, np.nan
                bal = eq_x
                open_ -= {j for (j, _, _, _) in held}
                continue
        for (j, _, _, _) in new:
            open_.add(j)
        act = held + new
        worst = bal + r * sum(lo for (_, lo, _, _) in act)
        if M is not None and act and worst <= L + M:
            eq_x = L + M - SLIP * r * len(act)
            if eq_x < L:
                return False, np.nan
            bal = eq_x
            open_ -= {j for (j, _, _, _) in act}
            continue
        if worst < L:
            return False, np.nan
        bal += r * sum(cl for (j, _, cl, last) in act if last)
        open_ -= {j for (j, _, _, last) in act if last}
    return True, bal - 100.0


def sim(P, OP, r, M, slip=SLIP, trig=None):
    res = [(st,) + two_step_g(P, OP, r, st, M, slip, trig=trig) for st in PM.STARTS]
    return pd.DataFrame(res, columns=["st", "out", "months", "pday"]).assign(gap=False)


def line(s):
    return f"P12 {s['p12']:4.0%} P24 {s['p24']:4.0%} P36 {s['p36']:4.0%} propadlo {s['fail']:4.0%} medián {s['med']:5.1f}"


def main():
    _, f3s = F87.f33_trades_stop()
    rs = [t for mk in F.US for t in PM.rsi2_trades(mk) if t["t_in"] >= pd.Timestamp("2003-01-01")]
    trades = f3s + rs
    P = PM.Portfolio(trades)
    OP = open_map(trades)
    say("F90 Denní pojistka na celý účet — FTMO 2 kroky, F33 se stopem + RSI(2), starty 2003–2023, nejdéle 36 měsíců")
    say(f"Pojistka: zavřít vše při equity ≤ L + M, L = max(půlnoční zůstatek − 5 %, 90 %); skluz {SLIP} R na pozici, gap na otevření za open.")
    say(f"Obchodů {len(trades)} (F33 {len(f3s)}, RSI(2) {len(rs)})")

    R = {}
    for M in (None,) + MARGINS:
        say(f"\n=== {'BEZ POJISTKY (základ)' if M is None else f'POJISTKA M = {M} % (denně −{5 - M:g} %, celkem {90 + M:g} %)'} ===")
        say("  r %  | celé                                               | vývoj 2003–14                                     | kontrola 2015–23")
        for r in GRID:
            if M is None and r > 3.0:
                continue
            S = sim(P, OP, r, M)
            a, e, lt = PM.summarize(S), PM.summarize(EARLY(S)), PM.summarize(LATE(S))
            R[(M, r)] = (a, e, lt)
            say(f"  {r:4.2f} | {line(a)} | {line(e)} | {line(lt)}")

    b_all, b_e, b_l = R[(None, 1.25)]
    say(f"\nKontrola shody se F87/F89 při 1,25 % bez pojistky: {line(b_all)} (má být P24 17 %, P36 65 %, propadlo 3 %, medián 27,2)")

    say("\nBEZPEČNÉ RIZIKO na celém období (propadlo ≤ 10 %), jen popis:")
    for M in (None,) + MARGINS:
        safe = [r for r in GRID if (M, r) in R and R[(M, r)][0]["fail"] <= 0.10]
        if safe:
            r0 = max(safe)
            say(f"  {'bez pojistky' if M is None else f'M = {M}'}: {r0} % → {line(R[(M, r0)][0])}")

    say("\nVÝBĚR NA VÝVOJI (starty 2003–2014):")
    cand = []
    for M in MARGINS:
        ok = [r for r in GRID if R[(M, r)][1]["fail"] <= 0.10]
        if not ok:
            say(f"  M = {M}: žádné riziko s propady ≤ 10 % ve vývoji")
            continue
        r_ = max(ok)
        e = R[(M, r_)][1]
        cand.append((e["p24"], -(e["med"] if e["med"] == e["med"] else 99), M, r_))
        say(f"  M = {M}: r_vývoj {r_} % → vývoj {line(e)}")
    if not cand:
        say("\n=> ROZHODNUTÍ: NE (žádná varianta)")
        open(os.path.join(PM.OUT, "f90_souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
        return
    _, _, Ms, rs_ = max(cand)
    a, e, lt = R[(Ms, rs_)]
    say(f"  → M* = {Ms} %, r* = {rs_} %")
    say(f"\nPŘI M* = {Ms}, r* = {rs_}:")
    say(f"  celé    {line(a)}")
    say(f"  vývoj   {line(e)}   | základ 1,25 % bez pojistky: {line(b_e)}")
    say(f"  kontrola {line(lt)}   | základ 1,25 % bez pojistky: {line(b_l)}")

    ok1 = e["fail"] <= 0.10 and lt["fail"] <= 0.10

    def better(x, b):
        med_ok = x["med"] == x["med"] and b["med"] == b["med"] and x["med"] <= 0.8 * b["med"]
        return med_ok or x["p12"] >= b["p12"] + 0.10
    ok2 = better(e, b_e) and better(lt, b_l)
    Sh = sim(P, OP, rs_, Ms, slip=SLIP_HI)
    eh, lh = PM.summarize(EARLY(Sh)), PM.summarize(LATE(Sh))
    ok3 = eh["fail"] <= 0.15 and lh["fail"] <= 0.15
    say(f"  skluz {SLIP_HI} R: vývoj {line(eh)} | kontrola {line(lh)}")
    say(f"\n  1) propadlo ≤ 10 % ve vývoji i kontrole: {'ANO' if ok1 else 'NE'}")
    say(f"  2) medián −20 % nebo P12 +10 p. b. proti základu ve vývoji i kontrole: {'ANO' if ok2 else 'NE'}")
    say(f"  3) skluz 0,25 R: propadlo ≤ 15 % ve vývoji i kontrole: {'ANO' if ok3 else 'NE'}")
    say(f"\n=> ROZHODNUTÍ podle pravidla zapsaného předem: {'ANO' if ok1 and ok2 and ok3 else 'NE'}")

    # popis: zasahy pojistky a financovany ucet
    trig = []
    S = sim(P, OP, rs_, Ms, trig=trig)
    cnt = Counter(trig)
    say(f"\nZÁSAHY POJISTKY při M* a r*: {len(cnt)} různých dnů; nejčastější (počet startů, kde zasáhla):")
    say("  " + ", ".join(f"{d.date()} ({n}×)" for d, n in cnt.most_common(12)))
    fails = S[S.out == "propadl"]
    if len(fails):
        say("  propadlé starty: " + ", ".join(f"{s.date()}→{p.date()}" for s, p in zip(fails.st, fails.pday)))
    for M, r in ((None, 1.25), (Ms, rs_)):
        Sx = sim(P, OP, r, M)
        fr = [funded_g(P, OP, r, d + pd.Timedelta(days=1), M) for d in Sx[Sx.out == "prosel"].pday]
        if fr:
            surv = np.mean([x[0] for x in fr])
            gain = np.nanmedian([x[1] for x in fr if x[0]]) if any(x[0] for x in fr) else np.nan
            say(f"  financovaný účet 12 m po projití ({'bez pojistky' if M is None else f'M = {M}'}, {r} %): "
                f"přežije {surv:.0%}, medián zisku {gain:+.1f} % (n {len(fr)})")
    open(os.path.join(PM.OUT, "f90_souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
