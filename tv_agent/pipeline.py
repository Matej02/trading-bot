"""
Pipeline: signal -> vsichni agenti -> rozhodnuti -> (paper / demo obchod) -> denik.

Do deniku jde KAZDY signal vcetne zamitnutych, s referencni vstupni cenou
a SL/TP. shadow_eval.py pak dopocita, jak by dopadly - a teprve z toho
jde poznat, jestli agenti filtruji dobre, nebo jen nahodne.
"""

import json
import math
import time
from dataclasses import asdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import mt5_connector
from tv_agent.agents import Verdict
from tv_agent.sources import closed_h1

JOURNAL = "tv_journal.jsonl"
MAGIC = 20261026
SL_ATR, TP_ATR = 1.5, 2.5          # stejne jako backtestovane strategie


def journal_write(rec):
    with open(JOURNAL, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=float, ensure_ascii=False) + "\n")


def detect_server_offset(symbol="EURUSD") -> int:
    """Posun casu serveru brokera proti UTC v hodinach (server = UTC + posun).
    Zjisti se z cerstveho ticku; kdyz je trh zavreny, vraci 0 s varovanim."""
    tick = mt5_connector.mt5.symbol_info_tick(symbol)
    if tick is None:
        print("VAROVANI: nelze zjistit cas serveru, predpokladam UTC")
        return 0
    diff_h = (tick.time - datetime.now(timezone.utc).timestamp()) / 3600
    rounded = round(diff_h)
    if abs(diff_h - rounded) > 0.2:      # tick neni cerstvy (trh zavreny) -> neda se poznat
        print(f"VAROVANI: posledni tick neni cerstvy ({diff_h:+.2f} h), predpokladam UTC")
        return 0
    return int(rounded)


def measure_markup(symbol, samples=5):
    """O kolik pipu je ziva cena (za kterou se plni prikazy) sirsi nez historie ticku.

    U tohohle brokera se lisi: ve stejne vterine historie EURUSD 0.5 pipu,
    ziva cena 1.9 pipu (prirazka ~0.7 pipu na kazde strane). Svicky i historie
    ticku jsou ze surove ceny, takze normaly z historie se o tohle musi posunout.
    Vraci None, kdyz neni cerstvy tick (zavreny trh)."""
    mt5 = mt5_connector.mt5
    pip = mt5_connector.get_pip_value_per_lot(symbol)[0]
    diffs = []
    for _ in range(samples):
        live = mt5.symbol_info_tick(symbol)
        hist = mt5.copy_ticks_range(symbol, live.time - 120, live.time + 1, mt5.COPY_TICKS_INFO)
        if hist is not None and len(hist):
            same = hist[hist["time"] == live.time]
            if len(same):
                diffs.append(((live.ask - live.bid) - (same[-1]["ask"] - same[-1]["bid"])) / pip)
        time.sleep(0.5)
    return float(np.median(diffs)) if diffs else None


def _atr(symbol, server_offset_h=0) -> float:
    df = closed_h1(symbol, 30, server_offset_h)        # ATR(14) vic nepotrebuje
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - df["close"].shift()).abs(),
                    (df["low"] - df["close"].shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(14).mean().iloc[-1])


def ensure_levels(s, server_offset_h=0):
    """Doplni SL/TP, kdyz je signal (napr. z TradingView) neposlal."""
    if s.sl is not None and s.tp is not None:
        return
    atr = _atr(s.symbol, server_offset_h)
    if s.direction == "long":
        s.sl, s.tp = s.price - SL_ATR * atr, s.price + TP_ATR * atr
    else:
        s.sl, s.tp = s.price + SL_ATR * atr, s.price - TP_ATR * atr


def normalize_lots(symbol, lots):
    """Zaokrouhli dolu na krok brokera. None = pod minimem (pozice by musela byt
    vetsi a rizikovejsi, nez rika risk management)."""
    si = mt5_connector.mt5.symbol_info(symbol)
    step = si.volume_step or 0.01
    lots = math.floor(lots / step + 1e-9) * step
    if lots < si.volume_min:
        return None
    return round(min(lots, si.volume_max), 8)


def process(s, agents, rm, pip_cache, paper=True, server_offset_h=0, markup=None,
            risk_pct=None, magic=MAGIC, write=True) -> dict:
    """risk_pct: vlastni riziko setupu (jinak z RiskConfig), magic: cislo systemu na demu,
    write=False: nic nezapise do deniku (kontrolni beh)."""
    ensure_levels(s, server_offset_h)

    verdicts = []
    for a in agents:
        try:
            v = a.check(s)
        except Exception as e:                       # padly agent = veto, ne pad celeho bota
            v = Verdict(a.name, False, f"chyba agenta: {e}")
        verdicts.append(v)
    approved = all(v.approve for v in verdicts)

    pip_size, pip_val = pip_cache[s.symbol]
    bid, ask, sp = mt5_connector.get_current_prices(s.symbol)
    entry = ask if s.direction == "long" else bid
    action, ticket, lots = "zamitnuto", None, None

    if approved:
        raw = rm.position_size(abs(entry - s.sl), pip_val, pip_size, risk_pct_override=risk_pct)
        lots = normalize_lots(s.symbol, raw) if raw > 0 else None
        if not lots:
            approved = False
            verdicts.append(Verdict("velikost", False, f"velikost {raw:.4f} lotu je 0 nebo pod minimem brokera"))
        elif paper:
            action = "paper"
        else:
            res = mt5_connector.place_market_order(s.symbol, s.direction, lots, s.sl, s.tp,
                                                   comment=f"tv-{s.setup}"[:31], dry_run=False, magic=magic)
            action, entry, ticket = "provedeno", res.price, res.order

    rec = {
        "logged": datetime.now(timezone.utc).isoformat(),
        "signal": s.to_dict(),
        "approved": approved,
        "action": action,
        "mode": "paper" if paper else "demo",
        "entry_ref": entry,
        "spread_pips": sp / pip_size,
        "markup_pips": (markup or {}).get(s.symbol, 0.0),   # pro prepocet svicek na zivou cenu
        "lots": lots,
        "ticket": ticket,
        "server_offset_h": server_offset_h,
        "verdicts": [asdict(v) for v in verdicts],
    }
    if write:
        journal_write(rec)

    mark = "SCHVALENO" if approved else "ZAMITNUTO"
    print(f"\n[{s.symbol} {s.direction} {s.setup}] {mark} -> {action}")
    for v in verdicts:
        print(f"   {'OK ' if v.approve else 'VETO'} {v.agent:<10} {v.reason}")
    return rec
