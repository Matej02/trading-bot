"""
F25 - parove obchody (z-skore log spreadu na H1). Plan predem ve vaultu (Vyzkum/F25 ...).
Spusteni: python -I f25_pary.py -> D:\\Trading bot\\research_data\\f25\\f25_souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.join(LB.ROOT, "research_data", "f25")
os.makedirs(OUT, exist_ok=True)
NB, NZ, MAXH = 1400, 460, 230
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def h1_from_m1(mk, src):
    d = LB.load_m1(mk, src)
    g = d.groupby(d.u.dt.floor("h"))
    return pd.DataFrame({"o": g.o.first(), "c": g.c.last()})


def h1_broker(mk):
    d = pd.read_pickle(os.path.join(LB.ROOT, "research_data", f"{mk}_H1.pkl"))
    d = d.rename(columns={"open": "o", "close": "c"})[["o", "c"]]
    d.index = pd.to_datetime(d.index).tz_localize("UTC")
    return d


def cost_arrays(mk, idx, px):
    b = L.BROKER[mk]
    sbh = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0)
    ref = float(np.median(px[-30 * 23:]))
    hrs = idx.tz_convert("Europe/London").hour.to_numpy()
    return sbh[hrs] / ref * px, 10.0 ** -b["digits"], b["swapLong"], b["swapShort"]


def nights(t0, t1):
    """Pocet swapu mezi dvema casy (rollover 17:00 NY, ze stredy na ctvrtek 3x)."""
    ny0 = (t0.tz_convert("America/New_York") - pd.Timedelta(hours=17)).normalize()
    ny1 = (t1.tz_convert("America/New_York") - pd.Timedelta(hours=17)).normalize()
    n = 0
    for k in range(1, (ny1 - ny0).days + 1):
        wd = (ny0 + pd.Timedelta(days=k)).dayofweek
        n += 3 if wd == 3 else (1 if wd < 5 else 0)
    return n


def run_pair(A, B, mA, mB, lo=None, hi=None):
    df = A.join(B, how="inner", lsuffix="A", rsuffix="B").dropna()
    la, lb = np.log(df.cA), np.log(df.cB)
    cov = la.rolling(NB).cov(lb)
    var = lb.rolling(NB).var()
    beta = (cov / var).shift(0)
    s = la - beta * lb
    mu = s.rolling(NZ).mean()
    sd = s.rolling(NZ).std()
    z = ((s - mu) / sd).to_numpy()
    beta, sdv = beta.to_numpy(), sd.to_numpy()
    idx = df.index
    oA, oB = df.oA.to_numpy(), df.oB.to_numpy()
    sprA, tA, swlA, swsA = cost_arrays(mA, idx, df.cA.to_numpy())
    sprB, tB, swlB, swsB = cost_arrays(mB, idx, df.cB.to_numpy())
    ok = np.ones(len(df), bool)
    if lo is not None:
        ok &= idx >= lo
    if hi is not None:
        ok &= idx < hi
    trades = []
    i = NB + NZ
    n = len(df)
    while i < n - 2:
        if not ok[i] or not np.isfinite(z[i]) or abs(z[i]) <= 2 or abs(z[i]) >= 4:
            i += 1
            continue
        d = -1 if z[i] > 2 else 1               # +1 = long spread (long A, short B)
        e, bt, sde = i + 1, beta[i], sdv[i]
        x = None
        for j in range(e, min(n - 1, e + MAXH)):
            if (d == 1 and z[j] >= 0) or (d == -1 and z[j] <= 0) or abs(z[j]) >= 4:
                x = j + 1
                break
        if x is None:
            x = min(n - 1, e + MAXH)
        trades.append(leg_pnl(idx, oA, oB, sprA, sprB, tA, tB, swlA, swsA, swlB, swsB, e, x, d, bt, sde))
        i = x
    return pd.DataFrame(trades), (idx, oA, oB, sprA, sprB, tA, tB, swlA, swsA, swlB, swsB, ok, beta, sdv)


def leg_pnl(idx, oA, oB, sprA, sprB, tA, tB, swlA, swsA, swlB, swsB, e, x, d, bt, sde):
    # noha A: smer d, noha B: smer -d s vahou bt (v nominalu vuci A)
    def leg(o, spr, t, swl, sws, dd):
        if dd == 1:
            ent, ex = o[e] + spr[e] + t, o[x] - t
            r = ex / ent - 1
            sw = swl
        else:
            ent, ex = o[e] - t, o[x] + spr[x] + t
            r = 1 - ex / ent
            sw = sws
        return r, sw
    nn = nights(idx[e], idx[x])
    rA, swA = leg(oA, sprA, tA, swlA, swsA, d)
    rB, swB = leg(oB, sprB, tB, swlB, swsB, -d)
    ret = rA + abs(bt) * rB + (swA + abs(bt) * swB) * nn
    gross = d * ((oA[x] / oA[e] - 1) - bt * (oB[x] / oB[e] - 1))
    return dict(u=idx[e], d=d, hold=x - e, ret=ret, gross=gross, R=ret / (2 * sde) if sde > 0 else np.nan, beta=bt)


def random_base(ctx, T, reps=3, seed=5):
    idx, oA, oB, sprA, sprB, tA, tB, swlA, swsA, swlB, swsB, ok, beta, sdv = ctx
    rng = np.random.default_rng(seed)
    cand = np.where(ok & np.isfinite(beta) & np.isfinite(sdv))[0]
    cand = cand[cand < len(idx) - 2]
    R = []
    for r in T.itertuples():
        for _ in range(reps):
            e = int(rng.choice(cand))
            x = min(len(idx) - 1, e + int(r.hold))
            R.append(leg_pnl(idx, oA, oB, sprA, sprB, tA, tB, swlA, swsA, swlB, swsB, e, x, int(r.d), beta[e - 1], sdv[e - 1])["R"])
    return np.array(R)


say("F25 Párové obchody – z-skóre log spreadu (β 1400 H1, z 460 H1), vstup |z|>2, výstup z=0 / |z|>=4 / 230 svíček")
say("=" * 100)
SP = LB.SPLIT
SP18 = pd.Timestamp("2019-01-01", tz="UTC")
data = {}
data["NS_hd"] = (h1_from_m1("NAS100mini", "hd"), h1_from_m1("SPX500mini", "hd"))
data["NS_br"] = (h1_from_m1("NAS100mini", "broker"), h1_from_m1("SPX500mini", "broker"))
data["XAU_XAG"] = (h1_broker("XAUUSD"), h1_broker("XAGUSD"))
data["EUR_GBP"] = (h1_broker("EURUSD"), h1_broker("GBPUSD"))
data["BRENT_WTI"] = (h1_broker("BRENT_OIL"), h1_broker("CRUDE_OIL"))
MK = {"NS_hd": ("NAS100mini", "SPX500mini"), "NS_br": ("NAS100mini", "SPX500mini"), "XAU_XAG": ("XAUUSD", "XAGUSD"),
      "EUR_GBP": ("EURUSD", "GBPUSD"), "BRENT_WTI": ("BRENT_OIL", "CRUDE_OIL")}
PARTS = {"vyvoj": [("NS_hd", None, SP), ("XAU_XAG", None, SP18), ("EUR_GBP", None, SP18)],
         "kontrola": [("NS_br", SP, None), ("XAU_XAG", SP18, None), ("EUR_GBP", SP18, None)],
         "zdroj2": [("NS_hd", SP, LB.HD_END)],
         "brent_wti": [("BRENT_WTI", None, None)]}
res = {}
for part, items in PARTS.items():
    Ts, rnd = [], []
    say(f"\n{part.upper()}")
    for key, lo, hi in items:
        A, B = data[key]
        T, ctx = run_pair(A, B, *MK[key], lo=lo, hi=hi)
        if len(T):
            T["pair"] = key
            Ts.append(T)
            say(f"   {key:10s}", LB.fmt(LB.st(T.R)), f"| průměr {T.ret.mean() * 100:+.3f} % / obchod, bez nákladů {T.gross.mean() * 100:+.3f} %, držení medián {T.hold.median():.0f} h")
            if part in ("vyvoj", "kontrola"):
                rnd.append(random_base(ctx, T))
    T = pd.concat(Ts, ignore_index=True)
    T.to_pickle(os.path.join(OUT, f"f25_{part}.pkl"))
    res[part] = LB.st(T.R)
    say("   CELKEM   ", LB.fmt(res[part]))
    if rnd:
        res[part + "_rnd"] = LB.st(np.concatenate(rnd))
        say("   náhoda   ", LB.fmt(res[part + "_rnd"]))
allT = pd.concat([pd.read_pickle(os.path.join(OUT, f"f25_{p}.pkl")) for p in ("vyvoj", "kontrola")])
say("\nPo letech (vývoj + kontrola):")
for y, g in allT.groupby(allT.u.dt.year):
    say(f"   {y}: n {len(g):3d}  {g.R.mean():+.3f} R  součet {g.R.sum():+6.1f} R")
say("\nROZHODNUTÍ podle pravidel zapsaných předem")
LB.decide(say, res["vyvoj"], res["kontrola"], {"Brent/WTI": res["brent_wti"]}, res["vyvoj_rnd"], res["kontrola_rnd"], res["zdroj2"])
open(os.path.join(OUT, "f25_souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES))
