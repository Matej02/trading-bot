"""
Live test FM strategii (F12-F16) a obecne strategie uzivatele (F20) na MT5 DEMO uctu primo z overeneho Python kodu testu (stejne signaly jako simulator,
shoda TS/Python 19/21, 49/49, 33/34, 7/11 pri stejne historii, 35/35).

Kazdou minutu: stahne z MT5 posledni M1 (75 dni) a H1 (6500), prevede cas serveru (Londyn) na UTC jako testy, spocita
kandidaty signalu kazde strategie a pokud nejaky vznikl na prave uzavrene svicce, posle na DEMO market order se SL/TP.
Pojistky: obchoduje JEN kdyz MT5 hlasi ucet jako DEMO (jinak konec), SL >= 3x spread, riziko 0,25 % zustatku na obchod,
jedna pozice na strategii a trh, casove vystupy (intradenni do 19:45 Praha - PC se vecer vypina, test 22:00; F15 nejdyl 10 dni).
Denik: fm_demo_journal.jsonl, stav: fm_demo_state.json (vse v D:\\Trading bot).

Spusteni:  py run_fm_demo.py            (suchy beh: jen vypise, co by udelal)
           py run_fm_demo.py --live     (posila prikazy na DEMO ucet)
           py run_fm_demo.py --once     (jeden cyklus a konec)
"""
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = r"D:\Trading bot"
os.chdir(ROOT)
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8")
import mt5_connector as mc  # noqa: E402

mt5 = mc.mt5
import research_f8 as F  # noqa: E402
import research_f10 as X  # noqa: E402
import research_f12 as F12  # noqa: E402
import research_f13_ves as V13  # noqa: E402
import research_f14_pat as V14  # noqa: E402
import research_f15_hve as V15  # noqa: E402
import research_f16_hak as V16  # noqa: E402
import research_f20_user as V20  # noqa: E402
import f2x_live as FX  # noqa: E402

LIVE_DIR = os.path.join(ROOT, "scratch", "live_mt5")
os.makedirs(LIVE_DIR, exist_ok=True)
JOURNAL = os.path.join(ROOT, "fm_demo_journal.jsonl")
STATE = os.path.join(ROOT, "fm_demo_state.json")
RISK_PCT = 0.25
SL_MIN_SPREADS = 3
M1_DAYS = 75
# uzivatel vypina PC kolem 20:00 (2026-11-05) -> intradenni obchody zavrit pred vypnutim, nove jen do 19:00 (test: 22:00)
INTRADAY_CLOSE_H = 19.75
INTRADAY_LAST_OPEN_H = 19.0
M1_DAYS_F20 = 180                    # 4H struktura F20 se ustali az od ~180 dni historie (SPX500: 75 d 36/50, 180 d 50/50)
F12.KS = (1.5,)                      # live jen vybrana varianta (k = 1,5)

STRATS = {
    "F12_mucka": dict(magic=20261112, tf=60, markets=["EURUSD", "GBPUSD", "XAUUSD", "XAGUSD", "NAS100mini"], intraday=True),
    "F13_ves": dict(magic=20261113, tf=60, markets=["NAS100mini", "SPX500mini", "EURUSD", "GBPUSD", "XAUUSD"], intraday=True),
    "F14_pat": dict(magic=20261114, tf=900, markets=["NAS100mini", "GBPUSD", "XAUUSD"], intraday=True),
    "F15_hve": dict(magic=20261115, tf=3600, markets=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
                                                     "XAUUSD", "XAGUSD", "CRUDE_OIL", "NAS100mini", "SPX500mini"], intraday=False, hold_days=10),
    "F16_hak": dict(magic=20261116, tf=900, markets=["XAUUSD", "XAGUSD"], intraday=True),
    "F20_user": dict(magic=20261120, tf=900, markets=["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "NAS100mini", "SPX500mini",
                                                      "GER_30mini"], intraday=True),   # obecna strategie uzivatele (F20)
    # vyzkum F22-F33 (2026-11-09): vlastni casovani v cycle_f2x / time_exits, ne pres CAND (custom=True)
    "F33_rebal": dict(magic=20261133, tf=60, markets=["SPX500mini", "NAS100mini"], intraday=False, hold_days=8, custom=True),
    "F31_fomc": dict(magic=20261131, tf=60, markets=["SPX500mini", "NAS100mini"], intraday=False, hold_days=3, custom=True),
    "F29_krypto": dict(magic=20261129, tf=60, markets=["BTCUSD", "ETHUSD"], intraday=False, hold_days=8, custom=True),
}


