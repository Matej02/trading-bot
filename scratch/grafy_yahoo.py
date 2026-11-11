"""
Pohled na grafy - plne automaticky, bez MT5 a bez TradingView (to automaticke pouziti zakazuje).
Svicky z Yahoo Finance (zdarma, bez uctu), grafy se kresli jako obrazky, ktere si Claude prohlidne.
  python scratch/grafy_yahoo.py                 -> stahne data, nakresli grafy (denni + 15m) a vypise urovne
  python scratch/grafy_yahoo.py zapis TRH SMER  -> zapise Claudeho bias (long/short/neutral) s aktualni cenou
  python scratch/grafy_yahoo.py vyhodnot        -> vyhodnoti zapisy, jejichz obchodni den (do 17:00 NY) skoncil
Den = 17:00-17:00 NY jako v testech F13. Zlato a indexy jsou futures (GC=F, NQ=F, ES=F): cena se od CFD lisi o par bodu,
struktura grafu je stejna.
"""
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Trading bot"
OUT = os.path.join(ROOT, "scratch", "grafy")
IMG = os.path.join(ROOT, "znalosti", "Přílohy", "Grafy")
JL = os.environ.get("GRAFY_JL") or os.path.join(OUT, "claude_bias.jsonl")
VY = JL.replace(".jsonl", "_vysledky.jsonl")
TRHY = {"EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "XAUUSD": "GC=F", "NAS100": "NQ=F", "SPX500": "ES=F"}
PRG, NY = "Europe/Prague", "America/New_York"
SM = {1: "long", -1: "short", 0: "neutral"}
os.makedirs(OUT, exist_ok=True)
os.makedirs(IMG, exist_ok=True)


def yahoo(tk, interval, rng):
    last = None
    for host in ("query1", "query2"):
        for _ in range(2):
            try:
                url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(tk)}?range={rng}&interval={interval}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (grafy bot)"})
                j = json.loads(urllib.request.urlopen(req, timeout=30).read())["chart"]["result"][0]
                q = j["indicators"]["quote"][0]
                df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")},
                                  index=pd.to_datetime(j["timestamp"], unit="s", utc=True)).dropna()
                return df[~df.index.duplicated(keep="last")]
            except Exception as e:  # noqa: BLE001
                last = e
                time.sleep(3)
    raise RuntimeError(f"Yahoo {tk} {interval}: {last}")


def den_ny(idx):
    """Obchodni den (datum), do ktereho cas patri: den konci v 17:00 NY."""
    return (idx.tz_convert(NY).tz_localize(None) + pd.Timedelta(hours=7)).normalize()


def denni(h1):
    g = h1.groupby(den_ny(h1.index))
    return pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()})


def bias(D, k):
    o, h, l, c = D.open.values, D.high.values, D.low.values, D.close.values
    p, q = k - 1, k - 2
    if q < 0:
        return 0
    if c[p] > h[q]:
        return 1
    if c[p] < l[q]:
        return -1
    if h[p] > h[q] and c[p] < h[q]:
        return -1
    if l[p] < l[q] and c[p] > l[q]:
        return 1
    bt, bb = max(o[q], c[q]), min(o[q], c[q])
    if c[p] > bt:
        return 1 if c[p] >= bt + 0.5 * (h[q] - bt) else -1
    if c[p] < bb:
        return -1 if c[p] <= bb - 0.5 * (bb - l[q]) else 1
    return 0


def stav(mk):
    tk = TRHY[mk]
    h1, m15 = yahoo(tk, "60m", "6mo"), yahoo(tk, "15m", "5d")
    D = denni(h1)
    k = len(D) - 1
    b = bias(D, k)
    now_p = pd.Timestamp.now(tz=PRG)
    d0 = now_p.normalize()
    cz = m15.index.tz_convert(PRG)
    asia = m15[(cz >= d0 + pd.Timedelta(hours=2)) & (cz < d0 + pd.Timedelta(hours=8))]
    nyd = m15.index.tz_convert(NY).normalize()
    nyo = m15[nyd == nyd[-1]].open.iloc[0]
    return dict(mk=mk, tk=tk, h1=h1, m15=m15, D=D, bias=b, cena=float(m15.close.iloc[-1]), cas=m15.index[-1],
                pdh=float(D.high.iloc[k - 1]), pdl=float(D.low.iloc[k - 1]), den=str(D.index[k].date()),
                asie_h=float(asia.high.max()) if len(asia) else math.nan, asie_l=float(asia.low.min()) if len(asia) else math.nan,
                ny_open=float(nyo), rozpeti=float((D.high - D.low).iloc[-16:-1].mean()),
                dnes_h=float(D.high.iloc[k]), dnes_l=float(D.low.iloc[k]))


