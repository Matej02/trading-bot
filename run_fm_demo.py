"""
Live test FM strategii (F12-F16) na MT5 DEMO uctu primo z overeneho Python kodu testu (stejne signaly jako simulator,
shoda TS/Python 19/21, 49/49, 33/34, 7/11 pri stejne historii, 35/35).

Kazdou minutu: stahne z MT5 posledni M1 (75 dni) a H1 (6500), prevede cas serveru (Londyn) na UTC jako testy, spocita
kandidaty signalu kazde strategie a pokud nejaky vznikl na prave uzavrene svicce, posle na DEMO market order se SL/TP.
Pojistky: obchoduje JEN kdyz MT5 hlasi ucet jako DEMO (jinak konec), SL >= 3x spread, riziko 0,25 % zustatku na obchod,
jedna pozice na strategii a trh, casove vystupy jako v testu (intradenni do 22:00 Praha, F15 nejdyl 10 dni).
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

LIVE_DIR = os.path.join(ROOT, "scratch", "live_mt5")
os.makedirs(LIVE_DIR, exist_ok=True)
JOURNAL = os.path.join(ROOT, "fm_demo_journal.jsonl")
STATE = os.path.join(ROOT, "fm_demo_state.json")
RISK_PCT = 0.25
SL_MIN_SPREADS = 3
M1_DAYS = 75
F12.KS = (1.5,)                      # live jen vybrana varianta (k = 1,5)

STRATS = {
    "F12_mucka": dict(magic=20261112, tf=60, markets=["EURUSD", "GBPUSD", "XAUUSD", "XAGUSD", "NAS100mini"], intraday=True),
    "F13_ves": dict(magic=20261113, tf=60, markets=["NAS100mini", "SPX500mini", "EURUSD", "GBPUSD", "XAUUSD"], intraday=True),
    "F14_pat": dict(magic=20261114, tf=900, markets=["NAS100mini", "GBPUSD", "XAUUSD"], intraday=True),
    "F15_hve": dict(magic=20261115, tf=3600, markets=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
                                                     "XAUUSD", "XAGUSD", "CRUDE_OIL", "NAS100mini", "SPX500mini"], intraday=False, hold_days=10),
    "F16_hak": dict(magic=20261116, tf=900, markets=["XAUUSD", "XAGUSD"], intraday=True),
}


def log(*a):
    print(datetime.now().strftime("%H:%M:%S"), *a, flush=True)


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
def fetch_m1(mk):
    r = mt5.copy_rates_from_pos(mk, mt5.TIMEFRAME_M1, 0, M1_DAYS * 1440)
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


CAND = {"F12_mucka": cand_f12, "F13_ves": cand_f13, "F14_pat": cand_f14, "F15_hve": cand_f15, "F16_hak": cand_f16}


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
                if cfg["intraday"] and (h >= 22.0 or today != od):
                    why = "konec dne 22:00 (jako test)"
                if not cfg["intraday"] and now - p.time > cfg["hold_days"] * 86400 + 3 * 3600:
                    why = f"max {cfg['hold_days']} dni"
                if why:
                    if live:
                        mc.close_position(p, comment=f"{name}-cas"[:31], dry_run=False)
                    journal(dict(strategy=name, market=mk, action="zavreno" if live else "suchy beh zavreni", ticket=p.ticket, why=why))
                    log(f"  <<< {name} {mk} zavreno: {why}")


# ---------------------------------------------------------------- hlavni smycka
def due(name, now):
    """Kdy ma smysl strategii pocitat (na uzavreni jeji svicky)."""
    tf = STRATS[name]["tf"]
    sec = int(now) % 86400
    if tf == 60:
        h, _ = prague_hour(now)
        return 7.9 <= h < 17.6                             # F12/F13 killzones (8-11:30, 9-11, 13:30-17)
    if tf == 900:
        return sec % 900 < 75
    return sec % 3600 < 75


def cycle(state, live, force=False):
    now = time.time()
    seen = set(state["seen"])
    time_exits(live)
    todo = {n for n in STRATS if force or due(n, now)}
    if not todo:
        return
    clear_caches()
    mks = sorted({m for n in todo for m in STRATS[n]["markets"]})
    last_m1 = {}
    for mk in mks:
        try:
            mt5.symbol_select(mk, True)
            last_m1[mk] = fetch_m1(mk)
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
        log(f"kontrola {', '.join(sorted(todo))} na {len(last_m1)}/{len(mks)} trzich | otevrenych pozic {n_pos}")


def main():
    live = "--live" in sys.argv
    once = "--once" in sys.argv
    mc.connect()
    if not mc.is_demo_account():
        raise SystemExit("Ucet v MT5 neni DEMO - live test FM strategii bezi jen na demu. Konec.")
    log(f"FM demo runner {'LIVE NA DEMU' if live else 'SUCHY BEH'} | strategie: {', '.join(STRATS)} | riziko {RISK_PCT} %")
    state = load_state()
    if once:
        cycle(state, live, force=True)
        return
    while True:
        try:
            cycle(state, live)
        except SystemExit:
            raise
        except Exception as e:
            log("chyba cyklu:", e)
            traceback.print_exc(limit=2)
        time.sleep(60 - time.time() % 60 + 8)   # 8 s po uzavreni minuty


if __name__ == "__main__":
    main()
