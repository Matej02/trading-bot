"""Graf kumulativniho R: F13 indexy, HistData 2010-2019 (novy vzorek) + broker 2019-2026, a HistData na prekryvu."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

OUT = r"D:\Trading bot\research_data\histdata\out"
DST = sys.argv[1]
NEW_END = pd.Timestamp("2019-02-21")


def load(label):
    d = pd.concat([pd.read_pickle(os.path.join(OUT, f"{label}_{m}.pkl")) for m in ("NAS100mini", "SPX500mini")])
    d["dt"] = pd.to_datetime(d.t, unit="s")
    return d.sort_values("dt")


A, C = load("A_broker"), load("C_hist_jako_broker")
nw = C[C.dt < NEW_END]
both = pd.concat([nw, A[A.dt >= NEW_END]]).sort_values("dt")
fig, ax = plt.subplots(figsize=(12, 5.5))
ax.plot(both.dt, both.R.cumsum(), color="#1f5fbf", lw=1.6, label="HistData do 2019-02 (nový vzorek), pak broker (původní test)")
ov = C[C.dt >= NEW_END]
ax.plot(ov.dt, nw.R.sum() + ov.R.cumsum(), color="#d08020", lw=1.1, alpha=0.8, label="HistData na překryvu 2019–2025 (kontrola zdroje dat)")
ax.axvline(NEW_END, color="gray", ls="--", lw=1)
ax.axvline(pd.Timestamp("2022-01-01"), color="gray", ls=":", lw=1)
ax.axhline(0, color="black", lw=0.6)
ax.text(pd.Timestamp("2013-01-01"), ax.get_ylim()[1] * 0.9, "nový vzorek (nikdy neladěno)\nn 417, −0,11 R", fontsize=9)
ax.text(pd.Timestamp("2019-04-01"), ax.get_ylim()[1] * 0.9, "vývoj\n(broker)", fontsize=9)
ax.text(pd.Timestamp("2022-03-01"), ax.get_ylim()[1] * 0.9, "OOS (broker)\nn 206, +0,25 R", fontsize=9)
ax.set_title("F13 Veselovský na NAS100 + SPX500 (varianta z dema), kumulativní R s náklady")
ax.set_ylabel("součet R")
ax.legend(loc="lower right", fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(DST, dpi=110)
print("ulozeno", DST)
