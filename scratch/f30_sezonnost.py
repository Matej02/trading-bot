"""
F30 - mesicni sezonnost prubezne (10 let zpet, >= 7 z 10 let stejne znamenko). Plan predem ve vaultu (Vyzkum/F30 ...).
Spusteni: python -I f30_sezonnost.py -> D:\\Trading bot\\research_data\\f30\\f30_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f30")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
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
    ok = (d.high >= d.low) & (d.low <= d.open) & (d.open <= d.high) & (d.low <= d.close) & (d.close <= d.high) & (d.close > 0)
    return d[ok].dropna()


def broker_daily(mk):
    p = os.path.join(RD, f"{mk}_H1.pkl")
    if not os.path.exists(p):
        return None
    h = pd.read_pickle(p)
    h.index = pd.to_datetime(h.index)
    g = h.groupby(h.index.normalize())
    return pd.DataFrame({"open": g.open.first(), "close": g.close.last()}).dropna()


def monthly(d):
    g = d.groupby([d.index.year, d.index.month])
    m = pd.DataFrame({"o": g.open.first(), "c": g.close.last(), "d0": g.apply(lambda x: x.index[0]), "d1": g.apply(lambda x: x.index[-1]),
                      "n": g.size()})
    m.index.names = ["y", "m"]
    m = m[m.n >= 10]
    m["r"] = m.c / m.o - 1
    return m


def nights(d0, d1, crypto):
    days = pd.date_range(d0 + pd.Timedelta(days=1), d1, freq="D")
    if crypto:
        return len(days)
    wd = days.dayofweek
    return int(((wd < 5) & (wd != 3)).sum() + 3 * (wd == 3).sum())


def signals(mk, M):
    """Pro kazdy mesic: smer z predchozich 10 let (>= 8 let dat, >= 7 stejne znamenko) a sd mesicnich vynosu za 10 let."""
    out = {}
    years = sorted(set(M.index.get_level_values(0)))
    for (y, mo) in M.index:
        hist = [M.r.get((yy, mo), np.nan) for yy in range(y - 10, y)]
        hist = np.array([x for x in hist if x == x])
        if len(hist) < 8:
            continue
        mean = hist.mean()
        d = 1 if mean > 0 else -1
        if (np.sign(hist) == d).sum() < 7:
            continue
        allm = M.r[(M.index.get_level_values(0) >= y - 10) & (M.index.get_level_values(0) < y)]
        sd = allm.std()
        if not sd > 0:
            continue
        out[(y, mo)] = (d, sd)
    return out


def trades(mk, M, sig, rel, swl, sws, crypto):
    rows = []
    for k, (d, sd) in sig.items():
        if k not in M.index:
            continue
        x = M.loc[k]
        n = nights(x.d0, x.d1, crypto)
        net = d * x.r - rel + (swl if d == 1 else sws) * n
        net_l = x.r - rel + swl * n
        rows.append(dict(mk=mk, grp=group(mk), y=k[0], m=k[1], d=d, R=net / sd, R_long=net_l / sd, pct=net * 100))
    return pd.DataFrame(rows)


say("F30 Měsíční sezónnost průběžně – směr z předchozích 10 let (>= 7 z 10 let stejně), drží se celý měsíc, náklady + swap")
say("=" * 100)
mkts = sorted(p[3:-7] for p in os.listdir(RD) if p.startswith("f6_") and p.endswith("_1d.pkl"))
Ts, T2s = [], []
for mk in mkts:
    if mk not in L.BROKER:
        continue
    d = yahoo(mk)
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    cr = group(mk) == "krypto"
    M = monthly(d)
    sig = signals(mk, M)
    T = trades(mk, M, sig, rel, b["swapLong"], b["swapShort"], cr)
    if len(T):
        Ts.append(T)
    bd = broker_daily(mk)
    if bd is not None and len(bd) > 200:
        M2 = monthly(bd)
        T2 = trades(mk, M2, {k: v for k, v in sig.items() if k[0] >= 2019}, rel, b["swapLong"], b["swapShort"], cr)
        if len(T2):
            T2s.append(T2)
T = pd.concat(Ts, ignore_index=True)
T2 = pd.concat(T2s, ignore_index=True)
T.to_pickle(os.path.join(OUT, "f30_yahoo.pkl"))
T2.to_pickle(os.path.join(OUT, "f30_broker.pkl"))
S = {}
for name, g in (("vyvoj", T[T.y < 2019]), ("kontrola", T[T.y >= 2019]), ("zdroj2", T2)):
    S[name] = LB.st(g.R)
    S[name + "_long"] = LB.st(g.R_long)
    say(f"\n{name.upper():9s}", LB.fmt(S[name]), f"| průměr {g.pct.mean():+.3f} % za měsíc")
    say("   stále long stejné trhoměsíce:", LB.fmt(S[name + "_long"]))
    say("   long / short signály:", LB.fmt(LB.st(g.R[g.d == 1])), "/", LB.fmt(LB.st(g.R[g.d == -1])))
    for gg, x in g.groupby("grp"):
        S[f"{name}_{gg}"] = LB.st(x.R)
        say(f"   {gg:9s}", LB.fmt(S[f"{name}_{gg}"]))
say("\nPo měsících (celé období):")
for mo, g in T.groupby("m"):
    say(f"   {mo:2d}: n {len(g):4d}  {g.R.mean():+.3f} R  (long {int((g.d == 1).sum())}, short {int((g.d == -1).sum())})")
say("\nROZHODNUTÍ podle pravidel zapsaných předem")
grp_pos = sum(1 for g in ("indexy", "forex", "komodity", "krypto") if S.get(f"kontrola_{g}", {"m": -1})["m"] > 0)
c = [("1) vývoj > 0 a t >= 2,0", S["vyvoj"]["m"] > 0 and S["vyvoj"]["t"] >= 2.0, f"{S['vyvoj']['m']:+.3f} R, t {S['vyvoj']['t']:+.2f}"),
     ("2) kontrola > 0 a t >= 1,5", S["kontrola"]["m"] > 0 and S["kontrola"]["t"] >= 1.5, f"{S['kontrola']['m']:+.3f} R, t {S['kontrola']['t']:+.2f}"),
     ("3) v kontrole >= 3 ze 4 skupin > 0", grp_pos >= 3, f"{grp_pos} ze 4"),
     ("4) lepší než stále long (vývoj i kontrola)", S["vyvoj"]["m"] > S["vyvoj_long"]["m"] and S["kontrola"]["m"] > S["kontrola_long"]["m"],
      f"{S['vyvoj']['m']:+.3f} vs {S['vyvoj_long']['m']:+.3f}; {S['kontrola']['m']:+.3f} vs {S['kontrola_long']['m']:+.3f}"),
     ("5) druhý zdroj > 0", S["zdroj2"]["m"] > 0, f"{S['zdroj2']['m']:+.3f} R")]
for name, ok, val in c:
    say(f"   {name}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
open(os.path.join(OUT, "f30_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
