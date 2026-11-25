"""
F87 meritko s F33 se stopem 3 ATR jako v runneru. Plan predem: Vyzkum/F87 Meritko s F33 se stopem jako v runneru.md (commit 420cdcb).
Bot ani runner se nemeni. Spusteni: python -I f87_f33_stop.py -> research_data/prop/f87_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import prop_meritko as PM  # noqa: E402
import f86_riziko_zkousky as F86  # noqa: E402

LINES = []
GRID = F86.GRID


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def f33_trades_stop():
    """F33 jako PM.f33_trades, navic stop 3 ATR(20) = -1 jednotka. Vraci (bez_stopu, se_stopem)."""
    T = pd.read_pickle(os.path.join(F.RD, "f33", "f33_yahoo.pkl"))
    plain, stop = [], []
    cache = {}
    for _, t in T.iterrows():
        mk = t.mk
        if mk not in cache:
            dd = F.yahoo(mk)
            cache[mk] = (dd, PM._atr20(dd))
        d, A = cache[mk]
        t_in = pd.Timestamp(t.t)
        t_out = t_in + pd.offsets.BMonthEnd(0)
        if t_in not in d.index:
            continue
        i = d.index.get_loc(t_in)
        unit = 3 * A.iloc[i - 1]
        if not unit > 0:
            continue
        E, sgn = d.open.iloc[i], float(t.d)
        R = float(t.R) / 3.0
        seg = d.loc[t_in:t_out]
        if not len(seg):
            continue
        rows = []
        for day, r in seg.iterrows():
            worst = (r.low - E) / unit if sgn > 0 else (E - r.high) / unit
            rows.append((day, worst, sgn * (r.close - E) / unit, sgn * (r.open - E) / unit))
        cost = R - rows[-1][2]                      # naklady testu (R po nakladech - hruby vysledek na zavreni)
        p_plain = [(a, b, c) for a, b, c, _ in rows]
        p_plain[-1] = (p_plain[-1][0], min(p_plain[-1][1], R), R)
        plain.append(dict(s="F33", mk=mk, t_in=t_in, t_out=p_plain[-1][0], R=R, path=p_plain, stopped=False))
        ps, Rs, hit = [], None, False
        for q, (day, worst, cl, op) in enumerate(rows):
            if q > 0 and op <= -1.0:
                Rs = op + cost
                ps.append((day, Rs, Rs))
                hit = True
                break
            if worst <= -1.0:
                Rs = -1.0 + cost
                ps.append((day, Rs, Rs))
                hit = True
                break
            ps.append((day, worst, cl))
        if not hit:
            Rs = R
            ps[-1] = (ps[-1][0], min(ps[-1][1], R), R)
        stop.append(dict(s="F33", mk=mk, t_in=t_in, t_out=ps[-1][0], R=Rs, path=ps, stopped=hit))
    return plain, stop


def line(s):
    return f"P12 {s['p12']:4.0%} P24 {s['p24']:4.0%} P36 {s['p36']:4.0%} propadlo {s['fail']:4.0%} medián {s['med']:5.1f}"


def main():
    plain, stop = f33_trades_stop()
    say("F87 Měřítko s F33 se stopem 3 ATR(20) jako v runneru (bot ani runner se nemění)")
    say("=" * 100)
    say(f"F33 obchodů {len(stop)}, zastaveno {sum(t['stopped'] for t in stop)}")
    worse = False
    for nm, a, b in (("2003–2018", "2003-01-01", "2019-01-01"), ("2019–2026", "2019-01-01", "2100-01-01")):
        rp = np.array([t["R"] for t in plain if a <= str(t["t_in"].date()) < b])
        rsx = np.array([t["R"] for t in stop if a <= str(t["t_in"].date()) < b])
        say(f"   {nm}: bez stopu {rp.mean():+.3f} R | se stopem {rsx.mean():+.3f} R | rozdíl {rsx.mean() - rp.mean():+.3f} | "
            f"nejhorší bez/se {rp.min():+.2f}/{rsx.min():+.2f} | n {len(rp)}")
        if rsx.mean() < rp.mean() - 0.05:
            worse = True
    st = [t for t in stop if t["stopped"]]
    say("   zastavené obchody: " + ", ".join(f"{t['t_in'].date()} {t['mk'][:3]} {t['R']:+.2f} (bez stopu "
                                             f"{next(p['R'] for p in plain if p['t_in'] == t['t_in'] and p['mk'] == t['mk']):+.2f})" for t in st))
    rs = [t for mk in F.US for t in PM.rsi2_trades(mk) if t["t_in"] >= pd.Timestamp("2003-01-01")]
    P = PM.Portfolio(stop + rs)
    say("\nMěřítko F33 se stopem + RSI(2), pevné riziko:")
    say("  r %  | vývoj (2003–14)                                   | kontrola (2015–23)                                | celé")
    R = {}
    for r in GRID:
        S = F86.sim(P, r, 0)
        a, e, lt = PM.summarize(S), PM.summarize(F86.EARLY(S)), PM.summarize(F86.LATE(S))
        R[r] = (a, e, lt)
        say(f"  {r:4.2f} | {line(e)} | {line(lt)} | {line(a)}")
    safe = [r for r in GRID if R[r][0]["fail"] <= 0.10]
    say("")
    if safe:
        r0 = max(safe)
        say(f"BEZPEČNÉ RIZIKO (celé období, propadlo ≤ 10 %): {r0} % → {line(R[r0][0])}")
    rdev = [r for r in GRID if R[r][1]["fail"] <= 0.10]
    if rdev:
        r1 = max(rdev)
        say(f"r* vybrané na vývoji: {r1} % → kontrola {line(R[r1][2])}")
    say(f"Dřívější základ (F33 bez stopu) při 1,0 %: P24 8 %, P36 40 %, propadlo 0 %, medián 30,9")
    say(f"\nROZHODNUTÍ: 1) základ měřítka = F33 se stopem (jak obchoduje runner), bezpečné riziko {max(safe) if safe else '–'} %. "
        f"2) stop F33 oslabuje o víc než 0,05 R: {'ANO (jen informace, runner se nemění)' if worse else 'NE'}")
    open(os.path.join(PM.OUT, "f87_souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
