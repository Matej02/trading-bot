"""OCR popisků v obrázcích všech FM PDF (jen obsahové obrázky, bez loga a pozadí).
Výstup: scratch/fm/ocr/<modul>.txt  a  scratch/fm/ocr_vse.txt. Čísla z cenové osy, data a vodoznaky se zahazují."""
import os
import re
import sys

import pymupdf
from rapidocr_onnxruntime import RapidOCR

SRC = r"D:\youtube\FM pdfka"
OUT = r"D:\Trading bot\scratch\fm\ocr"
os.makedirs(OUT, exist_ok=True)
eng = RapidOCR()
JUNK = re.compile(r"(tradingview|wizards|watermark|published on|fundedmind|www\.|\.com|\.net|^[\d\s.,:%+\-/|()$€]+$)", re.I)


def useful(t):
    t = t.strip()
    if len(t) < 3 or JUNK.search(t):
        return False
    letters = sum(c.isalpha() for c in t)
    return letters >= 3 and letters / len(t) > 0.4


groups = {}
for root, _, files in os.walk(SRC):
    for f in sorted(files):
        if f.lower().endswith(".pdf"):
            rel = os.path.relpath(os.path.join(root, f), SRC)[:-4]
            groups.setdefault("__".join(rel.split(os.sep)[:2]), []).append(rel)

done = 0
for g, rels in sorted(groups.items()):
    outp = os.path.join(OUT, g + ".txt")
    if os.path.exists(outp):
        continue
    lines = []
    for rel in rels:
        doc = pymupdf.open(os.path.join(SRC, rel + ".pdf"))
        for i, pg in enumerate(doc, 1):
            A = pg.rect.width * pg.rect.height
            boxes = []
            for info in pg.get_image_info():
                x0, y0, x1, y1 = info["bbox"]
                fr = max(0, x1 - x0) * max(0, y1 - y0) / A
                if 0.03 <= fr <= 0.9:
                    boxes.append(pymupdf.Rect(x0, y0, x1, y1) & pg.rect)
            if not boxes:
                continue
            texts = []
            for b in boxes:
                zoom = max(1.0, min(3.0, 1600 / max(b.width, 1)))
                pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=b)
                res, _ = eng(pix.tobytes("png"))
                for r in res or []:
                    if useful(r[1]):
                        texts.append(r[1].strip())
            done += 1
            if texts:
                lines.append(f"[{rel} | s{i}] " + " | ".join(dict.fromkeys(texts)))
    with open(outp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(g, len(lines), "stran s textem", flush=True)

with open(r"D:\Trading bot\scratch\fm\ocr_vse.txt", "w", encoding="utf-8") as fh:
    for f in sorted(os.listdir(OUT)):
        fh.write(open(os.path.join(OUT, f), encoding="utf-8").read() + "\n")
print("hotovo", done, "stran s obrázky")
