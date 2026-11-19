"""
F46 zlato v asijske seanci (long 23:00 -> 07:00 Londyn) a F47 dluhopisy -> zlato (TLT za mesic > 0 -> long XAU dalsi mesic).
Plan predem ve vaultu: Vyzkum/F46 a F47 Zlato a dluhopisy.md (2026-11-19).
Spusteni: python -I f46_f47.py -> D:\\Trading bot\\research_data\\f46\\souhrn.txt
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
OUT = os.path.join(RD, "f46")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    diff = a.mean() - b.mean()
    return diff, diff / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def broker_h1(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))[["open", "high", "low", "close"]].astype(float)
    u = pd.DatetimeIndex(h.index).tz_localize("UTC")
    dst = np.array([x.dst().seconds > 0 for x in (u + pd.Timedelta(hours=1)).tz_convert("Europe/London")])
    h.index = (u + pd.to_timedelta(dst.astype(np.int64) * 3600, unit="s")).tz_convert("Europe/London")
    return h


# ===================================================================== F46
def f46_windows(mk):
    h = broker_h1(mk)
    b = L.BROKER[mk]
    sbh = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0)
    rel = sbh / float(h.close.iloc[-1])
    D = h.groupby(h.index.date).agg(H=("high", "max"), Lo=("low", "min"), C=("close", "last"))
    pc = D.C.shift(1)
    atr = np.maximum(D.H - D.Lo, np.maximum((D.H - pc).abs(), (D.Lo - pc).abs())).rolling(20).mean().shift(1)
    op = h.open
    rows = []
    for t0, E in op.items():
        if t0.minute != 0:
            continue
        t1 = t0 + pd.Timedelta(hours=8)
        if t1 not in op.index:
            continue
        if t0.day_of_week >= 5 or (t0.day_of_week == 4 and t0.hour >= 15):
            continue                                             # pres vikend ne
        if 21 <= t0.hour <= 22 or (t0.hour < 23 and t0.hour + 8 > 21 and t0.hour <= 21):
            pass
        X = op[t1]
        a = atr.get(t1.date(), np.nan)
        if not (a > 0):
            continue
        net = (X - E) - rel[t0.hour] * E / 2 - rel[t1.hour] * X / 2
        rows.append(dict(t=t0, h=t0.hour, R=net / a))
    return pd.DataFrame(rows)


def f46():
    say("=" * 100)
    say("F46 ZLATO V ASIJSKÉ SEANCI – long 23:00 → 07:00 Londýn, srovnání = stejně dlouhá okna ostatních hodin")
    say("=" * 100)
    S = {}
    for mk in ("XAUUSD", "XAGUSD"):
        W = f46_windows(mk)
        W["y"] = W.t.dt.year
        S[mk] = W
    W = S["XAUUSD"]
    res = {}
    for nm, sel in (("vyvoj", W.t.dt.year < 2019), ("kontrola", W.t.dt.year >= 2019)):
        X = W[sel]
        e, o = X[X.h == 23].R, X[X.h != 23].R
        diff, t = welch(e, o)
        res[nm] = dict(ev=LB.st(e), diff=diff, t=t)
        say(f"{nm:9s} XAU 23→07: {LB.fmt(res[nm]['ev'])} | ostatní okna {o.mean():+.3f} R | převis {diff:+.3f}, t {t:+.2f}")
    hours = W.groupby("h").R.mean()
    say("Průměr R podle hodiny začátku okna (XAU, celé období): " + "  ".join(f"{int(k)}:{v:+.3f}" for k, v in hours.items()))
    G = S["XAGUSD"]
    dag, _ = welch(G[G.h == 23].R, G[G.h != 23].R)
    say(f"stříbro: 23→07 {G[G.h == 23].R.mean():+.3f} R | převis {dag:+.3f}")
    yr = W[W.h == 23].groupby("y").R.mean()
    yo = W[W.h != 23].groupby("y").R.mean()
    ex = (yr - yo).dropna()
    worst = yr.sort_values().iloc[: max(1, len(yr) // 3)].mean()
    share = float((ex > 0).mean())
    say("po letech (XAU 23→07): " + "  ".join(f"{y}:{v:+.3f}" for y, v in yr.items()))
    say(f"nejhorší třetina let průměr {worst:+.3f} R | převis kladný v {int((ex > 0).sum())} z {len(ex)} let ({share:.0%})")
    v, k = res["vyvoj"], res["kontrola"]
    c = [("1) vývoj > 0, převis > 0, t >= 2,0", v["ev"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['ev']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ("2) kontrola > 0, převis > 0, t >= 1,5", k["ev"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['ev']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ("3) stříbro převis > 0", dag > 0, f"{dag:+.3f}"),
         ("4) nejhorší třetina let > 0", worst > 0, f"{worst:+.3f}"),
         ("5) převis kladný v >= 60 % let", share >= 0.60, f"{share:.0%}")]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")


# ===================================================================== F47
def yahoo_close(mk):
    c = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))["close"].astype(float)
    c.index = pd.to_datetime(c.index).tz_localize(None).normalize()
    return c[c > 0].dropna()


def tlt():
    j = json.load(open(os.path.join(RD, "f33", "yahoo", "TLT.json")))["chart"]["result"][0]
    t = pd.to_datetime(j["timestamp"], unit="s").normalize()
    return pd.Series(j["indicators"]["adjclose"][0]["adjclose"], index=t, dtype=float).dropna()


def monthly(c):
    return c.groupby([c.index.year, c.index.month]).last()


def f47_series(mk, c):
    """Mesicni cisty vynos drzeni XAU/XAG v mesici m (long), s naklady; signal z TLT na konci mesice m-1."""
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(c.iloc[-1])
    T = monthly(tlt())
    sig = (T / T.shift(1) - 1)                        # vynos TLT za mesic m-1 -> plati pro mesic m
    M = monthly(c)
    r = M / M.shift(1) - 1
    nights = 21 * 7 / 5
    net = r - rel + b["swapLong"] * nights            # vstup + vystup = 1 spread, swap ~30 noci
    df = pd.DataFrame({"r": net, "s": sig.shift(1)}).dropna()
    df.index = pd.to_datetime([f"{y}-{m:02d}-01" for y, m in df.index])
    return df


def f47():
    say("\n" + "=" * 100)
    say("F47 DLUHOPISY → ZLATO – TLT za předchozí měsíc > 0 → long XAU celý měsíc, jinak mimo trh")
    say("=" * 100)
    G = f47_series("XAUUSD", yahoo_close("XAUUSD"))
    h = broker_h1("XAUUSD")
    bc = h.close.groupby(h.index.date).last()
    bc.index = pd.to_datetime(bc.index)
    B = f47_series("XAUUSD", bc)
    S = f47_series("XAGUSD", yahoo_close("XAGUSD"))
    res = {}
    for nm, X in (("vyvoj", G[G.index < "2019-01-01"]), ("kontrola", G[G.index >= "2019-01-01"]), ("broker", B[B.index >= "2019-01-01"]),
                  ("stribro", S)):
        up, dn = X[X.s > 0].r, X[X.s <= 0].r
        diff, t = welch(up, dn)
        strat = np.where(X.s > 0, X.r, 0.0)
        sh_s = strat.mean() / strat.std() * np.sqrt(12)
        sh_l = X.r.mean() / X.r.std() * np.sqrt(12)
        res[nm] = dict(diff=diff, t=t, shs=sh_s, shl=sh_l)
        say(f"{nm:9s} po TLT nahoru {up.mean() * 100:+.2f} %/měs (n {len(up)}) | po TLT dolů {dn.mean() * 100:+.2f} % (n {len(dn)}) | "
            f"rozdíl {diff * 100:+.2f} p. b., t {t:+.2f} | Sharpe strategie {sh_s:.2f} vs stále long {sh_l:.2f}")
    v, k = res["vyvoj"], res["kontrola"]
    c = [("1) vývoj rozdíl > 0, t >= 2,0", v["diff"] > 0 and v["t"] >= 2.0, f"{v['diff'] * 100:+.2f} p. b., t {v['t']:+.2f}"),
         ("2) kontrola rozdíl > 0, t >= 1,5", k["diff"] > 0 and k["t"] >= 1.5, f"{k['diff'] * 100:+.2f} p. b., t {k['t']:+.2f}"),
         ("3) stříbro rozdíl > 0", res["stribro"]["diff"] > 0, f"{res['stribro']['diff'] * 100:+.2f} p. b."),
         ("4) broker 2019+ rozdíl > 0", res["broker"]["diff"] > 0, f"{res['broker']['diff'] * 100:+.2f} p. b."),
         ("5) Sharpe strategie > stále long (vývoj i kontrola)", v["shs"] > v["shl"] and k["shs"] > k["shl"],
          f"{v['shs']:.2f} vs {v['shl']:.2f}; {k['shs']:.2f} vs {k['shl']:.2f}")]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")


if __name__ == "__main__":
    f46()
    f47()
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
