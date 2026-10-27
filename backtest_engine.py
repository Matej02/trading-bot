"""
Backtest engine - simuluje bota bar po baru na historickych OHLC datech.
Zaznamenava kazdy trade a pocita vysledne statistiky.
"""

import pandas as pd
from dataclasses import dataclass
from strategy import add_indicators as default_add_indicators, generate_signal as default_generate_signal, compute_sl_tp as default_compute_sl_tp
from risk_manager import RiskManager, RiskConfig


PIP_SIZE = 0.0001          # EUR/USD
PIP_VALUE_PER_LOT = 10.0   # USD, standardni lot, EUR/USD


@dataclass
class Trade:
    entry_time: object
    direction: str
    entry_price: float
    sl: float
    tp: float
    lots: float
    exit_time: object = None
    exit_price: float = None
    pnl: float = None
    result: str = None  # "win" / "loss"
    label: str = None   # ktery system (par+strategie) trade otevrel - jen pro portfolio backtest


def run_backtest(df: pd.DataFrame, risk_cfg: RiskConfig, pip_size: float = PIP_SIZE, pip_value_per_lot: float = PIP_VALUE_PER_LOT,
                  add_indicators=default_add_indicators, generate_signal=default_generate_signal, compute_sl_tp=default_compute_sl_tp,
                  spread_pips: float = 0.0, swap_points_long: float = 0.0, swap_points_short: float = 0.0,
                  point_size: float = None, trail_atr: float = None, breakeven_at_r: float = None,
                  max_bars_in_trade: int = None):
    """add_indicators/generate_signal/compute_sl_tp jsou vymenitelne - vychozi je
    strategie z strategy.py, ale pro vyzkumne ucely (jina vstupni logika) jde
    dosadit jine funkce se stejnym rozhranim, beze zmeny simulacni smycky.

    Naklady:
      spread_pips        - zaplaceno jednou za round-trip
      swap_points_*      - poplatek za drzeni pres noc (v bodech/noc, jak to
                           vraci MT5 symbol_info); dulezite pro D1/H4 strategie
      point_size         - velikost bodu (pro prevod swapu); default pip_size/10

    Vystupni logika (vsechno volitelne, default = pevny SL/TP jako drive):
      trail_atr          - trailing stop N*ATR za nejlepsi dosazenou cenou
      breakeven_at_r     - presun SL na vstup, jakmile je zisk >= N*R
      max_bars_in_trade  - zavrit na trhu po N barech
    """
    df = add_indicators(df)
    rm = RiskManager(risk_cfg)
    if point_size is None:
        point_size = pip_size / 10

    trades = []
    open_trade: Trade = None
    equity_curve = []
    bars_in_trade = 0
    best_price = None
    initial_risk = None

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i - 1]
        rm.new_bar(row.name)

        # spravuj otevreny trade
        if open_trade is not None:
            bars_in_trade += 1
            is_long = open_trade.direction == "long"

            # aktualizuj nejlepsi dosazenou cenu (pro trailing / breakeven)
            best_price = max(best_price, row["high"]) if is_long else min(best_price, row["low"])

            # breakeven: jakmile zisk dosahl N*R, posun SL na vstup
            if breakeven_at_r is not None and initial_risk:
                reached = (best_price - open_trade.entry_price) if is_long else (open_trade.entry_price - best_price)
                if reached >= breakeven_at_r * initial_risk:
                    open_trade.sl = max(open_trade.sl, open_trade.entry_price) if is_long else min(open_trade.sl, open_trade.entry_price)

            # trailing stop: SL se tahne N*ATR za nejlepsi cenou, nikdy zpet
            if trail_atr is not None and not pd.isna(row["atr"]):
                trail = (best_price - trail_atr * row["atr"]) if is_long else (best_price + trail_atr * row["atr"])
                open_trade.sl = max(open_trade.sl, trail) if is_long else min(open_trade.sl, trail)

            hit_sl = (row["low"] <= open_trade.sl) if is_long else (row["high"] >= open_trade.sl)
            hit_tp = (row["high"] >= open_trade.tp) if is_long else (row["low"] <= open_trade.tp)

            exit_price = None
            if hit_sl and hit_tp:
                # konzervativni predpoklad: pokud oba v jedne svicce, pocitej horsi variantu (SL)
                exit_price = open_trade.sl
            elif hit_sl:
                exit_price = open_trade.sl
            elif hit_tp:
                exit_price = open_trade.tp
            elif max_bars_in_trade is not None and bars_in_trade >= max_bars_in_trade:
                exit_price = row["close"]  # casovy vystup na trhu

            if exit_price is not None:
                price_diff = (exit_price - open_trade.entry_price) if is_long else (open_trade.entry_price - exit_price)
                pips = price_diff / pip_size
                # spread se zaplati jednou za round-trip (vstup na ask, vystup na bid u longu a naopak)
                gross = (pips - spread_pips) * pip_value_per_lot * open_trade.lots
                # swap za kazdou drzenou noc (MT5 vraci body za noc; streda se uctuje 3x - zjednoduseno prumerem)
                nights = max((row.name - open_trade.entry_time).days, 0)
                swap_pts = swap_points_long if is_long else swap_points_short
                swap_cost = nights * swap_pts * (point_size / pip_size) * pip_value_per_lot * open_trade.lots
                pnl = gross + swap_cost
                open_trade.exit_time = row.name
                open_trade.exit_price = exit_price
                open_trade.pnl = pnl
                open_trade.result = "win" if pnl > 0 else "loss"
                rm.register_trade_result(pnl)
                trades.append(open_trade)
                open_trade = None
                bars_in_trade = 0
                best_price = None
                initial_risk = None

        # hledej novy vstup, jen pokud nejsme v pozici a risk manager dovoli obchodovat
        if open_trade is None and rm.can_trade():
            signal = generate_signal(row, prev_row)
            if signal is not None:
                sl, tp = compute_sl_tp(row["close"], row["atr"], signal)
                sl_dist = abs(row["close"] - sl)
                lots = rm.position_size(sl_dist, pip_value_per_lot, pip_size)
                if lots > 0:
                    open_trade = Trade(
                        entry_time=row.name,
                        direction=signal,
                        entry_price=row["close"],
                        sl=sl,
                        tp=tp,
                        lots=lots,
                    )
                    bars_in_trade = 0
                    best_price = row["close"]
                    initial_risk = sl_dist

        equity_curve.append({"time": row.name, "balance": rm.balance, "halted": rm.halted, "passed": rm.challenge_passed})

        if rm.halted or rm.challenge_passed:
            break

    equity_df = pd.DataFrame(equity_curve).set_index("time")
    return trades, equity_df, rm


