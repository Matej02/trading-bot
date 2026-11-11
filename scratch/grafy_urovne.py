"""
Pohled na grafy (TradingView) - pomocnik, JEN CTENI z MT5. MT5 nikdy nespousti: kdyz terminal64 nebezi, skonci.
  python scratch/grafy_urovne.py                 -> urovne dne (PDH/PDL, Asie 2-8 Praha, NY open, bias podle pravidel F13)
  python scratch/grafy_urovne.py zapis TRH SMER  -> zapise Claudeho bias (long/short/neutral) s aktualni cenou do deniku
  python scratch/grafy_urovne.py vyhodnot        -> vyhodnoti zapisy, jejichz den (17:00 NY) uz skoncil
Cas serveru brokera je UTC cely rok. Den = 17:00-17:00 NY jako v testech F13. Denik: scratch/grafy/claude_bias.jsonl
"""
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Trading bot"
OUT = os.path.join(ROOT, "scratch", "grafy")
JL = os.environ.get("GRAFY_JL") or os.path.join(OUT, "claude_bias.jsonl")
TRHY = ["EURUSD", "GBPUSD", "XAUUSD", "NAS100mini", "SPX500mini"]
os.makedirs(OUT, exist_ok=True)

r = subprocess.run(["tasklist", "/fi", "imagename eq terminal64.exe"], capture_output=True, text=True)
if "terminal64.exe" not in r.stdout.lower():
    sys.exit("MT5 nebezi - urovne z MT5 nejsou, MT5 se odsud nespousti. Pouzij jen TradingView.")

import MetaTrader5 as mt5  # noqa: E402
import pandas as pd  # noqa: E402

if not mt5.initialize():
    sys.exit(f"MT5 nedostupne {mt5.last_error()}")


def h1(mk, n=900):
    mt5.symbol_select(mk, True)
    x = pd.DataFrame(mt5.copy_rates_from_pos(mk, mt5.TIMEFRAME_H1, 0, n))
    x["t"] = pd.to_datetime(x.time, unit="s", utc=True)
    ny = x.t.dt.tz_convert("America/New_York").dt.tz_localize(None)
    x["den"] = (ny + pd.Timedelta(hours=7)).dt.normalize()          # obchodni den od 17:00 NY
    x["nyden"] = ny.dt.normalize()
    x["cz"] = x.t.dt.tz_convert("Europe/Prague")
    return x


def bias(D, k):
    o, h, l, c = D.open.values, D.high.values, D.low.values, D.close.values
    p, q = k - 1, k - 2
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


def urovne(mk):
    x = h1(mk)
    D = x.groupby("den").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
    k = len(D) - 1                                                  # dnesni (rozbehnuty) den
    dnes = x[x.den == D.index[k]]
    b = bias(D, k)
    pdh, pdl = D.high.iloc[k - 1], D.low.iloc[k - 1]
    cil = pdh if b == 1 else pdl if b == -1 else float("nan")
    trefen = (b == 1 and dnes.high.max() >= pdh) or (b == -1 and dnes.low.min() <= pdl)
    czd = x.cz.iloc[-1].normalize()
    a = x[(x.cz >= czd + pd.Timedelta(hours=2)) & (x.cz < czd + pd.Timedelta(hours=8))]
    nyo = x[x.nyden == x.nyden.iloc[-1]].open.iloc[0]
    tr = (D.high - D.low).tail(15).mean()
    tick = mt5.symbol_info_tick(mk)
    return dict(trh=mk, cena=tick.bid, bias=b, cil=cil, cil_trefen=bool(trefen), pdh=pdh, pdl=pdl,
                asie_h=a.high.max() if len(a) else float("nan"), asie_l=a.low.min() if len(a) else float("nan"),
                ny_open=nyo, rozpeti_dne=tr, dnes_h=dnes.high.max(), dnes_l=dnes.low.min(), den=str(D.index[k].date()))


SM = {1: "long", -1: "short", 0: "neutral"}

