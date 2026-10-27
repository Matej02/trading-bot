"""
Momentum (strategy_momentum.py) v botovi.

Dve knihy v tv_momentum_book.json:
  strategie - smer, ktery by drzela samotna strategie (meni se jen pri zmene
              znamenka trendu)
  schvalene - co pustili agenti (paper: jen zapis, demo: skutecne pozice s MAGIC)

Signal vznika pri ZMENE smeru. Zavreni schvalene pozice jde bez veta (snizuje
riziko). Novy smer jde pres agenty jako kazdy jiny signal. Kdyz ho zamitne
docasny duvod (spread, rollover, limit obchodu za den), zkusi se dalsi dny
znovu (max 5x); zamitnuti statistikem plati az do dalsi zmeny smeru.

Kazda zmena smeru jde do deniku i s bid/ask, takze vysledek samotne strategie
bez agentu jde spocitat zpetne (evaluate) - stinovy test vuci schvalenym.
"""

import json
import os
from datetime import datetime, timedelta, timezone

import numpy as np

import mt5_connector
import strategy_momentum as sm
from tv_agent import pipeline
from tv_agent.signals import Signal

BOOK = "tv_momentum_book.json"
MAX_RETRIES = 5
FINAL_VETO = {"statistik"}            # tohle se do dalsi zmeny smeru nezmeni, nema smysl zkouset znovu


def load_book():
    if os.path.exists(BOOK):
        with open(BOOK, encoding="utf-8") as f:
            return json.load(f)
    return {"strategie": {}, "schvalene": {}}


def save_book(book):
    tmp = BOOK + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(book, f, indent=1, ensure_ascii=False)
    os.replace(tmp, BOOK)


def _money_per_price(symbol, price):
    mt5 = mt5_connector.mt5
    d = price * 0.001
    return (mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, symbol, 1.0, price, price + d) or 0) / d


def swap_money_per_night(symbol, direction, lots):
    """Swap za jednu noc v mene uctu (zaporne = platis). Pro paper pozice -
    na demu ho broker pocita sam."""
    si = mt5_connector.mt5.symbol_info(symbol)
    sw = si.swap_long if direction == "long" else si.swap_short
    if si.swap_mode in (1, 7, 8):                       # body
        money = sw * si.point * _money_per_price(symbol, si.bid)
    elif si.swap_mode in (2, 3, 4, 9):                  # penize na lot
        money = sw
    elif si.swap_mode in (5, 6):                        # rocni %
        money = si.bid * sw / 100 / 360 * _money_per_price(symbol, si.bid)
    else:
        money = 0.0
    return money * lots


def swap_nights(opened, closed, roll3_mt5):
    """Uctovane noci: kazdy pracovni den 1x, v den brokera 3x (MT5: 0 = nedele)."""
    roll3 = (roll3_mt5 - 1) % 7
    n, d = 0, opened.date()
    while d < closed.date():
        if d.weekday() < 5:
            n += 3 if d.weekday() == roll3 else 1
        d += timedelta(days=1)
    return n


def close_approved(s, pos, paper, now, dry):
    mt5 = mt5_connector.mt5
    bid, ask, _ = mt5_connector.get_current_prices(s)
    d = pos["dir"]
    if dry:
        print(f"   [{s}] zavrel bych schvalenou pozici {d} {pos['lots']} lotu (kontrolni beh)")
        return
    if paper:
        exit_px = bid if d == "long" else ask
        otype = mt5.ORDER_TYPE_BUY if d == "long" else mt5.ORDER_TYPE_SELL
        pnl = mt5.order_calc_profit(otype, s, pos["lots"], pos["entry"], exit_px) or 0.0
        nights = swap_nights(datetime.fromisoformat(pos["od"]), now, mt5.symbol_info(s).swap_rollover3days)
        swap = swap_money_per_night(s, d, pos["lots"]) * nights
    else:
        pnl = swap = 0.0
        exit_px = None
        for p in mt5_connector.get_open_positions(s, magic=sm.MAGIC):
            pnl += p.profit
            swap += p.swap
            _, exit_px = mt5_connector.close_position(p, comment=f"tv-{sm.SETUP}"[:31], dry_run=False)
    pipeline.journal_write({
        "typ": "momentum_zavreni", "logged": now.isoformat(), "symbol": s, "dir": d,
        "entry": pos["entry"], "exit": exit_px, "lots": pos["lots"], "pnl": pnl, "swap": swap,
        "od": pos["od"], "mode": "paper" if paper else "demo",
    })
    print(f"   [{s}] zavreno {d} {pos['lots']} lotu: {pnl:+.2f} + swap {swap:+.2f}")


def try_entry(s, st, close, book, agents, rm, pip_cache, paper, server_offset_h, markup, now, dry):
    direction = "long" if st["dir"] > 0 else "short"
    bid, ask, _ = mt5_connector.get_current_prices(s)
    price = ask if direction == "long" else bid
    sig = Signal(id=f"{sm.SETUP}-{s}-{now:%Y-%m-%d}", symbol=s, direction=direction, setup=sm.SETUP,
                 price=price, time=now, source="python",
                 sl=sm.disaster_sl(price, direction, sm.rel_vol(close)), tp=0.0)      # tp 0 = bez TP
    rec = pipeline.process(sig, agents, rm, pip_cache, paper=paper, server_offset_h=server_offset_h,
                           markup=markup, risk_pct=sm.risk_pct(), magic=sm.MAGIC, write=not dry)
    st["pokusy"] = st.get("pokusy", 0) + 1
    if rec["approved"]:
        book["schvalene"][s] = {"dir": direction, "entry": rec["entry_ref"], "lots": rec["lots"],
                                "ticket": rec["ticket"], "od": now.isoformat()}
        st["cekajici"] = False
        return
    vetoes = {v["agent"] for v in rec["verdicts"] if not v["approve"]}
    if vetoes & FINAL_VETO or st["pokusy"] >= MAX_RETRIES:
        st["cekajici"] = False


