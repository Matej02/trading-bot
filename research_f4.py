"""
F4 - denni signal ve smeru tydenniho trendu, ale VSTUP AZ NA MENSIM TIMEFRAMU (2026-10-28).

Otazka uzivatele: smer z tydne, signal z denni svicky a nacasovani vstupu na 1h / 15m - zlepsi to
uspesnost nebo vysledek proti F2 (vstup hned na otevreni dalsiho dne)?

PLAN STANOVENY PREDEM (nemeni se podle vysledku):
  Denni signal = proraz_d1 z F2 beze zmeny: denni zavreni nad 20dennim max / pod min, tydenni trend
  (EMA50 tydnu + sklon 3 tydny) stejnym smerem. Trhy: 9 trhu z F2. Denni svicky MT5 / Binance.
  Po signalu se ceka nejdele 5 dni (okno) na vstup na mensim timeframu, jinak se obchod nebere:
    A  zaklad (F2): vstup na prvni svicce po zavreni dne, SL 2 ATR(14) denni, TP 2R
    B  retest: limit na prorazene urovni (20denni max/min), SL 1 ATR denni od urovne, TP 2R
    C1 pullback 1h: svicka 1h se dotkne EMA20(1h) a zavre zpet ve smeru signalu -> vstup na otevreni
       dalsi; SL za nejnizsim/nejvyssim bodem poslednich 10 svicek 1h, TP 2R
    C15 totez na 15m
  Vsude: SL ma prednost pred TP ve stejne svicce, nejdele 48 dennich svicek (mimo krypto x 1.4 kalendarne),
  spread brokera v dane hodine (long za ask, ven za bid), swapy podle dni drzeni, jedna pozice na trh
  a variantu najednou. Pri vstupu limitem (B) se v teze svicce kontroluje jen SL (opatrne).
  Data 1h: forex/zlato od 2009-10, krypto/indexy od 2019. Data 15m: MT5 jen od 2021-22 -> C15 ma kratky vyber.
  Vyber: obchody do 2023-12-31; z B, C1, C15 s n >= 60 a prumerem > 0 se vybere JEDNA s nejvyssim t.
  Holdout 2024+: PROSLO = n >= 60, prumer R (se swapy) > 0, t >= 2.0, PF >= 1.10.
  LEPSI NEZ F2 = navic prumer R v holdoutu vyssi nez varianta A ve stejnem obdobi.
  Uspesnost se uvadi u vseho (cil uzivatele), rozhoduje ale prumer R (pri 1:2 je zlom kolem 33 %).
"""
import os

import numpy as np
import pandas as pd
from numba import njit

import research_f2 as f

WINDOW_D = 5
MAX_HOLD_D = 48
K_A, K_B, RRR = 2.0, 1.0, 2.0
N_MIN, T_MIN, PF_MIN = 60, 2.0, 1.10


def secs(idx):
    """Unixove sekundy z indexu bez ohledu na jednotku (data jsou ulozena v mikrosekundach)."""
    return idx.as_unit("s").asi8.astype(np.int64)


def load(mk, tf):
    """Ulozena data z F2 (bez ohledu na stari); kdyz nejsou, stahne je research_f2."""
    name = f"binance_{f.BINANCE[mk]}_{tf}.pkl" if mk in f.BINANCE else f"mt5_{mk}_{tf}.pkl"
    path = os.path.join(f.DATA, name)
    return pd.read_pickle(path) if os.path.exists(path) else f.load(mk, tf)


@njit(cache=True)
def run_trade(t, o, h, l, c, spread, m, d, entry, sl, tp, end_t, intrabar):
    """Od svicky m (vstup v ni) do SL / TP / konce drzeni. Vraci (vystupni cena, index vystupu)."""
    n = len(c)
    first = True
    while True:
        hs = spread[m] / 2
        if d == 1:
            if not first and o[m] - hs <= sl:
                return o[m] - hs, m
            if l[m] - hs <= sl:
                return sl, m
            if not (first and intrabar) and h[m] - hs >= tp:
                return tp, m
        else:
            if not first and o[m] + hs >= sl:
                return o[m] + hs, m
            if h[m] + hs >= sl:
                return sl, m
            if not (first and intrabar) and l[m] + hs <= tp:
                return tp, m
        if m == n - 1 or t[m + 1] >= end_t:
            return c[m] - d * hs, m
        first = False
        m += 1


