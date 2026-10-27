"""
Posle zkusebni alert na bezici prijimac (python run_tv_agent.py --source webhook),
presne ve tvaru, jaky pak bude posilat TradingView. Signal je oznaceny jako test,
takze se do stinoveho vyhodnoceni nepocita.

  python simulate_alert.py EURUSD long
  python simulate_alert.py EURUSD short --secret spatny   # ma vratit 403
"""

import argparse
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

import mt5_connector

ap = argparse.ArgumentParser()
ap.add_argument("symbol")
ap.add_argument("direction", choices=["long", "short", "buy", "sell"])
ap.add_argument("--port", type=int, default=8787)
ap.add_argument("--secret", help="jinak z TV_WEBHOOK_SECRET")
args = ap.parse_args()

mt5_connector.connect()
bid, ask, _ = mt5_connector.get_current_prices(args.symbol.upper())
mt5_connector.disconnect()

now = datetime.now(timezone.utc).isoformat()
payload = {
    "secret": args.secret or os.environ.get("TV_WEBHOOK_SECRET", ""),
    "id": f"sim-{now}-{args.symbol}",
    "symbol": f"OANDA:{args.symbol.upper()}",
    "direction": args.direction,
    "setup": "simulace",
    "price": ask if args.direction in ("long", "buy") else bid,
    "time": now,
    "test": True,
}
req = urllib.request.Request(f"http://127.0.0.1:{args.port}/tv", data=json.dumps(payload).encode(),
                             headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        print(r.status, r.read().decode())
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode())
