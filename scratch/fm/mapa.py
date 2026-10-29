import csv, os
r = list(csv.DictReader(open(r"D:\Trading bot\scratch\fm\listy\listy.csv", encoding="utf-8-sig")))
prev = None
for x in r:
    a = x["obrazky"].split(" || ")[0].split(os.sep)[0]
    if a != prev:
        print(x["list"], a); prev = a
