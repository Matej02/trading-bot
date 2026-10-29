"""
F7b - test samotnych konceptu z dokumentu s velkym vzorkem (ablace, krok 7 dokumentu) (2026-10-28).

Duvod: verna pravidla 6 strategii davaji jen par obchodu za rok (filtry se nasobi), takze se z nich neda nic
overit. Tady se kazdy stavebni kamen testuje zvlast, jednoduchym mechanickym vstupem, na tisicich udalosti.

PLAN STANOVENY PREDEM:
  K1 SFP na poolu likvidity (M15: knot za urovni aspon 0,05 ATR, close zpet, hloubka <= 0,5 ATR) -> obchod
     proti sweepu trhem na otevreni dalsi svicky, SL za extremem sweepu + 0,1 ATR(M15), TP 2R, vystup
     nejpozdeji 16:00 NY (krypto 23:00 UTC). Zvlast pro kazdy druh poolu: PDH/PDL, PWH/PWL, EQH/EQL, Asie,
     Londyn, pdVAH/pdVAL, kompozitni VAH/VAL; varianta jen v killzone.
  K2 VWAP pullback v trendu (idea S4): rezim trend a H4 smer, close M15 nad VWAP, low se dotkne pasma
     VWAP..VWAP+1 sigma poprve od doby, kdy byla cena nad +1 sigma -> long trhem (short zrcadlove), SL 1 ATR(M15),
     TP 2R, vystup 15:30 NY / 22:30 UTC, nejvys 2x denne.
  K3 prurazy z balance (idea S5): balance >= 3 dny, H1 close za high/low balance s RVOL >= 1,5 -> pokracovani
     trhem, SL 1 ATR(H1), TP 2R, nejdele 3 obchodni dny.
  Kazdy koncept: vyvoj do 2025-02 / OOS od 2025-03, po nakladech, a porovnani s nahodnymi vstupy (stejny smer,
  SL v ATR, TP, drzeni a denni doba, nahodny den). Koncept "ma vyhodu" = OOS prumer > 0, o >= 0,1 R lepsi
  nez nahoda, a t >= 2 (vyvoj i OOS stejne znamenko).
"""
import os
import sys
import time

import numpy as np
import pandas as pd

import f7_lib as L
import research_f7 as R

sys.stdout.reconfigure(line_buffering=True)
OUT = L.D7
KIND = {1: "PDH/PDL", 2: "PWH/PWL", 3: "EQH/EQL", 4: "Asie", 5: "Londyn", 6: "pdVAH/VAL", 7: "kompozit VAH/VAL"}


def k1(B, PL, kz):
    M = B["T"]["M15"]
    out = []
    for p in np.flatnonzero(PL["trig"] >= 0):
        m, bsw = PL["trig"][p], PL["sw"][p]
        i = M["e"][m]
        if kz and not R.in_kz(B["nyh"][M["s"][m]]):
            continue
        d = -PL["side"][p]
        ei = R.base_ext(B, M["s"][bsw], i, d)
        ext = B["l"][ei] if d == 1 else B["h"][ei]
        A = M["a"][m]
        out.append(R.S(i, d, ext, ei, 0, 0, L.exit_idx(B, i, 16, utc_hour=23), direct=True, mkt=True,
                       SL=ext - 0.1 * A if d == 1 else ext + 0.1 * A, tp1R=2.0, f1=1.0, tag=KIND[PL["kind"][p]]))
    return out


def k2(B):
    M = B["T"]["M15"]
    e = M["e"]
    vw, sg = B["vw"][e], B["sg"][e]
    reg, h4 = B["regime"][e], B["h4st"][e]
    out = []
    day = M["day"]
    above = below = False
    cnt = {}
    for m in range(1, len(e)):
        if day[m] != day[m - 1]:
            above = below = False
        i = e[m]
        if M["c"][m] > vw[m] + sg[m]:
            above = True
        if M["c"][m] < vw[m] - sg[m]:
            below = True
        if reg[m] != 2 or not B["dok"][i]:
            continue
        A = M["a"][m]
        for d, flag in ((1, above), (-1, below)):
            if not flag or h4[m] != d:
                continue
            touch = (M["l"][m] <= vw[m] + sg[m] and M["c"][m] > vw[m]) if d == 1 else (M["h"][m] >= vw[m] - sg[m] and M["c"][m] < vw[m])
            if not touch or cnt.get((day[m], d), 0) >= 2:
                continue
            cnt[(day[m], d)] = cnt.get((day[m], d), 0) + 1
            if d == 1:
                above = False
            else:
                below = False
            out.append(R.S(i, d, np.nan, i, 0, 0, L.exit_idx(B, i, 15.5, utc_hour=22.5), direct=True, mkt=True,
                           SL=B["c"][i] - d * A, tp1R=2.0, f1=1.0, tag="VWAP pullback"))
    return out


