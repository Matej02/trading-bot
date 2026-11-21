"""
F58 meny slabnou ve svych mistnich hodinach (Breedon a Ranaldo 2013) a F59 Turnaround Tuesday na US indexech.
Plan predem ve vaultu: Vyzkum/F58 a F59 Meny v mistnich hodinach a Turnaround Tuesday.md (2026-11-20).
Spusteni: python -I f58_f59.py -> D:\\Trading bot\\research_data\\f58\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402

LB, L = F.LB, F.L
RD = F.RD
OUT = os.path.join(RD, "f58")
os.makedirs(OUT, exist_ok=True)
CACHE = os.path.join(RD, "histdata", "m1_fx")
LINES = []
LON = "Europe/London"


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


# ------------------------------------------------------------------ F58 data (H1 v pravem UTC)
def hd_h1(sym):
    m = pd.read_pickle(os.path.join(CACHE, f"{sym}.pkl"))        # index UTC (prevedeno z NY casu HistData)
    r = m.resample("1h")
    h = pd.DataFrame({"open": r.open.first(), "high": r.high.max(), "low": r.low.min(), "close": r.close.last()}).dropna()
    return h


def br_h1(mk):
    h = pd.read_pickle(os.path.join(RD, f"{mk}_H1.pkl"))[["open", "high", "low", "close"]].astype(float)
    u = pd.DatetimeIndex(h.index).tz_localize("UTC")
    dst = np.array([x.dst().seconds > 0 for x in (u + pd.Timedelta(hours=1)).tz_convert(LON)])
    h.index = u + pd.to_timedelta(dst.astype(np.int64) * 3600, unit="s")
    return h[~h.index.duplicated()].sort_index()


# (start hodina Londyn, delka h, smer) pro kazdy par: okno mistnich hodin + okno US hodin
PLAN = {
    "EURUSD": [(7, 5, -1), (16, 5, +1)],
    "GBPUSD": [(7, 5, -1), (16, 5, +1)],
    "USDCHF": [(7, 5, +1), (16, 5, -1)],
    "USDJPY": [(0, 6, +1), (16, 5, -1)],
    "AUDUSD": [(0, 6, -1), (16, 5, +1)],
    "NZDUSD": [(0, 6, -1), (16, 5, +1)],
}


def windows(mk, h):
    """Vrati (signal, srovnani) DataFrame (day, R)."""
    b = L.BROKER[mk]
    spr = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0)
    loc = h.index.tz_convert(LON).tz_localize(None)
    op = pd.Series(h.open.to_numpy(), index=loc)
    cl = pd.Series(h.close.to_numpy(), index=loc)
    op, cl = op[~op.index.duplicated()], cl[~cl.index.duplicated()]
    g = h.groupby(loc.date)
    D = pd.DataFrame({"H": g.high.max(), "L": g.low.min(), "C": g.close.last()})
    pc = D.C.shift(1)
    atr = np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs())).rolling(20).mean().shift(1)
    atr.index = pd.to_datetime(atr.index)
    days = pd.DatetimeIndex(atr.index[atr.index.day_of_week < 5])
    sig_starts = {s for s, _, _ in PLAN[mk]}
    rs, rb = [], []
    for start, ln, dd in PLAN[mk]:
        for hr in range(24):
            t0 = days + pd.Timedelta(hours=hr)
            tl = t0 + pd.Timedelta(hours=ln - 1)
            E = op.reindex(t0).to_numpy()
            X = cl.reindex(tl).to_numpy()
            A = atr.reindex(days).to_numpy()
            ok = np.isfinite(E) & np.isfinite(X) & (A > 0)
            if not ok.any():
                continue
            # swap: okno prechazi pulnoc UTC
            u0 = t0.tz_localize(LON, ambiguous="NaT", nonexistent="NaT").tz_convert("UTC")
            u1 = (tl + pd.Timedelta(minutes=59)).tz_localize(LON, ambiguous="NaT", nonexistent="NaT").tz_convert("UTC")
            ok &= u0.notna() & u1.notna()
            nd = (u1.normalize().tz_localize(None) - u0.normalize().tz_localize(None)).days.to_numpy()
            thu = (u1.tz_localize(None).normalize().day_of_week.to_numpy() == 3)
            nights = np.where(nd > 0, np.where(thu, 3, 1), 0)
            cost = spr[hr] / 2 + spr[(hr + ln) % 24] / 2
            sw = (b["swapLong"] if dd == 1 else b["swapShort"]) * E * nights
            R = (dd * (X - E) - cost + sw) / A
            rows = list(zip(days[ok], R[ok]))
            if hr == start:
                rs += rows
            elif hr not in sig_starts:
                rb += rows
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def ev(pairs, a=None, b=None):
    S, B = [], []
    for mk, h in pairs:
        s, bb = windows(mk, h)
        S.append(s)
        B.append(bb)
    s, bb = pd.concat(S).groupby("day").R.mean(), pd.concat(B).groupby("day").R.mean()
    def sel(x):
        m = np.ones(len(x), bool)
        if a is not None:
            m &= x.index >= a
        if b is not None:
            m &= x.index < b
        return x[m]
    s, bb = sel(s), sel(bb)
    diff, t = F.welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


def decide(R, oth, share):
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    c = [("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ("3) jiné trhy převis > 0", oth["diff"] > 0, f"{oth['diff']:+.3f}"),
         ("4) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
         ("5) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    for nm, ok, val in c:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
    say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")


def show(R):
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")


def years(full):
    ys = sorted(set(full["s"].index.year))
    dif = {y: full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean() for y in ys}
    say("po letech převis: " + "  ".join(f"{y}:{v:+.3f}" for y, v in dif.items()))
    pos = [v > 0 for v in dif.values()]
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({np.mean(pos):.0%})")
    return float(np.mean(pos))


def f58():
    say("=" * 100)
    say("F58 MĚNY SLÁBNOU VE SVÝCH MÍSTNÍCH HODINÁCH – Evropa 07–12 / Asie 00–06 Londýn cizí měna slabá, 16–21 USD slabý")
    say("=" * 100)
    SP = pd.Timestamp("2019-01-01")
    HD = [(m, hd_h1(m)) for m in ("EURUSD", "GBPUSD", "USDJPY")]
    BR = [(m, br_h1(m)) for m in ("EURUSD", "GBPUSD", "USDJPY")]
    OT = [(m, br_h1(m)) for m in ("AUDUSD", "NZDUSD", "USDCHF")]
    R = {"vyvoj": ev(HD, pd.Timestamp("2010-01-01"), SP), "kontrola": ev(HD, SP, None), "broker": ev(BR, SP, None)}
    show(R)
    oth = ev(OT, pd.Timestamp("2010-01-01"), None)
    say(f"jiné trhy AUDUSD, NZDUSD, USDCHF (broker 2010+): signál {LB.fmt(oth['sig'])} | převis {oth['diff']:+.3f}, t {oth['t']:+.2f}")
    for mk, h in HD + OT:
        for j, (s0, ln, dd) in enumerate(PLAN[mk]):
            P = dict(PLAN)
            P_save = PLAN[mk]
            PLAN[mk] = [P_save[j]]
            v = ev([(mk, h)])
            PLAN[mk] = P_save
            say(f"   {mk} {s0:02d}:00+{ln}h {'long' if dd > 0 else 'short'}: {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    full = ev(HD)
    share = years(full)
    decide(R, oth, share)


# ------------------------------------------------------------------ F59
def f59_trades(mk, d, open_entry=False):
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    pc = d.close.shift(1)
    A = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean().to_numpy()
    O, C, idx, n = d.open.to_numpy(), d.close.to_numpy(), d.index, len(d)
    dow = idx.day_of_week
    rs, rb = [], []
    for i in range(22, n):
        if not A[i - 1] > 0:
            continue
        E = O[i] if open_entry else C[i - 1]
        nts = 0 if open_entry else F.nights(idx[i - 1], idx[i])
        R = ((C[i] - E) - rel * (E + C[i]) / 2 + b["swapLong"] * E * nts) / A[i - 1]
        sig = dow[i] == 1 and dow[i - 1] == 0 and C[i - 1] < C[i - 2]
        (rs if sig else rb).append((idx[i], R))
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def ev59(mks, src, a, b, open_entry=False):
    S, B = [], []
    for mk in mks:
        d = F.yahoo(mk) if src == "yahoo" else F.broker(mk)
        s, bb = f59_trades(mk, d, open_entry)
        S.append(s)
        B.append(bb)
    s, bb = pd.concat(S).groupby("day").R.mean(), pd.concat(B).groupby("day").R.mean()
    sel = lambda x: x[(x.index >= a) & ((x.index < b) if b is not None else True)]  # noqa: E731
    s, bb = sel(s), sel(bb)
    diff, t = F.welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


def f59():
    say("\n" + "=" * 100)
    say("F59 TURNAROUND TUESDAY – pondělí dolů → long pondělní zavření → úterní zavření; srovnání = ostatní dny")
    say("=" * 100)
    US = ["SPX500mini", "NAS100mini", "US30mini"]
    EU = ["GER_30mini", "GBR_100mini", "FRA_40mini"]
    D0 = pd.Timestamp("1990-01-01")
    R = {"vyvoj": ev59(US, "yahoo", D0, F.SPLIT), "kontrola": ev59(US, "yahoo", F.SPLIT, None), "broker": ev59(US, "broker", F.SPLIT, None)}
    show(R)
    oth = ev59(EU, "yahoo", D0, None)
    say(f"jiné trhy {', '.join(EU)}: signál {LB.fmt(oth['sig'])} | převis {oth['diff']:+.3f}, t {oth['t']:+.2f}")
    for nm, a, b in (("vývoj", D0, F.SPLIT), ("kontrola", F.SPLIT, None)):
        v = ev59(US, "yahoo", a, b, open_entry=True)
        say(f"popis – vstup úterní otevření, {nm}: {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    share = years(ev59(US, "yahoo", D0, None))
    decide(R, oth, share)


if __name__ == "__main__":
    f58()
    f59()
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
