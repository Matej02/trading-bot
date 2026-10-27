"""
Zdroje signalu:
  - python_signals(): pravidla pocitana v Pythonu (zdarma, bez TradingView)
  - start_webhook(): prijimac TradingView alertu (vyzaduje placeny TV plan)

Obe vraci stejny Signal, takze prepnuti na TradingView je jen vymena zdroje.
"""

import hmac
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import mt5_connector
from tv_agent.signals import Signal, from_tradingview


def closed_h1(symbol, n_bars, server_offset_h=0, tries=10):
    """Uzavrene H1 svicky.

    copy_rates_from_pos(..., 0, n) vraci jako posledni radek svicku, ktera se
    prave tvori (par vterin dat) - ta se zahodi, backtest ji nikdy nevidel.
    Navic prvni dotaz na symbol obcas vrati starou cache terminalu (AUDJPY
    prislo o 4 jeny vedle), proto se overi, ze tvorici se svicka je ta aktualni.
    A broker ma v historii diry (EURUSD: chybi 2025-10-07 az 2026-10-22) -
    indikatory pres diru by michaly rok stara data, proto se takova data odmitnou."""
    expected = (datetime.now(timezone.utc) + timedelta(hours=server_offset_h)) \
        .replace(minute=0, second=0, microsecond=0, tzinfo=None)
    for _ in range(tries):
        df = mt5_connector.fetch_h1_history(symbol, n_bars=n_bars)
        if df.index[-1] == expected:
            break
        time.sleep(2)
    else:
        raise mt5_connector.MT5ConnectionError(
            f"{symbol}: data nejsou aktualni (posledni svicka {df.index[-1]}, ocekavana {expected})")
    gaps = df.index.to_series().diff()
    hole = gaps[gaps > timedelta(days=5)]
    if len(hole):
        end = hole.index[-1]
        raise mt5_connector.MT5ConnectionError(
            f"{symbol}: v poslednich {n_bars} svickach je dira v datech ({hole.iloc[-1].days} dni pred {end:%Y-%m-%d}); "
            f"po ni je zatim jen {(df.index > end).sum()} svicek")
    return df.iloc[:-1]


def python_signals(setups, server_offset_h=0):
    """setups: [(symbol, strategy_module, nazev_setupu), ...]
    Posuzuje se POSLEDNI UZAVRENA svicka."""
    out = []
    for symbol, mod, setup in setups:
        try:
            df = closed_h1(symbol, 400, server_offset_h)
        except mt5_connector.MT5ConnectionError as e:
            print(f"   [{symbol} {setup}] preskakuji: {e}")
            continue
        ind = mod.add_indicators(df)
        row, prev = ind.iloc[-1], ind.iloc[-2]
        direction = mod.generate_signal(row, prev)
        if direction is None:
            print(f"   [{symbol} {setup}] zadny signal na svicce {row.name}")
            continue
        bar_close_server = row.name + timedelta(hours=1)
        bar_close_utc = (bar_close_server - timedelta(hours=server_offset_h)).tz_localize(timezone.utc)
        out.append(Signal(
            id=f"{setup}-{symbol}-{row.name.isoformat()}",
            symbol=symbol, direction=direction, setup=setup,
            price=float(row["close"]), time=bar_close_utc.to_pydatetime(), source="python",
        ))
    return out


class _Handler(BaseHTTPRequestHandler):
    queue = None
    secret = None

    def _reply(self, code, text):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def do_POST(self):
        if self.path != "/tv":
            return self._reply(404, "not found")
        length = min(int(self.headers.get("Content-Length", 0)), 10_000)
        try:
            payload = json.loads(self.rfile.read(length))
        except Exception:
            return self._reply(400, "spatny JSON")
        if not self.secret or not hmac.compare_digest(str(payload.get("secret", "")), self.secret):
            return self._reply(403, "spatny secret")
        try:
            sig = from_tradingview(payload)
        except Exception as e:
            return self._reply(400, f"neplatny signal: {e}")
        self.queue.put(sig)
        self._reply(200, "ok")

    def log_message(self, fmt, *args):
        pass


def start_webhook(queue, secret, port=8787, host="127.0.0.1"):
    """Spusti prijimac na pozadi. Vychozi host 127.0.0.1 = jen z tohoto PC;
    pro TradingView bude potreba verejna adresa (tunel/VPS) - az ve F5."""
    _Handler.queue = queue
    _Handler.secret = secret
    srv = ThreadingHTTPServer((host, port), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
