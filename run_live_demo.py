"""
Live/demo obchodovani napojene na MT5 terminal. Podporuje portfolio vic
nezavislych systemu (par + strategie) najednou - kazdy sleduje vlastni
pozici podle magic cisla, ale risk management (balance, drawdown, denni
ztrata, cooldown po prohre) je SDILENY za cely ucet, protoze presne tak
to hlida prop firma (limity plati na cely ucet, ne na jednotlivou strategii).

Portfolio (viz README.md, sekce "Vyzkum druhe strategie", pro duvod vyberu):
  - EURUSD + pullback strategie (strategy.py)
  - EURUSD + bbsqueeze strategie (strategy_bbsqueeze.py)
  - AUDJPY + bbsqueeze strategie (strategy_bbsqueeze.py)

POZOR - bezpecne vychozi chovani:
  - Bez --live nic neposila na broker, jen loguje, co by udelal (dry-run).
  - Pokud ucet neni DEMO a das --live, skript se odmitne spustit, dokud
    nepridas i --i-understand-this-is-a-real-account.

Pouziti:
  python run_live_demo.py              # dry-run na demo uctu
  python run_live_demo.py --live       # opravdu posila obchody

Predpoklad: MT5 terminal je nainstalovany, spusteny a rucne prihlaseny
do demo uctu (viz README.md). Ucet musi byt v Hedging rezimu (umoznuje
soubezne pozice ve stejnem symbolu od ruznych systemu) - overeno funkcni
na tomhle demo uctu.
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(line_buffering=True)

import mt5_connector
from risk_manager import RiskConfig, RiskManager
import strategy as strategy_pullback
import strategy_bbsqueeze

STATE_FILE = "challenge_state.json"
LIVE_LOG_FILE = "live_trades_log.csv"

PORTFOLIO = [
    {"symbol": "EURUSD", "strategy": strategy_pullback, "magic": 20260819, "label": "EURUSD-pullback", "risk_pct": 0.17},
    {"symbol": "EURUSD", "strategy": strategy_bbsqueeze, "magic": 20260820, "label": "EURUSD-bbsqueeze", "risk_pct": 0.17},
    {"symbol": "AUDJPY", "strategy": strategy_bbsqueeze, "magic": 20260821, "label": "AUDJPY-bbsqueeze", "risk_pct": 0.17},
]


def load_or_init_challenge_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
        return state["starting_balance"], datetime.fromisoformat(state["challenge_start"])

    balance = mt5_connector.get_account_balance()
    challenge_start = datetime.now(timezone.utc)
    with open(STATE_FILE, "w") as f:
        json.dump({"starting_balance": balance, "challenge_start": challenge_start.isoformat()}, f, indent=2)
    print(f"Novy {STATE_FILE} vytvoren: starting_balance={balance}, challenge_start={challenge_start}")
    return balance, challenge_start


def log_signal(label: str, symbol: str, direction: str, row, sl: float, tp: float, lots: float, live: bool):
    is_new = not os.path.exists(LIVE_LOG_FILE)
    with open(LIVE_LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["time", "system", "symbol", "direction", "entry", "sl", "tp", "lots", "mode"])
        writer.writerow([row.name, label, symbol, direction, row["close"], sl, tp, lots, "LIVE" if live else "DRY_RUN"])


def wait_for_next_bar():
    """Ceka do zacatku dalsi H1 svicky (+ maly buffer), po kratkych
    useccich, aby Ctrl+C zafungoval rychle a ne az za hodinu."""
    now = datetime.now(timezone.utc)
    next_hour = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
    target = next_hour + timedelta(seconds=5)
    print(f"Cekam na dalsi H1 svicku ({target.isoformat()})...")
    while True:
        remaining = (target - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(30, remaining))


def process_system(system: dict, pip_cache: dict, rm: RiskManager, live: bool):
    symbol, strat, magic, label = system["symbol"], system["strategy"], system["magic"], system["label"]

    open_positions = mt5_connector.get_open_positions(symbol, magic=magic)
    if open_positions:
        print(f"  [{label}] pozice uz otevrena, cekam na jeji zavreni.")
        return

    if not rm.can_trade():
        print(f"  [{label}] risk manager nedovoluje dalsi obchod (limit/cooldown).")
        return

    df = mt5_connector.fetch_h1_history(symbol, n_bars=300)
    df = strat.add_indicators(df)
    row, prev_row = df.iloc[-1], df.iloc[-2]
    signal = strat.generate_signal(row, prev_row)
    if signal is None:
        print(f"  [{label}] zadny signal na posledni uzavrene svicce.")
        return

    sl, tp = strat.compute_sl_tp(row["close"], row["atr"], signal)
    sl_dist = abs(row["close"] - sl)
    pip_size, pip_value_per_lot = pip_cache[symbol]
    lots = rm.position_size(sl_dist, pip_value_per_lot, pip_size, risk_pct_override=system.get("risk_pct"))
    if lots <= 0:
        return

    mt5_connector.place_market_order(symbol, signal, lots, sl, tp, comment=label, dry_run=not live, magic=magic)
    log_signal(label, symbol, signal, row, sl, tp, lots, live=live)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="opravdu posilat objednavky (jinak jen dry-run log)")
    parser.add_argument("--i-understand-this-is-a-real-account", action="store_true", dest="confirm_real")
    args = parser.parse_args()

    mt5_connector.connect()

    if args.live and not mt5_connector.is_demo_account() and not args.confirm_real:
        print("STOP: tenhle ucet NENI demo a --live je zapnuty bez potvrzeni.")
        print("Pridej --i-understand-this-is-a-real-account, pokud to opravdu chces.")
        mt5_connector.disconnect()
        return

    starting_balance, challenge_start = load_or_init_challenge_state()
    risk_cfg = RiskConfig(
        starting_balance=starting_balance,
        risk_per_trade_pct=0.17,  # kazdy system v PORTFOLIO ma i tak vlastni risk_pct - tohle je jen fallback
        max_daily_loss_pct=4.0,
        max_total_drawdown_pct=8.0,
        profit_target_pct=8.0,
        max_trades_per_day=8,  # zvyseno z 4 - ted bezi 3 nezavisle systemy najednou
        loss_cooldown_bars=5,
    )
    rm = RiskManager(risk_cfg)

    symbols = sorted({s["symbol"] for s in PORTFOLIO})
    pip_cache = {sym: mt5_connector.get_pip_value_per_lot(sym) for sym in symbols}

    print(f"Live demo runner | portfolio: {', '.join(s['label'] for s in PORTFOLIO)}")
    print(f"mode={'LIVE ORDERS' if args.live else 'DRY RUN'} | starting_balance={starting_balance} | "
          f"challenge_start={challenge_start.isoformat()}")

    try:
        while True:
            balance, peak, day_start_balance, trades_today, cooldown_active = mt5_connector.compute_risk_state_from_history(
                starting_balance, challenge_start, cooldown_bars=risk_cfg.loss_cooldown_bars
            )
            rm.refresh_from_broker(balance, peak, day_start_balance, trades_today, cooldown_active=cooldown_active)

            print(f"\n[{datetime.now(timezone.utc).isoformat()}] balance={balance:.2f} peak={peak:.2f} "
                  f"trades_today={trades_today} cooldown={rm.cooldown_remaining} halted={rm.halted} passed={rm.challenge_passed}")

            if rm.halted:
                print(f"ZASTAVENO: {rm.halt_reason}")
                break
            if rm.challenge_passed:
                print("CHALLENGE SPLNEN.")
                break

            for system in PORTFOLIO:
                process_system(system, pip_cache, rm, live=args.live)

            wait_for_next_bar()
    except KeyboardInterrupt:
        print("\nPreruseno uzivatelem (Ctrl+C).")
    finally:
        mt5_connector.disconnect()


if __name__ == "__main__":
    try:
        main()
    except mt5_connector.MT5ConnectionError as e:
        print(f"\nCHYBA: {e}")
        raise SystemExit(1)