def k3(B):
    D, H1 = B["T"]["D1"], B["T"]["H1"]
    be = D["bal_end"]
    out = []
    for dd in range(25, len(D["s"])):
        if not D["ok"][dd] or not (be[dd - 1] and be[dd - 2] and be[dd - 3]):
            continue
        r = 3
        while r < 10 and be[dd - r - 1]:
            r += 1
        bhi, blo = D["h"][dd - r:dd].max(), D["l"][dd - r:dd].min()
        done = set()
        for j in np.flatnonzero(H1["day"] == D["key"][dd]):
            if j < 1:
                continue
            for d, edge in ((1, bhi), (-1, blo)):
                if d in done or not ((H1["c"][j] - edge) * d > 0 and (H1["c"][j - 1] - edge) * d <= 0):
                    continue
                done.add(d)
                if not H1["rv"][j] >= 1.5:
                    continue
                i = H1["e"][j]
                texit = min(R.friday_close(B, i), int(np.searchsorted(B["day"], B["day"][i] + 3)))
                out.append(R.S(i, d, np.nan, i, 0, 0, texit, direct=True, mkt=True, SL=B["c"][i] - d * H1["a"][j],
                               tp1R=2.0, f1=1.0, tag="balance breakout"))
    return out


def main():
    rows = []
    only = [x for x in sys.argv[1:] if not x.startswith("-")]
    for mk, base in R.MARKETS:
        if only and mk not in only:
            continue
        bases = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--base=")]
        if bases and (base or L.MK[mk]["base"]) not in bases:
            continue
        if not os.path.exists(os.path.join(OUT, f"{mk}_{base or L.MK[mk]['base']}.pkl")):
            continue
        t0 = time.time()
        B = L.prepare(mk, base)
        PL = R.build_pools(B)
        grp = B["cls"] if base is None else f"{B['cls']}@{base}"
        vt = "M15"
        for name, su in (("K1 SFP", k1(B, PL, False)), ("K1 SFP v KZ", k1(B, PL, True)), ("K2", k2(B)), ("K3", k3(B))):
            tr = R.execute(B, su, vt, "mkt")
            trd = pd.DataFrame(tr)
            if not len(trd):
                continue
            trd["vtf"] = vt
            rb = R.random_baseline(B, trd, reps=5)
            rmean = rb.groupby("key").R.mean() if len(rb) else pd.Series(dtype=float)
            trd["rnd"] = trd.index.map(rmean)
            trd["koncept"], trd["mk"], trd["grp"] = name, mk if base is None else f"{mk}@{base}", grp
            rows.append(trd)
        print(f"  {mk}@{base or 'zakl'} hotovo ({time.time() - t0:.0f} s)")
    df = pd.concat(rows, ignore_index=True)
    df["oos"] = df.t >= R.SPLIT_T
    df.to_pickle(os.path.join(OUT, "f7_koncepty.pkl"))
    lines = []

    def out(x=""):
        print(x)
        lines.append(x)

    out("F7b - koncepty z dokumentu s velkym vzorkem (vstup trhem, TP 2R, po nakladech; rnd = nahodne vstupy)")
    for grp in ["KRYPTO", "FOREX", "KOMODITY", "FOREX@M1", "KOMODITY@M1", "FOREX@M5", "KOMODITY@M5"]:
        G = df[df.grp == grp]
        if not len(G):
            continue
        out(f"\n=== {grp} ({', '.join(sorted(G.mk.unique()))})")
        for (kc, tag), g in G.groupby(["koncept", "tag"]):
            dv, oo = g[~g.oos], g[g.oos]
            sd, so = R_st(dv.R), R_st(oo.R)
            edge = so["n"] >= 30 and so["mean"] > 0 and (so["mean"] - oo.rnd.mean()) >= 0.1 and so["t"] >= 2 and sd["mean"] > 0
            out(f"  {kc:12s} {tag:18s} vyvoj n {sd['n']:5d} {sd['mean']:+.3f} R (rnd {dv.rnd.mean():+.3f}) win {sd['win']:4.1f}% | "
                f"OOS n {so['n']:5d} {so['mean']:+.3f} R (rnd {oo.rnd.mean():+.3f}) win {so['win']:4.1f}% t {so['t']:+.2f}"
                f"{'  <- VYHODA' if edge else ''}")
    open(os.path.join(OUT, "f7_koncepty.txt"), "w", encoding="utf-8").write("\n".join(lines))


def R_st(r):
    r = np.asarray(r, float)
    n = len(r)
    if n < 2:
        return dict(n=n, mean=r.mean() if n else np.nan, win=np.nan, t=np.nan)
    return dict(n=n, mean=r.mean(), win=(r > 0).mean() * 100, t=r.mean() / r.std(ddof=1) * np.sqrt(n))


if __name__ == "__main__":
    main()
