"""
Prop runner pro FTMO (2 kroky, Swing) podle vaultu: Projekt/Navrh pravidel prop runneru.md (2026-11-25).
Samostatny program - demo runner run_fm_demo.py se nemeni. Obchoduje jen overene strategie F33 (se stopem 3 ATR) a RSI(2).

Pojistky:
  - obchoduje JEN na cisle uctu z prop_config.json a na serveru, jehoz nazev obsahuje server_contains (jinak konec);
  - denni pojistka: L = max(zustatek o pulnoci Praha - 5 % pocatecniho, 90 % pocatecniho); equity <= L + rezerva -> zavrit vse,
    do pulnoci (Praha) nic noveho;
  - pred vstupem: equity - riziko otevrenych pozic u SL - riziko noveho obchodu musi zustat nad pojistkou;
  - neaktivita (FTMO cl. 13.2.3): 27 dni bez noveho obchodu -> nejmensi lot na US500 a do minuty zavrit;
  - cil faze (+10 %, pak +5 %) a >= 4 obchodni dny -> zavrit vse a dal neobchodovat (upozorneni).
Heslo runner nikdy nezpracovava: MT5 terminal prihlasuje uzivatel rucne.

Spusteni:  py run_prop.py            (suchy beh: nic neposila, jen vypisuje)
           py run_prop.py --live     (posila prikazy, jen na uctu z configu)
           py run_prop.py --once     (jeden cyklus a konec)
"""
import json
import math
import os
import sys
import time
import traceback
import urllib.request
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import f2x_live as FX  # noqa: E402

PRAGUE = ZoneInfo("Europe/Prague")
NY = FX.NY
CONFIG = os.path.join(HERE, "prop_config.json")
STATE = os.path.join(HERE, "prop_state.json")
JOURNAL = os.path.join(HERE, "prop_journal.jsonl")
LOGFILE = os.path.join(HERE, "prop_log.txt")
NO_POPUP = False                           # testy

MAGIC = {"F33": 20270133, "RSI2": 20270142, "KEEPALIVE": 20270199}
F33_MARKETS = ["SPX500mini", "NAS100mini"]
RSI2_MARKETS = ["SPX500mini", "NAS100mini", "US30mini"]
YAHOO = FX.RSI2_YAHOO                      # vnitrni nazev -> index na Yahoo (^GSPC, ^NDX, ^DJI)


# ====================================================================== ciste funkce (testovane v test_run_prop.py)
def guard_levels(mid_balance, initial, day_pct=5.0, max_pct=10.0, margin_pct=2.0):
    """(limit FTMO dne L, uroven pojistky G). Vse v penezich uctu."""
    L = max(mid_balance - initial * day_pct / 100.0, initial * (1 - max_pct / 100.0))
    return L, L + initial * margin_pct / 100.0


def prague_midnight_utc(now_utc):
    p = now_utc.astimezone(PRAGUE)
    return datetime(p.year, p.month, p.day, tzinfo=PRAGUE).astimezone(timezone.utc)


def day_start_balance(balance, deals, since_utc, offset_s):
    """Zustatek o pulnoci Praha = dnesni zustatek - vysledky obchodu uzavrenych od pulnoci.
    deals: objekty s .time (cas serveru v s), .profit, .swap, .commission, .fee, .entry; offset_s = server - UTC."""
    since = since_utc.timestamp()
    done = 0.0
    for d in deals:                                   # vstupni i vystupni obchody (provize se uctuje i pri vstupu)
        if d.time - offset_s >= since:
            done += d.profit + d.swap + d.commission + getattr(d, "fee", 0.0)
    return balance - done


def trading_days(deals, phase_start, offset_s):
    """Pocet ruznych dni (Praha) se vstupem do obchodu od zacatku faze."""
    out = set()
    for d in deals:
        if getattr(d, "entry", 0) != 0:
            continue
        t = datetime.fromtimestamp(d.time - offset_s, timezone.utc).astimezone(PRAGUE).date()
        if t >= phase_start:
            out.add(t)
    return len(out)


def last_entry_utc(deals, offset_s, default):
    ts = [d.time - offset_s for d in deals if getattr(d, "entry", 0) == 0]
    return datetime.fromtimestamp(max(ts), timezone.utc) if ts else default