LOGFILE = os.path.join(ROOT, "fm_demo_log.txt")


def log(*a):
    s = " ".join(str(x) for x in (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),) + a)
    print(s, flush=True)
    try:
        with open(LOGFILE, "a", encoding="utf-8") as f:
            f.write(s + "\n")
    except OSError:
        pass


def journal(rec):
    rec["logged"] = datetime.now(timezone.utc).isoformat()
    with open(JOURNAL, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=float) + "\n")


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {"seen": []}


def save_state(s):
    s["seen"] = s["seen"][-3000:]
    json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)


# ---------------------------------------------------------------- data z MT5 ve formatu testu
def fetch_m1(mk, days=M1_DAYS):
    r = mt5.copy_rates_from_pos(mk, mt5.TIMEFRAME_M1, 0, days * 1440)
    if r is None or len(r) < 5000:
        raise RuntimeError(f"M1 {mk}: malo dat ({0 if r is None else len(r)})")
    df = pd.DataFrame(r).drop_duplicates("time").sort_values("time")
    srv = pd.to_datetime(df.time, unit="s").dt.tz_localize("Europe/London", ambiguous="NaT", nonexistent="shift_forward")
    df = df[srv.notna()].copy()
    df["t"] = srv[srv.notna()].dt.tz_convert("UTC").dt.tz_localize(None).astype("datetime64[s]").astype(np.int64)
    df = df.rename(columns={"open": "o", "high": "h", "low": "l", "close": "c", "tick_volume": "v"})[["t", "o", "h", "l", "c", "v"]]
    df = df.iloc[:-1].astype({"v": float}).reset_index(drop=True)          # posledni svicka se jeste tvori
    df.to_pickle(os.path.join(LIVE_DIR, f"{mk}_M1.pkl"))
    return int(df.t.iloc[-1])


def fetch_h1(mk):
    r = mt5.copy_rates_from_pos(mk, mt5.TIMEFRAME_H1, 0, 6500)
    if r is None or len(r) < 2000:
        raise RuntimeError(f"H1 {mk}: malo dat")
    df = pd.DataFrame(r)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("time")[["open", "high", "low", "close", "tick_volume"]].astype(float).iloc[:-1]
    df.to_pickle(os.path.join(LIVE_DIR, f"{mk}_H1.pkl"))


_orig_load = F.load


def live_load_h1(mk):
    cwd = os.getcwd()
    try:
        os.chdir(LIVE_DIR)
        os.makedirs("research_data", exist_ok=True)
        src = os.path.join(LIVE_DIR, f"{mk}_H1.pkl")
        dst = os.path.join(LIVE_DIR, "research_data", f"{mk}_H1.pkl")
        if os.path.exists(src):
            os.replace(src, dst)
        return _orig_load(mk)
    finally:
        os.chdir(cwd)


X.D10 = LIVE_DIR                     # X.load1 cte M1 z live slozky
F.load = live_load_h1                # F.load (F15) cte H1 z live slozky


def clear_caches():
    for c in (F12._CACHE, V13._C, V14._C, V15._C, V16._C):
        c.clear()


