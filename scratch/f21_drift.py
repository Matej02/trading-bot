"""
F21 - nocni drift indexu (long od zavreni burzy do otevreni dalsiho dne). Plan predem ve vaultu:
znalosti/Vyzkum/F21 Nocni drift indexu (long pres noc).md
Spusteni: python -I f21_drift.py  -> D:\\Trading bot\\research_data\\f21\\ (obchody + souhrn)
Kod runneru ani vyzkumu se nemeni; f7_lib se jen cte (spready a swapy brokera).
"""
import os
import sys

ROOT = r"D:\Trading bot"
sys.path.insert(0, ROOT)
os.chdir(ROOT)                       # f7_lib cte simulator/lib/broker.json relativne
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f7_lib as L  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(ROOT, "research_data", "f21")
os.makedirs(OUT, exist_ok=True)
BRK = os.path.join(ROOT, "research_data", "f10")
HD = os.path.join(ROOT, "research_data", "histdata", "m1", "m1_skutecne_utc")
SPLIT = pd.Timestamp("2019-02-21", tz="UTC")
HD_END = pd.Timestamp("2026-01-01", tz="UTC")
EX = {"NAS100mini": ("America/New_York", 960, 570), "SPX500mini": ("America/New_York", 960, 570),
      "US30mini": ("America/New_York", 960, 570), "GER_30mini": ("Europe/Berlin", 1050, 540)}   # tz, zavreni, otevreni (min)
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def load(path, broker):
    d = pd.read_pickle(path)[["t", "o", "h", "l", "c"]].copy()
    u = pd.to_datetime(d.t, unit="s").dt.tz_localize("UTC")
    if broker:   # cas serveru = UTC, ale data byla ctena jako Londyn -> v britskem letnim case +1 h zpet na skutecne UTC
        dst = (u + pd.Timedelta(hours=1)).dt.tz_convert("Europe/London").map(lambda x: x.dst().seconds > 0).to_numpy()
        u = u + pd.to_timedelta(dst.astype(np.int64) * 3600, unit="s")
    d["u"] = u
    return d


def build(mk, d, ref):
    """Obchody nocniho driftu + denni seance + ATR20; d = M1 se skutecnym UTC."""
    tz, cl, op = EX[mk]
    b = L.BROKER[mk]
    sbh = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0)
    tick = 10.0 ** -b["digits"]
    loc = d.u.dt.tz_convert(tz)
    d = d.assign(date=loc.dt.date, mod=loc.dt.hour * 60 + loc.dt.minute, wd=loc.dt.dayofweek)
    d = d[d.wd < 5]
    lon_h = d.u.dt.tz_convert("Europe/London").dt.hour.to_numpy()
    d = d.assign(spr=sbh[lon_h] / ref * d.c.to_numpy())
    # denni ATR20 (z predchozich 20 seanci)
    g = d.groupby("date")
    D = pd.DataFrame({"H": g.h.max(), "L": g.l.min(), "C": g.c.last()})
    pc = D.C.shift(1)
    tr = np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs()))
    D["atr"] = tr.rolling(20).mean().shift(1)
    ent = d[(d["mod"] >= cl - 3) & (d["mod"] <= cl - 1)].groupby("date").last()          # zavreni (cena c svicky 15:59)
    exi = d[(d["mod"] >= op) & (d["mod"] <= op + 3)].groupby("date").first()            # otevreni (cena o svicky 9:30)
    ed = np.array(sorted(exi.index))
    rows = []
    for dt, e in ent.iterrows():
        k = np.searchsorted(ed, dt, side="right")
        atr = D.atr.get(dt, np.nan)
        if k >= len(ed) or not atr > 0:
            continue
        x = exi.loc[ed[k]]
        if (x.u - e.u) > pd.Timedelta(days=4):
            continue
        nights = 3 if e.wd == 2 else 1                                                     # swap: streda -> ctvrtek 3x
        buy = e.c + e.spr + tick
        sell = x.o - tick
        swap = b["swapLong"] * e.c * nights
        net = sell - buy + swap
        rows.append(dict(mk=mk, date=dt, u=e.u, wd=int(e.wd), dur=(x.u - e.u).total_seconds(), entry=e.c, exit=x.o,
                         gross=x.o - e.c, net=net, R=net / atr, Rg=(x.o - e.c) / atr, pct=net / e.c * 100, atr=atr))
    T = pd.DataFrame(rows)
    # denni seance: otevreni 9:30 -> zavreni 15:59 stejneho dne
    day = []
    for dt, x in exi.iterrows():
        if dt not in ent.index or not D.atr.get(dt, np.nan) > 0:
            continue
        e = ent.loc[dt]
        if e.u <= x.u:
            continue
        net = (e.c - tick) - (x.o + x.spr + tick)
        day.append(dict(mk=mk, date=dt, u=x.u, R=net / D.atr[dt], pct=net / x.o * 100))
    return T, pd.DataFrame(day), d, D, sbh, tick


