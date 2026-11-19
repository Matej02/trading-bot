"""
F43 Pruraz F2 prisna proverka - signal vs. stejne vstupy/vystupy ve vsech dnech s tydennim trendem (drift).
Plan predem ve vaultu: Vyzkum/F43 Pruraz F2 prisna proverka.md (2026-11-19).
Spusteni: python -I f43_proraz.py -> D:\\Trading bot\\research_data\\f43\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f2x_lib as LB  # noqa: E402

L = LB.L
RD = os.path.join(LB.ROOT, "research_data")
OUT = os.path.join(RD, "f43")
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
DEV0, SPLIT = pd.Timestamp("1990-01-01"), pd.Timestamp("2019-01-01")
F2 = ["BTCUSD", "ETHUSD", "XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "SPX500mini", "NAS100mini", "GER_30mini"]
OTHER = ["US30mini", "GBR_100mini", "FRA_40mini", "XAGUSD", "CRUDE_OIL"]
CRYPTO = {"BTCUSD", "ETHUSD"}
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def clean(d, mk):
    d = d[["open", "high", "low", "close"]].astype(float)
    ok = (d.high >= d.low) & (d.low <= d.close) & (d.close <= d.high) & (d.low <= d.open) & (d.open <= d.high) & (d.close > 0)
    d = d[ok].dropna()
    return d if mk in CRYPTO else d[d.index.day_of_week < 5]


def yahoo(mk):
    d = pd.read_pickle(os.path.join(RD, f"f6_{mk}_1d.pkl"))
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    return clean(d, mk)


def broker(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))
    h.index = pd.to_datetime(h.index)
    g = h.groupby(h.index.normalize())
    d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()}).dropna()
    return clean(d, mk)


def weekly_trend(c):
    """Tydenni trend k zavreni kazdeho dne: jen dokoncene tydny (tyden konci v nedeli; patek = posledni den tydne)."""
    wk = c.resample("W-SUN").last().dropna()
    e = wk.ewm(span=50, adjust=False).mean()
    tr = pd.Series(np.where((wk > e) & (e > e.shift(3)), 1, np.where((wk < e) & (e < e.shift(3)), -1, 0)), index=wk.index)
    tr[np.arange(len(tr)) < 53] = 0
    # den D: pouzit posledni tyden, ktery skoncil nejpozdeji koncem dne D (patek = dokonceny tyden u ne-krypta)
    dow = np.asarray(c.index.day_of_week)
    lab = c.index + pd.to_timedelta(6 - dow, unit="D")                       # nedele tydne dne D
    done = lab.where(dow >= 4, lab - pd.Timedelta(days=7))                   # od patku je tyden hotovy
    return pd.Series(tr.reindex(done, method="ffill").to_numpy(), index=c.index).fillna(0)


def nights(d0, d1, crypto):
    if crypto:
        return (d1 - d0).days
    days = pd.date_range(d0 + pd.Timedelta(days=1), d1, freq="D")
    w = days.day_of_week
    return int(((w < 5) & (w != 3)).sum() + 3 * (w == 3).sum())


def run(mk, d):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    c = d.close
    pc = c.shift(1)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    atr = tr.rolling(14).mean().to_numpy()
    wt = weekly_trend(c).to_numpy()
    hi20 = d.high.shift(1).rolling(20).max().to_numpy()
    lo20 = d.low.shift(1).rolling(20).min().to_numpy()
    O, H, Lo, C = d.open.to_numpy(), d.high.to_numpy(), d.low.to_numpy(), c.to_numpy()
    idx, n = d.index, len(d)
    cr = mk in CRYPTO

    def one(i, dd):
        e = i + 1
        if e >= n or not atr[i] > 0:
            return None
        risk = 2 * atr[i]
        sl, tp = C[i] - dd * risk, C[i] + dd * 2 * risk
        E = O[e]
        if (dd == 1 and E <= sl) or (dd == -1 and E >= sl):
            X, k = E, e
        else:
            X = None
            for k in range(e, min(e + 48, n)):
                hit_sl = Lo[k] <= sl if dd == 1 else H[k] >= sl
                hit_tp = H[k] >= tp if dd == 1 else Lo[k] <= tp
                if hit_sl:
                    X = sl if k == e else (min(sl, O[k]) if dd == 1 else max(sl, O[k]))
                    break
                if hit_tp:
                    X = tp if k == e else (max(tp, O[k]) if dd == 1 else min(tp, O[k]))
                    break
            if X is None:
                if e + 47 >= n:
                    return None
                k = e + 47
                X = C[k]
        sw = (b["swapLong"] if dd == 1 else b["swapShort"]) * E * nights(idx[e], idx[k], cr)
        net = dd * (X - E) - rel * (E + X) / 2 + sw
        return k, net / risk

    rs, rb = [], []
    busy = -1
    for i in range(260, n - 1):
        dd = int(wt[i])
        if dd == 0:
            continue
        r = one(i, dd)
        if r is not None:
            rb.append((idx[i + 1], r[1]))
        brk = (dd == 1 and C[i] > hi20[i]) or (dd == -1 and C[i] < lo20[i])
        if brk and i > busy and r is not None:
            rs.append((idx[i + 1], r[1]))
            busy = r[0]
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    diff = a.mean() - b.mean()
    return diff, diff / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def evaluate(mks, src, a, b):
    S, B = [], []
    for mk in mks:
        d = yahoo(mk) if src == "yahoo" else broker(mk)
        s, bb = run(mk, d)
        S.append(s)
        B.append(bb)
    s = pd.concat(S).groupby("day").R.mean()
    bb = pd.concat(B).groupby("day").R.mean()
    sel = lambda x: x[(x.index >= a) & ((x.index < b) if b is not None else True)]  # noqa: E731
    s, bb = sel(s), sel(bb)
    diff, t = welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


def main():
    say("F43 Průraz F2 – zavření za 20denním extrémem ve směru týdenního trendu, vstup otevření dalšího dne, SL 2 ATR / TP 4 ATR / 48 dní")
    say("srovnání = stejné vstupy a výstupy ve všech dnech s daným týdenním trendem; hodnoceno po dnech vstupu; R = výsledek / 2 ATR")
    say("=" * 100)
    R = {"vyvoj": evaluate(F2, "yahoo", DEV0, SPLIT), "kontrola": evaluate(F2, "yahoo", SPLIT, None),
         "broker": evaluate(F2, "broker", SPLIT, None)}
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    oth = evaluate(OTHER, "yahoo", DEV0, None)
    say(f"jiné trhy (US30, FTSE, CAC, XAG, WTI): signál {LB.fmt(oth['sig'])} | převis {oth['diff']:+.3f}, t {oth['t']:+.2f}")
    say("Po trzích (Yahoo, celé období, signál / převis):")
    for mk in F2:
        v = evaluate([mk], "yahoo", DEV0, None)
        say(f"   {mk:11s} {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}")
    full = evaluate(F2, "yahoo", DEV0, None)
    pos, line = [], []
    for y in sorted(set(full["s"].index.year)):
        dy = full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean()
        pos.append(dy > 0)
        line.append(f"{y}:{dy:+.2f}")
    share = float(np.mean(pos))
    for i in range(0, len(line), 10):
        say("   " + "  ".join(line[i:i + 10]))
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    c = [("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ("3) jiné trhy převis > 0", oth["diff"] > 0, f"{oth['diff']:+.3f}"),
         ("4) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
         ("5) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
