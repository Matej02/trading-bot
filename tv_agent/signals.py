"""
Jednotny format signalu - stejny pro Python zdroj i TradingView webhook,
aby agenti nemuseli vedet, odkud signal prisel.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class Signal:
    id: str                 # unikatni - podle nej Validator chyta duplicity
    symbol: str
    direction: str          # "long" / "short"
    setup: str              # napr. "bbsqueeze_h1" - podle nej Statistik hleda overeni
    price: float            # cena v okamziku signalu
    time: datetime          # UTC
    source: str             # "python" / "tradingview" / "test"
    sl: float | None = None
    tp: float | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["time"] = self.time.isoformat()
        return d


def from_tradingview(payload: dict) -> Signal:
    """Prevede JSON z TradingView alertu na Signal.

    Ocekavany tvar zpravy alertu (nastavi se v Pine Scriptu / dialogu alertu):
      {"secret": "...", "id": "{{timenow}}-{{ticker}}", "symbol": "{{ticker}}",
       "direction": "long", "setup": "nazev_setupu", "price": {{close}},
       "time": "{{timenow}}"}
    """
    direction = str(payload["direction"]).lower()
    direction = {"buy": "long", "sell": "short"}.get(direction, direction)
    if direction not in ("long", "short"):
        raise ValueError(f"neznamy smer: {payload['direction']}")

    raw_t = payload.get("time")
    t = datetime.fromisoformat(str(raw_t).replace("Z", "+00:00")) if raw_t else datetime.now(timezone.utc)
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)

    symbol = str(payload["symbol"]).split(":")[-1].upper()     # "OANDA:EURUSD" -> "EURUSD"
    return Signal(
        id=str(payload.get("id") or f"{symbol}-{t.isoformat()}"),
        symbol=symbol,
        direction=direction,
        setup=str(payload.get("setup", "nezname")),
        price=float(payload["price"]),
        time=t,
        source="test" if payload.get("test") else "tradingview",   # simulate_alert.py -> nepocita se
        sl=float(payload["sl"]) if payload.get("sl") is not None else None,
        tp=float(payload["tp"]) if payload.get("tp") is not None else None,
    )