def random_windows(mk, d, D, T, reps=3, seed=7):
    """Nahodne okno stejne delky: start v nahodnou minutu vsedniho dne, stejne naklady (spread, tick, swap pres 17:00 NY)."""
    rng = np.random.default_rng(seed)
    b = L.BROKER[mk]
    tick = 10.0 ** -b["digits"]
    ut = d.u.to_numpy().astype("datetime64[s]").astype(np.int64)
    o, spr, dates = d.o.to_numpy(), d.spr.to_numpy(), d.date.to_numpy()
    atr = D.atr
    R = []
    for dur in T.dur.to_numpy():
        for _ in range(reps):
            i = int(rng.integers(0, len(ut) - 1))
            j = int(np.searchsorted(ut, ut[i] + dur))
            if j >= len(ut) or ut[j] - ut[i] > dur + 300:
                continue
            a = atr.get(dates[i], np.nan)
            if not a > 0:
                continue
            # pocet rolloveru 17:00 NY mezi i a j (ctvrtek = 3x)
            ny = pd.to_datetime([ut[i], ut[j]], unit="s").tz_localize("UTC").tz_convert("America/New_York")
            r0 = (ny[0] - pd.Timedelta(hours=17)).normalize()
            r1 = (ny[1] - pd.Timedelta(hours=17)).normalize()
            n = 0
            for k in range(1, (r1 - r0).days + 1):
                wd = (r0 + pd.Timedelta(days=k)).dayofweek          # novy obchodni den (cas NY + 7 h)
                n += 3 if wd == 3 else (1 if wd < 5 else 0)
            net = (o[j] - tick) - (o[i] + spr[i] + tick) + b["swapLong"] * o[i] * n
            R.append(net / a)
    return np.array(R)


def st(R):
    R = np.asarray(R, float)
    n = len(R)
    if n < 2:
        return dict(n=n, m=np.nan, t=np.nan, win=np.nan)
    return dict(n=n, m=R.mean(), t=R.mean() / R.std(ddof=1) * np.sqrt(n), win=(R > 0).mean())


def f(s):
    return f"n {s['n']:5d} | {s['m']:+.4f} R | t {s['t']:+.2f} | výhra {s['win']:.0%}" if s["n"] >= 2 else f"n {s['n']}"


res = {}
for mk in ("SPX500mini", "NAS100mini", "US30mini", "GER_30mini"):
    bd = load(os.path.join(BRK, f"{mk}_M1.pkl"), broker=True)
    ref = float(np.median(bd.c.to_numpy()[-30 * 1440:]))
    T, Dy, dd, D, _, _ = build(mk, bd, ref)
    T = T[T.u >= SPLIT]
    Dy = Dy[Dy.u >= SPLIT]
    res[("broker", mk)] = (T, Dy, dd[dd.u >= SPLIT], D)
    if mk in ("SPX500mini", "NAS100mini"):
        hd = load(os.path.join(HD, f"{mk}_M1.pkl"), broker=False)
        T2, Dy2, dd2, D2, _, _ = build(mk, hd, ref)
        res[("hd_vyvoj", mk)] = (T2[T2.u < SPLIT], Dy2[Dy2.u < SPLIT], dd2[dd2.u < SPLIT], D2)
        res[("hd_prekryv", mk)] = (T2[(T2.u >= SPLIT) & (T2.u < HD_END)], Dy2[(Dy2.u >= SPLIT) & (Dy2.u < HD_END)], None, D2)
    print(mk, "hotovo", flush=True)

for k, v in res.items():
    v[0].to_pickle(os.path.join(OUT, f"f21_{k[0]}_{k[1]}.pkl"))


def part(src, mks):
    T = pd.concat([res[(src, m)][0] for m in mks], ignore_index=True)
    Dy = pd.concat([res[(src, m)][1] for m in mks], ignore_index=True)
    return T, Dy


