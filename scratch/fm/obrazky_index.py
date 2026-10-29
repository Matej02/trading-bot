"""Najde všechny strany FM PDF, kde je obrázek s obsahem (graf, tabulka) - ne jen logo/pozadí šablony.
Výstup: scratch/fm/obrazky.csv (soubor, strana, plocha obrázků %, znaků textu)."""
import csv
import os

import pymupdf

SRC = r"D:\youtube\FM pdfka"
rows = []
for root, _, files in os.walk(SRC):
    for f in sorted(files):
        if not f.lower().endswith(".pdf"):
            continue
        p = os.path.join(root, f)
        rel = os.path.relpath(p, SRC)[:-4]
        doc = pymupdf.open(p)
        for i, pg in enumerate(doc, 1):
            A = pg.rect.width * pg.rect.height
            area = 0.0
            for info in pg.get_image_info():
                x0, y0, x1, y1 = info["bbox"]
                a = max(0, x1 - x0) * max(0, y1 - y0)
                fr = a / A
                if fr > 0.9 or fr < 0.03:  # celostránkové pozadí / logo
                    continue
                area += fr
            txt = len("".join(pg.get_text().split()))
            rows.append(dict(soubor=rel, strana=i, plocha=round(min(area, 1) * 100), znaku=txt, stran=len(doc)))
with open(r"D:\Trading bot\scratch\fm\obrazky.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
obr = [r for r in rows if r["plocha"] >= 8]
print("stran celkem", len(rows), "| s obsahovým obrázkem", len(obr), "| v PDF", len({r["soubor"] for r in obr}))
