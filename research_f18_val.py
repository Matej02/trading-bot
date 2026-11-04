"""
F18 - Valchar: PDF + 220 obrazku jako zdroj (F18_PLAN.md). Vychazi z F11 (research_f11_val.py), pridava:
- fundament = momentum skore Trading Analyzer (zmena za 5 dni >= +2 long / <= -2 short) nebo bias skore (>= +5 / <= -5),
  skore z research_data/fm_score (dolarove pary, 2017-2024-10) [PDF TrA Score Momentum, obr 184-200];
- H4 OB uvnitr aktivni D1 zony (find_zones) = "daily zona + 4H level" [obr 211-215];
- volume: POC/HVN impulzu v OB je povinne (uz v F11), likvidita = sweep H4 pivot low nad OB pred dotekem [obr 207-217];
- zadny vstup 2 h pred red news (FOMC/NFP/CPI dny 12:30-14:30 UTC) [PDF News].
Trhy: dolarove pary bez CHF + XAUUSD, NAS100, SPX500 (bez skore). Simulace na M1 s naklady.
"""
import os
import sys

import numpy as np
import pandas as pd

os.chdir(r"D:\Trading bot")
sys.path.insert(0, r"D:\Trading bot")
import f7_lib as L
import research_f8 as F
import research_f10 as X

D11 = os.path.join("research_data", "f18")
os.makedirs(D11, exist_ok=True)
MARKETS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "XAUUSD", "NAS100mini", "SPX500mini"]
SCORED = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"}


def score_series(mk):
    s = pd.read_csv(os.path.join("research_data", "fm_score", f"{mk[:3]}_{mk[3:]}.csv"))
    t = pd.to_datetime(s.timestamp).astype("datetime64[s]").astype("int64").to_numpy() + 86400
    o = np.argsort(t)
    return t[o], s.score.to_numpy(float)[o]


_P = {}