def run_portfolio_backtest(data_by_symbol: dict, portfolio: list, risk_cfg: RiskConfig, pip_info: dict,
                            spread_pips_by_symbol: dict = None):
    """Backtestuje vic nezavislych systemu (par+strategie) najednou nad
    SDILENYM risk managerem - presne to, co dela run_live_demo.py naostro.
    Nutne pro poctivou validaci portfolia, protoze systemy sdili denni
    limit obchodu a cooldown, takze vysledek NENI proste soucet
    jednotlivych izolovanych backtestu.

    data_by_symbol: {symbol: OHLC DataFrame}, pip_info: {symbol: (pip_size, pip_value_per_lot)}
    portfolio: [{"symbol":.., "strategy": modul, "magic": int, "label": str}, ...]
    """
    prepared = []
    for cfg in portfolio:
        df = cfg["strategy"].add_indicators(data_by_symbol[cfg["symbol"]])
        prepared.append({**cfg, "df": df, "open_trade": None})

    master_index = None
    for p in prepared:
        idx = p["df"].index
        master_index = idx if master_index is None else master_index.intersection(idx)
    master_index = master_index.sort_values()

    rm = RiskManager(risk_cfg)
    trades = []
    equity_curve = []

    for i in range(1, len(master_index)):
        ts, prev_ts = master_index[i], master_index[i - 1]
        rm.new_bar(ts)

        for p in prepared:
            df = p["df"]
            row, prev_row = df.loc[ts], df.loc[prev_ts]
            pip_size, pip_value_per_lot = pip_info[p["symbol"]]

            ot = p["open_trade"]
            if ot is not None:
                hit_sl = (row["low"] <= ot.sl) if ot.direction == "long" else (row["high"] >= ot.sl)
                hit_tp = (row["high"] >= ot.tp) if ot.direction == "long" else (row["low"] <= ot.tp)
                exit_price = ot.sl if (hit_sl and hit_tp) or hit_sl else (ot.tp if hit_tp else None)
                if exit_price is not None:
                    price_diff = (exit_price - ot.entry_price) if ot.direction == "long" else (ot.entry_price - exit_price)
                    spread = (spread_pips_by_symbol or {}).get(p["symbol"], 0.0)
                    pnl = ((price_diff / pip_size) - spread) * pip_value_per_lot * ot.lots
                    ot.exit_time, ot.exit_price, ot.pnl = ts, exit_price, pnl
                    ot.result = "win" if pnl > 0 else "loss"
                    rm.register_trade_result(pnl)
                    trades.append(ot)
                    p["open_trade"] = None

            if p["open_trade"] is None and rm.can_trade():
                signal = p["strategy"].generate_signal(row, prev_row)
                if signal is not None:
                    sl, tp = p["strategy"].compute_sl_tp(row["close"], row["atr"], signal)
                    sl_dist = abs(row["close"] - sl)
                    lots = rm.position_size(sl_dist, pip_value_per_lot, pip_size, risk_pct_override=p.get("risk_pct"))
                    if lots > 0:
                        p["open_trade"] = Trade(
                            entry_time=ts, direction=signal, entry_price=row["close"],
                            sl=sl, tp=tp, lots=lots, label=p["label"],
                        )

        equity_curve.append({"time": ts, "balance": rm.balance, "halted": rm.halted, "passed": rm.challenge_passed})
        if rm.halted or rm.challenge_passed:
            break

    equity_df = pd.DataFrame(equity_curve).set_index("time")
    return trades, equity_df, rm


def summarize(trades, equity_df, rm: RiskManager, risk_cfg: RiskConfig):
    n = len(trades)
    wins = [t for t in trades if t.result == "win"]
    losses = [t for t in trades if t.result == "loss"]
    win_rate = len(wins) / n * 100 if n else 0.0
    gross_win = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    max_dd = (equity_df["balance"].cummax() - equity_df["balance"]).max() if not equity_df.empty else 0

    status = "CHALLENGE SPLNEN" if rm.challenge_passed else ("ZASTAVENO - " + rm.halt_reason if rm.halted else "DATA DOSLA (bez rozhodnuti)")

    return {
        "pocet_obchodu": n,
        "winrate_%": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "inf",
        "konecny_balance": round(rm.balance, 2),
        "max_drawdown_$": round(max_dd, 2),
        "vysledek": status,
    }
