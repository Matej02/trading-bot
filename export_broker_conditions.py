"""
Vyexportuje skutecne podminky brokera z MT5 do simulatoru (simulator/lib/broker.json):
spread po hodinach (ziva cena = historie ticku + prirazka), swapy, hodnotu pohybu
ceny v USD na lot, minimalni lot a krok. Spoustet znovu, kdyz se podminky zmeni.
"""

import json
import os
import sys

import mt5_connector as mc
import research_f1 as r
import strategy_momentum as sm

sys.stdout.reconfigure(line_buffering=True)

OUT = os.path.join("simulator", "lib", "broker.json")
BINANCE = {"BTCUSD": "BTCUSDT", "ETHUSD": "ETHUSDT"}
NAMES = {
    "SPX500mini": "S&P 500", "US30mini": "Dow Jones 30", "NAS100mini": "Nasdaq 100", "GER_30mini": "DAX 40",
    "GBR_100mini": "FTSE 100", "FRA_40mini": "CAC 40", "EUR_50mini": "Euro Stoxx 50", "ESP_35mini": "IBEX 35",
    "XAUUSD": "Zlato", "GAUUSD": "Zlato (gram)", "XPTUSD": "Platina", "XAGUSD": "Stribro",
    "CRUDE_OIL": "Ropa WTI", "BRENT_OIL": "Ropa Brent", "BTCUSD": "Bitcoin", "ETHUSD": "Ethereum",
}

mc.connect()
mt5 = mc.mt5
# cena Yahoo vs broker: kde se lisi vic nez 5 % (GAUUSD je v gramech, Yahoo v uncich),
# simulator ceny z Yahoo prepocita, jinak by P&L vyslo nasobne vedle
yahoo_last = {s: c.iloc[-1] for s, c in sm.fetch_daily(sm.UNIVERSE, period="1mo").items() if len(c)}
spreads = json.load(open("tv_spreads.json"))
markup = spreads.get("_markup", {})
out = {}
for s in sm.UNIVERSE:
    mt5.symbol_select(s, True)
    si = mt5.symbol_info(s)
    pip, _ = mc.get_pip_value_per_lot(s)
    price = si.bid
    # maly krok (u USDJPY apod. se zisk prevadi kurzem na konci kroku) a 100 lotu,
    # aby zaokrouhleni order_calc_profit na centy nezkreslilo vysledek
    d = price * 0.001
    money_per_price = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, s, 100.0, price, price + d) / d / 100
    sl, ss = r.swap_frac(si, price)
    hours = spreads.get(s, {})
    mk = markup.get(s, 0.0)
    by_hour = [round((hours[str(h)] + mk) * pip, si.digits + 1) if str(h) in hours else None for h in range(24)]
    fallback = sorted(v for v in by_hour if v is not None)
    med = fallback[len(fallback) // 2] if fallback else si.spread * si.point
    ratio = price / yahoo_last[s] if s in yahoo_last else 1.0
    scale = 1.0 if abs(ratio - 1) < 0.05 or BINANCE.get(s) else ratio
    out[s] = {
        "priceScale": scale,                       # cena Yahoo x tohle = cena brokera
        "name": NAMES.get(s, s),
        "group": si.path.split("\\")[0],
        "yahoo": sm.YAHOO[s],
        "binance": BINANCE.get(s),
        "digits": si.digits,
        "pip": pip,
        "spreadByHour": [v if v is not None else med for v in by_hour],
        "swapLong": sl, "swapShort": ss,          # podil ceny za noc
        "roll3": (si.swap_rollover3days - 1) % 7,  # python weekday (0 = pondeli), 3x swap
        "moneyPerPrice": money_per_price,          # USD za pohyb ceny o 1.0 na 1 lot
        "volMin": si.volume_min, "volStep": si.volume_step, "volMax": si.volume_max,
        "decisionHour": sm.decision_hour(s),
    }
    print(f"{s:<12} spread {med:.5g}  swap L {100 * sl:+.4f} % S {100 * ss:+.4f} %  $/1.0 ceny/lot {money_per_price:.4g}"
          f"  broker/Yahoo {ratio:.4f}{'  -> PREPOCET' if scale != 1.0 else ''}")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"account": "GlobalDynamicMarkets-Demo", "markets": out}, f, indent=1, ensure_ascii=False)
print(f"\nZapsano {len(out)} trhu do {OUT}")
