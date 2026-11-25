"""
Meritko prop zkousky (FTMO 2 kroky). Plan predem ve vaultu: Metodika/Strategie vyzkumu a meritko prop zkousky.md.

Pouziti jako modul:
    import prop_meritko as PM
    P = PM.Portfolio([...seznam obchodu s denni cestou...])
    PM.report(P, "nazev")

Spusteni samostatne = vychozi stav (F33 + RSI(2)): python -I prop_meritko.py -> research_data/prop/meritko_zaklad.txt
Obchod = dict(s, mk, t_in, t_out, R, path) kde path = [(den, low_R, close_R), ...] od vstupu po vystup vcetne,
R = vysledek po nakladech v jednotkach rizika (1 = ztrata u stopu), close_R posledniho dne = R.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402

L = F.L
OUT = os.path.join(F.RD, "prop")
os.makedirs(OUT, exist_ok=True)
LINES = []

RISKS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
STARTS = pd.date_range("2003-01-01", "2023-10-01", freq="MS")
CAP_MONTHS = 36
DAY_LIMIT, MAX_LIMIT = 5.0, 10.0          # % pocatecniho kapitalu
TARGETS = (10.0, 5.0)                    # Challenge, Verification
MIN_DAYS = 4
INACTIVE_DAYS = 30


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


# ---------------------------------------------------------------- obchody s denni cestou
def _atr20(d):
    pc = d.close.shift(1)
    tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
    return tr.rolling(20).mean()


def rsi2_trades(mk, d=None, rel=None, swap_long=None, label="RSI2"):
    """RSI(2) podle F42 (Yahoo), stejne jako f52_kombinace.rsi2_trades, navic denni cesta."""
    if d is None:
        d = F.yahoo(mk)
    b = L.BROKER.get(mk, {})
    if rel is None:
        rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    if swap_long is None:
        swap_long = b["swapLong"]
    c = d.close
    s200, s5, rsi = c.rolling(200).mean(), c.rolling(5).mean(), F.rsi_wilder(c)
    A = _atr20(d).to_numpy()
    O, Lo, C, S5 = d.open.to_numpy(), d.low.to_numpy(), c.to_numpy(), s5.to_numpy()
    sig = ((c > s200) & (rsi < 10)).to_numpy()
    idx, n = d.index, len(d)
    rows, busy = [], -1
    for i in range(200, n - 1):
        if not sig[i] or i <= busy or not A[i] > 0:
            continue
        e = i + 1
        E, risk = O[e], 3 * A[i]
        stop, X, k = E - risk, None, None
        path = []
        for k in range(e, min(e + 10, n)):
            if Lo[k] <= stop:
                X = min(stop, O[k]) if k > e else stop
                path.append((idx[k], (X - E) / risk, (X - E) / risk))
                break
            path.append((idx[k], (Lo[k] - E) / risk, (C[k] - E) / risk))
            if C[k] > S5[k] or k == e + 9:
                X = C[k]
                break
        if X is None:
            continue
        net = (X - E) - rel * (E + X) / 2 + swap_long * E * F.nights(idx[e], idx[k])
        R = net / risk
        path[-1] = (path[-1][0], min(path[-1][1], R), R)
        rows.append(dict(s=label, mk=mk, t_in=idx[e], t_out=idx[k], R=R, path=path))
        busy = k
    return rows


def f33_trades():
    """F33 z research_data/f33/f33_yahoo.pkl (R v ATR -> /3), denni cesta z Yahoo dat indexu."""
    T = pd.read_pickle(os.path.join(F.RD, "f33", "f33_yahoo.pkl"))
    rows = []
    cache = {}
    for _, t in T.iterrows():
        mk = t.mk
        if mk not in cache:
            dd = F.yahoo(mk)
            cache[mk] = (dd, _atr20(dd))
        d, A = cache[mk]
        t_in = pd.Timestamp(t.t)
        t_out = t_in + pd.offsets.BMonthEnd(0)
        if t_in not in d.index:
            continue
        i = d.index.get_loc(t_in)
        unit = 3 * A.iloc[i - 1]
        if not unit > 0:
            continue
        E, sgn = d.open.iloc[i], float(t.d)
        R = float(t.R) / 3.0
        seg = d.loc[t_in:t_out]
        path = []
        for day, r in seg.iterrows():
            worst = (r.low - E) / unit if sgn > 0 else (E - r.high) / unit
            path.append((day, worst, sgn * (r.close - E) / unit))
        if not path:
            continue
        path[-1] = (path[-1][0], min(path[-1][1], R), R)
        rows.append(dict(s="F33", mk=mk, t_in=t_in, t_out=path[-1][0], R=R, path=path))
    return rows


# ---------------------------------------------------------------- simulace zkousky
class Portfolio:
    def __init__(self, trades):
        self.trades = trades
        by_day = {}
        for j, t in enumerate(trades):
            last = len(t["path"]) - 1
            for q, (day, lo, cl) in enumerate(t["path"]):
                by_day.setdefault(pd.Timestamp(day), []).append((j, lo, cl, q == 0, q == last))
        self.days = sorted(by_day)
        self.by_day = by_day
        self.day_arr = np.array(self.days, dtype="datetime64[ns]")


def one_challenge(P, risk, start):
    end = start + pd.DateOffset(months=CAP_MONTHS)
    i0 = int(np.searchsorted(P.day_arr, np.datetime64(start)))
    phase, bal, tdays, phase_start = 0, 100.0, 0, start
    open_ids = set()
    last_entry, gap = start, False
    for day in P.days[i0:]:
        if day >= end:
            break
        rows = P.by_day[day]
        mid = bal
        worst, close_open, closed = bal, 0.0, 0.0
        entered = False
        for (j, lo, cl, first, last) in rows:
            if first and day >= phase_start:
                open_ids.add(j)
                entered = True
            if j not in open_ids:
                continue
            worst += lo * risk
            if last:
                closed += cl * risk
                open_ids.discard(j)
            else:
                close_open += cl * risk
        if worst < mid - DAY_LIMIT or worst < 100.0 - MAX_LIMIT:
            return "propadl", (day - start).days / 30.44, gap
        bal += closed
        if entered:
            tdays += 1
            if (day - last_entry).days > INACTIVE_DAYS:
                gap = True
            last_entry = day
        eq = bal + close_open
        if eq >= 100.0 + TARGETS[phase] and tdays >= MIN_DAYS:
            if phase == 1:
                return "prosel", (day - start).days / 30.44, gap
            phase, bal, tdays = 1, 100.0, 0
            open_ids = set()
            phase_start = day + pd.Timedelta(days=1)
    return "vyprselo", np.nan, gap


def simulate(P, risk, starts=STARTS):
    res = [(st,) + one_challenge(P, risk, st) for st in starts]
    return pd.DataFrame(res, columns=["st", "out", "months", "gap"])


def summarize(S):
    n = len(S)
    ok = S[S.out == "prosel"]
    return dict(
        p12=(ok.months <= 12).sum() / n, p24=(ok.months <= 24).sum() / n, p36=len(ok) / n,
        fail=(S.out == "propadl").sum() / n, med=ok.months.median() if len(ok) else np.nan,
        gap=S.gap.mean(), n=n)


def report(P, name):
    say(f"\n=== {name}: {len(P.trades)} obchodů, {P.days[0].date()}–{P.days[-1].date()} ===")
    say("riziko | prošlo do 12 / 24 / 36 m | propadlo | medián měs. | mezera >30 dní bez vstupu | (starty 2003–14 | 2015–23: do 12 m, propadlo, medián)")
    out = {}
    for r in RISKS:
        S = simulate(P, r)
        a = summarize(S)
        e = summarize(S[S.st < "2015-01-01"])
        lt = summarize(S[S.st >= "2015-01-01"])
        out[r] = dict(all=a, early=e, late=lt)
        say(f"{r:4.2f} % | {a['p12']:4.0%} / {a['p24']:4.0%} / {a['p36']:4.0%} | {a['fail']:4.0%} | {a['med']:5.1f} | {a['gap']:4.0%} "
            f"| {e['p12']:4.0%}, {e['fail']:4.0%}, {e['med']:5.1f} | {lt['p12']:4.0%}, {lt['fail']:4.0%}, {lt['med']:5.1f}")
    safe = [r for r in RISKS if out[r]["all"]["fail"] <= 0.10]
    if safe:
        r = max(safe)
        a = out[r]["all"]
        say(f"BEZPEČNÉ RIZIKO (propadlo ≤ 10 %): {r} % → do 12 m {a['p12']:.0%}, do 24 m {a['p24']:.0%}, do 36 m {a['p36']:.0%}, "
            f"medián {a['med']:.1f} měs., propadlo {a['fail']:.0%}")
    else:
        say("BEZPEČNÉ RIZIKO: žádné (propadlo > 10 % i při 0,5 %)")
    return out


def main():
    rs = []
    for mk in F.US:
        rs += rsi2_trades(mk)
    rs = [t for t in rs if t["t_in"] >= pd.Timestamp("2003-01-01")]
    f3 = f33_trades()
    say("Měřítko prop zkoušky FTMO 2 kroky (+10 %, pak +5 %; denní −5 % z půlnočního zůstatku; celkově −10 %; ≥ 4 dny se vstupem; bez časového limitu, sledováno 36 měsíců)")
    say("Starty každý měsíc 2003-01 až 2023-10 (250 startů). Equity den po dni, nejhorší equity = všechny otevřené pozice na svém low.")
    say("Data: RSI(2) Yahoo SPX/NAS/US30 podle F42, F33 Yahoo SPX/NAS podle F33. Náklady jako v testech.")
    report(Portfolio(rs), "RSI(2) samotná")
    report(Portfolio(f3), "F33 samotná")
    report(Portfolio(rs + f3), "F33 + RSI(2) (dnešní ověřené portfolio)")
    open(os.path.join(OUT, "meritko_zaklad.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))


if __name__ == "__main__":
    main()
