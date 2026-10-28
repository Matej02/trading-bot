"""Prida do research_f6.py moznost obchodovat na zavreni (CFD po zavreni burzy) - vychozi chovani se nemeni."""
import os

os.chdir(r"D:\Trading bot")
p = "research_f6.py"
s = open(p, encoding="utf-8").read()

s = s.replace("def engine(o, h, l, c, a, sig, exit_mode, xlo, xhi, sma5, ibs, stop_k, trail_k, max_days, spread):",
              "def engine(o, h, l, c, a, sig, exit_mode, xlo, xhi, sma5, ibs, stop_k, trail_k, max_days, spread, at_close=False):", 1)
s = s.replace("def engine_mr3(o, h, l, c, a, sig, lo7, hi7, stop_k, max_days, spread):",
              "def engine_mr3(o, h, l, c, a, sig, lo7, hi7, stop_k, max_days, spread, at_close=False):", 1)
assert s.count("        e = o[j] + d * hs") == 2
s = s.replace("        e = o[j] + d * hs", "        e = (c[i] if at_close else o[j]) + d * hs")
# prvni den: pri vstupu na zavreni muze otevreni dalsiho dne prestrelit stop (gap)
s = s.replace("ex = min(o[m], stop) if m > j else stop", "ex = min(o[m], stop) if (m > j or at_close) else stop")
s = s.replace("ex = max(o[m], stop) if m > j else stop", "ex = max(o[m], stop) if (m > j or at_close) else stop")
s = s.replace("ex = (min(o[m], stop) if m > j else stop) - hs", "ex = (min(o[m], stop) if (m > j or at_close) else stop) - hs")
s = s.replace("ex = (max(o[m], stop) if m > j else stop) + hs", "ex = (max(o[m], stop) if (m > j or at_close) else stop) + hs")
assert s.count("""            if out:
                ex = o[m + 1] - d * hs
                m += 1
                break""") == 2
s = s.replace("""            if out:
                ex = o[m + 1] - d * hs
                m += 1
                break""", """            if out:
                if at_close:  # vystup na zavreni (CFD po zavreni burzy)
                    ex = c[m] - d * hs
                else:
                    ex = o[m + 1] - d * hs
                    m += 1
                break""")
# run(): predat at_close
s = s.replace("def run(sid, mk, df, cost_mult=1.0):", "def run(sid, mk, df, cost_mult=1.0, at_close=False, side=0):", 1)
s = s.replace("ent, ext, r, days, e = engine_mr3(o, h, l, c, a, sig, lo7, hi7, p[\"stop_k\"], p[\"max_days\"], sp)",
              "ent, ext, r, days, e = engine_mr3(o, h, l, c, a, sig, lo7, hi7, p[\"stop_k\"], p[\"max_days\"], sp, at_close)", 1)
s = s.replace("""                                      p["max_days"], sp)""", """                                      p["max_days"], sp, at_close)""", 1)
# side: 1 = jen long, -1 = jen short (signal druhe strany se zahodi pred simulaci)
s = s.replace("""    a = atr(h, l, c, 20)
    sp = spread_yahoo(mk) * cost_mult""", """    a = atr(h, l, c, 20)
    if side:
        sig = np.where(sig == side, sig, 0)
    sp = spread_yahoo(mk) * cost_mult""", 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
