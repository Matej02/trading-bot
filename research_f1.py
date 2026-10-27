"""
F1 - hledani strategie se SKUTECNYMI naklady (2026-10-26).

Testuji jen tridy signalu, ktere dosavadni vyzkum (README, 1 500+ kombinaci)
NEpokryl a ktere maji oporu v odborne literature:

  A  trendove momentum napric portfoliem (time-series momentum, Moskowitz-Ooi-
     Pedersen 2012) - evidence je na urovni PORTFOLIA mnoha trhu, ne jednoho paru
  B  kratkodobe vraceni k prumeru na akciovych indexech (IBS, RSI(2))
  C  prelom mesice na akciovych indexech (turn-of-the-month)
  D  carry - drzet smer s kladnym swapem (je jen u par trhu, hlavne lira,
     rand, peso). Pozor: swap je dnesni a pouziva se i zpetne, sazby se ale
     v case menily - u carry je to nejvetsi slabina tohohle testu.

PLAN STANOVENY PREDEM (nemeni se podle vysledku):
  - Rozhodnuti 1x denne v pevnou likvidni hodinu (ne pri uzavreni D1 svicky,
    to je v rollover okne): US indexy 19:00 UTC, ostatni 15:00 UTC.
  - Naklad = ZIVY spread v te hodine (median historie ticku + prirazka brokera
    namerena ted) x 1.25 (rezerva na skluz). Swap za kazdou noc podle brokera
    (3x v jeho den), jako podil ceny - dnesni sazby, i zpetne.
  - Vyber parametru: data do 2022-12-31. Overeni (holdout): 2023-01-01 az dnes.
    Z kazde rodiny jde na holdout JEN jedna varianta - nejlepsi ve vyberu.
    Broker ma indexy (a ropu) az od 2019-02-21, proto staci historie od 2019-03
    (upraveno podle dostupnosti dat PRED prvnim behem, ne podle vysledku).
  - Long-only strategie (B, C) se meri proti driftu: od kazdeho obchodu se
    odecte, co by za stejny pocet dni vydelalo obycejne drzeni (vcetne swapu).
    (Past c. 3 z README: jednostranny test namerl drift trhu, ne edge.)
  - Indexy se hybou spolu, proto se t u B a C pocita z prumeru za den vstupu
    (shluky), ne z jednotlivych obchodu. U A z denniho P&L portfolia (Newey-West).
  - PROSLO = na holdoutu: vysledek (u B, C nad driftem) > 0 s t >= 2.25
    (Bonferroni pro 4 rodiny), PF >= 1.10, n >= 100 obchodu.
    Carry drzi pozici trvale (obchodu je par), proto u nej n = dny v pozici
    a PF z dennich vysledku portfolia (stanoveno pred behem).
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

sys.stdout.reconfigure(line_buffering=True)

import mt5_connector as mc

DATA_DIR = "research_data"
SPLIT = pd.Timestamp("2023-01-01")
HISTORY_FROM = pd.Timestamp("2019-03-01")     # indexy u brokera zacinaji 2019-02-21
SLIP = 1.25
MAX_COST_RATIO = 0.05                         # naklad max 5 % denniho rozsahu
T_PASS, PF_PASS, N_PASS = 2.25, 1.10, 100

US_INDEX = {"S&P500", "DOW30", "NAS100", "SPX500mini", "US30mini", "NAS100mini"}
INDEX_GROUPS = {        # stejny index ve dvou podobach -> jen jeden; cash CFD ma prednost (futures roluji)
    "US500": ["SPX500mini", "S&P500"], "US30": ["US30mini", "DOW30"], "NAS": ["NAS100mini", "NAS100"],
    "DE": ["GER_30mini", "DAX40"], "UK": ["GBR_100mini", "UK100"], "FR": ["FRA_40mini"],
    "EU50": ["EUR_50mini"], "ES": ["ESP_35mini"],
}
OTHER_GROUPS = ("FOREX", "METALS", "CRYPTO")
ENERGY = ("CRUDE_OIL", "BRENT_OIL", "NATGAS", "BRENTmini", "OILUSDmini")


def decision_hour(sym):
    return 19 if sym in US_INDEX else 15


# ---------------------------------------------------------------- data a naklady

def load_h1(sym, n=99_000):                   # terminal vic nez ~99 600 svicek najednou nevyda
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{sym.replace('&', 'and')}_H1.pkl")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 86400:
        return pd.read_pickle(path)
    mc.mt5.symbol_select(sym, True)
    rates = None
    for _ in range(5):
        rates = mc.mt5.copy_rates_from_pos(sym, mc.mt5.TIMEFRAME_H1, 0, n)
        if rates is not None and len(rates) > 1000:
            break
        time.sleep(2)
    if rates is None or len(rates) < 1000:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("time")[["open", "high", "low", "close"]].iloc[:-1]   # bez tvorici se svicky
    df.to_pickle(path)
    return df


def daily(h1, hour, max_jump):
    """Denni rada s rozhodnutim v pevnou hodinu: px = cena (open H1 svicky) v tu
    hodinu, hi/lo = rozsah za uplynulych 24 h. Dny, kdy trh v tu hodinu nebezel,
    vypadnou."""
    is_dec = h1.index.hour == hour
    grp = np.cumsum(is_dec)
    g = h1.groupby(grp)
    agg = pd.DataFrame({"hi": g["high"].max(), "lo": g["low"].min(), "n": g.size()})
    dec = h1[is_dec]
    # rozhodnuti k (1..K) zacina skupinu k; okno PRED nim = skupina k-1
    # (skupina 0 chybi, kdyz data zacinaji presne v hodine rozhodnuti)
    prev = agg.reindex(range(len(dec) + 1)).iloc[:len(dec)]
    out = pd.DataFrame({"px": dec["open"].values}, index=dec.index)
    out["hi"] = np.maximum(prev["hi"].values, out["px"].values)
    out["lo"] = np.minimum(prev["lo"].values, out["px"].values)
    out["nbars"] = prev["n"].values
    out = out[out["nbars"] >= 6]
    jump = out["px"].pct_change().abs() > max_jump
    if jump.any():
        print(f"      varovani: {jump.sum()} dennich skoku > {max_jump:.0%} (chyba dat), vynechavam")
        out = out[~jump]
    return out


def markup(sym, samples=5):
    """Prirazka zive ceny proti historii ticku, v cenovych jednotkach (None = trh stoji)."""
    diffs = []
    for _ in range(samples):
        live = mc.mt5.symbol_info_tick(sym)
        if live is None or abs(live.time - datetime.now(timezone.utc).timestamp()) > 300:
            return None
        h = mc.mt5.copy_ticks_range(sym, live.time - 300, live.time + 1, mc.mt5.COPY_TICKS_INFO)
        if h is not None and len(h):
            same = h[h["time"] == live.time]
            if len(same):
                diffs.append((live.ask - live.bid) - (same[-1]["ask"] - same[-1]["bid"]))
        time.sleep(0.3)
    return float(np.median(diffs)) if diffs else None


def live_cost(sym, hour, mk):
    """Zivy spread v dane hodine: median historie ticku v tu hodinu + prirazka."""
    now = datetime.now(timezone.utc)
    t = mc.mt5.copy_ticks_range(sym, now - timedelta(days=14), now, mc.mt5.COPY_TICKS_INFO)
    if t is None or len(t) == 0:
        return None
    hrs = (t["time"] // 3600) % 24
    sp = t["ask"] - t["bid"]
    sel = sp[hrs == hour]
    return (float(np.median(sel)) if len(sel) else float(np.median(sp))) + mk


def swap_frac(si, price):
    """(long, short) swap za noc jako podil ceny; kladne = broker pripisuje."""
    mode = si.swap_mode
    if mode == 0:
        sl = ss = 0.0
    elif mode in (1, 7, 8):                                  # body
        sl, ss = si.swap_long * si.point, si.swap_short * si.point
    elif mode in (2, 3, 4, 9):                               # penize na lot (9 = v mene zisku)
        # NE tick_value/tick_size: u US30mini a NAS100mini je to 10x mene, nez kolik
        # broker skutecne pocita (order_calc_profit) - swap by vysel 10x vetsi
        delta = price * 0.001
        money_per_price = (mc.mt5.order_calc_profit(mc.mt5.ORDER_TYPE_BUY, si.name, 1.0, price, price + delta) or 0) / delta
        if money_per_price <= 0:                             # XRPUSD vraci 0
            money_per_price = si.trade_tick_value / si.trade_tick_size
        sl, ss = si.swap_long / money_per_price, si.swap_short / money_per_price
    elif mode in (5, 6):                                     # rocni % z ceny
        sl, ss = price * si.swap_long / 100 / 360, price * si.swap_short / 100 / 360
    else:
        raise ValueError(f"neznamy swap_mode {mode}")
    return sl / price, ss / price


def swap_nights(index, roll3_mt5):
    """Pocet uctovanych swapu za prechod z dne i na i+1: kazdy pracovni den mezi
    nimi 1x, v den brokera 3x (pokryva vikend). MT5: 0 = nedele, 1 = pondeli..."""
    roll3 = (roll3_mt5 - 1) % 7                              # -> python: 0 = pondeli
    days = index.normalize()
    out = np.zeros(len(index))
    for i in range(len(index) - 1):
        n = 0
        d = days[i]
        while d < days[i + 1]:
            if d.weekday() < 5:
                n += 3 if d.weekday() == roll3 else 1
            d += pd.Timedelta(days=1)
        out[i] = n
    return out


# ---------------------------------------------------------------- backtest

def run_positions(d, pos, u):
    """pos[i] = pozice rozhodnuta v case i (-1/0/1), drzena do i+1. Velikost pri
    vstupu = 1/volatilita denni zmeny (stejne riziko na kazdem trhu), P&L je tedy
    v 'dennich sigmach'. Vraci (denni P&L, obchody [(vstup, smer, pnl, dni)])."""
    px = d["px"].values
    cost, nights = u["cost"], u["nights"]
    n = len(px)
    # diry v historii brokera (EURUSD chybi skoro cely rok) - pres diru se nedrzi
    # a skok pres ni se nepocita do volatility
    hole = np.diff(d.index.values) > np.timedelta64(7, "D")
    chg = np.diff(px, prepend=np.nan)
    chg[1:][hole] = np.nan
    vol = pd.Series(chg).rolling(60, min_periods=40).std().values
    pnl = np.zeros(n)
    trades = []
    cur, units, t_pnl, t_start, t_days = 0, 0.0, 0.0, 0, 0
    for i in range(n - 1):
        p = 0 if hole[i] else pos[i]
        if p != cur:
            if cur != 0:                                         # zavreni
                c = units * cost / 2 * SLIP
                pnl[i] -= c
                trades.append((d.index[t_start], cur, t_pnl - c, t_days))
                cur = 0
            if p != 0 and vol[i] > 0:                            # otevreni (NaN > 0 je False)
                units = 1.0 / vol[i]
                c = units * cost / 2 * SLIP
                pnl[i] -= c
                cur, t_pnl, t_start, t_days = p, -c, i, 0
        if cur != 0:
            sw = (u["sl"] if cur > 0 else u["ss"]) * px[i] * nights[i]
            step = ((px[i + 1] - px[i]) * cur + sw) * units
            pnl[i + 1] += step
            t_pnl += step
            t_days += 1
    if cur != 0:
        trades.append((d.index[t_start], cur, t_pnl, t_days))
    return pd.Series(pnl, index=d.index.normalize()), trades


def drift_per_day(d, u):
    """Co vydela obycejne drzeni long za kazdy den (vcetne swapu, bez spreadu),
    ve stejnych jednotkach jako obchody: zmena / volatilita v ten den.
    Hodnota u dne i = krok z i do i+1 (diry vynechany)."""
    px = d["px"].values
    hole = np.diff(d.index.values) > np.timedelta64(7, "D")
    chg = np.diff(px, prepend=np.nan)
    chg[1:][hole] = np.nan
    vol = pd.Series(chg).rolling(60, min_periods=40).std().values
    step = np.append(np.diff(px), np.nan) + u["sl"] * px * u["nights"]
    step[:-1][hole] = np.nan
    return pd.Series(step / vol, index=d.index.normalize())


def stats(tr):
    """tr: [(vstup, smer, pnl, dni, nad_driftem)]"""
    if not tr:
        return {"n": 0, "PF": 0, "win%": 0, "prumer": 0, "nad_driftem": 0, "t": 0, "dny_vstupu": 0}
    df = pd.DataFrame(tr, columns=["date", "dir", "pnl", "days", "ex"])
    wins, losses = df.loc[df.pnl > 0, "pnl"].sum(), -df.loc[df.pnl < 0, "pnl"].sum()
    cl = df.groupby(df["date"].dt.normalize())["ex"].mean()      # shluky podle dne vstupu
    t = cl.mean() / (cl.std(ddof=1) / np.sqrt(len(cl))) if len(cl) > 2 and cl.std(ddof=1) > 0 else 0.0
    return {"n": len(df), "dny_vstupu": len(cl), "PF": wins / losses if losses else np.inf,
            "win%": 100 * (df.pnl > 0).mean(), "prumer": df.pnl.mean(), "nad_driftem": df.ex.mean(), "t": t}


def newey_west_t(x, lag=10):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 30:
        return 0.0
    e = x - x.mean()
    s = e @ e / n
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return x.mean() / np.sqrt(s / n)


def evaluate(fn, syms, universe, long_only, per_day=False):
    parts = {"vyber": [], "holdout": []}
    port = []
    for s in syms:
        u = universe[s]
        d = u["d"]
        pnl, trades = run_positions(d, fn(d, u), u)
        port.append(pnl.rename(s))
        bpd = {"vyber": 0.0, "holdout": 0.0}
        if long_only:                     # drift za den zvlast pro vyber a holdout
            b = u["bench"]
            bpd = {"vyber": b[b.index < SPLIT].mean(), "holdout": b[b.index >= SPLIT].mean()}
        for t0, dr, p, dd in trades:
            part = "vyber" if t0 < SPLIT else "holdout"
            parts[part].append((t0, dr, p, dd, p - dd * bpd[part]))
    P = pd.concat(port, axis=1)
    P = P.groupby(level=0).sum(min_count=1).mean(axis=1)
    res = {}
    for part, tr in parts.items():
        st = stats(tr)
        if not long_only:
            pp = P[P.index < SPLIT] if part == "vyber" else P[P.index >= SPLIT]
            st["t"] = newey_west_t(pp.values)
            if per_day:
                act = pp[pp.fillna(0) != 0]
                pos, neg = act[act > 0].sum(), -act[act < 0].sum()
                st.update(n=len(act), PF=pos / neg if neg else np.inf, prumer=act.mean() if len(act) else 0.0,
                          nad_driftem=act.mean() if len(act) else 0.0, **{"win%": 100 * (act > 0).mean() if len(act) else 0})
        res[part] = st
    return res


# ---------------------------------------------------------------- strategie

def rsi(px, n=2):
    d = px.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def pos_tsmom(d, L):
    return np.sign(d["px"] / d["px"].shift(L) - 1).fillna(0).astype(int).values


def pos_ibs(d, thr, trend):
    ibs = (d["px"] - d["lo"]) / (d["hi"] - d["lo"]).replace(0, np.nan)
    ok = ibs < thr
    if trend:
        ok &= d["px"] > d["px"].rolling(200).mean()
    return ok.fillna(False).astype(int).values           # drzi 1 den, pak znovu rozhodne


def pos_rsi2(d, thr):
    """Connors: vstup RSI(2) < thr nad SMA200, vystup nad SMA5 nebo po 10 dnech."""
    px = d["px"].values
    r = rsi(d["px"]).values
    sma200 = d["px"].rolling(200).mean().values
    sma5 = d["px"].rolling(5).mean().values
    pos = np.zeros(len(px), int)
    held = 0
    for i in range(1, len(px)):
        if pos[i - 1]:
            held += 1
            pos[i] = 0 if (px[i] > sma5[i] or held >= 10) else 1
        elif r[i] < thr and px[i] > sma200[i]:
            pos[i], held = 1, 0
    return pos


def pos_tom(d, start, end):
    """Long od start-teho posledniho obchodniho dne mesice do end-teho dne noveho."""
    month = d.index.to_period("M")
    one = pd.Series(1, index=d.index)
    from_end = one.groupby(month).cumcount(ascending=False) + 1      # 1 = posledni den
    from_start = one.groupby(month).cumcount() + 1                   # 1 = prvni den
    return ((from_end <= start) | (from_start < end)).astype(int).values


def pos_carry(d, u, trend):
    side = 1 if u["sl"] > 0 else -1 if u["ss"] > 0 else 0
    pos = np.full(len(d), side)
    if trend:                                   # drzet jen kdyz 60denni trend jde stejnym smerem
        pos = np.where(pos_tsmom(d, 60) == side, side, 0)
    return pos


FAMILIES = {
    "A_momentum": [(f"L={L}", lambda d, u, L=L: pos_tsmom(d, L)) for L in (20, 60, 120, 250)],
    "B_navrat_k_prumeru": [(f"IBS<{t}{' +trend' if tr else ''}", lambda d, u, t=t, tr=tr: pos_ibs(d, t, tr))
                           for t in (0.1, 0.2, 0.3) for tr in (False, True)]
                          + [(f"RSI2<{t}", lambda d, u, t=t: pos_rsi2(d, t)) for t in (5, 10, 20)],
    "C_prelom_mesice": [(f"od -{s} do +{e}", lambda d, u, s=s, e=e: pos_tom(d, s, e))
                        for s in (1, 2) for e in (3, 4)],
    "D_carry": [("cisty", lambda d, u: pos_carry(d, u, False)),
                ("+trend 60", lambda d, u: pos_carry(d, u, True))],
}
LONG_ONLY = {"B_navrat_k_prumeru", "C_prelom_mesice"}


def family_symbols(fam, universe):
    if fam in LONG_ONLY:
        return [s for s, u in universe.items() if u["index"]]
    if fam == "D_carry":
        return [s for s, u in universe.items() if u["sl"] > 0 or u["ss"] > 0]
    return list(universe)


# ---------------------------------------------------------------- hlavni beh

def build_universe(names):
    print("\n=== Data a naklady (zivy spread v hodine rozhodnuti) ===")
    indices = []
    for grp, cands in INDEX_GROUPS.items():
        for c in cands:
            if c in names:
                h = load_h1(c)
                if h is not None and h.index[0] <= HISTORY_FROM:
                    indices.append(c)
                    break
                print(f"   {c:<12} kratka historie ({'zadna' if h is None else h.index[0].date()}), zkousim dalsi")
    others = [s for s in names if mc.mt5.symbol_info(s).path.split("\\")[0] in OTHER_GROUPS or s in ENERGY]

    meta_path = os.path.join(DATA_DIR, "naklady.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    universe = {}
    for s in indices + others:
        print(f"   .. {s}", end="\r")
        h = load_h1(s)
        if h is None or h.index[0] > HISTORY_FROM:
            print(f"   {s:<12} vynechan: kratka historie ({'zadna' if h is None else h.index[0].date()})")
            continue
        si = mc.mt5.symbol_info(s)
        crypto = si.path.startswith("CRYPTO")
        hour = decision_hour(s)
        d = daily(h, hour, 0.6 if crypto else 0.25)
        if s in meta and meta[s]["den"] == str(datetime.now(timezone.utc).date()):
            mk, c = meta[s]["prirazka"], meta[s]["naklad"]
        else:
            mk = markup(s)
            if mk is None:
                print(f"   {s:<12} vynechan: prirazku nejde ted zmerit (trh stoji)")
                continue
            c = live_cost(s, hour, mk)
            if c is None:
                print(f"   {s:<12} vynechan: chybi tick data")
                continue
            meta[s] = {"den": str(datetime.now(timezone.utc).date()), "prirazka": mk, "naklad": c}
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=1)
        ratio = c / (d["hi"] - d["lo"]).tail(250).mean()
        sl, ss = swap_frac(si, d["px"].iloc[-1])
        keep = ratio <= MAX_COST_RATIO
        print(f"   {s:<12} od {h.index[0].date()}  spread {c:.5g} ({100 * ratio:4.1f} % dne, prirazka {mk:.3g})  "
              f"swap/noc L {100 * sl:+.4f} % S {100 * ss:+.4f} %"
              f"{'' if keep else '  -> vynechan (naklad > 5 %)'}")
        if not keep:
            continue
        u = {"d": d, "cost": c, "sl": sl, "ss": ss, "nights": swap_nights(d.index, si.swap_rollover3days),
             "index": s in indices}
        if u["index"]:
            u["bench"] = drift_per_day(d, u)
        universe[s] = u
    return universe


def main():
    mc.connect()
    names = [s.name for s in mc.mt5.symbols_get()]

    print("\n=== D: CARRY - ma nektery trh kladny swap? ===")
    pos_sw = [s for s in names if mc.mt5.symbol_info(s).swap_long > 0 or mc.mt5.symbol_info(s).swap_short > 0]
    print(f"Kladny swap aspon jednim smerem: {len(pos_sw)} z {len(names)} symbolu")
    for s in pos_sw:
        si = mc.mt5.symbol_info(s)
        print(f"   {s:<10} long {si.swap_long:+.2f}  short {si.swap_short:+.2f}  (mode {si.swap_mode})")

    universe = build_universe(names)
    n_idx = sum(u["index"] for u in universe.values())
    print(f"\nVesmir: {len(universe)} trhu, z toho akciovych indexu {n_idx}: "
          f"{', '.join(s for s, u in universe.items() if u['index'])}")

    summary = []
    for fam, variants in FAMILIES.items():
        long_only = fam in LONG_ONLY
        syms = family_symbols(fam, universe)
        print(f"\n=== {fam} ({len(syms)} trhu: {', '.join(syms) if len(syms) <= 12 else 'vsechny'}) ===")
        if not syms:
            print("   zadny trh - rodina se neda testovat")
            summary.append((fam, "-", stats([]), False))
            continue
        best = None
        for name, fn in variants:
            res = evaluate(fn, syms, universe, long_only, per_day=fam == "D_carry")
            v = res["vyber"]
            print(f"   {name:<14} vyber: n={v['n']:>5}  PF {v['PF']:.2f}  win {v['win%']:4.1f} %  "
                  f"{'nad driftem' if long_only else 'prumer'} {v['nad_driftem']:+.3f}  t {v['t']:+.2f}")
            if best is None or v["t"] > best[1]["vyber"]["t"]:
                best = (name, res)
        name, res = best
        h = res["holdout"]
        ok = h["n"] >= N_PASS and h["PF"] >= PF_PASS and h["nad_driftem"] > 0 and h["t"] >= T_PASS
        print(f"   -> na holdout jde nejlepsi z vyberu: {name}")
        print(f"      HOLDOUT 2023+: n={h['n']}  PF {h['PF']:.2f}  win {h['win%']:.1f} %  "
              f"{'nad driftem' if long_only else 'prumer'} {h['nad_driftem']:+.3f}  t {h['t']:+.2f}"
              f"   =>  {'PROSLO' if ok else 'NEPROSLO'}")
        summary.append((fam, name, h, ok))

    print("\n=== SHRNUTI ===")
    for fam, name, h, ok in summary:
        print(f"   {fam:<20} {name:<14} holdout PF {h['PF']:.2f}, t {h['t']:+.2f}, n {h['n']}  ->  "
              f"{'PROSLO' if ok else 'neproslo'}")


if __name__ == "__main__":
    main()
