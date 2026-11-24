"""
F73-F78 dluhopisy, VIX a strach jako signal pro indexy. Plan predem ve vaultu:
Vyzkum/F73 az F78 Dluhopisy, VIX a strach jako signal pro indexy.md (commit dc680ce).
Signal na zavreni dne i -> long od otevreni i+1 na h dni (stop 3 ATR20), proti stejnemu obchodu ze vsech dni.
Spusteni: python -I f73_f78.py -> D:\\Trading bot\\research_data\\f73\\souhrn.txt
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402

LB, L = F.LB, F.L
RD = F.RD
OUT = os.path.join(RD, "f73")
os.makedirs(OUT, exist_ok=True)
SPLIT = pd.Timestamp("2019-01-01")
US = ["SPX500mini", "NAS100mini", "US30mini"]
EU = ["GER_30mini", "GBR_100mini", "FRA_40mini"]
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def yjson(path, adj=False):
    j = json.load(open(path))["chart"]["result"][0]
    t = pd.to_datetime(j["timestamp"], unit="s").normalize()
    v = j["indicators"]["adjclose"][0]["adjclose"] if adj else j["indicators"]["quote"][0]["close"]
    return pd.Series(v, index=t, dtype=float).dropna().groupby(level=0).last()


VIX = yjson(os.path.join(RD, "f44", "VIX.json"))
TLT = yjson(os.path.join(RD, "f33", "yahoo", "TLT.json"), adj=True)
JPY = F.yahoo("USDJPY")

# ---------------------------------------------------------------- signaly (serie bool podle data, US kalendar)
_v = VIX
SIG_VIX_STRETCH = _v >= 1.10 * _v.rolling(10).mean()
_vmax5 = _v.rolling(5).max()
_p90 = _v.shift(1).rolling(252).quantile(0.90)
SIG_FEAR_FADE = (_vmax5 >= _p90) & (_v <= 0.9 * _vmax5)
SIG_VIX30 = _v >= 30
_r5 = TLT / TLT.shift(5) - 1
SIG_TLT = _r5 >= _r5.shift(1).rolling(252).quantile(0.90)
_jc = JPY.close
_jpc = _jc.shift(1)
_jtr = np.maximum(JPY.high - JPY.low, np.maximum((JPY.high - _jpc).abs(), (JPY.low - _jpc).abs()))
SIG_JPY = (_jc - _jpc) <= -1.5 * _jtr.rolling(20).mean()


def ext(s, d):
    """Signal z US/jineho kalendare na dny trhu d (jen dny, kdy oba maji data)."""
    return s.reindex(d.index).fillna(False).astype(bool).to_numpy()


TESTS = {
    "F73 utek do dluhopisu": dict(h=5, dev0="2004-01-01",
                                  sig=lambda mk, d: ext(SIG_TLT, d) & (d.close / d.close.shift(5) - 1 < 0).to_numpy()),
    "F74 natazeny VIX": dict(h=5, dev0="1990-01-01", sig=lambda mk, d: ext(SIG_VIX_STRETCH, d)),
    "F75 strach odeznivá": dict(h=10, dev0="1991-01-01", sig=lambda mk, d: ext(SIG_FEAR_FADE, d)),
    "F76 VIX >= 30": dict(h=20, dev0="1990-01-01", sig=lambda mk, d: ext(SIG_VIX30, d)),
    "F77 52tydenni maximum": dict(h=20, dev0="1990-01-01",
                                  sig=lambda mk, d: (d.close >= d.close.rolling(252).max()).to_numpy()),
    "F78 utek do jenu": dict(h=5, dev0="1997-01-01", sig=lambda mk, d: ext(SIG_JPY, d)),
}


def run(mk, d, sig, h):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    c = d.close
    pc = c.shift(1)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    A = tr.rolling(20).mean().to_numpy()
    O, Lo, C = d.open.to_numpy(), d.low.to_numpy(), c.to_numpy()
    idx, n = d.index, len(d)

    def one(i):
        e = i + 1
        if e + h - 1 >= n or not A[i] > 0:
            return None
        E = O[e]
        risk = 3 * A[i]
        stop = E - risk
        X = None
        for k in range(e, e + h):
            if Lo[k] <= stop:
                X = min(stop, O[k]) if k > e else stop
                break
        if X is None:
            k = e + h - 1
            X = C[k]
        net = (X - E) - rel * (E + X) / 2 + b["swapLong"] * E * F.nights(idx[e], idx[k])
        return k, net / risk

    rs, rb = [], []
    busy = -1
    for i in range(252, n - 1):
        r = one(i)
        if r is None:
            continue
        rb.append((idx[i + 1], r[1]))
        if sig[i] and i > busy:
            rs.append((idx[i + 1], r[1]))
            busy = r[0]
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def evaluate(name, cfg, mks, src, a, b):
    Ss, Bs = [], []
    for mk in mks:
        d = F.yahoo(mk) if src == "yahoo" else F.broker(mk)
        s, bb = run(mk, d, cfg["sig"](mk, d), cfg["h"])
        Ss.append(s)
        Bs.append(bb)
    s = pd.concat(Ss).groupby("day").R.mean()
    bb = pd.concat(Bs).groupby("day").R.mean()
    sel = lambda x: x[(x.index >= pd.Timestamp(a)) & ((x.index < pd.Timestamp(b)) if b is not None else True)]  # noqa: E731
    s, bb = sel(s), sel(bb)
    if len(s) < 2:
        return dict(sig=LB.st(s), base=LB.st(bb), diff=np.nan, t=np.nan, s=s, b=bb)
    diff, t = F.welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


def test(name, cfg):
    say("=" * 100)
    say(f"{name}  (drzeni {cfg['h']} dni, vyvoj od {cfg['dev0']})")
    R = {"vyvoj": evaluate(name, cfg, US, "yahoo", cfg["dev0"], SPLIT),
         "kontrola": evaluate(name, cfg, US, "yahoo", SPLIT, None),
         "broker": evaluate(name, cfg, US, "broker", SPLIT, None)}
    for k, v in R.items():
        say(f"{k:9s} signal:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnani: {LB.fmt(v['base'])}")
        say(f"{'':9s} previs {v['diff']:+.3f} R, t {v['t']:+.2f}")
    O = {}
    for mk in EU:
        O[mk] = evaluate(name, cfg, [mk], "yahoo", cfg["dev0"], None)
        say(f"{mk:11s}: signal {LB.fmt(O[mk]['sig'])} | previs {O[mk]['diff']:+.3f}, t {O[mk]['t']:+.2f}")
    full = evaluate(name, cfg, US, "yahoo", cfg["dev0"], None)
    pos, line = [], []
    for y in sorted(set(full["s"].index.year)):
        dy = full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean()
        pos.append(dy > 0)
        line.append(f"{y}:{dy:+.2f}")
    share = float(np.mean(pos)) if pos else 0.0
    for i in range(0, len(line), 10):
        say("   " + "  ".join(line[i:i + 10]))
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    c = [v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0,
         k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5,
         all(O[m]["diff"] > 0 for m in O),
         br["sig"]["m"] > 0 and br["diff"] > 0,
         share >= 0.55]
    say(f"previs kladny v {sum(pos)} z {len(pos)} let ({share:.0%})")
    say("BODY 1-5: " + " ".join("ANO" if x else "ne" for x in c) + f"  => {'VYHODA (proslo vse)' if all(c) else 'BEZ VYHODY'}")
    return all(c), c


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    res = {nm: test(nm, cfg) for nm, cfg in TESTS.items()}
    say("=" * 100)
    for nm, (ok, c) in res.items():
        say(f"{nm:28s} {sum(c)}/5  {'PROSLO' if ok else 'neproslo'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write("\n".join(LINES) + "\n")
