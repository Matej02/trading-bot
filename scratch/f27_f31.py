"""
F27 pokracovani po zpravach (NFP, CPI) a F31 drift pred FOMC. Plany predem ve vaultu (Vyzkum/F27 ..., F31 ...).
Spusteni: python -I f27_f31.py -> D:\\Trading bot\\research_data\\f27\\ (souhrny)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
OUT = os.path.join(LB.ROOT, "research_data", "f27")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
K = json.load(open(os.path.join(LB.ROOT, "research_data", "kalendar_2010_2021.json")))
NEWS = {pd.Timestamp(x).date() for x in K["NFP"] + K["CPI"] + [d for d in L.NFP + L.CPI if d >= "2021-09-01"]}
FOMC = {pd.Timestamp(x).date() for x in K["FOMC"] + [d for d in L.FOMC if d >= "2021-09-01"]}
TZ = "America/New_York"


def prepare(mk, src):
    d = LB.load_m1(mk, src)
    tick = LB.add_costs(mk, d, LB.broker_ref(mk))
    loc = d.u.dt.tz_convert(TZ)
    pr = d.u.dt.tz_convert("Europe/Prague")
    P = dict(mk=mk, tick=tick, u=d.u.to_numpy(), o=d.o.to_numpy(), h=d.h.to_numpy(), l=d.l.to_numpy(), c=d.c.to_numpy(),
             spr=d.spr.to_numpy(), mod=(loc.dt.hour * 60 + loc.dt.minute).to_numpy(), date=loc.dt.date.to_numpy(),
             prmod=(pr.dt.hour * 60 + pr.dt.minute).to_numpy(), wd=loc.dt.dayofweek.to_numpy(), atr=LB.daily_atr(d, TZ))
    dd = P["date"]
    starts = np.r_[0, np.where(dd[1:] != dd[:-1])[0] + 1]
    ends = np.r_[starts[1:], len(dd)]
    P["idx"] = {dd[s]: (s, e) for s, e in zip(starts, ends) if P["wd"][s] < 5}
    # ATR15: prumerny true range M15 svicek za predchozich 20 dni
    q = pd.DataFrame({"g": d.u.dt.floor("15min"), "h": d.h, "l": d.l, "c": d.c, "date": dd})
    m15 = q.groupby("g").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"), date=("date", "first"))
    pc = m15.c.shift(1)
    m15["tr"] = np.maximum(m15.h - m15.l, np.maximum((m15.h - pc).abs(), (m15.l - pc).abs()))
    P["atr15"] = m15.groupby("date").tr.mean().rolling(20).mean().shift(1)
    return P


def bars(P, dt, m0, m1):
    s, e = P["idx"][dt]
    j = np.where((P["mod"][s:e] >= m0) & (P["mod"][s:e] <= m1))[0]
    return s + j


def exit_i(P, dt):
    s, e = P["idx"][dt]
    j = np.where(P["prmod"][s:e] >= 19 * 60 + 45)[0]
    return s + int(j[0]) if len(j) else None


def news_trade(P, dt, d=None, sl_a=None):
    """d/sl_a zadane = nahodny obchod (stejny smer a SL v nasobcich ATR15)."""
    a15 = P["atr15"].get(dt, np.nan)
    if not a15 > 0:
        return None
    w = bars(P, dt, 510, 524)
    nx = bars(P, dt, 525, 540)
    k = exit_i(P, dt)
    if len(w) < 10 or len(nx) == 0 or k is None or k <= nx[0]:
        return None
    i = int(nx[0])
    o, h, l, spr, t = P["o"], P["h"], P["l"], P["spr"], P["tick"]
    if d is None:
        mv = P["c"][w[-1]] - o[w[0]]
        if abs(mv) <= 0.5 * a15:
            return None
        d = 1 if mv > 0 else -1
        sl = l[w].min() - t if d == 1 else h[w].max() + spr[i] + t
    else:
        sl = o[i] - d * sl_a * a15
    E = o[i] + spr[i] + t if d == 1 else o[i] - t
    risk = abs(E - sl)
    if not risk > 0:
        return None
    tp = E + d * 2 * risk
    r = LB.sim(o, h, l, P["c"], spr, t, i, k, d, sl, tp)
    if r is None:
        return None
    return dict(mk=P["mk"], date=dt, u=P["u"][i], d=d, R=r[0], why=r[1], sl_a=abs(o[i] - sl) / a15)


def fomc_trade(P, D, prev):
    a = P["atr"].get(D, np.nan)
    e = bars(P, prev, 840, 850)
    x = bars(P, D, 835, 845)
    if not a > 0 or len(e) == 0 or len(x) == 0:
        return None
    i, j = int(e[0]), int(x[0])
    o, spr, t = P["o"], P["spr"], P["tick"]
    E = o[i] + spr[i] + t
    X = o[j] - t
    nights = 3 if pd.Timestamp(D).dayofweek == 3 else 1
    sw = L.BROKER[P["mk"]]["swapLong"] * E * nights
    return dict(mk=P["mk"], date=D, u=P["u"][i], R=(X - E + sw) / a, Rg=(o[j] - o[i]) / a)


def period(P, lo, hi):
    ds = sorted(P["idx"])
    return [x for x in ds if (lo is None or pd.Timestamp(x) >= lo) and (hi is None or pd.Timestamp(x) < hi)]


DATA = {}
for mk in ("SPX500mini", "NAS100mini", "US30mini", "GER_30mini", "XAUUSD", "EURUSD"):
    DATA[("broker", mk)] = prepare(mk, "broker")
    if mk in ("SPX500mini", "NAS100mini"):
        DATA[("hd", mk)] = prepare(mk, "hd")
    print(mk, "pripraveno", flush=True)
SP = LB.SPLIT.tz_localize(None)
HE = LB.HD_END.tz_localize(None)
PARTS = {"vyvoj": [("hd", m, None, SP) for m in ("SPX500mini", "NAS100mini")],
         "kontrola": [("broker", m, SP, None) for m in ("SPX500mini", "NAS100mini")],
         "zdroj2": [("hd", m, SP, HE) for m in ("SPX500mini", "NAS100mini")]}

for kind in ("f27", "f31"):
    LINES = []

    def say(*a):
        s_ = " ".join(str(x) for x in a)
        print(s_, flush=True)
        LINES.append(s_)
    other = {"f27": ("XAUUSD", "EURUSD"), "f31": ("US30mini", "GER_30mini")}[kind]
    parts = dict(PARTS)
    for m in other:
        parts[m] = [("broker", m, SP, None)]
    say("F27 Pokračování po zprávách NFP/CPI (vstup 8:45 NY ve směru prvních 15 min, SL extrém, TP 2R, výstup 19:45 Praha)" if kind == "f27"
        else "F31 Drift před FOMC (long 14:00 NY den předem → 13:55 NY v den oznámení), R = výsledek / ATR20")
    say("=" * 100)
    S = {}
    rng = np.random.default_rng(13)
    for name, items in parts.items():
        Ts, rnd = [], []
        for src, mk, lo, hi in items:
            P = DATA[(src, mk)]
            ds = period(P, lo, hi)
            rows = []
            if kind == "f27":
                ev = [x for x in ds if x in NEWS]
                rows = [r for r in (news_trade(P, x) for x in ev) if r]
                quiet = [x for x in ds if x not in NEWS]
                for r in rows:
                    for _ in range(3):
                        q = quiet[int(rng.integers(0, len(quiet)))]
                        x = news_trade(P, q, d=r["d"], sl_a=r["sl_a"])
                        if x:
                            rnd.append(x["R"])
            else:
                for n_, D in enumerate(ds):
                    if n_ == 0:
                        continue
                    r = fomc_trade(P, D, ds[n_ - 1])
                    if r is None:
                        continue
                    if D in FOMC:
                        rows.append(r)
                    elif not (ds[n_ - 1] in FOMC):
                        rnd.append(r["R"])
            T = pd.DataFrame(rows)
            if len(T):
                Ts.append(T)
        T = pd.concat(Ts, ignore_index=True) if Ts else pd.DataFrame(columns=["R"])
        T.to_pickle(os.path.join(OUT, f"{kind}_{name}.pkl"))
        S[name] = LB.st(T.R)
        say(f"\n{name.upper():10s}", LB.fmt(S[name]))
        if len(T) and kind == "f27":
            say("   long / short:", LB.fmt(LB.st(T.R[T.d == 1])), "/", LB.fmt(LB.st(T.R[T.d == -1])))
            say("   výstupy:", T.groupby("why").R.agg(["count", "mean"]).round(2).to_dict("index"))
        if len(T) and kind == "f31":
            say("   bez nákladů:", LB.fmt(LB.st(T.Rg)))
        if rnd:
            S[name + "_rnd"] = LB.st(np.array(rnd))
            say("   " + ("náhoda:" if kind == "f27" else "stejné okno v jiné dny:"), LB.fmt(S[name + "_rnd"]))
    allT = pd.concat([pd.read_pickle(os.path.join(OUT, f"{kind}_{p}.pkl")) for p in ("vyvoj", "kontrola")], ignore_index=True)
    if len(allT):
        say("\nPo letech:")
        for y, g in allT.groupby(pd.to_datetime(allT.u, utc=True).dt.year):
            say(f"   {y}: n {len(g):3d}  {g.R.mean():+.3f} R  součet {g.R.sum():+6.1f} R")
    say("\nROZHODNUTÍ podle pravidel zapsaných předem")
    LB.decide(say, S["vyvoj"], S["kontrola"], {m: S[m] for m in other}, S["vyvoj_rnd"], S["kontrola_rnd"], S["zdroj2"])
    open(os.path.join(OUT, f"{kind}_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
