"""
Pripojeni k MetaTrader 5 terminalu - realna historicka data + demo/live
obchodovani pres oficialni Python balicek `MetaTrader5` (Windows-only,
mluvi s bezicim terminalem pres IPC).

Bezpecnostni princip: tenhle modul NIKDY nepracuje s heslem primo.
Standardni pouziti je, ze se uzivatel rucne prihlasi do demo uctu
v MT5 terminalu (GUI) a `connect()` se pak jen pripoji k uz bezicimu,
prihlasenemu terminalu (`mt5.initialize()` bez credentials).

Automaticky login je podporeny jen pro pripad, ze terminal jeste neni
prihlaseny - credentials se ctou VYHRADNE z env promennych
(MT5_LOGIN / MT5_PASSWORD / MT5_SERVER), nikdy nejsou v kodu.
"""

import os
from datetime import datetime, timezone

import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None


class MT5ConnectionError(RuntimeError):
    pass


def _require_mt5():
    if mt5 is None:
        raise MT5ConnectionError(
            "Balicek 'MetaTrader5' neni nainstalovany. Spust: pip install MetaTrader5"
        )


def connect(path: str | None = None) -> None:
    """Pripoji se k bezicimu MT5 terminalu. Pokud jsou nastavene env
    promenne MT5_LOGIN/MT5_PASSWORD/MT5_SERVER, prihlasi se s nimi;
    jinak predpoklada, ze terminal je uz rucne prihlaseny do uctu."""
    _require_mt5()

    kwargs = {}
    if path:
        kwargs["path"] = path

    login = os.environ.get("MT5_LOGIN")
    password = os.environ.get("MT5_PASSWORD")
    server = os.environ.get("MT5_SERVER")
    if login and password and server:
        kwargs.update(login=int(login), password=password, server=server)

    if not mt5.initialize(**kwargs):
        code, desc = mt5.last_error()
        raise MT5ConnectionError(
            f"mt5.initialize() selhal ({code}: {desc}). Zkontroluj, ze je MT5 "
            "terminal nainstalovany, spusteny a prihlaseny do uctu."
        )

    info = mt5.account_info()
    if info is None:
        mt5.shutdown()
        raise MT5ConnectionError(
            "Pripojeno k terminalu, ale account_info() je prazdne - "
            "je terminal prihlaseny do obchodniho uctu?"
        )

    mode = "DEMO" if info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO else "!!! LIVE - REALNE PENIZE !!!"
    print(f"Pripojeno: ucet {info.login} @ {info.server} | balance={info.balance} {info.currency} | {mode}")


def disconnect() -> None:
    if mt5 is not None:
        mt5.shutdown()


def is_demo_account() -> bool:
    _require_mt5()
    info = mt5.account_info()
    return info is not None and info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO


def get_account_balance() -> float:
    _require_mt5()
    info = mt5.account_info()
    if info is None:
        raise MT5ConnectionError("account_info() je prazdne - neni pripojeno?")
    return info.balance


def fetch_h1_history(symbol: str = "EURUSD", n_bars: int = 8000) -> pd.DataFrame:
    """Stahne poslednich n_bars H1 sviček ze skutecne historie brokera.
    Vraci DataFrame ve stejnem tvaru jako generate_sample_data (index=time,
    sloupce open/high/low/close), takze je to primy nahradnik za synteticka data."""
    _require_mt5()

    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, n_bars)
    if rates is None or len(rates) == 0:
        code, desc = mt5.last_error()
        raise MT5ConnectionError(
            f"copy_rates_from_pos({symbol}) nevratilo data ({code}: {desc}). "
            "Zkontroluj presny nazev symbolu v Market Watch (napr. 'EURUSD' vs 'EURUSD.m' "
            "nebo 'EURUSDm' - lisi se broker od brokera)."
        )

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("time")[["open", "high", "low", "close", "tick_volume"]].astype(float)
    df.index.name = "time"
    return df


def get_pip_value_per_lot(symbol: str = "EURUSD") -> tuple[float, float]:
    """Vrati (pip_size, pip_value_per_lot) podle skutecnych parametru
    symbolu u tohoto brokera - presnejsi nez natvrdo zapsana konstanta,
    funguje spravne i pro jiny nez USD ucet."""
    _require_mt5()

    sym = mt5.symbol_info(symbol)
    if sym is None:
        raise MT5ConnectionError(f"Symbol {symbol} nenalezen. Zkontroluj nazev v Market Watch.")

    pip_size = sym.point * 10 if sym.digits in (3, 5) else sym.point
    # Hodnota podle skutecneho vypoctu zisku brokera. tick_value/tick_size u nekterych
    # symbolu nesedi (US30mini, NAS100mini: 10x mene) -> pozice by vysla 10x vetsi.
    price = sym.bid or sym.ask
    pip_value_per_lot = None
    if price:
        pip_value_per_lot = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, symbol, 1.0, price, price + pip_size)
    if not pip_value_per_lot:
        tick_size = sym.trade_tick_size or sym.point
        pip_value_per_lot = sym.trade_tick_value * (pip_size / tick_size)
    return pip_size, pip_value_per_lot


