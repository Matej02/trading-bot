"""
F50 pondelni efekt BTC (long po 00:00 -> ut 00:00 UTC) a F51 drift pred FOMC na BTC (long 14:00 NY -> 13:00 NY v den FOMC).
Plan predem ve vaultu: Vyzkum/F50 a F51 Krypto pondeli a FOMC.md (2026-11-19, oprava zdroju pred vypoctem).
Spusteni: python -I f50_f51.py -> D:\\Trading bot\\research_data\\f50\\souhrn.txt
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f50")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
K = json.load(open(os.path.join(RD, "kalendar_2010_2021.json")))
FOMC = {pd.Timestamp(x).date() for x in K["FOMC"] + [d for d in L.FOMC if d >= "2021-09-01"]}
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    diff = a.mean() - b.mean()
    return diff, diff / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def broker(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))[["open", "high", "low", "close"]].astype(float)
    u = pd.DatetimeIndex(h.index).tz_localize("UTC")
    # oprava 2026-11-21: surova H1 brokera = UTC cely rok (overeno proti GC=F), drivejsi posun +1 h v letnim case byl chybny
    dst = np.zeros(len(u), bool)
    h.index = u + pd.to_timedelta(dst.astype(np.int64) * 3600, unit="s")
    return h[~h.index.duplicated()].sort_index()


def binance(sym):
    h = pd.read_pickle(os.path.join(RD, f"binance_{sym}_1h.pkl"))[["open", "high", "low", "close"]].astype(float)
    h.index = pd.DatetimeIndex(h.index).tz_localize("UTC")
    return h


def atr_utc(d):
    g = d.groupby(d.index.date)
    D = pd.DataFrame({"H": g.high.max(), "L": g.low.min(), "C": g.close.last()})
    pc = D.C.shift(1)
    a = np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs())).rolling(20).mean().shift(1)
    a.index = pd.to_datetime(a.index)
    return a


def wins(mk, d, start_fn, end_fn, ev_fn):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    atr = atr_utc(d)
    op = d.open
    rows = []
    for D in pd.date_range(d.index[0].normalize(), d.index[-1].normalize(), freq="D"):
        t0, t1 = start_fn(D), end_fn(D)
        if t0 not in op.index or t1 not in op.index:
            continue
        a = atr.get(t0.tz_convert("UTC").normalize().tz_localize(None), np.nan)
        if not a > 0:
            continue
        E, X = op[t0], op[t1]
        net = (X - E) - rel * (E + X) / 2 + b["swapLong"] * E
        rows.append(dict(day=D.tz_localize(None) if D.tzinfo else D, ev=ev_fn(D), R=net / a))
    return pd.DataFrame(rows)


def evaluate(name, start_fn, end_fn, ev_fn):
    say("\n" + "=" * 100)
    say(name)
    say("=" * 100)
    B = wins("BTCUSD", broker("BTCUSD"), start_fn, end_fn, ev_fn)
    N = wins("BTCUSD", binance("BTCUSDT"), start_fn, end_fn, ev_fn)
    E = wins("ETHUSD", broker("ETHUSD"), start_fn, end_fn, ev_fn)
    B, E = B[B.day >= "2014-01-01"], E[E.day >= "2017-01-01"]

    def ex(T):
        e, o = T[T.ev].R, T[~T.ev].R
        diff, t = welch(e, o)
        return dict(ev=LB.st(e), base=LB.st(o), diff=diff, t=t)
    R = {"vyvoj": ex(B[B.day < "2022-01-01"]), "kontrola": ex(B[B.day >= "2022-01-01"]), "binance": ex(N[N.day >= "2019-01-01"]), "ETH": ex(E)}
    for k, v in R.items():
        say(f"{k:9s} událost: {LB.fmt(v['ev'])}")
        say(f"{'':9s} ostatní: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    pos, line = [], []
    for y, g in B.groupby(B.day.dt.year):
        if g.ev.sum() < 1:
            continue
        dy = g[g.ev].R.mean() - g[~g.ev].R.mean()
        pos.append(dy > 0)
        line.append(f"{y}:{dy:+.2f}")
    share = float(np.mean(pos))
    say("Po letech převis (broker BTC): " + "  ".join(line) + f" → kladný v {sum(pos)} z {len(pos)} ({share:.0%})")
    v, k = R["vyvoj"], R["kontrola"]
    c = [("1) vývoj: událost > 0, převis > 0, t >= 2,0", v["ev"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['ev']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ("2) kontrola: událost > 0, převis > 0, t >= 1,5", k["ev"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['ev']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ("3) ETH převis > 0", R["ETH"]["diff"] > 0, f"{R['ETH']['diff']:+.3f}"),
         ("4) Binance převis > 0", R["binance"]["diff"] > 0, f"{R['binance']['diff']:+.3f}"),
         ("5) převis kladný v >= 60 % let", share >= 0.60, f"{share:.0%}")]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")


def utc0(D):
    return pd.Timestamp(D.date(), tz="UTC")


evaluate("F50 PONDĚLNÍ EFEKT BTC – long pondělí 00:00 → úterý 00:00 UTC, srovnání = stejné 24h okno v ostatní dny",
         utc0, lambda D: utc0(D) + pd.Timedelta(days=1), lambda D: D.dayofweek == 0)
NY = "America/New_York"
evaluate("F51 DRIFT PŘED FOMC NA BTC – long 14:00 NY den předem → 13:00 NY v den oznámení (H1), srovnání = stejné okno v ostatní dny",
         lambda D: pd.Timestamp(f"{D.date()} 14:00", tz=NY).tz_convert("UTC"),
         lambda D: pd.Timestamp(f"{(D + pd.Timedelta(days=1)).date()} 13:00", tz=NY).tz_convert("UTC"),
         lambda D: (D + pd.Timedelta(days=1)).date() in FOMC)
open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
