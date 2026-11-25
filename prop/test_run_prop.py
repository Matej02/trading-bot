"""Testy prop runneru bez MT5 (falesny terminal). Spusteni: python -I -m unittest test_run_prop.py  (ve slozce prop)"""
import os
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace as NS
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_prop as R  # noqa: E402

TMP = tempfile.mkdtemp()
R.STATE, R.JOURNAL, R.LOGFILE = (os.path.join(TMP, x) for x in ("s.json", "j.jsonl", "l.txt"))
R.NO_POPUP = True                                    # bez vyskakovacich oken


class FakeMT5:
    POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
    ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
    TRADE_ACTION_DEAL, ORDER_TIME_GTC, ORDER_FILLING_IOC, TRADE_RETCODE_DONE = 1, 0, 1, 10009

    def __init__(self, login=123, server="FTMO-Demo", balance=100000.0, equity=None, offset=7200):
        self.acc = NS(login=login, server=server, balance=balance, equity=equity if equity is not None else balance)
        self.pos, self.deals, self.sent, self.offset = [], [], [], offset
        self.price = {"US500.cash": 6000.0, "US100.cash": 21000.0, "US30.cash": 44000.0}
        self.n = 1000

    def account_info(self):
        return self.acc

    def terminal_info(self):
        return NS(trade_allowed=True)

    def positions_get(self):
        return list(self.pos)

    def history_deals_get(self, a, b):
        return list(self.deals)

    def symbol_select(self, s, on):
        return True

    def symbol_info_tick(self, s):
        p = self.price[s]
        import time
        return NS(bid=p - 0.5, ask=p + 0.5, time=int(time.time()) + self.offset)

    def symbol_info(self, s):
        return NS(volume_step=0.01, volume_min=0.01, volume_max=100.0, digits=2)

    def order_calc_profit(self, t, s, lots, p1, p2):
        return (p2 - p1) * lots * (1 if t == 0 else -1)     # 1 lot = 1 $ za bod

    def last_error(self):
        return (0, "ok")

    def order_send(self, req):
        self.sent.append(req)
        self.n += 1
        if "position" in req:
            self.pos = [p for p in self.pos if p.ticket != req["position"]]
        else:
            import time
            self.pos.append(NS(ticket=self.n, symbol=req["symbol"], volume=req["volume"], type=req["type"], magic=req["magic"],
                               sl=req.get("sl", 0.0), price_current=req["price"], time=int(time.time()) + self.offset))
        return NS(retcode=self.TRADE_RETCODE_DONE, order=self.n, price=req["price"])


CFG = dict(login=123, server_contains="FTMO", initial_capital=100000, phase_start="2027-01-11", target_pct=10, risk_pct=1.25,
           guard_margin_pct=2.0, keepalive_days=27,
           symbols={"SPX500mini": "US500.cash", "NAS100mini": "US100.cash", "US30mini": "US30.cash"})


def deal(t_utc, profit=0.0, entry=1, commission=0.0, offset=7200):
    return NS(time=int(t_utc.timestamp()) + offset, profit=profit, swap=0.0, commission=commission, fee=0.0, entry=entry, type=0)


