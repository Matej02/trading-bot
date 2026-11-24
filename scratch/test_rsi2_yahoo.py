"""Test 2026-11-24: RSI2 SMA200 z Yahoo (f2x_live.sma200_yahoo + rsi2_signal(trend=...)).
Simuluje MT5 s dirami (vynechane dny 10/2025-14.2.2026 a 15.6.-14.8.2026) a porovna stare a nove rozhodnuti."""
import sys
from datetime import date
sys.path.insert(0, r"D:\Trading bot")
import f2x_live as FX

def holey(d):
    return date(2025, 10, 1) <= d <= date(2026, 2, 14) or date(2026, 6, 15) <= d <= date(2026, 8, 14)

for mk, tk in FX.RSI2_YAHOO.items():
    y = FX.yahoo_adjclose(tk, rng="2y")
    print(f"{mk} ({tk}): {len(y)} dni Yahoo, {min(y)} .. {max(y)}")
    for day in [date(2026, 11, 17), date(2026, 11, 18), date(2026, 11, 19), date(2026, 11, 20), date(2026, 11, 23)]:
        if day not in y:
            continue
        xs = [d for d in sorted(y) if d <= day and not holey(d)]
        days, closes = xs, [y[d] for d in xs]
        old_ok, old_txt = FX.rsi2_signal(days, closes)
        st, c, s = FX.sma200_yahoo(y, day)
        new_ok, new_txt = FX.rsi2_signal(days, closes, trend=(c, s))
        print(f"  {day}: STARE {'SIGNAL' if old_ok else '-':6s} {old_txt}\n              NOVE  {'SIGNAL' if new_ok else '-':6s} {new_txt}")
# stavy sma200_yahoo
y = FX.yahoo_adjclose("^GSPC", rng="2y")
print("svatek 4.7.2026:", FX.sma200_yahoo(y, date(2026, 7, 3))[0], FX.sma200_yahoo(y, date(2026, 7, 4))[0])
print("budouci den:", FX.sma200_yahoo(y, date(2026, 12, 31))[0])
print("malo dat:", FX.sma200_yahoo({date(2026, 1, 2): 1.0}, date(2026, 1, 2))[0])