def keepalive_due(last_in_utc, now_utc, days=27):
    return (now_utc - last_in_utc) >= timedelta(days=days)


def target_reached(equity, initial, target_pct, n_days, min_days=4):
    if target_pct is None:
        return False
    return equity >= initial * (1 + target_pct / 100.0) - 1e-6 and n_days >= min_days


def size_lots(risk_money, loss_per_lot, step, vmin, vmax, minlot_mult=1.5):
    """Loty pro dane riziko u SL. Kdyz vyjde min nez nejmensi lot, vezme se nejmensi lot,
    pokud jeho riziko nepresahne minlot_mult x pozadovane. Jinak None."""
    if not loss_per_lot or loss_per_lot <= 0 or risk_money <= 0:
        return None
    raw = risk_money / loss_per_lot
    lots = math.floor(raw / step + 1e-9) * step
    if lots < vmin:
        return vmin if vmin * loss_per_lot <= risk_money * minlot_mult else None
    return round(min(lots, vmax), 8)


def server_offset_s(tick_time, now_ts, tz_name="Europe/Athens"):
    """Posun casu serveru proti UTC v s. Z ticku jen kdyz vyjde presne +2 h nebo +3 h (cerstvy tick, FTMO = GMT+2/+3),
    jinak podle casoveho pasma serveru z configu."""
    if tick_time:
        cand = int(round((tick_time - now_ts) / 3600.0)) * 3600
        if cand in (7200, 10800):
            return cand
    return int(datetime.fromtimestamp(now_ts, ZoneInfo(tz_name)).utcoffset().total_seconds())


def atr20(ohlc):
    """ohlc = [(den, o, h, l, c)] uzavrenych dni; ATR20 jako v testech (prumer TR za 20 dni)."""
    if len(ohlc) < 21:
        return None
    tr = []
    for i in range(1, len(ohlc)):
        _, _, h, l, _ = ohlc[i]
        pc = ohlc[i - 1][4]
        tr.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(tr[-20:]) / 20


# ====================================================================== data z Yahoo (stejny zdroj jako testy F33 a F42)
_YC = {}


