"""Vykresli vybrane strany PDF do PNG: render.py <relativni cesta bez .pdf> <strany 1,2,3> [sirka px]"""
import os
import sys

import pymupdf

SRC = r"D:\youtube\FM pdfka"
OUT = r"D:\Trading bot\scratch\fm\png"
os.makedirs(OUT, exist_ok=True)
rel, pages = sys.argv[1], [int(x) for x in sys.argv[2].split(",")]
width = int(sys.argv[3]) if len(sys.argv) > 3 else 1400
doc = pymupdf.open(os.path.join(SRC, rel + ".pdf"))
for p in pages:
    pg = doc[p - 1]
    zoom = width / pg.rect.width
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    name = rel.replace(os.sep, "_").replace("/", "_").replace(" ", "_") + f"_s{p}.png"
    path = os.path.join(OUT, name)
    pix.save(path)
    print(path)
