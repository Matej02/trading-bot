"""
Spusti backtest na REALNYCH H1 datech (nahrada za run_backtest.py,
ktery bezel jen na syntetickych datech pro overeni mechaniky kodu).

Pouziti:
  # z CSV exportu (MT5 Historical Data Center nebo jiny vendor)
  python run_backtest_real.py --csv cesta/k/datum.csv

  # primo z bezicicho, prihlaseneho MT5 terminalu
  python run_backtest_real.py --mt5 --symbol EURUSD --bars 8000
"""

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from backtest_engine import run_backtest, summarize, PIP_SIZE, PIP_VALUE_PER_LOT
from risk_manager import RiskConfig
from load_csv_history import load_mt5_history_csv
from mt5_connector import MT5ConnectionError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", help="cesta k CSV souboru s H1 historii (MT5 export)")
    parser.add_argument("--mt5", action="store_true", help="stahnout historii primo z bezicicho MT5 terminalu")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--bars", type=int, default=8000)
    args = parser.parse_args()

    if not args.csv and not args.mt5:
        parser.error("zadej --csv <soubor> nebo --mt5")

    if args.mt5:
        import mt5_connector
        mt5_connector.connect()
        try:
            df = mt5_connector.fetch_h1_history(args.symbol, args.bars)
            pip_size, pip_value_per_lot = mt5_connector.get_pip_value_per_lot(args.symbol)
        finally:
            mt5_connector.disconnect()
    else:
        df = load_mt5_history_csv(args.csv)
        pip_size, pip_value_per_lot = PIP_SIZE, PIP_VALUE_PER_LOT
        print(f"POZOR: pip_value_per_lot = pevna konstanta ({pip_value_per_lot} USD/pip/lot) - "
              f"presne jen pro EURUSD na USD uctu se standardnim lotem. Pro presne cislo "
              f"od tveho brokera pouzij --mt5 misto --csv.")

    print(f"Nacteno {len(df)} realnych H1 svicek: {df.index.min()} az {df.index.max()}")

    risk_cfg = RiskConfig(
        starting_balance=100_000.0,
        risk_per_trade_pct=0.5,
        max_daily_loss_pct=4.0,
        max_total_drawdown_pct=8.0,
        profit_target_pct=8.0,
        max_trades_per_day=4,
        loss_cooldown_bars=5,
    )

    trades, equity_df, rm = run_backtest(df, risk_cfg, pip_size=pip_size, pip_value_per_lot=pip_value_per_lot)
    stats = summarize(trades, equity_df, rm, risk_cfg)

    print("\nVYSLEDKY BACKTESTU (REALNA data):")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    if not equity_df.empty:
        plt.figure(figsize=(10, 5))
        plt.plot(equity_df.index, equity_df["balance"])
        plt.axhline(risk_cfg.starting_balance, color="gray", linestyle="--", linewidth=1)
        plt.title("Equity curve (REALNA data)")
        plt.xlabel("Cas")
        plt.ylabel("Balance ($)")
        plt.tight_layout()
        plt.savefig("equity_curve_REAL.png", dpi=120)
        print("\nEquity curve ulozena: equity_curve_REAL.png")

    if trades:
        trades_df = pd.DataFrame([{
            "entry_time": t.entry_time, "direction": t.direction, "entry": t.entry_price,
            "sl": t.sl, "tp": t.tp, "lots": t.lots, "exit_time": t.exit_time,
            "exit": t.exit_price, "pnl": round(t.pnl, 2), "result": t.result,
        } for t in trades])
        trades_df.to_csv("trades_log_REAL.csv", index=False)
        print("Trade log ulozen: trades_log_REAL.csv")
    else:
        print("Zadne obchody - zkontroluj rozsah dat a session filter (13:00-17:00 UTC).")


if __name__ == "__main__":
    try:
        main()
    except MT5ConnectionError as e:
        print(f"\nCHYBA: {e}")
        raise SystemExit(1)
