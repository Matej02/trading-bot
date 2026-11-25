"""
F92 den vysledku behem dne a F93 druhy den po vysledcich. Plan predem: Vyzkum/F92 a F93 Vysledky firem behem dne.md (commit 5767863).
Data: research_data/f88/udalosti.pkl (EDGAR), research_data/f85/yahoo_us.pkl. Bot se nemeni.
Spusteni: python -I f92_vysledky_den.py -> research_data/f88/f92_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import f85_rsi2_akcie as F85  # noqa: E402
import f88_pead as F88  # noqa: E402
import prop_meritko as PM  # noqa: E402
import f87_f33_stop as F87  # noqa: E402
import f86_riziko_zkousky as F86  # noqa: E402

RD = os.path.join(F.RD, "f88")
LINES = []
DEV = ("2004-09-01", "2017-01-01")
CTL = ("2017-01-01", "2100-01-01")
COST = dict(norm=(0.0005, 0.00004), pess=(0.0010, 0.00004), gross=(0.0, 0.0))
MAX_DAY = 3


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def intraday_all(d, s, m):
    """Obchod otevreni -> zavreni kazdy den k >= 21, smer s, stop m x ATR(20) z k-1 (m=None bez stopu, jednotka 1 ATR)."""
    O, Hh, Lo, C = (d[c].to_numpy() for c in ("open", "high", "low", "close"))
    A = PM._atr20(d).to_numpy()
    k = np.arange(21, len(d))
    E = O[k]
    risk = (m if m else 1.0) * A[k - 1]
    worst = (Lo[k] - E) if s > 0 else (E - Hh[k])
    hit = (worst <= -risk) if m else np.zeros(len(k), bool)
    X = np.where(hit, E - s * risk, C[k])
    gross = s * (X - E)
    ok = (risk > 0) & (E > 0) & np.isfinite(risk)
    out = dict(k=k, ok=ok, lo=np.where(hit, -1.0, worst / risk))
    for nm, (hs, cm) in COST.items():
        out[nm] = (gross - (hs + cm) * (E + X)) / risk
    return out


def build(E, us, test, m=1.0, zthr=2.0, with_paths=False):
    ix = F.yahoo("SPX500mini")
    ixr = ix.close.pct_change()
    rows, cand = [], []
    for t, g in E.groupby("ticker"):
        if t not in us:
            continue
        d = F85.clean(us[t])
        if len(d) < 300:
            continue
        n = len(d)
        O, C = d.open.to_numpy(), d.close.to_numpy()
        ret = d.close.pct_change().to_numpy()
        exc = (d.close.pct_change() - ixr.reindex(d.index)).to_numpy()
        base, fa = {}, {}
        for s in (1, -1):
            fa[s] = intraday_all(d, s, m)
            dates = d.index[fa[s]["k"]]
            for nm, (a, b) in (("dev", DEV), ("ctl", CTL)):
                msk = fa[s]["ok"] & (dates >= a) & (dates < b)
                base[(s, nm)] = {c: float(np.nanmean(fa[s][c][msk])) if msk.any() else np.nan for c in COST}
        for ev in g.itertuples():
            D = F88.reaction_day(d.index, ev.et)
            if D < 62 or D >= n:
                continue
            if test == "F92":
                mins = ev.et.hour * 60 + ev.et.minute
                if 570 <= mins < 960:
                    continue
                sd = np.nanstd(ret[D - 60:D], ddof=1)
                z = (O[D] / C[D - 1] - 1.0) / sd if sd > 0 else np.nan
                k = D
            else:
                sd = np.nanstd(exc[D - 60:D], ddof=1)
                z = exc[D] / sd if sd > 0 else np.nan
                k = D + 1
            if not np.isfinite(z) or abs(z) < zthr or k >= n:
                continue
            s = 1 if z > 0 else -1
            q = k - 21
            if q < 0 or not fa[s]["ok"][q]:
                continue
            day = d.index[k]
            per = "dev" if DEV[0] <= str(day.date()) < DEV[1] else ("ctl" if day >= pd.Timestamp(CTL[0]) else None)
            if per is None:
                continue
            row = dict(t=t, day=day, z=z, s=s, per=per)
            for c in COST:
                row[c] = fa[s][c][q]
                row["x_" + c] = fa[s][c][q] - base[(s, per)][c]
            rows.append(row)
            if with_paths:
                Rn = float(fa[s]["norm"][q])
                lo = min(float(fa[s]["lo"][q]), Rn)
                cand.append(dict(s=test, mk=t, t_in=day, t_out=day, R=Rn, path=[(day, lo, Rn)], z=abs(z)))
    return pd.DataFrame(rows), cand


def per_day(cands):
    by = {}
    for c in cands:
        by.setdefault(c["t_in"], []).append(c)
    out = []
    for day in sorted(by):
        out += sorted(by[day], key=lambda x: (-x["z"], x["mk"]))[:MAX_DAY]
    return out


def keepalive(trades):
    e = pd.Series(sorted(set(pd.Timestamp(t["t_in"]) for t in trades)))
    e = e[(e >= "2004-09-01") & (e < "2026-01-01")]
    gaps = e.diff().dt.days.dropna()
    need, last = 0, e.iloc[0]
    for x in e.iloc[1:]:
        while (x - last).days > 28:
            last += pd.Timedelta(days=28)
            need += 1
        last = x
    yrs = (e.iloc[-1] - e.iloc[0]).days / 365.25
    return int((gaps > 30).sum()), int(gaps.max()), need / yrs


def evaluate(test, E, us):
    say("\n" + "=" * 110)
    say(f"{test}: " + ("den výsledků, otevření → zavření ve směru gapu (|z gapu| ≥ 2)" if test == "F92" else
                       "den po reakci, otevření → zavření ve směru reakce (|z| ≥ 2 jako F88)") + ", stop 1 ATR")
    T, cand = build(E, us, test, with_paths=True)
    say(f"Obchodů: {len(T)} (long {int((T.s > 0).sum())}, short {int((T.s < 0).sum())}), vývoj {int((T.per == 'dev').sum())}, kontrola {int((T.per == 'ctl').sum())}")
    g = F88.stat(T, "dev", "gross")
    say("RYCHLÉ SÍTO (vývoj bez nákladů): " + F88.fmt(g))
    if not g["x"] > 0:
        say("   => převis bez nákladů ≤ 0 → NE, dál se nepočítá.")
        return False, T, cand
    dev, ctl = F88.stat(T, "dev", "norm"), F88.stat(T, "ctl", "norm")
    pdv, pct = F88.stat(T, "dev", "pess"), F88.stat(T, "ctl", "pess")
    say("VÝVOJ 2004–2016:    " + F88.fmt(dev) + f" | výher {dev['win']:.0%}")
    say("KONTROLA 2017–2026: " + F88.fmt(ctl) + f" | výher {ctl['win']:.0%}")
    say(f"Pesimistické náklady: vývoj R {pdv['R']:+.3f}, kontrola R {pct['R']:+.3f}")
    xl, xs = T[T.s > 0].x_norm.mean(), T[T.s < 0].x_norm.mean()
    say(f"Strany (celé období): long převis {xl:+.3f} R (n {int((T.s > 0).sum())}), short převis {xs:+.3f} R (n {int((T.s < 0).sum())})")
    yrs = T.groupby(T.day.dt.year).x_norm.mean()
    pos = (yrs > 0).mean()
    say(f"Převis po letech: kladný v {(yrs > 0).sum()} z {len(yrs)} ({pos:.0%}). " + " ".join(f"{y}:{v:+.2f}" for y, v in yrs.items()))
    crit = [
        ("2) vývoj: R > 0, převis > 0, t ≥ 3,0", dev["R"] > 0 and dev["x"] > 0 and dev["t"] >= 3.0, f"{dev['R']:+.3f}, {dev['x']:+.3f}, t {dev['t']:.2f}"),
        ("3) kontrola: R > 0, převis > 0, t ≥ 2,0", ctl["R"] > 0 and ctl["x"] > 0 and ctl["t"] >= 2.0, f"{ctl['R']:+.3f}, {ctl['x']:+.3f}, t {ctl['t']:.2f}"),
        ("4) pesimistické náklady: R > 0 ve vývoji i kontrole", pdv["R"] > 0 and pct["R"] > 0, f"{pdv['R']:+.3f} / {pct['R']:+.3f}"),
        ("5) long i short převis > 0", xl > 0 and xs > 0, f"{xl:+.3f} / {xs:+.3f}"),
        ("6) převis kladný aspoň v 60 % let", pos >= 0.60, f"{pos:.0%}"),
    ]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    say(f"   1) síto: ANO ({g['x']:+.3f})")
    for nm, ok, v in crit:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({v})")
    passed = all(c[1] for c in crit)
    say(f"   => {test}: {'VÝHODA (prošlo vše)' if passed else 'NEPROŠLO'} — body {1 + sum(c[1] for c in crit)}/6")

    say("POPIS (nerozhoduje)")
    for mm, zt in ((0.5, 2.0), (2.0, 2.0), (None, 2.0), (1.0, 1.5), (1.0, 3.0)):
        Tv, _ = build(E, us, test, m=mm, zthr=zt)
        a, b = F88.stat(Tv, "dev", "norm"), F88.stat(Tv, "ctl", "norm")
        say(f"   stop {mm if mm else 'žádný'} ATR, |z| ≥ {zt}: vývoj R {a['R']:+.3f} převis {a['x']:+.3f} t {a['t']:.2f} (n {a['n']}) | "
            f"kontrola R {b['R']:+.3f} převis {b['x']:+.3f} t {b['t']:.2f} (n {b['n']})")
    gq = F88.stat(T, "ctl", "gross")
    say(f"   bez nákladů kontrola: R {gq['R']:+.3f}, převis {gq['x']:+.3f}, t {gq['t']:.2f}")
    return passed, T, cand


def yardstick(name, cand):
    rs = [t for mk in F.US for t in PM.rsi2_trades(mk) if t["t_in"] >= pd.Timestamp("2003-01-01")]
    _, f3s = F87.f33_trades_stop()
    ch = per_day(cand)
    say(f"\nMĚŘÍTKO PROP ZKOUŠKY: základ F33 se stopem + RSI(2) proti základ + {name} (nejvýš {MAX_DAY} obchody denně, přednost |z|)")
    say(f"   obchodů {name} {len(ch)} (~{len(ch) / 22.2:.0f} ročně), průměr {np.mean([c['R'] for c in ch]):+.3f} R")
    g0, m0, k0 = keepalive(f3s + rs)
    g1, m1, k1 = keepalive(f3s + rs + ch)
    say(f"   mezery > 30 dní bez nového obchodu (2004-09 až 2025): základ {g0}× (nejdelší {m0} dní, udržovacích ~{k0:.1f}/rok) | "
        f"+ {name} {g1}× (nejdelší {m1} dní, ~{k1:.1f}/rok)")
    base, new = PM.Portfolio(f3s + rs), PM.Portfolio(f3s + rs + ch)
    res = {}
    for r in (1.0, 1.25, 1.5):
        Sb, Sn = F86.sim(base, r, 0), F86.sim(new, r, 0)
        for nm, sel in (("celé", lambda X: X), ("2003–14", F86.EARLY), ("2015–23", F86.LATE)):
            a, b = PM.summarize(sel(Sb)), PM.summarize(sel(Sn))
            res[(r, nm)] = (a, b)
            say(f"   {r:4.2f} % {nm:8s}: základ {F86.line(a)} | + {name} {F86.line(b)}")
    ok = True
    for nm in ("2003–14", "2015–23"):
        a, b = res[(1.25, nm)]
        better = (b["med"] == b["med"] and a["med"] == a["med"] and b["med"] <= 0.8 * a["med"]) or b["p12"] >= a["p12"] + 0.10
        ok = ok and better and b["fail"] <= 0.10
    say(f"   => pomáhá prop cíli při 1,25 % (medián −20 % nebo P12 +10 p. b., propadlo ≤ 10 %, obě části): {'ANO' if ok else 'NE'}")


def main():
    E = F88.events()
    us = pd.read_pickle(os.path.join(F.RD, "f85", "yahoo_us.pkl"))
    say("F92 a F93 Výsledky firem během dne — americké akcie FTMO, EDGAR 8-K 2.02, ceny Yahoo")
    say(f"Událostí: {len(E)} u {E.ticker.nunique()} firem. Náklady 0,05 % + 0,004 % na stranu, bez financování (zavírá se týž den).")
    for test in ("F92", "F93"):
        passed, T, cand = evaluate(test, E, us)
        if len(cand):
            if not passed:
                say("   (měřítko jen jako popis, test neprošel)")
            yardstick(test, cand)
    open(os.path.join(RD, "f92_souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
