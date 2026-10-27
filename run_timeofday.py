"""
Automaticky runner pro time-of-day strategii.

Bezi sam, kazdou minutu kontroluje, jestli nastal cas na otevreni nebo
zavreni nejake pozice. Zadne indikatory - jen hodiny.

HLAVNI UCEL NENI ZISK, ALE MERENI.
Ke kazdemu obchodu se loguje ocekavana cena vs skutecna, aby se dalo
zjistit, jaky je REALNY naklad na plneni. To je jedina otevrena otazka:
backtest rika, ze edge je +0.64 pipu pri nakladu 1.10. Pokud je skutecny
naklad vyssi, edge neexistuje. Odpoved da az tenhle beh.

Bezpecne vychozi chovani:
  - bez --live nic neposila, jen loguje (a i tak meri skutecne ceny)
  - na jinem nez DEMO uctu se --live odmitne bez extra potvrzeni

Pouziti:
  python run_timeofday.py            # dry-run, meri ceny
  python run_timeofday.py --live     # opravdu obchoduje na demu
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
from strategy_timeofday import SETUPS, validate_setups

STATE_FILE = "tod_state.json"
TRADE_LOG = "tod_trades.csv"
FILL_LOG = "tod_fills.csv"
RISK_PCT_PER_SETUP = 0.10      # velmi konzervativni - jde o mereni, ne o vydelek
ASSUMED_STOP_PIPS = 20.0       # pro vypocet velikosti pozice (strategie nema SL)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    st = {"starting_balance": mt5_connector.get_account_balance(),
          "started": datetime.now(timezone.utc).isoformat(), "opened": {}}
    with open(STATE_FILE, "w") as f:
        json.dump(st, f, indent=2)
    print(f"Novy {STATE_FILE}: starting_balance={st['starting_balance']}")
    return st


def save_state(st):
    with open(STATE_FILE, "w") as f:
        json.dump(st, f, indent=2)


def log_row(path, header, row):
    is_new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(header)
        w.writerow(row)


def pip_of(symbol, pip_cache):
    return pip_cache[symbol][0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--i-understand-this-is-a-real-account", action="store_true", dest="confirm_real")
    args = ap.parse_args()

    problems = validate_setups()
    if problems:
        print("CHYBA v definici setupu:")
        for p in problems:
            print(f"  - {p}")
        return

    mt5_connector.connect()

    if args.live and not mt5_connector.is_demo_account() and not args.confirm_real:
        print("STOP: ucet neni DEMO a --live je zapnuty bez potvrzeni.")
        mt5_connector.disconnect()
        return

    st = load_state()
    pip_cache = {s.symbol: mt5_connector.get_pip_value_per_lot(s.symbol) for s in SETUPS}
    risk_cfg = RiskConfig(starting_balance=st["starting_balance"], risk_per_trade_pct=RISK_PCT_PER_SETUP,
                          max_daily_loss_pct=4.0, max_total_drawdown_pct=8.0,
                          profit_target_pct=100.0, max_trades_per_day=len(SETUPS) * 2,
                          loss_cooldown_bars=0)
    rm = RiskManager(risk_cfg)

    print(f"Time-of-day runner | mode={'LIVE' if args.live else 'DRY RUN'}")
    print(f"Setupy ({len(SETUPS)}):")
    for s in SETUPS:
        print(f"  {s.label}: vstup {s.entry_hour_utc:02d}:00 UTC, drzeni {s.hold_hours}h, "
              f"vystup {s.exit_hour_utc:02d}:00 | ocekavana edge {s.expected_edge_pips} "
              f"pipu, naklad {s.expected_cost_pips}")
    print("Ucel behu: zmerit SKUTECNY naklad na plneni. Viz tod_fills.csv\n")

    try:
        while True:
            now = datetime.now(timezone.utc)

            for s in SETUPS:
                pip_size, pip_val = pip_cache[s.symbol]
                open_pos = mt5_connector.get_open_positions(s.symbol, magic=s.magic)
                key = str(s.magic)

                # --- ZAVIRANI: uplynula doba drzeni? ---
                if open_pos:
                    rec = st["opened"].get(key)
                    if rec:
                        opened_at = datetime.fromisoformat(rec["time"])
                        if now >= opened_at + timedelta(hours=s.hold_hours):
                            pos = open_pos[0]
                            bid, ask, _ = mt5_connector.get_current_prices(s.symbol)
                            expected_exit = bid if s.direction == "long" else ask
                            _, fill = mt5_connector.close_position(pos, dry_run=not args.live)
                            actual = fill if fill else expected_exit
                            slip = abs(actual - expected_exit) / pip_size
                            gross = ((actual - rec["entry_price"]) if s.direction == "long"
                                     else (rec["entry_price"] - actual)) / pip_size
                            print(f"  [{s.label}] ZAVRENO @ {actual:.5f} | hruby vysledek "
                                  f"{gross:+.2f} pipu | skluz {slip:.2f}")
                            log_row(TRADE_LOG,
                                    ["entry_time", "exit_time", "setup", "symbol", "smer", "lots",
                                     "entry_price", "exit_price", "gross_pips", "expected_edge"],
                                    [rec["time"], now.isoformat(), s.label, s.symbol, s.direction,
                                     rec["lots"], rec["entry_price"], actual, round(gross, 2),
                                     s.expected_edge_pips])
                            log_row(FILL_LOG,
                                    ["time", "setup", "faze", "ocekavana_cena", "skutecna_cena",
                                     "skluz_pipu", "spread_pipu"],
                                    [now.isoformat(), s.label, "exit", expected_exit, actual,
                                     round(slip, 2), ""])
                            st["opened"].pop(key, None)
                            save_state(st)
                    continue

                # --- OTEVIRANI: je presne cas vstupu? ---
                if now.hour == s.entry_hour_utc and now.minute < 2 and key not in st["opened"]:
                    if not rm.can_trade():
                        print(f"  [{s.label}] risk manager blokuje vstup.")
                        continue
                    bid, ask, spread_raw = mt5_connector.get_current_prices(s.symbol)
                    expected_entry = ask if s.direction == "long" else bid
                    spread_pips = spread_raw / pip_size
                    lots = rm.position_size(ASSUMED_STOP_PIPS * pip_size, pip_val, pip_size,
                                            risk_pct_override=RISK_PCT_PER_SETUP)
                    if lots <= 0:
                        continue

                    res = mt5_connector.place_market_order(
                        s.symbol, s.direction, lots, sl=0.0, tp=0.0,
                        comment=s.label, dry_run=not args.live, magic=s.magic)
                    actual_entry = res.price if res else expected_entry
                    slip = abs(actual_entry - expected_entry) / pip_size

                    print(f"  [{s.label}] OTEVRENO @ {actual_entry:.5f} | spread "
                          f"{spread_pips:.2f} pipu (cekano {s.expected_cost_pips}) | skluz {slip:.2f}")
                    log_row(FILL_LOG,
                            ["time", "setup", "faze", "ocekavana_cena", "skutecna_cena",
                             "skluz_pipu", "spread_pipu"],
                            [now.isoformat(), s.label, "entry", expected_entry, actual_entry,
                             round(slip, 2), round(spread_pips, 2)])

                    if args.live:
                        st["opened"][key] = {"time": now.isoformat(), "entry_price": actual_entry,
                                             "lots": lots}
                        save_state(st)

            time.sleep(30)

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
