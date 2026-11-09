"""
F33 / F31 / F29 pro MT5 demo runner (run_fm_demo.py). Jen rozhodovani (ciste funkce s parametrem now), prikazy posila runner.
Pravidla z planu zapsanych predem ve vaultu (Vyzkum/F33, F31, F29) s upravami pro PC zapnute do 20:00 Praha:
  F33 rebalancovani: vstup na otevreni US seance dne L-2 (9:30 NY, jako v testu), signal SPY vs TLT do zavreni L-3,
      |rozdil| >= 2 p. b. -> obchod proti viteziu; vystup 15:55 NY posledniho obchodniho dne mesice (21:55 Praha).
  F31 drift pred FOMC: long 14:00 NY v posledni obchodni den pred FOMC (20:00 Praha - jen kdyz bezi PC), ven 13:55 NY v den FOMC.
  F29 krypto momentum: v pondeli (UTC) vynos za 28 dni k nedelnimu zavreni > 0 -> long na tyden, ven pri prvni kontrole
      v dalsi pondeli (v testu pondeli 00:00 UTC).
SL vsude 3 x ATR20 (denni) jako pojistka, TP daleko (10 R) - v testech bez stopu a TP.
"""
import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
F33_THRESHOLD = 0.02
# rozhodnuti FOMC (posledni den radneho zasedani, oznameni 14:00 NY); zdroj federalreserve.gov, 2027 predbezne
FOMC = {date.fromisoformat(x) for x in (
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
    "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08")}
LAST_FOMC = max(FOMC)


# ------------------------------------------------------------------ burzovni kalendar NYSE

def _nth_weekday(y, m, wd, n):
    d = date(y, m, 1)
    return d + timedelta(days=(wd - d.weekday()) % 7 + 7 * (n - 1))


def _last_weekday(y, m, wd):
    d = (date(y, m + 1, 1) if m < 12 else date(y + 1, 1, 1)) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - wd) % 7)


def _easter(y):
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    return date(y, (h + l_ - 7 * m + 114) // 31, (h + l_ - 7 * m + 114) % 31 + 1)


def _observed(d):
    return d - timedelta(days=1) if d.weekday() == 5 else d + timedelta(days=1) if d.weekday() == 6 else d


_HOL = {}


def nyse_holidays(y):
    if y not in _HOL:
        ny = date(y, 1, 1)
        h = {ny + timedelta(days=1) if ny.weekday() == 6 else None if ny.weekday() == 5 else ny,
             _nth_weekday(y, 1, 0, 3), _nth_weekday(y, 2, 0, 3), _easter(y) - timedelta(days=2), _last_weekday(y, 5, 0),
             _observed(date(y, 6, 19)) if y >= 2022 else None, _observed(date(y, 7, 4)), _nth_weekday(y, 9, 0, 1),
             _nth_weekday(y, 11, 3, 4), _observed(date(y, 12, 25))}
        _HOL[y] = {x for x in h if x}
    return _HOL[y]


def is_trading_day(d):
    return d.weekday() < 5 and d not in nyse_holidays(d.year)


def trading_days_left(d):
    """Kolik obchodnich dni NYSE zbyva v mesici PO dni d (0 = d je posledni obchodni den)."""
    n, x = 0, d + timedelta(days=1)
    while x.month == d.month:
        n += is_trading_day(x)
        x += timedelta(days=1)
    return n


def last_trading_day(d):
    x = (date(d.year, d.month + 1, 1) if d.month < 12 else date(d.year + 1, 1, 1)) - timedelta(days=1)
    while not is_trading_day(x):
        x -= timedelta(days=1)
    return x


def next_trading_day(d):
    x = d + timedelta(days=1)
    while not is_trading_day(x):
        x += timedelta(days=1)
    return x


def prev_trading_day(d):
    x = d - timedelta(days=1)
    while not is_trading_day(x):
        x -= timedelta(days=1)
    return x


def ny_dt(d, hh, mm):
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=NY)


