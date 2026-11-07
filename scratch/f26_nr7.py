"""
F26 - pruraz po uzkem dni (NR7), denni svicky, 39 trhu. Plan predem ve vaultu (Vyzkum/F26 ...).
Spusteni: python -I f26_nr7.py -> D:\\Trading bot\\research_data\\f26\\f26_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f26")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
SPLIT = pd.Timestamp("2019-01-01")
GROUPS = {"indexy": ["ESP_35mini", "EUR_50mini", "FRA_40mini", "GBR_100mini", "GER_30mini", "NAS100mini", "SPX500mini", "US30mini"],
          "krypto": ["BTCUSD", "ETHUSD"], "komodity": ["BRENT_OIL", "CRUDE_OIL", "XAGUSD", "XAUUSD", "XPTUSD"]}
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def group(mk):
    for g, l in GROUPS.items():
        if mk in l:
            return g
    return "forex"


def yahoo(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))[["open", "high", "low", "close"]].astype(float)
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    ok = (d.high > d.low) & (d.low <= d.open) & (d.open <= d.high) & (d.low <= d.close) & (d.close <= d.high) & (d.close > 0)
    return d[ok].dropna()                           # cisteni dat: vyradit svicky s nulovym rozpetim / cenami mimo H-L


def broker_daily(mk):
    p = os.path.join(RD, f"{mk}_H1.pkl")
    if not os.path.exists(p):
        return None
    h = pd.read_pickle(p)
    h.index = pd.to_datetime(h.index)
    g = h.groupby(h.index.normalize())
    d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()})
    d = d[(d.high > d.low)].dropna()
    return d[d.index.dayofweek < 5] if group(mk) != "krypto" else d


def costs(mk, last_price):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / last_price
    return rel, b["swapLong"], b["swapShort"], group(mk) == "krypto"


def nights(d0, d1, crypto):
    n = 0
    for k in range(1, (d1 - d0).days + 1):
        wd = (d0 + pd.Timedelta(days=k)).dayofweek
        n += 1 if crypto else (3 if wd == 3 else (1 if wd < 5 else 0))
    return n


def atr20(d):
    pc = d.close.shift(1)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    return tr.rolling(20).mean().shift(1).to_numpy()


def trade(o, h, l, c, idx, e, d, E, sl, rel, swl, sws, crypto, hold=3):
    """Vstup E v den e (smer d, SL sl). Kontrola SL od dne e+1, vystup na zavreni dne e+hold."""
    risk = abs(E - sl)
    if not risk > 0:
        return None
    x = None
    last = min(e + hold, len(c) - 1)
    for j in range(e + 1, last + 1):
        if d == 1 and o[j] <= sl:
            x = (j, o[j])
            break
        if d == -1 and o[j] >= sl:
            x = (j, o[j])
            break
        if d == 1 and l[j] <= sl:
            x = (j, sl)
            break
        if d == -1 and h[j] >= sl:
            x = (j, sl)
            break
    if x is None:
        x = (last, c[last])
    j, X = x
    cost = rel * (E + X) / 2.0                               # pul spreadu na vstupu + pul na vystupu
    sw = (swl if d == 1 else sws) * E * nights(idx[e], idx[j], crypto)
    pnl = d * (X - E) - cost + sw
    return pnl / risk, j


def run(mk, d, lo, hi, rel, swl, sws, crypto):
    o, h, l, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    idx = d.index
    a = atr20(d)
    rng = h - l
    nr7 = pd.Series(rng).rolling(7).apply(lambda x: x[-1] <= x.min(), raw=True).to_numpy() == 1
    out = []
    busy = -1
    for t in range(20, len(c) - 2):
        if not nr7[t] or t <= busy or not (lo <= idx[t] < hi) or not a[t] > 0:
            continue
        H, Lo = h[t], l[t]
        e = t + 1
        if o[e] > H:
            dd, E, sl = 1, o[e], Lo
        elif o[e] < Lo:
            dd, E, sl = -1, o[e], H
        else:
            up, dn = h[e] >= H, l[e] <= Lo
            if up and dn:                                    # obe strany proraženy -> stop prvni strany
                E, X = H, Lo
                cost = rel * (E + X) / 2.0
                out.append(dict(mk=mk, t=idx[e], d=1, R=(X - E - cost) / (E - X), why="obe", risk_atr=(H - Lo) / a[t], days=0))
                busy = e
                continue
            if not up and not dn:
                continue
            dd, E, sl = (1, H, Lo) if up else (-1, Lo, H)
        # SL uz ve dni vstupu (gap vstup a pak druha strana)
        if (dd == 1 and l[e] <= sl) or (dd == -1 and h[e] >= sl):
            cost = rel * (E + sl) / 2.0
            out.append(dict(mk=mk, t=idx[e], d=dd, R=(-abs(E - sl) - cost) / abs(E - sl), why="SL0", risk_atr=abs(E - sl) / a[t], days=0))
            busy = e
            continue
        r = trade(o, h, l, c, idx, e, dd, E, sl, rel, swl, sws, crypto)
        if r is None:
            continue
        out.append(dict(mk=mk, t=idx[e], d=dd, R=r[0], why="", risk_atr=abs(E - sl) / a[t], days=r[1] - e))
        busy = r[1]
    return pd.DataFrame(out), (o, h, l, c, idx, a)


def random_base(ctx, T, lo, hi, rel, swl, sws, crypto, reps=3, seed=3):
    o, h, l, c, idx, a = ctx
    rng = np.random.default_rng(seed)
    pool = np.where((idx >= lo) & (idx < hi) & np.isfinite(a) & (a > 0))[0]
    pool = pool[pool < len(c) - 5]
    R = []
    for r in T.itertuples():
        for _ in range(reps):
            e = int(rng.choice(pool))
            E = o[e]
            sl = E - r.d * r.risk_atr * a[e]
            if (r.d == 1 and l[e] <= sl) or (r.d == -1 and h[e] >= sl):
                R.append(-1.0 - rel * E / abs(E - sl))
                continue
            x = trade(o, h, l, c, idx, e, int(r.d), E, sl, rel, swl, sws, crypto)
            if x:
                R.append(x[0])
    return np.array(R)


say("F26 Průraz po úzkém dni (NR7) – denní svíčky, SL druhá strana NR7, výstup na zavření 3. dne, náklady + swap")
say("=" * 100)
mkts = sorted(p[3:-7] for p in os.listdir(RD) if p.startswith("f6_") and p.endswith("_1d.pkl"))
res = {"vyvoj": [], "kontrola": [], "zdroj2": []}
rnd = {"vyvoj": [], "kontrola": []}
for mk in mkts:
    if mk not in L.BROKER:
        say(f"   {mk}: chybí podmínky brokera, vynecháno")
        continue
    d = yahoo(mk)
    rel, swl, sws, cr = costs(mk, float(d.close.iloc[-1]))
    for part, lo, hi in (("vyvoj", pd.Timestamp("1900-01-01"), SPLIT), ("kontrola", SPLIT, pd.Timestamp("2100-01-01"))):
        T, ctx = run(mk, d, lo, hi, rel, swl, sws, cr)
        if len(T):
            T["grp"] = group(mk)
            res[part].append(T)
            rnd[part].append(random_base(ctx, T, lo, hi, rel, swl, sws, cr))
    bd = broker_daily(mk)
    if bd is not None and len(bd) > 300:
        T2, _ = run(mk, bd, SPLIT, pd.Timestamp("2100-01-01"), rel, swl, sws, cr)
        if len(T2):
            T2["grp"] = group(mk)
            res["zdroj2"].append(T2)
S = {}
for part in res:
    T = pd.concat(res[part], ignore_index=True)
    T.to_pickle(os.path.join(OUT, f"f26_{part}.pkl"))
    S[part] = LB.st(T.R)
    say(f"\n{part.upper():9s}", LB.fmt(S[part]))
    for g, gg in T.groupby("grp"):
        S[f"{part}_{g}"] = LB.st(gg.R)
        say(f"   {g:9s}", LB.fmt(S[f"{part}_{g}"]))
    say("   long / short:", LB.fmt(LB.st(T.R[T.d == 1])), "/", LB.fmt(LB.st(T.R[T.d == -1])))
    say("   obě strany proraženy (−1 R):", f"{(T.why == 'obe').mean():.0%}", "| stop už v den vstupu:", f"{(T.why == 'SL0').mean():.0%}")
    if part in rnd:
        S[part + "_rnd"] = LB.st(np.concatenate(rnd[part]))
        say("   náhoda:  ", LB.fmt(S[part + "_rnd"]))
allT = pd.concat([pd.read_pickle(os.path.join(OUT, f"f26_{p}.pkl")) for p in ("vyvoj", "kontrola")])
say("\nPo dekádách / letech od 2015:")
for y, g in allT.groupby(allT.t.dt.year // 5 * 5):
    say(f"   {y}–{y + 4}: n {len(g):5d}  {g.R.mean():+.3f} R")
say("\nROZHODNUTÍ podle pravidel zapsaných předem")
grp_pos = sum(1 for g in ("indexy", "forex", "komodity", "krypto") if S.get(f"kontrola_{g}", {"m": -1})["m"] > 0)
c = [("1) vývoj > 0 a t >= 2,0", S["vyvoj"]["m"] > 0 and S["vyvoj"]["t"] >= 2.0, f"{S['vyvoj']['m']:+.3f} R, t {S['vyvoj']['t']:+.2f}"),
     ("2) kontrola > 0 a t >= 1,5", S["kontrola"]["m"] > 0 and S["kontrola"]["t"] >= 1.5, f"{S['kontrola']['m']:+.3f} R, t {S['kontrola']['t']:+.2f}"),
     ("3) v kontrole >= 3 ze 4 skupin > 0", grp_pos >= 3, f"{grp_pos} ze 4"),
     ("4) lepší než náhoda", S["vyvoj"]["m"] > S["vyvoj_rnd"]["m"] and S["kontrola"]["m"] > S["kontrola_rnd"]["m"],
      f"{S['vyvoj']['m']:+.3f} vs {S['vyvoj_rnd']['m']:+.3f}; {S['kontrola']['m']:+.3f} vs {S['kontrola_rnd']['m']:+.3f}"),
     ("5) druhý zdroj > 0", S["zdroj2"]["m"] > 0, f"{S['zdroj2']['m']:+.3f} R")]
for name, ok, val in c:
    say(f"   {name}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
open(os.path.join(OUT, "f26_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