def decide(symbols, agents, rm, pip_cache, paper=True, server_offset_h=0, markup=None, dry=False):
    """Jedno denni rozhodnuti pro dane trhy. dry=True: nic nezapise, nic neposle."""
    now = datetime.now(timezone.utc)
    closes = sm.fetch_daily(symbols)
    if not closes:
        print("Yahoo neodpovedel - dnes zadne rozhodnuti, zkusi se pristi termin")
        return
    book = load_book()
    for s in symbols:
        c = closes.get(s)
        if c is None or len(c) < sm.LOOKBACK + 1:
            print(f"   [{s}] malo dat z Yahoo ({0 if c is None else len(c)} dni) - preskakuji")
            continue
        tgt = sm.target(c)
        st = book["strategie"].get(s, {"dir": 0})
        if tgt != st["dir"]:
            bid, ask, _ = mt5_connector.get_current_prices(s)
            ret = float(c.iloc[-1] / c.iloc[-1 - sm.LOOKBACK] - 1)
            print(f"\n[{s}] strategie meni smer {st['dir']:+d} -> {tgt:+d} (vynos za 250 dni {ret:+.1%})")
            if not dry:
                pipeline.journal_write({
                    "typ": "momentum_zmena", "logged": now.isoformat(), "symbol": s, "z": st["dir"], "na": tgt,
                    "bid": bid, "ask": ask, "vynos_250d": ret, "posledni_svicka": str(c.index[-1].date()),
                })
            pos = book["schvalene"].pop(s, None)
            if pos:
                close_approved(s, pos, paper, now, dry)
            st = {"dir": tgt, "od": now.isoformat(), "cekajici": tgt != 0, "pokusy": 0}
            book["strategie"][s] = st
        if st.get("cekajici") and s not in book["schvalene"]:
            try_entry(s, st, c, book, agents, rm, pip_cache, paper, server_offset_h, markup, now, dry)
    if not dry:
        save_book(book)


def evaluate():
    """Vysledek samotne strategie (stinove, z deniku) vs co pustili agenti."""
    recs = []
    if os.path.exists(pipeline.JOURNAL):
        with open(pipeline.JOURNAL, encoding="utf-8") as f:
            recs = [json.loads(l) for l in f if l.strip()]
    flips = [r for r in recs if r.get("typ") == "momentum_zmena"]
    if not flips:
        print("Momentum zatim nebezelo - v deniku nejsou zadne zmeny smeru.")
        return

    by_sym = {}
    for r in flips:
        by_sym.setdefault(r["symbol"], []).append(r)
    closed, opened = [], []
    for s, fl in by_sym.items():
        for a, b in zip(fl, fl[1:]):
            if a["na"]:
                entry = a["ask"] if a["na"] > 0 else a["bid"]
                exit_ = b["bid"] if a["na"] > 0 else b["ask"]
                closed.append(a["na"] * (exit_ / entry - 1))
        last = fl[-1]
        if last["na"]:
            bid, ask, _ = mt5_connector.get_current_prices(s)
            entry = last["ask"] if last["na"] > 0 else last["bid"]
            opened.append(last["na"] * ((bid if last["na"] > 0 else ask) / entry - 1))

    print("SAMOTNA STRATEGIE (bez agentu, stinove; vynos v % ceny vcetne spreadu, BEZ swapu):")
    if closed:
        x = np.array(closed)
        pf = x[x > 0].sum() / -x[x < 0].sum() if (x < 0).any() else float("inf")
        print(f"   uzavrenych {len(x)}: prumer {100 * x.mean():+.2f} %, win {100 * (x > 0).mean():.0f} %, PF {pf:.2f}")
    else:
        print("   zatim zadny uzavreny obchod (zmena smeru prichazi v radu tydnu az mesicu)")
    if opened:
        print(f"   otevrenych {len(opened)}: prumer {100 * np.mean(opened):+.2f} %")

    book = load_book()
    done = [r for r in recs if r.get("typ") == "momentum_zavreni"]
    print("\nCO PUSTILI AGENTI (v penezich, vcetne swapu):")
    print(f"   uzavrenych {len(done)}: {sum(r['pnl'] + r['swap'] for r in done):+.2f}")
    mt5 = mt5_connector.mt5
    mtm = 0.0
    for s, p in book["schvalene"].items():
        bid, ask, _ = mt5_connector.get_current_prices(s)
        otype = mt5.ORDER_TYPE_BUY if p["dir"] == "long" else mt5.ORDER_TYPE_SELL
        mtm += mt5.order_calc_profit(otype, s, p["lots"], p["entry"], bid if p["dir"] == "long" else ask) or 0.0
    print(f"   otevrenych {len(book['schvalene'])}: {mtm:+.2f} (bez swapu)")
    print("\nPozor: smysl to ma az po desitkach uzavrenych obchodu - u tehle strategie realne rok a vic.")
