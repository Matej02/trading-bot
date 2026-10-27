"""
F3 - overeny proraz z F2 (proraz_d1) na trzich, na kterych se NEVYBIRAL (2026-10-27).

Otazka: plati proraz s tydennim trendem i mimo 9 trhu z F2, nebo jsme ho na nich jen nasli?
Kdyz plati, pridaji se nove trhy do zivého obchodovani a bot bude mit vic obchodu stejne kvality.

PLAN STANOVENY PREDEM (nemeni se podle vysledku):
  Setup beze zmeny: proraz 20 dennich svicek ve smeru tydenniho trendu (EMA50 + sklon 3 tydny),
  SL 2 ATR(14), TP = 2 x SL, nejdele 48 svicek, vstup na otevreni dalsiho dne.
  Trhy: vsech 40 trhu s podminkami brokera (simulator/lib/broker.json = co umi simulator obchodovat)
  bez 9 trhu z F2 a bez GAUUSD (zlato v gramech = kopie XAUUSD) -> 30 novych trhu.
  Data: denni svicky z MT5, cela historie. Naklady: spread brokera v dane hodine + swapy
  (noci = svicky x 1.4, jako v research_f2_detail.py).
  Predem dane vyrazeni podle NAKLADU (ne podle vysledku): trh, kde je median spreadu > 10 % vzdalenosti SL.
  Hodnoti se SKUPINA najednou (shluky po dnech), jednotlive trhy se nevybiraji.
  PROSLO = cela historie: n >= 300, prumer R > 0, t >= 2.33, PF >= 1.10
           a zaroven obdobi 2024+ (jako holdout v F2): prumer R > 0.
  Pro predstavu (nerozhoduje): do 2023 / 2024+, longy / shorty, kontrolni skupina "kazdy den ve smeru
  trendu" (pridava samotny proraz neco?) a rozpad po trzich.
"""
import json
import os

import numpy as np
import pandas as pd

import research_f2 as f

F2_MARKETS = list(f.BINANCE) + f.MT5_MARKETS
NEW = [m for m in f.broker if m not in F2_MARKETS and m != "GAUUSD"]
K, RRR, MAX_SPREAD_OF_SL = 2.0, 2.0, 0.10
N_MIN, T_MIN, PF_MIN = 300, 2.33, 1.10


def run(mk, every_day=False):
    df = f.load(mk, "1d")
    b = f.broker[mk]
    spread = np.array(b["spreadByHour"])[df.index.hour]  # spread je v cenach brokera = data z MT5
    t = (df.index.astype("int64") // 10**9).values.astype(np.int64)
    o, h, l, c = (df[x].values for x in ("open", "high", "low", "close"))
    a = f.atr(h, l, c)
    trend = f.htf_trend(df, "1D", "1W", 86400)
    if every_day:
        sig = trend.astype(np.int8)
    else:
        raw = f.signals(df, "proraz")
        sig = np.where(raw == trend, raw, 0).astype(np.int8)
    e, d, r, bars = f.simulate(t, o, h, l, c, spread, sig, a, K, RRR, f.MAX_HOLD, 86400 * 4 + 3 * 86400)
    entry = o[e] + d * spread[e] / 2
    dist = K * a[e - 1]
    nights = bars * (1.0 if b["group"] == "CRYPTO" else 1.4)
    swap_r = np.where(d == 1, b["swapLong"], b["swapShort"]) * entry * nights / dist
    cost = float(np.nanmedian(spread[e] / dist)) if len(e) else np.nan
    return pd.DataFrame({"time": df.index[e], "market": mk, "dir": d, "R": r + swap_r, "R_bez": r, "bars": bars}), cost, df


def line(name, x):
    s = f.stats(x)
    return (f"   {name:<30} n={s['n']:>5}  win {s['win']:5.1f} %  prumer {s['meanR']:+.3f} R  t {s['t']:+.2f}  "
            f"PF {s['pf']:.2f}  obchodu/den {s['perDay']:.2f}  drzi {s['bars']:.1f} sv.")


def main():
    parts, ctrl, info = [], [], []
    for mk in NEW:
        try:
            tr, cost, df = run(mk)
        except Exception as e:
            print(f"   {mk:<12} data nejsou ({e})")
            continue
        ok = not (cost > MAX_SPREAD_OF_SL)
        info.append({"market": mk, "od": df.index[0].date(), "svicek": len(df), "spread_z_SL_%": round(100 * cost, 1),
                     "vyrazen_naklady": not ok})
        print(f"   {mk:<12} {len(df):>6} dennich svicek od {df.index[0].date()}  spread {100 * cost:5.1f} % SL"
              f"{'  -> VYRAZEN (naklady)' if not ok else ''}")
        if ok:
            parts.append(tr)
            ctrl.append(run(mk, every_day=True)[0])
    tr, ct = pd.concat(parts, ignore_index=True), pd.concat(ctrl, ignore_index=True)
    tr.to_csv(os.path.join(f.DATA, "f3_obchody.csv"), index=False)

    full, h = f.stats(tr), f.stats(tr[tr.time >= f.SPLIT])
    passed = full["n"] >= N_MIN and full["meanR"] > 0 and full["t"] >= T_MIN and full["pf"] >= PF_MIN and h["meanR"] > 0
    print(f"\n=== proraz 1d + tydenni trend, SL 2 ATR, RRR 1:2 na {len(parts)} novych trzich (se swapem) ===")
    print(line("CELA HISTORIE", tr))
    print(line("  bez swapu", tr.assign(R=tr.R_bez)))
    print(line("  do 2023", tr[tr.time < f.SPLIT]))
    print(line("  2024+", tr[tr.time >= f.SPLIT]))
    print(line("  jen longy", tr[tr.dir == 1]))
    print(line("  jen shorty", tr[tr.dir == -1]))
    print(line("KONTROLA kazdy den + trend", ct))
    print(line("  kontrola 2024+", ct[ct.time >= f.SPLIT]))
    print("\nPo trzich (jen pro predstavu, NEVYBIRA SE):")
    for mk, x in tr.groupby("market"):
        print(f"   {mk:<12} n={len(x):>4}  win {100 * (x.R > 0).mean():5.1f} %  prumer {x.R.mean():+.3f} R  "
              f"long/short {int((x.dir == 1).sum())}/{int((x.dir == -1).sum())}")
    print("\nVERDIKT:", "PROSLO - pridat vsechny nevyrazene trhy" if passed else "NEPROSLO - zustava jen 9 trhu z F2")
    json.dump({"proslo": bool(passed), "trhy": [p["market"].iloc[0] for p in parts],
               "vyrazene": [i["market"] for i in info if i["vyrazen_naklady"]],
               "cela": {k: float(v) for k, v in full.items()}, "od2024": {k: float(v) for k, v in h.items()}},
              open(os.path.join(f.DATA, "f3_verdikt.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