# ------------------------------------------------------------------ data SPY / TLT z Yahoo (upravene ceny vcetne dividend)

_YCACHE = {}


def yahoo_adjclose(tk, max_age=6 * 3600):
    hit = _YCACHE.get(tk)
    if hit and time.time() - hit[0] < max_age:
        return hit[1]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}?range=6mo&interval=1d&events=div"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (FM demo runner)"})
    j = json.loads(urllib.request.urlopen(req, timeout=30).read())["chart"]["result"][0]
    tz = ZoneInfo(j["meta"].get("exchangeTimezoneName", "America/New_York"))
    s = {datetime.fromtimestamp(t, tz).date(): v for t, v in zip(j["timestamp"], j["indicators"]["adjclose"][0]["adjclose"]) if v}
    _YCACHE[tk] = (time.time(), s)
    return s


def month_to_date(series, d):
    """Vynos od posledniho zavreni predchoziho mesice do zavreni dne d (None, kdyz data chybi)."""
    if d not in series:
        return None
    prev = [x for x in series if x < date(d.year, d.month, 1)]
    return series[d] / series[max(prev)] - 1 if prev else None


# ------------------------------------------------------------------ rozhodovani

def f33_entry(now_utc, spy, tlt):
    """Ve 9:30-9:40 NY dne L-2: (smer, popis) nebo None. spy/tlt = {date: adjclose}."""
    t = now_utc.astimezone(NY)
    d = t.date()
    if not is_trading_day(d) or trading_days_left(d) != 2 or not (ny_dt(d, 9, 30) <= t < ny_dt(d, 9, 40)):
        return None
    sig_day = prev_trading_day(d)                      # L-3
    rs, rb = month_to_date(spy, sig_day), month_to_date(tlt, sig_day)
    if rs is None or rb is None:
        return ("chyba", f"F33: chybi data SPY/TLT k {sig_day}")
    diff = rs - rb
    if abs(diff) < F33_THRESHOLD:
        return ("nic", f"F33: rozdil SPY {rs * 100:+.2f} % - TLT {rb * 100:+.2f} % = {diff * 100:+.2f} p. b. pod prahem 2 p. b.")
    return (-1 if diff > 0 else 1, f"F33: SPY {rs * 100:+.2f} %, TLT {rb * 100:+.2f} % od konce minuleho mesice do {sig_day} "
            f"(rozdil {diff * 100:+.2f} p. b.) -> {'short' if diff > 0 else 'long'} do 15:55 NY {last_trading_day(d)}")


def f33_exit_due(open_utc, now_utc):
    d = open_utc.astimezone(NY).date()
    return now_utc >= ny_dt(last_trading_day(d), 15, 55).astimezone(timezone.utc)


def f31_entry(now_utc):
    t = now_utc.astimezone(NY)
    d = t.date()
    return is_trading_day(d) and next_trading_day(d) in FOMC and ny_dt(d, 14, 0) <= t < ny_dt(d, 14, 10)


def f31_exit_due(open_utc, now_utc):
    d = open_utc.astimezone(NY).date()
    return now_utc >= ny_dt(next_trading_day(d), 13, 55).astimezone(timezone.utc)


def f29_week_start(now_utc):
    """Pondeli 00:00 UTC aktualniho tydne."""
    d = now_utc.date() - timedelta(days=now_utc.weekday())
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def f29_signal(daily_close, now_utc):
    """daily_close = {date (UTC den): close}. V pondeli (UTC): momentum k nedelnimu zavreni. Vraci (mom, popis) nebo None."""
    if now_utc.weekday() != 0:
        return None
    sun = now_utc.date() - timedelta(days=1)
    past = sun - timedelta(days=28)
    if sun not in daily_close or past not in daily_close:
        return None
    mom = daily_close[sun] / daily_close[past] - 1
    return mom, f"F29: vynos za 28 dni do {sun} {mom * 100:+.2f} %"


def f29_exit_due(open_utc, now_utc):
    return open_utc < f29_week_start(now_utc)