# ---------------------------------------------------------------- kandidati signalu (stejna logika jako kontrola shody)
def cand_f12(mk):
    P = F12.prep(mk)
    M, T, cz, D = P["M"], P["T"], P["cz"], P["D"]
    k = 1.5
    Xb = T["M1"]
    ev = P["S"][k]["M1"]["ev"]
    S4 = P["S"][k]["H4"]
    t = M["t"]
    n = len(t)
    out = []
    for q in range(max(1, len(ev["i"]) - 400), len(ev["i"])):
        if not ev["flip"][q]:
            continue
        d = int(ev["d"][q])
        if ev["d"][q - 1] != -d:
            continue
        sti, bp = int(ev["sti"][q]), int(ev["brk"][q - 1])
        if not (bp <= sti <= bp + 60):
            continue
        ic = int(Xb["en"][ev["i"][q]])
        kz = [w for w in F12.KZ if w[0] <= cz[ic] < w[1]]
        if not kz:
            continue
        kD = int(P["dmap"][ic])
        if kD < 2 or P["bm"][kD] != d:
            continue
        k4 = int(P["c4"][ic])
        if k4 < 1 or S4["tr"][k4] != d:
            continue
        b4 = int(S4["bos_i"][k4])
        if b4 < 0 or t[ic] - t[int(T["H4"]["en"][b4])] > 30 * 86400:
            continue
        sv = float(ev["st"][q])
        if not F12.in_poi(P, k, "obe", d, sv, int(Xb["en"][sti])):
            continue
        ext = M["h"][sti:ic + 1].max() if d == 1 else M["l"][sti:ic + 1].min()
        touch = -1
        for i in range(ic + 1, n):
            if not (kz[0][0] <= cz[i] < kz[0][1]):
                break
            lvl = ext - d * 0.618 * abs(ext - sv)
            if (d == 1 and M["l"][i] <= lvl) or (d == -1 and M["h"][i] >= lvl):
                touch = i
                break
            if (d == 1 and M["l"][i] < sv) or (d == -1 and M["h"][i] > sv):
                break
            ext = max(ext, M["h"][i]) if d == 1 else min(ext, M["l"][i])
        if touch < 0:
            continue
        aD = D["a"][kD - 1]
        px = M["c"][touch]
        fx = mk in ("EURUSD", "GBPUSD")
        mn, mx = (6 * M["pip"], 15 * M["pip"]) if fx else (0.086 * aD, 0.21 * aD)
        sl, risk = sv, (px - sv) * d
        if risk <= 0:
            continue
        if risk < mn:
            sl, risk = px - d * mn, mn
        if risk > mx:
            continue
        out.append((int(t[touch]) + 60, d, float(sl), float(px + d * 2.5 * risk)))
    return out


