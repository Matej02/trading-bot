"""
Bot s agenty: kazdy signal projde 4 agenty, kteri reknou ANO/NE a PROC.
Vsechno (i zamitnute) jde do tv_journal.jsonl, aby slo pozdeji zmerit,
jestli agenti filtruji lepe nez nahoda (--evaluate).

Pouziti:
  python run_tv_agent.py                           # signaly z Pythonu, paper (nic neposila)
  python run_tv_agent.py --source webhook          # prijimac TradingView alertu na 127.0.0.1:8787
  python run_tv_agent.py --test-signal EURUSD:long # jeden zkusebni signal skrz agenty a konec
  python run_tv_agent.py --evaluate                # stinove vyhodnoceni deniku
  python run_tv_agent.py --live                    # schvalene obchody opravdu posle - JEN na demo

Momentum (40 trhu, rozhodnuti 1x denne v 15:00 / 19:00 UTC, signal z Yahoo):
  python run_tv_agent.py --momentum-check          # kontrola: co by udelalo dnes, NIC nezapise ani neposle
  python run_tv_agent.py --source momentum         # papirovy beh (denik + tv_momentum_book.json)
  python run_tv_agent.py --evaluate-momentum       # vysledek strategie vs co pustili agenti

Webhook potrebuje tajny retezec v promenne prostredi TV_WEBHOOK_SECRET
(nastavis si ho sam, stejny pak das do zpravy alertu v TradingView).
"""

import argparse
import json
import os
import queue
import sys
import time
from datetime import datetime, timedelta, timezone

import numpy as np

sys.stdout.reconfigure(line_buffering=True)

import mt5_connector
import strategy as strategy_pullback
import strategy_bbsqueeze
import strategy_momentum as sm
from risk_manager import RiskConfig, RiskManager
from tv_agent import momentum, pipeline, shadow_eval, sources
from tv_agent.agents import MarketNowAgent, RiskAgent, StatisticianAgent, ValidatorAgent
from tv_agent.signals import Signal

STATE_FILE = "tv_state.json"
SPREAD_FILE = "tv_spreads.json"
REGISTRY = os.path.join("tv_agent", "setups.json")

SETUPS = [
    ("EURUSD", strategy_pullback, "pullback_h1"),
    ("EURUSD", strategy_bbsqueeze, "bbsqueeze_h1"),
    ("AUDJPY", strategy_bbsqueeze, "bbsqueeze_h1"),
]
SYMBOLS = sorted({s for s, _, _ in SETUPS})


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            st = json.load(f)
        return st["starting_balance"], datetime.fromisoformat(st["challenge_start"])
    bal, start = mt5_connector.get_account_balance(), datetime.now(timezone.utc)
    with open(STATE_FILE, "w") as f:
        json.dump({"starting_balance": bal, "challenge_start": start.isoformat()}, f, indent=2)
    print(f"Novy {STATE_FILE}: start {bal}")
    return bal, start


