"""F7: vizualni kontrola detekci (krok 1 dokumentu) - SFP na poolu, MSS s displacementem, FVG, vstup, SL, TP."""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f7 as R

mk = sys.argv[1] if len(sys.argv) > 1 else "BTCUSD"
B = L.prepare(mk)
PL = R.build_pools(B)
T = B["T"]["M1"]
su = R.setups_s1(B, PL, 0.0, False, False, 20)
rng = np.random.default_rng(3)
ex = []
for s in su:
    i = s["i"]
    k0 = T["ix"][i] + 1
    r = L.find_mss(T["o"], T["h"], T["l"], T["c"], T["a"], T["rv"], T["ph"], T["pl"], T["N"], k0, s["K"], s["d"], s["ext"],
                   T["ix"][s["ext_i"]], s["cancel"], 1.0)
    if r[0] >= 0:
        ex.append((s, r))
pick = [ex[j] for j in sorted(rng.choice(len(ex), size=min(6, len(ex)), replace=False))]
fig, axs = plt.subplots(2, 3, figsize=(18, 9))
for ax, (s, (k, dec, fj, Ld, ext, ob)) in zip(axs.flat, pick):
    d = s["d"]
    a0, a1 = max(T["ix"][s["ext_i"]] - 40, 0), min(dec + 60, len(T["c"]) - 1)
    x = np.arange(a0, a1 + 1)
    o, h, l, c = (T[q][a0:a1 + 1] for q in ("o", "h", "l", "c"))
    col = np.where(c >= o, "#2a9d8f", "#e76f51")
    ax.vlines(x, l, h, color=col, lw=0.8)
    ax.vlines(x, np.minimum(o, c), np.maximum(o, c), color=col, lw=3)
    lo, hi = (T["h"][fj - 2], T["l"][fj]) if d == 1 else (T["h"][fj], T["l"][fj - 2])
    A = T["a"][dec]
    E = (lo + hi) / 2
    SL = ext - 0.1 * A if d == 1 else ext + 0.1 * A
    risk = abs(E - SL)
    ax.axhspan(lo, hi, xmin=(fj - 2 - a0) / (a1 - a0), xmax=1, color="#f4a261", alpha=0.3, label="FVG z MSS")
    ax.axhline(E, color="k", lw=1, ls="--", label="vstup CE")
    ax.axhline(SL, color="#e63946", lw=1, label="SL")
    ax.axhline(E + d * 2 * risk, color="#2a9d8f", lw=1, label="TP1 2R")
    lvl = PL["lev"][(np.abs(PL["lev"] - (s["ext"])) < 3 * A) & (PL["cr"] <= s["i"])]
    ax.axvline(T["ix"][s["ext_i"]], color="#6c757d", lw=0.8, ls=":", label="extrem sweepu")
    ax.axvline(k, color="#264653", lw=1.2, ls="-.", label="MSS svicka")
    ax.axvline(T["ix"][s["i"]], color="#9b5de5", lw=0.8, ls=":", label="konec SFP svicky M15")
    t = pd.Timestamp(int(B["t"][T["s"][k]]), unit="s")
    ax.set_title(f"{mk} {'LONG' if d == 1 else 'SHORT'} {t:%Y-%m-%d %H:%M} UTC  (displacement {Ld} sv.)", fontsize=10)
    ax.tick_params(labelsize=7)
axs.flat[0].legend(fontsize=7, loc="best")
fig.suptitle("F7 kontrola detekci: SFP na poolu (M15) -> MSS s displacementem (M1) -> FVG -> limit na CE", fontsize=12)
fig.tight_layout()
p = os.path.join(L.D7, f"f7_kontrola_detekci_{mk}.png")
fig.savefig(p, dpi=110)
print(p, len(ex), "detekci")
