"""Test opravy casu v runneru (2026-11-21) bez MT5: fetch_m1 / fetch_h1 z run_fm_demo.py s umelymi svickami.
Ocekavani: M1 t = surovy cas serveru (UTC) v zime i v lete; H1 po nacteni pres research_f8.load (londynsky index) = skutecne UTC."""
import ast
import os
import sys
import tempfile

import numpy as np
import pandas as pd

ROOT = r"D:\Trading bot"
src = open(os.path.join(ROOT, "run_fm_demo.py"), encoding="utf-8").read()
fns = [n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name in ("fetch_m1", "fetch_h1")]
code = compile(ast.Module(body=fns, type_ignores=[]), "run_fm_demo_fns", "exec")


def rates(start, n, step):
    t = np.arange(n, dtype=np.int64) * step + int(pd.Timestamp(start, tz="UTC").timestamp())
    a = np.zeros(n, dtype=[("time", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"), ("close", "f8"), ("tick_volume", "i8")])
    a["time"], a["open"], a["high"], a["low"], a["close"], a["tick_volume"] = t, 1, 2, 0.5, 1.5, 10
    return a


class FakeMT5:
    TIMEFRAME_M1, TIMEFRAME_H1 = 1, 16385
    def __init__(self, start):
        self.start = start
    def copy_rates_from_pos(self, mk, tf, pos, n):
        return rates(self.start, 6000 if tf == self.TIMEFRAME_M1 else 2500, 60 if tf == self.TIMEFRAME_M1 else 3600)


ok = True
tmp = tempfile.mkdtemp()
sys.path.insert(0, ROOT)
for season, start in (("zima", "2026-01-12 00:00"), ("leto", "2026-07-06 00:00")):
    ns = {"pd": pd, "np": np, "os": os, "LIVE_DIR": tmp, "M1_DAYS": 5, "mt5": FakeMT5(start)}
    exec(code, ns)
    last = ns["fetch_m1"]("TEST", days=5)
    m1 = pd.read_pickle(os.path.join(tmp, "TEST_M1.pkl"))
    raw = rates(start, 6000, 60)["time"][:-1]
    good = np.array_equal(m1.t.to_numpy(), raw) and last == raw[-1]
    print(f"{season}: M1 t = surovy cas UTC: {'ANO' if good else 'NE'} (prvni {pd.Timestamp(m1.t.iloc[0], unit='s')} UTC)")
    ok &= good
    ns["fetch_h1"]("TEST")
    h = pd.read_pickle(os.path.join(tmp, "TEST_H1.pkl"))
    # stejny prevod jako research_f8.load
    idx = h.index.tz_localize("Europe/London", ambiguous="NaT", nonexistent="shift_forward")
    utc = idx[~idx.isna()].tz_convert("UTC").as_unit("s").asi8
    rawh = rates(start, 2500, 3600)["time"][:-1]
    good = set(utc) <= set(rawh) and len(utc) >= len(rawh) - 2
    print(f"{season}: H1 po research_f8.load = surovy cas UTC: {'ANO' if good else 'NE'} ({len(utc)} z {len(rawh)} svicek)")
    ok &= good
print("VYSLEDEK:", "OK" if ok else "CHYBA")
