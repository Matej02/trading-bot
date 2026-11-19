"""F49 RSI(2) na evropskych indexech (pravidla F42 beze zmeny). Plan predem ve vaultu: Vyzkum/F49 RSI(2) na evropskych indexech.md."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

import f42_rsi2 as F  # noqa: E402

LB = F.LB
OUT = os.path.join(F.RD, "f49")
os.makedirs(OUT, exist_ok=True)
EU = ["GER_30mini", "GBR_100mini", "FRA_40mini", "EUR_50mini", "ESP_35mini"]
LINES = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LINES.append(s)


say("F49 RSI(2) na evropských indexech – pravidla F42 beze změny; hodnoceno po dnech vstupu; R = výsledek / 3 ATR")
say("=" * 100)
R = {"vyvoj": F.evaluate(EU, "yahoo", F.DEV0, F.SPLIT), "kontrola": F.evaluate(EU, "yahoo", F.SPLIT, None),
     "broker": F.evaluate(EU, "broker", F.SPLIT, None)}
for k, v in R.items():
    say(f"{k:9s} signál:   {LB.fmt(v['sig'])}")
    say(f"{'':9s} srovnání: {LB.fmt(v['base'])}")
    say(f"{'':9s} převis {v['diff']:+.3f} R, t {v['t']:+.2f}")
pos_mk = 0
for mk in EU:
    v = F.evaluate([mk], "yahoo", F.DEV0, None)
    pos_mk += v["diff"] > 0
    k = F.evaluate([mk], "yahoo", F.SPLIT, None)
    say(f"   {mk:11s} celé: {LB.fmt(v['sig'])} | převis {v['diff']:+.3f} (t {v['t']:+.2f}) | 2019+: {k['sig']['m']:+.3f} R, převis {k['diff']:+.3f}")
full = F.evaluate(EU, "yahoo", F.DEV0, None)
pos, line = [], []
for y in sorted(set(full["s"].index.year)):
    dy = full["s"][full["s"].index.year == y].mean() - full["b"][full["b"].index.year == y].mean()
    pos.append(dy > 0)
    line.append(f"{y}:{dy:+.2f}")
share = float(np.mean(pos))
for i in range(0, len(line), 10):
    say("   " + "  ".join(line[i:i + 10]))
say(f"převis kladný v {sum(pos)} z {len(pos)} let ({share:.0%})")
say("ROZHODNUTÍ podle pravidel zapsaných předem")
v, k, br = R["vyvoj"], R["kontrola"], R["broker"]
c = [("1) vývoj: signál > 0, převis > 0, t >= 2,0", v["sig"]["m"] > 0 and v["diff"] > 0 and v["t"] >= 2.0, f"{v['sig']['m']:+.3f}, převis {v['diff']:+.3f}, t {v['t']:+.2f}"),
     ("2) kontrola: signál > 0, převis > 0, t >= 1,5", k["sig"]["m"] > 0 and k["diff"] > 0 and k["t"] >= 1.5, f"{k['sig']['m']:+.3f}, převis {k['diff']:+.3f}, t {k['t']:+.2f}"),
     ("3) aspoň 4 z 5 trhů převis > 0", pos_mk >= 4, f"{pos_mk} z 5"),
     ("4) broker: signál > 0 a převis > 0", br["sig"]["m"] > 0 and br["diff"] > 0, f"{br['sig']['m']:+.3f}, převis {br['diff']:+.3f}"),
     ("5) převis kladný v >= 55 % let", share >= 0.55, f"{share:.0%}")]
for nm, ok, val in c:
    say(f"   {nm}: {'ANO' if ok else 'NE'} ({val})")
say(f"   => {'VÝHODA (prošlo vše)' if all(x[1] for x in c) else 'BEZ VÝHODY'}")
open(os.path.join(OUT, "souhrn.txt"), "w", encoding="utf-8").write(chr(10).join(LINES))