def load_normal_spreads(symbols, days=10, max_age_days=7):
    """Medianovy spread v pipech pro kazdou hodinu serveru, z tick dat.
    (symbol_info.spread nadhodnocuje 3-4x - to uz nas jednou spalilo.)"""
    cache = {}
    if os.path.exists(SPREAD_FILE):
        with open(SPREAD_FILE) as f:
            cache = json.load(f)
    fresh = cache.get("_built") and \
        datetime.now(timezone.utc) - datetime.fromisoformat(cache["_built"]) < timedelta(days=max_age_days)
    if fresh and all(s in cache for s in symbols):
        return {s: cache[s] for s in symbols}

    print(f"Pocitam normalni spready z tick dat za {days} dni...")
    now = datetime.now(timezone.utc)
    out = {"_built": now.isoformat()}
    for sym in symbols:
        pip = mt5_connector.get_pip_value_per_lot(sym)[0]
        ticks = mt5_connector.mt5.copy_ticks_range(sym, now - timedelta(days=days), now,
                                                   mt5_connector.mt5.COPY_TICKS_INFO)
        if ticks is None or len(ticks) == 0:
            print(f"   {sym}: tick data nejsou, kontrola spreadu pojede bez normalu")
            continue
        hours = (ticks["time"] // 3600) % 24                    # cas serveru
        sp = (ticks["ask"] - ticks["bid"]) / pip
        out[sym] = {str(h): float(np.median(sp[hours == h])) for h in range(24) if (hours == h).any()}
        print(f"   {sym}: {len(ticks):,} ticku, typicky spread {np.median(sp):.2f} pipu")
    with open(SPREAD_FILE, "w") as f:
        json.dump(out, f, indent=2)
    return {s: out[s] for s in symbols if s in out}


def live_normals(raw, symbols):
    """Normaly z historie ticku jsou surova cena; obchoduje se za zivou cenu
    s prirazkou brokera. Zmeri prirazku a normaly o ni posune.
    Kdyz trh stoji (nejde zmerit), vezme posledni zmerenou hodnotu."""
    with open(SPREAD_FILE) as f:
        cache = json.load(f)
    stored = cache.get("_markup", {})
    markup = {}
    for sym in symbols:
        m = pipeline.measure_markup(sym)
        if m is None:
            m = stored.get(sym, 0.0)
            print(f"   {sym}: prirazku nejde ted zmerit, beru posledni znamou {m:.1f} pipu")
        markup[sym] = m
    cache["_markup"] = {**stored, **markup}
    with open(SPREAD_FILE, "w") as f:
        json.dump(cache, f, indent=2)
    print("Prirazka brokera k zive cene: " + ", ".join(f"{s} +{m:.1f} pipu" for s, m in markup.items()))
    return {s: {h: v + markup[s] for h, v in hrs.items()} for s, hrs in raw.items()}, markup


def seen_ids():
    """ID uz zpracovanych signalu z deniku - aby restart nevzal stejny signal znovu."""
    if not os.path.exists(pipeline.JOURNAL):
        return set()
    with open(pipeline.JOURNAL, encoding="utf-8") as f:
        recs = [json.loads(l) for l in f if l.strip()]
    return {r["signal"]["id"] for r in recs if "signal" in r}       # zaznamy momenta signal nemaji


def wait_until(target, what):
    print(f"\nCekam na {what} ({target:%Y-%m-%d %H:%M:%S} UTC)...")
    while (rem := (target - datetime.now(timezone.utc)).total_seconds()) > 0:
        time.sleep(min(30, rem))


def wait_for_next_bar():
    target = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1, seconds=5)
    wait_until(target, "dalsi H1 svicku")


