"""
F22 ORB a F23 navrat po gapu - US indexy a DAX. Plany predem ve vaultu (Vyzkum/F22 ..., F23 ...).
Spusteni: python -I f22_f23.py -> D:\\Trading bot\\research_data\\f22\\ (obchody + souhrny)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(LB.ROOT, "research_data", "f22")
os.makedirs(OUT, exist_ok=True)
# tz burzy, otevreni (min), konec OR, konec okna vstupu, vystup: ('praha', 19*60+45) nebo ('mistni', min), zavreni (min posledni svicky)
SES = {"US": dict(tz="America/New_York", op=570, orx=585, win=705, exit=("Europe/Prague", 1185), close=959),
       "EU": dict(tz="Europe/Berlin", op=540, orx=555, win=675, exit=("Europe/Berlin", 1045), close=1049)}
MK_SES = {"SPX500mini": "US", "NAS100mini": "US", "US30mini": "US", "GER_30mini": "EU"}


def prepare(mk, src):
    d = LB.load_m1(mk, src)
    tick = LB.add_costs(mk, d, LB.broker_ref(mk))
    S = SES[MK_SES[mk]]
    loc = d.u.dt.tz_convert(S["tz"])
    ex = d.u.dt.tz_convert(S["exit"][0])
    P = dict(mk=mk, tick=tick, S=S, u=d.u.to_numpy(), o=d.o.to_numpy(), h=d.h.to_numpy(), l=d.l.to_numpy(),
             c=d.c.to_numpy(), spr=d.spr.to_numpy(), mod=(loc.dt.hour * 60 + loc.dt.minute).to_numpy(),
             date=loc.dt.date.to_numpy(), wd=loc.dt.dayofweek.to_numpy(), exmod=(ex.dt.hour * 60 + ex.dt.minute).to_numpy(),
             atr=LB.daily_atr(d, S["tz"]))
    dates = pd.unique(P["date"])
    st_ = np.searchsorted(P["date"], dates, side="left") if False else None
    # indexy dni (data jsou serazena podle casu -> mistni datum je monotonni)
    idx = {}
    dd = P["date"]
    starts = np.r_[0, np.where(dd[1:] != dd[:-1])[0] + 1]
    ends = np.r_[starts[1:], len(dd)]
    for s, e in zip(starts, ends):
        idx[dd[s]] = (s, e)
    P["idx"] = idx
    return P


def exit_index(P, s, e):
    """Prvni svicka dne s casem vystupu >= limit (Praha 19:45 / Frankfurt 17:25)."""
    lim = P["S"]["exit"][1]
    j = np.where(P["exmod"][s:e] >= lim)[0]
    return s + int(j[0]) if len(j) else None


def orb_day(P, dt):
    S = P["S"]
    s, e = P["idx"][dt]
    m = P["mod"][s:e]
    orb = np.where((m >= S["op"]) & (m < S["orx"]))[0]
    if len(orb) < 10:
        return None
    hi, lo = P["h"][s + orb].max(), P["l"][s + orb].min()
    if hi - lo < 3 * P["spr"][s + orb[-1]]:
        return None
    k = exit_index(P, s, e)
    if k is None:
        return None
    for b0 in range(S["orx"], S["win"], 5):                     # M5 svicky po konci OR
        jj = np.where((m >= b0) & (m < b0 + 5))[0]
        if len(jj) == 0:
            continue
        cl = P["c"][s + jj[-1]]
        d = 1 if cl > hi else (-1 if cl < lo else 0)
        if d == 0:
            continue
        nxt = np.where(m >= b0 + 5)[0]
        if len(nxt) == 0:
            return None
        i = s + int(nxt[0])
        if i >= k:
            return None
        sl = lo if d == 1 else hi
        r = LB.sim(P["o"], P["h"], P["l"], P["c"], P["spr"], P["tick"], i, k, d, sl)
        if r is None:
            return None
        a = P["atr"].get(dt, np.nan)
        # popisne: vystup na zavreni NY seance
        kc = np.where(m >= S["close"] - 4)[0]
        r2 = LB.sim(P["o"], P["h"], P["l"], P["c"], P["spr"], P["tick"], i, s + int(kc[0]), d, sl) if len(kc) and s + kc[0] > i else None
        return dict(mk=P["mk"], date=dt, u=P["u"][i], d=d, R=r[0], why=r[1], R_close=r2[0] if r2 else np.nan,
                    mod_in=int(P["mod"][i]), sl_atr=abs(P["o"][i] - sl) / a if a > 0 else np.nan, tp_atr=np.nan,
                    wd=int(P["wd"][i]))
    return None


def gap_day(P, dt, prev_dt):
    S = P["S"]
    if prev_dt is None:
        return None
    s0, e0 = P["idx"][prev_dt]
    s, e = P["idx"][dt]
    m0, m = P["mod"][s0:e0], P["mod"][s:e]
    pc = np.where((m0 >= S["close"] - 2) & (m0 <= S["close"]))[0]
    op = np.where((m >= S["op"]) & (m <= S["op"] + 2))[0]
    a = P["atr"].get(dt, np.nan)
    if len(pc) == 0 or len(op) == 0 or not a > 0:
        return None
    C0 = P["c"][s0 + pc[-1]]
    i = s + int(op[0])
    O = P["o"][i]
    gap = O - C0
    if abs(gap) < 0.3 * a:
        return None
    k = exit_index(P, s, e)
    if k is None or k <= i:
        return None
    d = -1 if gap > 0 else 1
    sl = O + abs(gap) if d == -1 else O - abs(gap)
    r = LB.sim(P["o"], P["h"], P["l"], P["c"], P["spr"], P["tick"], i, k, d, sl, tp=C0)
    if r is None:
        return None
    return dict(mk=P["mk"], date=dt, u=P["u"][i], d=d, R=r[0], why=r[1], R_close=np.nan, mod_in=int(P["mod"][i]),
                sl_atr=abs(gap) / a, tp_atr=abs(gap) / a, wd=int(P["wd"][i]), gap_atr=gap / a)


def run(P, kind, lo=None, hi=None):
    dates = [x for x in P["idx"] if (lo is None or pd.Timestamp(x) >= lo) and (hi is None or pd.Timestamp(x) < hi)]
    dates = [x for x in dates if pd.Timestamp(x).dayofweek < 5]
    out = []
    for n_, dt in enumerate(dates):
        r = orb_day(P, dt) if kind == "orb" else gap_day(P, dt, dates[n_ - 1] if n_ else None)
        if r:
            out.append(r)
    return pd.DataFrame(out), dates


def random_base(P, T, dates, kind, reps=3, seed=11):
    rng = np.random.default_rng(seed)
    R = []
    for r in T.itertuples():
        for _ in range(reps):
            dt = dates[int(rng.integers(0, len(dates)))]
            s, e = P["idx"][dt]
            a = P["atr"].get(dt, np.nan)
            jj = np.where(P["mod"][s:e] >= r.mod_in)[0]
            k = exit_index(P, s, e)
            if not a > 0 or len(jj) == 0 or k is None:
                continue
            i = s + int(jj[0])
            if i >= k:
                continue
            E = P["o"][i]
            sl = E - r.d * r.sl_atr * a
            tp = E + r.d * r.tp_atr * a if r.tp_atr == r.tp_atr else np.nan
            x = LB.sim(P["o"], P["h"], P["l"], P["c"], P["spr"], P["tick"], i, k, int(r.d), sl, tp)
            if x:
                R.append(x[0])
    return np.array(R)


LINES = {"orb": [], "gap": []}
P_cache = {}
for mk in ("SPX500mini", "NAS100mini", "US30mini", "GER_30mini"):
    P_cache[("broker", mk)] = prepare(mk, "broker")
    if mk in ("SPX500mini", "NAS100mini"):
        P_cache[("hd", mk)] = prepare(mk, "hd")
    print(mk, "data pripravena", flush=True)

for kind, title in (("orb", "F22 Průraz úvodního rozpětí 15 min (výstup 19:45 Praha / DAX 17:25)"),
                    ("gap", "F23 Návrat po otevíracím gapu >= 0,3 ATR (TP předchozí zavření, výstup 19:45 Praha / DAX 17:25)")):
    def say(*a, _k=kind):
        s_ = " ".join(str(x) for x in a)
        print(s_, flush=True)
        LINES[_k].append(s_)
    say(title)
    say("=" * 100)
    res = {}
    for name, src, mks, lo, hi in (("vyvoj", "hd", ("SPX500mini", "NAS100mini"), None, LB.SPLIT.tz_localize(None)),
                                   ("kontrola", "broker", ("SPX500mini", "NAS100mini"), LB.SPLIT.tz_localize(None), None),
                                   ("zdroj2", "hd", ("SPX500mini", "NAS100mini"), LB.SPLIT.tz_localize(None), LB.HD_END.tz_localize(None)),
                                   ("US30", "broker", ("US30mini",), LB.SPLIT.tz_localize(None), None),
                                   ("DAX", "broker", ("GER_30mini",), LB.SPLIT.tz_localize(None), None)):
        Ts, rnd = [], []
        for mk in mks:
            P = P_cache[(src, mk)]
            T, dates = run(P, kind, lo, hi)
            if len(T):
                Ts.append(T)
                if name in ("vyvoj", "kontrola"):
                    rnd.append(random_base(P, T, dates, kind))
        T = pd.concat(Ts, ignore_index=True) if Ts else pd.DataFrame(columns=["R"])
        T.to_pickle(os.path.join(OUT, f"{kind}_{name}.pkl"))
        res[name] = LB.st(T.R)
        if rnd:
            res[name + "_rnd"] = LB.st(np.concatenate(rnd))
        say(f"\n{name.upper():9s}", LB.fmt(res[name]))
        if len(T):
            for mk in mks:
                if len(mks) > 1:
                    say(f"   {mk:11s}", LB.fmt(LB.st(T.R[T.mk == mk])))
            say("   long / short:", LB.fmt(LB.st(T.R[T.d == 1])), "/", LB.fmt(LB.st(T.R[T.d == -1])))
            say("   výstupy:", T.groupby("why").R.agg(["count", "mean"]).round(2).to_dict("index"))
            if kind == "orb":
                say("   popisně výstup na zavření NY 15:55:", LB.fmt(LB.st(T.R_close.dropna())))
        if name + "_rnd" in res:
            say("   náhoda:", LB.fmt(res[name + "_rnd"]))
    a = pd.read_pickle(os.path.join(OUT, f"{kind}_kontrola.pkl"))
    b = pd.read_pickle(os.path.join(OUT, f"{kind}_zdroj2.pkl"))
    j = a.merge(b, on=["mk", "date"], suffixes=("_b", "_h"))
    if len(j) > 2:
        same = (j.d_b == j.d_h).mean()
        say(f"\nshoda zdrojů 2019–2025: společných dní {len(j)} z {int((pd.to_datetime(a.u, utc=True) < LB.HD_END).sum())} (broker), stejný směr {same:.0%}, "
            f"korelace R {np.corrcoef(j.R_b, j.R_h)[0, 1]:.2f}")
    say("\nPo letech (vývoj HistData + kontrola broker):")
    allT = pd.concat([pd.read_pickle(os.path.join(OUT, f"{kind}_vyvoj.pkl")), a], ignore_index=True)
    for y, g in allT.groupby(pd.to_datetime(allT.u).dt.year):
        say(f"   {y}: n {len(g):4d}  {g.R.mean():+.3f} R  součet {g.R.sum():+7.1f} R")
    say("\nROZHODNUTÍ podle pravidel zapsaných předem")
    LB.decide(say, res["vyvoj"], res["kontrola"], {"US30": res["US30"], "DAX": res["DAX"]},
              res["vyvoj_rnd"], res["kontrola_rnd"], res["zdroj2"])
    open(os.path.join(OUT, f"{kind}_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES[kind]))
