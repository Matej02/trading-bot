"""F42 popisna kontrola: RSI(2) s rannim vstupem/vystupem (07:00 Praha) misto otevreni/zavreni dne - jak bude obchodovat runner (PC v noci vypnute).
Broker H1 2019-2026 (SPX, NAS, US30). Denni svicky = den serveru (UTC) jako MT5 D1."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import f42_rsi2 as F  # noqa: E402

LB, L = F.LB, F.L
out = []
allS, allB = [], []
for mk in F.US:
    h = pd.read_pickle(os.path.join(F.RD, f"{mk}_H1.pkl"))
    h.index = pd.to_datetime(h.index)
    g = h.groupby(h.index.normalize())
    d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()}).dropna()
    d = d[d.index.day_of_week < 5]
    # ranni cena: open svicky 06:00 server (= 07:00 Praha v zime, 08:00 v lete) kazdeho dne
    morn = h[h.index.hour == 6].open
    morn.index = morn.index.normalize()
    b = L.BROKER[mk]
    rel = float(np.median(b["spreadByHour"])) / b.get("priceScale", 1.0) / float(d.close.iloc[-1])
    c = d.close
    s200, s5, rsi = c.rolling(200).mean(), c.rolling(5).mean(), F.rsi_wilder(c)
    pc = c.shift(1)
    A = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs())).rolling(20).mean()
    idx = d.index
    MO = morn.reindex(idx).to_numpy()
    O, Lo, C, S5, AA = d.open.to_numpy(), d.low.to_numpy(), c.to_numpy(), s5.to_numpy(), A.to_numpy()
    up = (c > s200).to_numpy()
    sig = up & (rsi < 10).to_numpy()
    n = len(d)

    def one(i, morning):
        e = i + 1
        if e >= n or not AA[i] > 0:
            return None
        E = MO[e] if morning else O[e]
        if not E > 0:
            return None
        risk = 3 * AA[i]
        stop = E - risk
        X = None
        for k in range(e, min(e + 10, n)):
            if Lo[k] <= stop:
                X = stop
                break
            if C[k] > S5[k] or k == e + 9:
                if morning:
                    if k + 1 >= n or not MO[k + 1] > 0:
                        return None
                    X = MO[k + 1]
                    k = k + 1
                else:
                    X = C[k]
                break
        if X is None:
            return None
        net = (X - E) - rel * (E + X) / 2 + b["swapLong"] * E * F.nights(idx[e], idx[k])
        return k, net / risk

    for morning in (False, True):
        rs, rb, busy = [], [], -1
        for i in range(200, n - 2):
            if idx[i] < F.SPLIT:
                continue
            if up[i]:
                r = one(i, morning)
                if r:
                    rb.append((idx[i + 1], r[1]))
            if sig[i] and i > busy:
                r = one(i, morning)
                if r:
                    rs.append((idx[i + 1], r[1]))
                    busy = r[0]
        tag = "ráno" if morning else "test"
        allS.append(pd.DataFrame(rs, columns=["day", "R"]).assign(v=tag))
        allB.append(pd.DataFrame(rb, columns=["day", "R"]).assign(v=tag))
S, B = pd.concat(allS), pd.concat(allB)
for tag in ("test", "ráno"):
    s = S[S.v == tag].groupby("day").R.mean()
    bb = B[B.v == tag].groupby("day").R.mean()
    diff, t = F.welch(s, bb)
    line = f"{tag:5s} broker 2019-2026: signál {LB.fmt(LB.st(s))} | převis {diff:+.3f}, t {t:+.2f}"
    print(line)
    out.append(line)
open(os.path.join(F.OUT, "ranni_vstup.txt"), "w", encoding="utf-8").write(chr(10).join(out))
