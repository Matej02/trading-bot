"""Kontaktní listy grafů k prohlédnutí: z trading PDF (bez prop firem, journalingu, výsledků, mindsetu) vyřízne
obsahové obrázky a skládá je po 4 (2x2) na list s popiskem 'PDF | strana'. Výstup scratch/fm/listy/NNN.png + listy.csv."""
import csv
import io
import os

import pymupdf
from PIL import Image, ImageDraw, ImageFont

SRC = r"D:\youtube\FM pdfka"
OUT = r"D:\Trading bot\scratch\fm\listy"
os.makedirs(OUT, exist_ok=True)
SKIP = ("Prop Firm Blueprint", "8. Journaling", "7. Backtesting", "9. Futures", "Basecamp", "Launchpad",
        "Moje výsledky", "Propfirmy", "prop firmy", "Prop Firm Management", "Risk Management –", "⁠Risk Management –",
        "FUTURES vs CFD", "Co jsou futures", "Velikost Pozice", "Futures trading", "Lockout", "Journaling", "CNBC",
        "Forex Factory", "Forex factory", "Seasonax", "Úvod do TrA", "Představení Trading Analyzeru", "Co ovlivňuje NASDAQ",
        "Earnings")
CELL = 460  # šířka buňky v px
font = ImageFont.truetype("arial.ttf", 15)

import collections
cnt = collections.Counter()
for root, _, files in os.walk(SRC):
    for f in files:
        if f.lower().endswith(".pdf"):
            for pg in pymupdf.open(os.path.join(root, f)):
                for info in pg.get_image_info(hashes=True):
                    cnt[info["digest"]] += 1
items = []
for root, _, files in os.walk(SRC):
    for f in sorted(files):
        if not f.lower().endswith(".pdf"):
            continue
        rel = os.path.relpath(os.path.join(root, f), SRC)[:-4]
        if any(s in rel for s in SKIP):
            continue
        doc = pymupdf.open(os.path.join(SRC, rel + ".pdf"))
        for i, pg in enumerate(doc, 1):
            A = pg.rect.width * pg.rect.height
            for k, info in enumerate(pg.get_image_info(hashes=True)):
                x0, y0, x1, y1 = info["bbox"]
                fr = max(0, x1 - x0) * max(0, y1 - y0) / A
                if 0.06 <= fr <= 0.9 and cnt[info["digest"]] <= 2:
                    b = pymupdf.Rect(x0, y0, x1, y1) & pg.rect
                    zoom = min(3.0, CELL / max(b.width, 1))
                    pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=b)
                    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                    im.thumbnail((CELL, int(CELL * 0.75)))
                    short = rel.replace("Strategie\\", "").replace("Základy tradingu\\", "Z\\").replace(" Strategie (PDF)", "")
                    items.append((f"{short} | s{i}", im))

rows = []
N = 9
for n in range(0, len(items), N):
    chunk = items[n:n + N]
    H = int(CELL * 0.75) + 24
    sheet = Image.new("RGB", (CELL * 3 + 20, H * 3 + 20), "white")
    d = ImageDraw.Draw(sheet)
    for j, (label, im) in enumerate(chunk):
        x, y = (j % 3) * (CELL + 10), (j // 3) * (H + 10)
        d.rectangle([x, y, x + CELL, y + 20], fill=(30, 30, 30))
        d.text((x + 4, y + 2), str(j + 1) + ") " + label[-62:], fill="white", font=font)
        sheet.paste(im, (x, y + 22))
    name = f"{n // N + 1:03d}.png"
    sheet.save(os.path.join(OUT, name), optimize=True)
    rows.append(dict(list=name, obrazky=" || ".join(l for l, _ in chunk)))
with open(os.path.join(OUT, "listy.csv"), "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=["list", "obrazky"])
    w.writeheader()
    w.writerows(rows)
print("obrázků", len(items), "listů", len(rows))