def yahoo_ohlc(tk, max_age=600):
    """[(den NY, open, high, low, close)] vcetne pripadneho rozpracovaneho dne + posledni cena."""
    hit = _YC.get(tk)
    if hit and time.time() - hit[0] < max_age:
        return hit[1], hit[2]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}?range=2y&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (prop runner)"})
    j = json.loads(urllib.request.urlopen(req, timeout=30).read())["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    rows = []
    for t, o, h, l, c in zip(j["timestamp"], q["open"], q["high"], q["low"], q["close"]):
        if None in (o, h, l, c):
            continue
        rows.append((datetime.fromtimestamp(t, NY).date(), float(o), float(h), float(l), float(c)))
    last = float(j["meta"].get("regularMarketPrice") or rows[-1][4])
    _YC[tk] = (time.time(), rows, last)
    return rows, last


def completed(rows, today_ny):
    return [r for r in rows if r[0] < today_ny and r[0].weekday() < 5]


# ====================================================================== runner
class Runner:
    def __init__(self, mt5, cfg, live, state=None):
        self.mt5, self.cfg, self.live = mt5, cfg, live
        self.state = state if state is not None else self._load_state()
        self.offset = None
        self.initial = float(cfg["initial_capital"])
        self.sym = cfg["symbols"]

    # ---------------- zaznamy
    def log(self, *a):
        s = " ".join(str(x) for x in (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),) + a)
        print(s, flush=True)
        try:
            with open(LOGFILE, "a", encoding="utf-8") as f:
                f.write(s + "\n")
        except OSError:
            pass

    def journal(self, rec):
        rec["logged"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(JOURNAL, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        except OSError:
            pass

    def alert(self, msg, key, every_s=3600):
        self.log("UPOZORNENI: " + msg.replace("\n", " "))
        at = self.state.setdefault("alerts", {})
        if os.name != "nt" or NO_POPUP or time.time() - at.get(key, 0) < every_s:
            return
        at[key] = time.time()
        import ctypes
        import threading
        threading.Thread(target=lambda: ctypes.windll.user32.MessageBoxW(None, msg, "Prop runner - POZOR", 0x30 | 0x40000),
                         daemon=True).start()

    def _load_state(self):
        try:
            return json.load(open(STATE, encoding="utf-8"))
        except Exception:
            return {}

    def save_state(self):
        self.state["seen"] = self.state.get("seen", [])[-2000:]
        try:
            json.dump(self.state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, default=str)
        except OSError:
            pass

    # ---------------- ucet
    def check_account(self):
        ai = self.mt5.account_info()
        if ai is None:
            raise RuntimeError("MT5: account_info prazdne (terminal neprihlaseny?)")
        want, srv = int(self.cfg.get("login") or 0), self.cfg.get("server_contains", "FTMO")
        ok = ai.login == want and srv.lower() in str(ai.server).lower()
        if self.live and not ok:
            raise SystemExit(f"Ucet {ai.login} @ {ai.server} neni ucet z prop_config.json ({want}, server obsahuje '{srv}'). Konec.")
        if self.state.get("login") != ai.login:                 # novy ucet (dalsi faze) -> cisty stav
            self.state = {"login": ai.login, "seen": []}
            self.log(f"ucet {ai.login} @ {ai.server}: novy stav")
        return ai

    def server_offset(self):
        tk = self.mt5.symbol_info_tick(self.sym["SPX500mini"])
        self.offset = server_offset_s(getattr(tk, "time", None), time.time(), self.cfg.get("server_tz", "Europe/Athens"))
        return self.offset

    def deals(self, days=60):
        now = datetime.now(timezone.utc)
        r = self.mt5.history_deals_get(now - timedelta(days=days), now + timedelta(days=1))
        return [d for d in (r or []) if d.type in (0, 1)]           # jen nakupy/prodeje, bez vkladu

    def positions(self):
        return list(self.mt5.positions_get() or [])

    # ---------------- pojistka
    def guard(self, ai, now_utc):
        off = self.server_offset()
        mid = day_start_balance(ai.balance, self.deals(3), prague_midnight_utc(now_utc), off)
        L, G = guard_levels(mid, self.initial, margin_pct=float(self.cfg.get("guard_margin_pct", 2.0)))
        today = now_utc.astimezone(PRAGUE).date().isoformat()
        if ai.equity <= G and self.state.get("blocked_day") != today:
            self.state["blocked_day"] = today
            self.close_all(f"pojistka: equity {ai.equity:.2f} <= {G:.2f} (limit FTMO {L:.2f})")
            self.alert(f"Pojistka zavrela vsechny pozice.\nEquity {ai.equity:.2f}, pojistka {G:.2f}, limit FTMO {L:.2f}.\n"
                       "Do pulnoci (Praha) se nic noveho neotevre.", "guard", every_s=0)
        elif ai.equity <= G and self.positions():
            self.close_all("pojistka: dalsi pozice po zasahu")
        return mid, L, G

    def close_all(self, why):
        for p in self.positions():
            if self.live:
                try:
                    self._close(p, why)
                except Exception as e:  # noqa: BLE001
                    self.log(f"  CHYBA zavreni {p.ticket}: {e}")
                    continue
            self.journal(dict(action="zavreno" if self.live else "suchy beh zavreni", ticket=p.ticket, symbol=p.symbol, why=why))
            self.log(f"  <<< zavreno {p.symbol} {p.volume} lot ({p.ticket}): {why}")

    def _close(self, p, why):
        mt5 = self.mt5
        tick = mt5.symbol_info_tick(p.symbol)
        is_long = p.type == mt5.POSITION_TYPE_BUY
        req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume,
               "type": mt5.ORDER_TYPE_SELL if is_long else mt5.ORDER_TYPE_BUY, "position": p.ticket,
               "price": tick.bid if is_long else tick.ask, "deviation": 50, "magic": p.magic, "comment": why[:31],
               "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC}
        res = mt5.order_send(req)
        if res is None or res.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"zavreni selhalo: {getattr(res, 'retcode', None)} {mt5.last_error()}")

    # ---------------- vstupy
    def can_open(self, now_utc):
        today = now_utc.astimezone(PRAGUE).date().isoformat()
        if self.state.get("blocked_day") == today:
            return "pojistka dnes zasahla - do pulnoci nic noveho"
        if self.state.get("target_done"):
            return "cil faze splnen - runner uz neobchoduje"
        return None

    def loss_to_sl(self, otype, symbol, lots, price, sl):
        v = self.mt5.order_calc_profit(otype, symbol, lots, price, sl)
        return -v if v is not None and v < 0 else 0.0

    def open_risk(self):
        tot = 0.0
        for p in self.positions():
            if not p.sl:
                continue
            otype = self.mt5.ORDER_TYPE_BUY if p.type == self.mt5.POSITION_TYPE_BUY else self.mt5.ORDER_TYPE_SELL
            tot += self.loss_to_sl(otype, p.symbol, p.volume, p.price_current, p.sl)
        return tot

    def open_trade(self, strat, mk, d, atr, why, key, now_utc, G):
        mt5 = self.mt5
        self.state.setdefault("seen", []).append(key)
        blk = self.can_open(now_utc)
        if blk:
            return self._skip(strat, mk, blk)
        sym = self.sym[mk]
        if any(p.magic == MAGIC[strat] and p.symbol == sym for p in self.positions()):
            return self._skip(strat, mk, "uz otevreno")
        mt5.symbol_select(sym, True)
        tick, si = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
        if tick is None or si is None or not atr:
            return self._skip(strat, mk, "chybi cena nebo ATR")
        entry = tick.ask if d == 1 else tick.bid
        sl, tp = entry - d * 3 * atr, entry + d * 30 * atr
        otype = mt5.ORDER_TYPE_BUY if d == 1 else mt5.ORDER_TYPE_SELL
        risk_money = self.initial * float(self.cfg.get("risk_pct", 1.25)) / 100.0
        lots = size_lots(risk_money, self.loss_to_sl(otype, sym, 1.0, entry, sl), si.volume_step or 0.01, si.volume_min, si.volume_max)
        if not lots:
            return self._skip(strat, mk, "velikost pod nejmensim lotem (riziko by bylo > 1,5x)")
        new_risk = self.loss_to_sl(otype, sym, lots, entry, sl)
        eq = mt5.account_info().equity
        if eq - self.open_risk() - new_risk < G:
            return self._skip(strat, mk, f"riziko u SL by mohlo skoncit pod pojistkou ({eq:.0f} - otevrene - {new_risk:.0f} < {G:.0f})")
        rec = dict(strategy=strat, symbol=sym, dir="long" if d == 1 else "short", lots=lots, entry_ref=entry,
                   sl=round(sl, si.digits), tp=round(tp, si.digits), risk_money=round(new_risk, 2), why=why, live=self.live)
        if self.live:
            req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": sym, "volume": lots, "type": otype, "price": entry,
                   "sl": rec["sl"], "tp": rec["tp"], "deviation": 50, "magic": MAGIC[strat], "comment": f"prop {strat}",
                   "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC}
            res = mt5.order_send(req)
            if res is None or res.retcode != mt5.TRADE_RETCODE_DONE:
                return self._skip(strat, mk, f"broker odmitl: {getattr(res, 'retcode', None)} {mt5.last_error()}")
            rec.update(action="provedeno", ticket=res.order, fill=res.price)
        else:
            rec.update(action="suchy beh")
        self.journal(rec)
        self.log(f"  >>> {strat} {sym} {rec['dir']} {lots} lot @ {entry} SL {rec['sl']} (riziko {new_risk:.2f}) - {rec['action']}")
        return rec["action"]

    def _skip(self, strat, mk, why):
        self.journal(dict(strategy=strat, market=mk, action="neprovedeno", why=why))
        self.log(f"  --- {strat} {mk} neprovedeno: {why}")
        return why

    # ---------------- strategie (pravidla z f2x_live, data Yahoo jako v testech)
    def strategies(self, now_utc, G):
        t = now_utc.astimezone(NY)
        today = t.date()
        seen = set(self.state.get("seen", []))
        if not FX.is_trading_day(today):
            return
        # F33: 9:30-9:40 NY dne L-2
        k33 = f"F33|{today:%Y-%m}"
        if k33 not in seen and FX.trading_days_left(today) == 2 and FX.ny_dt(today, 9, 30) <= t < FX.ny_dt(today, 9, 40):
            r = FX.f33_entry(now_utc, FX.yahoo_adjclose("SPY"), FX.yahoo_adjclose("TLT"))
            if r and r[0] in (1, -1):
                for mk in F33_MARKETS:
                    rows, _ = yahoo_ohlc(YAHOO[mk])
                    self.open_trade("F33", mk, r[0], atr20(completed(rows, today)), r[1], f"{k33}|{mk}", now_utc, G)
                self.state["seen"].append(k33)
            elif r:
                self.log("  " + r[1])
                if r[0] == "nic":
                    self.state["seen"].append(k33)
        # RSI(2): vstup 9:30-9:45 NY dalsi obchodni den po signalu (test: otevreni dalsiho dne)
        if FX.ny_dt(today, 9, 30) <= t < FX.ny_dt(today, 9, 45):
            for mk in RSI2_MARKETS:
                rows, _ = yahoo_ohlc(YAHOO[mk])
                done = completed(rows, today)
                if not done:
                    continue
                k = f"RSI2|{done[-1][0]}|{mk}"
                if k in seen:
                    continue
                ok, txt = FX.rsi2_signal([r[0] for r in done], [r[4] for r in done])
                self.log(f"  {mk} {txt}")
                if ok:
                    self.open_trade("RSI2", mk, 1, atr20(done), txt, k, now_utc, G)
                else:
                    self.state.setdefault("seen", []).append(k)

    def exits(self, now_utc):
        t = now_utc.astimezone(NY)
        off = self.server_offset()
        for p in self.positions():
            ou = datetime.fromtimestamp(p.time - off, timezone.utc)
            why = None
            if p.magic == MAGIC["F33"] and FX.f33_exit_due(ou, now_utc):
                why = "konec mesice 15:55 NY (F33)"
            elif p.magic == MAGIC["RSI2"]:
                mk = next((m for m, s in self.sym.items() if s == p.symbol), None)
                if mk is None:
                    continue
                rows, last = yahoo_ohlc(YAHOO[mk], max_age=60)
                entry_day = ou.astimezone(NY).date()
                done = completed(rows, t.date())
                if FX.is_trading_day(t.date()) and FX.ny_dt(t.date(), 15, 50) <= t < FX.ny_dt(t.date(), 15, 58):
                    days, closes = [r[0] for r in done] + [t.date()], [r[4] for r in done] + [last]
                    why = FX.rsi2_exit(days, closes, entry_day)                 # pred zavrenim burzy (test: zavreni)
                else:
                    why = FX.rsi2_exit([r[0] for r in done], [r[4] for r in done], entry_day)   # dohnani zmeskaneho
                if why:
                    why = "RSI2: " + why
            elif p.magic == MAGIC["KEEPALIVE"] and time.time() - (p.time - off) >= 60:
                why = "udrzovaci obchod (neaktivita FTMO)"
            if why:
                if self.live:
                    try:
                        self._close(p, why)
                    except Exception as e:  # noqa: BLE001
                        self.log(f"  CHYBA zavreni {p.ticket}: {e}")
                        continue
                self.journal(dict(action="zavreno" if self.live else "suchy beh zavreni", ticket=p.ticket, symbol=p.symbol, why=why))
                self.log(f"  <<< {p.symbol} zavreno: {why}")

    def keepalive(self, now_utc, deals, G):
        start = datetime.fromisoformat(self.cfg["phase_start"]).replace(tzinfo=PRAGUE).astimezone(timezone.utc)
        last = max(last_entry_utc(deals, self.server_offset(), start), start)
        if not keepalive_due(last, now_utc, int(self.cfg.get("keepalive_days", 27))):
            return
        t = now_utc.astimezone(NY)
        if not (FX.is_trading_day(t.date()) and FX.ny_dt(t.date(), 10, 0) <= t < FX.ny_dt(t.date(), 15, 0)):
            return
        if self.can_open(now_utc) or any(p.magic == MAGIC["KEEPALIVE"] for p in self.positions()):
            return
        mt5, sym = self.mt5, self.sym["SPX500mini"]
        mt5.symbol_select(sym, True)
        tick, si = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
        if tick is None or si is None:
            return
        rec = dict(strategy="KEEPALIVE", symbol=sym, lots=si.volume_min, why=f"{(now_utc - last).days} dni bez noveho obchodu",
                   live=self.live)
        if self.live:
            req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": sym, "volume": si.volume_min, "type": mt5.ORDER_TYPE_BUY,
                   "price": tick.ask, "deviation": 50, "magic": MAGIC["KEEPALIVE"], "comment": "prop udrzovaci",
                   "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC}
            res = mt5.order_send(req)
            rec["action"] = "provedeno" if res is not None and res.retcode == mt5.TRADE_RETCODE_DONE else f"odmitnuto {getattr(res, 'retcode', None)}"
        else:
            rec["action"] = "suchy beh"
        self.journal(rec)
        self.alert(f"Udrzovaci obchod (neaktivita FTMO): {rec['why']}, nejmensi lot {sym}, zavre se do minuty. {rec['action']}",
                   "keepalive", every_s=0)

    def phase_target(self, ai, deals):
        tgt = self.cfg.get("target_pct")
        start = date.fromisoformat(self.cfg["phase_start"][:10])
        n = trading_days(deals, start, self.server_offset())
        if not self.state.get("target_done") and target_reached(ai.equity, self.initial, tgt, n):
            self.state["target_done"] = True
            self.close_all(f"cil faze +{tgt} % splnen ({n} obchodnich dni)")
            self.alert(f"Cil faze +{tgt} % je splneny (equity {ai.equity:.2f}, {n} obchodnich dni).\nVsechny pozice zavreny, "
                       "runner dal neobchoduje. Dalsi fazi prihlasis v MT5 a zmenis prop_config.json.", "target", every_s=0)
        return n

    # ---------------- cyklus
    def cycle(self, full=True):
        ai = self.check_account()
        now_utc = datetime.now(timezone.utc)
        mid, L, G = self.guard(ai, now_utc)
        if not full:
            return
        deals = self.deals(60)
        n = self.phase_target(ai, deals)
        try:
            self.exits(now_utc)
        except Exception as e:  # noqa: BLE001
            self.log(f"  vystupy: chyba {e} (zkusim za minutu)")
        try:
            self.strategies(now_utc, G)
        except Exception as e:  # noqa: BLE001
            self.log(f"  strategie: chyba {e}")
        self.keepalive(now_utc, deals, G)
        self.save_state()
        if int(time.time()) % 900 < 60:
            self.log(f"stav: equity {ai.equity:.2f}, zustatek o pulnoci {mid:.2f}, limit FTMO {L:.2f}, pojistka {G:.2f}, "
                     f"obchodnich dni {n}, pozic {len(self.positions())}"
                     + (" | POZOR: v MT5 vypnute Algoritmicke obchodovani" if not self.mt5.terminal_info().trade_allowed else ""))


def load_config(path=CONFIG):
    cfg = json.load(open(path, encoding="utf-8"))
    for k in ("login", "initial_capital", "phase_start", "symbols"):
        if k not in cfg:
            raise SystemExit(f"prop_config.json: chybi '{k}'")
    return cfg


def single_instance():
    if os.name != "nt":
        return None
    import ctypes
    k32 = ctypes.windll.kernel32
    h = k32.CreateMutexW(None, False, "Local\\prop_runner")
    if k32.GetLastError() == 183:
        raise SystemExit("Prop runner uz bezi v jinem okne - druha instance konci.")
    return h


def main():
    import MetaTrader5 as mt5
    live, once = "--live" in sys.argv, "--once" in sys.argv
    cfg = load_config()
    _mutex = single_instance() if live else None  # noqa: F841
    kw = {"path": cfg["terminal_path"]} if cfg.get("terminal_path") else {}
    if not mt5.initialize(**kw):
        raise SystemExit(f"MT5 initialize selhal: {mt5.last_error()} (spust a prihlas FTMO terminal)")
    r = Runner(mt5, cfg, live)
    ai = r.check_account()
    r.log(f"PROP RUNNER {'LIVE' if live else 'SUCHY BEH'} | ucet {ai.login} @ {ai.server} | faze cil {cfg.get('target_pct')} % | "
          f"riziko {cfg.get('risk_pct', 1.25)} % z {r.initial:.0f} | pojistka rezerva {cfg.get('guard_margin_pct', 2.0)} %")
    if once:
        r.cycle()
        return
    errs = 0
    while True:
        try:
            r.cycle(full=int(time.time()) % 60 < 10)
            errs = 0
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            errs += 1
            r.log("chyba cyklu:", e)
            traceback.print_exc(limit=2)
            if errs >= 30:
                r.alert(f"Prop runner {errs}x po sobe hlasi chybu:\n{e}\nZkontroluj MT5 a internet.", "errs")
        time.sleep(10 - time.time() % 10 + 1)


if __name__ == "__main__":
    main()
