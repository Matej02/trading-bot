"""
F15 - COT data (CFTC Legacy futures-only, research_data/cot/cot_legacy.pkl) pro Hvezdu.
COT index jako na jeho grafech ("COT index 26 20 80", obr 118-121): (net - min) / (max - min) * 100 za poslednich 26 tydnu,
extremy >= 80 / <= 20. Skupiny: commercials (hedgeri), non-commercials (fondy), nonreportables (retail).
Report je k uterku a vychazi v patek 15:30 ET -> pouzitelny od soboty 00:00 UTC (date + 4 dny), zadny pohled do budoucnosti.
Paru s USD jako zakladni menou (USDJPY, USDCAD, USDCHF) se znamenko otaci (futures jsou kotovane v USD).
"""
import os

import numpy as np
import pandas as pd

COT_FILE = os.path.join(r"D:\Trading bot", "research_data", "cot", "cot_legacy.pkl")
CODES = {"EURUSD": ("099741", 1), "GBPUSD": ("096742", 1), "USDJPY": ("097741", -1), "AUDUSD": ("232741", 1),
         "USDCAD": ("090741", -1), "USDCHF": ("092741", -1), "NZDUSD": ("112741", 1), "XAUUSD": ("088691", 1),
         "XAGUSD": ("084691", 1), "CRUDE_OIL": ("067651", 1), "NAS100mini": ("209742", 1), "SPX500mini": ("13874A", 1),
         "US30mini": ("124603", 1)}
_T = None


def table():
    global _T
    if _T is None:
        _T = pd.read_pickle(COT_FILE)
    return _T


def cot_index(x, n):
    lo = x.rolling(n, min_periods=n).min()
    hi = x.rolling(n, min_periods=n).max()
    return ((x - lo) / (hi - lo).replace(0, np.nan) * 100).to_numpy()


def series(mk, n=26):
    """Tydenni rada pro trh: t_avail (unix s), comm/nc/nr = COT index ve smeru paru (100 = byci pro par)."""
    code, sgn = CODES[mk]
    d = table()
    d = d[d.code == code].drop_duplicates("date").sort_values("date")
    out = pd.DataFrame({"date": d.date.to_numpy()})
    for k, (a, b) in {"comm": ("c_l", "c_s"), "nc": ("nc_l", "nc_s"), "nr": ("nr_l", "nr_s")}.items():
        net = (d[a] - d[b]).astype(float).reset_index(drop=True) * sgn
        out[k] = cot_index(net, n)
    out["t_avail"] = (pd.to_datetime(out.date) + pd.Timedelta(days=4)).astype("datetime64[s]").astype("int64")
    return out


def at(S, t):
    """Index posledniho reportu dostupneho v case t (unix s), nebo -1."""
    return int(np.searchsorted(S.t_avail.to_numpy(), t, side="right")) - 1
