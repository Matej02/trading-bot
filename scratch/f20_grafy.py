"""F20 grafy do vaultu: kumulativni R vybrane varianty a rodiny + ukazky obchodu (15m, svicka SFP, zona, POC svicky, SL/TP)."""
import os
import sys

sys.path.insert(0, r"D:\Trading bot")
os.chdir(r"D:\Trading bot")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import research_f10 as X
import research_f20_eval as E
import research_f20_user as U

OUTD = r"D:\Trading bot\znalosti\Přílohy"
G = E.load()
best = E.variant(G, "4H15", "zona", "2", "0", "close", "poc").sort_values("t")
fam = pd.concat([E.variant(G, b, p, v, "0", "close", "poc") for b in ("4H", "4H15") for p in ("zona", "zonapoc")
                 for v in ("0", "2")]).drop_duplicates(["mk", "fi"]).sort_values("t")
fig, ax = plt.subplots(figsize=(11, 4.5))
for df, lab, col in ((best, "vybraná (4H+15m bias, zóna, FRVP 2/3, close, TP nahý POC)", "C0"),
                     (fam, "rodina 8 sousedních variant (unikátní obchody)", "C1")):
    ax.plot(pd.to_datetime(df.t, unit="s"), df.R.cumsum(), label=f"{lab}  n={len(df)}", color=col)
ax.axvline(pd.Timestamp(X.OOS, unit="s"), color="k", ls="--", lw=1)
ax.text(pd.Timestamp(X.OOS, unit="s"), ax.get_ylim()[1] * 0.9, "  OOS 2022+", fontsize=9)
ax.axhline(0, color="grey", lw=0.6)
ax.set_title("F20 obecná strategie uživatele – kumulativní R (s náklady brokera, 7 trhů)")
ax.set_ylabel("R")
ax.legend(fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig(os.path.join(OUTD, "F20 obecná strategie – kumulativní R.png"), dpi=110)

# ukazky obchodu vybrane varianty (OOS)
ex = best[best.oos].head(6)
fig, axs = plt.subplots(2, 3, figsize=(16, 8.5))
cache = {}
for ax, r in zip(axs.flat, ex.itertuples()):
    if r.mk not in cache:
        cache.clear()
        cache[r.mk] = U.candidates(r.mk)
    P, C = cache[r.mk]
    Q, M = P["T"]["M15"], P["M"]
    c = [x for x in C if x["q"] == r.q][0]
    q0, q1 = max(0, r.q - 40), min(len(Q["c"]) - 1, r.q + 40)
    for k in range(q0, q1 + 1):
        col = "tab:green" if Q["c"][k] >= Q["o"][k] else "tab:red"
        ax.plot([k, k], [Q["l"][k], Q["h"][k]], color="k" if k == r.q else col, lw=0.8)
        ax.add_patch(plt.Rectangle((k - 0.35, min(Q["o"][k], Q["c"][k])), 0.7, abs(Q["c"][k] - Q["o"][k]) + 1e-12,
                                   color="k" if k == r.q else col))
    Z = P["S"][U.K]["Z"]
    si = c["si"]
    for z in Z[(Z[:, 0] == c["d"]) & (Z[:, 3] <= si) & (si <= Z[:, 4])]:
        ax.axhspan(z[1], z[2], color="tab:blue", alpha=0.15)
    E_ = r.sl_dist
    fi = int(r.fi)
    Ep = M["o"][fi]
    SL = c["sv"] - c["d"] * 0.1 * c["a15"]
    TP = Ep + c["d"] * r.tp_dist
    ax.axhline(c["lvl"], color="orange", lw=1, ls=":", label="vybraný swing")
    ax.axhline(c["vpoc"], color="purple", lw=1, ls="--", label="POC svíčky SFP")
    ax.axhline(SL, color="red", lw=1, label="SL")
    ax.axhline(TP, color="green", lw=1, label="TP (nahý denní POC)")
    ax.set_title(f"{r.mk} {pd.Timestamp(r.t, unit='s'):%Y-%m-%d %H:%M} UTC {'long' if r.d == 1 else 'short'} | "
                 f"R {r.R:+.2f} | FRVP {c['vp']}/3", fontsize=9)
    ax.set_xticks([])
    ax.legend(fontsize=6, loc="best")
fig.suptitle("F20 – ukázky obchodů vybrané varianty (OOS, 15m; černá = svíčka SFP, modrá = S/D zóna)", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUTD, "F20 obecná strategie – ukázky obchodů (OOS).png"), dpi=100)
print("ok")
