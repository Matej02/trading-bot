import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from generate_sample_data import generate_synthetic_eurusd_h1
from backtest_engine import run_backtest, summarize
from risk_manager import RiskConfig

print("=" * 60)
print("POZOR: beh na SYNTETICKYCH datech (viz generate_sample_data.py)")
print("Cilem je overit funkcnost kodu, NE zmerit skutecnou edge.")
print("=" * 60)

df = generate_synthetic_eurusd_h1(n_bars=8000)

risk_cfg = RiskConfig(
    starting_balance=100_000.0,
    risk_per_trade_pct=0.5,
    max_daily_loss_pct=4.0,
    max_total_drawdown_pct=8.0,
    profit_target_pct=8.0,
    max_trades_per_day=4,
)

trades, equity_df, rm = run_backtest(df, risk_cfg)
stats = summarize(trades, equity_df, rm, risk_cfg)

print("\nVYSLEDKY BACKTESTU (synteticka data):")
for k, v in stats.items():
    print(f"  {k}: {v}")

# uloz equity krivku jako obrazek
if not equity_df.empty:
    plt.figure(figsize=(10, 5))
    plt.plot(equity_df.index, equity_df["balance"])
    plt.axhline(risk_cfg.starting_balance, color="gray", linestyle="--", linewidth=1)
    plt.title("Equity curve (SYNTETICKA data - jen test mechaniky kodu)")
    plt.xlabel("Cas")
    plt.ylabel("Balance ($)")
    plt.tight_layout()
    plt.savefig("equity_curve_SYNTHETIC.png", dpi=120)
    print("\nEquity curve ulozena: equity_curve_SYNTHETIC.png")

# uloz seznam obchodu
import pandas as pd
if trades:
    trades_df = pd.DataFrame([{
        "entry_time": t.entry_time, "direction": t.direction, "entry": t.entry_price,
        "sl": t.sl, "tp": t.tp, "lots": t.lots, "exit_time": t.exit_time,
        "exit": t.exit_price, "pnl": round(t.pnl, 2), "result": t.result,
    } for t in trades])
    trades_df.to_csv("trades_log_SYNTHETIC.csv", index=False)
    print("Trade log ulozen: trades_log_SYNTHETIC.csv")