@njit(cache=True)
def find_entry(mode, t, o, h, l, c, spread, ema20, j, w_end, d, level, atr_d):
    """Vstup podle varianty. Vraci (index svicky vstupu, cena vstupu, SL, vstup limitem?) nebo index -1."""
    n = len(c)
    if mode == 0:  # A: hned
        e = o[j] + d * spread[j] / 2
        return j, e, e - d * K_A * atr_d, False
    if mode == 1:  # B: retest prorazene urovne
        sl = level - d * K_B * atr_d
        for m in range(j, n):
            if t[m] >= w_end:
                break
            hs = spread[m] / 2
            if d == 1:
                if o[m] + hs <= level:
                    return m, o[m] + hs, sl, False
                if l[m] + hs <= level:
                    return m, level, sl, True
            else:
                if o[m] - hs >= level:
                    return m, o[m] - hs, sl, False
                if h[m] - hs >= level:
                    return m, level, sl, True
        return -1, 0.0, 0.0, False
    # C: pullback k EMA20 mensiho timeframu a zavreni zpet
    for m in range(max(j, 10), n - 1):
        if t[m] >= w_end:
            break
        touch = (l[m] <= ema20[m] and c[m] > ema20[m]) if d == 1 else (h[m] >= ema20[m] and c[m] < ema20[m])
        if not touch:
            continue
        k = m + 1
        hs = spread[k] / 2
        e = o[k] + d * hs
        sl = np.min(l[m - 9:m + 1]) - spread[m] / 2 if d == 1 else np.max(h[m - 9:m + 1]) + spread[m] / 2
        dist = (e - sl) * d
        if dist <= 3 * spread[k]:  # SL uz za vstupem nebo jen o spread dal - nesmysl
            continue
        return k, e, sl, False
    return -1, 0.0, 0.0, False


MODES = {"A zaklad (F2)": (0, "1h"), "B retest urovne": (1, "1h"), "C1 pullback 1h": (2, "1h"), "C15 pullback 15m": (2, "15m")}


def trades(mk, mode, ltf):
    dd = load(mk, "1d")
    lo = load(mk, ltf)
    b = f.broker[mk]
    crypto = b["group"] == "CRYPTO"
    # denni signal presne jako F2
    h_, l_, c_ = (dd[x].values for x in ("high", "low", "close"))
    a = f.atr(h_, l_, c_)
    trend = f.htf_trend(dd, "1D", "1W", 86400)
    raw = f.signals(dd, "proraz")
    sig = np.where(raw == trend, raw, 0)
    hi20 = pd.Series(h_).rolling(20).max().shift(1).values
    lo20 = pd.Series(l_).rolling(20).min().shift(1).values
    # mensi timeframe
    t = secs(lo.index)
    o, h, l, c = (lo[x].values.astype(np.float64) for x in ("open", "high", "low", "close"))
    spread = np.array(b["spreadByHour"], dtype=np.float64)[lo.index.hour]
    ema20 = f.ema(c, 20)
    dt = secs(dd.index)
    hold_s = MAX_HOLD_D * 86400 * (1.0 if crypto else 1.4)
    out, busy_until = [], 0
    for i in np.nonzero(sig)[0]:
        if np.isnan(a[i]) or a[i] <= 0:
            continue
        decision = dt[i] + 86400
        if decision < busy_until or decision < t[0]:
            continue
        j = int(np.searchsorted(t, decision))
        if j >= len(t) - 1 or t[j] - decision > 4 * 86400:  # dira v datech mensiho timeframu
            continue
        d = int(sig[i])
        level = hi20[i] if d == 1 else lo20[i]
        m, entry, sl, intrabar = find_entry(mode, t, o, h, l, c, spread, ema20, j, decision + WINDOW_D * 86400, d, level, a[i])
        if m < 0:
            busy_until = decision + WINDOW_D * 86400
            continue
        dist = (entry - sl) * d
        if dist <= 0:
            continue
        tp = entry + d * RRR * dist
        ex, k = run_trade(t, o, h, l, c, spread, m, d, entry, sl, tp, t[m] + hold_s, intrabar)
        days = max((t[k] - t[m]) / 86400, 1 / 24)
        swap_r = (b["swapLong"] if d == 1 else b["swapShort"]) * entry * days / dist
        r = (ex - entry) * d / dist
        out.append({"time": lo.index[m], "market": mk, "dir": d, "R": r + swap_r, "R_bez": r, "bars": days,
                    "sl_atr": dist / a[i]})
        busy_until = t[k] + 1
    return pd.DataFrame(out)


