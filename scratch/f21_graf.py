"""Graf F21: kumulativni % za noc (po nakladech) a za denni seanci, prumer SPX + NAS; HistData do 2019-02, pak broker."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

D = r"D:\Trading bot\research_data\f21"
n = pd.concat([pd.read_pickle(os.path.join(D, f"f21_{s}_{m}.pkl")) for s in ("hd_vyvoj", "broker") for m in ("SPX500mini", "NAS100mini")])
n = n.groupby("date").agg(pct=("pct", "mean"), u=("u", "first")).sort_values("u")
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(n.u, n.pct.cumsum(), color="#1f5fbf", lw=1.5, label="noc 16:00 → 9:30 NY, po nákladech (průměr SPX + NAS)")
ax.axvline(pd.Timestamp("2019-02-21", tz="UTC"), color="gray", ls="--", lw=1)
ax.axhline(0, color="black", lw=0.6)
ax.text(pd.Timestamp("2012-01-01", tz="UTC"), ax.get_ylim()[1] * 0.85, "vývoj (HistData)\n+0,016 R/noc, t 2,4", fontsize=9)
ax.text(pd.Timestamp("2019-06-01", tz="UTC"), ax.get_ylim()[1] * 0.85, "kontrola (broker)\n+0,012 R/noc, t 1,5", fontsize=9)
ax.set_title("F21 Noční drift US indexů – součet % za noc (náhodné okno stejné délky vyšlo lépe: +0,036 / +0,023 R)")
ax.set_ylabel("součet % (bez složeného úročení)")
ax.legend(loc="upper left", fontsize=9, bbox_to_anchor=(0, 0.75))
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(sys.argv[1], dpi=110)
print("ok")
