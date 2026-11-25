"""
F85 RSI(2) na akciich. Plan predem ve vaultu: Vyzkum/F85 RSI(2) na akciich.md (commit a02a995).
Data: research_data/f85 (f85_stahni.py). Spusteni: python -I f85_rsi2_akcie.py -> research_data/f85/souhrn.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402
import prop_meritko as PM  # noqa: E402

RD = os.path.join(F.RD, "f85")
LINES = []
DEV = ("1996-01-01", "2019-01-01")
CTL = ("2019-01-01", "2100-01-01")
COST = dict(norm=(0.0005, 0.00004, 0.12), pess=(0.0010, 0.00004, 0.15), gross=(0.0, 0.0, 0.0))
MAXD = 10
MAX_POS = 5
FTMO_US = ["AAPL", "AMZN", "BA", "BABA", "BAC", "CSCO", "CVX", "DIS", "META", "FDX", "GE", "GM", "GOOG", "IBM", "INTC", "JNJ", "JPM",
           "KO", "MCD", "MSFT", "NFLX", "NVDA", "PFE", "QCOM", "RACE", "T", "TSLA", "V", "WMT", "XOM", "ZM", "RTX", "LMT", "PLTR", "AMD",
           "AVGO", "SBUX", "MSTR", "GME", "NKE", "ARM", "SNOW", "ASML", "AZN", "BRK-B"]


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


# ---------------------------------------------------------------- data
def clean(d):
    d = d[["open", "high", "low", "close"]].astype(float).copy()
    d.index = pd.to_datetime(d.index).tz_localize(None).normalize()
    ok = (d.high >= d.low) & (d.low <= d.close) & (d.close <= d.high) & (d.low <= d.open) & (d.open <= d.high) & (d.close > 0) & (d.low > 0)
    d = d[ok].dropna()
    d = d[~d.index.duplicated()]
    return d[d.index.day_of_week < 5]


def membership():
    h = pd.read_csv(os.path.join(RD, "raw", "sp500_hist.csv"))
    h["_d"] = pd.to_datetime(h.iloc[:, 0])
    h = h.sort_values("_d")
    dates = list(h["_d"])
    sets = [{x.strip().replace(".", "-") for x in str(s).split(",") if x.strip()} for s in h.iloc[:, 1]]
    iv = {}
    prev = set()
    for dt, cur in zip(dates, sets):
        for t in cur - prev:
            iv.setdefault(t, []).append([dt, pd.Timestamp("2100-01-01")])
        for t in prev - cur:
            iv[t][-1][1] = dt
        prev = cur
    return iv, dates, sets


def member_mask(idx, intervals):
    m = np.zeros(len(idx), bool)
    for a, b in intervals:
        m |= (idx >= a) & (idx < b)
    return m


# ---------------------------------------------------------------- obchody (vektorove, pravidlo F42)
def trades_all(d):
    """Pro kazdy den i (signal na zavreni) vysledek vstupu na otevreni i+1 podle F42. Vraci dict poli delky n (nan = neplatne)."""
    n = len(d)
    O, H, Lo, C = (d[c].to_numpy() for c in ("open", "high", "low", "close"))
    c = d.close
    S200, S5 = c.rolling(200).mean().to_numpy(), c.rolling(5).mean().to_numpy()
    rsi = F.rsi_wilder(c).to_numpy()
    A = PM._atr20(d).to_numpy()
    out = dict(up=np.zeros(n, bool), sig=np.zeros(n, bool), rsi=rsi, ok=np.zeros(n, bool), k=np.full(n, -1),
               hit=np.zeros(n, bool), E=np.full(n, np.nan), X=np.full(n, np.nan), Xno=np.full(n, np.nan), risk=np.full(n, np.nan),
               days=np.zeros(n), jstar=np.zeros(n, int))
    if n < 215:
        return out, None
    i = np.arange(200, n - 1)
    e = i + 1
    E, risk = O[e], 3 * A[i]
    stop = E - risk
    J = np.arange(MAXD)
    K = e[:, None] + J[None, :]
    vK = K < n
    Kc = np.minimum(K, n - 1)
    hit = (Lo[Kc] <= stop[:, None]) & vK
    exc = ((C[Kc] > S5[Kc]) | (J[None, :] == MAXD - 1)) & vK
    ev = hit | exc
    has = ev.any(axis=1)
    js = ev.argmax(axis=1)
    r = np.arange(len(i))
    ks = e + js
    ksc = np.minimum(ks, n - 1)
    ish = hit[r, js]
    X = np.where(ish, np.where(js == 0, stop, np.minimum(stop, O[ksc])), C[ksc])
    nxt = np.minimum(ksc + 1, n - 1)
    Xno = np.where(ish, X, np.where(ksc + 1 < n, O[nxt], np.nan))
    ok = has & (risk > 0) & (E > 0) & np.isfinite(X)
    up = c.to_numpy()[i] > S200[i]
    out["up"][i] = up
    out["sig"][i] = up & (rsi[i] < 10)
    out["ok"][i] = ok
    out["k"][i] = ks
    out["hit"][i] = ish
    out["E"][i], out["X"][i], out["Xno"][i], out["risk"][i] = E, X, Xno, risk
    out["jstar"][i] = js
    idx = d.index.to_numpy()
    out["days"][i] = (idx[ksc] - idx[e]).astype("timedelta64[D]").astype(float)
    path = dict(lo=np.where(vK, (Lo[Kc] - E[:, None]) / risk[:, None], np.nan), cl=np.where(vK, (C[Kc] - E[:, None]) / risk[:, None], np.nan),
                i0=200)
    return out, path


def net_R(o, sel, cost, X="X"):
    hs, cm, fin = COST[cost]
    E, Xv, rk = o["E"][sel], o[X][sel], o["risk"][sel]
    nights = o["days"][sel] + (1 if X == "Xno" else 0)
    return ((Xv - E) - (hs + cm) * (E + Xv) - fin * E * nights / 365.0) / rk


def stock_rows(t, d, mask):
    """Signalni obchody (s busy) a srovnani (vsechny dny nad SMA200) jen ve dnech clenstvi."""
    o, path = trades_all(d)
    n = len(d)
    idx = d.index
    base_sel = o["up"] & o["ok"] & mask
    sig_i = np.flatnonzero(o["sig"] & o["ok"] & mask)
    keep, busy = [], -1
    for i in sig_i:
        if i > busy:
            keep.append(i)
            busy = o["k"][i]
    keep = np.array(keep, int)
    sel = np.zeros(n, bool)
    sel[keep] = True
    S = pd.DataFrame(dict(day=idx[np.minimum(keep + 1, n - 1)], t=t, R=net_R(o, sel, "norm"), Rp=net_R(o, sel, "pess"),
                          Rg=net_R(o, sel, "gross"), Rno=net_R(o, sel, "norm", "Xno")))
    bi = np.flatnonzero(base_sel)
    B = pd.DataFrame(dict(day=idx[np.minimum(bi + 1, n - 1)], R=net_R(o, base_sel, "norm").astype("float32"),
                          Rg=net_R(o, base_sel, "gross").astype("float32")))
    # kandidati pro portfolio: vsechny platne signaly ve dnech clenstvi (bez busy, to resi portfolio)
    ci = sig_i
    cand = []
    if len(ci):
        Rn = net_R(o, np.isin(np.arange(n), ci), "norm")
        for q, i in enumerate(ci):
            js = o["jstar"][i]
            row = i - path["i0"]
            lo = path["lo"][row, :js + 1].copy()
            cl = path["cl"][row, :js + 1].copy()
            days = idx[i + 1:i + 2 + js]
            if len(days) != js + 1:
                continue
            p = [(days[m], float(lo[m]), float(cl[m])) for m in range(js + 1)]
            Rq = float(Rn[q])
            p[-1] = (p[-1][0], Rq if o["hit"][i] else min(p[-1][1], Rq), Rq)
            cand.append(dict(s="F85", mk=t, t_in=days[0], t_out=days[-1], R=float(Rn[q]), path=p, rsi=float(o["rsi"][i]),
                             notional=float(o["E"][i] / o["risk"][i])))
    return S, B, cand


# ---------------------------------------------------------------- vyhodnoceni
def per_day(T, col):
    return T.groupby("day")[col].mean()


def part(s, a, b):
    return s[(s.index >= a) & (s.index < b)]


def cmp(S, B, a, b, col="R", bcol="R"):
    s, bb = part(per_day(S, col), a, b), part(per_day(B, bcol), a, b)
    if len(s) < 3:
        return dict(n=len(s), sig=np.nan, base=np.nan, diff=np.nan, t=np.nan, win=np.nan, trades=0)
    diff, t = F.welch(s, bb)
    nt = ((S.day >= a) & (S.day < b)).sum()
    return dict(n=len(s), sig=s.mean(), base=bb.mean(), diff=diff, t=t, win=(s > 0).mean(), trades=int(nt))


def fmt(r):
    return (f"obchodů {r['trades']}, dní vstupu {r['n']} | signál {r['sig']:+.3f} R (výhra dnů {r['win']:.0%}) | srovnání {r['base']:+.3f} "
            f"| převis {r['diff']:+.3f}, t {r['t']:.2f}")


def portfolio(cands):
    """Nejvys MAX_POS akciovych pozic najednou, pri vic signalech prednost nejnizsi RSI(2)."""
    by = {}
    for c in cands:
        by.setdefault(c["t_in"], []).append(c)
    chosen, open_ = [], []
    for day in sorted(by):
        open_ = [p for p in open_ if p["t_out"] >= day]
        held = {p["mk"] for p in open_}
        for c in sorted(by[day], key=lambda x: (x["rsi"], x["mk"])):
            if len(open_) >= MAX_POS:
                break
            if c["mk"] in held:
                continue
            open_.append(c)
            held.add(c["mk"])
            chosen.append(c)
    return chosen


def main():
    us = pd.read_pickle(os.path.join(RD, "yahoo_us.pkl"))
    eu = pd.read_pickle(os.path.join(RD, "yahoo_eu.pkl"))
    iv, mdates, msets = membership()
    say("F85 RSI(2) na akciích — pravidlo F42 beze změny, členové S&P 500 k danému dni, Yahoo denní (upraveno o splity a dividendy)")
    say("Náklady: půl spreadu 0,05 % + provize 0,004 % na stranu, financování 12 % ročně za noc; pesimisticky 0,10 % a 15 %. R = výsledek / 3 ATR.")
    say("=" * 110)
    # pokryti dat
    rng = {t: (d.index.min(), d.index.max()) for t, d in us.items()}
    say("Pokrytí: podíl členů indexu, které mají data z Yahoo (k 1. obchodnímu dni roku):")
    cov = []
    for y in range(1996, 2027):
        j = max([q for q, dt in enumerate(mdates) if dt <= pd.Timestamp(f"{y}-01-15")] or [0])
        mem = msets[j]
        dt = pd.Timestamp(f"{y}-01-15")
        have = sum(1 for t in mem if t in rng and rng[t][0] <= dt <= rng[t][1])
        cov.append(f"{y}:{have / len(mem):.0%}")
    say("   " + "  ".join(cov))
    say(f"   tickerů ve složení od 1996: {len(iv)}, s daty z Yahoo: {sum(1 for t in iv if t in us)}")

    Ss, Bs, C = [], [], []
    for t, raw in us.items():
        if t not in iv:
            continue
        d = clean(raw)
        if len(d) < 260:
            continue
        m = member_mask(d.index, iv[t])
        if not m.any():
            continue
        S, B, cand = stock_rows(t, d, m)
        Ss.append(S)
        Bs.append(B)
        C += cand
    S, B = pd.concat(Ss, ignore_index=True), pd.concat(Bs, ignore_index=True)
    say(f"\nObchodů signálu {len(S)} na {S.t.nunique()} titulech, srovnávacích vstupů {len(B)}.")
    ext = S.sort_values("R")
    say("Nejhorší 5 obchodů (kontrola chyb v datech): " + ", ".join(f"{r.t} {r.day.date()} {r.R:+.2f}" for r in ext.head(5).itertuples()))
    say("Nejlepší 5 obchodů: " + ", ".join(f"{r.t} {r.day.date()} {r.R:+.2f}" for r in ext.tail(5).itertuples()))

    say("\nRYCHLÉ SÍTO (vývoj bez nákladů):")
    g = cmp(S, B, *DEV, col="Rg", bcol="Rg")
    say("   " + fmt(g))
    if not g["diff"] > 0:
        say("   => převis bez nákladů ≤ 0 → NE, dál se nepočítá.")
        open(os.path.join(RD, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
        return

    dev, ctl = cmp(S, B, *DEV), cmp(S, B, *CTL)
    say("\nVÝVOJ 1996–2018:   " + fmt(dev))
    say("KONTROLA 2019–2026: " + fmt(ctl))
    pd_, pc_ = cmp(S, B, *DEV, col="Rp"), cmp(S, B, *CTL, col="Rp")
    say(f"Pesimistické náklady: vývoj signál {pd_['sig']:+.3f} R, kontrola {pc_['sig']:+.3f} R")

    # Evropa (FTMO), cele obdobi, bez clenstvi
    Se, Be = [], []
    for t, raw in eu.items():
        d = clean(raw)
        if len(d) < 260:
            continue
        s_, b_, _ = stock_rows(t, d, np.ones(len(d), bool))
        Se.append(s_)
        Be.append(b_)
    SE, BE = pd.concat(Se, ignore_index=True), pd.concat(Be, ignore_index=True)
    eur = cmp(SE, BE, "1990-01-01", "2100-01-01")
    say(f"EVROPA (FTMO, {len(eu)} titulů, celé období): " + fmt(eur))

    # po letech
    s_all, b_all = per_day(S, "R"), per_day(B, "R")
    yrs = []
    for y in range(1996, 2027):
        sy, by_ = s_all[s_all.index.year == y], b_all[b_all.index.year == y]
        if len(sy) and len(by_):
            yrs.append((y, sy.mean() - by_.mean()))
    pos = sum(1 for _, v in yrs if v > 0) / len(yrs)
    say(f"Převis po letech: kladný v {sum(1 for _, v in yrs if v > 0)} z {len(yrs)} let ({pos:.0%}). " + " ".join(f"{y}:{v:+.2f}" for y, v in yrs))

    say("\nROZHODNUTÍ podle pravidel zapsaných předem")
    crit = [
        ("1) vývoj: signál > 0, převis > 0, t ≥ 3,0", dev["sig"] > 0 and dev["diff"] > 0 and dev["t"] >= 3.0, f"{dev['sig']:+.3f}, {dev['diff']:+.3f}, t {dev['t']:.2f}"),
        ("2) kontrola: signál > 0, převis > 0, t ≥ 2,0", ctl["sig"] > 0 and ctl["diff"] > 0 and ctl["t"] >= 2.0, f"{ctl['sig']:+.3f}, {ctl['diff']:+.3f}, t {ctl['t']:.2f}"),
        ("3) pesimistické náklady: signál > 0 ve vývoji i kontrole", pd_["sig"] > 0 and pc_["sig"] > 0, f"{pd_['sig']:+.3f} / {pc_['sig']:+.3f}"),
        ("4) Evropa FTMO: převis > 0", eur["diff"] > 0, f"{eur['diff']:+.3f}, t {eur['t']:.2f}"),
        ("5) převis kladný aspoň v 60 % let", pos >= 0.60, f"{pos:.0%}"),
    ]
    for nm, ok, v in crit:
        say(f"   {nm}: {'ANO' if ok else 'NE'} ({v})")
    passed = all(c[1] for c in crit)
    say(f"   => {'VÝHODA (prošlo vše)' if passed else 'NEPROŠLO'} — body {sum(c[1] for c in crit)}/5")

    say("\nPOPIS (nerozhoduje)")
    fu = [t for t in FTMO_US if t in us]
    Sf, Bf = [], []
    for t in fu:
        d = clean(us[t])
        if len(d) < 260:
            continue
        s_, b_, _ = stock_rows(t, d, np.ones(len(d), bool))
        Sf.append(s_)
        Bf.append(b_)
    SF, BF = pd.concat(Sf, ignore_index=True), pd.concat(Bf, ignore_index=True)
    say(f"   Akcie USA z nabídky FTMO ({len(fu)} titulů, dnešní seznam) 2019–2026: " + fmt(cmp(SF, BF, *CTL)))
    say(f"   Výstup až na otevření dalšího dne: vývoj {cmp(S, B, *DEV, col='Rno')['sig']:+.3f} R, kontrola {cmp(S, B, *CTL, col='Rno')['sig']:+.3f} R")
    rs = []
    for mk in F.US:
        rs += PM.rsi2_trades(mk)
    rs = [t for t in rs if t["t_in"] >= pd.Timestamp("2003-01-01")]
    m_idx = pd.Series([t["R"] for t in rs], index=pd.DatetimeIndex([t["t_out"] for t in rs]))
    m_idx = m_idx.groupby(m_idx.index.to_period("M")).sum()
    m_stk = s_all.groupby(s_all.index.to_period("M")).sum()
    j = m_idx.index.intersection(m_stk.index)
    say(f"   Korelace měsíčních výsledků s RSI(2) na indexech (2003+): {np.corrcoef(m_idx[j], m_stk[j])[0, 1]:+.2f}")

    say(f"\nMĚŘÍTKO PROP ZKOUŠKY: F33 + RSI(2) + F85 (nejvýš {MAX_POS} akciových pozic, přednost nejnižší RSI(2))")
    ch = portfolio(C)
    ch = [c for c in ch if c["t_in"] >= pd.Timestamp("2003-01-01")]
    say(f"   vybraných obchodů F85 {len(ch)} ({len(ch) / 23.8:.0f} ročně), průměr {np.mean([c['R'] for c in ch]):+.3f} R")
    f3 = PM.f33_trades()
    base = PM.Portfolio(rs + f3)
    new = PM.Portfolio(rs + f3 + ch)
    say("   riziko | ZÁKLAD do 12/24/36 m, propadlo, medián | S F85 do 12/24/36 m, propadlo, medián | mezera > 30 dní")
    res = {}
    for r in PM.RISKS:
        Sb, Sn = PM.simulate(base, r), PM.simulate(new, r)
        res[r] = (Sb, Sn)
        a, b = PM.summarize(Sb), PM.summarize(Sn)
        say(f"   {r:4.2f} % | {a['p12']:4.0%} {a['p24']:4.0%} {a['p36']:4.0%}, {a['fail']:4.0%}, {a['med']:5.1f} "
            f"| {b['p12']:4.0%} {b['p24']:4.0%} {b['p36']:4.0%}, {b['fail']:4.0%}, {b['med']:5.1f} | {b['gap']:4.0%}")
    # pravidlo meritka pri bezpecnem riziku zakladu (1,0 %)
    r0 = 1.0
    Sb, Sn = res[r0]
    okp = []
    for nm, msk in (("2003–14", lambda X: X[X.st < "2015-01-01"]), ("2015–23", lambda X: X[X.st >= "2015-01-01"])):
        a, b = PM.summarize(msk(Sb)), PM.summarize(msk(Sn))
        shorter = (np.isnan(a["med"]) and not np.isnan(b["med"])) or (b["med"] <= 0.8 * a["med"])
        more12 = b["p12"] - a["p12"] >= 0.10
        ok = (shorter or more12) and b["fail"] <= 0.10
        okp.append(ok)
        say(f"   starty {nm} při {r0} %: medián {a['med']:.1f} → {b['med']:.1f} měs., do 12 m {a['p12']:.0%} → {b['p12']:.0%}, "
            f"propadlo {b['fail']:.0%} → {'ANO' if ok else 'NE'}")
    say(f"   => pomáhá prop cíli (pravidlo měřítka): {'ANO' if all(okp) else 'NE'} (platí jen spolu s prověrkou výše)")
    # paka 1:1 (popis)
    nd = {}
    for c in ch:
        for (day, _, _) in c["path"]:
            nd[day] = nd.get(day, 0.0) + c["notional"] * 1.0
    v = np.array(list(nd.values()))
    say(f"   Páka 1:1 při 1 % riziku: objem akcií průměrně {v.mean():.0f} % účtu, nad 100 % ve {(v > 100).mean():.0%} dní, nejvýš {v.max():.0f} %")
    open(os.path.join(RD, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
