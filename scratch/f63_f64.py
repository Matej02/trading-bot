"""
F63 den pred svatkem na evropskych indexech, F64 hodiny bitcoinu (vyber okna na vyvoji 2019-2021, overeni 2022+).
Plan predem ve vaultu: Vyzkum/F63 a F64 Den pred svatkem v Evrope a hodiny bitcoinu.md (2026-11-20).
Spusteni: python -I f63_f64.py -> D:\\Trading bot\\research_data\\f63\\souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import f55_f57 as T55  # noqa: E402
import f58_f59 as T58  # noqa: E402

LB, L = F.LB, F.L
RD = F.RD
OUT = os.path.join(RD, "f63")
os.makedirs(OUT, exist_ok=True)
EU = ["GER_30mini", "GBR_100mini", "FRA_40mini", "EUR_50mini", "ESP_35mini"]
LON = "Europe/London"
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


def ok(nm, c, val):
    say(f"   {nm}: {'ANO' if c else 'NE'} ({val})")
    return c


# ------------------------------------------------------------------ F63
def yahoo_clean(mk):
    d = F.yahoo(mk)
    flat = (d.open == d.high) & (d.high == d.low) & (d.low == d.close)
    return d[~flat]


def pre_holidays(d):
    """Dny P: po nich nasleduje 1-2 pracovni dny bez obchodu. Vrati (set P, set dnu v okne prelomu mesice)."""
    idx = d.index
    nxt = idx[1:]
    gap = np.busday_count(idx[:-1].values.astype("datetime64[D]") + np.timedelta64(1, "D"), nxt.values.astype("datetime64[D]"))
    P = set(idx[:-1][(gap >= 1) & (gap <= 2)])
    per = idx.to_period("M")
    last = np.r_[per[1:] != per[:-1], False]
    first = np.r_[True, per[1:] != per[:-1]]
    k = np.ones(len(idx), int)
    for i in range(1, len(idx)):
        k[i] = 1 if first[i] else k[i - 1] + 1
    tom = set(idx[last | (k <= 3)])
    return P, tom


def cc_trades(mk, d, P, excl=None):
    b, rel, A = T55.prep(mk, d)
    C, idx = d.close.to_numpy(), d.index
    rs, rb = [], []
    for i in range(21, len(d)):
        if not A[i - 1] > 0:
            continue
        R = T55.net(b, rel, C[i - 1], C[i], idx[i - 1], idx[i]) / A[i - 1]
        if idx[i] in P:
            if excl is None or idx[i] not in excl:
                rs.append((idx[i], R))
        else:
            rb.append((idx[i], R))
    return pd.DataFrame(rs, columns=["day", "R"]), pd.DataFrame(rb, columns=["day", "R"])


def ev63(mks, src, a, b, excl_tom=False):
    Sx, Bx = [], []
    for mk in mks:
        y = yahoo_clean(mk)
        P, tom = pre_holidays(y)
        d = y if src == "yahoo" else F.broker(mk)
        s, bb = cc_trades(mk, d, P, tom if excl_tom else None)
        Sx.append(s)
        Bx.append(bb)
    s, bb = pd.concat(Sx).groupby("day").R.mean(), pd.concat(Bx).groupby("day").R.mean()
    m = lambda x: x[(x.index >= a) & ((x.index < b) if b is not None else np.ones(len(x), bool))]  # noqa: E731
    s, bb = m(s), m(bb)
    diff, t = F.welch(s, bb)
    return dict(sig=LB.st(s), base=LB.st(bb), diff=diff, t=t, s=s, b=bb)


def f63():
    say("=" * 100)
    say("F63 DEN PŘED SVÁTKEM V EVROPĚ – long zavření P−1 → zavření P; srovnání = ostatní dny; DAX, FTSE, CAC, EuroStoxx, IBEX")
    say("=" * 100)
    D0 = pd.Timestamp("1990-01-01")
    R = {"vyvoj": ev63(EU, "yahoo", D0, F.SPLIT), "kontrola": ev63(EU, "yahoo", F.SPLIT, None), "broker": ev63(EU, "broker", F.SPLIT, None)}
    for k, v in R.items():
        say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
        say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
        say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
    for mk in EU:
        y = yahoo_clean(mk)
        P, _ = pre_holidays(y)
        per = pd.Series(1, index=sorted(P))
        cnt = per.groupby(per.index.year).sum()
        v = ev63([mk], "yahoo", D0, None)
        say(f"   {mk:12s} {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f} | dnů P za rok ~{cnt.median():.0f} "
            f"(2000–26 min {cnt[cnt.index >= 2000].min()}, max {cnt[cnt.index >= 2000].max()})")
    ex = ev63(EU, "yahoo", D0, None, excl_tom=True)
    say(f"bez dnů přelomu měsíce (celé období): signál {LB.fmt(ex['sig'])} | převis {ex['diff']:+.3f}, t {ex['t']:+.2f}")
    full = ev63(EU, "yahoo", D0, None)
    ys = sorted(set(full["s"].index.year))
    dif = {y: full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean() for y in ys}
    pos = [v > 0 for v in dif.values()]
    share = float(np.mean(pos))
    say("po letech převis: " + "  ".join(f"{y}:{v:+.2f}" for y, v in dif.items()))
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")
    v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    c = [ok("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0,
            f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
         ok("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5,
            f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
         ok("3) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
         ok("4) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}"),
         ok("5) bez dnů přelomu měsíce převis > 0", ex["diff"] > 0, f"{ex['diff']:+.3f}")]
    say(f"   => {'VÝHODA (prošlo vše)' if all(c) else 'BEZ VÝHODY'}")


# ------------------------------------------------------------------ F64
def binance(sym):
    h = pd.read_pickle(os.path.join(RD, f"binance_{sym}_1h.pkl"))[["open", "high", "low", "close"]].astype(float)
    i = pd.DatetimeIndex(h.index)
    h.index = i.tz_localize("UTC") if i.tz is None else i.tz_convert("UTC")
    return h[~h.index.duplicated()].sort_index()


def windows64(h, mk, ln=4):
    """R pro kazde okno (zacatek v cele hodine UTC) a smer. Vrati dict (hodina, smer) -> Series po dnech UTC."""
    b = L.BROKER[mk]
    spr = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0)
    op = h.open
    cl = h.close
    day = h.index.floor("D")
    g = h.groupby(day)
    D = pd.DataFrame({"H": g.high.max(), "L": g.low.min(), "C": g.close.last()})
    pc = D.C.shift(1)
    atr = np.maximum(D.H - D.L, np.maximum((D.H - pc).abs(), (D.L - pc).abs())).rolling(20).mean().shift(1)
    days = atr.index[np.isfinite(atr.to_numpy())]
    A = atr.reindex(days).to_numpy()
    out = {}
    for s in range(24):
        t0 = days + pd.Timedelta(hours=s)
        t1 = t0 + pd.Timedelta(hours=ln - 1)
        E = op.reindex(t0).to_numpy()
        X = cl.reindex(t1).to_numpy()
        cost = spr[s] / 2 + spr[(s + ln - 1) % 24] / 2
        # pres pulnoc Londyn (rollover)? drzeni (t0, t0 + ln h)
        a0 = t0.tz_convert(LON)
        a1 = (t0 + pd.Timedelta(hours=ln) - pd.Timedelta(seconds=1)).tz_convert(LON)
        cross = np.asarray(a0.normalize() != a1.normalize()).astype(float)
        for dr, sw in (("long", b["swapLong"]), ("short", b["swapShort"])):
            mv = (X - E) if dr == "long" else (E - X)
            R = (mv - cost + sw * E * cross) / A
            m = np.isfinite(R)
            out[(s, dr)] = pd.Series(R[m], index=days[m].tz_localize(None))
    return out


def excess(W, key, a=None, b=None):
    s = W[key]
    others = [W[k] for k in W if k[1] == key[1] and k[0] != key[0]]
    bb = pd.concat(others).groupby(level=0).mean()
    if a is not None:
        s, bb = s[s.index >= a], bb[bb.index >= a]
    if b is not None:
        s, bb = s[s.index < b], bb[bb.index < b]
    diff, t = F.welch(s, bb)
    return dict(sig=LB.st(s), diff=diff, t=t, s=s, b=bb)


def f64():
    say("\n" + "=" * 100)
    say("F64 HODINY BITCOINU – 4h okna long/short podle hodiny UTC; výběr na vývoji 2019–2021, ověření 2022–2026")
    say("=" * 100)
    D22 = pd.Timestamp("2022-01-01")
    D19 = pd.Timestamp("2019-01-01")
    bn = binance("BTCUSDT")
    W = windows64(bn, "BTCUSD")
    res = []
    for key in W:
        v = excess(W, key, D19, D22)
        res.append((v["t"], key, v["diff"], v["sig"]["m"]))
    res.sort(reverse=True)
    say("vývoj 2019–2021, 10 nejlepších oken (t převisu):")
    for t, (s, dr), dfx, m in res[:10]:
        say(f"   {s:02d}:00–{(s + 4) % 24:02d}:00 UTC {dr:5s} | signál {m:+.3f} R | převis {dfx:+.3f} | t {t:+.2f}")
    best = res[0][1]
    s0, dr0 = best
    say(f"VYBRÁNO: {s0:02d}:00–{(s0 + 4) % 24:02d}:00 UTC {dr0}")
    dev = excess(W, best, D19, D22)
    kon = excess(W, best, D22, None)
    br = T58.br_h1("BTCUSD")
    Wb = windows64(br[br.index >= pd.Timestamp("2021-11-01", tz="UTC")], "BTCUSD")
    brk = excess(Wb, best, D22, None)
    We = windows64(binance("ETHUSDT"), "ETHUSD")
    eth = excess(We, best, D22, None)
    for nm, v in (("vývoj Binance 2019–21", dev), ("kontrola Binance 2022–26", kon), ("broker BTC 2022–26", brk), ("ETH Binance 2022–26", eth)):
        say(f"{nm:25s} signál {LB.fmt(v['sig'])} | převis {v['diff']:+.3f}, t {v['t']:+.2f}")
    full = excess(W, best, D19, None)
    ys = sorted(set(full["s"].index.year))
    dif = {y: full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean() for y in ys}
    pos = [v > 0 for v in dif.values()]
    share = float(np.mean(pos))
    say("po letech převis: " + "  ".join(f"{y}:{v:+.3f}" for y, v in dif.items()))
    say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")
    r1 = (bn.close / bn.open - 1) * 1e4
    hr = bn.index.hour
    for nm, msk in (("vývoj 2019–21", bn.index < pd.Timestamp("2022-01-01", tz="UTC")), ("kontrola 2022–26", bn.index >= pd.Timestamp("2022-01-01", tz="UTC"))):
        prof = r1[msk].groupby(hr[msk]).mean()
        say(f"popis – průměrný výnos 1h svíčky v bp podle hodiny UTC, {nm}: " + " ".join(f"{h:02d}:{v:+.1f}" for h, v in prof.items()))
    say("ROZHODNUTÍ podle pravidel zapsaných předem")
    c = [ok("1) vývoj: vybrané okno t >= 3,0", dev["t"] >= 3.0, f"t {dev['t']:+.2f}"),
         ok("2) kontrola: signál > 0, převis > 0, t >= 1,5", kon["sig"]["m"] > 0 and kon["diff"] > 0 and kon["t"] >= 1.5,
            f"{kon['sig']['m']:+.3f}, převis {kon['diff']:+.3f}, t {kon['t']:+.2f}"),
         ok("3) broker: signál > 0 a převis > 0", brk["sig"]["m"] > 0 and brk["diff"] > 0, f"{brk['sig']['m']:+.3f}, převis {brk['diff']:+.3f}"),
         ok("4) ETH převis > 0", eth["diff"] > 0, f"{eth['diff']:+.3f}"),
         ok("5) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
    say(f"   => {'VÝHODA (prošlo vše)' if all(c) else 'BEZ VÝHODY'}")


if __name__ == "__main__":
    f63()
    f64()
    open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