def cand_f13(mk):
    rows = V13.run_market(mk, dict(tf="M1", lvl="liq", entry="ob50", tp="tp2", parity=True))
    news = X.news_days()
    return [(int(r[0]) + 60, int(r[1]), float(r[2]), float(r[3])) for r in rows if (r[0] // 86400) not in news]


def cand_f14(mk):
    rows = V14.run_market(mk, dict(model="A", tf="M15", sess="full", tp="zona", parity=True))
    return [(int(r[0]) + 900, int(r[1]), float(r[2]), float(r[3])) for r in rows]


def cand_f15(mk):
    rows = V15.run_market(mk, dict(tf="den", base=3, dvw=1, lnl=1, entry="limit", cot="0", parity=True))
    return [(int(r[0]) + 3600, int(r[1]), float(r[2]), float(r[3])) for r in rows]


def cand_f16(mk):
    rows = V16.run_market(mk, dict(vlna=4, konf="fvg", entry="potvrz", sl="zona", tp="loc", parity=True))
    return [(int(r[0]) + 900, int(r[1]), float(r[2]), float(r[3])) for r in rows]


def cand_f20(mk):
    return V20.live_signals(mk)


CAND = {"F12_mucka": cand_f12, "F13_ves": cand_f13, "F14_pat": cand_f14, "F15_hve": cand_f15, "F16_hak": cand_f16,
        "F20_user": cand_f20}


def prague_hour(ts):
    z = pd.Timestamp(ts, unit="s", tz="UTC").tz_convert("Europe/Prague")
    return z.hour + z.minute / 60, z.date()


# ---------------------------------------------------------------- prikazy
def lots_for(mk, d, entry, sl, balance):
    si = mt5.symbol_info(mk)
    otype = mt5.ORDER_TYPE_BUY if d == 1 else mt5.ORDER_TYPE_SELL
    loss1 = mt5.order_calc_profit(otype, mk, 1.0, entry, sl)
    if not loss1 or loss1 >= 0:
        return None, None
    risk_money = balance * RISK_PCT / 100
    raw = risk_money / -loss1
    step = si.volume_step or 0.01
    lots = np.floor(raw / step + 1e-9) * step
    if lots < si.volume_min:
        return None, raw
    return round(min(lots, si.volume_max), 8), raw


def open_trade(name, mk, d, sl, tp, sig_t, live):
    cfg = STRATS[name]
    if not mc.is_demo_account():
        raise SystemExit("UCET NENI DEMO - konec, nic se neposila.")
    if mc.get_open_positions(mk, magic=cfg["magic"]):
        return "uz otevreno"
    if live and not algo_on():
        return ALGO_OFF
    if cfg["intraday"] and prague_hour(time.time())[0] >= INTRADAY_LAST_OPEN_H:
        return f"po {int(INTRADAY_LAST_OPEN_H)}:00 se intradenni obchod neotvira (PC se vecer vypina)"
    tick = mt5.symbol_info_tick(mk)
    si = mt5.symbol_info(mk)
    if tick is None or si is None:
        return "bez ceny"
    entry = tick.ask if d == 1 else tick.bid
    spread = tick.ask - tick.bid
    dist = (entry - sl) * d
    if dist <= 0 or (tp - entry) * d <= 0:
        return f"cena uz za SL/TP (vstup {entry}, SL {sl}, TP {tp})"
    if dist < SL_MIN_SPREADS * spread:
        return f"SL jen {dist / spread:.1f}x spread"
    bal = mt5.account_info().balance
    lots, raw = lots_for(mk, d, entry, sl, bal)
    if not lots:
        return f"velikost {raw} pod minimem brokera" if raw else "nelze spocitat velikost"
    digits = si.digits
    sl_r, tp_r = round(sl, digits), round(tp, digits)
    rec = dict(strategy=name, market=mk, dir="long" if d == 1 else "short", signal_t=sig_t, entry_ref=entry, sl=sl_r, tp=tp_r,
               lots=lots, spread=spread, rr=round((tp - entry) * d / dist, 2), live=live)
    if live:
        res = mc.place_market_order(mk, "long" if d == 1 else "short", lots, sl_r, tp_r, comment=name[:31], dry_run=False,
                                    magic=cfg["magic"])
        rec.update(action="provedeno", ticket=getattr(res, "order", None), fill=getattr(res, "price", None))
    else:
        rec.update(action="suchy beh")
    journal(rec)
    log(f"  >>> {name} {mk} {rec['dir']} {lots} lot @ {entry} SL {sl_r} TP {tp_r} (RR {rec['rr']}) - {rec['action']}")
    return rec["action"]


def time_exits(live):
    now = time.time()
    h, today = prague_hour(now)
    for name, cfg in STRATS.items():
        for mk in cfg["markets"]:
            for p in mc.get_open_positions(mk, magic=cfg["magic"]):
                _, od = prague_hour(p.time_msc / 1000 if p.time_msc else p.time)
                why = None
                if cfg["intraday"] and (h >= INTRADAY_CLOSE_H or today != od):
                    why = f"konec dne {int(INTRADAY_CLOSE_H)}:{int(INTRADAY_CLOSE_H % 1 * 60):02d} (PC se vecer vypina; test 22:00)"
                if not cfg["intraday"] and now - p.time > cfg["hold_days"] * 86400 + 3 * 3600:
                    why = f"max {cfg['hold_days']} dni"
                if cfg.get("custom"):                              # vystupy F33 / F31 / F29 (cas serveru = UTC)
                    ou, nu = datetime.fromtimestamp(p.time, timezone.utc), datetime.fromtimestamp(now, timezone.utc)
                    if name == "F33_rebal" and FX.f33_exit_due(ou, nu):
                        why = "konec mesice 15:55 NY (F33)"
                    elif name == "F31_fomc" and FX.f31_exit_due(ou, nu):
                        why = "den FOMC 13:55 NY - pred oznamenim (F31)"
                    elif name == "F29_krypto" and FX.f29_exit_due(ou, nu):
                        why = "tyden uplynul - pondeli (F29)"
                if why:
                    if live:
                        mc.close_position(p, comment=f"{name}-cas"[:31], dry_run=False)
                    journal(dict(strategy=name, market=mk, action="zavreno" if live else "suchy beh zavreni", ticket=p.ticket, why=why))
                    log(f"  <<< {name} {mk} zavreno: {why}")


# ---------------------------------------------------------------- hlavni smycka
def due(name, now):
    """Kdy ma smysl strategii pocitat (na uzavreni jeji svicky)."""
    if STRATS[name].get("custom"):
        return False                                       # F33/F31/F29 resi cycle_f2x
    tf = STRATS[name]["tf"]
    sec = int(now) % 86400
    if tf == 60:
        h, _ = prague_hour(now)
        return 7.9 <= h < 17.6                             # F12/F13 killzones (8-11:30, 9-11, 13:30-17)
    if tf == 900:
        return sec % 900 < 75
    return sec % 3600 < 75


def ensure_connected():
    """Po uspani PC nebo restartu terminalu se MT5 pripoji znovu (a znovu se overi, ze je ucet DEMO)."""
    if mt5.terminal_info() is not None and mt5.account_info() is not None:
        return
    log("MT5 odpojeno - pripojuji znovu")
    mc.connect()
    if not mc.is_demo_account():
        raise SystemExit("Ucet v MT5 neni DEMO - live test FM strategii bezi jen na demu. Konec.")


_MUTEX = None
ALGO_OFF = "v MT5 je vypnute Algoritmicke obchodovani (tlacitko v horni liste) - prikaz by broker odmitl"


def algo_on():
    ti = mt5.terminal_info()
    return bool(ti is not None and ti.trade_allowed)


_POPUP_AT = {}


def popup(msg, key, every_s=3600):
    """Vyskakovaci okno s upozornenim (neblokuje runner), stejny problem nejvys jednou za hodinu."""
    if os.name != "nt" or time.time() - _POPUP_AT.get(key, 0) < every_s:
        return
    _POPUP_AT[key] = time.time()
    import ctypes
    import threading
    threading.Thread(target=lambda: ctypes.windll.user32.MessageBoxW(None, msg, "FM demo live - POZOR", 0x30 | 0x40000),
                     daemon=True).start()


def single_instance():
    """Jen jedna bezici instance (dve by zdvojily prikazy). Windows mutex zmizi sam s koncem procesu."""
    global _MUTEX
    if os.name != "nt":
        return
    import ctypes
    k32 = ctypes.windll.kernel32
    _MUTEX = k32.CreateMutexW(None, False, "Local\\fm_demo_runner")
    if k32.GetLastError() == 183:          # ERROR_ALREADY_EXISTS
        raise SystemExit("Runner uz bezi v jinem okne - druha instance konci.")


def d1_closes_atr(mk, n=60):
    """Denni svicky z MT5 (cas serveru = UTC): {datum: close} uzavrenych dni a ATR20 (bez rozpracovaneho dne)."""
    r = mt5.copy_rates_from_pos(mk, mt5.TIMEFRAME_D1, 0, n)
    if r is None or len(r) < 25:
        return None, None
    df = pd.DataFrame(r).iloc[:-1]
    pc = df.close.shift(1)
    tr = np.maximum(df.high - df.low, np.maximum((df.high - pc).abs(), (df.low - pc).abs()))
    closes = {datetime.fromtimestamp(int(t), timezone.utc).date(): float(c) for t, c in zip(df.time, df.close)}
    return closes, float(tr.iloc[-20:].mean())


def f2x_open(state, name, mk, d, live, why, key):
    """Vstup F33/F31/F29: SL 3 ATR20 (pojistka), TP daleko (10 R) - v testech bez stopu a TP."""
    state["seen"].append(key)
    _, a = d1_closes_atr(mk)
    tick = mt5.symbol_info_tick(mk)
    if not a or tick is None:
        log(f"  {name} {mk}: chybi data pro ATR/cenu - nevstupuji")
        return
    entry = tick.ask if d == 1 else tick.bid
    sl = entry - d * 3 * a
    tp = entry + d * 30 * a
    log(f"SIGNAL {name} {mk} {'long' if d == 1 else 'short'} - {why}")
    res = open_trade(name, mk, d, sl, tp, int(time.time()), live)
    if res not in ("provedeno", "suchy beh"):
        journal(dict(strategy=name, market=mk, dir="long" if d == 1 else "short", signal_t=int(time.time()), action="neprovedeno", why=res))
        log(f"  --- neprovedeno: {res}")


def cycle_f2x(state, live):
    """F33 rebalancovani, F31 drift pred FOMC, F29 krypto momentum - casovani podle f2x_live (cista rozhodnuti)."""
    now = datetime.now(timezone.utc)
    seen = set(state["seen"])
    nyd = now.astimezone(FX.NY).date()
    # F33: 9:30-9:40 NY dne L-2
    key33 = f"F33_rebal|{nyd:%Y-%m}"
    if key33 not in seen and FX.is_trading_day(nyd) and FX.trading_days_left(nyd) == 2:
        if FX.ny_dt(nyd, 9, 30) <= now.astimezone(FX.NY) < FX.ny_dt(nyd, 9, 40):
            r = FX.f33_entry(now, FX.yahoo_adjclose("SPY"), FX.yahoo_adjclose("TLT"))
            if r and r[0] in (1, -1):
                for mk in STRATS["F33_rebal"]["markets"]:
                    f2x_open(state, "F33_rebal", mk, r[0], live, r[1], f"{key33}|{mk}")
                state["seen"].append(key33)
            elif r:
                log(f"  {r[1]}")
                if r[0] == "nic":
                    state["seen"].append(key33)
    # F31: 14:00-14:10 NY v posledni obchodni den pred FOMC
    if FX.f31_entry(now):
        for mk in STRATS["F31_fomc"]["markets"]:
            k = f"F31_fomc|{nyd}|{mk}"
            if k not in seen:
                f2x_open(state, "F31_fomc", mk, 1, live, f"zitra ({FX.next_trading_day(nyd)}) rozhoduje FOMC, ven 13:55 NY", k)
    # F29: v pondeli (UTC), jednou za tyden a trh
    if now.weekday() == 0:
        for mk in STRATS["F29_krypto"]["markets"]:
            k = f"F29_krypto|{now:%Y-%m-%d}|{mk}"
            if k in seen:
                continue
            mt5.symbol_select(mk, True)
            closes, _ = d1_closes_atr(mk)
            sig = FX.f29_signal(closes or {}, now)
            if sig is None:
                continue
            if sig[0] > 0:
                f2x_open(state, "F29_krypto", mk, 1, live, sig[1] + " > 0 -> long na tyden", k)
            else:
                state["seen"].append(k)
                log(f"  {sig[1]} <= 0 -> F29 {mk} tento tyden mimo trh")
    if now.date() > FX.LAST_FOMC and int(now.timestamp()) % 86400 < 60:     # jednou denne
        log("POZOR: dosly terminy FOMC v f2x_live.py - doplnit dalsi rok")


def cycle(state, live, force=False):
    now = time.time()
    seen = set(state["seen"])
    ensure_connected()
    time_exits(live)
    try:
        cycle_f2x(state, live)
    except Exception as e:                                 # chyba F33/F31/F29 nesmi zastavit FM strategie
        log(f"  F2x: chyba {e}")
    todo = {n for n in STRATS if not STRATS[n].get("custom") and (force or due(n, now))}
    if not todo:
        return
    clear_caches()
    mks = sorted({m for n in todo for m in STRATS[n]["markets"]})
    last_m1 = {}
    for mk in mks:
        try:
            mt5.symbol_select(mk, True)
            long_ = "F20_user" in todo and mk in STRATS["F20_user"]["markets"]
            last_m1[mk] = fetch_m1(mk, M1_DAYS_F20 if long_ else M1_DAYS)
            if "F15_hve" in todo and mk in STRATS["F15_hve"]["markets"]:
                fetch_h1(mk)
        except Exception as e:
            log(f"  data {mk}: {e}")
    for name in sorted(todo):
        cfg = STRATS[name]
        for mk in cfg["markets"]:
            if mk not in last_m1:
                continue
            try:
                cands = CAND[name](mk)
            except Exception as e:
                log(f"  {name} {mk}: chyba vypoctu {e}")
                traceback.print_exc(limit=1)
                continue
            bar_end = last_m1[mk] + 60          # konec posledni uzavrene M1 svicky (UTC)
            for (sig_end, d, sl, tp) in cands:
                key = f"{name}|{mk}|{sig_end}|{d}"
                if key in seen:
                    continue
                # jen cerstvy signal: vznikl na zavreni svicky v poslednich 3 minutach
                if not (bar_end - 180 <= sig_end <= bar_end):
                    continue
                seen.add(key)
                state["seen"].append(key)
                log(f"SIGNAL {name} {mk} {'long' if d == 1 else 'short'} (svicka do {pd.Timestamp(sig_end, unit='s')} UTC)")
                try:
                    why = open_trade(name, mk, d, sl, tp, sig_end, live)
                except SystemExit:
                    raise
                except Exception as e:
                    why = f"chyba prikazu: {e}"
                if why not in ("provedeno", "suchy beh"):
                    journal(dict(strategy=name, market=mk, dir="long" if d == 1 else "short", signal_t=sig_end, action="neprovedeno", why=why))
                    log(f"  --- neprovedeno: {why}")
    save_state(state)
    if int(now) % 900 < 60:                     # zivotni znamka kazdych 15 min, at je videt, ze runner bezi
        n_pos = sum(1 for n in STRATS for p in (mt5.positions_get() or []) if p.magic == STRATS[n]["magic"])
        log(f"kontrola {', '.join(sorted(todo))} na {len(last_m1)}/{len(mks)} trzich | otevrenych pozic {n_pos}"
            + ("" if algo_on() else " | POZOR: " + ALGO_OFF))
    if live and not algo_on():
        popup("V MT5 je vypnute Algoritmicke obchodovani.\n\nKlikni v MT5 v horni liste na 'Algoritmicke Obchodovani' "
              "(ikona musi byt zelena), jinak broker obchody z runneru odmitne.", "algo")
    if int(now) % 900 < 60:
        news_calendar_check()


def news_calendar_check():
    """Kalendar zprav (f7_lib FOMC/NFP/CPI) je rucne psany - bez novych terminu by filtr zprav potichu prestal fungovat."""
    import f7_lib as L
    last = min(max(L.FOMC), max(L.NFP), max(L.CPI))
    left = (pd.Timestamp(last) - pd.Timestamp.now(tz="UTC").tz_localize(None)).days
    if left < 45:
        msg = f"kalendar zprav (FOMC/NFP/CPI v f7_lib.py) konci {last} - doplnit dalsi terminy z bls.gov a federalreserve.gov"
        log("POZOR: " + msg)
        popup(msg, "news", every_s=86400)


def main():
    live = "--live" in sys.argv
    once = "--once" in sys.argv
    if live:
        single_instance()
    mc.connect()
    if not mc.is_demo_account():
        raise SystemExit("Ucet v MT5 neni DEMO - live test FM strategii bezi jen na demu. Konec.")
    log(f"FM demo runner {'LIVE NA DEMU' if live else 'SUCHY BEH'} | strategie: {', '.join(STRATS)} | riziko {RISK_PCT} %")
    if live and not algo_on():
        log("POZOR: " + ALGO_OFF)
    news_calendar_check()
    state = load_state()
    errs = 0
    if once:
        cycle(state, live, force=True)
        return
    while True:
        try:
            cycle(state, live)
            errs = 0
        except SystemExit:
            raise
        except Exception as e:
            errs += 1
            log("chyba cyklu:", e)
            traceback.print_exc(limit=2)
            if errs >= 5:
                popup(f"Runner {errs}x po sobe hlasi chybu:\n{e}\n\nZkontroluj, ze bezi MT5 a je pripojeny k internetu "
                      "(log: fm_demo_log.txt ve slozce Trading bot na disku D).", "errs")
        time.sleep(60 - time.time() % 60 + 8)   # 8 s po uzavreni minuty


if __name__ == "__main__":
    main()