def svicky(ax, df, urovne=()):
    x = range(len(df))
    lv = [v for v in urovne if not math.isnan(v)]
    lo, hi = min([df.low.min()] + lv), max([df.high.max()] + lv)
    ax.set_ylim(lo - 0.04 * (hi - lo), hi + 0.04 * (hi - lo))
    up = (df.close >= df.open).values
    col = ["#26a69a" if u else "#ef5350" for u in up]
    ax.vlines(x, df.low, df.high, color=col, linewidth=0.8)
    ax.bar(x, (df.close - df.open).abs().clip(lower=1e-9), bottom=df[["open", "close"]].min(axis=1), width=0.65, color=col)
    ax.set_xlim(-1, len(df) + 4)
    ax.grid(alpha=0.25)
    ax.yaxis.tick_right()


def cara(ax, y, txt, col, n):
    if not math.isnan(y):
        ax.axhline(y, color=col, linewidth=1, linestyle="--")
        ax.text(n + 3.5, y, f" {txt}", color=col, fontsize=8, va="center", ha="right",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=0.5))


def kresli(s, cesta):
    fx = s["mk"] in ("EURUSD", "GBPUSD")
    fmt = (lambda v: f"{v:.5f}") if fx else (lambda v: f"{v:.2f}")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 7), dpi=100, gridspec_kw={"width_ratios": [1, 1.6]})
    # denni (posledni 2 mesice), den = 17:00 NY
    D = s["D"].iloc[-45:]
    svicky(a1, D, (s["pdh"], s["pdl"]))
    a1.set_xticks(range(0, len(D), 5))
    a1.set_xticklabels([d.strftime("%d.%m.") for d in D.index[::5]], fontsize=8)
    cara(a1, s["pdh"], f"PDH {fmt(s['pdh'])}", "#1565c0", len(D))
    cara(a1, s["pdl"], f"PDL {fmt(s['pdl'])}", "#6a1b9a", len(D))
    a1.set_title("Denní (den 17:00–17:00 NY)", fontsize=10)
    # 15m posledni ~2,5 dne, cas Praha
    m = s["m15"].iloc[-240:]
    svicky(a2, m, (s["pdh"], s["pdl"], s["asie_h"], s["asie_l"], s["ny_open"]))
    cz = m.index.tz_convert(PRG)
    d0 = pd.Timestamp.now(tz=PRG).normalize()
    for od, do, col in ((2, 8, "#fff3c4"), (8, 11, "#e3f2fd"), (14, 17, "#e8f5e9")):
        sel = [i for i, t in enumerate(cz) if d0 + pd.Timedelta(hours=od) <= t < d0 + pd.Timedelta(hours=do)]
        if sel:
            a2.axvspan(sel[0] - 0.5, sel[-1] + 0.5, color=col, zorder=0)
    ticks = [i for i, t in enumerate(cz) if t.minute == 0 and t.hour % 4 == 0]
    a2.set_xticks(ticks)
    a2.set_xticklabels([cz[i].strftime("%a %H:%M") for i in ticks], fontsize=7, rotation=0)
    cara(a2, s["pdh"], "PDH", "#1565c0", len(m))
    cara(a2, s["pdl"], "PDL", "#6a1b9a", len(m))
    cara(a2, s["asie_h"], "Asie H", "#b8860b", len(m))
    cara(a2, s["asie_l"], "Asie L", "#b8860b", len(m))
    cara(a2, s["ny_open"], "NY open", "#424242", len(m))
    a2.set_title("15m, čas Praha | žlutě Asie 2–8, modře Londýn 8–11, zeleně NY 14–17 (dnes)", fontsize=10)
    t_p = s["cas"].tz_convert(PRG)
    fig.suptitle(f"{s['mk']} (Yahoo {s['tk']})  |  poslední svíčka {t_p:%d.%m. %H:%M} Praha  |  cena {fmt(s['cena'])}  |  "
                 f"bias pravidel F13: {SM[s['bias']]}", fontsize=12)
    fig.tight_layout()
    fig.savefig(cesta)
    plt.close(fig)