say("F21 Noční drift indexů – long od zavření (16:00 NY) do otevření (9:30 NY), po nákladech (spread, tick, swap)")
say("R = pohyb / ATR20 denního rozpětí; % = pohyb v % ceny")
say("=" * 100)
US2 = ("SPX500mini", "NAS100mini")
out = {}
for title, src, mks in (("VÝVOJ – HistData 2010-11..2019-02 (SPX + NAS)", "hd_vyvoj", US2),
                        ("KONTROLA – broker 2019-02..2026-10 (SPX + NAS)", "broker", US2),
                        ("DRUHÝ ZDROJ – HistData 2019-02..2025-12 (SPX + NAS)", "hd_prekryv", US2)):
    T, Dy = part(src, mks)
    s = st(T.R)
    out[src] = s
    say(f"\n{title}")
    say("   noc po nákladech:   ", f(s), f"| průměr {T.pct.mean():+.4f} % za noc, ~{T.pct.mean() * 252:+.1f} % ročně")
    say("   noc bez nákladů:    ", f(st(T.Rg)))
    say("   denní seance:       ", f(st(Dy.R)), f"| průměr {Dy.pct.mean():+.4f} % za den")
    for m in mks:
        say(f"     {m:11s} noc", f(st(T.R[T.mk == m])))
    if src != "hd_prekryv":
        rb = np.concatenate([random_windows(m, res[(src, m)][2], res[(src, m)][3], res[(src, m)][0]) for m in mks])
        out[src + "_rnd"] = st(rb)
        say("   náhodné okno stejné délky:", f(st(rb)))

# shoda zdroju na prekryvu
A = pd.concat([res[("broker", m)][0] for m in US2])
B = pd.concat([res[("hd_prekryv", m)][0] for m in US2])
j = A.merge(B, on=["mk", "date"], suffixes=("_b", "_h"))
say(f"\n   shoda zdrojů na překryvu: společných nocí {len(j)}, korelace R {np.corrcoef(j.R_b, j.R_h)[0, 1]:.3f}, "
    f"průměr R broker {j.R_b.mean():+.4f} / HistData {j.R_h.mean():+.4f}")

say("\nJINÉ TRHY – broker 2019-02..2026-10")
other = {}
for m in ("US30mini", "GER_30mini"):
    T, Dy = res[("broker", m)][0], res[("broker", m)][1]
    other[m] = st(T.R)
    say(f"   {m:11s} noc", f(other[m]), f"| {T.pct.mean():+.4f} % za noc | denní seance", f(st(Dy.R)))

say("\nPOPISNĚ (nerozhoduje): po dnech vstupu a po letech, SPX + NAS, HistData do 2019-02 + broker potom")
allT = pd.concat([part("hd_vyvoj", US2)[0], part("broker", US2)[0]], ignore_index=True)
for wd, g in allT.groupby("wd"):
    say(f"   {['po', 'út', 'st', 'čt', 'pá'][wd]}: {f(st(g.R))}")
for y, g in allT.groupby(allT.u.dt.year):
    s = st(g.R)
    say(f"   {y}: n {s['n']:4d}  {s['m']:+.4f} R  součet {g.R.sum():+7.1f} R  {g.pct.sum():+6.1f} %")
w = allT.nsmallest(3, "R")
say("   nejhorší noci:", "; ".join(f"{r.mk} {r.date} {r.R:+.2f} R ({r.pct:+.2f} %)" for r in w.itertuples()))

say("\nROZHODNUTÍ podle pravidel zapsaných předem")
c1 = out["hd_vyvoj"]["m"] > 0 and out["hd_vyvoj"]["t"] >= 2.0
c2 = out["broker"]["m"] > 0 and out["broker"]["t"] >= 1.5
c3 = all(other[m]["m"] > 0 for m in other)
c4 = out["hd_vyvoj"]["m"] > out["hd_vyvoj_rnd"]["m"] and out["broker"]["m"] > out["broker_rnd"]["m"]
for name, ok, val in (("1) vývoj > 0 a t >= 2,0", c1, f"t {out['hd_vyvoj']['t']:+.2f}"),
                      ("2) kontrola > 0 a t >= 1,5", c2, f"t {out['broker']['t']:+.2f}"),
                      ("3) US30 i DAX > 0", c3, ", ".join(f"{m} {other[m]['m']:+.4f}" for m in other)),
                      ("4) lepší než náhodné okno (vývoj i kontrola)", c4,
                       f"{out['hd_vyvoj']['m']:+.4f} vs {out['hd_vyvoj_rnd']['m']:+.4f}; {out['broker']['m']:+.4f} vs {out['broker_rnd']['m']:+.4f}")):
    say(f"   {name}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if c1 and c2 and c3 and c4 else 'BEZ VÝHODY'}")
open(os.path.join(OUT, "f21_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