def get_open_positions(symbol: str = "EURUSD", magic: int | None = None):
    """magic=None vrati vsechny otevrene pozice v danem symbolu. S magic
    vrati jen pozice patrici konkretnimu systemu (strategii) - potrebne,
    kdyz na stejnem symbolu bezi vic nezavislych strategii najednou."""
    _require_mt5()
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return []
    if magic is not None:
        positions = [p for p in positions if p.magic == magic]
    return list(positions)


def close_position(position, comment: str = "bot-close", dry_run: bool = True):
    """Zavre konkretni otevrenou pozici na trhu. Vraci (result, fill_price).
    Pouziva se u casove rizenych strategii, kde se nezavira na SL/TP,
    ale po uplynuti dane doby."""
    if dry_run:
        print(f"    [DRY RUN] zavrel bych pozici {getattr(position, 'ticket', '?')} "
              f"{position.symbol} {position.volume} lot")
        return None, None

    _require_mt5()

    tick = mt5.symbol_info_tick(position.symbol)
    if tick is None:
        raise MT5ConnectionError(f"symbol_info_tick({position.symbol}) selhalo pri zavirani.")

    is_long = position.type == mt5.POSITION_TYPE_BUY
    close_type = mt5.ORDER_TYPE_SELL if is_long else mt5.ORDER_TYPE_BUY
    price = tick.bid if is_long else tick.ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": close_type,
        "position": position.ticket,
        "price": price,
        "deviation": 20,
        "magic": position.magic,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        code, desc = mt5.last_error()
        raise MT5ConnectionError(
            f"zavreni pozice {position.ticket} selhalo: "
            f"retcode={getattr(result, 'retcode', None)} ({code}: {desc})"
        )
    return result, result.price


def get_current_prices(symbol: str):
    """Vraci (bid, ask, spread_v_bodech) - pro mereni skutecnych nakladu."""
    _require_mt5()
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise MT5ConnectionError(f"symbol_info_tick({symbol}) selhalo.")
    return tick.bid, tick.ask, tick.ask - tick.bid


def place_market_order(symbol: str, direction: str, lots: float, sl: float, tp: float,
                        comment: str = "bot", dry_run: bool = True, magic: int = 20260819):
    """Posle market order se SL/TP. Pri dry_run=True (vychozi) nic
    neposila na broker, jen vypise, co by udelal - bezpecny default,
    dokud si nejsi jisty, ze vsechno funguje spravne."""
    if direction not in ("long", "short"):
        raise ValueError("direction musi byt 'long' nebo 'short'")

    if dry_run:
        # i v dry-run ukaz SKUTECNE aktualni ceny - pro mereni nakladu
        try:
            bid, ask, sp = get_current_prices(symbol)
            would = ask if direction == "long" else bid
            print(f"    [DRY RUN] {direction.upper()} {lots} lot {symbol} @ {would:.5f} "
                  f"(bid={bid:.5f} ask={ask:.5f} spread={sp:.5f})")
        except Exception:
            print(f"    [DRY RUN] {direction.upper()} {lots} lot {symbol} | SL={sl:.5f} TP={tp:.5f}")
        return None

    _require_mt5()

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise MT5ConnectionError(f"symbol_info_tick({symbol}) selhalo.")

    order_type = mt5.ORDER_TYPE_BUY if direction == "long" else mt5.ORDER_TYPE_SELL
    price = tick.ask if direction == "long" else tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lots,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": magic,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        code, desc = mt5.last_error()
        raise MT5ConnectionError(
            f"order_send selhal: retcode={getattr(result, 'retcode', None)} ({code}: {desc})"
        )
    print(f"[LIVE] {direction.upper()} {lots} lot {symbol} @ {price} | SL={sl:.5f} TP={tp:.5f} | ticket={result.order}")
    return result


def compute_risk_state_from_history(starting_balance: float, challenge_start: datetime, cooldown_bars: int = 0):
    """Rekonstruuje balance/equity_peak/day_start_balance/trades_today
    primo z historie obchodu na uctu. Broker je jediny zdroj pravdy,
    takze tohle po restartu skriptu nikdy neztrati spravny stav
    (na rozdil od lokalnich pocitadel v pameti).

    cooldown_active rika, jestli posledni uzavreny obchod byla ztrata
    v ramci posledních cooldown_bars hodin (1 H1 bar = 1 hodina) -
    stejna logika jako v backtestu, aby se live chovani shodovalo."""
    _require_mt5()

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    deals = mt5.history_deals_get(challenge_start, now) or []
    closed = sorted((d for d in deals if d.entry == mt5.DEAL_ENTRY_OUT), key=lambda d: d.time)

    balance = starting_balance
    peak = starting_balance
    day_start_balance = starting_balance
    trades_today = 0
    last_deal_time = None
    last_deal_realized = None

    for d in closed:
        deal_time = datetime.fromtimestamp(d.time, tz=timezone.utc)
        realized = d.profit + d.swap + d.commission
        if deal_time < today_start:
            day_start_balance = balance + realized
        else:
            trades_today += 1
        balance += realized
        peak = max(peak, balance)
        last_deal_time = deal_time
        last_deal_realized = realized

    cooldown_active = False
    if cooldown_bars > 0 and last_deal_time is not None and last_deal_realized < 0:
        hours_since = (now - last_deal_time).total_seconds() / 3600
        cooldown_active = hours_since < cooldown_bars

    return balance, peak, day_start_balance, trades_today, cooldown_active