if len(sys.argv) == 1:
    print(f"Urovne z MT5 (broker, jen cteni) {datetime.now():%Y-%m-%d %H:%M} Praha. Bias = pravidla F13 (Veselovsky) z dennich svicek 17:00 NY.\n")
    print("| Trh | Cena | Bias pravidel | Cil (PDH/PDL) | Cil uz trefen | PDH | PDL | Asie H 2-8 | Asie L 2-8 | NY open | Prumerne denni rozpeti |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for mk in TRHY:
        u = urovne(mk)
        f = (lambda v: f"{v:.5f}") if mk in ("EURUSD", "GBPUSD") else (lambda v: f"{v:.2f}")
        print(f"| {mk} | {f(u['cena'])} | {SM[u['bias']]} | {f(u['cil']) if u['bias'] else '-'} | {'ano' if u['cil_trefen'] else 'ne'} | "
              f"{f(u['pdh'])} | {f(u['pdl'])} | {f(u['asie_h'])} | {f(u['asie_l'])} | {f(u['ny_open'])} | {f(u['rozpeti_dne'])} |")

elif sys.argv[1] == "zapis":
    mk, sm = sys.argv[2], sys.argv[3].lower()
    assert mk in TRHY, f"neznamy trh {mk}"
    assert sm in ("long", "short", "neutral"), "smer musi byt long / short / neutral"
    u = urovne(mk)
    rec = dict(ts=int(datetime.now(timezone.utc).timestamp()), trh=mk, claude={"long": 1, "short": -1, "neutral": 0}[sm],
               pravidla=u["bias"], cena=u["cena"], pdh=u["pdh"], pdl=u["pdl"], den=u["den"])
    with open(JL, "a", encoding="utf-8") as fo:
        fo.write(json.dumps(rec) + "\n")
    print("zapsano", rec)

elif sys.argv[1] == "vyhodnot":
    if not os.path.exists(JL):
        sys.exit("zatim zadne zapisy")
    R = [json.loads(s) for s in open(JL, encoding="utf-8") if s.strip()]
    rows = []
    for rec in R:
        t0 = pd.Timestamp(rec["ts"], unit="s", tz="UTC")
        ny0 = t0.tz_convert("America/New_York")
        konec = (ny0 + pd.Timedelta(hours=7)).normalize() + pd.Timedelta(hours=17)   # 17:00 NY konce obchodniho dne
        if konec.tz_convert("UTC") > pd.Timestamp.now(tz="UTC"):
            continue
        m = pd.DataFrame(mt5.copy_rates_range(rec["trh"], mt5.TIMEFRAME_M1, t0.to_pydatetime(), konec.tz_convert("UTC").to_pydatetime()))
        if m.empty:
            continue
        c1, hi, lo = m.close.iloc[-1], m.high.max(), m.low.min()
        for kdo in ("claude", "pravidla"):
            b = rec[kdo]
            if b == 0:
                continue
            rows.append(dict(kdo=kdo, smer=(c1 - rec["cena"]) * b > 0, cil=(hi >= rec["pdh"]) if b == 1 else (lo <= rec["pdl"]),
                             shoda=rec["claude"] == rec["pravidla"]))
    if not rows:
        sys.exit("zatim nic k vyhodnoceni (den zapisu jeste neskoncil)")
    T = pd.DataFrame(rows)
    print("Vyhodnoceni biasu (smer = cena na konci dne 17:00 NY vs cena pri zapisu; cil = dosazeni PDH/PDL do konce dne)")
    for kdo, g in T.groupby("kdo"):
        n, k = len(g), int(g.smer.sum())
        z = (k - 0.5 * n) / math.sqrt(0.25 * n)
        print(f"  {kdo:9s} n {n:4d}  smer {k / n * 100:5.1f} % (z {z:+.2f})  cil {g.cil.mean() * 100:5.1f} %")
    c = T[(T.kdo == "claude")]
    if len(c):
        print(f"  claude pri shode s pravidly n {int(c.shoda.sum())}, pri neshode n {int((~c.shoda).sum())}"
              f" (smer pri neshode {c[~c.shoda].smer.mean() * 100 if (~c.shoda).any() else float('nan'):.1f} %)")
mt5.shutdown()
