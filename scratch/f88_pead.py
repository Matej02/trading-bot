"""
F88 drift po vysledcich firem (PEAD) na americkych akciich FTMO. Plan predem: Vyzkum/F88 Drift po vysledcich firem (PEAD).md (commit 1315927).
Data: research_data/f88/udalosti.pkl (EDGAR 8-K 2.02), ceny research_data/f85/yahoo_us.pkl. Bot se nemeni.
Spusteni: python -I f88_pead.py -> research_data/f88/souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import f85_rsi2_akcie as F85  # noqa: E402
import prop_meritko as PM  # noqa: E402
import f87_f33_stop as F87  # noqa: E402
import f86_riziko_zkousky as F86  # noqa: E402

RD = os.path.join(F.RD, "f88")
LINES = []
DEV = ("2004-09-01", "2017-01-01")
CTL = ("2017-01-01", "2100-01-01")
COST = dict(norm=(0.0005, 0.00004, 0.12), pess=(0.0010, 0.00004, 0.15), gross=(0.0, 0.0, 0.0))
Z0, H0 = 2.0, 20
MAX_POS = 5


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def events():
    E = pd.read_pickle(os.path.join(RD, "udalosti.pkl"))
    E = E[E.form == "8-K"].copy()
    E["et"] = pd.to_datetime(E.acceptance, utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)
    E = E.sort_values(["ticker", "et"])
    keep, last = [], {}
    for r in E.itertuples():
        p = last.get(r.ticker)
        if p is not None and (r.et - p).days <= 20:
            continue
        keep.append(r.Index)
        last[r.ticker] = r.et
    return E.loc[keep]


def reaction_day(idx, et):
    """Index dne reakce D v obchodnich dnech akcie."""
    d0 = pd.Timestamp(et.date())
    t = et.hour * 60 + et.minute
    if t >= 16 * 60:
        return int(np.searchsorted(idx.values, np.datetime64(d0), side="right"))
    return int(np.searchsorted(idx.values, np.datetime64(d0), side="left"))


def fixed_all(d, H, s):
    """Obchod se smerem s, vstup na otevreni kazdeho dne e, vystup na zavreni e+H-1, stop 3 ATR(20) z e-1. Vektorove."""
    n = len(d)
    O, Hh, Lo, C = (d[c].to_numpy() for c in ("open", "high", "low", "close"))
    A = PM._atr20(d).to_numpy()
    e = np.arange(21, n - H + 1)
    E, risk = O[e], 3 * A[e - 1]
    J = np.arange(H)
    K = e[:, None] + J[None, :]
    worst = (Lo[K] - E[:, None]) if s > 0 else (E[:, None] - Hh[K])
    opn = s * (O[K] - E[:, None])
    gap = (opn <= -risk[:, None]) & (J[None, :] > 0)
    hit = gap | (worst <= -risk[:, None])
    has = hit.any(axis=1)
    js = np.where(has, hit.argmax(axis=1), H - 1)
    r = np.arange(len(e))
    ks = e + js
    g_hit = gap[r, js]
    gross = np.where(has, np.where(g_hit, opn[r, js], -risk), s * (C[ks] - E))
    X = E + s * gross
    idx = d.index.to_numpy()
    nights = (idx[ks] - idx[e]).astype("timedelta64[D]").astype(float)
    ok = (risk > 0) & (E > 0)
    out = dict(e=e, ks=ks, ok=ok, risk=risk, E=E, X=X, gross=gross, nights=nights, js=js, hit=has)
    for k, (hs, cm, fin) in COST.items():
        out[k] = (gross - (hs + cm) * (E + X) - fin * E * nights / 365.0) / risk
    return out


def build(E, us, H=H0, zthr=Z0, with_paths=False):
    """Signalni obchody s prevysem proti vsem dnum (stejna akcie, smer a obdobi)."""
    ix = F.yahoo("SPX500mini")
    ixr = ix.close.pct_change()
    rows, cand = [], []
    for t, g in E.groupby("ticker"):
        if t not in us:
            continue
        d = F85.clean(us[t])
        if len(d) < 300:
            continue
        ret = d.close.pct_change()
        exc = (ret - ixr.reindex(d.index)).to_numpy()
        base = {}
        for s in (1, -1):
            fa = fixed_all(d, H, s)
            dates = d.index[fa["e"]]
            for nm, (a, b) in (("dev", DEV), ("ctl", CTL)):
                m = fa["ok"] & (dates >= a) & (dates < b)
                base[(s, nm)] = {k: float(np.nanmean(fa[k][m])) if m.any() else np.nan for k in COST}
            base[(s, "fa")] = fa
        n = len(d)
        for ev in g.itertuples():
            D = reaction_day(d.index, ev.et)
            if D < 62 or D + 1 + H > n:
                continue
            sd = np.nanstd(exc[D - 60:D], ddof=1)
            ar = exc[D]
            if not (sd > 0) or not np.isfinite(ar):
                continue
            z = ar / sd
            if abs(z) < zthr:
                continue
            s = 1 if z > 0 else -1
            fa = base[(s, "fa")]
            q = D + 1 - 21
            if q < 0 or q >= len(fa["e"]) or not fa["ok"][q]:
                continue
            day = d.index[D + 1]
            per = "dev" if DEV[0] <= str(day.date()) < DEV[1] else ("ctl" if day >= pd.Timestamp(CTL[0]) else None)
            if per is None:
                continue
            row = dict(t=t, day=day, z=z, s=s, per=per)
            for k in COST:
                row[k] = fa[k][q]
                row["x_" + k] = fa[k][q] - base[(s, per)][k]
            rows.append(row)
            if with_paths:
                e, js, risk, E0 = fa["e"][q], fa["js"][q], fa["risk"][q], fa["E"][q]
                Lo, Hh, C = d.low.to_numpy(), d.high.to_numpy(), d.close.to_numpy()
                p = []
                for m in range(js + 1):
                    k = e + m
                    w = ((Lo[k] - E0) if s > 0 else (E0 - Hh[k])) / risk
                    p.append((d.index[k], float(w), float(s * (C[k] - E0) / risk)))
                Rn = float(fa["norm"][q])
                p[-1] = (p[-1][0], Rn if fa["hit"][q] else min(p[-1][1], Rn), Rn)
                cand.append(dict(s="F88", mk=t, t_in=d.index[e], t_out=d.index[e + js], R=Rn, path=p, z=abs(z), notional=float(E0 / risk)))
    return pd.DataFrame(rows), cand


def stat(T, per, col):
    x = T[T.per == per]
    if len(x) < 5:
        return dict(n=len(x), days=0, R=np.nan, x=np.nan, t=np.nan)
    pdm = x.groupby("day")["x_" + col].mean()
    t = pdm.mean() / (pdm.std(ddof=1) / np.sqrt(len(pdm))) if len(pdm) > 2 else np.nan
    return dict(n=len(x), days=len(pdm), R=x[col].mean(), x=pdm.mean(), t=t, win=(x[col] > 0).mean())


def fmt(r):
    return f"obchodů {r['n']}, dní vstupu {r['days']} | R signálu {r['R']:+.3f} | převis {r['x']:+.3f}, t {r['t']:.2f}"


def portfolio(cands):
    by = {}
    for c in cands:
        by.setdefault(c["t_in"], []).append(c)
    chosen, open_ = [], []
    for day in sorted(by):
        open_ = [p for p in open_ if p["t_out"] >= day]
        held = {p["mk"] for p in open_}
        for c in sorted(by[day], key=lambda x: (-x["z"], x["mk"])):
            if len(open_) >= MAX_POS:
                break
            if c["mk"] in held:
                continue
            open_.append(c)
            held.add(c["mk"])
            chosen.append(c)
    return chosen


def main():
    E = events()
    us = pd.read_pickle(os.path.join(F.RD, "f85", "yahoo_us.pkl"))
    say("F88 Drift po výsledcích firem (PEAD) — americké akcie FTMO, data zveřejnění z EDGAR (8-K, položka 2.02), ceny Yahoo")
    say(f"Událostí po vyčištění: {len(E)} u {E.ticker.nunique()} firem, {E.et.min().date()}–{E.et.max().date()}")
    say("Signál |z| ≥ 2, vstup na otevření D+1, držení 20 dní, stop 3 ATR. Náklady 0,05 % + 0,004 % na stranu, financování 12 % ročně (long i short).")
    say("=" * 110)
    T, cand = build(E, us, with_paths=True)
    say(f"Obchodů: {len(T)} (long {int((T.s > 0).sum())}, short {int((T.s < 0).sum())}), vývoj {int((T.per == 'dev').sum())}, kontrola {int((T.per == 'ctl').sum())}")
    g = stat(T, "dev", "gross")
    say("\nRYCHLÉ SÍTO (vývoj bez nákladů): " + fmt(g))
    if not g["x"] > 0:
        say("   => převis bez nákladů ≤ 0 → NE, dál se nepočítá.")
        open(os.path.join(RD, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
        return
    dev, ctl = stat(T, "dev", "norm"), stat(T, "ctl", "norm")
    pdv, pct = stat(T, "dev", "pess"), stat(T, "ctl", "pess")
    say("VÝVOJ 2004–2016:   " + fmt(dev))
    say("KONTROLA 2017–2026: " + fmt(ctl))
    say(f"Pesimistické náklady: vývoj R {pdv['R']:+.3f}, kontrola R {pct['R']:+.3f}")
    xl, xs = T[T.s > 0].x_norm.mean(), T[T.s < 0].x_norm.mean()
    say(f"Strany (celé období): long převis {xl:+.3f} R (n {int((T.s > 0).sum())}), short převis {xs:+.3f} R (n {int((T.s < 0).sum())})")
    yrs = T.groupby(T.day.dt.year).x_norm.mean()
    pos = (yrs > 0).mean()
    say(f"Převis po letech: kladný v {(yrs > 0).sum()} z {len(yrs)} ({pos:.0%}). " + " ".join(f"{y}:{v:+.2f}" for y, v in yrs.items()))

    say("\nROZHODNUTÍ podle pravidel zapsaných předem")
    crit = [
        ("2) vývoj: R > 0, převis > 0, t ≥ 3,0", dev["R"] > 0 and dev["x"] > 0 and dev["t"] >= 3.0, f"{dev['R']:+.3f}, {dev['x']:+.3f}, t {dev['t']:.2f}"),
        ("3) kontrola: R > 0, převis > 0, t ≥ 2,0", ctl["R"] > 0 and ctl["x"] > 0 and ctl["t"] >= 2.0, f"{ctl['R']:+.3f}, {ctl['x']:+.3f}, t {ctl['t']:.2f}"),
        ("4) pesimistické náklady: R > 0 ve vývoji i kontrole", pdv["R"] > 0 and pct["R"] > 0, f"{pdv['R']:+.3f} / {pct['R']:+.3f}"),
        ("5) long i short převis > 0", xl > 0 and xs > 0, f"{xl:+.3f} / {xs:+.3f}"),
        ("6) převis kladný aspoň v 60 % let", pos >= 0.60, f"{pos:.0%}"),
    ]
    for nm, ok, v in crit:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({v})")
    say(f"   1) síto: ANO ({g['x']:+.3f})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(c[1] for c in crit) else 'NEPROŠLO'} — body {1 + sum(c[1] for c in crit)}/6")

    say("\nPOPIS (nerozhoduje)")
    for zt, hh in ((1.5, 20), (3.0, 20), (2.0, 10), (2.0, 40)):
        Tv, _ = build(E, us, H=hh, zthr=zt)
        a, b = stat(Tv, "dev", "norm"), stat(Tv, "ctl", "norm")
        say(f"   |z| ≥ {zt}, držení {hh} dní: vývoj R {a['R']:+.3f} převis {a['x']:+.3f} t {a['t']:.2f} (n {a['n']}) | "
            f"kontrola R {b['R']:+.3f} převis {b['x']:+.3f} t {b['t']:.2f} (n {b['n']})")
    rs = [t for mk in F.US for t in PM.rsi2_trades(mk) if t["t_in"] >= pd.Timestamp("2003-01-01")]
    m_idx = pd.Series([t["R"] for t in rs], index=pd.DatetimeIndex([t["t_out"] for t in rs]))
    m_idx = m_idx.groupby(m_idx.index.to_period("M")).sum()
    m_p = T.groupby(T.day.dt.to_period("M")).norm.sum()
    j = m_idx.index.intersection(m_p.index)
    say(f"   Korelace měsíčních výsledků s RSI(2) na indexech: {np.corrcoef(m_idx[j], m_p[j])[0, 1]:+.2f}")

    say(f"\nMĚŘÍTKO PROP ZKOUŠKY při 1,25 %: základ F33 se stopem + RSI(2) proti základ + F88 (nejvýš {MAX_POS} pozic, přednost nejvyšší |z|)")
    ch = portfolio(cand)
    say(f"   vybraných obchodů F88 {len(ch)} ({len(ch) / 22.2:.0f} ročně), průměr {np.mean([c['R'] for c in ch]):+.3f} R")
    _, f3s = F87.f33_trades_stop()
    base, new = PM.Portfolio(f3s + rs), PM.Portfolio(f3s + rs + ch)
    for r in (1.0, 1.25, 1.5):
        Sb, Sn = F86.sim(base, r, 0), F86.sim(new, r, 0)
        for nm, sel in (("celé", lambda X: X), ("2003–14", F86.EARLY), ("2015–23", F86.LATE)):
            a, b = PM.summarize(sel(Sb)), PM.summarize(sel(Sn))
            say(f"   {r:4.2f} % {nm:8s}: základ {F86.line(a)} | + F88 {F86.line(b)}")
    open(os.path.join(RD, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