def line(name, x):
    s = f.stats(x)
    return (f"   {name:<34} n={s['n']:>4}  win {s['win']:5.1f} %  prumer {s['meanR']:+.3f} R  t {s['t']:+.2f}  "
            f"PF {s['pf']:.2f}  drzi {s['bars']:.1f} dne")


def main():
    res = {}
    for name, (mode, ltf) in MODES.items():
        parts = []
        for mk in list(f.BINANCE) + f.MT5_MARKETS:
            try:
                parts.append(trades(mk, mode, ltf))
            except Exception as e:
                print(f"   {name} {mk}: {e}")
        res[name] = pd.concat([p for p in parts if len(p)], ignore_index=True)
    pd.concat([x.assign(varianta=k) for k, x in res.items()]).to_csv(os.path.join(f.DATA, "f4_obchody.csv"), index=False)

    for part, cond in (("VYBER do 2023", lambda x: x.time < f.SPLIT), ("HOLDOUT 2024+", lambda x: x.time >= f.SPLIT)):
        print(f"\n=== {part} (se swapy) ===")
        for name, x in res.items():
            y = x[cond(x)]
            print(line(name, y) + (f"  SL prumer {y.sl_atr.mean():.2f} ATR" if len(y) else ""))

    sel = {k: f.stats(x[x.time < f.SPLIT]) for k, x in res.items() if not k.startswith("A")}
    cand = {k: s for k, s in sel.items() if s["n"] >= N_MIN and s["meanR"] > 0}
    print("\nKandidati ve vyberu (n >= 60, prumer > 0):", ", ".join(f"{k} (t {s['t']:.2f})" for k, s in cand.items()) or "zadny")
    if not cand:
        print("VERDIKT: NEPROSLO - zadna varianta vstupu na mensim timeframu neni ve vyberu kladna; zustava F2 (vstup hned).")
        return
    best = max(cand, key=lambda k: cand[k]["t"])
    h = res[best][res[best].time >= f.SPLIT]
    hs, ha = f.stats(h), f.stats(res["A zaklad (F2)"][res["A zaklad (F2)"].time >= f.SPLIT])
    passed = hs["n"] >= N_MIN and hs["meanR"] > 0 and hs["t"] >= T_MIN and hs["pf"] >= PF_MIN
    print(f"Vybrana: {best}")
    print(line(f"{best} holdout", h))
    print(line("  jen longy", h[h.dir == 1]))
    print(line("  jen shorty", h[h.dir == -1]))
    print(line("  bez swapu", h.assign(R=h.R_bez)))
    print("\nVERDIKT:", "PROSLO" if passed else "NEPROSLO",
          "a je LEPSI NEZ F2" if passed and hs["meanR"] > ha["meanR"] else
          ("ale NENI lepsi nez F2 (vstup hned)" if passed else "- zustava F2 (vstup hned)"))


if __name__ == "__main__":
    main()
