"""Vytazeni textu ze vsech FM PDF (pdftotext -enc UTF-8 -layout) do scratch/fm/txt se stejnou strukturou.
Vystup: index.csv (soubor, stran, znaku, znaku na stranu) - podle nej poznam PDF, ktera jsou jen obrazky."""
import csv
import os
import subprocess
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else r"D:\youtube\FM pdfka"
DST = r"D:\Trading bot\scratch\fm\txt"

rows = []
for root, _, files in os.walk(SRC):
    for f in sorted(files):
        if not f.lower().endswith(".pdf"):
            continue
        src = os.path.join(root, f)
        rel = os.path.relpath(src, SRC)
        out = os.path.join(DST, rel[:-4] + ".txt")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        r = subprocess.run(["pdftotext", "-enc", "UTF-8", "-layout", src, out], capture_output=True)
        txt = open(out, encoding="utf-8", errors="replace").read() if os.path.exists(out) else ""
        pages = txt.count("\f") or 1
        chars = len("".join(txt.split()))
        rows.append(dict(soubor=rel, stran=pages, znaku=chars, na_stranu=round(chars / pages), mb=round(os.path.getsize(src) / 1e6, 2),
                         chyba=r.stderr.decode("utf-8", "replace")[:100].strip()))

with open(os.path.join(os.path.dirname(DST), "index.csv"), "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(len(rows), "PDF; stran", sum(r["stran"] for r in rows), "; znaku", sum(r["znaku"] for r in rows))
print("malo textu (<150 znaku/strana):", sum(r["na_stranu"] < 150 for r in rows))