def wait_for_momentum_hour():
    """Dalsi termin rozhodnuti momenta (pracovni den, 15:00 nebo 19:00 UTC). Vraci hodinu."""
    now = datetime.now(timezone.utc)
    hours = sorted({sm.decision_hour(s) for s in sm.UNIVERSE})
    day = now.replace(minute=0, second=30, microsecond=0)
    for add in range(8):
        d = day + timedelta(days=add)
        for h in hours:
            t = d.replace(hour=h)
            if t > now and t.weekday() < 5:
                wait_until(t, f"rozhodnuti momenta v {h}:00 UTC")
                return h
    raise RuntimeError("nenasel jsem dalsi termin")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["python", "webhook", "momentum"], default="python")
    ap.add_argument("--live", action="store_true", help="schvalene obchody poslat na DEMO ucet")
    ap.add_argument("--test-signal", metavar="SYMBOL:SMER", help="napr. EURUSD:long")
    ap.add_argument("--evaluate", action="store_true")
    ap.add_argument("--momentum-check", action="store_true", help="co by momentum udelalo dnes, nic nezapise")
    ap.add_argument("--evaluate-momentum", action="store_true")
    ap.add_argument("--port", type=int, default=8787)
    args = ap.parse_args()
    use_momentum = args.source == "momentum" or args.momentum_check

    mt5_connector.connect()
    try:
        if args.evaluate:
            shadow_eval.evaluate()
            return
        if args.evaluate_momentum:
            momentum.evaluate()
            return
        if args.momentum_check and args.live:
            print("--momentum-check je jen kontrola, s --live nejde.")
            return
        if args.live and not mt5_connector.is_demo_account():
            print("STOP: ucet NENI demo. Tenhle bot zatim obchoduje jen na demu.")
            return

        paper = not args.live
        offset = pipeline.detect_server_offset()
        starting_balance, challenge_start = load_state()
        rm = RiskManager(RiskConfig(starting_balance=starting_balance, risk_per_trade_pct=0.25,
                                    max_daily_loss_pct=4.0, max_total_drawdown_pct=8.0,
                                    profit_target_pct=8.0, max_trades_per_day=4, loss_cooldown_bars=5))
        symbols = SYMBOLS
        if args.test_signal:
            symbols = sorted(set(symbols) | {args.test_signal.split(":")[0].upper()})
        if use_momentum:
            symbols = sorted(set(symbols) | set(sm.UNIVERSE))
        for s in symbols:
            mt5_connector.mt5.symbol_select(s, True)            # bez Market Watch nejsou ceny
        pip_cache = {s: mt5_connector.get_pip_value_per_lot(s) for s in symbols}

        normals, markup = live_normals(load_normal_spreads(symbols), symbols)
        validator = ValidatorAgent(pip_cache)
        validator.seen = seen_ids()
        agents = [
            validator,
            MarketNowAgent(pip_cache, normals, server_offset_h=offset, holds_weekends={sm.SETUP}),
            StatisticianAgent(REGISTRY),
            RiskAgent(rm, starting_balance, challenge_start),
        ]
        print(f"Rezim: {'DEMO obchody' if args.live else 'PAPER (nic se neposila)'} | "
              f"cas serveru = UTC{offset:+d} | agenti: {', '.join(a.name for a in agents)}")

        def handle(sig):
            if sig.symbol not in pip_cache:
                print(f"\n[{sig.symbol}] symbol neni v seznamu sledovanych ({', '.join(pip_cache)}) - preskakuji")
                return
            try:
                pipeline.process(sig, agents, rm, pip_cache, paper=paper, server_offset_h=offset, markup=markup)
            except Exception as e:          # jeden spatny signal nesmi shodit bota
                print(f"\nCHYBA pri zpracovani {sig.id}: {e}")

        if args.test_signal:
            sym, direction = args.test_signal.split(":")
            sym, direction = sym.upper(), direction.lower()
            bid, ask, _ = mt5_connector.get_current_prices(sym)
            now = datetime.now(timezone.utc)
            handle(Signal(id=f"test-{sym}-{now.isoformat()}", symbol=sym, direction=direction,
                          setup="test", price=ask if direction == "long" else bid,
                          time=now, source="test"))
            print(f"\nZapsano do {pipeline.JOURNAL}")
            return

        if args.momentum_check:
            book = momentum.load_book()
            print(f"\nKONTROLNI BEH momenta: {len(sm.UNIVERSE)} trhu, riziko na trh {sm.risk_pct():.2f} % "
                  f"pri pojistnem SL {sm.DISASTER_SL_SIGMA} sigma. Nic se nezapise ani neposle.")
            print(f"Kniha: strategie drzi {sum(1 for v in book['strategie'].values() if v['dir'])} trhu, "
                  f"schvalenych pozic {len(book['schvalene'])}")
            momentum.decide(sm.UNIVERSE, agents, rm, pip_cache, paper=True, server_offset_h=offset,
                            markup=markup, dry=True)
            return

        if args.source == "momentum":
            print(f"Momentum: {len(sm.UNIVERSE)} trhu, rozhodnuti v pracovni dny 15:00 a 19:00 UTC  (Ctrl+C = konec)")
            while True:
                hour = wait_for_momentum_hour()
                syms = [s for s in sm.UNIVERSE if sm.decision_hour(s) == hour]
                print(f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC] momentum: {len(syms)} trhu")
                try:
                    momentum.decide(syms, agents, rm, pip_cache, paper=paper, server_offset_h=offset, markup=markup)
                except Exception as e:      # vypadek Yahoo / MT5 nesmi shodit bota, zkusi se pristi termin
                    print(f"CHYBA momenta: {e}")

        if args.source == "webhook":
            secret = os.environ.get("TV_WEBHOOK_SECRET")
            if not secret:
                print("CHYBI TV_WEBHOOK_SECRET. Nastav si ho sam (nikomu ho neposilej), napr. v PowerShellu:")
                print('   $env:TV_WEBHOOK_SECRET = "<dlouhy-nahodny-retezec>"')
                return
            q = queue.Queue()
            sources.start_webhook(q, secret, port=args.port)
            print(f"Prijimac bezi na http://127.0.0.1:{args.port}/tv  (Ctrl+C = konec)")
            while True:
                try:
                    handle(q.get(timeout=1))
                except queue.Empty:
                    pass

        print(f"Setupy: {', '.join(f'{s} {n}' for s, _, n in SETUPS)}  (Ctrl+C = konec)")
        while True:
            wait_for_next_bar()
            print(f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC] kontroluji uzavrenou svicku")
            for sig in sources.python_signals(SETUPS, server_offset_h=offset):
                handle(sig)
    except KeyboardInterrupt:
        print("\nPreruseno (Ctrl+C).")
    finally:
        mt5_connector.disconnect()


if __name__ == "__main__":
    try:
        main()
    except mt5_connector.MT5ConnectionError as e:
        print(f"\nCHYBA: {e}")
        raise SystemExit(1)
