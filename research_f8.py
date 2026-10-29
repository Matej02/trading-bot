"""
F8 - strategie z FM PDF (viz F8_PLAN.md a znalosti/FM/).
Test A: S/D zony na vyssich TF (W1/D1/H4) podle pravidel FM (baze 1-6 malych svicek, pohyb ven >= k ATR,
        do 5 svicek BOS, jen prvni dotek, limit na proximal, SL za distal).
Test B: daily bias (Veselovsky, Mucka).
Data MT5 H1 (server = Londyn), z nich H4/D1/W1 (den konci 17:00 NY). Simulace f7_lib.sim_trade na H1 s naklady brokera.
Spusteni: py research_f8.py [A|B|vse]
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L

D8 = os.path.join("research_data", "f8")
os.makedirs(D8, exist_ok=True)
FOREX = ["AUDJPY", "AUDUSD", "CADJPY", "CHFJPY", "EURCAD", "EURJPY", "EURUSD", "GBPJPY", "GBPNZD", "GBPUSD",
         "NZDJPY", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"]
OTHER = ["XAUUSD", "XAGUSD", "SPX500mini", "NAS100mini", "US30mini", "GER_30mini", "GBR_100mini", "FRA_40mini",
         "EUR_50mini", "CRUDE_OIL", "BRENT_OIL"]
MARKETS = FOREX + OTHER
OOS = pd.Timestamp("2020-01-01", tz="UTC").value // 10**9


# ---------------------------------------------------------------- data
def load(mk):
    df = pd.read_pickle(os.path.join("research_data", f"{mk}_H1.pkl"))
    idx = df.index.tz_localize("Europe/London", ambiguous="NaT", nonexistent="shift_forward")
    ok = ~idx.isna()
    df, idx = df[ok], idx[ok]
    t = idx.tz_convert("UTC").as_unit("s").asi8
    ny = idx.tz_convert("America/New_York").tz_localize(None).as_unit("s").asi8
    lt = ny + 7 * 3600
    b = L.BROKER[mk]
    c = df.close.to_numpy(float)
    sbh = np.array(b["spreadByHour"], float) / b.get("priceScale", 1.0)
    lon_h = df.index.hour.to_numpy()
    if b["group"] == "FOREX":
        spr = sbh[lon_h]
    else:
        ref = float(np.median(c[-720:]))
        spr = sbh[lon_h] / ref * c
    tick = 10.0 ** -b["digits"]
    day = lt // 86400
    wd = (day + 3) % 7
    new_day = np.r_[True, day[1:] != day[:-1]]
    cum_sw = np.cumsum(np.where(wd == 3, 3, 1) * new_day).astype(np.float64)
    H = dict(mk=mk, t=t, lt=lt, day=day, o=df.open.to_numpy(float), h=df.high.to_numpy(float),
             l=df.low.to_numpy(float), c=c, spr=spr, tick=tick, cum_sw=cum_sw,
             swl=b["swapLong"], sws=b["swapShort"])
    H["hend"] = np.zeros(len(c), np.bool_)
    return H


def resample(H, key):
    """Svicky vyssiho TF z H1 podle klice (pole stejne delky). Vraci o,h,l,c,start,end (indexy H1)."""
    chg = np.r_[True, key[1:] != key[:-1]]
    st = np.flatnonzero(chg)
    en = np.r_[st[1:] - 1, len(key) - 1]
    o = H["o"][st]
    h = np.maximum.reduceat(H["h"], st)
    l = np.minimum.reduceat(H["l"], st)
    c = H["c"][en]
    return dict(o=o, h=h, l=l, c=c, st=st, en=en, a=L.wilder_atr(h, l, c, 14))


def tfs(H):
    return {"H4": resample(H, H["lt"] // (4 * 3600)), "D1": resample(H, H["day"]),
            "W1": resample(H, (H["day"] + 3) // 7)}


# ---------------------------------------------------------------- zony
def last_swing(h, l, N=3):
    """Pro kazdou svicku i: high/low posledniho potvrzeneho pivotu (potvrzeni N svicek po pivotu)."""
    ph, pl = L.pivots(h, l, N)
    n = len(h)
    sh = np.full(n, np.nan)
    sl = np.full(n, np.nan)
    tr = np.zeros(n, np.int8)  # trend: 2 vyssi high + 2 vyssi low = 1, zrcadlove -1
    hs, ls = [], []
    cur_h = cur_l = np.nan
    for i in range(n):
        p = i - N
        if p >= 0:
            if ph[p]:
                cur_h = h[p]
                hs.append(h[p])
            if pl[p]:
                cur_l = l[p]
                ls.append(l[p])
        sh[i], sl[i] = cur_h, cur_l
        if len(hs) >= 2 and len(ls) >= 2:
            if hs[-1] > hs[-2] and ls[-1] > ls[-2]:
                tr[i] = 1
            elif hs[-1] < hs[-2] and ls[-1] < ls[-2]:
                tr[i] = -1
    return sh, sl, tr


def find_zones(T, k_out, bmax=6, base_body=0.5):
    o, h, l, c, a = T["o"], T["h"], T["l"], T["c"], T["a"]
    n = len(c)
    body = c - o
    sh, sl, tr = last_swing(h, l)
    Z = []
    skip = {1: -1, -1: -1}
    for j in range(20, n - 1):
        aj = a[j - 1]
        if not np.isfinite(aj) or aj <= 0:
            continue
        for d in (1, -1):
            if j <= skip[d] or d * body[j] < 0.5 * aj:
                continue
            s, m = 0.0, 0
            for k in range(j, min(j + 3, n)):
                if d * body[k] <= 0:
                    break
                s += d * body[k]
                m += 1
                if s >= k_out * aj:
                    break
            if s < k_out * aj:
                continue
            b0 = j
            while b0 - 1 >= 0 and j - (b0 - 1) <= bmax and abs(body[b0 - 1]) <= base_body * aj:
                b0 -= 1
            if b0 == j:
                continue
            if d == 1:
                prox = max(o[b0:j].max(), c[b0:j].max())
                dist = l[b0:j + 1].min()
                lvl = sh[b0]
            else:
                prox = min(o[b0:j].min(), c[b0:j].min())
                dist = h[b0:j + 1].max()
                lvl = sl[b0]
            hgt = (prox - dist) * d
            if not np.isfinite(lvl) or hgt <= 0 or hgt > 3 * aj:
                continue
            act = -1
            for k in range(j, min(j + 5, n)):
                if (c[k] - lvl) * d > 0:
                    act = k
                    break
            if act < 0:
                continue
            # zona je znama az po dokonceni pohybu ven (j+m-1); drivejsi aktivace = pohled do budoucnosti
            act = max(act, j + m - 1)
            lo = max(0, b0 - 10)
            piv = (l[lo:b0].min() >= dist - 0.25 * hgt) if d == 1 else (h[lo:b0].max() <= dist + 0.25 * hgt)
            inv = n  # prvni close za distal po aktivaci
            for k in range(act + 1, n):
                if (c[k] - dist) * d < 0:
                    inv = k
                    break
            Z.append(dict(d=d, prox=prox, dist=dist, b0=b0, j=j, act=act, inv=inv, piv=bool(piv), tr=int(tr[act]),
                          atr=aj))
            skip[d] = j + m - 1
    return Z


# ---------------------------------------------------------------- obchody
def first_fill(H, i0, i1, d, E, SL, TP):
    """Index H1 vyplneni limitu E (dotek), nebo -1; zruseno pri TP nebo SL pred vyplnenim."""
    h, l, spr, tick = H["h"], H["l"], H["spr"], H["tick"]
    for i in range(i0, min(i1, len(h) - 1) + 1):
        if d == 1:
            if l[i] + spr[i] <= E - tick:
                return i
            if h[i] >= TP:
                return -1
        else:
            if h[i] >= E + tick:
                return i
            if l[i] + spr[i] <= TP:
                return -1
    return -1


def simulate(H, d, E, SL, TP, fi, hold, be):
    n = len(H["c"])
    sw = H["swl"] if d == 1 else H["sws"]
    if be:  # pri +1R presun SL na vstup (mikro podil na tp1 spusti BE v sim_trade)
        tp1, f1, tp2, f2 = E + (E - SL), 1e-9, TP, 1 - 1e-9
    else:
        tp1, f1, tp2, f2 = TP, 1.0, np.nan, np.nan
    r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], fi, fi, 0, d, E, SL, tp1, f1, tp2, f2,
                    np.full(1, np.nan), 0, min(fi + hold, n - 1), np.nan, H["hend"], 0, 0.0, H["cum_sw"], sw)
    return r


def touch_info(H, T, Z):
    """Pro kazdou zonu: index prvniho doteku limitu (proximal) v H1 a max priznivy pohyb pred dotekem."""
    h, l, spr, tick = H["h"], H["l"], H["spr"], H["tick"]
    n = len(h)
    for z in Z:
        z["fi"] = -1
        i0 = T["en"][z["act"]] + 1
        i1 = min(T["en"][min(z["inv"], z["act"] + 120, len(T["en"]) - 1)], n - 2)
        if i0 > i1:
            continue
        d, E = z["d"], z["prox"]
        if d == 1:
            hit = np.flatnonzero(l[i0:i1 + 1] + spr[i0:i1 + 1] <= E - tick)
        else:
            hit = np.flatnonzero(h[i0:i1 + 1] >= E + tick)
        if len(hit) == 0:
            continue
        fi = i0 + hit[0]
        z["fi"] = fi
        if fi == i0:
            z["run"] = 0.0
        else:
            z["run"] = (h[i0:fi].max() - E) if d == 1 else (E - (l[i0:fi] + spr[i0:fi]).min())


def zone_trades(H, T, Z, opp, var, tfname):
    """var: piv, trend, sl20, tp ('2','3','zone'), be. opp = zony stejneho TF pro cil 'zone'."""
    out = []
    hold = {"H4": 10 * 24, "D1": 30 * 24, "W1": 30 * 24}[tfname]
    for z in Z:
        if z["fi"] < 0 or (var["piv"] and not z["piv"]) or (var["trend"] and z["tr"] != z["d"]):
            continue
        d, E, dist = z["d"], z["prox"], z["dist"]
        hgt = (E - dist) * d
        SL = dist - d * (0.2 * hgt if var["sl20"] else 0.0)
        risk = (E - SL) * d
        if var["tp"] == "zone":
            cands = [y["prox"] for y in opp if y["d"] == -d and y["act"] <= z["act"] < y["inv"] and (y["prox"] - E) * d > 0]
            if not cands:
                continue
            tgt = min(cands) if d == 1 else max(cands)
            R = (tgt - E) * d / risk
            if R < 2:
                continue
            R = min(R, 6.0)
        else:
            R = float(var["tp"])
        if z["run"] >= R * risk:  # cil dosazen pred dotekem = limit zrusen
            continue
        TP = E + d * R * risk
        st, Rr, fi2, ex, why, mfe, E2, rk = simulate(H, d, E, SL, TP, z["fi"], hold, var["be"])
        if st == 0:
            continue
        out.append(dict(mk=H["mk"], tf=tfname, d=d, fi=fi2, ex=ex, t=int(H["t"][fi2]), R=Rr, why=why, Rt=R,
                        risk_atr=risk / z["atr"], piv=z["piv"], hold=hold))
    return out


def one_per_dir(tr):
    """Na trh a smer nejvys 1 otevreny obchod (podle casu vyplneni)."""
    tr = sorted(tr, key=lambda x: x["fi"])
    last = {1: -1, -1: -1}
    keep = []
    for x in tr:
        if x["fi"] > last[x["d"]]:
            keep.append(x)
            last[x["d"]] = x["ex"]
    return keep


def variants():
    for piv in (True, False):
        for trend in (True, False):
            for sl20 in (False, True):
                for tp in ("2", "3", "zone"):
                    for be in (False, True):
                        yield dict(piv=piv, trend=trend, sl20=sl20, tp=tp, be=be)


def vname(v, k):
    return f"k{k} {'piv' if v['piv'] else 'vse'} {'tr' if v['trend'] else 'notr'} {'sl20' if v['sl20'] else 'sl0'} tp{v['tp']} {'be' if v['be'] else 'nobe'}"


def test_a():
    rows = []
    for mk in MARKETS:
        H = load(mk)
        T = tfs(H)
        for k in (1.5, 2.0):
            Zs = {tf: find_zones(T[tf], k) for tf in ("H4", "D1", "W1")}
            for tf in ("H4", "D1"):
                touch_info(H, T[tf], Zs[tf])
            # D1 zona v platne W1 zone stejneho typu (casy v H1 indexech)
            W = Zs["W1"]
            dvw = []
            for z in Zs["D1"]:
                ta = T["D1"]["en"][z["act"]]
                lo, hi = sorted((z["prox"], z["dist"]))
                for w in W:
                    if w["d"] != z["d"]:
                        continue
                    wa, wi = T["W1"]["en"][w["act"]], T["W1"]["en"][min(w["inv"], len(T["W1"]["en"]) - 1)]
                    wlo, whi = sorted((w["prox"], w["dist"]))
                    if wa <= ta < wi and lo <= whi and hi >= wlo:
                        dvw.append(z)
                        break
            sets = {"A1 D1": ("D1", Zs["D1"]), "A2 DvW": ("D1", dvw), "A3 H4": ("H4", Zs["H4"])}
            for name, (tf, Z) in sets.items():
                for v in variants():
                    tr = one_per_dir(zone_trades(H, T[tf], Z, Zs[tf], v, tf))
                    for x in tr:
                        x.update(test=name, var=vname(v, k))
                    rows += tr
        print(mk, "hotovo", len(rows), flush=True)
    df = pd.DataFrame(rows)
    df.to_pickle(os.path.join(D8, "f8_A_obchody.pkl"))
    return df


# ---------------------------------------------------------------- test B daily bias
def test_b():
    rows = []
    for mk in MARKETS:
        H = load(mk)
        D = resample(H, H["day"])
        o, h, l, c = D["o"], D["h"], D["l"], D["c"]
        n = len(c)
        for t in range(2, n - 1):
            sig = {}
            # Veselovsky
            if c[t - 1] > h[t - 2]:
                sig["V"] = 1
            elif h[t - 1] > h[t - 2] and c[t - 1] < h[t - 2]:
                sig["V"] = -1
            elif c[t - 1] < l[t - 2]:
                sig["V"] = -1
            elif l[t - 1] < l[t - 2] and c[t - 1] > l[t - 2]:
                sig["V"] = 1
            # Mucka
            if c[t - 1] != o[t - 1]:
                sig["M"] = 1 if c[t - 1] > o[t - 1] else -1
            i0 = D["st"][t]
            hit_up = h[t] > h[t - 1]
            hit_dn = l[t] < l[t - 1]
            base = dict(mk=mk, t=int(H["t"][i0]), hit_up=hit_up, hit_dn=hit_dn)
            for rule, d in sig.items():
                for side in ("rule", "opp"):
                    dd = d if side == "rule" else -d
                    tgt = h[t - 1] if dd == 1 else l[t - 1]
                    SL = l[t - 1] if dd == 1 else h[t - 1]
                    op = o[t]
                    if (tgt - op) * dd <= 0 or (op - SL) * dd <= 0:
                        continue
                    sw = H["swl"] if dd == 1 else H["sws"]
                    r = L.sim_trade(H["o"], H["h"], H["l"], H["c"], H["spr"], H["tick"], i0, i0, 1, dd, op, SL, tgt,
                                    1.0, np.nan, np.nan, np.full(1, np.nan), 0, D["en"][t] + 1, np.nan, H["hend"],
                                    0, 0.0, H["cum_sw"], sw)
                    if r[0] == 0:
                        continue
                    rows.append(dict(base, rule=rule, side=side, d=dd, R=r[1], why=r[4],
                                     hit=hit_up if dd == 1 else hit_dn, Rt=(tgt - op) * dd / ((op - SL) * dd)))
        print(mk, "B hotovo", flush=True)
    df = pd.DataFrame(rows)
    df.to_pickle(os.path.join(D8, "f8_B_obchody.pkl"))
    return df


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "vse"
    if what in ("B", "vse"):
        test_b()
    if what in ("A", "vse"):
        test_a()