if len(sys.argv) == 1:
    now = datetime.now()
    print(f"Pohled na grafy {now:%Y-%m-%d %H:%M} Praha, data Yahoo (zdarma, bez uctu). Bias = pravidla F13 z dennich svicek 17:00 NY.\n")
    print("| Trh | Cena | Bias pravidel | Cil | Cil uz trefen | PDH | PDL | Asie H 2-8 | Asie L 2-8 | NY open | Prumerne denni rozpeti | Graf |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for mk in TRHY:
        try:
            s = stav(mk)
        except Exception as e:  # noqa: BLE001
            print(f"| {mk} | CHYBA dat: {e} |")
            continue
        fx = mk in ("EURUSD", "GBPUSD")
        f = (lambda v: f"{v:.5f}") if fx else (lambda v: f"{v:.2f}")
        jm = f"{now:%Y-%m-%d_%H%M}_{mk}.png"
        kresli(s, os.path.join(IMG, jm))
        cil = s["pdh"] if s["bias"] == 1 else s["pdl"] if s["bias"] == -1 else math.nan
        tref = (s["bias"] == 1 and s["dnes_h"] >= s["pdh"]) or (s["bias"] == -1 and s["dnes_l"] <= s["pdl"])
        print(f"| {mk} | {f(s['cena'])} | {SM[s['bias']]} | {f(cil) if s['bias'] else '-'} | {'ano' if tref else 'ne'} | {f(s['pdh'])} | "
              f"{f(s['pdl'])} | {f(s['asie_h'])} | {f(s['asie_l'])} | {f(s['ny_open'])} | {f(s['rozpeti'])} | {jm} |")
    print(f"\nObrazky: {IMG}")

elif sys.argv[1] == "zapis":
    mk, sm = sys.argv[2], sys.argv[3].lower()
    assert mk in TRHY, f"neznamy trh {mk}, povolene {list(TRHY)}"
    assert sm in ("long", "short", "neutral"), "smer musi byt long / short / neutral"
    s = stav(mk)
    rec = dict(ts=int(datetime.now(timezone.utc).timestamp()), trh=mk, claude={"long": 1, "short": -1, "neutral": 0}[sm],
               pravidla=s["bias"], cena=s["cena"], pdh=s["pdh"], pdl=s["pdl"], den=s["den"])
    with open(JL, "a", encoding="utf-8") as fo:
        fo.write(json.dumps(rec) + "\n")
    print("zapsano", rec)

elif sys.argv[1] == "vyhodnot":
    if not os.path.exists(JL):
        sys.exit("zatim zadne zapisy")
    R = [json.loads(x) for x in open(JL, encoding="utf-8") if x.strip()]
    hotovo = {(json.loads(x)["ts"], json.loads(x)["trh"]) for x in open(VY, encoding="utf-8")} if os.path.exists(VY) else set()
    cache = {}
    nove = 0
    for rec in R:
        if (rec["ts"], rec["trh"]) in hotovo:
            continue
        konec = (pd.Timestamp(rec["den"]) + pd.Timedelta(hours=17)).tz_localize(NY)   # 17:00 NY = konec obchodniho dne
        if konec > pd.Timestamp.now(tz=NY) - pd.Timedelta(minutes=30):
            continue
        if rec["trh"] not in cache:
            cache[rec["trh"]] = yahoo(TRHY[rec["trh"]], "15m", "60d")
        m = cache[rec["trh"]]
        t0 = pd.Timestamp(rec["ts"], unit="s", tz="UTC")
        x = m[(m.index >= t0) & (m.index < konec.tz_convert("UTC"))]
        if x.empty:
            continue
        c1, hi, lo = float(x.close.iloc[-1]), float(x.high.max()), float(x.low.min())
        out = dict(ts=rec["ts"], trh=rec["trh"], den=rec["den"], claude=rec["claude"], pravidla=rec["pravidla"], cena=rec["cena"],
                   close=c1, hi=hi, lo=lo, pdh=rec["pdh"], pdl=rec["pdl"])
        with open(VY, "a", encoding="utf-8") as fo:
            fo.write(json.dumps(out) + "\n")
        nove += 1
    if not os.path.exists(VY):
        sys.exit("zatim nic k vyhodnoceni (den zapisu jeste neskoncil)")
    V = [json.loads(x) for x in open(VY, encoding="utf-8") if x.strip()]
    rows = []
    for v in V:
        for kdo in ("claude", "pravidla"):
            b = v[kdo]
            if b:
                rows.append(dict(kdo=kdo, smer=(v["close"] - v["cena"]) * b > 0,
                                 cil=(v["hi"] >= v["pdh"]) if b == 1 else (v["lo"] <= v["pdl"]), shoda=v["claude"] == v["pravidla"]))
    T = pd.DataFrame(rows)
    dni = len({v["den"] for v in V})
    print(f"Vyhodnoceni biasu: {len(V)} zapisu za {dni} obchodnich dni (nove {nove}). Rozhodnuti az po >= 30 dnech a >= 100 zapisech long/short.")
    print("  smer = cena na konci dne 17:00 NY vs cena pri zapisu; cil = PDH (long) / PDL (short) zasazen po zapisu do konce dne")
    if T.empty:
        sys.exit("  zatim jen neutralni zapisy")
    for kdo, g in T.groupby("kdo"):
        n, k = len(g), int(g.smer.sum())
        z = (k - 0.5 * n) / math.sqrt(0.25 * n)
        print(f"  {kdo:9s} n {n:4d}  smer {k / n * 100:5.1f} % (z {z:+.2f})  cil {g.cil.mean() * 100:5.1f} %")
    c = T[T.kdo == "claude"]
    if len(c) and (~c.shoda).any():
        print(f"  claude pri neshode s pravidly: n {int((~c.shoda).sum())}, smer {c[~c.shoda].smer.mean() * 100:.1f} %")