class PureFunctions(unittest.TestCase):
    def test_guard_levels(self):
        self.assertEqual(R.guard_levels(100000, 100000), (95000, 97000))
        self.assertEqual(R.guard_levels(93000, 100000), (90000, 92000))          # celkovy limit 90 % vyhrava
        self.assertEqual(R.guard_levels(108000, 100000), (103000, 105000))

    def test_prague_midnight(self):
        self.assertEqual(R.prague_midnight_utc(datetime(2026, 11, 25, 10, 0, tzinfo=timezone.utc)),
                         datetime(2026, 11, 24, 23, 0, tzinfo=timezone.utc))
        self.assertEqual(R.prague_midnight_utc(datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)),
                         datetime(2026, 6, 30, 22, 0, tzinfo=timezone.utc))

    def test_day_start_balance(self):
        now = datetime(2026, 11, 25, 15, 0, tzinfo=timezone.utc)
        mid = R.prague_midnight_utc(now)
        deals = [deal(mid - timedelta(hours=1), 500.0), deal(mid + timedelta(hours=5), -300.0), deal(mid + timedelta(hours=6), 0.0, 0, -4.0)]
        self.assertAlmostEqual(R.day_start_balance(100196.0, deals, mid, 7200), 100500.0)

    def test_trading_days_and_last_entry(self):
        base = datetime(2027, 1, 12, 15, 0, tzinfo=timezone.utc)
        deals = [deal(base, entry=0), deal(base + timedelta(hours=2), entry=0), deal(base + timedelta(days=1), entry=0),
                 deal(base + timedelta(days=2), 100.0, entry=1), deal(base - timedelta(days=5), entry=0)]
        self.assertEqual(R.trading_days(deals, date(2027, 1, 11), 7200), 2)
        self.assertEqual(R.last_entry_utc(deals, 7200, None), base + timedelta(days=1))

    def test_keepalive_due(self):
        t = datetime(2027, 2, 1, tzinfo=timezone.utc)
        self.assertFalse(R.keepalive_due(t - timedelta(days=26, hours=23), t))
        self.assertTrue(R.keepalive_due(t - timedelta(days=27), t))

    def test_target(self):
        self.assertTrue(R.target_reached(110000, 100000, 10, 4))
        self.assertFalse(R.target_reached(110000, 100000, 10, 3))
        self.assertFalse(R.target_reached(109999, 100000, 10, 9))
        self.assertFalse(R.target_reached(200000, 100000, None, 9))

    def test_size_lots(self):
        self.assertEqual(R.size_lots(1250, 500, 0.01, 0.01, 100), 2.5)
        self.assertIsNone(R.size_lots(1250, 2000, 1.0, 1.0, 100))               # nejmensi lot by riskoval 1,6x
        self.assertEqual(R.size_lots(1250, 1700, 1.0, 1.0, 100), 1.0)          # 1,36x -> nejmensi lot
        self.assertEqual(R.size_lots(1250, 1000, 1.0, 1.0, 100), 1.0)

    def test_server_offset(self):
        now = 1_800_000_000
        self.assertEqual(R.server_offset_s(now + 7200 - 40, now), 7200)
        self.assertEqual(R.server_offset_s(now + 10800 + 900, now), 10800)
        winter = datetime(2027, 1, 15, tzinfo=timezone.utc).timestamp()
        self.assertEqual(R.server_offset_s(winter - 3 * 86400, winter), 7200)    # stary tick o vikendu -> pasmo serveru

    def test_atr20(self):
        rows = [(i, 100, 101, 99, 100) for i in range(30)]
        self.assertAlmostEqual(R.atr20(rows), 2.0)
        self.assertIsNone(R.atr20(rows[:10]))


