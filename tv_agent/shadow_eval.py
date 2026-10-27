"""
Stinove vyhodnoceni deniku: jak dopadly PRIJATE vs ZAMITNUTE signaly.

Pro kazdy zaznam se z H1 svicek po case signalu zjisti, co prislo driv,
SL nebo TP (kdyz oboji v jedne svicce, pocita se SL - konzervativne).
Vstupni cena je referencni ask/bid v okamziku rozhodnuti, takze spread
je zapocitany.

PRAVIDLO VYHODNOCENI (stanovene predem, at se neohyba podle vysledku):
  Agenti pomahaji, pokud prumer prijatych minus prumer zamitnutych > 0
  s t > 2, pri alespon 50 uzavrenych signalech v kazde skupine.

Rozpad po jednotlivych agentech (co agent pustil vs co vetoval, bez ohledu
na ostatni) je jen orientacni - u vic agentu najednou se nahodou nejaky
"prokaze" casteji, proto o nich rozhoduje az potvrzeni na novych datech.
"""

import json
import os

import numpy as np
import pandas as pd

import mt5_connector
from tv_agent.pipeline import JOURNAL

MIN_PER_GROUP = 50


def _outcome(rec, bars, pip):
    s = rec["signal"]
    is_long = s["direction"] == "long"
    entry, sl, tp = rec["entry_ref"], s["sl"], s["tp"]
    t_server = (pd.Timestamp(s["time"]).tz_convert("UTC").tz_localize(None)
                + pd.Timedelta(hours=rec.get("server_offset_h", 0)))
    # Svicky jsou surovy bid. Long se zavira na zivem bidu (o pul prirazky niz),
    # short na zivem asku (zivy bid + spread) - bez toho by short vysel o cely spread lip.
    half_markup = rec.get("markup_pips", 0.0) / 2 * pip
    shift = -half_markup if is_long else rec["spread_pips"] * pip - half_markup
    after = bars[bars.index >= t_server]
    for _, b in after.iterrows():
        lo, hi = b["low"] + shift, b["high"] + shift
        hit_sl = lo <= sl if is_long else hi >= sl
        hit_tp = hi >= tp if is_long else lo <= tp
        if hit_sl or hit_tp:
            exit_px = sl if hit_sl else tp
            return ((exit_px - entry) if is_long else (entry - exit_px)) / pip
    return None      # jeste otevrene


def evaluate(path=JOURNAL):
    if not os.path.exists(path):
        print(f"Denik {path} zatim neexistuje.")
        return
    recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    # testovaci signaly ne; momentum nema SL/TP, vyhodnocuje ho tv_agent/momentum.py
    recs = [r for r in recs if "signal" in r and r["signal"]["source"] != "test"
            and not r["signal"]["setup"].startswith("momentum")]
    if not recs:
        print("V deniku nejsou zadne skutecne signaly (testovaci se nepocitaji).")
        return

    cache, rows = {}, []
    for r in recs:
        sym = r["signal"]["symbol"]
        if sym not in cache:
            cache[sym] = (mt5_connector.fetch_h1_history(sym, n_bars=3000),
                          mt5_connector.get_pip_value_per_lot(sym)[0])
        bars, pip = cache[sym]
        row = {"skupina": "prijate" if r["approved"] else "zamitnute",
               "pipu": _outcome(r, bars, pip), "setup": r["signal"]["setup"], "symbol": sym}
        for v in r["verdicts"]:
            row[f"agent_{v['agent']}"] = v["approve"]
        rows.append(row)

    df = pd.DataFrame(rows)
    closed = df.dropna(subset=["pipu"])
    print(f"Signalu v deniku: {len(df)}, uzavrenych: {len(closed)}, otevrenych: {df['pipu'].isna().sum()}\n")

    print("CELKOVE (vsichni agenti dohromady):")
    a = closed[closed.skupina == "prijate"].pipu
    z = closed[closed.skupina == "zamitnute"].pipu
    _print_group("prijate", a)
    _print_group("zamitnute", z)
    if len(a) < MIN_PER_GROUP or len(z) < MIN_PER_GROUP:
        print(f"VERDIKT: malo dat (prijatych {len(a)}, zamitnutych {len(z)}, potreba {MIN_PER_GROUP} v kazde).")
    else:
        diff, t = _welch(a, z)
        print(f"Rozdil prijate - zamitnute: {diff:+.2f} pipu, t = {t:.2f}")
        print("VERDIKT: agenti POMAHAJI" if diff > 0 and t > 2
              else "VERDIKT: agenti NEPROKAZALI prinos - filtruji jako nahoda")

    print("\nPO AGENTECH (orientacne - co agent pustil vs co vetoval):")
    for col in sorted(c for c in closed.columns if c.startswith("agent_")):
        part = closed.dropna(subset=[col])
        ok, veto = part[part[col] == True].pipu, part[part[col] == False].pipu
        line = f"  {col[6:]:<10} pustil n={len(ok):>4} ({ok.mean() if len(ok) else 0:+.2f})  " \
               f"vetoval n={len(veto):>4} ({veto.mean() if len(veto) else 0:+.2f})"
        if len(ok) >= MIN_PER_GROUP and len(veto) >= MIN_PER_GROUP:
            diff, t = _welch(ok, veto)
            line += f"  rozdil {diff:+.2f}, t = {t:.2f}"
        else:
            line += "  malo dat"
        print(line)


def _print_group(name, x):
    if not len(x):
        print(f"  {name:<10} n=   0")
        return
    wins, losses = x[x > 0].sum(), -x[x < 0].sum()
    pf = wins / losses if losses else float("inf")
    print(f"  {name:<10} n={len(x):>4}  prumer {x.mean():+.2f} pipu  "
          f"winrate {(x > 0).mean()*100:5.1f} %  PF {pf:.2f}")


def _welch(a, b):
    diff = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return diff, (diff / se if se else 0.0)
