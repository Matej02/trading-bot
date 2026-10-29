import os

import pandas as pd

d = pd.read_csv(r"D:\Trading bot\scratch\fm\index.csv", encoding="utf-8-sig")
d["slozka"] = d.soubor.map(lambda s: "/".join(s.split(os.sep)[:2]))
g = d.groupby("slozka").agg(pdf=("soubor", "count"), stran=("stran", "sum"), znaku=("znaku", "sum"),
                            malo=("na_stranu", lambda s: (s < 150).sum()))
print(g.to_string())
print()
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 140)
print(d[d.na_stranu < 150][["soubor", "stran", "znaku", "mb"]].to_string())
