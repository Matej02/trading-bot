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


def yahoo_adjclose(tk, max_age=6 * 3600, rng="6mo"):
    hit = _YCACHE.get((tk, rng))
    if hit and time.time() - hit[0] < max_age:
        return hit[1]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{tk}?range={rng}&interval=1d&events=div"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (FM demo runner)"})
    j = json.loads(urllib.request.urlopen(req, timeout=30).read())["chart"]["result"][0]
    tz = ZoneInfo(j["meta"].get("exchangeTimezoneName", "America/New_York"))
    s = {datetime.fromtimestamp(t, tz).date(): v for t, v in zip(j["timestamp"], j["indicators"]["adjclose"][0]["adjclose"]) if v}
    _YCACHE[(tk, rng)] = (time.time(), s)
    return s


# RSI(2): trendovy filtr SMA200 z dennich dat indexu na Yahoo (2026-11-24). Historie MT5 dema ma diry
# (10/2025-2/2026, 6-8/2026; broker data nema), SMA200 z MT5 tak vychazela moc nizko. Test F42 i simulator = Yahoo.
RSI2_YAHOO = {"SPX500mini": "^GSPC", "NAS100mini": "^NDX", "US30mini": "^DJI"}


def sma200_yahoo(series, day):
    """series = {date: zavreni} z Yahoo. Vraci ("ok", zavreni dne day, SMA200 do day vcetne),
    ("svatek", None, None) kdyz Yahoo ma pozdejsi dny, ale day ne (burza zavrena), nebo ("chybi", None, None)."""
    xs = sorted(d for d in series if d <= day)
    if xs and xs[-1] == day and len(xs) >= 200:
        return "ok", series[day], sum(series[d] for d in xs[-200:]) / 200
    if day not in series and any(d > day for d in series):
        return "svatek", None, None
    return "chybi", None, None


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


# ------------------------------------------------------------------ RSI(2) pullback (vyzkum F42, prislo 5/5, souhlas uzivatele 2026-11-19)
# Denni svicky MT5 (den serveru = UTC), jen pracovni dny, jen UZAVRENE. Signal na zavreni dne: zavreni > SMA200 a RSI(2) < 10.
# Vstup rano dalsiho dne (PC v noci vypnute; test: otevreni dne), stop 3 ATR20, ven az zavreni > SMA5 nebo po 10 dnech
# (runner zavira pri prvnim behu po uzavreni dne). Kontrola na datech brokera 2019-26: test +0,066 R, ranni varianta +0,058 R.

def rsi_wilder(closes, n=2):
    """RSI s Wilderovym vyhlazenim (stejne jako simulator a test F42). closes = list/array, vraci posledni hodnotu."""
    if len(closes) <= n:
        return None
    up = dn = 0.0
    a = 1.0 / n
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        g, l = max(d, 0.0), max(-d, 0.0)
        if i == 1:
            up, dn = g, l
        else:
            up, dn = up + a * (g - up), dn + a * (l - dn)
    return 100.0 if dn == 0 else 100 - 100 / (1 + up / dn)


def rsi2_signal(days, closes, trend=None):
    """days/closes = uzavrene pracovni denni svicky (vzestupne). Vraci (signal, popis) pro posledni svicku.
    trend = (zavreni, SMA200) z jineho zdroje (Yahoo, runner od 2026-11-24); None = SMA200 z closes (paritni test F42)."""
    if len(closes) < 205:
        return False, "RSI(2): malo dennich dat"
    c, sma200 = trend if trend else (closes[-1], sum(closes[-200:]) / 200)
    src = " (Yahoo)" if trend else ""
    r = rsi_wilder(closes[-250:])
    ok = c > sma200 and r is not None and r < 10
    return ok, (f"RSI(2): zavreni {days[-1]} {c:.2f}{src} {'>' if c > sma200 else '<='} SMA200{src} {sma200:.2f}, "
                f"RSI(2) {r:.1f}" + (" < 10 -> long" if ok else ""))


def rsi2_exit(days, closes, entry_day):
    """Duvod vystupu (zavreni > SMA5, nebo 10. den vcetne dne vstupu) podle uzavrenych dni od dne vstupu, jinak None."""
    k = 0
    for i, d in enumerate(days):
        if d < entry_day or i < 4:
            continue
        k += 1
        sma5 = sum(closes[i - 4:i + 1]) / 5
        if closes[i] > sma5:
            return f"zavreni {d} {closes[i]:.2f} nad SMA5 {sma5:.2f} (RSI2)"
        if k >= 10:
            return f"10. den od vstupu ({d}) (RSI2)"
    return None


def next_events_text(now_utc):
    """Kratky text do zivotni znamky runneru: kdy dalsi F33 / F31 / F29."""
    d = now_utc.astimezone(NY).date()
    x = d
    while not (is_trading_day(x) and trading_days_left(x) == 2 and (x > d or now_utc < ny_dt(x, 9, 40).astimezone(timezone.utc))):
        x += timedelta(days=1)
    fomc = [f for f in sorted(FOMC) if now_utc < ny_dt(prev_trading_day(f), 14, 10).astimezone(timezone.utc)]
    f31 = f"F31 {prev_trading_day(fomc[0]):%d.%m.} 20:00" if fomc else "F31 dosly terminy FOMC"
    mon = now_utc.date() + timedelta(days=(7 - now_utc.weekday()) % 7 or 7)
    return f"hlida F33 {x:%d.%m.} 15:30, {f31}, F29 {mon:%d.%m.}"