def run_market(mk, var, info=False):
    if mk not in _P:
        _P.clear()
        M0 = X.load1(mk)
        T0 = X.tfs(M0)
        _P[mk] = (M0, T0, F.find_zones(T0["D1"], 1.5), score_series(mk) if mk in SCORED else None)
    M, T, ZD, SC = _P[mk]
    if var.get("score", "0") != "0" and SC is None:
        return []
    H4, H1, D = T["H4"], T["H1"], T["D1"]
    o, h, l, c = H4["o"], H4["h"], H4["l"], H4["c"]
    sh, sl, _ = F.last_swing(h, l, 3)
    ph, pl = L.pivots(h, l, 3)
    _, _, trD = F.last_swing(D["h"], D["l"], 2)
    out, used, busy = [], set(), -1
    for k in range(5, len(c) - 1):
        for d in (1, -1):
            lvl = sh[k] if d == 1 else sl[k]
            if not np.isfinite(lvl) or (c[k] - lvl) * d <= 0 or (c[k - 1] - lvl) * d > 0 or (d, lvl) in used:
                continue
            used.add((d, lvl))
            kd = int(np.searchsorted(D["st"], H4["st"][k], side="right")) - 2
            if kd < 0 or trD[kd] != d:
                continue
            ob = -1
            for j in range(k - 1, max(k - 11, 0), -1):
                if (c[j] - o[j]) * d < 0:
                    ob = j
                    break
            if ob < 0:
                continue
            # OB 1-3 svicky: pridej sousedni male svicky pred OB stejne barvy
            ob0 = ob
            while ob0 - 1 >= 0 and ob - ob0 < 2 and (c[ob0 - 1] - o[ob0 - 1]) * d < 0:
                ob0 -= 1
            if d == 1:
                edge = max(max(o[q], c[q]) for q in range(ob0, ob + 1))
                bot = l[ob0:ob + 1].min()
            else:
                edge = min(min(o[q], c[q]) for q in range(ob0, ob + 1))
                bot = h[ob0:ob + 1].max()
            hgt = abs(edge - bot)
            a4 = H4["a"][k]
            if not a4 > 0 or hgt <= 0:
                continue
            s0, s1 = H4["st"][ob0], H4["en"][k]
            bw = a4 / 20
            lo_p = M["l"][s0:s1 + 1].min()
            nb = int((M["h"][s0:s1 + 1].max() - lo_p) / bw) + 1
            hist = np.zeros(nb)
            mid = 0.5 * (M["h"][s0:s1 + 1] + M["l"][s0:s1 + 1])
            np.add.at(hist, ((mid - lo_p) / bw).astype(int).clip(0, nb - 1), M["v"][s0:s1 + 1])
            poc = lo_p + (hist.argmax() + 0.5) * bw
            if not (min(edge, bot) - 0.25 * hgt <= poc <= max(edge, bot) + 0.25 * hgt):
                continue
            E = edge if var["entry"] != "50" else 0.5 * (edge + bot)
            SL = bot - d * 0.1 * a4
            risk = (E - SL) * d
            i_last = H4["en"][min(k + 60, len(c) - 1)]
            if H4["en"][k] + 1 <= busy:
                continue
            fi = X.m1_first(M, H4["en"][k] + 1, i_last, cond_low=E if d == 1 else None, cond_high=E if d == -1 else None)
            if fi < 0:
                continue
            kdf = int(np.searchsorted(D["st"], fi, side="right")) - 2
            if kdf < 0 or trD[kdf] != d:  # bias D1 musi platit i v den vstupu
                continue
            imp = M["h"][s0:fi].max() if d == 1 else M["l"][s0:fi].min()
            kf = int(np.searchsorted(H4["st"], fi, side="right")) - 1
            if var["liq"]:
                ok = False
                for p in range(k + 1, kf - 2):
                    if d == 1 and pl[p] and l[p] > edge and M["l"][H4["en"][p + 3]:fi + 1].min() < l[p]:
                        ok = True
                        break
                    if d == -1 and ph[p] and h[p] < edge and M["h"][H4["en"][p + 3]:fi + 1].max() > h[p]:
                        ok = True
                        break
                if not ok:
                    continue
            if var.get("dvw", 0):
                ok = False
                for z in ZD:
                    if z["d"] != d:
                        continue
                    za, zi = D["en"][z["act"]], D["en"][min(z["inv"], len(D["en"]) - 1)]
                    zl_, zh_ = sorted((z["prox"], z["dist"]))
                    if za <= fi < zi and min(edge, bot) <= zh_ and max(edge, bot) >= zl_:
                        ok = True
                        break
                if not ok:
                    continue
            if var.get("score", "0") != "0":
                st_, sv_ = SC
                jj = int(np.searchsorted(st_, M["t"][fi], side="right")) - 1
                if jj < 5 or M["t"][fi] - st_[jj] > 5 * 86400:
                    continue
                if var["score"] == "mom" and not ((d == 1 and sv_[jj] - sv_[jj - 5] >= 2) or (d == -1 and sv_[jj] - sv_[jj - 5] <= -2)):
                    continue
                if var["score"] == "bias" and not ((d == 1 and sv_[jj] >= 5) or (d == -1 and sv_[jj] <= -5)):
                    continue
            if (M["t"][fi] // 86400) in X.news_days() and 12.5 <= (M["t"][fi] % 86400) / 3600 < 14.5:
                continue
            atrD = D["a"][max(kd, 0)]
            if var["entry"] == "potvrz":
                q0 = int(np.searchsorted(H1["st"], fi, side="right")) - 1
                qc = -1
                for q in range(q0, min(q0 + 12, len(H1["c"]) - 1)):
                    if (d == 1 and H1["l"][q] <= SL) or (d == -1 and H1["h"][q] >= SL):
                        break
                    if (H1["c"][q] - edge) * d > 0:
                        qc = q
                        break
                if qc < 0:
                    continue
                i0 = H1["en"][qc] + 1
                E0 = M["o"][i0]
                rk = (E0 - SL) * d
                Rt = (imp - E0) * d / rk if rk > 0 else 0
                if Rt < 1.8:
                    continue
                Rt = min(Rt, 3.0)
                s = X.sim(M, d, E0, SL, E0 + d * Rt * rk, i0, i0, 1, i0 + 30 * 1440)
            else:
                Rt = (imp - E) * d / risk if risk > 0 else 0
                if Rt < 1.8:
                    continue
                Rt = min(Rt, 3.0)
                s = X.sim(M, d, E, SL, E + d * Rt * risk, fi, fi, 0, fi + 30 * 1440)
            if s:
                r = X.rec(M, "F18", X.vn(var), d, s, Rt, atrD, "30d")
                r.update(sl_dist=s["risk"], tp_dist=Rt * s["risk"], cz=0.0)
                if info:
                    r.update(E_=s["E"], SL_=SL, TP_=s["E"] + d * Rt * s["risk"], ob0=int(H4["st"][ob0]), ob1=int(H4["en"][ob]),
                             obE=edge, obB=bot, bos=lvl, ibos=int(H4["en"][k]), poc=poc)
                out.append(r)
                busy = s["ex"]
    return out


def chart(mk, tr, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    M = X.load1(mk)
    H1 = X.agg(M, M["lt"] // 3600)
    fig, axs = plt.subplots(3, 3, figsize=(21, 15))
    for ax, x in zip(axs.flat, tr[:9]):
        a = int(np.searchsorted(H1["st"], x["ob0"])) - 40
        e = int(np.searchsorted(H1["st"], x["ex"])) + 20
        a, e = max(a, 0), min(e, len(H1["c"]) - 1)
        for i in range(a, e):
            col = "#26a69a" if H1["c"][i] >= H1["o"][i] else "#ef5350"
            ax.plot([i, i], [H1["l"][i], H1["h"][i]], color=col, lw=0.6)
            ax.add_patch(plt.Rectangle((i - 0.3, min(H1["o"][i], H1["c"][i])), 0.6, abs(H1["c"][i] - H1["o"][i]) + 1e-12, color=col))
        pos = lambda i1: int(np.searchsorted(H1["st"], i1, side="right")) - 1
        ax.add_patch(plt.Rectangle((pos(x["ob0"]), min(x["obE"], x["obB"])), pos(x["fi"]) - pos(x["ob0"]) + 5, abs(x["obE"] - x["obB"]),
                                   color="#2962ff" if x["d"] == 1 else "#ff6d00", alpha=0.25))
        for y, col, lab in ((x["bos"], "gray", "BOS lvl"), (x["E_"], "b", "vstup"), (x["SL_"], "r", "SL"), (x["TP_"], "g", "TP"), (x["poc"], "m", "POC")):
            ax.axhline(y, color=col, lw=0.8, ls="--" if lab in ("BOS lvl", "POC") else "-")
            ax.text(a, y, lab, fontsize=7, color=col)
        for i1, col in ((x["ibos"], "gray"), (x["fi"], "b"), (x["ex"], "k")):
            ax.axvline(pos(i1), color=col, lw=0.8)
        ax.set_title(f"{mk} {pd.to_datetime(x['t'], unit='s'):%Y-%m-%d %H:%M} {'LONG' if x['d'] == 1 else 'SHORT'} R={x['R']:+.2f}", fontsize=10)
    plt.tight_layout()
    plt.savefig(path, dpi=70)
    plt.close()


GRID = [dict(entry=e, liq=lq, dvw=dv, score=sc) for e in ("hrana", "50", "potvrz") for lq in (True, False) for dv in (0, 1)
        for sc in ("0", "mom", "bias")]

if __name__ == "__main__":
    for mk in sys.argv[1:] or MARKETS:
        rows = []
        for var in GRID:
            rows += run_market(mk, var)
        pd.DataFrame(rows).to_pickle(os.path.join(D11, f"f18_{mk}{X.SUF}.pkl"))
        print(mk, len(rows), flush=True)
