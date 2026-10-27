"""
Doplnek k research_f1.py (pruzkumny, NE test): kolik z vysledku sebral spread
a kolik swap. Odpovida na otazku "nemely strategie edge, nebo ji snedly
naklady brokera?". Na rozhodnuti PROSLO/NEPROSLO nema vliv.
"""

import sys

import research_f1 as r
import mt5_connector as mc

sys.stdout.reconfigure(line_buffering=True)

mc.connect()
universe = r.build_universe([s.name for s in mc.mt5.symbols_get()])

VARIANTS = {
    "A_momentum": ["L=60", "L=250"],
    "B_navrat_k_prumeru": ["IBS<0.2 +trend", "RSI2<5"],
    "C_prelom_mesice": ["od -1 do +3", "od -1 do +4"],
    "D_carry": ["cisty", "+trend 60"],
}
print("\nPrumer na obchod v dennich sigmach (u B, C nad driftem; u D na den), t v zavorce")
print("ferovy swap = jen urokovy rozdil (co jedna strana plati, druha dostava), bez prirazky brokera")
COLS = (("hrube", False, None), ("+ spread", True, None), ("+ ferovy swap", True, "fair"), ("+ swap brokera", True, "full"))
print(f"{'':<34}" + "".join(f"{c[0]:>17}" for c in COLS))
for fam, names in VARIANTS.items():
    syms = r.family_symbols(fam, universe)
    lo = fam in r.LONG_ONLY
    for name in names:
        fn = dict(r.FAMILIES[fam])[name]
        for part in ("vyber", "holdout"):
            cells = []
            for _, cost_on, swap in COLS:
                uni = {}
                for s in syms:
                    u = dict(universe[s])
                    if not cost_on:
                        u["cost"] = 0.0
                    if swap is None:
                        u["nights"] = u["nights"] * 0
                    elif swap == "fair":
                        half = (u["sl"] - u["ss"]) / 2
                        u["sl"], u["ss"] = half, -half
                    if lo:
                        u["bench"] = r.drift_per_day(u["d"], u)
                    uni[s] = u
                # carry: trhy vybrane podle puvodniho swapu; znamenko ferove casti je stejne
                res = r.evaluate(fn, syms, uni, lo, per_day=fam == "D_carry")[part]
                cells.append(f"{res['nad_driftem']:+.3f} ({res['t']:+.1f})")
            print(f"{fam[:12] + ' ' + name:<26}{part:<8}" + "".join(f"{c:>17}" for c in cells))