class RunnerTests(unittest.TestCase):
    def mk(self, **kw):
        m = FakeMT5(**kw)
        return m, R.Runner(m, dict(CFG), live=True, state={"login": 123, "seen": []})

    def test_account_lock(self):
        m = FakeMT5(login=999)
        with self.assertRaises(SystemExit):
            R.Runner(m, dict(CFG), live=True, state={}).check_account()
        m2 = FakeMT5(server="OtherBroker-Live")
        with self.assertRaises(SystemExit):
            R.Runner(m2, dict(CFG), live=True, state={}).check_account()
        R.Runner(FakeMT5(login=999), dict(CFG), live=False, state={}).check_account()   # suchy beh jen cte

    def test_guard_closes_and_blocks(self):
        m, r = self.mk(balance=100000.0, equity=96900.0)
        m.pos = [NS(ticket=1, symbol="US500.cash", volume=2.0, type=0, magic=R.MAGIC["RSI2"], sl=5900.0, price_current=5950.0, time=0)]
        now = datetime(2027, 3, 10, 15, 0, tzinfo=timezone.utc)
        mid, L, G = r.guard(m.acc, now)
        self.assertEqual((L, G), (95000, 97000))
        self.assertEqual(m.pos, [])
        self.assertEqual(r.state["blocked_day"], "2027-03-10")
        self.assertIn("pojistka", r.can_open(now))
        self.assertIsNone(r.can_open(now + timedelta(days=1)))

    def test_guard_quiet_above_level(self):
        m, r = self.mk(balance=100000.0, equity=97500.0)
        m.pos = [NS(ticket=1, symbol="US500.cash", volume=2.0, type=0, magic=1, sl=0.0, price_current=6000.0, time=0)]
        r.guard(m.acc, datetime(2027, 3, 10, 15, 0, tzinfo=timezone.utc))
        self.assertEqual(len(m.pos), 1)
        self.assertNotIn("blocked_day", r.state)

    def test_entry_sizing_and_pre_entry_check(self):
        m, r = self.mk(balance=100000.0)
        now = datetime(2027, 3, 10, 14, 35, tzinfo=timezone.utc)
        res = r.open_trade("RSI2", "SPX500mini", 1, 100.0, "test", "k1", now, 97000)   # SL 300 bodu, 1 250 $ -> 4,16 lotu
        self.assertEqual(res, "provedeno")
        self.assertAlmostEqual(m.sent[-1]["volume"], 4.16)
        self.assertAlmostEqual(m.sent[-1]["sl"], 5700.5)
        self.assertEqual(r.open_trade("RSI2", "SPX500mini", 1, 100.0, "test", "k2", now, 97000), "uz otevreno")
        m.acc.equity = 98000.0                                     # 98 000 - 1 248 (otevrene) - 1 248 (nove) < 97 000
        self.assertIn("pod pojistkou", r.open_trade("RSI2", "NAS100mini", 1, 300.0, "test", "k3", now, 97000))

    def test_target_closes_and_stops(self):
        m, r = self.mk(balance=109000.0, equity=110100.0)
        m.pos = [NS(ticket=7, symbol="US100.cash", volume=1.0, type=0, magic=R.MAGIC["F33"], sl=0.0, price_current=21000.0, time=0)]
        base = datetime(2027, 1, 12, 15, 0, tzinfo=timezone.utc)
        deals = [deal(base + timedelta(days=i), entry=0) for i in range(4)]
        r.phase_target(m.acc, deals)
        self.assertTrue(r.state["target_done"])
        self.assertEqual(m.pos, [])
        self.assertIn("cil faze", r.can_open(base + timedelta(days=10)))

    def test_keepalive_opens_and_closes(self):
        m, r = self.mk()
        start = datetime(2027, 1, 11, tzinfo=R.PRAGUE)
        now = datetime(2027, 2, 9, 16, 0, tzinfo=timezone.utc)          # utery 11:00 NY, 29 dni od startu bez obchodu
        r.keepalive(now, [], 0)
        self.assertEqual(len(m.pos), 1)
        self.assertEqual(m.pos[0].magic, R.MAGIC["KEEPALIVE"])
        self.assertAlmostEqual(m.pos[0].volume, 0.01)
        r.keepalive(now, [], 0)                                          # druhy se neotevre
        self.assertEqual(len(m.pos), 1)
        m.pos[0].time -= 120                                             # o 2 min starsi
        with mock.patch.object(R, "yahoo_ohlc", side_effect=AssertionError("Yahoo se nema volat")):
            r.exits(now)
        self.assertEqual(m.pos, [])
        recent = [deal(now - timedelta(days=3), entry=0)]
        r.keepalive(now, recent, 0)
        self.assertEqual(m.pos, [])
        self.assertTrue(start < now)

    def test_rsi2_signal_entry_window(self):
        m, r = self.mk()
        days, d0 = [], date(2026, 1, 5)
        while len(days) < 260:
            if R.FX.is_trading_day(d0):
                days.append(d0)
            d0 += timedelta(days=1)
        closes = [5000 + 5 * i for i in range(len(days) - 3)] + [6200, 6150, 6100]   # trend nahoru, 3 dny pokles
        rows = [(d, c, c + 20, c - 20, c) for d, c in zip(days, closes)]
        today = R.FX.next_trading_day(days[-1])
        now = datetime(today.year, today.month, today.day, 9, 35, tzinfo=R.NY).astimezone(timezone.utc)
        with mock.patch.object(R, "yahoo_ohlc", return_value=(rows, closes[-1])):
            r.strategies(now, 0)
        rsi = [x for x in m.sent if x.get("magic") == R.MAGIC["RSI2"]]
        self.assertEqual(len(rsi), 3)                                   # SPX, NAS, US30
        self.assertTrue(all(x["type"] == 0 for x in rsi))
        late = now + timedelta(minutes=20)                              # po 9:45 NY uz ne
        m.sent.clear()
        r.state["seen"] = []
        with mock.patch.object(R, "yahoo_ohlc", return_value=(rows, closes[-1])):
            r.strategies(late, 0)
        self.assertEqual(m.sent, [])

    def test_rsi2_exit_before_close(self):
        m, r = self.mk()
        days, d0 = [], date(2026, 1, 5)
        while len(days) < 30:
            if R.FX.is_trading_day(d0):
                days.append(d0)
            d0 += timedelta(days=1)
        closes = [6000.0] * 25 + [5900, 5850, 5800, 5790, 5780]
        rows = [(d, c, c, c, c) for d, c in zip(days, closes)]
        today = R.FX.next_trading_day(days[-1])
        open_t = datetime(today.year, today.month, today.day, 9, 35, tzinfo=R.NY).astimezone(timezone.utc)
        m.pos = [NS(ticket=5, symbol="US500.cash", volume=1.0, type=0, magic=R.MAGIC["RSI2"], sl=5500.0, price_current=5790.0,
                    time=int(open_t.timestamp()) + 7200)]
        t1555 = datetime(today.year, today.month, today.day, 15, 55, tzinfo=R.NY).astimezone(timezone.utc)
        with mock.patch.object(R, "yahoo_ohlc", return_value=(rows, 5795.0)):          # pod SMA5 -> drzet
            r.exits(t1555)
        self.assertEqual(len(m.pos), 1)
        with mock.patch.object(R, "yahoo_ohlc", return_value=(rows, 5900.0)):          # nad SMA5 -> ven pred zavrenim
            r.exits(t1555)
        self.assertEqual(m.pos, [])


if __name__ == "__main__":
    unittest.main()
