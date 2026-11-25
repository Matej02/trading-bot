"""
F94 gap bez zpravy, F95 nabeh pred vysledky, F96 NAS100 v den vysledku velkych firem.
Plan predem: Vyzkum/F94 az F96 Gap bez zpravy, nabeh pred vysledky, index a velke firmy.md (commit fedec3c). Bot se nemeni.
Spusteni: python -I f94_f96.py -> research_data/f88/f94_f96_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import f85_rsi2_akcie as F85  # noqa: E402
import f88_pead as F88  # noqa: E402
import f92_vysledky_den as G  # noqa: E402

RD = os.path.join(F.RD, "f88")
LINES = []
DEV, CTL = G.DEV, G.CTL
MEGA = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOG"]


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def period(day):
    if DEV[0] <= str(day.date()) < DEV[1]:
        return "dev"
    return "ctl" if day >= pd.Timestamp(CTL[0]) else None


def intraday_costs(d, s, m, costs):
    O, Hh, Lo, C = (d[c].to_numpy() for c in ("open", "high", "low", "close"))
    A = G.PM._atr20(d).to_numpy()
    k = np.arange(21, len(d))
    E, risk = O[k], m * A[k - 1]
    worst = (Lo[k] - E) if s > 0 else (E - Hh[k])
    hit = worst <= -risk
    X = np.where(hit, E - s * risk, C[k])
    gross = s * (X - E)
    out = dict(k=k, ok=(risk > 0) & (E > 0) & np.isfinite(risk))
    for nm, hs in costs.items():
        out[nm] = (gross - hs * (E + X)) / risk
    return out


def bases(d, fa, cols):
    b = {}
    dates = d.index[fa["k"]] if "k" in fa else d.index[fa["e"]]
    for nm, (a, z) in (("dev", DEV), ("ctl", CTL)):
        msk = fa["ok"] & (dates >= a) & (dates < z)
        b[nm] = {c: float(np.nanmean(fa[c][msk])) if msk.any() else np.nan for c in cols}
    return b


def row(t, day, z, s, fa, q, base, cols):
    per = period(day)
    if per is None or not fa["ok"][q]:
        return None
    r = dict(t=t, day=day, z=z, s=s, per=per)
    for c in cols:
        r[c] = fa[c][q]
        r["x_" + c] = fa[c][q] - base[per][c]
    return r


# ---------------------------------------------------------------- F94
def f94(E, us):
    px = {}
    for t in E.ticker.unique():
        if t in us:
            d = F85.clean(us[t])
            if len(d) >= 300:
                px[t] = d
    gaps = pd.DataFrame({t: d.open / d.close.shift(1) - 1.0 for t, d in px.items()})
    cnt = gaps.notna().sum(axis=1)
    med = gaps.median(axis=1).where(cnt >= 10)
    rows = []
    for t, d in px.items():
        g = E[E.ticker == t]
        n = len(d)
        excl, first = set(), pd.Timestamp(g.et.min().date())
        for ev in g.itertuples():
            D = F88.reaction_day(d.index, ev.et)
            excl.update(range(D - 3, D + 4))
        ret = d.close.pct_change().to_numpy()
        gp = (d.open / d.close.shift(1) - 1.0).to_numpy()
        mm = med.reindex(d.index).to_numpy()
        fa = {s: G.intraday_all(d, s, 1.0) for s in (1, -1)}
        bs = {s: bases(d, fa[s], G.COST) for s in (1, -1)}
        for k in range(62, n):
            day = d.index[k]
            if day < first or k in excl or not np.isfinite(mm[k]):
                continue
            sd = np.nanstd(ret[k - 60:k], ddof=1)
            if not sd > 0:
                continue
            z = (gp[k] - mm[k]) / sd
            if not np.isfinite(z) or abs(z) < 2.0:
                continue
            s = -1 if z > 0 else 1
            r = row(t, day, z, s, fa[s], k - 21, bs[s], G.COST)
            if r:
                rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- F95
def f95(E, us):
    rows = []
    for t, g in E.groupby("ticker"):
        if t not in us:
            continue
        d = F85.clean(us[t])
        if len(d) < 300:
            continue
        fa = F88.fixed_all(d, 5, 1)
        bs = bases(d, fa, F88.COST)
        for ev in g.itertuples():
            D = F88.reaction_day(d.index, ev.et)
            e = D - 5
            q = e - 21
            if q < 0 or q >= len(fa["e"]) or D >= len(d):
                continue
            r = row(t, d.index[e], np.nan, 1, fa, q, bs, F88.COST)
            if r:
                rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- F96
def f96(E, us):
    nas = F.yahoo("NAS100mini")
    b = F.L.BROKER["NAS100mini"]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(nas.close.iloc[-1])
    costs = dict(norm=rel / 2, pess=rel, gross=0.0)
    sig = {}
    for t in MEGA:
        if t not in us:
            continue
        d = F85.clean(us[t])
        ret = d.close.pct_change().to_numpy()
        for ev in E[E.ticker == t].itertuples():
            mins = ev.et.hour * 60 + ev.et.minute
            if 570 <= mins < 960:
                continue
            D = F88.reaction_day(d.index, ev.et)
            if D < 62 or D >= len(d):
                continue
            sd = np.nanstd(ret[D - 60:D], ddof=1)
            z = (d.open.iloc[D] / d.close.iloc[D - 1] - 1.0) / sd if sd > 0 else np.nan
            if np.isfinite(z) and abs(z) >= 2.0:
                sig.setdefault(d.index[D], []).append(np.sign(z))
    fa = {s: intraday_costs(nas, s, 1.0, costs) for s in (1, -1)}
    bs = {s: bases(nas, fa[s], costs) for s in (1, -1)}
    pos = {day: i for i, day in enumerate(nas.index)}
    rows = []
    for day, ss in sorted(sig.items()):
        tot = sum(ss)
        if tot == 0 or day not in pos:
            continue
        s = 1 if tot > 0 else -1
        q = pos[day] - 21
        if q < 0:
            continue
        r = row("NAS100", day, float(tot), s, fa[s], q, bs[s], costs)
        if r:
            rows.append(r)
    return pd.DataFrame(rows), rel


def judge(name, T, long_only=False):
    say(f"Obchodů: {len(T)} (long {int((T.s > 0).sum())}, short {int((T.s < 0).sum())}), vývoj {int((T.per == 'dev').sum())}, kontrola {int((T.per == 'ctl').sum())}")
    g = F88.stat(T, "dev", "gross")
    say("RYCHLÉ SÍTO (vývoj bez nákladů): " + F88.fmt(g))
    if not g["x"] > 0:
        say(f"   => {name}: převis bez nákladů ≤ 0 → NE (síto), dál se nepočítá.")
        return
    dev, ctl = F88.stat(T, "dev", "norm"), F88.stat(T, "ctl", "norm")
    pdv, pct = F88.stat(T, "dev", "pess"), F88.stat(T, "ctl", "pess")
    gc = F88.stat(T, "ctl", "gross")
    say("VÝVOJ 2004–2016:    " + F88.fmt(dev))
    say("KONTROLA 2017–2026: " + F88.fmt(ctl) + f" | bez nákladů převis {gc['x']:+.3f} t {gc['t']:.2f}")
    say(f"Pesimistické náklady: vývoj R {pdv['R']:+.3f}, kontrola R {pct['R']:+.3f}")
    yrs = T.groupby(T.day.dt.year).x_norm.mean()
    pos = (yrs > 0).mean()
    say(f"Převis po letech: kladný v {(yrs > 0).sum()} z {len(yrs)} ({pos:.0%}). " + " ".join(f"{y}:{v:+.2f}" for y, v in yrs.items()))
    crit = [
        ("2) vývoj: R > 0, převis > 0, t ≥ 3,0", dev["R"] > 0 and dev["x"] > 0 and dev["t"] >= 3.0, f"{dev['R']:+.3f}, {dev['x']:+.3f}, t {dev['t']:.2f}"),
        ("3) kontrola: R > 0, převis > 0, t ≥ 2,0", ctl["R"] > 0 and ctl["x"] > 0 and ctl["t"] >= 2.0, f"{ctl['R']:+.3f}, {ctl['x']:+.3f}, t {ctl['t']:.2f}"),
        ("4) pesimistické náklady: R > 0 ve vývoji i kontrole", pdv["R"] > 0 and pct["R"] > 0, f"{pdv['R']:+.3f} / {pct['R']:+.3f}"),
    ]
    if not long_only:
        xl, xs = T[T.s > 0].x_norm.mean(), T[T.s < 0].x_norm.mean()
        crit.append(("5) long i short převis > 0", xl > 0 and xs > 0, f"{xl:+.3f} / {xs:+.3f}"))
    crit.append(("6) převis kladný aspoň v 60 % let", pos >= 0.60, f"{pos:.0%}"))
    say(f"   1) síto: ANO ({g['x']:+.3f})")
    for nm, ok, v in crit:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({v})")
    tot = 1 + len(crit)
    say(f"   => {name}: {'VÝHODA (prošlo vše)' if all(c[1] for c in crit) else 'NEPROŠLO'} — body {1 + sum(c[1] for c in crit)}/{tot}")


def main():
    E = F88.events()
    us = pd.read_pickle(os.path.join(F.RD, "f85", "yahoo_us.pkl"))
    say("F94–F96 — americké akcie FTMO a NAS100, EDGAR 8-K 2.02, ceny Yahoo")
    say("\n" + "=" * 100 + "\nF94: gap bez zprávy (očištěný o medián gapů 40 akcií), |z| ≥ 2, proti gapu, otevření → zavření, stop 1 ATR")
    judge("F94", f94(E, us))
    say("\n" + "=" * 100 + "\nF95: náběh před výsledky, long otevření X−4 → zavření X (den před oznámením), stop 3 ATR, financování 12 %")
    judge("F95", f95(E, us), long_only=True)
    T, rel = f96(E, us)
    say("\n" + "=" * 100 + f"\nF96: NAS100 otevření → zavření ve směru gapu Apple/Microsoft/Nvidia/Amazon/Meta/Alphabet, stop 1 ATR, spread {rel:.5%}")
    judge("F96", T)
    open(os.path.join(RD, "f94_f96_souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
