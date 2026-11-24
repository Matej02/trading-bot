"""Test 2026-11-24: vetev RSI2 v run_fm_demo.cycle_f2x se SMA200 z Yahoo (bez MT5, funkce vytazene pres ast)."""
import ast, sys, time, types
from datetime import date, datetime, timezone
sys.path.insert(0, r"D:\Trading bot")
import f2x_live as FX
src = open(r"D:\Trading bot\run_fm_demo.py", encoding="utf-8").read()
tree = ast.parse(src)
keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == "cycle_f2x")
        or (isinstance(n, ast.Assign) and any(getattr(t, "id", "") in ("_RSI2_YFAIL", "RSI2_OPEN_H") for t in n.targets))]
logs, opened = [], []
y = FX.yahoo_adjclose("^GSPC", rng="2y")
def d1(mk):  # MT5 s dirami: jen dny mimo diry, do 18. 11.
    xs = [d for d in sorted(y) if d <= SIG and not (date(2025,10,1) <= d <= date(2026,2,14) or date(2026,6,15) <= d <= date(2026,8,14))]
    return xs, [y[d] for d in xs], 50.0
class FakeDT(datetime):
    @classmethod
    def now(cls, tz=None): return NOW
ns = dict(FX=types.SimpleNamespace(**{k: getattr(FX, k) for k in dir(FX) if not k.startswith("__")}), time=time, datetime=FakeDT, timezone=timezone,
          mt5=types.SimpleNamespace(symbol_select=lambda *a: True), STRATS={"RSI2": {"markets": ["SPX500mini"]}, "F33_rebal": {"markets": []}, "F31_fomc": {"markets": []}, "F29_krypto": {"markets": []}},
          prague_hour=lambda ts: (8.0, None), d1_weekdays=d1, log=logs.append,
          f2x_open=lambda state, name, mk, d, live, why, k, atr=None: (opened.append((mk, why)), state["seen"].append(k)))
exec(compile(ast.Module(body=keep, type_ignores=[]), "runner", "exec"), ns)
def run(sig, now, yahoo=None):
    global SIG, NOW
    SIG, NOW = sig, now
    logs.clear(); opened.clear(); ns["_RSI2_YFAIL"].clear()
    if yahoo: ns["FX"].yahoo_adjclose = yahoo
    st = {"seen": []}
    ns["cycle_f2x"](st, False)
    ns["FX"].yahoo_adjclose = FX.yahoo_adjclose
    return st, list(logs), list(opened)
print("18.11 (signal ve starem kodu):", run(date(2026,11,18), datetime(2026,11,19,7,30,tzinfo=timezone.utc)))
def boom(*a, **k): raise OSError("sit nedostupna")
print("Yahoo chyba:", run(date(2026,11,18), datetime(2026,11,19,7,30,tzinfo=timezone.utc), boom))
print("Yahoo bez dne:", run(date(2026,11,18), datetime(2026,11,19,7,30,tzinfo=timezone.utc), lambda *a, **k: {d: v for d, v in y.items() if d < date(2026,11,18)}))
# umely signal: Yahoo nad SMA200 a RSI < 10 (posledni 3 dny prudky pokles, ale nad prumerem)
fake = dict(y); base = date(2026,11,18)
fake = {d: v * 1.3 if d >= date(2026,11,1) else v for d, v in y.items() if d <= base}
fake[date(2026,11,12)], fake[date(2026,11,13)], fake[date(2026,11,16)], fake[date(2026,11,17)], fake[base] = 9800, 9850, 9700, 9600, 9500
y_backup = y
y = fake
print("umely signal:", run(base, datetime(2026,11,19,7,30,tzinfo=timezone.utc), lambda *a, **k: fake))
