"""
Jen cteni: prehraje kandidaty signalu FM strategii runneru (stejne funkce CAND jako live) na aktualnich datech MT5
a ke kazdemu signalu od OD rekne, jestli runner v tu dobu bezel, co se se signalem stalo a proc.
Live soubory runneru se nemeni: data jdou do scratch/replay_live. Obchody se neposilaji.
Spusteni (MT5 uz musi bezet prihlaseny): python scratch/demo_replay.py [YYYY-MM-DD]
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Trading bot"
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import MetaTrader5 as mt5  # noqa: E402
import pandas as pd  # noqa: E402

import run_fm_demo as R  # noqa: E402

OUT = os.path.join(ROOT, "scratch", "replay_live")
os.makedirs(OUT, exist_ok=True)
R.LIVE_DIR = OUT
R.X.D10 = OUT
OD = datetime.fromisoformat(sys.argv[1] if len(sys.argv) > 1 else "2026-10-27").replace(tzinfo=timezone.utc)
PRG = "Europe/Prague"

if not mt5.initialize():
    sys.exit(f"MT5 nedostupne {mt5.last_error()}")
assert mt5.account_info().trade_mode == 0, "ucet neni demo"

# kdy runner bezel: radky logu (cas Praha); mezera > 20 min = nebezel
runs = []
for ln in open(os.path.join(ROOT, "fm_demo_log.txt"), encoding="utf-8"):
    m = re.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)", ln)
    if m:
        runs.append(pd.Timestamp(m.group(1), tz=PRG).tz_convert("UTC"))
runs = sorted(runs)


def running(ts):
    t = pd.Timestamp(ts, unit="s", tz="UTC")
    before = [x for x in runs if x <= t + pd.Timedelta(minutes=2)]
    after = [x for x in runs if x >= t - pd.Timedelta(minutes=2)]
    return bool(before and after and (after[0] - before[-1]) <= pd.Timedelta(minutes=20))


seen = set(json.load(open(os.path.join(ROOT, "fm_demo_state.json"), encoding="utf-8"))["seen"])
spread_now = {}
rows = []
for name, cfg in R.STRATS.items():
    if cfg.get("custom"):
        continue
    for mk in cfg["markets"]:
        R.clear_caches()
        mt5.symbol_select(mk, True)
        try:
            R.fetch_m1(mk, R.M1_DAYS_F20 if name == "F20_user" else R.M1_DAYS)
            if name == "F15_hve":
                R.fetch_h1(mk)
            cands = R.CAND[name](mk)
        except Exception as e:  # noqa: BLE001
            print(f"{name} {mk}: chyba {e}")
            continue
        si = mt5.symbol_info(mk)
        spread_now[mk] = si.spread * si.point
        for (sig_end, d, sl, tp) in cands:
            if sig_end < OD.timestamp():
                continue
            z = pd.Timestamp(sig_end, unit="s", tz="UTC").tz_convert(PRG)
            rows.append(dict(strat=name, mk=mk, t=z, d="long" if d == 1 else "short", sl=sl, tp=tp, sig_end=sig_end,
                             intraday=cfg["intraday"], key=f"{name}|{mk}|{sig_end}|{d}"))
mt5.shutdown()

T = pd.DataFrame(rows).sort_values("t") if rows else pd.DataFrame()
start_live = pd.Timestamp("2026-11-05 10:35", tz=PRG)
print(f"Signaly FM strategii od {OD:%d.%m.} podle dat MT5 (cas Praha), runner live od {start_live:%d.%m. %H:%M}\n")
for _, r in T.iterrows():
    if r.t < start_live:
        stav = "pred startem dema"
    elif r.key in seen:
        stav = "runner ho videl (viz log)"
    elif not running(r.sig_end):
        stav = "runner nebezel (PC vypnute / noc / vikend)"
    elif r.intraday and r.t.hour + r.t.minute / 60 >= R.INTRADAY_LAST_OPEN_H:
        stav = "po 19:00 se intradenni neotvira"
    else:
        stav = "runner bezel, ale signal NEVIDEL (prozkoumat)"
    print(f"{r.t:%a %d.%m. %H:%M}  {r.strat:10s} {r.mk:11s} {r.d:5s}  {stav}")
T.to_pickle(os.path.join(OUT, "replay_signaly.pkl"))
