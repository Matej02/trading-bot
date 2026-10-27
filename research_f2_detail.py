"""
F2 - kontrola dvou setupu, ktere prosly holdoutem (prurazy 1d s tydennim trendem, SL 2 ATR, RRR 1.5 a 2).
Nejde o dalsi hledani, jen o naklady a puvod vysledku:
  1) swapy - obchody se drzi 12-15 dni, v testu se swap nepocital (u momenta prave swap sebral vsechno),
  2) long vs short a jednotlive trhy - nevydelal jen rust trhu 2024-2026 (longy na zlate, indexech, BTC)?
Swap za noc podle brokera (podil ceny); noci ~ svicky x 1.4 (5 svicek = 7 nocni, 3x v den brokera),
u krypta svicky x 1 (obchoduje i o vikendu).
"""
import numpy as np
import pandas as pd

import research_f2 as f

SETUPS = [("proraz", "1d", "trend", 2.0, 1.5), ("proraz", "1d", "trend", 2.0, 2.0)]


def trades_for(fam, tf, filt, k, rrr):
    out = []
    ltf_rule, htf_rule = f.TFS[tf]
    for mk in list(f.BINANCE) + f.MT5_MARKETS:
        df = f.load(mk, tf)
        b = f.broker[mk]
        spread = np.array(b["spreadByHour"])[df.index.hour]
        t = (df.index.astype("int64") // 10**9).values.astype(np.int64)
        o, h, l, c = (df[x].values for x in ("open", "high", "low", "close"))
        a = f.atr(h, l, c)
        trend = f.htf_trend(df, ltf_rule, htf_rule, f.TF_SEC[tf])
        raw = f.signals(df, fam)
        sig = raw if filt == "bez" else np.where(raw == trend, raw, 0).astype(np.int8)
        e, d, r, bars = f.simulate(t, o, h, l, c, spread, sig, a, k, rrr, f.MAX_HOLD, f.TF_SEC[tf] * 4 + 3 * 86400)
        entry = o[e] + d * spread[e] / 2
        dist = k * a[e - 1]
        nights = bars * (1.0 if b["group"] == "CRYPTO" else 1.4)
        frac = np.where(d == 1, b["swapLong"], b["swapShort"])
        swap_r = frac * entry * nights / dist
        out.append(pd.DataFrame({"time": df.index[e], "market": mk, "dir": d, "R": r, "R_swap": r + swap_r, "bars": bars}))
    return pd.concat(out, ignore_index=True)


def line(name, x, col):
    s = f.stats(x.assign(R=x[col]))
    return (f"   {name:<22} n={s['n']:>4}  win {s['win']:5.1f} %  prumer {s['meanR']:+.3f} R  t {s['t']:+.2f}  "
            f"PF {s['pf']:.2f}")


def main():
    for setup in SETUPS:
        tr = trades_for(*setup)
        print(f"\n=== {setup[0]} {setup[1]} filtr {setup[2]}, SL {setup[3]} ATR, RRR 1:{setup[4]} ===")
        for part, x in (("VYBER do 2023", tr[tr.time < f.SPLIT]), ("HOLDOUT 2024+", tr[tr.time >= f.SPLIT])):
            print(f" {part}:")
            print(line("bez swapu", x, "R"))
            print(line("SE SWAPEM", x, "R_swap"))
            print(line("jen longy (se swapem)", x[x.dir == 1], "R_swap"))
            print(line("jen shorty (se swapem)", x[x.dir == -1], "R_swap"))
        h = tr[tr.time >= f.SPLIT]
        print(" HOLDOUT po trzich (se swapem):")
        for mk, x in h.groupby("market"):
            print(f"   {mk:<11} n={len(x):>3}  win {100 * (x.R_swap > 0).mean():5.1f} %  prumer {x.R_swap.mean():+.3f} R  "
                  f"long/short {int((x.dir == 1).sum())}/{int((x.dir == -1).sum())}")


if __name__ == "__main__":
    main()
